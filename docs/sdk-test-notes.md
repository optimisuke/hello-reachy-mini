# Reachy Mini SDK 実機テストメモ

技術記事へ加工するための素材。事実と推測を分けて記録する。

## 記録カテゴリ

- SDK・API
- 実機・ハードウェア
- 実行環境・依存関係
- 接続・デプロイ
- Codexの制約・学び
- 記事化の観点
- 未解決・要検証

各項目は複数カテゴリにまたがってよい。Reachy Mini側の現象とCodex側の実行制約は
混同しない。

## 実行環境と構成

- Macからの遠隔操作には `hello.py` を使う
- Wireless版の本体内（Raspberry Pi CM4）での実行には `hello_on_robot.py` を使う
- 本体内では `connection_mode="localhost_only"` で本体のdaemonへ接続する
- 本体のアプリ用Python環境は `/venvs/apps_venv`

## MacからWireless版を操作するときの通信経路

### カテゴリ

SDK・API / 接続・デプロイ / 記事化の観点

Mac上のPythonコードは、用途ごとに複数の通信方式を使う。

- 頭、アンテナ、胴体などの操作命令と状態通知:
  `ws://reachy-mini.local:8000/ws/sdk` のWebSocket
- カメラ映像とリアルタイム音声ストリーム: WebRTC
- 音声ファイルのアップロードと再生開始:
  daemonのHTTP REST API（`/api/media/sounds/upload` と `/api/media/play_sound`）
- WebRTC接続の相手探し・接続交渉（シグナリング）にもWebSocketを使う

### 学び

- Python SDKからのすべての通信がWebRTCになるわけではない
- HTTPは要求と応答、WebSocketは常時接続の双方向命令、WebRTCは低遅延な映像・音声に
  向くという役割分担
- WebRTCは単一の通信線というより、接続交渉、NAT越え、暗号化された映像・音声転送などを
  組み合わせた仕組み
- `ReachyMini(media_backend="no_media")` ではメディア経路を初期化せず、操作用WebSocketのみを
  使うため、モーションテストの接続が軽い

## Wireless本体上でPythonを動かす場合

### カテゴリ

SDK・API / 実行環境・依存関係 / 接続・デプロイ / 記事化の観点

Pythonスクリプトとハードウェア制御daemonは、同じCM4上でも別プロセスとして動く。

```text
本体上のPythonスクリプト
  └─ localhostのWebSocket
       └─ Reachy Mini daemon
            └─ モーター制御バス
                 └─ 頭・胴体・アンテナ
```

- `hello_on_robot.py` は `connection_mode="localhost_only"` と
  `media_backend="no_media"` を指定している
- そのため、モーション命令は本体内のlocalhost WebSocketを通る
- Wi-FiやWebRTCは使わないが、SDKとdaemon間は引き続きプロトコルベース
- カメラや音声を本体上で使う場合は、WebRTCではなくローカルIPCや本体の音声デバイスを
  使えるため、ネットワーク越しより経路が短い

### 学び

- 「本体上で実行する」と「Pythonがモーターを直接駆動する」は同じではない
- daemonを境界にすることで、Mac実行と本体実行でほぼ同じSDKコードを再利用できる
- 本体実行の利点は低遅延、Wi-Fi非依存、メディアへの直接アクセス。欠点はCM4の計算資源が
  Macより小さいこと

## 初回の `uv run`

### 現象

初回の `uv run --frozen python hello.py` は実行開始まで約1分かかり、多数のパッケージを
ダウンロードした。

### 原因と学び

- `.venv` がなかったため、`uv run` が仮想環境を作成した
- `uv.lock` に固定された `reachy-mini` SDKと依存パッケージを初回に自動取得した
- GStreamer関連などを含むためダウンロード量が大きい
- 2回目以降は作成済み環境を再利用するため、実行は数秒で完了した

## 接続成功でもロボットが動かない

### 現象

SDKは「接続しました」「完了しました」と正常終了したが、実機は動かなかった。

### 原因

起動中のAppを停止したあと、モーターが無効な状態だった。daemonはモーター無効時にも
移動命令を受理し、エラーを返さず完了できる。

### 解決

移動命令より前に次を実行した。

```python
mini.enable_motors()
```

Mac版と本体版の両方へ追加したところ、挨拶モーションが動作した。

### 学び

「SDK接続成功」「移動タスク正常完了」「実機が物理的に動く」は別々に確認する必要がある。

## Wireless版へのSSH接続

- 接続先: `pollen@reachy-mini.local`（環境によっては `reachy-mini` でも可）
- 公式ドキュメント記載のデフォルトユーザー名: `pollen`
- 公式ドキュメント記載のデフォルトパスワード: `root`
- 当初パスワードを `pollen` と推測したが失敗。公式Quickstartで `root` と確認した
- 本体へSSH接続し、`apps_venv` を有効化した実行でモーション動作を確認した

```bash
source /venvs/apps_venv/bin/activate
python ~/hello_on_robot.py
```

## Codex実行環境からのSSH/SCP

### 現象

Codexから `scp` を実行しようとしたが、Reachy Miniへ通信する前に承認処理の403エラーで
拒否された。一方、ユーザー自身のMacターミナルからは転送・SSH接続できた。

### 学び

- Codexから外部機器へ接続・書き込みする操作は、サンドボックス外実行の追加承認対象になる
- `.sh` やAnsibleで包んでも、その中のSSH通信に必要な権限は変わらない
- 今回はReachy MiniやSSH認証ではなく、Codex側の承認サービス障害だった

## 鍵認証でエージェントから本体実行を自動化する（成功・2026-08-29）

### カテゴリ

接続・デプロイ / 実行環境・依存関係

### 現象

Claude Code から `hello_on_robot.py` を本体上で実行しようとしたが、SSHが
`Permission denied (publickey,password)` で失敗した。ロボット自体はオンラインで、
`ping` は応答し、daemonのHTTP（`http://reachy-mini.local:8000/`）も200を返していた。

### 原因

初期状態の本体はパスワード認証しか使えない。エージェントのBashは対話的な
パスワード入力ができないため、`ssh` も `scp` もその場で止まる。ロボット側の障害では
なく、認証方式とエージェント実行環境の組み合わせの問題。

### 解決

ユーザーがMacのターミナルから一度だけ公開鍵を登録した。

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub pollen@reachy-mini.local
```

パスワード（デフォルト `root`）の入力はこの1回だけで済む。以降は
`~/.ssh/authorized_keys` の鍵で認証されるため、エージェントから
`scp` → `ssh` → 実行までを非対話で一括実行できるようになった。

```bash
scp hello_on_robot.py pollen@reachy-mini.local:~/hello_on_robot.py
ssh pollen@reachy-mini.local 'source /venvs/apps_venv/bin/activate && python -u ~/hello_on_robot.py'
```

2回連続で実行し、いずれも終了コード0でモーション（正面→左右へ首を傾けアンテナを振る
→正面）が完走した。出力も同一で、再現性がある。

### 実機で分かったこと

- 本体の `apps_venv` のPythonは3.12.12で、Mac側の検証環境（3.12）と同じマイナー
  バージョン。一方、本体のシステムPython（`python3`）は3.13.5で別物
- venvを有効化せずに `python3 -V` を見ると3.13.5が返るため、実行に使われる
  バージョンと混同しやすい。`source /venvs/apps_venv/bin/activate` の後に
  `python -V` で確認する
- `/venvs/` には `apps_venv` と `mini_daemon` の2つがあり、どちらもPython 3.12系
- 実行のたびに次の警告が2行出るが無害。CM4にGPUのデバイスノードが無く、
  ONNX RuntimeのGPU探索が失敗しているだけで、モーションは正常に完走する

```text
[W:onnxruntime:Default, device_discovery.cc:283 GetGpuDevices] Failed to detect devices under "/sys/class/drm/card0"
```

- `python` に `-u` を付けると、SSH越しでも `print` が即座に流れてくるため進行が追える

### 学び

- 「エージェントから実機を動かせるか」は、SDKやネットワークではなく認証方式で決まる。
  鍵登録は最初の1回だけの作業で、以降の検証サイクルが大幅に短くなる
- 切り分けの順序が有効だった。`ping`（到達性）→ daemonのHTTP（サービス生存）→
  SSH（認証）と分けると、ロボット側の障害か認証の問題かを即断できる
- 過去にCodexで同じ操作が承認エラーで止まった事例と混同しないこと。今回は承認では
  通っており、失敗点は本体側の認証方式だった

### 記事化の観点

- 「ロボットは生きているのに繋がらない」ときの切り分け手順（到達性・サービス・認証）
- エージェントに実機を触らせる前提条件としてのSSH鍵登録
- onnxruntimeのGPU警告は無視してよい、という初学者が不安になりやすいポイント
- バージョン確認は必ずvenv有効化後に行う。システムPythonとvenvのPythonが
  違うため、有効化前の `python3 -V` を実行環境と誤認しやすい（実際に誤認した）

## 胴体回転

- 確認日: 2026-08-29
- 使用スクリプト: `body_rotation.py`
- 動作: 胴体を 0° → 20° → -20° → 0° の順に回転
- 実機で確認した挙動: 胴体の回転中、首が逆方向へ補正され、頭は正面を保っているように見える
- `ReachyMini` の `automatic_body_yaw` は既定値の `True`
- スクリプトから頭の目標姿勢は明示的に送っていない
- 上記の首補正は目視結果。`automatic_body_yaw` との因果関係は推測であり、明示的に
  `False` にした比較テストが必要

### 本体上での実行（成功・2026-08-29）

`body_rotation_on_robot.py` として on-robot 版を作成し、鍵認証経由で転送・実行した。
終了コード0で完走し、胴体は 0° → 20° → -20° → 0° と各1秒で動いた。

Mac版 `body_rotation.py` との差分は3点のみで、モーションのコードは一切変えていない。

- `connection_mode="localhost_only"` を追加（本体内daemonへ直結する）
- 各ステップで `body_yaw` をprint（SSH越しに進行を追うため）
- 接続メッセージをon-robot向けに変更

学び。

- Mac向けスクリプトのon-robot移植は、接続引数の変更だけで済む場合がある。
  SDKのモーションAPIは接続モードに依存しない
- `media_backend="no_media"` はMac版と共通でよい。モーションだけならカメラ・音声の
  初期化は不要
- ここでもonnxruntimeのGPU警告は出るが無害（[鍵認証の項](#鍵認証でエージェントから本体実行を自動化する成功2026-08-29)と同じ）

## 音声再生（解決 2026-08-30・原因は未確定）

### カテゴリ

SDK・API / 接続・デプロイ / Codexの制約・学び / 未解決・要検証

### 試したこと

- Macの `say` で16 kHz・16 bit PCMのWAVを一時生成
- `ReachyMini(media_backend="default")` でWireless版へ接続
- `mini.media.play_sound()` で本体スピーカーからの再生を試行

### 現象

- 約90秒待っても音声は聞こえなかった
- 標準出力もなく、Pythonプロセスが終了しなかった
- モーションのみの `media_backend="no_media"` は数秒で正常に動作している

### 現時点の判断

- 初回テストは出力をflushしていなかったため、どの処理で停止したか断定できない
- 後続のカメラ取得では同じ `media_backend="default"` のWebRTC接続が約5秒で成功した
- したがって、WebRTC接続全体の不調という当初の推測は弱くなった。音声送信、
  `play_sound()`、終了処理のどこで止まるかをflush付きログで切り分ける必要がある
- 原因は未確定。Reachy Mini Controlとの競合、既存セッション、daemonまたはSDKのログを
  次回確認する

### Codex側で発生した別問題

- 固まったテストプロセスのPIDは確認できた
- ユーザーから終了許可を得たが、Codexの追加承認サービスが403を返し `kill` は未実行
- これは音声が鳴らなかった原因とは別であり、Codex実行環境の制約として切り分ける

### 本体上での再生は成功した（2026-08-29）

切り分けの決め手になった結果。`audio_playback_on_robot.py` を作り、本体上で
`connection_mode="localhost_only"` + `media_backend="default"` で内蔵音源を再生したら、
実機のスピーカーから「ぴぽっ」と鳴り、プロセスも終了コード0で正常終了した。

```bash
ssh pollen@reachy-mini.local \
  'source /venvs/apps_venv/bin/activate && python -u ~/audio_playback_on_robot.py'
```

再生した音源は、インストール済みパッケージに同梱されたWAV。パスを直書きせず
`Path(reachy_mini.__file__).parent / "assets" / "wake_up.wav"` で解決している。

- 内蔵音源: `/venvs/apps_venv/lib/python3.12/site-packages/reachy_mini/assets/wake_up.wav`
  （`go_sleep.wav` も同じディレクトリにある）
- `mini.media.play_sound()` は非ブロッキング。再生中に `with` を抜けると音が切れるため、
  待ち時間が必要（このスクリプトでは既定3秒、`--wait` で変更可）

### これで分かったこと（原因の絞り込み）

- daemon、音声出力デバイス、スピーカー、`play_sound()` のAPIそのものは正常
- したがってMac版の失敗要因は「音声出力側」ではなく、次のどちらかに絞られる
  1. Mac→本体のWebRTC経由の音声送信経路
  2. Macの `say` が生成したWAV（16 kHz・16 bit PCM）の扱い
- 本体上ではハングも起きない。Mac版の「プロセスが終了しない」症状は、
  ネットワーク越しのメディア経路に固有の問題である可能性が高い（推測）

### 切り分け結果：WAV形式は無罪、原因は送信経路（2026-08-30）

Macの `say` が生成したWAVを `scp` で本体へ送り、本体上の
`audio_playback_on_robot.py` で再生したところ、**スピーカーから正常に音が鳴った**。
プロセスも終了コード0で正常終了した。

```bash
say --file-format=WAVE --data-format=LEI16@16000 -o mac_say.wav "こんにちは。リーチーミニです。"
scp mac_say.wav pollen@reachy-mini.local:~/
ssh pollen@reachy-mini.local \
  'source /venvs/apps_venv/bin/activate && python -u ~/audio_playback_on_robot.py ~/mac_say.wav --wait 5'
