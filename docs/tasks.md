# Reachy Mini SDK 検証タスク

更新日: 2026-08-30

優先度は「P」列にユーザーが記入する。未記入は優先度未定を意味する。
状態は 未着手 / 調査中 / 解決 / 要検証 のいずれか。

## 現在の環境

- Wireless版 Reachy Mini
- 本体daemon: 1.10.0
- Mac側 `reachy-mini` SDK: 1.10.0
- Python: Mac 3.12 / 本体 `apps_venv` 3.12.12（本体のシステムPythonは3.13.5）
- 実機Appは停止した状態でテスト
- Mac→本体はSSH鍵認証済み。エージェントから `scp` + `ssh` で非対話実行できる

## 検証済みスクリプト

| スクリプト | 実行場所 | 状態 |
| --- | --- | --- |
| `hello.py` | Mac | 動作確認済み（`--voice` も可） |
| `hello_on_robot.py` | 本体 | 動作確認済み |
| `body_rotation.py` | Mac | 動作確認済み |
| `body_rotation_on_robot.py` | 本体 | 動作確認済み |
| `audio_playback.py` | Mac | 動作確認済み |
| `audio_playback_on_robot.py` | 本体 | 動作確認済み |
| `camera_snapshot.py` | Mac | 動作確認済み |
| `camera_snapshot_on_robot.py` | 本体 | 動作確認済み |
| `face_tracking.py` | Mac | 動作確認済み（修正後） |
| `face_tracking_on_robot.py` | 本体 | 動作確認済み |
| `recorded_moves_on_robot.py` | 本体 | 動作確認済み（ダンス19種・感情85種） |
| `antenna_input_on_robot.py` | 本体 | 動作確認済み |
| `mic_recording_on_robot.py` | 本体 | 動作確認済み（合図音付き） |

---

# A. モーション再生

## A-1. ダンスライブラリを再生する

| P | 状態 |
| --- | --- |
|  | 完了（2026-08-30） |

`pollen-robotics/reachy-mini-dances-library` がdaemon起動時にプリダウンロード済みで、
**19種類**が即使える。

```
yeah_nod, chin_lead, dizzy_spin, neck_recoil, pendulum_swing,
interwoven_spirals, sharp_side_tilt, polyrhythm_combo, side_to_side_sway,
side_glance_flick, chicken_peck, simple_nod, side_peekaboo,
stumble_and_recover, groovy_sway_and_roll, grid_snap, jackson_square,
head_tilt_roll, uh_huh_tilt
```

```python
from reachy_mini.motion.recorded_move import RecordedMoves
moves = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
mini.play_move(moves.get("simple_nod"), sound=True)
```

やること:

- `--list` で一覧、名前指定で再生できるスクリプトを作る
- 短いもの（`simple_nod`）から試し、本格的なもの（`groovy_sway_and_roll`、
  `jackson_square`）へ進む
- 再生時間、可動範囲の大きさ、机上での安定性を記録する
- `initial_goto_duration` の有無で開始時の動きがどう変わるか比較する

完了条件: 任意のダンスを名前指定で再生でき、危険なもの／安全なものを分類できる。

結果: 19件すべて1.82〜5.00秒・音なしと判明。`simple_nod` を本体上で再生し、うなずき動作を
目視確認した（定義1.82秒に対し実測2.84秒＝`initial_goto_duration=1.0` を含む）。
スクリプト: `recorded_moves_on_robot.py --library dances`（`--list` で一覧）。

残り: 長いダンス（`jackson_square` 5.00秒、`side_peekaboo` 5.00秒）の可動範囲と机上での
安定性は未確認。

## A-2. 感情モーション（Recorded Moves）を再生する

| P | 状態 |
| --- | --- |
|  | 完了（2026-08-30） |

`pollen-robotics/reachy-mini-emotions-library` に**85種類**。音付き（sidecar sound）の
ものがある。`dance1`〜`dance3`、`laughing1`、`rage1`、`proud1`、`toc-toc-toc`、
`wake-mini-up`、`mini-deep-sleep` など。

やること:

- `sound=True` / `False` で音の有無を比較する
- 初回再生時のアセット取得時間と2回目以降の差を測る（キャッシュ済みなら差は出ない見込み）
- 感情の種類ごとに動きの大きさを分類する

