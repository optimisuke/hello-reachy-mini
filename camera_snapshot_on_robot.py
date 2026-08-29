"""Save one camera frame as a JPEG directly on a Wireless Reachy Mini."""

import argparse
import signal
import time
from pathlib import Path

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def timeout_handler(signum: int, frame: object) -> None:
    raise TimeoutError("カメラ接続が制限時間内に完了しませんでした")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default=str(Path.home() / "camera_snapshot_on_robot.jpg"),
        help="保存先のJPEGパス",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=0.0,
        help="撮影前の頭のピッチ角（度）。負の値で上向き",
    )
    parser.add_argument(
        "--no-lift",
        action="store_true",
        help="撮影前に頭を正面へ上げる処理を省略する",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="接続と取得の上限秒数",
    )
    args = parser.parse_args()
    output = Path(args.output)

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(args.timeout)
    started = time.monotonic()
    try:
        print("ローカルの Reachy Mini daemon に接続しています...", flush=True)
        with ReachyMini(
            connection_mode="localhost_only",
            media_backend="default",
        ) as mini:
            print(f"接続しました（{time.monotonic() - started:.1f}秒）", flush=True)
            if not args.no_lift:
                # 電源投入直後などは頭が下がっているため、撮影前に持ち上げる。
                print(f"頭を正面へ上げます（pitch={args.pitch}度）", flush=True)
                mini.enable_motors()
                mini.goto_target(
                    head=create_head_pose(pitch=args.pitch, degrees=True),
                    duration=1.5,
                )
                time.sleep(0.5)
            for attempt in range(50):
                jpeg = mini.media.get_frame_jpeg()
                if jpeg:
                    output.write_bytes(jpeg)
                    print(
                        f"保存しました: {output} "
                        f"({len(jpeg)} bytes, {attempt + 1}回目の取得, "
                        f"合計{time.monotonic() - started:.1f}秒)",
                        flush=True,
                    )
                    return
                time.sleep(0.1)
            raise RuntimeError("カメラフレームを取得できませんでした")
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