```

つまりWAVの形式（mono / 16000 Hz / 16bit PCM）に問題はなく、daemonはこの形式を
そのまま再生できる。**原因はMac→本体の音声送信経路（WebRTC）側に確定した。**

参考として、生成したWAVと本体内蔵WAVの形式は異なるが、どちらも本体上で再生できた。

| | Mac生成（`say`） | 本体内蔵 `wake_up.wav` |
| --- | --- | --- |
| チャンネル | mono | stereo |
| サンプリングレート | 16000 Hz | 44100 Hz |
| 形式 | 16bit PCM | 16bit PCM |

### 学び

- 「本体内蔵WAVは鳴るがMac生成WAVは鳴らない」という観察から形式差を疑ったが、
  形式差は存在したものの原因ではなかった。**目立つ差分が原因とは限らない**
- 実行場所を変えて同じ入力を試すのは、入力（データ）と経路を分離する有効な手段
- `README.md` に「16 kHz・16 bit PCMで生成」と書いているが、これはこちら側で決めた
  仕様であり、本体の要求仕様ではない。本体はどちらの形式も再生できた

### Mac版も再テストで成功した（2026-08-30）

送信経路の調査に入る前に、念のためMac版 `audio_playback.py` をそのまま再実行したら
**音が鳴り、終了コード0で正常終了した**。以前の「約90秒待っても終わらない」症状は
再現しなかった。WebRTCのログも `Audio send chain ready (bidirectional audio enabled)`
まで到達していた。

つまりMac経由の音声再生は現在は動作する。ハングも無音も起きない。

### 原因は未確定（推測の域）

再テストで直ってしまったため、当時の失敗要因を確定できていない。前回の失敗時から
変わった点は次の3つで、どれが効いたかは切り分けていない。

1. SDKと本体daemonを1.9.0から1.10.0へ更新した
2. スクリプトに `enable_motors()` を追加した（音声とは直接関係しないはずだが、
   接続直後の状態が変わった可能性はある）
3. 実機Appを停止した状態でテストした（前回は競合していた可能性がある）

もっとも疑わしいのは1のバージョン更新（推測）。ただし当時のログを残していないため
断定できない。**再現しなくなった不具合は原因を特定できない**という教訓として記録する。

### この一件で確定した事実

推測ではなく確定した事実は次のとおり。

- daemonはMacの `say` が生成する形式（mono / 16000 Hz / 16bit PCM）をそのまま再生できる
- 本体内蔵WAV（stereo / 44100 Hz）とMac生成WAVの形式差は、再生可否に影響しない
- `mini.media.play_sound()` は非ブロッキング。呼び出し後に待ち時間を入れないと、
  `with` を抜けた時点で音が切れる
- Wireless版では `No Reachy Mini Audio USB device found!` の後に
  `GstWebRTCClient initialized` と出れば正常。USB Audio未検出はエラーではない
- 正常時のWebRTCログは `Audio send chain ready (bidirectional audio enabled)` まで進む。
  次に音声が鳴らない事象が起きたら、この行まで到達しているかが切り分けの目印になる

### 学び

- 「本体内蔵WAVは鳴るがMac生成WAVは鳴らない」から形式差を疑ったが、形式差は原因では
  なかった。**目立つ差分が原因とは限らない**
- 実行場所を変えて同じ入力を試すと、入力（データ）と経路を分離できる。今回は
  「WAVを本体へ送って本体で鳴らす」ことで形式を無罪と確定させた
- 調査に着手する前に、**まず現状をそのまま再実行して再現性を確認する**べきだった。
  今回は経路の調査に入る直前に再実行して、直っていることに気づいた
- 失敗時のログを残していないと、直った後に原因を特定できなくなる。次からは失敗時点の
  daemonログとSDKバージョンを保存する

### 記事化の観点

- 「再現しなくなったバグ」の扱い。原因未確定のまま解決扱いにするときの記録の書き方
- バージョン更新で直った可能性があるなら、まず更新してから調査するほうが早い
- 切り分けの型として「入力を固定して経路を変える」「経路を固定して入力を変える」

### 移植で分かった注意点

`audio_playback.py` はMac版のみ有効。`hello.py` の `speak_on_macos()` を
importしており、その中で `shutil.which("say")` に依存しているため、本体上では
そのまま動かせない。on-robot版は音源をファイルパスで受け取る形に分離した。

## カメラ静止画取得（成功）

### カテゴリ

SDK・API / 実機・ハードウェア / 接続・デプロイ / 記事化の観点

### 試したこと

- Mac上で `ReachyMini(media_backend="default")` を使用
- `mini.media.get_frame_jpeg()` でJPEGデータを取得
- `camera_snapshot.jpg` として保存
- 接続停止に備え、Pythonの `SIGALRM` で20秒の上限を設定

### 結果

- 約5秒で取得・保存に成功
- 画像は破損しておらず、Reachy Miniの視点から室内と人物が鮮明に写った
- `No Reachy Mini Audio USB device found!` の後に `GstWebRTCClient initialized` と表示
  され、Wireless版のWebRTC経路へ正常にフォールバックした

### 学び

- `get_frame()` はBGRのNumPy配列、`get_frame_jpeg()` はそのまま保存可能なJPEGバイト列
- 静止画保存だけならPillowやOpenCVを追加せず `get_frame_jpeg()` が使える
- USB Audio未検出のログはWireless版では即エラーを意味せず、その後のWebRTC初期化を
  確認する必要がある
- カメラ成功により、先の音声失敗はWebRTC全体ではなく音声固有の経路である可能性が増した

### 本体上での実行（成功・2026-08-29）

`camera_snapshot_on_robot.py` を作り、本体上で実行して1280x720のJPEG（322 KB）を
保存できた。画像は破損なく、室内と人物が鮮明に写っていた。

Mac版との性能差が明確に出た。

| 項目 | Mac経由（WebRTC） | 本体上（localhost_only） |
| --- | --- | --- |
| 接続完了 | 約5秒 | 0.4秒 |
| フレーム取得 | リトライ前提のループ | 1回目で成功 |
| 撮影完了まで | 約5秒 | 2.5秒（うち約2秒は頭上げ待ち） |

- 本体上では `No Reachy Mini Audio USB device found!` や `GstWebRTCClient initialized` の
  ログが出ない。WebRTCを経由せずローカルのメディア経路を使うため
- `get_frame_jpeg()` は本体上なら初回呼び出しで返る。Mac経由でリトライが必要だったのは
  WebRTCのストリーム確立待ちだったと考えられる（推測）

### 撮影前に頭を上げる必要がある

実機の頭は、待機状態だと下向き気味になる。そのまま撮ると床や膝が写るため、撮影前に
頭の姿勢を明示的に指定した。

```python
mini.enable_motors()
mini.goto_target(head=create_head_pose(pitch=-10.0, degrees=True), duration=1.5)
time.sleep(0.5)
```

- `create_head_pose(pitch=...)` は**負の値で上向き**
- `goto_target` の完了後も、姿勢が落ち着くまで待ち時間を入れたほうが安定する
- カメラだけのテストでも `enable_motors()` が必要。姿勢を変えるならモーターを使う
- 記事化の観点: 「カメラの画角が変」の原因が、カメラ設定ではなく頭の姿勢だという点は
  初学者が気づきにくい

## daemon内蔵音源の再生（成功）

### カテゴリ

SDK・API / 実機・ハードウェア / 接続・デプロイ

- 顔追跡テストの開始時に `wake_up.wav`、終了時に `go_sleep.wav` を再生
- `media_backend="no_media"` のまま、`PlaySoundCmd` を操作用WebSocketでdaemonへ送信
- 両方とも本体スピーカーから聞こえた
- Mac生成WAVのアップロード再生失敗とは異なり、本体内蔵音源の再生経路は正常
- 今後の実機テストは、開始・終了が分かりやすいよう音などの合図を付ける

## 顔追跡（原因確定・解決 2026-08-29）

### カテゴリ

SDK・API / 実機・ハードウェア / 未解決・要検証 / 記事化の観点

### SDKが提供する範囲

- 公開API: `start_head_tracking()`、`stop_head_tracking()`、`get_tracked_face()`
- SDK 1.9.0の内部実装はYuNet顔検出モデルをONNX Runtimeで実行
- 顔検出と追跡はWireless本体のdaemon側で行われる
- 検出位置から頭の目標姿勢を計算し、モーターへ反映するところまでSDK側が提供

### 実機結果

- 15秒と30秒の2回テストした
- どちらも全サンプルで `detected=False`、頭は追従しなかった
- 開始・終了音とモーター、通常カメラ撮影は別テストで正常
- daemon statusはSDK・本体とも1.9.0、制御ループ約50 Hz、明示的エラーなし
- daemonログにはカメラ起動を確認したが、顔検出失敗の直接原因は見つかっていない

### SDK・daemon 1.10.0更新後

- 本体daemonとMac側SDKをともに1.10.0へ更新
- 更新直後の30秒テストではSDKの `get_tracked_face()` は全て `detected=False`
- 直後にREST APIで追跡を有効化すると `enabled=true` を返した
- 数秒後、REST APIの `/api/media/tracking/face` は `detected=true` と顔座標を返した
- その後の再テストでは、ユーザーが頭の追従らしき動きを目視確認した
- 一方、その実行中もMac SDKの `get_tracked_face()` 表示は `False` のままだった

### 当時の解釈（後に否定された）

- 更新後の初回は顔検出モデル準備に30秒以上かかり、テスト時間内に間に合わなかった
  可能性がある（推測）
- 顔追跡そのものは動作したが、WebSocket経由のSDK状態取得とREST APIの顔検出状態に
  不整合がある可能性がある（要検証）
- 実機の動作確認とテレメトリ表示は別々に評価する必要がある

いずれも誤り。真の原因は下記の `media_backend` 指定だった。

### 本体再起動時の観察

- SSHから `sudo reboot` を実行
- 起動過程は「mDNS名を解決できない」→「名前解決できるが8000番ポート未起動」→
  「daemon応答」の順で変化した
- daemon応答まで戻った時点で本体1.10.0、backend ready、制御ループ約50 Hz、エラーなし
- 再起動後のモーターモードは `disabled`。実機スクリプト側で移動前に
  `enable_motors()` が必要

### 原因確定：`media_backend="no_media"` では顔追跡が成立しない（2026-08-29）

daemon側の実装
（`/venvs/mini_daemon/lib/python3.12/site-packages/reachy_mini/vision/face_tracking.py`）
を読んで原因が確定した。

trackerは**自分でカメラを開かない**。GStreamerの `unixfdsrc` で共有カメラフィードの
unixソケット（`CAMERA_SOCKET_PATH`）へ接続しに行く実装になっている。

```python
source = Gst.ElementFactory.make("unixfdsrc")
source.set_property("socket-path", CAMERA_SOCKET_PATH)
...
if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
    if not feed_lost:
        feed_lost = True
        logger.warning("Face tracker cannot reach the camera feed; retrying.")
    pipeline.set_state(Gst.State.NULL)
    self._stop.wait(1.0)
    continue
```

そのため `media_backend="no_media"` で接続すると、カメラフィードを誰も配信しておらず
`set_state(PLAYING)` がFAILUREになる。trackerは1秒間隔で再試行し続けるだけで
フレームを1枚も受け取らず、`get_tracked_face()` の `detected` は永久に `False` になる。
顔が一度も検出されないので、頭も当然動かない。

### 比較テスト（本体上、同一スクリプト・同一条件）

`face_tracking_on_robot.py` に `--media-backend` を付けて2条件を比較した。

| 条件 | `media_backend` | 検出率 |
| --- | --- | --- |
| A | `no_media` | 0/15（0%） |
| B | `default` | 12/15（80%） |

条件Bでは `x` が +0.46 〜 -0.33 の範囲で変化し、`ts` も更新され続けた。実機の頭も顔を
追って動いた（目視確認）。最初の2〜3秒だけ `detected=False` なのは、カメラの
パイプライン確立待ちによる立ち上がり時間。

### Mac版も同じ1行で直った

`face_tracking.py` の `media_backend="no_media"` を `"default"` に変えるだけで、
Mac経由でも30秒中24回（80%）検出し、`x` は -0.59 〜 +0.49 で変化した。

### 学び

- **これはSDKやハードウェアの不調ではなく、こちらのスクリプトのバグだった。**
  「daemon側で動く機能だからクライアント側のメディアは不要」という思い込みが原因
- `media_backend` はクライアントが映像・音声を使うかどうかのフラグではなく、
  **カメラフィードそのものの配信可否**に効く。daemon側機能でも影響を受ける
- 実行場所（Mac／本体）は無関係だった。同じバグが両方で同じ症状を出していた
- 過去に一度だけREST APIで `detected=true` になったのは、その時点で別経路により
  カメラフィードが開いていたためと考えると整合する（推測）
- `feed_lost` フラグにより警告ログは**状態遷移時の1回だけ**出る。テスト中に
  ログをgrepしても何も出ないことがあるため、「ログが無い＝正常」ではない

### daemonログの見方（顔追跡）

追跡固有の警告は3種類ある。これを狙ってgrepすると切り分けが速い。

```bash
sudo journalctl -u reachy-mini-daemon.service -o cat --since "now" > /tmp/log.txt
grep -i "face\|track" /tmp/log.txt
```

- `Face tracker cannot reach the camera feed; retrying.` → カメラフィード未配信
  （＝`media_backend` の問題）
- `Face tracking unavailable: missing GStreamer plugins.` → GStreamer要素の不足
- `Face tracker crashed.` → 検出処理内の例外

`sudo` はパスワードなしで通る（`sudo -n true` で確認済み）。

### 既定値のままなら動いていた

`ReachyMini.__init__` の既定値を確認したところ `media_backend="default"` だった
（`connection_mode` の既定は `auto`）。つまり**何も指定しなければ最初から動いていた**。
`no_media` は自分で足した指定であり、それが原因だった。

- 「軽いほうが速いはず」「daemon側の機能だからクライアントのメディアは不要」という
  自前の最適化が、必要な機能を切っていた
- ただし `no_media` 自体は無駄ではない。モーションのみのスクリプト（`hello.py`、
  `body_rotation.py`）ではカメラ・WebRTCの初期化を省けるので有効
- 使い分けの結論
  - モーションのみ → `no_media` でよい
  - カメラ、音声、顔追跡を使う → 既定（`default`）のままにする
- 教訓: 既定値を確認せずに引数を足すと、既定値が正しかった場合に自分でバグを作る

### 初心者向けの説明（記事用の噛み砕き）

技術用語をそのまま書くと伝わらないため、記事では次の順で説明する。

**GStreamer は映像を流す配管キット。** 部品（エレメント）をつないでデータを流す。
名前が `...src` で終わる部品が入口（蛇口）、`...sink` で終わる部品が出口（排水口）。
今回のtrackerの配管は次の形で、`appsink` から出たコマを顔検出にかけている。

```text
unixfdsrc → queue → v4l2convert → capsfilter → appsink
  入口      バッファ   変換・縮小     形式指定     出口
