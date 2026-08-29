"""Record from the microphone and save a WAV, running on the robot itself.

`media.get_audio_sample()` は float32 の配列を返す。WAV へ保存するため 16bit PCM へ
変換する。録音後にそのまま再生して内容を確認できる。
"""

import argparse
import time
import wave
from pathlib import Path

import numpy as np

import reachy_mini
from reachy_mini import ReachyMini


# 合図に使う内蔵音源。長さは wake_up 0.41秒、count 0.66秒、go_sleep 3.60秒。
ASSETS = Path(reachy_mini.__file__).parent / "assets"
CUE_START = ASSETS / "wake_up.wav"
CUE_END = ASSETS / "count.wav"


def play_cue(mini: ReachyMini, sound: Path, wait: float) -> None:
    """Play a short built-in sound and wait for it to finish.

    play_sound は非ブロッキングなので、鳴り終わるまで待たないと合図音が録音へ
    混ざる。
    """
    mini.media.play_sound(str(sound))
    time.sleep(wait)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default=str(Path.home() / "mic_recording.wav"),
        help="保存先のWAVパス",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help="録音する秒数",
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=3,
        help="録音開始前のカウントダウン秒数",
    )
    parser.add_argument(
        "--playback",
        action="store_true",
        help="録音後にスピーカーから再生する",
    )
    parser.add_argument(
        "--no-cue",
        action="store_true",
        help="録音の開始・終了を知らせる合図音を鳴らさない",
    )
    args = parser.parse_args()
    output = Path(args.output)

    print("ローカルの Reachy Mini daemon に接続しています...", flush=True)
    with ReachyMini(
        connection_mode="localhost_only",
        media_backend="default",
    ) as mini:
        rate = mini.media.get_input_audio_samplerate()
        channels = mini.media.get_input_channels()
        print(f"接続しました。入力: {rate} Hz / {channels} ch", flush=True)

        for remaining in range(args.countdown, 0, -1):
            print(f"  録音開始まで {remaining}秒...", flush=True)
            time.sleep(1.0)

        if not args.no_cue:
            # 合図音が録音へ混ざらないよう、鳴り終わってから録音を始める。
            print("  ピッと鳴ったら話してください。", flush=True)
            play_cue(mini, CUE_START, 1.0)

        print(f">>> 録音開始（{args.seconds}秒）。話してください。", flush=True)
        chunks: list[np.ndarray] = []
        empty = 0
        mini.media.start_recording()
        started = time.monotonic()
        try:
            while time.monotonic() - started < args.seconds:
                sample = mini.media.get_audio_sample()
                if sample is None:
                    empty += 1
                    time.sleep(0.01)
                    continue
                chunks.append(np.asarray(sample, dtype=np.float32))
        finally:
            mini.media.stop_recording()
        print("<<< 録音終了", flush=True)
        if not args.no_cue:
            play_cue(mini, CUE_END, 1.0)

        if not chunks:
            raise SystemExit(
                f"音声サンプルを取得できませんでした（None を {empty} 回受信）"
            )

        audio = np.concatenate([chunk.reshape(-1) for chunk in chunks])
        frames = audio.size // channels
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
        print(
            f"取得: {len(chunks)}チャンク / {audio.size}サンプル "
            f"（{frames / rate:.2f}秒相当, None受信 {empty}回）",
            flush=True,
        )
        print(f"音量: ピーク {peak:.4f} / RMS {rms:.4f}", flush=True)
        if peak < 0.001:
            print("警告: ほぼ無音です。マイクが拾えていない可能性があります。", flush=True)

        # float32 (-1.0〜1.0) を 16bit PCM へ変換して保存する。
        pcm = np.clip(audio, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)
        with wave.open(str(output), "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(pcm.tobytes())
        print(f"保存しました: {output} ({output.stat().st_size} bytes)", flush=True)

        if args.playback:
            print("録音した音声を再生します。", flush=True)
            mini.media.play_sound(str(output))
            time.sleep(frames / rate + 1.5)

    print("完了しました。", flush=True)


if __name__ == "__main__":
    main()
