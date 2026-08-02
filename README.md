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
uv sync
```

## 実行

Reachy Mini Control を起動してロボットへ接続した状態で実行します。

```bash
uv run python hello.py
```

Reachy Mini が正面を向き、頭を傾けながらアンテナを振ったあと、正面の姿勢へ
戻ります。SDK が USB 接続とネットワーク接続を自動判定します。

### 音声付きで実行する

macOS の `say` で挨拶音声を生成し、Reachy Mini のスピーカーで再生します。

```bash
uv run python hello.py --voice
```

音声ストリーミングが利用できない構成でも、エラーを表示してモーションは最後まで
実行します。特に Wireless 版へ Mac から接続する場合は、SDK の WebRTC 対応状況に
よって音声が再生できないことがあります。

## トラブルシューティング

- 接続できない: Reachy Mini Control でロボットがオンラインか確認する
- ロボットが動かない: `Applications` で実行中の App を停止する
- Lite 版: Reachy Mini Control を開いたままにして daemon を動作させる
- Wireless 版: Mac と Reachy Mini を同じネットワークへ接続する

公式資料: [Reachy Mini SDK Quickstart](https://huggingface.co/docs/reachy_mini/en/SDK/quickstart)