```

**unix socket は同じPC内だけをつなぐ土管。** `/tmp/...sock` のようなファイルパスに
見えるが、中身が保存されるファイルではなく蛇口。片方が流し込み、もう片方が受け取る。

**`fd` は file descriptor（引換券）。** 映像を丸ごとコピーして渡すのではなく、
「このメモリ領域に画像がある」という券だけを渡す。1280x720を毎秒何十枚もコピーすると
CPUが持たないため、券だけ渡して実物は共有する設計。

**なぜこの構造か。** カメラは物理的に1個だが、使いたいプログラムは複数ある
（顔追跡、Macへの配信、写真撮影、会話アプリ）。全員が勝手に開くと取り合いになるので、
daemonだけがカメラを開いて配る。

```text
                        ┌→ 蛇口(unix socket) →→ 顔追跡 tracker
カメラ(imx708) → daemon ┤
                        └→ WebRTC →→→→→→→→→→→ Mac
```

**失敗の説明。** trackerは「カメラを開く人」ではなく「蛇口にホースを繋ぎに来る人」。
`no_media` ではdaemonがカメラを開かない＝蛇口に水が流れないので、繋ごうとして失敗し、
1秒待ってまた試すのを延々と繰り返していた。フレームが1枚も来ないため顔は検出されず、
頭も動かない。

ひとことでまとめると「顔追跡はカメラを自分で開かない。誰かがカメラを開いていないと、
覗く先が空っぽ。`media_backend` はそのスイッチだった」。

### 記事化の観点

- 「daemon側で動く機能なら、クライアントのメディア設定は関係ない」は誤り。
  ハマりどころとして記事の見出しになる
- 症状（`detected` が常にFalse、頭が動かない）から原因（`media_backend`）への距離が
  遠く、SDKのソースを読むまで分からなかった。ライブラリのソースを読む価値の実例
- 誤った仮説（モデル未ダウンロード、バージョン差、SDKとRESTの不整合）を3つ立てて
  いずれも外した。切り分けの順序として「まず実装を読む」が有効だった例
- 「ログが1回しか出ない」設計に気づかないと、ログ無しを正常と誤読する
- 既定値のままで動いたものを、自前の最適化で壊していた。「引数を足す前に既定値を
  確認する」は初心者向けの教訓として使える
- `unixfdsrc`、unixソケット、file descriptorは、蛇口・土管・引換券のたとえで説明できる

### 検出パラメータ（実装から）

- `FaceDetector` の既定 `score_threshold=0.6`、`nms_threshold=0.3`
- 検出スレッドはLinuxで `nice` 19（最低優先度）に設定され、daemon本体へCPUを譲る
- `start_head_tracking(weight=...)` の `weight` は 0〜1。0は「検出を止めるが
  trackerは破棄しない」安価なON/OFF用

## Recorded Moves（ダンス・感情モーション）成功・2026-08-30

### カテゴリ

SDK・API / 実機・ハードウェア / 記事化の観点

### 2つのライブラリが最初から使える

ダンスと感情モーションは同じ Recorded Moves の仕組みで、HuggingFaceのデータセットと
して配布される。**daemon起動時にプリダウンロードされる**ため、追加の設定なしで即再生
できた（`preload_default_datasets()` が起動時に走る）。

| ライブラリ | データセット | 件数 |
| --- | --- | --- |
| ダンス | `pollen-robotics/reachy-mini-dances-library` | 19 |
| 感情 | `pollen-robotics/reachy-mini-emotions-library` | 85 |

```python
from reachy_mini.motion.recorded_move import RecordedMoves
library = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
print(library.list_moves())
move = library.get("simple_nod")
print(move.duration, move.sound_path)
mini.play_move(move, initial_goto_duration=1.0, sound=True)
```

### 性質の違いが明確だった

- **ダンスは全19件が1.82〜5.00秒で、すべて音なし。** 音楽に合わせて組み合わせる素材と
  いう位置づけに見える（推測）
- **感情は85件中84件が音付き**（`waiting` のみ音なし）。長さは2.14秒（`inquiring1`）
  から19.76秒（`sleep1`）まで幅がある
- `RecordedMove` は `duration` と `sound_path` を持つので、**再生前に長さと音の有無が
  分かる**。危険な長さのモーションを事前に弾ける

### 実測

`simple_nod`（定義1.82秒）→ 実測2.84秒。`laughing1`（4.64秒）→ 5.70秒、
`proud1`（3.76秒）→ 4.87秒、`surprised1`（2.48秒）→ 3.58秒。いずれも
**定義＋約1.1秒**で、`initial_goto_duration=1.0`（開始姿勢への移動）とほぼ一致した。

### 注意点

- **音を鳴らすなら `media_backend` を既定（`default`）にする。** `no_media` では
  顔追跡と同じ理由で音が出ない
- 再生前に `enable_motors()` と頭を正面へ上げる処理が必要（待機姿勢は頭が下がっている）
- 存在しない名前を `get()` へ渡す前に `list_moves()` で検証すると、ロボットを動かして
  から失敗するのを避けられる

### 記事化の観点

- 「箱から出してすぐ104種類のモーションが使える」は記事の見どころになる
- ダンスは音なし・感情は音付きという設計の違い
- `duration` を事前に読めるので、安全確認を自動化できる

## アンテナを物理入力として使う（成功・2026-08-30）

### カテゴリ

SDK・API / 実機・ハードウェア / 記事化の観点

### モーター名が指定できる

`enable_motors(ids=[...])` / `disable_motors(ids=[...])` は個別のモーター名を取る。
有効な名前は `src/reachy_mini/assets/config/hardware_config.yaml` に対応する。

```text
body_rotation, stewart_1 … stewart_6, right_antenna, left_antenna
```

アンテナだけトルクを切れば、**頭と胴体は姿勢を保ったまま**アンテナを手で動かせる。

```python
mini.disable_motors(ids=["left_antenna", "right_antenna"])
left, right = mini.get_present_antenna_joint_positions()  # ラジアン
```

### 実測して分かったこと

20秒間、0.5秒間隔で読み取った結果。

- **左右が独立して読める。** 片方だけ動かしても他方は値を保つ
- **可動域は広い**: 左 83.1°、右 186.6°（右は +159.9° まで回った）
- **符号が左右で逆。** 左は手前へ倒すと負、右は正に増える（鏡像配置のため）
- **静止時の値は安定**（±0.1°程度）。しきい値判定に十分使える
- **ゼロ点はズレる。** 開始時点で左 -0.6°、右 +21.4° だった。手で動かした位置が
  そのまま残るため、**絶対角度ではなく起動時の値を基準にする必要がある**
- **戻り止めがない。** トルクを切ると倒した位置に留まる（バネで戻らない）

### 用途の判断

ボタンではなく**ダイヤル／レバー**として扱うのが妥当。

- 向く用途: 値の入力、大きく倒したことをイベントとして検出する
- 向かない用途: 「押して離す」というボタン的な操作

### トルクを戻すときの注意

トルクを戻した瞬間に、直前の目標値へ跳ねる可能性がある。復帰直後に**現在値を目標へ
設定**すると跳ねない。

```python
mini.enable_motors(ids=["left_antenna", "right_antenna"])
left, right = mini.get_present_antenna_joint_positions()
mini.goto_target(antennas=[left, right], duration=0.5)
```

### 記事化の観点

- モーターを部分的に切れることは、触って遊べる入力として使える発見
- 「ゼロ点がズレる」「戻り止めがない」は実機を触らないと分からない性質
- 単位はラジアン。度で扱うなら変換が必要

## マイク録音（成功・2026-08-30）

### カテゴリ

SDK・API / 実機・ハードウェア / 記事化の観点

### 入出力でサンプリングレートが違う

実機から取得した仕様。

| | レート | チャンネル |
| --- | --- | --- |
| 入力（マイク） | **16000 Hz** | **2 ch** |
| 出力（内蔵WAV） | 44100 Hz | 2 ch |

```python
rate = mini.media.get_input_audio_samplerate()      # 16000
channels = mini.media.get_input_channels()          # 2
```

マイクはReSpeakerのアレイなのでステレオ扱い。**入力16 kHz / 出力44.1 kHz**と非対称
なので、録った音をそのまま流す処理を書くときは注意が必要。

### `get_audio_sample()` はポーリング前提

`media.start_recording()` の後、`get_audio_sample()` を繰り返し呼んでチャンクを集める。
**データが無いときは `None` を返す**ため、`None` を無視して回し続ける実装が必要。

```python
mini.media.start_recording()
chunks = []
while time.monotonic() - started < seconds:
    sample = mini.media.get_audio_sample()
    if sample is None:
        time.sleep(0.01)
        continue
    chunks.append(np.asarray(sample, dtype=np.float32))
mini.media.stop_recording()
```

5秒の録音での実測値。

- 74チャンク / 151,552サンプル（`None` 受信は158回）
- 151552 ÷ 2ch ÷ 16000 Hz = **4.74秒相当**（指定5.0秒に対して妥当）
- 1チャンク ≒ 2048サンプル（1024フレーム × 2ch）

### float32 から16bit PCMへの変換

`get_audio_sample()` が返すのは float32（-1.0〜1.0）。WAVへ保存するには変換する。

```python
pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
with wave.open(path, "wb") as wav:
    wav.setnchannels(channels)
    wav.setsampwidth(2)
    wav.setframerate(rate)
    wav.writeframes(pcm.tobytes())
```

保存したWAVを `media.play_sound()` で再生し、**自分の声として聞き取れることを確認した**。

### 音量の指標を出すと切り分けが速い

ピークとRMSを表示すると、「録れているのに聞こえない」のか「そもそも録れていない」のかが
すぐ分かる。実測では声を入れたときピーク0.29〜0.62、RMS0.025〜0.068だった。
ピークが0.001未満ならほぼ無音として警告を出すようにした。

### 開始・終了の合図音は必須だった

最初は表示だけで進めたが、ユーザーが「いつ始まったか分からない」状態になった。内蔵音源を
合図に使うと解決した。**合図音が録音へ混ざらないよう、鳴り終わってから録音を開始する**
（`play_sound()` は非ブロッキングなので待ち時間が必要）。

内蔵音源の長さ（`reachy_mini/assets/`、すべて44100 Hz・2ch）。

| ファイル | 長さ | 用途 |
| --- | --- | --- |
| `wake_up.wav` | 0.41秒 | 開始の合図に向く |
| `count.wav` | 0.66秒 | 終了の合図に向く |
| `dance1.wav` | 0.99秒 | |
| `impatient1.wav` | 0.90秒 | |
| `go_sleep.wav` | 3.60秒 | 長いので合図には不向き |
| `confused1.wav` | 5.71秒 | |

### 記事化の観点

- 入力16 kHz / 出力44.1 kHzという非対称は、音声処理を書くときの落とし穴
- `None` を返すポーリングAPIは、初見だと「録れていない」と誤解しやすい
- 人間が関わるテストでは、画面表示だけでなく**音の合図**が要る。実際にこれで詰まった
- ピーク・RMSを出すだけで切り分けが速くなる

## 公式ドキュメントから分かったこと（2026-08-30 調査）

### カテゴリ

SDK・API / 接続・デプロイ / 記事化の観点

### クライアントの経路は3つあり、文書化の度合いが違う

| 経路 | 対象 | 文書化 |
| --- | --- | --- |
| Python SDK | Python | 公式ドキュメントあり |
| JavaScript SDK | ブラウザ | 公式ドキュメントあり。**WebRTC**接続。公式は「新しいアプリはこれが推奨」 |
| REST API `:8000` | 任意 | OpenAPIは取得できるが**モーション系エンドポイントは無い** |
| `ws://:8000/ws/sdk` | 任意 | **文書化なし**。SDKのソースから判明した内部API |

公式ドキュメント: https://huggingface.co/docs/reachy_mini/en/SDK/javascript-sdk

JS SDKはHuggingFace OAuth → シグナリングサーバー（HF Space）→ WebRTC P2Pという流れ。
接続確立後はシグナリングサーバーが経路から外れる。

**マイコン（ESP32など）から操作したい場合、WebRTCは重すぎる**（DTLS/SRTP、ICE、SDP、
OAuth）。内部APIの `/ws/sdk` を直接叩く手もあるが無保証。本体側にPython SDKを使った
HTTPプロキシを置くのが安定（`docs/ideas.md` 参照）。

### アップロード音声は 16 kHz モノ 16bit PCM WAV が必須

公式ドキュメントの明記事項。**daemonはトランスコードしない。**

> Audio must be canonical 16 kHz mono 16-bit PCM WAV. Apps are responsible for
> normalizing before upload — the daemon does not transcode. Format mismatch is a
> frequent cause of "audio is silent / wrong speed" on inherited datasets.

「無音になる／速度がおかしい」の頻出原因としてフォーマット不一致が挙げられている。
以前ハマった音声再生の問題と関係する可能性がある（要検証）。ただし本プロジェクトの実測
では、**Macの `say` が生成した mono / 16000 Hz のWAVは本体上で正常に再生できた**ため、
`play_sound()` によるファイル再生と、データチャネル経由のアップロード再生では要求が
異なると思われる（推測）。マイク入力も16 kHzなので、**16 kHzモノが本体の標準**と考えて
おくとよい。

