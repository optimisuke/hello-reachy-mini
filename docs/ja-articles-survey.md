# Reachy Mini 日本語技術記事サーベイ

調査日: 2026-08-29
調査方法: Zenn API（`api/search`, `api/articles?topicname=reachymini`）、Qiita API、note 検索API、
DuckDuckGo HTML検索。`WebSearch` ツールは本環境で使用不可（CLAUDE.md参照）。

## サマリ

- 日本語の一次情報（実機を触った記事）は **おおむね20〜25本程度** しかなく、まだ非常に薄い。
- 発信の中心は **note**。Zennは3本、Qiitaは実質2本のみ。技術記事プラットフォームとしては
  ほぼ空白地帯。
- 時系列は3波ある。
  1. 2025-07 発表直後の「概要紹介」波（npaka ほか、ニュース解説が主）
  2. 2025-10〜2026-02 出荷・CES 2026 後の「入門・SDK・会話アプリ」波
  3. 2026-06〜08 個人開発者の実機到着による「自作アプリ・応用」波（いま進行中）
- ネタとしては **LLM音声対話** に極端に偏っている。制御・センサ・評価・運用の話がほぼない。

## 主要な書き手

| 書き手 | 媒体 | 立ち位置 | 特徴 |
| --- | --- | --- | --- |
| npaka | note / CGWORLD連載 | 国内で唯一の体系的な入門シリーズ | 概要、入門(1)〜(3)、conversation app、MCP、dashboard一覧、DGX Spark連携。いいね数も最多帯（12〜63） |
| robo_ai_tech（Aoki） | note | 実装ベースの連載型。法人向け相談も併記 | セットアップ、開発方法、監視システム①〜③ |
| akiiiiita（Akihiro Ueda） | Qiita | DGX Spark + ローカルLLMで会話・顔認識 | Gemma系＋Tsukasa_Speech、家族認識をVLMゼロショットで実装 |
| nszknao（Nishizaka Naoto） | Zenn | 自作アプリの実機デプロイ〜HF Space公開 | 本リポジトリの関心領域と最も近い |
| fmbro0203 | Zenn | 公式 conversation app の内部構造＋Tool追加 | Realtime API の Function Calling を写経可能なレベルで解説 |
| Beaver's Hive | Zenn | 車載相棒ロボの作品系（いいね30） | Gemini Live API + MCP + Style-Bert-VITS2 + 自作車載マウント |
| trtd56（toda） | note | エッセイ／考察（いいね23） | 「動くこと」が関係性を変える。子供・ペットの反応 |
| ascam / h3adeu / masa_cloud / shirakabado 等 | note | 開封・組み立て・所感・構成解説 | 一次情報は浅めだが読者は多い |
| togakyo | Qiita | Reachy **2** シミュレータ（three.js + Docker + LLM） | Mini ではないが隣接事例 |

そのほか、Seeed Studio Wiki 日本語版、ai-souken、reachymini.net/ja などの
翻訳・SEO系解説ページ、ITmedia のブログ記事（2025-07）が存在する。

## 記事カテゴリ分類と充足度

| カテゴリ | 代表記事 | 充足度 |
| --- | --- | --- |
| ニュース・概要解説 | npaka「Reachy Mini の概要」、各種まとめnote | 過剰。二次情報が多い |
| 開封・組み立て | ascam「ロボット、届きました／組み立てました」 | 足りている |
| 初期セットアップ | robo_ai_tech「セットアップ記録」、npaka入門(1) | 足りている |
| Python SDK 入門 | npaka入門(3)、robo_ai_tech「開発方法」 | 最小限。API網羅はされていない |
| 自作アプリ作成・実機デプロイ・HF公開 | nszknao | **1本だけ** |
| 公式 conversation app の内部構造・Tool追加 | fmbro0203 | 1本だけ |
| クラウドLLM音声対話 | chatgpt_lab（Realtime APIで受付自動化）、Beaver's Hive（Gemini Live） | やや充実 |
| ローカルLLM音声対話・低遅延化 | akiiiiita（DGX Spark）、h3adeu（VAD/STT/LLM/TTS分解）、npaka（local-conversation） | やや充実。国内で最も競争が激しい領域 |
| MCP連携 | npaka（Claude Desktop / ローカルLLM で MCP）、trtd56（Claude Code + hooks） | 芽が出た段階 |
| ビジョン応用 | robo_ai_tech（監視・自動追尾・録画解析）、akiiiiita（家族認識） | 事例2件。実測カメラ視野角75°などの一次情報あり |
| 業務・ユースケース検討 | ascam「会社はどう変わる？」、chatgpt_lab | 少ない |
| 人とロボットの関係性・考察 | trtd56 | 1本。だが反響は大きい |
| Reachy 2 / シミュレータ | togakyo | Mini からは離れる |