完了条件: 音付きで再生でき、キャッシュの効き方を説明できる。

結果: 85件中84件が音付き（`waiting` のみ音なし）。長さは2.14〜19.76秒。
`laughing1` `proud1` `surprised1` を連続再生し、動きと音の両方を確認した。実測はいずれも
定義＋約1.1秒。スクリプト: `recorded_moves_on_robot.py --library emotions`。

残り: キャッシュ有無による初回取得時間の差は未計測（プリダウンロード済みのため差が出ない
可能性が高い）。

## A-3. `play_move` と `async_play_move` の違いを確認する

| P | 状態 |
| --- | --- |
|  | 未着手 |

docstringはどちらも "Asynchronously play a Move" と書かれており、違いが不明。

やること:

- 両者を呼んで戻るタイミングを計測する
- `cancel_move()` で再生を中断できるか確認する
- `play_frequency`（既定100 Hz）を下げると動きがどう変わるか

完了条件: 使い分けの基準を説明できる。

## A-4. モーションを自作する（記録・再生）

| P | 状態 |
| --- | --- |
|  | 未着手 |

`start_recording()` / `stop_recording()` がある。`stop_recording()` は記録データを
返す。重力補償（B-3）と組み合わせれば、手で動かした軌跡を記録できる可能性がある。

やること:

- 記録データの構造（キー、座標系、サンプリング間隔）を確認する
- 記録したデータを `Move` として再生できるか確認する
- JSONへ保存して再利用できる形にする

完了条件: 手で動かした動きを記録し、再生できる。

## A-5. `wake_up()` / `goto_sleep()`

| P | 状態 |
| --- | --- |
|  | 未着手 |

起床・就寝モーション。`wake_up()` は音も鳴る。

やること: 実行時の姿勢変化と音を記録し、スクリプトの開始・終了処理に使えるか判断する。

## A-6. 補間方法（InterpolationTechnique）を比較する

| P | 状態 |
| --- | --- |
|  | 未着手 |

`goto_target(method=...)` の既定は `MIN_JERK`。他に何が選べるか、動きの質がどう
変わるかを確認する。

## A-7. `set_target` 系（連続制御）を試す

| P | 状態 |
| --- | --- |
|  | 未着手 |

`goto_target` が「補間して移動」なのに対し、`set_target` は目標値の直接指定。
`set_target_head_pose`、`set_target_antenna_joint_positions`、`set_target_body_yaw` も
ある。

やること: ループで連続的に目標を送り、滑らかに動かせるか（制御周期、追従性）を確認する。

## A-8. 胴体回転時の首補正を比較する

| P | 状態 |
| --- | --- |
|  | 説明は判明（実測での確認は残っている） |

`automatic_body_yaw=True`（既定）では、胴体回転中に首が逆方向へ補正され頭が正面を
保つように見えた。

**公式ドキュメント（JS SDK）に説明があった。** 首が補正されているのではなく、
**頭の目標姿勢がワールド座標系で指定されている**ため、胴体が回っても頭の視線が
ワールド座標で固定され、結果として逆回転して見えるだけだった。

頭を胴体へ追従させたい場合は、頭のRPYのyawへ胴体のyaw差分を足し、`head` と `body_yaw` を
**同じ呼び出しで**送る。基準値はテレメトリの現在値ではなく、自分が最後に指令した値を使う
（テレメトリは遅れるため差分の積み上げが破綻する）。

やること: 実際に「頭を胴体へ追従させる」コードを書いて、説明どおりになるか確認する。
`set_automatic_body_yaw(False)` との違いも合わせて見る。

---

# B. モーター・センサー

## B-1. アンテナを物理入力として読む

| P | 状態 |
| --- | --- |
|  | 完了（2026-08-30） |

`get_present_antenna_joint_positions()` で現在値が読める。

やること: 押す／倒す操作と値の対応を記録し、入力デバイスとして使えるか判断する。

結果: アンテナだけトルクを切って手で動かし、角度を読めることを確認した。
スクリプト: `antenna_input_on_robot.py`。

- 可動域は左83.1°、右186.6°。符号は左右で逆（鏡像配置）
- 静止時は±0.1°程度で安定し、しきい値判定に使える
- ゼロ点はズレる（起動時の値を基準にする必要がある）
- 戻り止めがないため、ボタンではなくダイヤル／レバーとして扱うのが妥当

