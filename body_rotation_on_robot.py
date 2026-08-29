"""Rotate the body from side to side directly on a Wireless Reachy Mini."""

import math

from reachy_mini import ReachyMini


def main() -> None:
    print("ローカルの Reachy Mini daemon に接続しています...")
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="no_media",
    ) as mini:
        print("接続しました。胴体を左右に動かします。")
        mini.enable_motors()
        for angle in (0, 20, -20, 0):
            print(f"body_yaw = {angle} 度")
            mini.goto_target(body_yaw=math.radians(angle), duration=1.0)

    print("完了しました。")


if __name__ == "__main__":
    main()
