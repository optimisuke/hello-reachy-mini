"""Minimal HTTP proxy that exposes Reachy Mini over REST, to run on the robot.

ESP32 のようなマイコンから操作するための最小構成。すべて GET にしてあるので、
`http.begin(url); http.GET();` の2行で呼べる。

本体上で実行する:

    source /venvs/apps_venv/bin/activate
    python reachy_proxy.py

Mac から確認する:

    curl http://reachy-mini.local:8080/
    curl http://reachy-mini.local:8080/moves
    curl "http://reachy-mini.local:8080/move/simple_nod"
"""

import argparse
import math
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import (
    DEFAULT_EMOTIONS_DATASET,
    RecordedMoves,
)
from reachy_mini.utils import create_head_pose


# daemon 自身のREST。プロキシと同じ本体で動いているのでlocalhostで足りる。
DAEMON_URL = "http://localhost:8000"

LIBRARIES = {
    "dances": "pollen-robotics/reachy-mini-dances-library",
    "emotions": DEFAULT_EMOTIONS_DATASET,
}

# SDK への同時アクセスを防ぐ。FastAPI の同期エンドポイントはスレッドプールで動くため、
# ロックなしだと複数リクエストが同時にロボットを操作しうる。
_lock = threading.Lock()

# wait=false で再生中かどうか。ロックは再生中ずっと保持されるため、状態は別に持つ。
_playing = threading.Event()

_state: dict[str, Any] = {"mini": None, "libraries": {}}


def get_mini() -> ReachyMini:
    """Return the live SDK connection, or fail with 503 if it is not ready."""
    mini = _state["mini"]
    if mini is None:
        raise HTTPException(status_code=503, detail="ロボットへ接続していません")
    return mini