## B-2. 現在姿勢の読み取り

| P | 状態 |
| --- | --- |
|  | 未着手 |

`get_current_head_pose()`（4x4行列）、`get_current_joint_positions()`（頭とアンテナ）。

やること: 指令値と実測値の差、座標系の向き、4x4行列の読み方を整理する。

## B-3. 重力補償

| P | 状態 |
| --- | --- |
|  | 未着手 |

`enable_gravity_compensation()` / `disable_gravity_compensation()`。頭を手で安全に
動かせる状態になると思われる。

やること:

- 短時間だけ有効化し、手で頭を動かせるか確認する
- モーター有効時・無効時との違いを記録する
- **終了時に必ず通常状態へ戻す**

## B-4. IMU

| P | 状態 |
| --- | --- |
|  | 未着手 |

`mini.imu` プロパティ。加速度・姿勢が取れると思われる（データ構造は未確認、
`reachy_mini.io.protocol` に `IMUData` は無かった）。

やること: データ構造を確認し、本体を傾けたときの値変化を記録する。「持ち上げ検知」
などに使えるか判断する。

## B-5. モーターの部分制御

| P | 状態 |
| --- | --- |
|  | 未着手 |

`enable_motors(ids=[...])` / `disable_motors(ids=[...])` はID指定ができる。

やること: 有効なID名の一覧を調べ、頭だけ／アンテナだけの有効化を試す。

---

# C. 音声

## C-1. マイク録音

| P | 状態 |
| --- | --- |
|  | 完了（2026-08-30） |

`media.start_recording()` / `get_audio_sample()` / `stop_recording()`。
`get_input_audio_samplerate()`、`get_input_channels()` で仕様も取れる。

やること:

- 数秒録音してWAVへ保存し、再生して内容を確認する
- 入力レート・チャンネル数を記録する
- Mac経由と本体上実行の違いを記録する

結果: 5秒録音してWAV保存・再生まで確認した。スクリプト: `mic_recording_on_robot.py`。

- 入力は16000 Hz / 2 ch（出力の44100 Hzと非対称）
- `get_audio_sample()` はポーリング前提で、データが無いと `None` を返す
- float32を16bit PCMへ変換して保存する
- ピーク・RMSを表示すると「録れていない」のか「聞こえないだけ」かの切り分けが速い
- 開始・終了の合図音（`wake_up.wav` / `count.wav`）が実用上必須だった

## C-2. 音源方向推定（DoA）

| P | 状態 |
| --- | --- |
|  | 未着手 |

`media.get_DoA()` が `(角度, 有効フラグ)` を返す。ReSpeakerマイクアレイ由来。
角度はラジアンで 0＝左、π/2＝正面、π＝右（`DoaSnapshot` のdocstringより）。

やること: 左右から声をかけて値の変化を記録する。「音のした方を向く」実装を試す。

## C-3. 音声リアクティブな頭の揺れ（wobbling）

| P | 状態 |
| --- | --- |
|  | 未着手 |

`enable_wobbling()` / `disable_wobbling()`。音声再生に合わせて頭が揺れる機能。
`reachy_mini.motion.speech_tapper` と `head_wobbler` が関係していそう。

やること: 音声再生と組み合わせて動きを確認する。喋っているように見せる用途に使えるか。

## C-4. 音声ストリーミング送出

| P | 状態 |
| --- | --- |
|  | 未着手 |

`media.push_audio_sample()` でNumPy配列を直接流せる。`play_sound()` がファイル再生
なのに対し、こちらは生成した音を逐次送る用途。

やること: サイン波などを生成して流し、レイテンシと途切れの有無を確認する。

## C-5. 音量・音声設定のAPI

| P | 状態 |
| --- | --- |
|  | 未着手 |

REST APIに音量系がある。`POST /api/volume/set`、`POST /api/volume/microphone/set`、
`GET /api/volume/microphone/current`、`POST /api/volume/test-sound`、
`POST /api/audio/config/apply`、`GET /api/audio/config/parameter/{name}`。

やること: 音量変更が実際に効くか確認し、SDKからの操作方法があるか調べる。

---

# D. カメラ・ビジョン

## D-1. `look_at_image` で画像内の点を見る

