"""Play recorded moves (dances and emotions) directly on a Wireless Reachy Mini.

ダンスと感情モーションは同じ Recorded Moves の仕組みで再生できる。どちらも
HuggingFace のデータセットとして配布され、daemon 起動時にキャッシュ済み。
"""

import argparse
import time

from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import (
    DEFAULT_EMOTIONS_DATASET,
    RecordedMoves,
)
from reachy_mini.utils import create_head_pose


LIBRARIES = {
    "dances": "pollen-robotics/reachy-mini-dances-library",
    "emotions": DEFAULT_EMOTIONS_DATASET,
}


def show_list(library: RecordedMoves, name: str) -> None:
    """Print every move in the library with its duration and sound availability."""
    names = sorted(library.list_moves())
    print(f"=== {name}: {len(names)}件 ===")
    for move_name in names:
        move = library.get(move_name)
        sound = "音あり" if move.sound_path else "音なし"
        print(f"  {move_name:<24} {move.duration:5.2f}秒  {sound}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "names",
        nargs="*",
        help="再生するモーション名（複数指定で連続再生）",
    )
    parser.add_argument(
        "--library",
        default="dances",
        choices=sorted(LIBRARIES),
        help="使用するライブラリ",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="モーション名の一覧を表示して終了する",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="モーションに紐づく音を鳴らさない",
    )
    parser.add_argument(
        "--initial-goto",
        type=float,
        default=1.0,
        help="開始姿勢へ移動する時間（秒）。0で移動なし",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=1.0,
        help="連続再生するときのモーション間の待ち時間（秒）",
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
        help="再生開始前のカウントダウン秒数",
    )
    args = parser.parse_args()

    dataset = LIBRARIES[args.library]
    print(f"ライブラリを読み込みます: {dataset}", flush=True)
    library = RecordedMoves(dataset)

    if args.list or not args.names:
        show_list(library, args.library)
        if not args.list:
            print("\n名前を指定して再生してください。", flush=True)
        return

    # 存在しない名前は接続前に弾く。ロボットを動かしてから失敗するのを避ける。
    available = set(library.list_moves())
    unknown = [name for name in args.names if name not in available]
    if unknown:
        raise SystemExit(f"存在しないモーション名: {', '.join(unknown)}")

    moves = [(name, library.get(name)) for name in args.names]
    total = sum(move.duration for _, move in moves)
    print(f"再生予定: {len(moves)}件、合計 {total:.1f}秒", flush=True)
    for name, move in moves:
        sound = "音あり" if move.sound_path else "音なし"
        print(f"  {name} ({move.duration:.2f}秒, {sound})", flush=True)

    # 音を鳴らすモーションがあるならメディア経路を開く必要がある。顔追跡と同じ理由で、
    # "no_media" では音が鳴らない。
    use_sound = not args.no_sound
    media_backend = "default" if use_sound else "no_media"

    print("ローカルの Reachy Mini daemon に接続しています...", flush=True)
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend=media_backend,
    ) as mini:
        print(f"接続しました（media_backend={media_backend}）", flush=True)
        mini.enable_motors()
        # 待機姿勢では頭が下がっているため、正面へ上げてから再生する。
        mini.goto_target(head=create_head_pose(), duration=1.5)

        for remaining in range(args.countdown, 0, -1):
            print(f"  開始まで {remaining}秒...", flush=True)
            time.sleep(1.0)

        for index, (name, move) in enumerate(moves):
            print(f">>> [{index + 1}/{len(moves)}] {name} 再生開始", flush=True)
            started = time.monotonic()
            mini.play_move(
                move,
                initial_goto_duration=args.initial_goto,
                sound=use_sound,
            )
            elapsed = time.monotonic() - started
            print(f"    完了（実測 {elapsed:.2f}秒 / 定義 {move.duration:.2f}秒）", flush=True)
            if index + 1 < len(moves):
                time.sleep(args.gap)

        print("正面へ戻します。", flush=True)
        mini.goto_target(head=create_head_pose(), duration=1.0)

    print("完了しました。", flush=True)


if __name__ == "__main__":
    main()
