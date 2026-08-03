# Reachy Mini Application 調査メモ

最終確認日: 2026-08-03  
確認対象: Reachy Mini SDK 1.9.0 / Reachy Mini Wireless

## 概要

Reachy Miniには、大きく分けてPython ApplicationとWeb/JavaScript Applicationが
ある。どちらも同じdaemonの制御機能を利用するが、コードの実行場所と配布方法が
異なる。

| 種類 | 主な実行場所 | 向いている用途 |
| --- | --- | --- |
| Python Application | Wireless版本体のCM4、またはLite版を接続したPC | 自律動作、制御ループ、Pythonライブラリ、オフライン/LAN利用 |
| Web/JavaScript Application | ブラウザまたはHugging Face Space | URL共有、画面中心の操作、リモート操作、WebRTCによるメディア利用 |

本体だけで動作させたい場合はPython Applicationを選ぶ。

## Wireless版Python Applicationの実行モデル

Reachy Mini ControlでPython Applicationをインストールすると、Hugging Face
Spaceからパッケージが取得され、Wireless版本体の共用仮想環境へインストールされる。

```text
Reachy Mini Control
  └─ Install / Start
       ↓ daemon API
Reachy Mini Wireless (CM4)
  ├─ /venvs/apps_venv/
  │    └─ ApplicationのPythonパッケージ
  ├─ Application subprocess
  └─ Reachy Mini daemon
       └─ モーター・カメラ・マイク・スピーカー
```

- Application用の共用環境は`/venvs/apps_venv/`。
- daemon用環境は別にあり、通常はApplicationから変更しない。
- daemonはApplicationをPython subprocessとして起動する。
- 実行中のApplicationは原則1つだけ。
- 停止時はdaemonが`SIGINT`を送り、終了後にロボットをデフォルト姿勢へ戻す。
- Applicationは接続済みの`ReachyMini`と`stop_event`を受け取る。

## Applicationの作成

Python Applicationのフォルダは手作業で組み立てず、公式CLIを使用する。

```bash
reachy-mini-app-assistant create \
  hello_reachy_mini \
  ../hello-reachy-mini-app
```

Hugging Face Spaceも同時に作る場合は`--publish`を付ける。

```bash
reachy-mini-app-assistant create \
  hello_reachy_mini \
  ../hello-reachy-mini-app \
  --publish
```

生成される構造の例:

```text
hello-reachy-mini-app/
├── README.md
├── pyproject.toml
├── index.html
└── hello_reachy_mini/
    ├── __init__.py
    ├── main.py
    └── static/       # 任意の設定画面
```

Applicationクラスは`ReachyMiniApp`を継承し、`run()`を実装する。

```python
import threading

from reachy_mini import ReachyMini, ReachyMiniApp


class HelloReachyMiniApp(ReachyMiniApp):
    def run(
        self,
        reachy_mini: ReachyMini,
        stop_event: threading.Event,
    ) -> None:
        while not stop_event.is_set():
            # reachy_miniを使って動作する
            break
```

通常の単体スクリプトと異なり、Application内で自分から`ReachyMini()`を生成する
必要はない。

## 検証

構造、メタデータ、entry pointを公式CLIで検証する。

```bash
reachy-mini-app-assistant check ../hello-reachy-mini-app
```

開発中はdaemonを起動した状態で直接実行できる。

```bash
cd ../hello-reachy-mini-app
python -m hello_reachy_mini.main
```

Wireless版本体で手動テストする場合は、アプリを転送して`apps_venv`へインストール
する。通常の配布ではReachy Mini Controlにインストールを任せる。

## Hugging Faceへの公開

Reachy MiniのPython ApplicationはHugging Face Spaceとして配布される。公開には
Write権限を持つHugging Faceトークンが必要。

```bash
hf auth login
reachy-mini-app-assistant publish ../hello-reachy-mini-app
```

