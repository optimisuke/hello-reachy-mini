"""Save one Reachy Mini camera frame as a JPEG."""

import signal
import time
from pathlib import Path

from reachy_mini import ReachyMini


OUTPUT = Path(__file__).with_name("camera_snapshot.jpg")


def timeout_handler(signum: int, frame: object) -> None:
    raise TimeoutError("カメラ接続が20秒以内に完了しませんでした")


def main() -> None:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(20)
    try:
        print("Reachy Mini のカメラへ接続しています...", flush=True)
        with ReachyMini(media_backend="default") as mini:
            for _ in range(50):
                jpeg = mini.media.get_frame_jpeg()
                if jpeg:
                    OUTPUT.write_bytes(jpeg)
                    print(f"保存しました: {OUTPUT}", flush=True)
                    return
                time.sleep(0.1)
            raise RuntimeError("カメラフレームを取得できませんでした")
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
