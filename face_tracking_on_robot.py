"""Track a face with the daemon-side tracker, running on the robot itself."""

import argparse
import time

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds",
        type=int,
        default=30,
        help="追跡を続ける秒数",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="顔状態をポーリングする間隔（秒）",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=-10.0,
        help="追跡開始前の頭のピッチ角（度）。負の値で上向き",
    )
    parser.add_argument(
        "--media-backend",
        default="no_media",
        choices=["no_media", "default"],
        help=(
            "daemonのメディア経路。default にするとカメラフィードが開くため、"
            "tracker が unixfdsrc でフレームを受け取れるかを比較できる"
        ),
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=5,
        help="追跡開始前のカウントダウン秒数（顔を正面へ構える時間）",
    )
    parser.add_argument(
        "--weight",
        type=float,
        default=1.0,
        help="start_head_tracking の weight（1で頭の制御を追跡へ完全に委ねる）",
    )
    args = parser.parse_args()

    print("ローカルの Reachy Mini daemon に接続しています...", flush=True)
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend=args.media_backend,
    ) as mini:
        print(f"接続しました（media_backend={args.media_backend}）", flush=True)
        mini.enable_motors()
        # トルクONで現在の姿勢に固定されるため、追跡開始前に頭を上げてカメラを
        # 正面へ向ける。
        print(f"頭を正面へ上げます（pitch={args.pitch}度）", flush=True)
        mini.goto_target(
            head=create_head_pose(pitch=args.pitch, degrees=True),
            duration=1.5,
        )
        time.sleep(0.5)

        for remaining in range(args.countdown, 0, -1):
            print(f"  開始まで {remaining}秒... 顔をカメラの正面へ", flush=True)
            time.sleep(1.0)
        print(">>> 追跡開始（ここから顔を左右へ動かしてください）", flush=True)

        mini.start_head_tracking(weight=args.weight)
        print(
            f"{args.seconds}秒間、顔を追跡します。顔を左右へ動かしてください。",
            flush=True,
        )
        detected_count = 0
        samples = 0
        started = time.monotonic()
        try:
            while time.monotonic() - started < args.seconds:
                face = mini.get_tracked_face()
                samples += 1
                if face.detected:
                    detected_count += 1
                print(
                    f"[{time.monotonic() - started:5.1f}s] "
                    f"detected={face.detected} x={face.x} y={face.y} "
                    f"roll={face.roll} ts={face.ts}",
                    flush=True,
                )
                time.sleep(args.interval)
        finally:
            mini.stop_head_tracking()
            mini.goto_target(
                head=create_head_pose(pitch=args.pitch, degrees=True),
                duration=1.0,
            )

        rate = detected_count / samples * 100 if samples else 0.0
        print(
            f"検出率: {detected_count}/{samples} ({rate:.0f}%)",
            flush=True,
        )

    print("追跡を停止しました。", flush=True)


if __name__ == "__main__":
    main()