## まだ試されていない・記事化されていない領域

**制御・モーション**
- 頭部6自由度 Stewart プラットフォームの運動学（可動範囲、特異点、`create_head_pose` の
  実測限界、SDKの自動クランプが実際にどこで効くか）
- `set_target` と `goto_target` の使い分け、補間・軌道生成、周期制御ループの実測レイテンシ
- 胴体回転とアンテナを含めた「表情」設計の作法。既存記事はダンス/エモーションの一覧
  （npaka）で止まっており、自作モーションの作り方は空白
- IMU の活用事例が皆無（持ち上げ検知、転倒検知、揺れへの反応）

**アプリ基盤・運用**
- Wireless版本体（CM4）上でのアプリ実行モデル、`/venvs/apps_venv` 共有venvの制約、
  依存衝突の実際 → 本リポジトリの `docs/reachy-mini-applications.md` の内容は
  日本語ではほぼ未公開の情報
- daemon の REST API 仕様、Web/JavaScript Application（WebRTC）側の作り方
- アプリのライフサイクル、`stop_event`／SIGINT でのグレースフル終了の設計パターン
- CM4 の熱・CPU 負荷・バッテリー持ち、常時稼働時の挙動
- 複数アプリ切り替え、自動起動、アップデート耐性のある運用構成

**AI 応用の未開拓側**
- 音声入力なしの応用（カメラのみ、IMUのみ、時間駆動）
- 発話タイミング・割り込み・ターンテイキングの実装比較（記事はどれも構成紹介止まり）
- 低遅延の**定量計測**（VAD→発話開始までの実測値の比較表がどこにもない）
- ローカル vs クラウドのコスト・遅延・精度の比較検証
- LeRobot／模倣学習系との接続（Reachy Mini は腕がないため事例なし＝逆に狙い目）
- 音声認識の日本語精度、雑音下・遠距離での実測

**その他**
- Lite版とWireless版の実機比較記事が見当たらない
- 教育利用（授業・ワークショップ）の実践記録
- 失敗談・トラブルシューティングの体系的まとめ（断片的にしか存在しない）
- Microduck（2026-08発表の399ドルアヒル型）との比較。ニュース記事は既に多数出たが、
  実機比較はまだ誰もできていない

## 記事化の狙い目（本プロジェクト向け）

1. **本体上でアプリを動かす話**。SDKでMacから叩く記事は増えてきたが、CM4上での実行、
   共有venv、daemon経由の起動という「Application モデル」の解説は日本語でほぼ空白。
   nszknao の記事が唯一近いので、差分は運用・内部構造・つまづきの深さで出す。
2. **モーター無効状態でも命令が成功してしまう**類の、daemonの挙動に起因するハマり。
   一次情報として価値が高い（`docs/sdk-test-notes.md` の素材）。
3. **姿勢・可動範囲の実測**。カメラ視野角の公称120°→実測75°（robo_ai_tech）のように、
   公称値と実測値の乖離ネタは読まれる。
4. **LLM会話に寄せない切り口**。この領域だけ既に混雑しているため、制御・センサ・
   運用に振ったほうが空白を取れる。

## 参照リスト