Spaceの`README.md`には次のタグが必要。公式CLIが自動で追加する。

```yaml
---
tags:
  - reachy_mini_python_app
---
```

### 公開範囲

| 公開範囲 | コードを閲覧・cloneできる人 | 利用範囲 |
| --- | --- | --- |
| Public | 誰でも | 一般ユーザーが発見・インストール可能 |
| Private | 所有者と許可されたメンバー | 自分やチーム内でのテスト向け |
| Protected | 所有者と共同作業者 | コードを隠してアプリを共有する有料プラン向け |

最初はPrivate Spaceで実機インストールを確認し、公開準備が整ってからPublicへ
変更するのが安全。GitHubとHugging Faceの公開範囲は独立している。

## GitHub Actionsによるデプロイ

GitHubをソース管理の正本にし、`main`へのpushをHugging Face Spaceへ自動同期
できる。公式の`huggingface/hub-sync` Actionを使用する例:

```yaml
name: Deploy to Hugging Face

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: huggingface/hub-sync@v0.1.0
        with:
          github_repo_id: ${{ github.repository }}
          huggingface_repo_id: YOUR_HF_USERNAME/hello-reachy-mini
          hf_token: ${{ secrets.HF_TOKEN }}
          private: true
```

`HF_TOKEN`には対象SpaceだけへWrite可能なfine-grained tokenを設定する。長期トークンを
GitHubへ保存しない構成にしたい場合は、Hugging Face Trusted PublishersとGitHub
OIDCも利用できる。

## APIキーなどのユーザー設定

Python Applicationには設定用Web UIを同梱できる。Applicationクラスに
`custom_app_url`を設定し、`static/`にHTML/CSS/JavaScriptを置く。Wireless版では
通常、同じLANから次のURLを開く。

```text
http://reachy-mini.local:8042
```

設定画面からApplication内のFastAPIへ値をPOSTし、本体側で保存する。LLM APIキーを
扱う場合は次を守る。

- APIキーをGitHubやHugging Face Spaceへcommitしない。
- ブラウザからLLM APIを直接呼ばず、本体側のPythonから呼ぶ。
- APIキーをログやGETレスポンスへ出さない。
- 保存ファイルはApplication専用にし、所有者だけが読める権限にする。
- 設定取得APIはキー本体ではなく「設定済みか」だけを返す。
- キーの差し替えと削除を設定画面から行えるようにする。
- 設定画面はHTTPなので、信頼できるLAN内で使用する。

Hugging Face SpaceのSecretsは、ユーザーのWireless本体へインストールされたPython
Applicationには自動転送されない。オンロボットの秘密情報はApplication自身の
設定画面で受け取る設計が適している。

## このプロジェクトからの次の段階

現在の`hello.py`と`hello_on_robot.py`は仕組みを理解するための単体スクリプト。
Application化するときは、現リポジトリ内にフォルダを手作業で追加するのではなく、
公式CLIで別のApplicationプロジェクトを生成する。

推奨する最初のApplication:

1. 挨拶モーションを`ReachyMiniApp`へ移植する。
2. `stop_event`による安全な停止を実装する。
3. Private Spaceへ公開する。
4. Reachy Mini Controlからインストールして実機確認する。
5. GitHub Actionsによる同期を追加する。
6. 必要ならPublicへ変更する。

## 公式資料

- [Building & Publishing Apps](https://huggingface.co/docs/reachy_mini/v1.9.0/SDK/apps)
- [Reachy Mini Development Guide for AI Agents](https://github.com/pollen-robotics/reachy_mini/blob/main/AGENTS.md)
- [Development Workflow for Wireless Reachy Mini](https://huggingface.co/docs/reachy_mini/platforms/reachy_mini/development_workflow)
- [Hugging Face Repository Visibility](https://huggingface.co/docs/hub/en/repositories-settings)
- [Hugging Face GitHub Actions](https://huggingface.co/docs/hub/en/repositories-github-actions)
