# CLAUDE.md

プロジェクト共通の指示は @AGENTS.md に記載している。作業前に必ずそちらも参照すること。

## この環境で使えないツール

- `WebSearch` ツールは使用不可（現在のモデルでは未対応。呼び出すとAPIエラーになる）。
  Web調査が必要な場合は次の代替手段を使う。
  - `WebFetch` で対象URLを直接取得する
  - Bashの `curl` で検索・APIを叩く
    - DuckDuckGo HTML: `curl -s "https://html.duckduckgo.com/html/?q=..." -H 'User-Agent: Mozilla/5.0'`
    - Zenn: `https://zenn.dev/api/search?q=...&source=articles`、`https://zenn.dev/api/articles?topicname=...`
    - Qiita: `https://qiita.com/api/v2/items?query=...`
    - note: `https://note.com/api/v3/searches?context=note&q=...`