### 頭は world frame。`body_yaw` だけ送ると頭が逆回転して見える

胴体回転時に首が逆方向へ補正されるように見えた現象（本メモ「胴体回転」）の**公式説明が
見つかった**。

> The `head` matrix is in the world frame. Sending `setTarget({ body_yaw })` alone
> rotates the body but not the head's commanded world yaw — the head's gaze stays
> fixed in world frame, so visually it appears to counter-rotate as the body turns.

つまり「首が補正されている」のではなく、**頭の目標がワールド座標で固定されているため、
胴体が回っても視線が動かない**というのが正しい理解。戦車のように頭を胴体へ追従させたい
場合は、頭のRPYのyawへ胴体のyaw差分を足して、`head` と `body_yaw` を**同じ呼び出しで**
送る必要がある。

またその基準値には、テレメトリの `state.head` ではなく**自分が最後に指令した値**を使う
こと。テレメトリはWebRTCのRTT分遅れるため、差分を積み上げると入力が速いときに破綻する。

### モーターモードは3つある

`setMotorMode(mode)` の選択肢が明記されていた。

- `enabled`: 位置制御
- `disabled`: 脱力（limp）
- `gravity_compensation`: 手で動かせる（float by hand）

`docs/tasks.md` B-3（重力補償）の裏付けになる。Python SDKの
`enable_gravity_compensation()` と対応する。

### その他

- `subscribePose()` で約30 Hzのポーズ配信を受け取れる（既定は500 msポーリング）
- `head_joint_positions` は7要素で、`[0]` が胴体yaw、`[1..6]` がStewartプラットフォームの
  首6モーター。`antennas_joint_positions` は `[right, left]`（ラジアン）
- JS SDK側の `playMove` では音声とモーションのズレ補正 `audioLeadMs` の既定が **-100 ms**
  （モーター立ち上がりとGStreamerウォームアップの実測値）
- 長いモーションはブラウザから毎フレーム送るのではなく、**daemon側の時計で再生**させる
  設計が推奨されている

### 記事化の観点

- 「Pythonでできることを他の言語からやる」ときの経路選択（公式JS SDK / 内部WS / 自前プロキシ）
- 16 kHzモノという制約が入出力に一貫している点
- ワールド座標系の頭姿勢は、実機を触ると「首が勝手に補正される」と誤解しやすい。
  公式の説明を読むと設計意図が分かる好例
- 実測で気づいた現象を、後から公式ドキュメントで裏付けられた流れ

## REST APIプロキシを本体で動かす（成功・2026-08-30）

### カテゴリ

SDK・API / 接続・デプロイ / 記事化の観点

### やったこと

マイコン（ESP32など）から操作できるようにするため、本体上でFastAPIのプロキシを動かし、
HTTP RESTでロボットを操作した。実装は `reachy_proxy.py`。

```bash
# 本体上で
source /venvs/apps_venv/bin/activate
python reachy_proxy.py       # 既定 0.0.0.0:8080

# Macから
curl "http://reachy-mini.local:8080/move/groovy_sway_and_roll"
curl "http://reachy-mini.local:8080/move/proud1?library=emotions"
curl "http://reachy-mini.local:8080/antennas?left=30&right=-30"
```

全エンドポイントの動作を確認した。ダンス・感情モーション（音付き）・アンテナ・胴体回転・
頭の姿勢・内蔵音源・状態取得・404/400のエラー応答。

### 実測した応答時間

| 操作 | 定義 | 応答 |
| --- | --- | --- |
| `groovy_sway_and_roll` | 1.84秒 | 2.98秒 |
| `jackson_square` | 5.00秒 | 8.25秒 |
| `laughing1`（音付き） | 4.64秒 | 5.87秒 |
| `wait=false` で17.26秒のモーション | 17.26秒 | **0.15秒** |

`jackson_square` は定義5.00秒に対して8.25秒かかった。`initial_goto`（1.0秒）を引いても
2.2秒余計で、`laughing1` の差（1.2秒）より大きい。開始姿勢が遠い、または可動範囲の
大きいモーションは実再生が長引く可能性がある（要検証）。

### 重要な訂正: daemonのRESTにモーションAPIは存在する

以前「REST APIにモーション系エンドポイントは無い」と記録したが**誤り**だった。openapiの
一覧を分割表示した際に該当部分を読み飛ばしていた。実際には存在する。

```text
POST /api/move/goto
POST /api/move/set_target
POST /api/move/play/recorded-move-dataset/{dataset_name}/{move_name}
POST /api/move/play/wake_up
POST /api/move/play/goto_sleep
POST /api/move/stop
GET  /api/move/running
```

実機で確認した挙動。

```bash
# データセット名のスラッシュはURLエンコードする（%2F）
curl -X POST "http://reachy-mini.local:8000/api/move/play/recorded-move-dataset/pollen-robotics%2Freachy-mini-dances-library/yeah_nod"
# → {"uuid":"825aa755-..."} を返す非ブロッキング方式

curl "http://reachy-mini.local:8000/api/move/running"
# → 再生中は [{"uuid":"..."}]、アイドル時は []

curl -X POST "http://reachy-mini.local:8000/api/move/stop"
# → ボディ必須（uuid指定）。ボディなしは422
```

**つまりESP32からdaemonを直接叩くこともできる。** それでもプロキシを置く価値は残る。

- 角度を**度**で受けられる（ESP32側でラジアン変換や4x4行列生成が不要）
- エンドポイントを単純化できる（全部GET、パスも短い）
- データセット名のURLエンコードを隠せる
- 複数操作をまとめた高レベルAPIを作れる

### 発見: `async_play_move` は `await` 必須（タスクA-3の答え）

`play_move` と `async_play_move` は**ソースが同一**で、`play_move.__wrapped__` が
`async_play_move` を指している。**`play_move` は非同期版の同期ラッパー**だった。

```python
inspect.iscoroutinefunction(ReachyMini.play_move)        # False
inspect.iscoroutinefunction(ReachyMini.async_play_move)  # True
ReachyMini.play_move.__wrapped__                         # async_play_move
```

そのため `async_play_move` を同期コードから呼ぶと**コルーチンが生成されるだけで実行され
ない**。ログに次が出て、ロボットは動かない。

```text
RuntimeWarning: coroutine 'ReachyMini.async_play_move' was never awaited
```

関節角を時系列でサンプリングして、実際に動いていないことを確認した（変化は±0.002の
ノイズのみ）。**非同期に再生したいなら、同期版 `play_move` をスレッドで回す**のが確実。

```python
threading.Thread(target=lambda: mini.play_move(move), daemon=True).start()
```

### 実装のハマりどころ

**1. `/state` でロックを取ると再生中にタイムアウトする**

再生スレッドがロックを保持し続けるため、状態取得がロック待ちで詰まった。**読み取りは
ロック不要**にして解決した。書き込み（動かす操作）だけを排他する。

**2. `is_move_running` はPython SDKから取れない**

`client.get_status()` が返す `DaemonStatus` に `is_move_running` は無い。`.state` は
daemonのライフサイクルenum（`running` など）で、関節や再生状態ではない。`StateSnapshot`
には存在するが、SDKのクライアントに取得口が無い。**daemonの `GET /api/move/running` を
使うのが早い**。

**3. `nohup` だけではSSH切断で止まることがある**

`ssh -f` + `nohup setsid ... < /dev/null &` にすると確実に切り離せた。

**4. SDKの同時接続は可能だった**

プロキシが接続を保持したままでも、別プロセスから `ReachyMini()` で接続して操作できた。
Appとスクリプトの排他（`robot-app-lock-status`）とは別の話らしい（要検証）。
ただし同時に動かすと指令が競合するため、実運用では避けるべき。

### 記事化の観点

- 「マイコンからロボットを操作する」構成として、プロキシ層を置く設計は分かりやすい
- 公式ドキュメントに無いdaemonのREST APIを、openapi.jsonから発見できる
- 自分の過去メモの誤り（モーションAPIが無い）を、実際に叩いて訂正した流れ
- `async_` 接頭辞のメソッドを同期コードから呼んで動かない、という初学者が必ず踏む罠
- 排他ロックの範囲設計（読み取りは外す）は実際にタイムアウトして気づいた

## daemonのbackendが停止しているとREST操作が効かない（2026-08-30）

### カテゴリ

接続・デプロイ / SDK・API / 記事化の観点

### 現象

REST APIでモーションを送ったら **HTTP 503 `Backend not running`** が返った。
その直前までは同じリクエストで正常に動いていた。

### 原因

ユーザーがReachy Mini Control側でdaemonを停止していた。アイドルによる自動停止ではない。
`GET /api/daemon/status` の `state` が `stopped` になっていた。

### 層の区別が必要

「Appを止めれば操作できる」と理解していたが、実際には層が3つある。

| 層 | 操作に必要か | 確認方法 |
| --- | --- | --- |
| Reachy Mini の App | **不要**（`null` のままで動く） | `GET /api/apps/current-app-status` |
| daemon プロセス | 必要（常時稼働） | `GET /api/daemon/status` |
| daemon の **backend** | **必要**（`state: running`） | 同上 |
| モーターのトルク | **必要**（`enabled`） | `GET /api/motors/status` |

### 復旧手順

```bash
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=false"
# wake_up クエリパラメータは必須。無いと 422
# wake_up=true なら起床モーションと音が入る
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled
```

起動後の `backend_status` で制御ループの実測値も見える。

```json
{"ready":true,"motor_control_mode":"enabled",
 "control_loop_stats":{"mean_control_loop_frequency":49.6,
   "max_control_loop_interval":0.0216,"nb_error":0,
   "motor_controller":"ControlLoopStats(period=~20.00ms, read_dt=~1.92 ms, write_dt=~0.39 ms)"}}
```

### 見つけにくい失敗が2つある

1. **backend が停止していると 503 を返す。** これはエラーになるので気づける
2. **backend は動いていてもモーターが `disabled` だと、`goto` は uuid を返すのに
   ロボットが動かない。** 成功したように見えるため気づきにくい。実際に、backend起動直後は
   `motor_control_mode: disabled` で、そのまま `goto` を送ると uuid（200）が返るのに
   無反応だった。アンテナの実測値が -174.7° / 167.9° という脱力状態のままだった

### 学び

- **HTTP 200 とロボットが動くことは別。** 非ブロッキングAPIでは「受け付けた」しか
  意味しない。実際に動いたかは関節角を読んで確認する
- 状態確認は冪等なので、クライアント側で「確認して必要なら起動」を毎回通すのが安全
- 本体を再起動するとモーターのトルクは `disabled` から始まる（既存メモにも記録あり）

### 記事化の観点

- 「App を止めれば動く」ではなく、daemon の backend とモーターのトルクという層がある
- 200が返るのに動かない、という切り分けの難しい失敗の実例
- マイコンから操作するときに必要な初期化シーケンスとして記事に書ける

## SDK 1.10.0への更新とPython要件

### カテゴリ

実行環境・依存関係 / 課題と解決 / 記事化の観点

### 現象

`uv add 'reachy-mini==1.10.0'` が依存解決に失敗した。実際にはPython 3.12を使っているが、
プロジェクトの `requires-python` が `>=3.10` だったため、uvはPython 3.10でも成立する
ロックを作ろうとした。

### 原因

Reachy Mini SDK 1.10.0はPython 3.11以上を要求する。`requires-python=">=3.10"` という
プロジェクトの対応範囲と矛盾した。

### 解決

- `requires-python = ">=3.11"` へ変更
- `reachy-mini==1.10.0` を明示的に固定
- 実際の `.python-version` は3.12のため、実行環境自体の変更は不要

### 学び

uvの依存解決は「今使っているPython」だけでなく、プロジェクトが対応すると宣言した
Pythonバージョン範囲全体を考慮する。

## reachy_mini_conversation_app のLLM実行場所とバックエンド構成

### カテゴリ

SDK・API / 接続・デプロイ / 記事化の観点 / 未解決・要検証

### 調査対象

`pollen-robotics/reachy_mini_conversation_app` v1.0.1（コミット 531baaa、2026-08-19）。
コードを読んで確認した事実を記録する。

### LLMはロボット本体では動いていない

デフォルト（`HF_REALTIME_CONNECTION_MODE=deployed`）では、Hugging Face側の
realtimeサーバで動く。

```python
# src/reachy_mini_conversation_app/config.py:69
HF_REALTIME_SESSION_PROXY_URL = "https://pollen-robotics-reachy-mini-realtime-url.hf.space/session"
```

- このSpaceはプロキシで、実体は「session allocator」へ転送される。
  コードのコメントに `allocator changes do not require app releases` とあり、
  アプリを更新せずにバックエンドを差し替えられる設計。
- **APIキー不要**。READMEに `The default setup uses the Hugging Face backend and
  does not require an API key.` と明記されている。
- セッション割り当て時に `hf auth login` のキャッシュ資格情報へフォールバックし、
  さらにdaemonから取得した `hardware_id` を送っている
  （`huggingface_realtime.py:1043-1048`）。実機保有者に紐づけて提供していると推測。
- 本体（CM4）がやるのは音声入出力、カメラ、モーター制御のみ。推論はしない。

### プロトコルはOpenAI互換だが、OpenAIではない

`openai` パッケージの `AsyncOpenAI` と `openai.types.realtime.*` を使いつつ、
接続先はHF。過去のマルチバックエンド構成は削除されている。

```python
# config.py:91
_OBSOLETE_BACKEND_ENV_NAMES = ("BACKEND_PROVIDER", "MODEL_NAME")
```

- 以前は `BACKEND_PROVIDER` でOpenAIなどを選べた。現在は
  「Hugging Faceが唯一のバックエンド」。
- ボイス名は `Aiden` `Eric` `Ono_Anna` `Serena` `Sohee` `Uncle_Fu` `Vivian` で、
  OpenAIのボイス名ではない。
