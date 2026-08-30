# Reachy Mini daemon REST API チートシート

`docs/daemon-openapi.yaml` から、よく使うものを抜き出したもの。

- ベースURL: `http://reachy-mini.local:8000`（本体上からは `http://localhost:8000`）
- ブラウザで閲覧
  - `/docs`（Swagger UI）: **試せる**。「Try it out」で実際にリクエストを送れる
  - `/redoc`（ReDoc）: **読める**。3カラムで俯瞰しやすい。全体を探すならこちら
- 生の定義: `/openapi.json`
- このリポジトリの控え
  - `docs/daemon-openapi.json`: 取得したまま無加工
  - `docs/daemon-openapi.yaml`: YAML化したもの（`info` に取得元と日付を補記。それ以外は同一）
- **公式ドキュメントサイトには記載がない**。daemon が自己文書化して配信している
- 取得日: 2026-08-30 / 本体daemon 1.10.0 / 全100オペレーション
- **角度の単位はラジアン**

## モーション

```bash
# 頭・アンテナ・胴体を補間して移動。4x4行列は不要で roll/pitch/yaw が使える
curl -X POST http://reachy-mini.local:8000/api/move/goto \
  -H 'Content-Type: application/json' \
  -d '{"head_pose":{"x":0,"y":0,"z":0,"roll":0,"pitch":-0.3,"yaw":0},
       "antennas":[0.7,-0.7],"body_yaw":0.0,"duration":1.0,"interpolation":"minjerk"}'
# → {"uuid":"..."} を返す非ブロッキング方式

# 目標値の直接指定（連続制御用。補間しない）
curl -X POST http://reachy-mini.local:8000/api/move/set_target \
  -H 'Content-Type: application/json' \
  -d '{"target_head_pose":{"pitch":-0.2},"target_antennas":[0.3,-0.3],"target_body_yaw":0.0}'

# ダンス・感情モーションの再生（ボディ不要。データセット名の / は %2F にする）
curl -X POST "http://reachy-mini.local:8000/api/move/play/recorded-move-dataset/pollen-robotics%2Freachy-mini-dances-library/simple_nod"
curl -X POST "http://reachy-mini.local:8000/api/move/play/recorded-move-dataset/pollen-robotics%2Freachy-mini-emotions-library/laughing1"

# モーション名の一覧
curl "http://reachy-mini.local:8000/api/move/recorded-move-datasets/list/pollen-robotics%2Freachy-mini-dances-library"

# 起床・就寝
curl -X POST http://reachy-mini.local:8000/api/move/play/wake_up
curl -X POST http://reachy-mini.local:8000/api/move/play/goto_sleep

# 再生中の一覧と停止（stop は uuid 必須）
curl http://reachy-mini.local:8000/api/move/running
curl -X POST http://reachy-mini.local:8000/api/move/stop \
  -H 'Content-Type: application/json' -d '{"uuid":"..."}'
```

`interpolation` は `linear` / `minjerk`（既定）/ `ease_in_out` / `cartoon`。

`head_pose` は2形式のどちらでもよい。

- `XYZRPYPose`: `{x, y, z, roll, pitch, yaw}`（すべて既定0.0。**指定した項目だけ書けばよい**）
- `Matrix4x4Pose`: `{"m": [...16要素...]}`

## 状態

```bash
curl http://reachy-mini.local:8000/api/state/full   # 姿勢・アンテナ・胴体・制御モード・DoAを一括
curl http://reachy-mini.local:8000/api/state/present_head_pose
curl http://reachy-mini.local:8000/api/state/present_antenna_joint_positions
curl http://reachy-mini.local:8000/api/state/present_body_yaw
curl http://reachy-mini.local:8000/api/state/doa    # 音源方向
```

`/api/state/full` の応答例。

```json
{"control_mode":"enabled",
 "head_pose":{"x":-0.001,"y":0.0008,"z":-0.001,"roll":0.064,"pitch":0.054,"yaw":0.022},
 "head_joints":null,"body_yaw":0.0,
 "antennas_position":[0.006,-0.008],
 "timestamp":"2026-08-30T00:24:49.568179Z","passive_joints":null,"doa":null}
```

## モーター

```bash
curl http://reachy-mini.local:8000/api/motors/status
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/disabled
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/gravity_compensation
```

`gravity_compensation` は頭を手で動かせるモード。

