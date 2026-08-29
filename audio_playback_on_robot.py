"""Play a bundled WAV through the speaker directly on a Wireless Reachy Mini."""

import argparse
import time
from pathlib import Path

import reachy_mini
from reachy_mini import ReachyMini


def default_sound() -> Path:
    """Return a WAV bundled with the installed reachy_mini package."""
    return Path(reachy_mini.__file__).parent / "assets" / "wake_up.wav"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sound",
        nargs="?",
        help="再生する WAV のパス（省略時は内蔵の wake_up.wav）",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=3.0,
        help="再生完了を待つ秒数（play_sound は非ブロッキング）",
    )
    args = parser.parse_args()

    sound = Path(args.sound) if args.sound else default_sound()
    if not sound.is_file():
        raise SystemExit(f"WAV が見つかりません: {sound}")

    print(f"再生する音源: {sound}")
    print("ローカルの Reachy Mini daemon に接続しています...")
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="default",
    ) as mini:
        print("接続しました。スピーカーから再生します。")
        mini.media.play_sound(str(sound))
        # play_sound は非ブロッキングなので、再生中は接続を維持する。
        time.sleep(args.wait)

    print("完了しました。")


if __name__ == "__main__":
    main()