- 文字起こしだけ `model="gpt-4o-transcribe"` を指定しているが、これはOpenAI互換
  パラメータをそのまま渡しているだけで、実際に動くモデルはコードから特定できない（要検証）。
- 音声フォーマットはコメントに `the HF compatible server uses rate=None for
  native 16 kHz mode` とあり、OpenAI仕様の24kHzではなく16kHzネイティブ。

### ローカルバックエンドに切り替えられる

```env
HF_REALTIME_CONNECTION_MODE=local
HF_REALTIME_WS_URL=ws://127.0.0.1:8765/v1/realtime
```

- 指定先は `huggingface/speech-to-speech` を自分で起動したエンドポイント。
- README記載の3構成。①同一マシン ②PCで起動し同一Wi-Fi上のWireless版から叩く
  （`ws://<laptop-lan-ip>:8765`）③SSHリモートフォワード
  `ssh -N -R 8765:127.0.0.1:8765 <robot-user>@<robot-host>`。
- `local` のときはキャッシュ資格情報と `hardware_id` は送信されない。
  明示設定した `HF_TOKEN` のみが渡る。
- Web UIのSettings > Connectionからも切り替えられ、UIが `.env` を書く。

### カメラの画像処理は2系統に分かれている

**顔追跡はロボット本体（daemon）でローカル処理。**

```python
# moves.py:393
if speaking and self.current_robot.get_tracked_face(wait=False).detected:
```

SDK側は `ReachyMini.get_tracked_face()` で、docstringは
`Return the latest face observed by daemon-side head tracking.`。
実体は `daemon/backend/abstract.py` の `_face_target` で、
daemonが常時更新している。アプリの `head_tracking` ツールは
`movement_manager.set_head_tracking(enabled)` のフラグを立てるだけ。
どの検出器を使っているかはSDKパッケージ内から特定できなかった（要検証）。

**シーン理解はクラウド送信。**

`tools/camera.py` は `deps.reachy_mini.media.get_frame_jpeg()` でJPEGを取り、
base64にして返すだけ。解析はしない。

```python
return {"b64_im": base64.b64encode(jpeg_bytes).decode("utf-8")}
```

`huggingface_realtime.py:655-662` がそれを realtime セッションへ
`input_image` として `data:image/jpeg;base64,...` で投げる。つまり
**画像の内容理解はバックエンド側のマルチモーダルモデル**が担当する。
READMEにも `Vision is handled by the realtime backend when the camera tool is used`
とある。

まとめると、顔の位置＝本体、画像の意味＝クラウド。

### バックエンドの中身：e2eではなくVAD/STT/LLM/TTSのカスケード

`local` モードで指定する `huggingface/speech-to-speech` は、READMEに
`A low-latency, fully modular voice-agent pipeline: VAD -> STT -> LLM -> TTS` と
明記された**4段のカスケード構成**。音声を直接入出力するe2eモデルではない。

| 段 | 既定の実装 |
| --- | --- |
| VAD | Silero VAD v5 |
| STT | Parakeet TDT 0.6b-v3（`nvidia/parakeet-tdt-0.6b-v3`） |
| LLM | OpenAI互換API（既定 `gpt-5.6-terra` / Responses API、reasoning effort none） |
| TTS | Qwen3-TTS（`Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`、既定スピーカー `Aiden`） |

**デフォルト（`deployed`）のバックエンドも、これと同じ実装である可能性が高い。**
根拠は次の3点。

- 会話アプリのボイス一覧（`Aiden` `Ono_Anna` `Serena` `Sohee` `Uncle_Fu` `Vivian`）が
  `speech-to-speech` のQwen3-TTSスピーカー一覧と一致する
- どちらもOpenAI Realtime互換のWebSocketを話し、`local` モードのポートも
  `speech-to-speech` の既定 `8765` と一致
- 入力音声の文字起こし言語をセッション設定で渡す作りは、STTが独立した段として
  存在するカスケード構成と整合する（e2eなら不要）

ただしdeployed側の実体はSpaceプロキシの先にあり、クライアントからは確認できない。
「たぶん同じ実装」までが言える範囲（要検証）。

クライアントから見ると、音声を送って音声が返るのでe2eのように見える。
だが実際は縦積みなので、段ごとにモデルを差し替えられる。逆に言うと、
段のどこかが日本語に対応していなければ日本語で動かない。

### 日本語で認識されにくい原因

原因は3層ある。上の2つはこちらで直せるが、3つ目は直せない可能性がある。

**1. 文字起こしの言語が既定で `en` に固定される**

```python
# config.py:157-160
def _normalize_transcription_language(value: str | None) -> str:
    candidate = (value or "").strip()
    return candidate or "en"
```

この値がそのままセッション設定に渡る。

```python
# huggingface_realtime.py:232-235
transcription=AudioTranscriptionParam(
    model="gpt-4o-transcribe",
    language=config.REALTIME_TRANSCRIPTION_LANGUAGE,
),
```

STTに「入力は英語」と宣言しているため、日本語音声の認識精度が落ちる。
ホワイトリストはなく任意の文字列を通すので、`ja` を指定できる。

**2. プロファイルのプロンプトが英語固定を指示している**

```text
# profiles/default/profile.md
You speak English by default and switch languages only if explicitly told.
```

STTが通っても、この指示があるため英語で返答する。

**3. 既定のSTT（Parakeet TDT）が日本語に対応していない**

`speech-to-speech` のREADMEの言語対応表より。

| 段 | バックエンド | 対応言語 |
| --- | --- | --- |
| STT | Parakeet TDT（既定） | **25の欧州言語**。日本語は含まれない |
| STT | Whisper / Whisper MLX / Faster Whisper | 広範な多言語（チェックポイント次第） |
| TTS | Qwen3-TTS（既定） | 多言語。`--qwen3_tts_language auto` |

これが本命の原因と考えられる。deployedバックエンドがParakeetを使っているなら、
`REALTIME_TRANSCRIPTION_LANGUAGE=ja` を設定しても日本語は認識されない。
READMEの例が `zh` しか挙げていないのも、単に例示なのか対応範囲の反映なのかは不明（要検証）。

なおTTS（Qwen3-TTS）は多言語対応なので、**出力側は日本語を話せる**見込み。
スピーカー名 `Ono_Anna` は日本語音声と推測される（要検証）。
つまり詰まっているのは入力側。

### 日本語対応の手順

**まず試すこと（安い順）**

ロボット上のアプリの `.env` に設定する。

```env
REALTIME_TRANSCRIPTION_LANGUAGE=ja
```

加えて、プロファイルを複製して次を変更する。バンドル済みプロファイルは直接編集しない。

- `You speak English by default...` の行を、日本語で話す指示に置き換える
- プロンプト本文自体を日本語で書く
- ボイスを `Ono_Anna` に変更する

プロファイルはWeb UIからも作成でき、`profile.md` はTOMLメタデータ（`+++` 囲み）＋
Markdown本文という構成。

**それで改善しない場合（本命の対処）**

deployedバックエンドのSTTは差し替えられないため、`local` モードで自分の
`speech-to-speech` サーバを立て、STTをWhisper系にする。

```bash
speech-to-speech serve \
    --stt whisper-mlx \
    --stt_model_name large-v3 \
    --language ja \
    --tts qwen3 \
    --qwen3_tts_speaker Ono_Anna
```

- Macで立てるなら `--stt whisper-mlx`、Linux/CUDAなら `--stt faster-whisper`
- 複数言語を混ぜるなら `--language auto`（STTが発話ごとに言語を判定してLLMへ渡す）。
  小さいLLM向けには `--enable_lang_prompt` で「その言語で返して」という指示を付加できる
- LLMは `--model_name` と `--responses_api_base_url` で任意のOpenAI互換先に向けられる。
  ローカル完結にするならllama.cppやvLLMを指定する

そのうえで、ロボット側の `.env` を次にする。

```env
HF_REALTIME_CONNECTION_MODE=local
HF_REALTIME_WS_URL=ws://<PCのLAN IP>:8765/v1/realtime
```

この構成なら入力STT・LLM・TTSすべてを日本語対応の組み合わせに揃えられる。
遅延はPC側の性能に依存する。

### 学び

- 「Reachy Miniの会話アプリ」は実機単体で完結しておらず、既定ではHFのクラウド推論に
  依存する。オフラインで使いたい場合は `local` モードとローカルサーバの用意が前提。
- バックエンドはe2eの音声モデルではなくVAD/STT/LLM/TTSのカスケード。
  クライアントからはe2eに見えるが、実際は段ごとに差し替え可能な構成。
- **日本語が通らないのはアプリの問題ではなく、既定STT（Parakeet TDT）の言語対応の問題**
  である可能性が高い。設定変更だけでは解決しない場合、STTを差し替える必要がある。
  つまり「日本語で使う」＝「自前バックエンドを立てる」に近い。
- バックエンドがSpaceプロキシ経由なので、ユーザー側から見て実際のモデルが何かは
  分からず、いつ差し替わってもおかしくない。記事に書くならモデル名は断定しない。
- fmbro0203のZenn記事（2026-01）は「OpenAI Realtime API」として内部構造を解説して
  いるが、現在はHF一本に統合済み。半年で構造が変わっており、記事は腐りやすい。
- 日本語で使えないという体験そのものが、日本語記事のネタとして価値が高い。
  英語圏の書き手には見えない問題で、`docs/ja-articles-survey.md` の調査でも
  「音声認識の日本語精度」は誰も書いていない空白だった。

### VADとは何か、どこで動くか

VAD（Voice Activity Detection、音声区間検出）は、マイク入力から「人が話している
区間」と「無音・雑音」を切り分ける処理。役割は2つ。

- 発話の開始と終了を判定し、STTへ渡す区間を切り出す（ターンテイキング）
- ロボットが話している最中の割り込みを検知する

`speech-to-speech` の既定はSilero VAD v5。会話アプリ側はセッション設定でこう指定して
いる。

```python
turn_detection=ServerVad(type="server_vad", interrupt_response=True),
```

`server_vad` なので**VADもサーバ側**。ロボットは音声を流し続けるだけで、区切りの
判断はしていない。

### 各段の実行場所まとめ

| 段 | deployedモード | localモード | ロボット本体 |
| --- | --- | --- | --- |
| VAD | HF側 | 自前サーバ | 動かない |
| STT | HF側 | 自前サーバ | 動かない |
| LLM | HF側 | 自前サーバ、または外部API | 動かない |
| TTS | HF側 | 自前サーバ | 動かない |
| 顔検出・追従 | 本体daemon | 本体daemon | **動く** |
| 音声入出力・カメラ・モーター | 本体 | 本体 | **動く** |

### 画像も同じ無償枠に含まれる

カメラ画像は別サービスではなく、同じrealtimeセッションへ `input_image` として
送られる。APIキーは不要（README: `does not require an API key`）。

ただし公式にクォータや無償の保証は書かれていない。セッション割り当て時に
`hardware_id` を送っているため、実機保有者向けの提供と考えられる。仕様変更や
制限の追加はいつでもあり得る（要検証）。

### CM4でSTTを動かせるか

Wireless版のコンピュータはRaspberry Pi CM4（公式ドキュメントで確認）。
BCM2711、Cortex-A72 4コア 1.5GHz、GPU/NPUなし。結論は**実用的でない**。

- Parakeet TDT 0.6B をARM CPUで回すのは非現実的（推測）
- whisper.cppのtiny/baseなら動く可能性があるが、そのサイズでの日本語精度は
  実用に厳しい。small以上は実時間に間に合わないと見込む（推測、要検証）
- Qwen3-TTS 1.7BとLLMは論外
- 加えて、同じ4コアでdaemonがモーター制御ループ・カメラ・音声を回している。
  CPUを奪うと制御のジッタや音の途切れが出る恐れがある

したがって推論はPC/Mac側か、クラウドに置く。

### STT/TTSを外部APIに出せる

`speech-to-speech` はSTTとTTSもOpenAI互換エンドポイントに委譲できる。

- STT: `--stt openai` → `POST /v1/audio/transcriptions`
  （`docs/openai-compatible-stt.md`）。VAD・ターン管理・会話状態は手元に残り、
  認識だけ外部へ出す。16kHzモノラルPCM16のWAVをアップロードする
- TTS: `/v1/audio/speech` 互換エンドポイント（`docs/openai-compatible-tts.md`）
- LLM: `--llm_backend responses-api` / `chat-completions` に
  `--responses_api_base_url` で任意の互換先

```bash
# OpenAIホストのSTTを使う例
speech-to-speech local \
  --stt openai \
  --openai_stt_base_url https://api.openai.com/v1 \
  --openai_stt_model gpt-transcribe
```

vLLMで `Qwen/Qwen3-ASR-1.7B` を立てて向ける構成も公式ドキュメントに例がある。
STTを外部にしてもLLMとTTSは独立に選べる。

なおライブ文字起こしを有効にすると、確定前の発話を繰り返しアップロードするため
リクエスト数が増える（有料APIではコストに直結）。

### `--stt none` で音声を直接LLMに渡す構成もある

```bash
speech-to-speech serve \
  --stt none \
  --llm_backend chat-completions \
  --model_name "<音声入力対応モデル>" \
  --responses_api_base_url "https://provider.example/v1"
```

VADで切り出した音声セグメントをそのまま音声入力対応モデルへ送る。STT段が消えるので
構成は2段に近くなる。`responses-api` では非対応で、`chat-completions` のみ。
モデル側が音声入力に対応している必要がある。

### できるだけ無料で日本語対応させる場合の選択肢

**案0: まずタダで試す（5分）**

deployedのまま `.env` に `REALTIME_TRANSCRIPTION_LANGUAGE=ja` を入れ、プロファイルを
日本語化する。既定STTがParakeetなら効かないと予想されるが、コストゼロなので先に試す。

**案1: Macでフルローカル（電気代のみ、完全無料）**

```bash
speech-to-speech serve \
  --mac-optimal-settings \
  --stt whisper-mlx \
  --language ja \
  --tts qwen3 --qwen3_tts_speaker Ono_Anna \
  --llm_backend mlx-lm \
  --model_name mlx-community/Qwen3-4B-Instruct-2507-4bit
```

