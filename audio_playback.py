"""Play a short macOS-generated voice through Reachy Mini."""

from reachy_mini import ReachyMini

from hello import speak_on_macos


def main() -> None:
    print("Reachy Mini の音声機能へ接続しています...")
    with ReachyMini(media_backend="default") as mini:
        print("スピーカーから音声を再生します。")
        speak_on_macos(mini, "こんにちは。リーチーミニです。")
    print("完了しました。")


if __name__ == "__main__":
    main()
