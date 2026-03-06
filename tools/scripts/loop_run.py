#!/usr/bin/env python
"""
loop_run.py — 自動連続ループ実行スクリプト

Usage:
  python tools/scripts/loop_run.py           # pending タスクがなくなるまで自動実行
  python tools/scripts/loop_run.py 3         # 最大3ループ実行
  python tools/scripts/loop_run.py --dry-run # 実行せず次タスクだけ表示

ループは以下の条件で停止:
  - pending タスクがなくなった
  - 指定した max_loops に達した
  - on_stop.py が report_source=incomplete を連続で返した（無限ループ防止）
  - エラー終了（claude の returncode != 0）
"""
import json
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
RUNS_DIR  = REPO_ROOT / "runtime" / "runs"
LATEST    = RUNS_DIR / "latest.json"

# 引数解析
args = sys.argv[1:]
DRY_RUN   = "--dry-run" in args
args = [a for a in args if not a.startswith("--")]
max_loops = int(args[0]) if args else 999

# 連続 incomplete でのフェイルセーフ
MAX_CONSECUTIVE_INCOMPLETE = 2


def get_next_task():
    if not LATEST.exists():
        return None
    try:
        d = json.loads(LATEST.read_text(encoding="utf-8"))
        return d.get("next_task")
    except Exception:
        return None


def get_last_report_source():
    if not LATEST.exists():
        return None
    try:
        d = json.loads(LATEST.read_text(encoding="utf-8"))
        return d.get("report_source")
    except Exception:
        return None


def print_status(msg):
    print(f"[loop-run] {msg}", flush=True)


# ─── 事前確認 ──────────────────────────────────────────────
next_task = get_next_task()
if next_task:
    label = f"{next_task['task_id']} — {next_task['task_title'][:60]}"
else:
    label = "（次タスクなし）"

print_status(f"開始。max_loops={max_loops}, 次タスク: {label}")

if DRY_RUN:
    print_status("--dry-run モード: 実行しません")
    sys.exit(0)

if not next_task:
    print_status("pending タスクがありません。終了します。")
    sys.exit(0)

# ─── ループ実行 ─────────────────────────────────────────────
consecutive_incomplete = 0

for i in range(1, max_loops + 1):
    next_task = get_next_task()
    if not next_task:
        print_status(f"全タスク完了。{i - 1} ループ実行しました。")
        break

    task_label = f"{next_task['task_id']} — {next_task['task_title'][:50]}"
    print_status(f"ループ {i}/{max_loops}: {task_label}")

    # loop_start.py を起動（Stop Hook が正しく動くよう同プロセスで実行）
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "scripts" / "loop_start.py")],
        cwd=str(REPO_ROOT),
    )

    if result.returncode != 0:
        print_status(f"エラー終了 (returncode={result.returncode})。中断します。")
        sys.exit(result.returncode)

    # 結果確認
    report_source = get_last_report_source()
    print_status(f"ループ {i} 完了 — report_source={report_source}")

    if report_source == "incomplete":
        consecutive_incomplete += 1
        print_status(f"WARNING: report Skill が実行されませんでした ({consecutive_incomplete}/{MAX_CONSECUTIVE_INCOMPLETE})")
        if consecutive_incomplete >= MAX_CONSECUTIVE_INCOMPLETE:
            print_status("連続 incomplete 検出。無限ループを防止するため中断します。")
            sys.exit(1)
    else:
        consecutive_incomplete = 0

print_status("loop_run 終了。")