- `--mac-optimal-settings` はSTT=Parakeet / LLM=MLX LM / TTS=Qwen3-TTS(mlx-audio, 6bit)
  を既定にするプリセット。明示した `--stt` は上書きされる
- whisperのモデルサイズは小さめから試す。large-v3は遅延が大きい可能性がある（要検証）
- ロボットから届かせる方法は、LAN IPで待ち受ける方法か、会話アプリのREADMEにある
  SSHリモートフォワード `ssh -N -R 8765:127.0.0.1:8765 <robot-user>@<robot-host>`。
  後者はホストのbind設定に悩まなくて済む

**案2: 重い段だけ外部の無料枠に出す**

`--stt openai` や `--llm_backend chat-completions` の `base_url` を、無料枠のある
OpenAI互換プロバイダへ向ける。マシンが弱い場合の選択肢。無料枠の条件は変動するため
利用前に確認する。

**案3: LLMだけクラウド、STT/TTSはローカル**

`speech-to-speech` の既定に近い形。STTを日本語対応のWhisper系にしておけば、
LLMは好きな互換APIに出せる。

いずれの案でもロボット側の設定は同じ。

```env
HF_REALTIME_CONNECTION_MODE=local
HF_REALTIME_WS_URL=ws://<バックエンドのホスト>:8765/v1/realtime
```

### インスタンスディレクトリと `.env` の場所（実機で確認）

会話アプリの設定・状態の保存先は、ホームディレクトリではなく
**site-packages内のパッケージディレクトリ**だった。

```text
/venvs/apps_venv/lib/python3.12/site-packages/reachy_mini_conversation_app/
├── startup_settings.json   ← 実機で発見
├── .env                    ← ここに置く
├── memory.v1.json          ← remember/forgetの保存先
└── profile_toolsets.json   ← ツール有効/無効の上書き
```

READMEは既定の保存先を `~/.local/share/reachy_mini_conversation_app/` と書いているが、
Wireless版本体で実際にアプリを動かした環境では `~/.local/share/` 配下にアプリの
ディレクトリは作られず、`uv` だけだった。

### なぜそうなるか

SDKの `ReachyMiniApp._get_instance_path()` は**モジュールファイル自身のパス**を返す。

```python
# reachy_mini/apps/app.py:169-175
def _get_instance_path(self) -> Path:
    """Get the file path of the app instance."""
    module_name = type(self).__module__
    mod = importlib.import_module(module_name)
    return Path(mod.__file__).resolve()
```

会話アプリ側はその `.parent` をインスタンスパスとして使う。

```python
# main.py:361
instance_path = self._get_instance_path().parent
```

つまりインストール先のパッケージディレクトリがそのままインスタンスパスになる。
`.env` の読み込みもそこを直接見る。

```python
# main.py:108-112
env_path = Path(instance_path) / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path), override=True)
    refresh_runtime_config_from_env()
```

`override=True` なので、`config.py` の `find_dotenv(usecwd=True)` で読んだ内容よりも
こちらが優先される。設定はここに置くのが正しい。

### 注意：アプリ更新で消える

site-packages配下なので、**アプリを更新・再インストールすると `.env` も
`memory.v1.json` も失われる**。「本体のアプリ本体を直接触るな」という原則と矛盾する
場所に、アプリ自身が状態を書いている。

対策として、`.env` とカスタムプロファイルはこのリポジトリ側で管理し、更新のたびに
転送し直す運用にする。

### 記事化の観点

- 公式READMEの記載（`~/.local/share/...`）と実機の挙動が食い違う。日本語記事でも
  英語記事でも触れられていない。設定を変えようとして最初に詰まる箇所。
- 「アプリ更新で設定が消える」は実際に踏むと分かりにくい罠。

### 日本語対応の実機検証：案0は失敗、原因が確定（2026-08-29）

`.env` に `REALTIME_TRANSCRIPTION_LANGUAGE=ja` を設定してアプリを再起動し、実機で
日本語で話しかけた結果を記録する。

#### 設定が読まれたことの確認

```text
INFO reachy_mini_conversation_app.utils:114 | Loaded instance configuration from
  /venvs/apps_venv/lib/python3.12/site-packages/reachy_mini_conversation_app/.env
INFO reachy_mini_conversation_app.utils:123 | Configured Hugging Face realtime backend,
  connection mode: deployed
INFO reachy_mini_conversation_app.huggingface_realtime:1063 | Allocated realtime session ...
INFO reachy_mini_conversation_app.huggingface_realtime:712 | Realtime session initialized
  with profile=None voice='Ono_Anna'
```

`.env` は正しく読み込まれた。ログは
`journalctl -u reachy-mini-daemon` で確認できる（アプリはdaemonの子プロセス）。

#### 現象：日本語音声が欧州言語として文字起こしされる

```text
role=user content=Nihongo de Sabete has in this kiddo.     ← 「日本語で話せますか？」
role=user content=Ich hungere.                             ← ドイツ語として解釈された
role=user content=Imani hongole sabet ter no.              ← 「今日本語で話してるの」
role=user content=Montanchantus Averity no canoe.
```

#### 原因（確定）

**deployedバックエンドのSTTは日本語に対応していない。**
ローマ字風の綴りに崩れるだけでなく、`Ich hungere.` のように**ドイツ語として
出力された**。日本語対応モデルではこうならない。既定STTである
Parakeet TDT（25欧州言語、日本語を含まない）の挙動と一致する。

`REALTIME_TRANSCRIPTION_LANGUAGE=ja` は `.env` から読み込まれているにもかかわらず
効かなかった。サーバ側で無視されたか、モデルがその言語を扱えないためと考えられる。

**したがって、deployedモードのままでは日本語で使えない。**
設定変更では解決せず、STTの差し替えが必須。

#### 副産物：出力側は日本語に対応していた

```text
role=assistant content=もちろん！日本語で話せるよ。何を手伝おうか？
role=assistant content=ごめんね、聞き取り違えたかも。日本語で話しているんだね
```

- LLMは日本語で応答できる
- TTS（`voice='Ono_Anna'`）は日本語を発話できた。`Ono_Anna` が日本語ボイスという
  推測が裏付けられた
- 既定プロファイルの `You speak English by default` という指示は、会話の流れで
  上書きされた。プロンプトは絶対的な制約ではない

つまり詰まっているのは**入力STTの1箇所だけ**。

#### 副産物：ターン遅延の実測値

```text
Turn latency: response.created 1369 ms after user transcript
Turn latency: first audio delta 1410 ms after user transcript
（短い発話では 852 ms / 916 ms）
```

- deployedモード、Wireless版本体、日本の自宅Wi-Fi環境での値
- `user transcript` 確定からの計測なので、VADとSTTの時間は含まない。
  体感の応答時間はこれより長い
- アプリが自前でこのログを出しているため、追加の計測コードなしで取得できる

#### 学び

- 予測（既定STTがParakeetで日本語非対応）は実機で裏付けられた。
  切り分けの鍵は**文字起こしのログを見ること**。音声の印象だけでは
  「認識が悪い」で終わってしまう。
- ローマ字化ではなく別の欧州言語に化けるのが、言語非対応の決定的なサイン。
- 応答が日本語で返ってくるため、一見「日本語対応している」ように見えてしまう。
  実際には入力が壊れているだけで、会話が成立しない。この誤解しやすさは記事の
  見出しになる。

#### 記事化の観点

- 「Reachy Miniは日本語で会話できるのか」は日本語圏で誰も検証していない。
  結論（既定では不可、STT差し替えが必要）と、その判定方法（文字起こしログ）は
  そのまま記事になる。
- `Ich hungere.` は証拠として分かりやすく、図表なしで伝わる。
- ターン遅延の実測値は英語圏でも公開されていない。

### 会話アプリのログの見方

アプリはdaemonの子プロセスとして動くため、ログはdaemonのjournalに出る。
サービス名は `reachy-mini-daemon`（`systemctl list-units | grep -i reachy` で確認できる）。

```bash
# 直近を検索する
journalctl -u reachy-mini-daemon -n 300 --no-pager \
  | grep -iE "instance configuration|realtime|transcription|role="

# 起動の瞬間から追う（流しながらUIでアプリを起動し直す）
journalctl -u reachy-mini-daemon -f
```

すべての行が `launcher.sh[PID]: reachy_mini.apps.manager.runner - WARNING - ` で
始まるが、これはdaemonが子プロセスの出力を転送しているためで、実際のレベルは
そのあとの `INFO` 側を見る。WARNINGに見えても異常ではない。

#### 見るべき行

| ログ | 意味 |
| --- | --- |
| `utils:114 \| Loaded instance configuration from .../.env` | `.env` が読まれた |
| `utils:123 \| Configured ... connection mode: deployed` | 接続モード（deployed / local） |
| `huggingface_realtime:1063 \| Allocated realtime session ...` | セッション確保に成功 |
| `huggingface_realtime:712 \| Realtime session initialized with profile=... voice='...'` | 使用中のプロファイルとボイス |
| `core_tools:319 \| Found N tools to load` | 有効なツール一覧 |
| `console:899 \| role=user content=...` | **STTの文字起こし結果（確定）** |
| `console:899 \| role=user_partial content=...` | 発話中の途中結果 |
| `console:899 \| role=assistant content=...` | LLMの応答テキスト |
| `huggingface_realtime:777 \| Turn latency: response.created N ms after user transcript` | 応答生成までの遅延 |
| `huggingface_realtime:848 \| Turn latency: first audio delta N ms after user transcript` | 音声が返り始めるまでの遅延 |
| `console:851 \| User intervention: flushing player queue` | 割り込みを検知して再生を中断した |

#### 切り分けの要点

**`role=user` の行が最重要。** ここに何が入っているかで原因が一発で分かる。

- 空、でたらめ、別言語 → STTの問題
- 正しい日本語なのに `role=assistant` が英語 → プロンプトの問題

音声を聞いた印象だけでは「認識が悪い」で終わってしまい、STTとプロンプトの
どちらが原因か区別できない。ログを見るのが最短。

`Turn latency` の2行は、アプリが標準で出しているので計測コードを書かずに
遅延を測れる。ただし起点が `user transcript` 確定時点なので、VADとSTTの時間は
含まれない。

### 案1の変種：STTをOpenAI APIに出す構成（未実施）

Macでモデルを回さず、STTを外部APIへ委譲する。`speech-to-speech` は
`--stt openai` でOpenAI互換の `/v1/audio/transcriptions` に投げられる。

```text
VAD音声 -> POST /v1/audio/transcriptions
```

#### 使えるフラグ（実装から確認）

- `--openai_stt_base_url` / `--openai_stt_model` / `--openai_stt_language`
- `--openai_stt_api_key`（省略時、base_urlが `https://api.openai.com/v1` の場合のみ
  `OPENAI_API_KEY` を暗黙に使う。他のエンドポイントには渡されない）
- `--openai_stt_response_format`（`json` / `text`）
- TTS側も同様に `--tts openai` ＋ `--openai_tts_base_url` / `--openai_tts_model` /
  `--openai_tts_voice` / `--openai_tts_sample_rate` で外部化できる

`gpt-transcribe` では言語ヒントを複数形の `languages[]` で送り、応答の
`languages` から検出言語を読む。旧モデルや互換サーバは単数形の `language`。
この差はハンドラ側が吸収する。

#### コスト上の注意

`enable_live_transcription` の既定値は **True**（`module_arguments.py:65`）。
発話中に累積音声を `live_transcription_update_interval`（既定0.5秒）ごとに
再アップロードするため、有料APIではリクエスト数が大幅に増える。
外部STTを使うときは明示的に切る。

```bash
--enable_live_transcription False
```

#### 起動時のチェック挙動

ハンドラは起動時に**1秒の無音を実際にエンドポイントへ投げて疎通確認する**。
エンドポイント・認証・モデル・レスポンス形式のいずれかが誤っていると、
realtimeサーバがセッションを受け付けない。設定ミスは起動時点で分かる。

#### 実行場所の選択肢

STT・LLM・TTSをすべて外部APIにすると、`speech-to-speech` 側にはVAD（Silero VAD v5）と
セッション管理しか残らない。したがって理屈上は本体のCM4でも動く可能性がある。

- 案1-A: Macで `speech-to-speech serve` を動かし、STT/LLMをOpenAIへ。TTSはローカルの
  Qwen3-TTS（無料、`Ono_Anna` で日本語発話が実機確認済み）。素直で確実
- 案1-B: **本体上で `speech-to-speech` を動かし、全段を外部APIへ。**Mac不要で
  ロボット単体運用になる。ただし依存パッケージ（torch等）がCM4に入るか、
  ディスクとメモリが足りるかは未検証。成立すれば日本語圏・英語圏ともに
  事例が見当たらない構成（要検証）

#### 記事化の観点

案1-Bが成立するなら「クラウドAPIだけで、ロボット単体で日本語会話」という構成になり、
DGX SparkやGPU前提の既存記事（akiiiiita、h3adeu、npaka）とは別の軸になる。
必要なのはAPIキーだけで、再現ハードルが低い。

### deployedバックエンドは段単位で差し替えられない

「STTだけOpenAI APIにして、他はHFのまま」という構成は**取れない**。

deployedモードでは、VAD/STT/LLM/TTSの4段すべてがHF側のサーバ内で動いている。
クライアントから渡せるのはセッション設定（プロファイル、ボイス、文字起こし言語）だけで、
パイプラインの途中に自分のSTTを差し込む口がない。

したがって、

```text
STTを差し替えたい
  → 自前の speech-to-speech サーバを立てる（localモード）以外に方法がない
    → その時点で LLM と TTS も自分で指定することになる
```

ただし「他はHFのまま」に近い形は作れる。自前サーバの各段の向き先を選ぶだけ。

- STT: OpenAI API（`--stt openai`）
- LLM: HF Inference Providers（`https://router.huggingface.co/v1` はOpenAI互換。
  `speech-to-speech` のREADMEもLLMスロットの選択肢として明記している）
