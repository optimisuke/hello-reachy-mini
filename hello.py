"""Make Reachy Mini greet with a small, safe motion."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def greet_with_motion(mini: ReachyMini) -> None:
    """Look forward, tilt the head, wiggle the antennas, then reset."""
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


def speak_on_macos(mini: ReachyMini, message: str) -> None:
    """Generate speech with macOS and play it through Reachy Mini."""
    say = shutil.which("say")
    if say is None:
        raise RuntimeError("macOS の say コマンドが見つかりません")

    with tempfile.TemporaryDirectory(prefix="hello-reachy-mini-") as tmp_dir:
        audio_path = Path(tmp_dir) / "hello.aiff"
        subprocess.run(
            [say, "-o", str(audio_path), message],
            check=True,
        )
        mini.media.play_sound(str(audio_path))
        # play_sound is non-blocking; keep the connection alive during playback.
        time.sleep(3.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Reachy Mini のスピーカーで挨拶する（macOS）",
    )
    args = parser.parse_args()

    media_backend = "default" if args.voice else "no_media"
    print("Reachy Mini に接続しています...")
    with ReachyMini(media_backend=media_backend) as mini:
        print("接続しました。挨拶します！")
        greet_with_motion(mini)

        if args.voice:
            try:
                speak_on_macos(mini, "こんにちは。リーチーミニです。")
            except Exception as exc:
                print(f"音声は再生できませんでした: {exc}")

    print("完了しました。")


if __name__ == "__main__":
    main()
