# hello-reachy-mini

Reachy Mini に接続して、頭とアンテナで挨拶する最初の Python プロジェクトです。

## 必要なもの

- 組み立てと初期設定が完了した Reachy Mini
- Reachy Mini Control が動作する Mac
- Python 3.11 以上（Reachy Mini SDK 1.10.0 の要件）
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

## HTTP REST で操作する

### 通常は daemon の REST を直接叩けば十分

Reachy Mini の daemon は `http://reachy-mini.local:8000` で **100 個のエンドポイント**を
公開しています。ESP32 のようなマイコンから操作したい場合、**追加のサーバーを立てずに
これを直接叩くのが一番簡単です**。

```bash
# ダンス再生（ボディ不要。データセット名のスラッシュは %2F にする）
curl -X POST "http://reachy-mini.local:8000/api/move/play/recorded-move-dataset/pollen-robotics%2Freachy-mini-dances-library/simple_nod"

# 頭とアンテナを動かす（roll/pitch/yaw で指定できる。単位はラジアン）
curl -X POST http://reachy-mini.local:8000/api/move/goto \
  -H 'Content-Type: application/json' \
  -d '{"head_pose":{"pitch":-0.3},"antennas":[0.7,-0.7],"duration":1.0}'

# 現在の状態（姿勢・アンテナ・胴体・制御モード・音源方向をまとめて）
curl http://reachy-mini.local:8000/api/state/full

# モーターモード（enabled / disabled / gravity_compensation）
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/gravity_compensation

# 顔追跡、音、音量
curl -X POST http://reachy-mini.local:8000/api/media/tracking/enable
curl -X POST http://reachy-mini.local:8000/api/media/play_sound -H 'Content-Type: application/json' -d '{"file":"wake_up.wav"}'
curl -X POST http://reachy-mini.local:8000/api/volume/set -H 'Content-Type: application/json' -d '{"volume":60}'
```

4x4 行列を組み立てる必要はありません。`head_pose` は `{x,y,z,roll,pitch,yaw}` で
受け付けます。補間方法も `linear` / `minjerk` / `ease_in_out` / `cartoon` から選べます。

エンドポイントの全体はブラウザで閲覧できます。公式ドキュメントサイトには記載が
ありませんが、daemon 自身が OpenAPI 定義を配信しています。

- http://reachy-mini.local:8000/docs — Swagger UI。「Try it out」でその場で試せる
- http://reachy-mini.local:8000/redoc — ReDoc。3カラムで全体を俯瞰しやすい
- http://reachy-mini.local:8000/openapi.json — 生の定義

このリポジトリにも控えを置いています。

- [`docs/daemon-rest-cheatsheet.md`](docs/daemon-rest-cheatsheet.md) — よく使うものを curl の例で
- [`docs/daemon-openapi.json`](docs/daemon-openapi.json) — 取得したまま無加工
- [`docs/daemon-openapi.yaml`](docs/daemon-openapi.yaml) — YAML 版

マイコンから使うときの注意は次の3点だけです。

- **単位はラジアン**。度で扱いたければ `deg * PI / 180` を計算する
- データセット名が長いので定数にしておく
- モーション再生は `uuid` を返す非ブロッキング方式。完了は `GET /api/move/running` で確認し、
  止めるときは `POST /api/move/stop` に uuid を渡す

### 動かないときは daemon の backend とモーターを確認する

`/api/move/...` が **HTTP 503 `Backend not running`** を返す場合、daemon の backend が
停止しています（Reachy Mini Control から停止したときに起こります）。

```bash
curl http://reachy-mini.local:8000/api/daemon/status                    # state を確認
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=false"
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled  # トルクON
```

`wake_up` クエリパラメータは必須です。また **backend が動いていてもモーターが
`disabled` だと、`goto` は uuid を返すのにロボットは動きません**（成功したように見えて
しまうので注意）。

### `reachy_proxy.py`（プロキシ実装・通常は不要）

`reachy_proxy.py` は本体上で動かす FastAPI のプロキシで、すべて GET の単純な REST を
公開します。**上記の daemon 直叩きで足りるため通常は不要**ですが、次のような場合には
使えます。

- 角度を**度**で受けたい（ラジアン変換をマイコン側に書きたくない）
- GET だけで済ませたい（POST と JSON ボディを避けたい）
- 複数操作をまとめた高レベルな API を作りたい

まず本体へ転送して起動します。

```bash
scp reachy_proxy.py pollen@reachy-mini.local:~/
ssh pollen@reachy-mini.local
source /venvs/apps_venv/bin/activate
python reachy_proxy.py        # 既定は 0.0.0.0:8080
```

同じネットワークから叩きます。

```bash
curl http://reachy-mini.local:8080/                       # エンドポイント一覧
curl http://reachy-mini.local:8080/moves                  # ダンス19種の一覧
curl "http://reachy-mini.local:8080/moves?library=emotions"   # 感情85種の一覧
curl "http://reachy-mini.local:8080/move/simple_nod"          # ダンス再生
curl "http://reachy-mini.local:8080/move/laughing1?library=emotions"  # 音付き
curl "http://reachy-mini.local:8080/move/dance2?library=emotions&wait=false"  # 待たない
curl "http://reachy-mini.local:8080/antennas?left=30&right=-30"
curl "http://reachy-mini.local:8080/body_yaw?deg=20"
curl "http://reachy-mini.local:8080/head?pitch=-10"
curl http://reachy-mini.local:8080/state                  # 現在の関節角と再生状態
curl http://reachy-mini.local:8080/cancel                 # 再生を中断
```

角度はすべて度で指定します。`wait=false` を付けると再生完了を待たずに応答が返るため、
長いモーション（最長19.76秒）でもマイコン側のタイムアウトを気にせず呼べます。完了は
`/state` の `playing` で確認できます。

マイコンからは2行で呼べます。

```cpp
http.begin("http://reachy-mini.local:8080/move/laughing1?library=emotions&wait=false");
http.GET();
```

FastAPI と uvicorn は本体の `apps_venv` に最初から入っているため、追加インストールは
不要です。

## ドキュメント

- [Reachy Mini Application 調査メモ](docs/reachy-mini-applications.md)
- [SDK 実機テストメモ](docs/sdk-test-notes.md)
- [検証タスク一覧](docs/tasks.md)
- [アイデアメモ](docs/ideas.md)
- [daemon REST API チートシート](docs/daemon-rest-cheatsheet.md)
- [M5Stack StopWatch 連携の引き継ぎプロンプト](docs/handoff-m5stack-controller.md)

公式資料: [Reachy Mini SDK Quickstart](https://huggingface.co/docs/reachy_mini/en/SDK/quickstart)
