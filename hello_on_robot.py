"""Run a small greeting directly on a Wireless Reachy Mini."""

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def main() -> None:
    print("ローカルの Reachy Mini daemon に接続しています...")
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="no_media",
    ) as mini:
        print("接続しました。挨拶します！")
        mini.enable_motors()
        mini.goto_target(
            head=create_head_pose(),
            antennas=[0.0, 0.0],
            duration=1.0,
        )
        mini.goto_target(
            head=create_head_pose(roll=8.0, degrees=True),
            antennas=[0.5, -0.5],
            duration=0.5,
        )
        mini.goto_target(
            head=create_head_pose(roll=-8.0, degrees=True),
            antennas=[-0.5, 0.5],
            duration=0.5,
        )
        mini.goto_target(
            head=create_head_pose(),
            antennas=[0.0, 0.0],
            duration=1.0,
        )

    print("完了しました。")


if __name__ == "__main__":
    main()