### Zenn
- 2026-06-11 nszknao「Reachy Mini Wireless で自作 Hello World アプリを作り、実機デプロイから HF 公開までやってみる」 https://zenn.dev/nszknao/articles/reachy-mini-hello-world-app
- 2026-02-15 beavers_hive「【フィジカルAI x Gemini x MCP】相棒ロボ「Reachy」と楽しくドライブ！」 https://zenn.dev/beavers_hive/articles/8d4d34d54bec1c
- 2026-01-22 fmbro0203「Reachy mini を賢くする：Function Calling（Tool）の追加方法を内部構造まで踏み込んで解説」 https://zenn.dev/fmbro0203/articles/006e82babd957b

### Qiita
- 2026-06-05 akiiiiita「Reachy Miniに家族になってもらった」 https://qiita.com/akiiiiita/items/3cd3785b6c93a7288e9f
- 2026-06-04 akiiiiita「Reachy Miniが来たのでDGX sparkで会話させてみた」 https://qiita.com/akiiiiita/items/4443e15799dbf560bca9
- 2026-08-11 togakyo「Reachy 2 のシミュレータで、子供が話しかけられるロボットを作った」 https://qiita.com/togakyo/items/b3523951f405895fd4cc

### note（一次情報・解説）
- 2025-07-10 npaka「Reachy Mini の概要」 https://note.com/npaka/n/nc6a5d23ac25b
- 2025-10-23 npaka「Reachy Mini 入門 (1) - 事始め」 https://note.com/npaka/n/n24f8e6e4df7c
- 2025-10-23 npaka「入門 (2) - Reachy Mini conversation app」 https://note.com/npaka/n/nda57df378355
- 2025-10-27 npaka「入門 (3) - Python SDK」 https://note.com/npaka/n/n0caf10e20c96
- 2026-01-06 npaka「NVIDIA は DGX Spark と Reachy Mini でエージェントに命を吹き込む」 https://note.com/npaka/n/n3fcd04d3ae6d
- 2026-02-01 npaka「Reachy Mini Robot with NeMo Agent Toolkit Tutorial の概要」 https://note.com/npaka/n/n281f72eb1e40
- 2026-02-05 npaka「Reachy Mini dashboard のダンス・エモーション・アプリの一覧」 https://note.com/npaka/n/n1f0add28df7b
- 2026-02-09 npaka「Claude Desktop で Reachy Mini MCP を試す」 https://note.com/npaka/n/n32db182cd26f
- 2026-02-09 npaka「reachy-mini-local-conversation の概要」 https://note.com/npaka/n/ne79bde2cca76
- 2026-02-10 npaka「ローカルLLM で Reachy Mini MCP を試す」 https://note.com/npaka/n/na4c205ed442f
- 2026-03-27 / 04-23 npaka「CGWORLD にて NVIDIA DGX Spark × Reachy Mini の連載」 https://note.com/npaka/n/nee8919d9c574 , https://note.com/npaka/n/n7110847ae451
- 2026-01-15 trtd56「Reachy Miniを触って気づいた、AIが"こっち側"にいることの意味」 https://note.com/trtd56/n/nce8aef61d4d0
- 2026-03-01 chatgpt_lab「Reachy Mini × Realtime APIでイベント受付を自動化してみた」 https://note.com/chatgpt_lab/n/n55e179ff1534
- 2026-07-28 h3adeu「Reachy Mini とローカル AI で実現する「遅延のない会話」の構成要素」 https://note.com/h3adeu/n/n54d87387a7f2
- 2026-08-02 robo_ai_tech「Reachy Mini セットアップ記録」 https://note.com/robo_ai_tech/n/nb9b19f192b6d
- 2026-08-03 robo_ai_tech「Reachy Mini の開発方法」 https://note.com/robo_ai_tech/n/n7a135f325191
- 2026-08-10/14/19 robo_ai_tech「Reachy Miniで監視システムを構築してみた ①②③」 https://note.com/robo_ai_tech/n/ncead71e7c247 , https://note.com/robo_ai_tech/n/n56d7965682f5 , https://note.com/robo_ai_tech/n/n918667119812
- 2026-07-14 / 07-29 ascam「ロボット、届きました。」「ロボット、組み立てました。【Reachy mini】」 https://note.com/ascam/n/ned1203fcabae , https://note.com/ascam/n/n72485c400c48
- 2026-02-25 ascam「小さなロボットで、会社はどう変わる？Reachy Mini活用案」 https://note.com/ascam/n/nf6f4e7e17989
- 2026-07-05 masa_cloud「ロボット×オンデバイスAIの可能性：GemmaとReachy Miniが示す未来」 https://note.com/masa_cloud/n/n38e07846beb9

