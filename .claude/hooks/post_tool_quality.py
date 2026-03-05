#!/usr/bin/env python3
"""PostToolUse Hook: post_tool_quality.py - 品質チェックと監査ログ記録"""
import json, sys, py_compile
from datetime import datetime, timezone
from pathlib import Path

RUNTIME = Path("runtime")
AUDIT_LOG = RUNTIME / "artifacts" / "audit_log.jsonl"

def append_audit(event, result):
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(),
                 "tool_name": event.get("tool_name"),
                 "file_path": event.get("tool_input", {}).get("file_path", ""),
                 "result": result}
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[post_tool_quality] audit失敗: {e}", file=sys.stderr)

def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", tool_input.get("path", ""))
    result = {"ok": True, "checks": []}

    if file_path:
        p = Path(file_path)
        if p.suffix == ".py" and p.exists():
            try:
                py_compile.compile(file_path, doraise=True)
                result["checks"].append({"check": "python_syntax", "ok": True})
            except py_compile.PyCompileError as e:
                result["ok"] = False
                result["checks"].append({"check": "python_syntax", "ok": False, "msg": str(e)})
                print(f"[post_tool_quality] ⚠️ 構文エラー: {file_path}: {e}", file=sys.stderr)

    append_audit(event, result)
    sys.exit(0)

if __name__ == "__main__":
    main()
