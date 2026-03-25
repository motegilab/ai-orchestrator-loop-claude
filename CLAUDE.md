# CLAUDE.md — AI Orchestrator Loop

## このリポジトリについて
Claude-First AI Orchestrator Loop のテンプレートリポジトリ。
新PJではこのファイルとSSO.mdをPJ固有内容に書き換えて使う。

## 必須：セッション開始時に必ず読むファイル
1. SSOT.md（設計の正本）
2. runtime/runs/latest.json（前回ループの結果）
3. runtime/reports/REPORT_LATEST.md（前回レポート）
4. tasks/milestones.json（現在のタスク状態）

## ワークフロー（Observe → Patch → Verify → Report）
1. **Observe**: 問題・タスクを調査する。Evidence firstで進める
2. **Patch**: 最小差分で修正する。1原因1修正を厳守する
3. **Verify**: 変更後は必ず検証する。exit codeとstdoutを記録する
4. **Report**: 結果をreport Skillで記録する。Stop前に必ず実行する

## 絶対ルール（Hookで強制される）
- SSOT.mdを人間の合意なしに編集しない（下記ワークフロー参照）
- policy/ssot_integrity.jsonを直接編集しない
- runtime/以外にランタイム生成物を置かない
- 1ループで複数原因を修正しない

## SSOT.md 更新ワークフロー
設計決定が増えたとき・未定義事項が確定したときに実施する。

1. 会話内でだいすけと合意を取る
2. `make ssot-edit-start`（バックアップ取得 + ゲート解除）
3. SSOT.md を編集（最小差分・該当セクションに追記）
4. `make ssot-edit-end`（ゲート再有効化 + ハッシュ更新）

## コマンド
```
make loop-start      # ループ開始
make loop-status     # 状態確認
make loop-stop       # 停止
make ssot-edit-start # SSOT編集モード開始（バックアップ自動取得）
make ssot-edit-end   # SSOT編集モード終了（ハッシュ更新）
```

## ファイル構成
- SSOT.md: 設計の正本（読むこと）
- .claude/hooks/: Hook実装（自動実行）
- .claude/skills/: PJ固有Skills
- policy/: ポリシー設定
- tasks/milestones.json: タスク進行
- runtime/: 実行生成物（git管理外）

## レポートフォーマット
毎回のStop時にon_stop.pyが以下を生成する:
- runtime/runs/YYYY-MM-DD_runNNN.json
- runtime/reports/REPORT_LATEST.md
- runtime/logs/next_session.md（次回SeessionStartで自動注入）

## 注意
- CLAUDE.mdは200行以内に保つ（超えるとClaudeの注意力が分散する）
- PJ固有の詳細はdocs/以下のファイルに書いてここからリンクする