- TTS: HF Inference ProvidersのOpenAI互換 `/v1/audio/speech` に向けられれば
  `--tts openai` で済む。未確認（トークンなしでは401しか返らず、
  エンドポイントの存在を確認できなかった。要検証）

TTSがHF側で使えない場合の代替は2つ。

- OpenAIのTTSに向ける（`tts-1` は $15/100万文字。30分の会話で約$0.05なので影響は小さい）
- Macでローカルに回す（無料だが、案1-Bの「本体単体」という前提は崩れる）

### deployedバックエンドの正体が確定した

`huggingface/speech-to-speech` のREADMEに次の記述がある。

```text
This pipeline runs in production as the conversation backend for
thousands of Reachy Mini robots.
```

**deployedモードのバックエンドはこのパイプラインそのもの**と公式に書かれている。
これまで「ボイス名の一致から推定」としていた点が確定した。

したがって、既定STTがParakeet TDT（25欧州言語、日本語なし）であることも
ほぼ確定と扱ってよい。実機で日本語がドイツ語として文字起こしされた現象と整合する。

### API利用時のコスト見積もり（2026-08-29時点の価格）

前提: 30分セッション、ユーザー発話60回×平均5秒（合計5分）、返答は既定プロンプト通り
1〜2文（日本語60文字程度）。

単価:

- `gpt-transcribe`: $0.0045 / 分
- `gpt-5.6-terra`: 入力 $2.00 / 出力 $12.00（100万トークン、Standard・short context）。
  キャッシュ入力は $0.20
- `tts-1`: $15 / 100万文字

| 段 | 内訳 | 費用 |
| --- | --- | --- |
| STT（live transcription off） | 5分 | $0.02 |
| STT（live transcription on） | 20〜32分相当 | $0.09〜0.15 |
| LLM 入力 | 3,000 tok × 60ターン = 180k | $0.36 |
| LLM 出力 | 60 tok × 60ターン = 3.6k | $0.04 |
| TTS | 3,600文字 | $0.05 |
| 合計（live on） | | **約 $0.55 / 30分** |

- 毎日30分使っても月 $15〜17程度
- **支配的なのはLLMの入力トークン（約65%）**。原因は17個のツールスキーマが
  毎ターン送られること。プロファイルの `default_tools` を削ると直接効く
- プロンプトキャッシュが効けば入力単価は1/10になり、LLM分は $0.36 → $0.04 まで
  下がる余地がある（`responses-api` 経由で実際に効くかは未検証）

#### live transcriptionのコスト構造

累積した発話を毎回再アップロードするため、理屈上は発話長の2乗で増える。

```text
5秒の発話  → 0.5s,1.0s,...,5.0s を再送 = 27.5秒 + 確定分5秒 ≈ 6.5倍
10秒の発話 → ≈ 11.5倍
```

実際には「進捗リクエストは同時に1本まで、それ以外は破棄」という実装のため
往復遅延で頭打ちになり、4〜6倍程度に収まる。30分あたりの差額は$0.1未満なので
有効のままでも実害は小さいが、長く喋る使い方では効いてくる。

#### アイドル時は課金されない

`idle_policy.py` は待機中の動作をローカルの重み付きランダムで選ぶ実装
（"Local idle tool selection and dispatch"、60%が「何もしない」）。LLMを呼ばない。

`REACHY_MINI_APP_TIMEOUT_MINUTES` の既定は1440分なのでアプリは立ち上がったままだが、
黙っていれば費用は発生しない。課金されるのは発話したときだけ。

### 「まとめてのAPI」の正確な意味（内部は分割、外向きは1本）

前の記述は不正確だった。整理する。

**内部は4段に分割されている。**公式リポジトリのREADMEが
`VAD -> STT -> LLM -> TTS` の modular pipeline と明記しており、さらに
`The LLM slot speaks OpenAI-compatible protocols` とある。つまりHF側のサーバ内部でも
LLMは別のAPIを呼んでいるはず。

**外向きのインターフェースは1本のWebSocket**（OpenAI Realtime互換）で、音声を送って
音声が返る。クライアントが指定できるのはセッション設定のフィールドだけ。

`_get_session_config()`（`huggingface_realtime.py:222-246`）が送っている全項目:

| フィールド | 内容 | 効いたか |
| --- | --- | --- |
| `instructions` | プロファイルのプロンプト | 効く |
| `audio.input.format` | 16kHz PCM | - |
| `audio.input.transcription.model` | **`"gpt-4o-transcribe"` がハードコード** | 未検証 |
| `audio.input.transcription.language` | `REALTIME_TRANSCRIPTION_LANGUAGE` | **効かなかった** |
| `audio.input.turn_detection` | `server_vad`, `interrupt_response=True` | - |
| `audio.output.voice` | ボイス名 | **効いた**（`Ono_Anna` で日本語発話） |
| `tools` / `tool_choice` | ツール定義 | 効く |

つまり「段ごとに差し替えられない」のではなく、**段ごとのパラメータを渡す口は
プロトコルに存在する**。STTモデル名のフィールドもある。差し替えられないのは
「STTの実装そのものを自分のサーバに向けること」。

### 未検証の可能性：STTモデル名を変えれば通るかもしれない

`voice` は明確に効いた（Qwen3-TTSのスピーカー名を渡して日本語音声が出た）。
つまりHF側サーバは**段ごとのパラメータを少なくとも一部は尊重している**。

とすれば `audio.input.transcription.model` も尊重される可能性がある。
現状は `"gpt-4o-transcribe"` がコードにハードコードされており、環境変数では変えられない
（`MODEL_NAME` は `_OBSOLETE_BACKEND_ENV_NAMES` で無視される）。

#### 試す価値のある実験（低コスト）

本体上の該当ファイルを1行書き換えて、日本語対応の文字起こしモデル名を渡してみる。

```python
# /venvs/apps_venv/lib/python3.12/site-packages/reachy_mini_conversation_app/
#   huggingface_realtime.py:233
model="gpt-4o-transcribe",   # ← ここを別のモデル名に変える
```

- site-packages配下なのでアプリ更新で戻る。実験用途には都合が良い
- 期待する結果は3通りで、どれでも情報になる
  1. 日本語が認識される → **deployedのまま無料で日本語対応できる**。最良
  2. サーバがエラーを返す → このフィールドは検証されている＝尊重されている証拠。
     受け付けるモデル名を探す価値がある
  3. 無視されて何も変わらない → `language` と同様に無視されている。案1-Bへ進む
- 渡すモデル名の候補は不明。HF側が何を受けるかは公開されていない（要検証）

`language=ja` が効かなかった事実は、サーバがこのフィールド群を無視している可能性と、
Parakeetが日本語コードを受け付けない可能性の両方と整合する。切り分けにはモデル名側の
実験が必要。

### 全体構成の理解（deployedモードの実像）

会話アプリは**AIモデルを1つも持っていない**。ロボット上の依存はこれだけ。

```toml
dependencies = [
    "huggingface-hub", "httpx", "python-dotenv",
    "openai==2.28.0",            # HFバックエンドと話すため
    "reachy_mini_dances_library", "reachy-mini", "mcp",
]
```

実機で確認しても、`apps_venv`（254パッケージ）に `speech_to_speech`・torch・
Whisper・Parakeet・Qwen 関連は**一つも入っていない**。

```text
ロボット (CM4)                        HF のサーバ（クラウド）
┌────────────────────┐            ┌──────────────────────┐
│ 会話アプリ            │            │ speech-to-speech      │
│  = Realtimeクライアント│──WebSocket─▶│  VAD → STT → LLM → TTS│
│  モデルは持たない      │◀───────────│                       │
└────────────────────┘  音声/音声  └──────────────────────┘
```

つまり「s2sを使っている」は正しいが、**動いている場所はHFのクラウド**。ロボットは
WebSocketで音声を送受信するだけ。だからCM4でも成立している。

アプリから見れば接続先URLが変わるだけなので、話し相手は
deployed / 自前s2s / 自作サーバのどれでも差し替えられる（`.env` の2行）。

### 音声は常時クラウドへ送られている

`input_audio_buffer.append` にゲートが無く（`huggingface_realtime.py:976-979`）、
VADもサーバ側（`server_vad`）。つまり**アプリ起動中はマイク音声を送り続けている**。

帯域の概算（16kHz モノラル PCM16、base64エンコード）:

| 項目 | 値 |
| --- | --- |
| 生PCM | 32 kB/s = 256 kbps |
| base64後 | 約 43 kB/s = 341 kbps |
| 1時間あたり（送信のみ） | 約 154 MB |
| 応答音声を含めた往復 | 概算 300 MB/時 |

含意:

- 無音・生活音・家族の会話もすべてHFへ送られる。プライバシー観点の指摘として記事価値が高い
- テザリングや従量制回線では通信量が問題になる
- HF側は数千台ぶんの常時音声を受けて、STT・LLM・TTSを**無料で**回している。
  ハードを売って推論コストを負担するモデル
- 遅延1.4秒が出ているのは、4段がHF側に同居しており、ネットワークを渡るのが
  音声の往復1回だけだから。段ごとに別のクラウドを呼ぶ構成より有利

### 記事化の観点

「$299のロボットが、実は喋っていない間もクラウドに音声を送り続けている」は、
仕組みの説明として分かりやすく、かつ誰も書いていない。帯域の実数と
`input_audio_buffer.append` にゲートが無いというコード根拠を添えられる。

### 実装方針の検討：4つの選択肢と結論

日本語対応のために「deployedバックエンドを離れる」と決めたあと、どう作るかを比較した。

#### 選択肢

| 案 | 内容 | 判断 |
| --- | --- | --- |
| 1 | `speech-to-speech` をそのままインストールして使う | 依存が重い。**却下** |
| 2 | `speech-to-speech` をforkして削る | 読む量が多い。**却下** |
| 3 | Realtimeサーバを自作（アプリは無改造） | 不要なプロトコル実装が発生。**次善** |
| 4 | **会話アプリをforkし、バックエンドを直接API呼び出しに置き換える** | **採用** |

#### 案1・2を却下した理由

`speech-to-speech` の必須依存（非Darwin）に次が含まれる。

- `torch` aarch64 wheel **427MB**（+ transformers、librosa 等）
- `faster-qwen3-tts[ggml]` → `qwentts-cpp-python` の配布wheelは
  **`cu128`（CUDA 12.8）かつ `manylinux_2_39`**。CM4にCUDAは無く、glibcも古い可能性が高い。
  **使わないTTSの依存でインストールが失敗しうる**

VADが `torch` を使う実装（`VAD/vad_iterator.py:3` で `import torch`）なので、torchは
「使わない依存」ではなく必須。本体の空きは4.3GBで入る見込みではあるが、
**使いたいのはVAD1つだけなのに代償が大きい。**

fork案（2）は、プロトコル層が `api/openai_realtime` で**5,951行**。WebRTC、複数
パイプライン、ライブ文字起こし、バックエンド抽象など不要な機能が理由で膨れている。
削るつもりで読むと pipeline 抽象まで芋づるになり、上流（0.2.12、活発）との乖離も負債。

#### 案3より案4が良い理由

決め手は、**会話アプリに差し替え口が用意されていた**こと。

```python
# main.py:167-184
def build_handler(startup_voice=None) -> ConversationHandler:
    from ...huggingface_realtime import HuggingFaceRealtimeHandler
    return HuggingFaceRealtimeHandler(...)
handler = build_handler(startup_settings.voice)
... handler_factory=build_handler
```

- 抽象基底クラス `conversation_handler.py` は**159行**
- 実装が必要な抽象メソッドは**9個**（`_is_connected` / `start_up` / `shutdown` /
  `receive(frame)` / `say(text)` / `apply_personality` / `get_available_voices` /
  `get_current_voice` / `change_voice`）
- `emit()` と文字起こし通知は基底クラスが実装済み
- アプリ全体9,567行のうちバックエンドは `huggingface_realtime.py` の1,069行＝11%だけ。
  かつて `BACKEND_PROVIDER` で複数バックエンドを選べた設計の名残

| | 案3：Realtimeサーバ自作 | 案4：appをfork |
| --- | --- | --- |
| 実装対象 | プロトコル13イベントの組み立て・順序・割り込み畳み | 抽象メソッド9個 |
| 仕様の参照先 | OpenAI Realtimeの挙動（s2sを読む） | `conversation_handler.py` 159行 |
| プロセス数 | 2 | **1** |
| ネットワークホップ | localhost WSが1つ増える | **無し** |
| ツール実行 | WS越しに `call_id` を往復 | **同一プロセス内の関数呼び出し** |
| 割り込み | プロトコルで畳む | 既存の再生キューflushを使える |
| アプリ変更 | ゼロ | 新規1ファイル＋`build_handler` 数行 |
| 上流追従 | 不要 | 必要（ただし差分は小さい） |

案3は「両端が自分のものなのにJSONイベントでやり取りする」無駄が本質的にある。
特にツール呼び出しを同一マシン内でシリアライズするのは筋が悪い。

#### 案4のリスクと軽減

- **fork維持**：差分が新規1ファイル＋数行なので取り込みは容易。UI・プロファイル・
  17ツール・moves・記憶・MCPは触らないので競合しない
- **配布**：ロボットへは rsync + `/venvs/apps_venv/bin/pip install` で直接入れる。
  HF Spaceへのpublishは後回しでよい
- **退路**：環境変数で `deployed` / `direct` を切り替えられるようにし、既存動作を残す

#### 採用構成

| 段 | 実装 | 検証状況 |
| --- | --- | --- |
| VAD | ハンドラ内（`receive()`）。`webrtcvad` か silero-onnx | 未 |
| STT | OpenAI `gpt-transcribe`（$0.0045/分） | 未 |
| LLM | HF router `Qwen/Qwen3-4B-Instruct-2507`（入力$0.01/1M） | **✅ 日本語・tool calling・streamを実機から確認** |
| TTS | OpenAI `gpt-4o-mini-tts` か ローカルKokoro（82M） | 未。HFは音声エンドポイント404 |

