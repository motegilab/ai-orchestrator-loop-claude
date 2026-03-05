#!/usr/bin/env python3
"""Stop Hook: on_stop.py - レポートとnext_session.mdを生成"""
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

RUNTIME = Path("runtime")
RUNS_DIR = RUNTIME / "runs"
REPORTS_DIR = RUNTIME / "reports"
LOGS_DIR = RUNTIME / "logs"
LATEST_RUN = RUNS_DIR / "latest.json"
LATEST_REPORT = REPORTS_DIR / "REPORT_LATEST.md"
NEXT_SESSION = LOGS_DIR / "next_session.md"

def get_run_id():
    today = datetime.now().strftime("%Y-%m-%d")
    existing = [f for f in RUNS_DIR.glob(f"{today}_run*.json") if f.name != "latest.json"] if RUNS_DIR.exists() else []
    return f"{today}_run{len(existing)+1:03d}"

def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}

    if event.get("stop_hook_active"):
        sys.exit(0)

    for d in [RUNS_DIR, REPORTS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    run_id = get_run_id()
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "run_id": run_id, "session_id": event.get("session_id","unknown"),
        "started_at": event.get("started_at", now), "stopped_at": now,
        "source": "claude-code-cli", "intent": "task_completed",
        "summary": "セッション完了（詳細はREPORT_LATEST.mdを参照）",
        "status": "success", "top_errors": [],
        "evidence_paths": [str(LATEST_REPORT), str(NEXT_SESSION)],
        "report_status": "success", "report_path": str(LATEST_REPORT),
        "next_session_path": str(NEXT_SESSION)
    }

    try:
        run_path = RUNS_DIR / f"{run_id}.json"
        run_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        LATEST_RUN.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[on_stop] WARNING: run record失敗: {e}", file=sys.stderr)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        LATEST_REPORT.write_text(f"""# REPORT_LATEST.md\nrun_id: {run_id}\ngenerated_at: {ts}\nstatus: success\n\n## hypothesis_one_cause\n（Claudeが作業中に更新する）\n\n## one_fix\n（実施した修正）\n\n## files_changed\n- （変更ファイル）\n\n## verify_commands\n```\n```\n\n## exit_codes\n- 0\n\n## evidence_paths\n- runtime/runs/{run_id}.json\n\n## decision\nsuccess\n""", encoding="utf-8")
    except Exception as e:
        print(f"[on_stop] ERROR: report失敗: {e}", file=sys.stderr)
        try:
            (REPORTS_DIR / "REPORT_FAILED.md").write_text(f"# REPORT FAILED\nrun_id: {run_id}\nerror: {e}\nnext_action: make loop-start", encoding="utf-8")
        except Exception:
            pass

    try:
        NEXT_SESSION.write_text(f"""# Next Session Context\ngenerated_at: {ts}\nprevious_run_id: {run_id}\n\n## DONE\n前回セッション（{run_id}）が完了しました。\n\n## NEXT\n1. SSOT.md §1（絶対ルール）を確認する\n2. tasks/milestones.json を読んで次のタスクを確認する\n3. runtime/reports/REPORT_LATEST.md を読んで前回の結果を確認する\n\n## FAIL\n（失敗内容があればここに記録）\n\n## FIX\n（失敗時: 最小差分・1原因1修正で対処）\n\n## VERIFY\n```bash\nmake loop-status\n```\n\n## CONTEXT\n- 前回のrun_id: {run_id}\n- ステータス: success\n""", encoding="utf-8")
    except Exception as e:
        print(f"[on_stop] WARNING: next_session.md失敗: {e}", file=sys.stderr)

    print(f"[on_stop] ✅ {run_id} 完了", file=sys.stderr)

if __name__ == "__main__":
    main()
