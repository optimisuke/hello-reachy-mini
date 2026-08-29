"""Track a face for 30 seconds using Reachy Mini's daemon-side tracker."""

import time

from reachy_mini import ReachyMini
from reachy_mini.io.protocol import PlaySoundCmd
from reachy_mini.utils import create_head_pose


def play_marker(mini: ReachyMini, sound: str) -> None:
    """Play a built-in sound through the daemon without opening Mac media."""
    mini.client.send_command(PlaySoundCmd(file=sound))
    time.sleep(1.0)


def main() -> None:
    print("Reachy Mini に接続しています...", flush=True)
    # 顔追跡はdaemon側で動くが、tracker自身はカメラを開かず共有カメラフィードへ
    # unixfdsrcで接続する。"no_media" だとそのフィードが配信されず、detectedが
    # 永久にFalseのままになる。追跡にはメディア経路を開く必要がある。
    with ReachyMini(media_backend="default") as mini:
        mini.enable_motors()
        # Enabling torque pins the current pose. Wake the camera up from the
        # sleep/down pose before asking the daemon to look for a face.
        mini.goto_target(head=create_head_pose(), duration=1.5)
        play_marker(mini, "wake_up.wav")
        mini.start_head_tracking(weight=1.0)
        print("30秒間、顔を追跡します。顔を左右へ動かしてください。", flush=True)
        try:
            for _ in range(30):
                face = mini.get_tracked_face()
                print(
                    f"顔検出={face.detected} x={face.x} y={face.y}",
                    flush=True,
                )
                time.sleep(1.0)
        finally:
            mini.stop_head_tracking()
            mini.goto_target(head=create_head_pose(), duration=1.0)
            play_marker(mini, "go_sleep.wav")
    print("追跡を停止し、正面へ戻しました。", flush=True)


if __name__ == "__main__":
    main()