| P | 状態 |
| --- | --- |
|  | 未着手 |

`look_at_image(u, v, duration, perform_movement)`。ピクセル座標を指定すると、そこを
見る姿勢になる。`perform_movement=False` なら姿勢行列だけ計算できる。

やること:

- 撮影画像から対象のピクセル座標を出し、そこを見せる
- 顔追跡を使わない「自作の追跡」が作れるか試す

## D-2. `look_at_world` で3D座標を見る

| P | 状態 |
| --- | --- |
|  | 未着手 |

`look_at_world(x, y, z, ...)`。Reachy Miniの基準座標系での点。

やること: 座標系の定義（原点、軸の向き、単位）を確認し、狙った方向を向かせる。

## D-3. 顔追跡の `weight` を比較する

| P | 状態 |
| --- | --- |
|  | 未着手 |

`start_head_tracking(weight=...)` は 0〜1。1で追跡が頭を完全に制御、中間値では
アプリ側のモーションが透けて見え、0は「検出を止めるがtrackerは破棄しない」。

やること: 0.3、0.5、1.0で動きの違いを記録する。自作モーションとの併用を試す。

## D-4. 連続フレーム取得とフレームレート

| P | 状態 |
| --- | --- |
|  | 未着手 |

`media.get_frame()`（BGRのNumPy配列）、`get_frame_jpeg()`（JPEGバイト列）。

やること: 連続取得して実効フレームレートを測る。Mac経由と本体上で比較する
（静止画では接続が5秒 vs 0.4秒と大差があった）。

## D-5. カメラ仕様とキャリブレーション情報

| P | 状態 |
| --- | --- |
|  | 未着手 |

`GET /api/camera/specs`。SDK内部では `CameraSpecs`、`intrinsics_for_size`、
カメラ行列 `K` と歪み `D` を使っている。

やること: 解像度、画角、内部パラメータを記録する。記事の「カメラ仕様」節に使う。

---

# E. 実行環境・システム

## E-1. メディアの排他制御（release / acquire）

| P | 状態 |
| --- | --- |
|  | 未着手 |

`release_media()` / `acquire_media()` / `media_released`。daemonからカメラ・音声
ハードウェアを解放して、自分のプログラムが直接触れるようにする仕組み。

やること: 解放中にdaemon側の機能（顔追跡など）がどうなるか確認する。
**顔追跡が共有カメラフィード依存だったことを踏まえると、影響が出るはず。**

## E-2. キネマティクス情報の取得

| P | 状態 |
| --- | --- |
|  | 未着手 |

`GET /api/kinematics/urdf`、`GET /api/kinematics/info`、`GET /api/kinematics/stl/{name}`。
URDFとSTLが取れるので、シミュレーションや可視化ができる。

やること: URDFを取得して構造（関節数、リンク、可動範囲）を整理する。

## E-3. Appの操作をAPIから行う

| P | 状態 |
| --- | --- |
|  | 未着手 |

`GET /api/apps/list-available`、`POST /api/apps/start-app/{name}`、
`POST /api/apps/stop-current-app`、`GET /api/apps/current-app-status`、
`PUT /api/apps/startup-app`（自動起動の設定）など。

やること: テスト前のApp停止をスクリプト化する。毎回手動で止める手間を省ける。

## E-4. 自作Appとしてパッケージ化する

| P | 状態 |
| --- | --- |
|  | 未着手 |

`reachy_mini.apps` に `app`、`manager`、`sources`、`jsonrpc_server` がある。
既存Appはhf_space（HuggingFace Space）として配布されている。

やること: 作ったスクリプトをAppとして動かす手順を調べる。UIから起動できる形が目標。

## E-5. daemonログの活用

| P | 状態 |
| --- | --- |
|  | 一部確認済み |

`sudo journalctl -u reachy-mini-daemon.service`（`sudo` はパスワード不要）。
`GET /logs` もある。顔追跡の切り分けで有効だった。

やること: `GET /logs` の内容とjournalctlの違いを確認し、切り分け手順としてまとめる。

## E-6. その他のシステムAPI

| P | 状態 |
| --- | --- |
|  | 未着手 |

