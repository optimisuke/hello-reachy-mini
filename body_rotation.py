"""Rotate Reachy Mini's body gently from side to side."""

import math

from reachy_mini import ReachyMini


def main() -> None:
    print("Reachy Mini に接続しています...")
    with ReachyMini(media_backend="no_media") as mini:
        mini.enable_motors()
        print("胴体を左右に動かします。")
        for angle in (0, 20, -20, 0):
            mini.goto_target(body_yaw=math.radians(angle), duration=1.0)
    print("完了しました。")


if __name__ == "__main__":
    main()
