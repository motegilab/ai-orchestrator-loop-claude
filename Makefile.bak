# AI Orchestrator Loop — Makefile
# 入口はこの3コマンドのみ

RUNTIME_DIR := runtime
NEXT_SESSION := $(RUNTIME_DIR)/logs/next_session.md

.PHONY: loop-start loop-stop loop-status setup

## ループ開始 — 前回のnext_session.mdを初期プロンプトとして渡す
loop-start:
	@mkdir -p $(RUNTIME_DIR)/runs $(RUNTIME_DIR)/reports $(RUNTIME_DIR)/logs $(RUNTIME_DIR)/artifacts
	@if [ -f "$(NEXT_SESSION)" ]; then \
		echo "[loop-start] 前回のコンテキストを読み込み中..."; \
		claude --add-dir ~/.claude/skills \
		       --allowedTools "Read,Write,Edit,MultiEdit,Bash,Task" \
		       -p "$$(cat $(NEXT_SESSION))"; \
	else \
		echo "[loop-start] 初回起動 — CLAUDE.mdとSSO.mdを読んでタスクを開始します"; \
		claude --add-dir ~/.claude/skills \
		       --allowedTools "Read,Write,Edit,MultiEdit,Bash,Task" \
		       -p "SSOT.mdとCLAUDE.mdを読んで、tasks/milestones.jsonの次のタスクを実行してください。"; \
	fi

## 状態確認 — 最新のrunとレポートを表示
loop-status:
	@echo "=== latest.json ==="
	@if [ -f "$(RUNTIME_DIR)/runs/latest.json" ]; then cat $(RUNTIME_DIR)/runs/latest.json; else echo "(まだありません)"; fi
	@echo ""
	@echo "=== REPORT_LATEST.md ==="
	@if [ -f "$(RUNTIME_DIR)/reports/REPORT_LATEST.md" ]; then cat $(RUNTIME_DIR)/reports/REPORT_LATEST.md; else echo "(まだありません)"; fi

## 停止（セッションはEscで止めるのが基本だが、ファイルのクリーンアップはここで）
loop-stop:
	@echo "[loop-stop] セッションを停止しました。"
	@echo "次回は make loop-start で再開できます。"

## 初回セットアップ（Python環境確認 + gitignore設定）
setup:
	@echo "[setup] 環境チェック..."
	@python --version || (echo "ERROR: Python3が必要です" && exit 1)
	@claude --version || (echo "ERROR: Claude Code CLIが必要です。https://claude.ai/download" && exit 1)
	@echo "runtime/" >> .gitignore
	@echo ".gitignore に runtime/ を追加しました"
	@python .claude/hooks/ssot_gate.py --update-hash
	@echo "[setup] 完了！make loop-start でループを開始できます"