`GET /api/daemon/status`、`POST /api/daemon/restart`、`GET /api/daemon/robot-name`、
`GET /api/daemon/hardware-id`、`GET /api/daemon/robot-app-lock-status`、
`GET /update/available`、`GET /settings`、`POST /health-check`、
`POST /cache/clear-hf`、`wifi/*` 系。

やること: 記事で触れる価値のあるものを選別する。`robot-app-lock-status` は
「Appとスクリプトの競合」の説明に使えそう。

---

# F. 解決済み（記録として残す）

## F-1. 顔追跡が動かない → 解決（2026-08-29）

原因: daemon側のtrackerは自分でカメラを開かず、GStreamerの `unixfdsrc` で共有カメラ
フィードへ接続する実装だった。`media_backend="no_media"` ではそのフィードが配信されず、
trackerはフレームを1枚も受け取れないため `detected` が永久に `False` になっていた。
SDKやハードウェアではなく、こちらのスクリプトのバグ。既定値は `"default"` なので、
**引数を書かなければ動いていた**。

修正: `ReachyMini(media_backend="default")`。

検証: 本体上で `no_media` 0/15（0%）→ `default` 12/15（80%）。Mac版も同じ1行修正で
24/30（80%）。どちらも頭の追従を目視確認。

## F-2. Mac生成WAVの音声再生が失敗する → 解決（2026-08-30）・原因は未確定

経過: Mac生成WAVを本体へ送って本体上で再生 → 鳴った（WAV形式は無罪）。続いてMac版を
そのまま再実行 → 鳴って正常終了。以前の「90秒待っても終わらない」は再現しなかった。

原因未確定: 変わった点は3つあり切り分けていない。(1) SDK/daemonを1.9.0→1.10.0へ更新
（最も疑わしい・推測）、(2) `enable_motors()` を追加、(3) Appを停止した状態でテスト。

## F-3. 接続成功でもロボットが動かない → 解決

原因はモーター無効。移動前に `enable_motors()` が必要。

## F-4. その他の完了項目

- Mac上のPythonから頭・アンテナの挨拶モーションを実行
- Wireless本体上のPythonから同じモーションを実行
- 胴体を左右20°回転するテストに成功
- WebRTC経由のカメラ静止画取得に成功（Mac 約5秒 / 本体 0.4秒）
- 本体内蔵音源の再生に成功
- 本体daemonとMac SDKを1.10.0へ更新、Python要件を3.11以上へ変更
- SSHによる本体再起動と、HTTPによる起動確認
- SSH鍵認証を登録し、エージェントから非対話で本体実行できるようにした

---

# テスト運用ルール

- 実行開始と終了を音または明確な表示で知らせる
- 長い待ちを含むテストにはカウントダウンを入れ、ユーザーが構える時間を作る
- モーション前にモーター状態と周囲の安全を確認する
- 寝た姿勢では、顔追跡や撮影前に頭を正面へ上げる
- 固まる可能性のある処理にはタイムアウトを付ける（Macに `timeout` コマンドは無い）
- **調査を始める前に、まず現状をそのまま再実行して再現性を確認する**
- **引数を足す前に既定値を確認する**（顔追跡の原因はこれだった）
- 失敗時はdaemonログとバージョンを保存する（後から原因を特定できなくなる）
- 成功、失敗、目視結果、ログ結果を分けて記録する
- Reachy Mini側の問題と、エージェント側の制約（承認・サンドボックス）を混同しない
- 人物が写った画像を記事へ掲載する前に、掲載可否とぼかしの必要性を確認する
- カメラ画像は `.gitignore` 済みだが、ファイル自体は都度削除する

# 記事化タスク

- Mac実行と本体実行の通信経路を図にする
- HTTP、WebSocket、WebRTC、unixソケットの役割分担を整理する
- 「接続成功なのに動かない」モーター無効問題を失敗事例として紹介する
- 「既定値のままなら動いていた」顔追跡バグを、原因究明の過程ごと記事にする
- `unixfdsrc` とカメラフィード共有の仕組みを、蛇口・土管・引換券のたとえで説明する
- uv初回実行と依存ダウンロード、Python要件変更を整理する
- 「再現しなくなったバグ」の扱いと記録の書き方
- エージェントから実機を操作する前提条件（SSH鍵認証）と切り分け手順

詳細な時系列と観察結果は `docs/sdk-test-notes.md` を参照する。