### 公式・翻訳・SEO系
- Seeed Studio Wiki 日本語版 https://wiki.seeedstudio.com/ja/reachymini_intro/
- reachymini.net 日本語ページ https://reachymini.net/ja/
- AI総合研究所「【Pollen Robotics】Reachy Miniとは？」 https://www.ai-souken.com/article/what-is-reachy-mini
- ITmedia ブログ（2025-07）「Hugging Faceの"Reachy Mini"は日本のロボティクス関係者にとっても学びが深い…」 https://blogs.itmedia.co.jp/serial/2025/07/huggingfacereachyminiai.html

## 注意
- いいね数・本数は 2026-08-29 時点。
- note検索は全文検索のため取りこぼしがある可能性がある（推測）。特に個人ブログ、
  はてなブログ、Speaker Deck、YouTube は網羅できていない（要検証）。

---

# 英語圏との比較（追加調査 2026-08-29）

調査方法: Hugging Face API（spaces/models/datasets）、GitHub Search API、
Hacker News Algolia API、HF公式ブログ。Reddit は 403、DuckDuckGo はレート制限で
途中から取得不可（要検証）。

## 結論：英語圏も「記事」は少ない。多いのは「コード」

意外なことに、英語圏にも解説記事・チュートリアル記事の蓄積はほとんどない。
- Hacker News の "reachy mini" 全ヒットは **21件**、最高スコアは発表記事の30ポイント。
- HF公式ブログの Reachy Mini 記事は **4本のみ**（発表 2025-07-09、DGX Spark 2026-01-05、
  fully local 2026-05-27、Adding MCP Tools 2026-06-03）。
- 個人ブログ・Medium・dev.to の技術記事もほぼ見つからない。

**代わりに英語圏の情報は「動くコード」に集約されている。** 日本語圏との差は
「記事の本数」ではなく「公開実装の本数」にある。

| 指標 | 数 |
| --- | --- |
| HF Spaces（`reachy_mini_python_app` タグ＝App Store のアプリ） | **425個** |
| GitHub で "reachy mini" を含むリポジトリ | **485個** |
| SDK `pollen-robotics/reachy_mini` のスター | 1,440 |
| `reachy_mini_conversation_app` のスター | 298 |

日本語記事は20〜25本、日本語圏の公開実装はほぼ見当たらない。この非対称が本質。

## App Store 上位アプリ（いいね順）

| likes | Space | 内容 |
| --- | --- | --- |
| 361 | itsMarco-G/reachy_phone_home | 個人開発アプリが公式を上回るトップ |
| 207 | d10g/f1commentator | F1実況ロボット |
| 178 | ravediamond/baby-reachy-mini-companion | 赤ちゃん向けコンパニオン |
| 171 | pollen-robotics/reachy_mini_conversation_app | 公式会話アプリ |
| 110 | panny247/hello_world | Hello World がこの順位 |
| 36 | yozkut/judgy_reachy_no_phone | スマホを見ていると怒る |
| 36 | tomrikert/clawbody | AIエージェントに身体を与える |
| 31 | 8bitkick/reachy_mini_3d_web_viz | 3D Web可視化 |
| 29 | mattdotvaughn/reachy_mini_language_tutor | 語学チューター |
| 25 | djhui5710/reachy_mini_home_assistant | Home Assistant連携 |
| 19 | **trtd56/rock_paper_scissors** | 日本人（note の trtd56）のアプリ |