torchもqwentts依存も不要になり、CM4でも成立する見込み。

#### fork済み

```text
origin   https://github.com/optimisuke/reachy_mini_conversation_app.git
upstream https://github.com/pollen-robotics/reachy_mini_conversation_app.git
clone先  /Users/ito/Private/reachy_mini_conversation_app
基点     531baaa (2026-08-19, v1.0.1)
```

### 未解決・要検証

- `local` モード＋Whisperでの日本語認識精度と遅延の実測（次にやること）
- deployedバックエンドのSTTがParakeet TDTそのものかどうか
  （日本語非対応であることは確定。モデル名は未確定）
- daemonの顔検出器の実装
- CM4上でwhisper.cpp tiny/baseがどこまで動くか、daemonへの影響
- アプリ更新時に `.env` が実際に消えるか（更新手順ごとの挙動）
- VAD・STTを含めた体感応答時間（`user transcript` 前の時間）の測り方
- 案1-B（本体上でVADのみ、全段クラウド）がCM4で成立するか
- OpenAI STTでの日本語認識精度と、ターン遅延の増減
- HF Inference Providers に OpenAI互換の `/v1/audio/speech` があるか（TTSの向き先）
- プロンプトキャッシュが `responses-api` 経由で効くか
- `audio.input.transcription.model` をHF側サーバが尊重するか（1行書き換えで検証可能）

## 直接API版バックエンドの実装（2026-08-30）

fork（`/Users/ito/Private/reachy_mini_conversation_app`）に `CONVERSATION_BACKEND=direct` を追加し、
ハンドラ内 VAD → STT → LLM → TTS を自前で回す `DirectCascadeHandler` を実装した。
既定（`huggingface`）は無改造で残してあるので、日本語が駄目なら env 1行で戻せる。

追加・変更したファイル:

```text
新規 src/reachy_mini_conversation_app/direct_cascade.py    # ハンドラ本体
新規 src/reachy_mini_conversation_app/speech_services.py   # STT/LLM/TTS の抽象と OpenAI互換実装
新規 src/reachy_mini_conversation_app/voice_activity.py    # エネルギーVAD（発話区切り）
新規 src/reachy_mini_conversation_app/audio/pcm.py         # WAV化・PCMデコード・リサンプル
新規 profiles/default_ja/profile.md                        # 日本語で話すプロファイル（バンドル品は複製）
変更 config.py / main.py / console.py / streaming.py / conversation_handler.py
```

### 現象：新バックエンドだとUIが「未接続」のまま出る（実装前に発見）

- **原因**：`console.py` の `_backend_connected()` が `vars(self.handler)["connection"]` を直接見ていた。
  Realtime ハンドラの属性名に依存した実装で、`connection` 属性を持たないハンドラは常に未接続扱い。
- **解決**：`self.handler._is_connected()`（基底クラスの抽象メソッド）を呼ぶよう変更。
  `console.py:582` が既に `_is_connected()` を呼んでいた前例があるので方針も一貫する。
- **学び**：`ConversationHandler` を実装するときは抽象メソッド以外にも
  「基底クラス経由でない暗黙の期待」がある。`vars(handler)` / `getattr(handler, ...)` を grep して洗い出すこと。

### 現象：`start_up()` が返ると5秒後に再接続が走る

- **原因**：`console.py` の `_run_handler_startup_loop()` は `await handler.start_up()` の
  **正常 return を「セッション終了」と解釈**して `_backend_retry_delay`（5秒）後にやり直す設計。
  Realtime 実装は `async for event in connection` でセッション寿命ぶんブロックしている。
- **解決**：`start_up()` の末尾で `await self._stopped.wait()`（`shutdown()` がセットする）してブロックする。
- **学び**：`start_up()` は「起動処理」ではなく「セッションを張っている間ずっと動く」契約。

### 現象：TTS音声のサンプルレートを誰も見てくれない

- **原因**：`console.py` の `play_loop` は `handler.emit()` が返す `(rate, samples)` の
  **rate を捨てて** `robot.media.push_audio_sample()` に渡す。SDK 側は
  `AudioBase.SAMPLE_RATE = 16000` 固定（入力 `get_audio_sample()` も 16kHz float32 mono）。
  一方 OpenAI `/v1/audio/speech` の `response_format="pcm"` は **24kHz 固定**（レート指定不可）。
- **解決**：ハンドラ側で 24k→16k にリサンプルしてから queue に載せる。
- **学び**：会話アプリの音声配管は入出力とも 16kHz mono 決め打ち。外部TTSを足すなら変換は自分の責任。

### 収穫：scipy と onnxruntime は既に依存に入っている

`reachy-mini` 1.10.0rc5 の依存に `scipy` と `onnxruntime` がある（`uv.lock` で確認）。つまり:

- リサンプルは `scipy.signal.resample_poly` が**新規依存なし**で使える（自作FIRは不要だった）
- silero-VAD の ONNX 版も **onnxruntime の追加インストールなし**で後から差し替えられる
  （モデルファイルの配布だけが課題）。今回はエネルギーVADで始めたが、退路はある。

### 現象：エネルギーVADが一度も発火しない

- **原因**：ノイズフロアを「全ての窓」で更新していたため、発話オンセットを数えている 6 窓（0.12秒）のあいだに
  **フロア自身が発話レベルへ引き上げられ、閾値（フロア×3）が入力を追い越した**。
  0.02 RMS の入力に対しフロアが 0.006→0.0067 に上がるだけで閾値が 0.02 を超える。
- **解決**：非 voiced（背景と判定した）窓だけでフロアを学習する。
- **学び**：適応閾値は「自分が測っている対象で自分を更新しない」。教科書どおりだが、実装すると踏む。

### 現象：`RuntimeWarning: Mean of empty slice` が出て区切りがおかしい

- **原因**：`push()` が窓をループしている最中に、発話確定 → `reset()` が
  **入力バッファ `_pending` を空にしていた**。ループは以降 空スライスを処理していた。
- **解決**：`_pending` の所有を `push()` に一元化し、ループ前に残りを確定させる。`reset()` は発話状態だけ触る。
- **学び**：ステートマシンのリセットが、呼び出し側のイテレーション対象を壊していないか確認する。

### 連続騒音はエネルギーVADの原理的な弱点

閾値を越える騒音（扇風機など）が鳴り続けると、voiced 判定が続いてフロア学習が止まり、
20秒の発話として切られ続ける。対策として **max_utterance で切ったときだけ、その区間のRMSを
新しいノイズフロアとして再学習**する自己修復を入れた。人間の発話が20秒で切られた場合も、
直後の無音でフロアは速く（係数0.3）落ちるので次のターンには影響しない。

### 最小発話長は「voiced 窓の合計」で見る

`min_utterance_s` を utterance 全体の長さで判定すると、preroll（0.3秒）＋末尾無音（0.7秒）が
含まれるので 0.2秒の咳でも 1.2秒になり、フィルタとして機能しない。voiced と判定した窓の合計で見る。

### OpenAI SDK 2.28 の細部

- async の `client.audio.speech.create(...)` は `HttpxBinaryResponseContent` を返すので
  **`await response.aread()`** でバイト列を取る。
- chat completions のツール定義は Realtime と形が違う（`{"type":"function","function":{...}}`）。
  ストリームのツール呼び出しは `delta.tool_calls[i]` に **index ごとの断片**で来るので
  `id` は最初の断片、`arguments` は連結して組み立てる。
- `numpy` 絡みで mypy strict が `no-any-return` を出す場合、`np.clip(...).astype(...)` を
  一度 注釈付き変数に受けると通る（scipy に型がないため）。

### `REALTIME_TRANSCRIPTION_LANGUAGE=ja` がついに効く

直接バックエンドの STT language にこの既存変数をそのまま流用した。新しい変数を増やさずに、
これまで「読み込まれるが無視されていた」設定が意味を持つようになる。

### 実機での確認手順（次にやること）

```bash
rsync -a --delete --exclude .git --exclude .venv \
  /Users/ito/Private/reachy_mini_conversation_app/ pollen@reachy-mini.local:/tmp/conv-app/
ssh pollen@reachy-mini.local '/venvs/apps_venv/bin/pip install /tmp/conv-app'
# instance の .env に CONVERSATION_BACKEND=direct / OPENAI_API_KEY / REALTIME_TRANSCRIPTION_LANGUAGE=ja
#   REACHY_MINI_CUSTOM_PROFILE=default_ja を書く
curl -X POST http://localhost:8000/api/apps/start-app/reachy_mini_conversation_app
journalctl -u reachy-mini-daemon -f | grep -E "role=(user|assistant)|Direct backend|Turn latency"
```

確認したいのは `role=user content=...` に**日本語が出るか**（STT の切り分け点）、
`Turn latency: assistant text ... ms` の実測、VAD 閾値（`DIRECT_VAD_*`）の実環境での妥当性。

### ローカルでのゲート結果（2026-08-30）

`uv sync --frozen` 済みの `.venv` で:

```text
ruff format --check .   87 files already formatted
ruff check .            All checks passed
mypy (strict, 49 files) Success
pytest                  360 passed, 3 failed
```

失敗3件は `tests/test_personality_avatars.py` で、**このマシンに git-lfs が入っておらず
アバターSVGがLFSポインタのまま**なのが原因（`assert '<svg' in 'version https://git-lfs...'`）。
実装とは無関係。pristine な worktree でも同じ。

もう一点、`tests/test_console.py` が丸ごとハングする現象に当たった:

- **原因**：`_backend_connected()` を `handler._is_connected()` に変えたところ、
  テストのハンドラが `MagicMock` なので **MagicMock が返り、JSON-RPC 応答の
  シリアライズができずクライアントが待ち続けた**（例外ではなく無応答になる）。
- **解決**：`bool(...)` で包む（戻り値の型注釈どおりにする）。テスト側の偽ハンドラにも
  `_is_connected()` を実装、または `_is_connected.return_value = False` を設定。
- **学び**：JSON-RPC の応答に入る値は必ず素の型にする。MagicMock は「例外を出さずに固まる」
  という最悪の壊れ方をする。

### 実APIでの疎通確認は未達（鍵が401）

STT/TTS だけを実APIに投げる確認スクリプトを書いたが、環境変数の `OPENAI_API_KEY` が
**401 invalid_api_key** で通らなかった。有効な鍵を入れれば次のスクリプトで
「日本語を合成 → 16kHzへリサンプル → 文字起こし」を一発で確認できる:

```python
# /tmp/smoke_direct.py
import asyncio, os, sys
sys.path.insert(0, "/Users/ito/Private/reachy_mini_conversation_app/src")
from openai import AsyncOpenAI
from reachy_mini_conversation_app.audio.pcm import resample
from reachy_mini_conversation_app.speech_services import (
    OpenAICompatibleSpeechToText, OpenAICompatibleTextToSpeech,
)

async def main() -> None:
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=60.0)
    tts = OpenAICompatibleTextToSpeech(client, "gpt-4o-mini-tts", 24000, voice_override=None)
    stt = OpenAICompatibleSpeechToText(client, "gpt-4o-transcribe", "ja")
    pcm24 = await tts.synthesize("今日はいい天気ですね。", "Ono_Anna")
    pcm16 = resample(pcm24, 24000, 16000)
    print(len(pcm24) / 24000, "s ->", await stt.transcribe(pcm16, 16000))
    await client.close()

asyncio.run(main())
```

ここで日本語が返れば、実機で詰まっていた STT の1点が解消していることになる。
LLM 段（HF router / Qwen3-4B）は実機で既に確認済みだが、このマシンには HF トークンがない。

### 鍵なしでの結線確認：ローカルにOpenAI互換サーバを立てて全段を通した

実APIの鍵が使えなかったので、`/v1/audio/transcriptions`・`/v1/audio/speech`・
`/v1/chat/completions`(SSE) を返すFastAPIサーバをローカルに立て、`DIRECT_*_BASE_URL` を
そこへ向けて `DirectCascadeHandler` を丸ごと動かした（スクリプト: `/tmp/local_stack_check.py`）。
ユニットテストのフェイクでは分からない**ワイヤ形式**が確認できる。

結果（すべて期待どおり）:

```text
transcriptions: model=gpt-4o-transcribe language=ja
                wav=(1ch, 2bytes, 16000Hz, 20800frames=1.3s) name=utterance.wav
speech:         model=gpt-4o-mini-tts voice=nova format=pcm
                input='やあ、元気？' / 'またね。'      ← 文単位で分割されている
chat:           model=Qwen/Qwen3-4B-Instruct-2507 tools=['dance']
                roles= system,user
                     → system,user,assistant,user
                     → system,user,assistant,user,assistant,tool
playback:       39 frames / 24000 samples @16k = 1.50s（24kHz 0.5s×3 → 16kHz 0.5s×3）
```

確認できたこと:

- `voice = "Ono_Anna"`（プロファイル）→ プロバイダの `nova` へのマッピングが効いている
- SSE のツール呼び出しが **2つの断片に分かれて届いても** `{"name":"macarena"}` に組み立てられる
- ツールは実際に `dispatch_tool_call` を通って走った（`{"status":"queued","move":"head_tilt_roll"}` が返った）
- ツール結果を `role=tool` で戻して**2周目の応答**まで回る
- `profiles/default_ja` が実パスで読まれ、日本語の greeting が最初のターンとして送られる
- リサンプルで**尺が保たれている**（0.5s×3 = 1.50s）
- 発話区切り：「やあ、元気？」で読点では切らず、`？`『。』で切っている

このスクリプトは**リポジトリには入れていない**（uvicorn をスレッドで立てる重いフィクスチャで、
CIでポート/タイミング由来のflakyになりやすい）。振る舞いのテストは
`tests/test_direct_cascade.py` などのユニットテスト側で担保している。

残るは実機での確認だけ:

1. 実際のマイク音声で VAD 閾値（`DIRECT_VAD_*`）が妥当か
2. `role=user content=...` に**日本語**が出るか（実APIのSTT）
3. ターン遅延（`Turn latency: assistant text ... ms`）とCM4のCPU負荷