def get_library(name: str) -> RecordedMoves:
    """Return a preloaded move library by short name."""
    if name not in LIBRARIES:
        raise HTTPException(
            status_code=400,
            detail=f"library は {'/'.join(LIBRARIES)} のいずれかです",
        )
    return _state["libraries"][name]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Hold one SDK connection for the whole process lifetime.

    リクエストごとに接続すると遅いので、起動時に1回だけ張って保持する。
    """
    print("Reachy Mini へ接続しています...", flush=True)
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="default",  # 感情モーションの音を鳴らすため既定のまま
    ) as mini:
        mini.enable_motors()
        mini.goto_target(head=create_head_pose(), duration=1.5)
        _state["mini"] = mini
        _state["libraries"] = {
            short: RecordedMoves(dataset) for short, dataset in LIBRARIES.items()
        }
        for short, library in _state["libraries"].items():
            print(f"  {short}: {len(library.list_moves())}件", flush=True)
        print("準備できました。", flush=True)
        try:
            yield
        finally:
            _state["mini"] = None
            print("接続を閉じます。", flush=True)


app = FastAPI(title="Reachy Mini proxy", lifespan=lifespan)


@app.get("/")
def index() -> dict[str, Any]:
    """Describe the available endpoints."""
    return {
        "name": "Reachy Mini proxy",
        "endpoints": [
            "GET /moves?library=dances|emotions",
            "GET /move/{name}?library=dances|emotions&initial_goto=1.0&sound=true&wait=true",
            "GET /cancel",
            "GET /antennas?left=30&right=-30",
            "GET /body_yaw?deg=20",
            "GET /head?roll=0&pitch=-10&yaw=0&duration=1.0",
            "GET /sound/{name}",
            "GET /state",
        ],
    }


@app.get("/moves")
def list_moves(library: str = "dances") -> dict[str, Any]:
    """List the moves available in one library."""
    moves = get_library(library)
    names = sorted(moves.list_moves())
    return {
        "library": library,
        "count": len(names),
        "moves": [
            {
                "name": name,
                "duration": moves.get(name).duration,
                "sound": moves.get(name).sound_path is not None,
            }
            for name in names
        ],
    }


@app.get("/move/{name}")
def play(
    name: str,
    library: str = "dances",
    initial_goto: float = 1.0,
    sound: bool = True,
    wait: bool = True,
) -> dict[str, Any]:
    """Play one recorded move.

    wait=true（既定）は再生完了まで応答を返さない。長いモーション（`sleep1` は19.76秒）
    ではマイコン側のHTTPタイムアウトが厳しくなるため、wait=false ですぐ返せるように
    してある。完了は `/state` の `is_move_running` で確認できる。
    """
    moves = get_library(library)
    if name not in moves.list_moves():
        raise HTTPException(status_code=404, detail=f"存在しないモーション: {name}")
    move = moves.get(name)
    mini = get_mini()

    def run() -> None:
        # async_play_move は await 必須のコルーチンなので同期コードから呼んでも動かない。
        # 同期ラッパーの play_move をスレッドで回す。
        with _lock:
            mini.play_move(move, initial_goto_duration=initial_goto, sound=sound)

    if wait:
        run()
    else:
        if _playing.is_set():
            raise HTTPException(status_code=409, detail="別のモーションを再生中です")

        def run_and_clear() -> None:
            try:
                run()
            finally:
                _playing.clear()

        _playing.set()
        threading.Thread(target=run_and_clear, daemon=True, name="play-move").start()

    return {
        "played": name,
        "library": library,
        "duration": move.duration,
        "waited": wait,
    }


@app.get("/cancel")
def cancel() -> dict[str, Any]:
    """Cancel the move currently playing (useful after wait=false)."""
    mini = get_mini()
    # 再生スレッドが _lock を保持しているため、ここでロックを取ると自分が待たされる。
    mini.cancel_move()
    return {"cancelled": True}


@app.get("/antennas")
def antennas(left: float = 0.0, right: float = 0.0, duration: float = 0.5) -> dict[str, Any]:
    """Move both antennas, in degrees."""
    mini = get_mini()
    with _lock:
        mini.goto_target(
            antennas=[math.radians(left), math.radians(right)],
            duration=duration,
        )
    return {"antennas_deg": [left, right]}


@app.get("/body_yaw")
def body_yaw(deg: float = 0.0, duration: float = 1.0) -> dict[str, Any]:
    """Rotate the body, in degrees."""
    mini = get_mini()
    with _lock:
        mini.goto_target(body_yaw=math.radians(deg), duration=duration)
    return {"body_yaw_deg": deg}


@app.get("/head")
def head(
    roll: float = 0.0,
    pitch: float = 0.0,
    yaw: float = 0.0,
    duration: float = 1.0,
) -> dict[str, Any]:
    """Set the head orientation, in degrees."""
    mini = get_mini()
    with _lock:
        mini.goto_target(
            head=create_head_pose(roll=roll, pitch=pitch, yaw=yaw, degrees=True),
            duration=duration,
        )
    return {"head_deg": {"roll": roll, "pitch": pitch, "yaw": yaw}}


@app.get("/sound/{name}")
def sound(name: str) -> dict[str, Any]:
    """Play one of the built-in sounds by file name (e.g. wake_up.wav)."""
    import reachy_mini

    path: Path = Path(reachy_mini.__file__).parent / "assets" / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"存在しない音源: {name}")
    mini = get_mini()
    with _lock:
        mini.media.play_sound(str(path))
    return {"played": name}


@app.get("/state")
def state() -> dict[str, Any]:
    """Return the current joint positions."""
    mini = get_mini()
    # 読み取りだけなのでロックを取らない。取ると長いモーションの再生中に
    # /state がロック待ちでタイムアウトしてしまう（実際にそうなった）。
    head_joints, antenna_joints = mini.get_current_joint_positions()
    # 再生状態は Python SDK からは取れない（get_status() が返す DaemonStatus には
    # is_move_running が無く、.state は daemon のライフサイクル enum）。
    # daemon 自身の REST `GET /api/move/running` が再生中タスクのuuid一覧を返すので、
    # それを使う。
    running: list[Any] = []
    try:
        running = httpx.get(f"{DAEMON_URL}/api/move/running", timeout=3.0).json()
    except Exception as exc:  # daemon が応答しなくても /state は返す
        print(f"running の取得に失敗: {exc}", flush=True)
    return {
        "head_joint_positions": list(head_joints),
        "antennas_joint_positions": list(antenna_joints),
        "antennas_deg": [math.degrees(v) for v in antenna_joints],
        "is_move_running": bool(running),
        "running": running,
        "playing": _playing.is_set(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0", help="待ち受けアドレス")
    parser.add_argument("--port", type=int, default=8080, help="待ち受けポート")
    args = parser.parse_args()
    # daemon が 8000 を使っているため、既定は 8080。
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
