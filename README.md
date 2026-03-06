# AI Orchestrator Loop — Claude-First

Claude Code CLI のHookシステムによって自律的に回るAI開発ループ。
人間がやることは `make loop-start` を叩くだけ。

## 前提条件

- **Claudeサブスクリプション**: Pro（$20/月）または Max（$100〜/月）が必要
  - Claude Codeを使うには Pro 以上が必要です
  - 自動化ループを多用するなら Max 5x ($100/月) 推奨
- **OS**: macOS / Linux / Windows（Git Bash または WSL）
- **Python**: 3.9以上

## クイックスタート

```bash
# 1. Claude Code CLI をインストール（ネイティブインストーラー推奨）
curl -fsSL https://claude.ai/install.sh | bash

# 2. バージョン確認
claude --version

# 3. このリポジトリをクローン
git clone https://github.com/motegilab/ai-orchestrator-loop-claude.git
cd ai-orchestrator-loop-claude

# 4. セットアップ（初回のみ）
make setup

# 5. ループ開始！
make loop-start
```

## コマンド

| コマンド | 説明 |
|----------|------|
| `make loop-start` | ループ開始 |
| `make loop-status` | 前回の状態を確認 |
| `make loop-stop` | 停止 |
| `make setup` | 初回セットアップ |

## フォルダ構成

```
.claude/
  hooks/          ← Hookスクリプト（自動実行）
  skills/         ← PJ固有Skills
  settings.json   ← Hook定義
SSOT.md           ← 設計の正本（読むこと）
CLAUDE.md         ← AIへの指示・記憶
policy/           ← ポリシー設定
tasks/            ← タスク進行
runtime/          ← 実行生成物（git管理外）
```

## 新PJへの展開

```bash
gh repo create my-new-project --template motegilab/ai-orchestrator-loop-claude
cd my-new-project
# CLAUDE.md と SSOT.md を PJ固有内容に書き換える
make setup
make loop-start
```

## ループの仕組み

```
make loop-start
  ↓
SessionStart Hook → 前回コンテキスト自動注入
  ↓
Claude が Observe → Patch → Verify → Report
  ↓
Stop Hook → レポート生成 + next_session.md 生成
  ↓
次回 make loop-start で自動継続
```