## メディア（音・カメラ・顔追跡）

```bash
# 音
curl http://reachy-mini.local:8000/api/media/sounds                  # 音源一覧
curl -X POST http://reachy-mini.local:8000/api/media/play_sound \
  -H 'Content-Type: application/json' -d '{"file":"wake_up.wav"}'
curl -X POST http://reachy-mini.local:8000/api/media/stop_sound
curl -X POST http://reachy-mini.local:8000/api/media/sounds/upload   # 音源のアップロード
curl -X DELETE http://reachy-mini.local:8000/api/media/sounds/xxx.wav

# 顔追跡
curl -X POST http://reachy-mini.local:8000/api/media/tracking/enable \
  -H 'Content-Type: application/json' -d '{"weight":1.0}'
curl -X POST http://reachy-mini.local:8000/api/media/tracking/disable
curl http://reachy-mini.local:8000/api/media/tracking/face           # 検出状態と座標

# 音声リアクティブな頭の揺れ
curl -X POST http://reachy-mini.local:8000/api/media/wobbling/enable
curl -X POST http://reachy-mini.local:8000/api/media/wobbling/disable

# ハードウェアの占有・解放
curl http://reachy-mini.local:8000/api/media/status
curl -X POST http://reachy-mini.local:8000/api/media/release
curl -X POST http://reachy-mini.local:8000/api/media/acquire
```

## 音量

```bash
curl http://reachy-mini.local:8000/api/volume/current
curl -X POST http://reachy-mini.local:8000/api/volume/set \
  -H 'Content-Type: application/json' -d '{"volume":60}'          # 0-100
curl http://reachy-mini.local:8000/api/volume/microphone/current
curl -X POST http://reachy-mini.local:8000/api/volume/microphone/set \
  -H 'Content-Type: application/json' -d '{"volume":70}'
curl -X POST http://reachy-mini.local:8000/api/volume/test-sound
```

## App 管理（テスト前の停止に便利）

```bash
curl http://reachy-mini.local:8000/api/apps/current-app-status      # 実行中のApp（無ければ null）
curl -X POST http://reachy-mini.local:8000/api/apps/stop-current-app
curl -X POST http://reachy-mini.local:8000/api/apps/start-app/{app_name}
curl http://reachy-mini.local:8000/api/apps/list-available
curl http://reachy-mini.local:8000/api/apps/startup-app             # 自動起動の設定
curl -X PUT  http://reachy-mini.local:8000/api/apps/startup-app
curl http://reachy-mini.local:8000/api/daemon/robot-app-lock-status # Appとスクリプトの排他状態
```

## その他

```bash
curl http://reachy-mini.local:8000/api/daemon/status
curl http://reachy-mini.local:8000/api/daemon/robot-name
curl http://reachy-mini.local:8000/api/camera/specs
curl http://reachy-mini.local:8000/api/kinematics/urdf              # URDF（可視化・シミュ用）
curl http://reachy-mini.local:8000/api/kinematics/info
curl http://reachy-mini.local:8000/logs
curl http://reachy-mini.local:8000/settings
curl http://reachy-mini.local:8000/update/available
```

## カテゴリ別の件数（全100オペレーション）

| カテゴリ | 件数 | 主な用途 |
| --- | --- | --- |
| hf-auth | 15 | HuggingFace 認証 |
| apps | 14 | App のインストール・起動・停止 |
| media | 14 | 音、顔追跡、wobbling、ハード占有 |
| wifi | 10 | ネットワーク設定 |
| move | 8 | モーション |
| daemon | 7 | daemon の状態・再起動・名前 |
| update | 6 | ファームウェア更新 |
| state | 5 | 現在の状態 |
| volume | 5 | 音量 |
| kinematics | 3 | URDF・STL |
| audio | 2 | XVF3800 音声ボードの設定 |
| motors | 2 | モーターモード |
| cache | 2 | キャッシュ削除 |
| camera, health-check, logs, settings, / | 各1 | |

## マイコン（ESP32）から使うときの注意

- **単位はラジアン。** 度で扱うなら `deg * PI / 180`
- データセット名が長いので定数にする
- モーション再生は uuid を返す非ブロッキング方式。完了は `/api/move/running` で確認
- `head_pose` は指定した項目だけ書けばよい（他は既定0.0）
- 認証は無い。**同じネットワークにいれば誰でも操作できる**
