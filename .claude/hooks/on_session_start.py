#!/usr/bin/env python3
"""
SessionStart Hook — 環境チェック + 前回コンテキストをClaudeに自動注入
stdout の内容が Claude の additionalContext になる
"""
import json, sys, os
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)
    lines = ["=== AI Orchestrator Loop — セッション開始 ===\n"]

    # 環境チェック
    missing = [f for f in ["SSOT.md","CLAUDE.md","policy/policy.json"] if not Path(f).exists()]
    if missing:
        lines.append(f"WARNING: 必須ファイルが見つかりません: {', '.join(missing)}\n")
    else:
        lines.append("✅ 環境チェック: OK\n")

    # 前回ループの結果
    latest_json = Path("runtime/runs/latest.json")
    if latest_json.exists():
        try:
            d = json.loads(latest_json.read_text(encoding="utf-8"))
            lines.append(f"前回ループ: {d.get('run_id','?')} / status={d.get('status','?')}\n")
            lines.append(f"要約: {d.get('summary','?')}\n")
        except Exception as e:
            lines.append(f"latest.json 読み込みエラー: {e}\n")
    else:
        lines.append("前回ループ: なし（初回起動）\n")

    # 引き継ぎコンテキスト
    next_session = Path("runtime/logs/next_session.md")
    if next_session.exists():
        lines.append("\n--- 前回セッションからの引き継ぎ ---\n")
        lines.append(next_session.read_text(encoding="utf-8"))
        lines.append("--- 引き継ぎここまで ---\n")
    else:
        lines.append("\n初回起動: SSOT.mdとCLAUDE.mdを読んでから tasks/milestones.json のタスクを開始してください。\n")

    print("".join(lines))

if __name__ == "__main__":
    main()
