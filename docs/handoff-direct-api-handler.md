# 引き継ぎプロンプト：直接API版ハンドラの実装

fork したリポジトリ `/Users/ito/Private/reachy_mini_conversation_app` で新しいセッションを
開き、以下をそのまま貼り付ける。

---

Reachy Mini の会話アプリ（このリポジトリ）を改造して、日本語で会話できるようにしたい。

## 背景（実機で検証済みの事実）

- このアプリの既定（`HF_REALTIME_CONNECTION_MODE=deployed`）は、HF がホストする
  `huggingface/speech-to-speech`（VAD→STT→LLM→TTS のカスケード）に WebSocket で接続する。
  アプリ自体は AI モデルを持たない Realtime クライアント。
- **その STT が日本語非対応**。実機で日本語を話すと `Ich hungere.`（ドイツ語）のように
  文字起こしされる。既定 STT は Parakeet TDT（25欧州言語、日本語なし）と見られる。
- `.env` の `REALTIME_TRANSCRIPTION_LANGUAGE=ja` は**効かない**（読み込みはログで確認済み）。
- `audio.input.transcription.model` は `"gpt-4o-transcribe"` がハードコードだが、
  OpenAI SDK の型が `Literal["whisper-1","gpt-4o-transcribe-latest","gpt-4o-mini-transcribe","gpt-4o-transcribe"]`
  に固定されているため、HF 側のモデル名は書けない。**飾りのフィールド**。
- 一方、**出力側は日本語 OK**。LLM は日本語で応答し、TTS は `voice='Ono_Anna'` で日本語を発話した。
  詰まっているのは入力 STT の1箇所だけ。

## やりたいこと

`ConversationHandler` を実装した新しいバックエンド（直接 API 呼び出し版）を追加し、
`main.py` の `build_handler` で環境変数で切り替えられるようにする。
Realtime プロトコルのサーバを立てず、ハンドラ内で直接 API を叩く。

### 構成

| 段 | 実装 | 状態 |
| --- | --- | --- |
| VAD | ハンドラ内。`webrtcvad` か silero-onnx（torch は使わない） | 未 |
| STT | OpenAI `gpt-transcribe`（`/v1/audio/transcriptions`、$0.0045/分） | 未 |
| LLM | HF router `Qwen/Qwen3-4B-Instruct-2507`（`https://router.huggingface.co/v1`、入力 $0.01/1M） | **検証済** |
| TTS | OpenAI `gpt-4o-mini-tts`、または ローカル Kokoro(82M) | 未 |

LLM は実機から検証済み：日本語応答 OK、`dance` ツールの Function Calling OK、SSE ストリーム OK。
HF router に OpenAI 互換の `/v1/audio/speech` と `/v1/audio/transcriptions` は**存在しない**（404）。

### 実装すべき抽象メソッド（`conversation_handler.py`、159行）

```
_is_connected() / start_up() / shutdown()
receive(frame: AudioFrame)   ← マイク音声。ここに VAD を置く
say(text)
apply_personality(profile) / get_available_voices() / get_current_voice() / change_voice()
```

`emit()` と文字起こし通知（`_emit_transcript`）は基底クラスが実装済み。

### 制約・方針

- **既存の deployed 動作を壊さない。**環境変数で `deployed` / `direct` を切り替え、
  日本語が駄目なら戻せるようにする。
- `huggingface_realtime.py`（1,069行）は消さずに残し、参照実装として使う。
- ボイス名は自分のハンドラ内で好きにマップできる（`config.py` の `HF_AVAILABLE_VOICES` は
  Qwen3-TTS のスピーカー名なので、直接API版では別の扱いにしてよい）。
- プロファイル（`profiles/*/profile.md`）の `You speak English by default and switch
  languages only if explicitly told.` は日本語で話す指示に差し替える。バンドル品は
  直接編集せず複製する。

## 実機の情報

- SSH: `ssh pollen@reachy-mini.local`（鍵認証済み。パスワードは `root`）
- ハード: Raspberry Pi CM4、4コア、RAM 3.7Gi（available 3.3Gi）、ディスク空き 4.3G
- アプリのインスタンスパス＝**site-packages 内**
  `/venvs/apps_venv/lib/python3.12/site-packages/reachy_mini_conversation_app/`
  ここに `.env` / `startup_settings.json` / `memory.v1.json` が置かれる。
  **アプリ更新で消えるので、設定はリポジトリ側で管理する。**
- デプロイ: rsync でロボットへ送り、`/venvs/apps_venv/bin/pip install <dir>`。
  起動/停止は `curl -X POST http://localhost:8000/api/apps/{start-app/<name>,stop-current-app}`
- ログ: `journalctl -u reachy-mini-daemon -f`
  - `console:899 | role=user content=...` ← **STT の文字起こし結果。切り分けの要点**
  - `console:899 | role=assistant content=...` ← LLM の応答
  - `huggingface_realtime:777/848 | Turn latency: ... ms after user transcript`
  - `utils:114 | Loaded instance configuration from ...` ← `.env` が読まれた証拠

## 参照

- 調査の全記録: `/Users/ito/Private/hello-reachy-mini/docs/sdk-test-notes.md`
  （実機検証、コスト見積もり、選択肢の比較と却下理由、ログの見方）
- 日本語記事サーベイ: `/Users/ito/Private/hello-reachy-mini/docs/ja-articles-survey.md`
- `speech-to-speech` の参照実装（プロトコル以外の細部で参考になる）:
  `git clone --depth 1 https://github.com/huggingface/speech-to-speech.git`
  - `src/speech_to_speech/VAD/` … VAD の閾値処理
  - `src/speech_to_speech/api/openai_realtime/handlers/response.py` … 割り込みの畳み方
  - `docs/openai-compatible-stt.md` … `/v1/audio/transcriptions` の使い方

## 最初にやってほしいこと

いきなり実装せず、まず `conversation_handler.py` と `huggingface_realtime.py` を読んで、
`receive()` から `emit()` までの音声の流れと、ツール呼び出しの往復を把握してほしい。
そのうえで実装計画を立てて、plan mode で提示して。

作業中に得た知見（期待と実際の挙動の違い、ハマりどころ、実機固有の注意点）は
`/Users/ito/Private/hello-reachy-mini/docs/sdk-test-notes.md` に、
「現象・原因・解決・学び」の形で追記していってほしい。