公式は marionette / hand_tracker_v2 / red_light_green_light / radio / testbench /
dances_library / homeassistant などを出しており、上位は個人開発が占める。

## GitHub で目立つ第三者実装

- `suharvest/reachy-claw`（35★）— **sub-200ms** の音声アシスタント。sherpa-onnx + OpenClaw。
  遅延をエンジニアリング目標として明示している唯一級の事例
- `algoryn-nl/reachy-mini-esp32-eyes`（34★）— **ハードウェアMOD**。ESP32制御の目を追加
- MCPサーバが複数並立（`agentculture/reachy-mini-mcp` 31★、`jackccrawford/reachy-mini-mcp` 28★、
  `PixelML/reachy-mini-mcp` 21★）
- `NVIDIA-AI-IOT/reachy-mini-jetson-assistant`（30★）— NVIDIA公式の Jetson 版パイプライン
- `V4C38/spectacles-reachy-mini`（26★）— **Snap Spectacles（AR）からの操作**
- `ArturSkowronski/clawd-reachy-mini`（30★）— WebSocket 経由で OpenClaw 接続
- `gamepop/reachy-mini-gemini`（13★）— Gemini Live API 版会話アプリ
- `alexey1312/reachy-mini-swift` — **ネイティブ Swift クライアント**（macOS/iOS）
- `lizhun781021/reachy-mini-s2s-setup` — 中国語音声対話（Paraformer ASR + Qwen3-TTS）。
  中国語圏でも同種の動きがある
- `felixfabricius/robot-chess-commentator`、`noelotpyrc/reachy-mini-receptionist` など
  用途特化が多数

## 日本語圏に無く英語圏にあるカテゴリ

1. **ハードウェア改造**（ESP32の目、クロー、3Dプリント拡張）
2. **遅延の数値目標を掲げた実装**（sub-200ms）
3. **MCPサーバを「プロダクト」として公開する**動き（日本語はnpakaの試用記事のみ）
4. **AR/モバイル/別言語クライアント**（Spectacles、Swift、iOS）
5. **エンタメ・用途特化アプリの量産**（F1実況、チェス解説、語学、メトロノーム、受付）
6. **公式のテストベンチ・ダンスライブラリ等の周辺ツール**の活用

## ここからの示唆

- 「英語圏には情報が豊富」という直感は半分だけ正しい。**解説記事は英語圏も薄く、
  差がついているのは公開実装（HF Space / GitHub）の数**。
- したがって日本語で書く価値は高い。特に、英語圏でもコードしか無く文章での解説が
  無い領域（App モデル、daemon の挙動、可動域や制御ループの実測、遅延の計測）は
  世界的にも文章化されていない。
- 逆に、日本語圏で誰も **HF App Store にアプリを公開していない**（trtd56 を除く）。
  記事とセットでアプリを1つ公開するだけで差別化になる。

---

## 追記：出荷台数の一次記述（2026-08-29）

公式の販売台数は非公開だが、`huggingface/speech-to-speech` のREADMEに次の記述がある。

```text
This pipeline runs in production as the conversation backend for
thousands of Reachy Mini robots.
```

**「数千台のReachy Mini」**。会話アプリを使っている台数なので総出荷台数の下限にあたる。

代理指標からの推定と整合する。

| 指標 | 値 |
| --- | --- |
| HF App Store のアプリ数 | 425 |
| アプリを公開した異なるアカウント数 | 306 |
| SDKリポジトリのissue/PR作者数 | 105人（700件） |
| SDKスター / フォーク | 1,440 / 290 |
| アプリのlikes | 合計1,754、中央値0、67%が0いいね |

アプリ公開者306人がオーナーの3〜10%と仮定すると3,000〜10,000台。上のREADMEの
「thousands」はこのレンジの下側を裏付ける。売上換算で$2M強、小規模チームとしては自然な規模。

新規参加者（初アプリを公開した月）は月25〜40人で横ばい。累積は線形に増えるだけで
加速していない。また245人（80%）が1本公開して以降活動していない。
