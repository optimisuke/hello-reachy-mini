# hello-reachy-mini

Reachy Mini（Wireless版）を Python と REST API から動かす検証プロジェクトです。挨拶
モーションから始めて、カメラ・音声・マイク・顔追跡・ダンス・アンテナ入力まで実機で
確認しています。

Mac からネットワーク越しに動かすスクリプトと、本体内蔵の Raspberry Pi（CM4）上で直接
動かす `*_on_robot.py` を対にして置いてあります。マイコンから操作する場合は
[HTTP REST で操作する](#http-rest-で操作する)を参照してください。

## スクリプト一覧

| 機能 | Mac から | 本体上で | 内容 |
| --- | --- | --- | --- |
| 挨拶 | `hello.py` | `hello_on_robot.py` | 頭とアンテナで挨拶。`--voice` で音声付き |
| 胴体回転 | `body_rotation.py` | `body_rotation_on_robot.py` | 胴体を左右 20° 回転 |
| 音声再生 | `audio_playback.py` | `audio_playback_on_robot.py` | WAV をスピーカーで再生 |
| カメラ | `camera_snapshot.py` | `camera_snapshot_on_robot.py` | 静止画を JPEG で保存 |
| 顔追跡 | `face_tracking.py` | `face_tracking_on_robot.py` | daemon 側の顔追跡で頭を追従 |
| モーション再生 | — | `recorded_moves_on_robot.py` | ダンス19種・感情85種を再生 |
| アンテナ入力 | — | `antenna_input_on_robot.py` | アンテナを手で動かして角度を読む |
| マイク録音 | — | `mic_recording_on_robot.py` | 録音して WAV 保存・再生 |
| REST プロキシ | — | `reachy_proxy.py` | HTTP で操作する層（通常は不要） |

引数を持つスクリプト（`recorded_moves_on_robot.py`、`camera_snapshot_on_robot.py`、
`face_tracking_on_robot.py`、`antenna_input_on_robot.py`、`mic_recording_on_robot.py`、
`audio_playback_on_robot.py`、`reachy_proxy.py`、`hello.py`）は `--help` で確認できます。

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
- ロボットが動かない: 実行中の App を停止し、移動前に `enable_motors()` を呼ぶ。
  接続に成功していてもモーターが無効だと動かない
- 顔追跡で `detected` が常に `False`: `media_backend` を既定（`"default"`）にする。
  daemon 側の顔追跡は共有カメラフィードに接続する実装なので、`"no_media"` では
  フレームが 1 枚も届かず、頭も動かない
- カメラの画角がおかしい: 待機姿勢では頭が下がっているため、撮影前に
  `goto_target(head=create_head_pose(pitch=...))` で正面へ上げる
- 音が鳴らない: モーションのみなら `"no_media"` でよいが、音やカメラを使うなら
  既定のままにする。`play_sound()` は非ブロッキングなので、再生中は接続を維持する
- REST で `Backend not running`（503）: 下記
  [動かないときは daemon の backend とモーターを確認する](#動かないときは-daemon-の-backend-とモーターを確認する)
- Lite 版: Reachy Mini Control を開いたままにして daemon を動作させる
- Wireless 版: Mac と Reachy Mini を同じネットワークへ接続する
- `No Reachy Mini Audio USB device found` は Wireless 版ではエラーではない。
  続いて `GstWebRTCClient initialized` と出れば WebRTC 経路へ正常に切り替わっている
- 本体上での実行で onnxruntime の GPU 警告（`/sys/class/drm/card0`）が出るのは無害。
  CM4 に GPU デバイスノードが無いため

## Wireless 本体上で実行する

`*_on_robot.py` は、Wireless 版に内蔵された Raspberry Pi（CM4）上で直接動かす
スクリプトです。Mac からネットワーク越しに操作せず、本体内の daemon へ `localhost` で
接続します（`connection_mode="localhost_only"`）。ネットワークを経由しないため速く、
カメラ接続は Mac 経由の約5秒に対して 0.4 秒でした。

### 最初に SSH 鍵を登録する

初期状態はパスワード認証のみなので、一度だけ鍵を登録しておくと以降のテストが楽になります
（デフォルトのユーザー名は `pollen`、パスワードは `root`）。

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub pollen@reachy-mini.local
```

### 転送して実行する

```bash
scp hello_on_robot.py pollen@reachy-mini.local:~/
ssh pollen@reachy-mini.local 'source /venvs/apps_venv/bin/activate && python -u ~/hello_on_robot.py'
```

`python` に `-u` を付けると、SSH 越しでも `print` が即座に流れてくるので進行が追えます。
本体の `apps_venv` は Python 3.12 系です（システムの `python3` は 3.13 系なので、
バージョンを確認するときは venv を有効化してから見てください）。

実行前に起動中の App を停止してください。停止は REST からもできます。

```bash
curl http://reachy-mini.local:8000/api/apps/current-app-status   # 実行中のApp（無ければ null）
curl -X POST http://reachy-mini.local:8000/api/apps/stop-current-app
```

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

検証と設計のメモ

- [SDK 実機テストメモ](docs/sdk-test-notes.md) — 現象・原因・解決・学びの形で記録した本体
- [検証タスク一覧](docs/tasks.md) — 済みと未着手の整理、優先度
- [アイデアメモ](docs/ideas.md) — マイコン連携、日本語会話、絵の講評

API リファレンス

- [daemon REST API チートシート](docs/daemon-rest-cheatsheet.md) — よく使う操作を curl の例で
- [`docs/daemon-openapi.json`](docs/daemon-openapi.json) / [`.yaml`](docs/daemon-openapi.yaml) — 実機から取得した OpenAPI 定義
- [Reachy Mini Application 調査メモ](docs/reachy-mini-applications.md)

会話アプリの日本語対応

- [バックエンド調査と実装方針](docs/handoff-direct-api-handler.md)
- [モデル選定の実測記録](docs/model-benchmarks.md)
- [日本語技術記事サーベイ](docs/ja-articles-survey.md)

別リポジトリ

- `reachy-m5-remote` — M5Stack StopWatch から操作するファームウェア。
  引き継ぎ資料は [`docs/handoff-m5stack-controller.md`](docs/handoff-m5stack-controller.md)

公式資料: [Reachy Mini SDK Quickstart](https://huggingface.co/docs/reachy_mini/en/SDK/quickstart)
