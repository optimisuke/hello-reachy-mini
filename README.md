# hello-reachy-mini

Reachy Mini に接続して、頭とアンテナで挨拶する最初の Python プロジェクトです。

## 必要なもの

- 組み立てと初期設定が完了した Reachy Mini
- Reachy Mini Control が動作する Mac
- Python 3.10 以上
- [`uv`](https://docs.astral.sh/uv/)（推奨）

実行前に Reachy Mini Control で起動中の App を停止してください。App と Python
スクリプトは同時にロボットを操作できません。

## セットアップ

```bash
uv sync --frozen
```

## 実行

Reachy Mini Control を起動してロボットへ接続した状態で実行します。

```bash
uv run --frozen python hello.py
```

Reachy Mini が正面を向き、頭を傾けながらアンテナを振ったあと、正面の姿勢へ
戻ります。SDK が USB 接続とネットワーク接続を自動判定します。

### 音声付きで実行する

macOS の `say` で挨拶音声を WAV（16 kHz・16 bit PCM）として一時生成し、
Reachy Mini のスピーカーで再生します。Wireless 版では SDK が WebRTC 接続を
自動的に使用します。

```bash
uv run --frozen python hello.py --voice
```

音声ストリーミングが利用できない構成でも、エラーを表示してモーションは最後まで
実行します。`No Reachy Mini Audio USB device found` に続いて
`GstWebRTCClient initialized` と表示される場合、Wireless 版の WebRTC 接続へ正常に
切り替わっているため、USB Audio のメッセージは問題ありません。

## トラブルシューティング

- 接続できない: Reachy Mini Control でロボットがオンラインか確認する
- ロボットが動かない: `Applications` で実行中の App を停止する
- Lite 版: Reachy Mini Control を開いたままにして daemon を動作させる
- Wireless 版: Mac と Reachy Mini を同じネットワークへ接続する
- 音声アップロードが HTTP 400 になる: 最新の `hello.py` が WAV を生成しているか確認する

## Wireless 本体上で実行する

`hello_on_robot.py` は、Wireless 版に内蔵された Raspberry Pi（CM4）上で直接動かす
スクリプトです。Mac からネットワーク越しに操作せず、本体内の daemon へ
`localhost` で接続します。

まずMacからスクリプトを転送します。

```bash
scp hello_on_robot.py pollen@reachy-mini.local:~/hello_on_robot.py
```

続いてReachy MiniへSSH接続します。

```bash
ssh pollen@reachy-mini.local
```

Reachy Mini内のアプリ用Python環境を有効化し、スクリプトを実行します。

```bash
source /venvs/apps_venv/bin/activate
python ~/hello_on_robot.py
```

このスクリプトでは `connection_mode="localhost_only"` を指定しているため、必ず
Reachy Mini本体内のdaemonへ接続します。実行前に起動中のAppを停止してください。

## ドキュメント

- [Reachy Mini Application 調査メモ](docs/reachy-mini-applications.md)

公式資料: [Reachy Mini SDK Quickstart](https://huggingface.co/docs/reachy_mini/en/SDK/quickstart)
