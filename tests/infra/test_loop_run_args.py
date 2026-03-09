"""
tests/infra/test_loop_run_args.py

loop_run.py の引数解析ロジックをサブプロセスで smoke テスト。
実際の Claude は起動しない（--dry-run + pending タスクなし で即終了する）。
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT     = Path(__file__).parent.parent.parent
LOOP_RUN_PY   = REPO_ROOT / "tools" / "scripts" / "loop_run.py"


def run(*extra_args, stdin_text="") -> tuple[int, str]:
    """loop_run.py を実行して (returncode, stdout+stderr) を返す"""
    result = subprocess.run(
        [sys.executable, str(LOOP_RUN_PY), *extra_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=stdin_text,
        cwd=str(REPO_ROOT),
    )
    return result.returncode, result.stdout + result.stderr


# ─── --dry-run ────────────────────────────────────────────────────────────────

def test_dry_run_exits_without_executing():
    code, out = run("--dry-run", "--skip-check")
    # dry-run はループを実行しないので returncode=0
    assert code == 0
    assert "--dry-run" in out or "実行しません" in out


# ─── max_loops 引数 ───────────────────────────────────────────────────────────

def test_explicit_loops_skips_interactive_prompt():
    """数値引数を渡すと対話プロンプトなしで即終了（pending タスクなし）"""
    code, out = run("3", "--skip-check")
    # pending タスクがないので 0 で終了するはず
    assert code == 0
    assert "pending タスクがありません" in out or "全タスク完了" in out or "loop_run 終了" in out


def test_yes_flag_skips_prompts():
    """--yes で全プロンプトをスキップして即終了"""
    code, out = run("--yes")
    assert code in (0, 1)  # SSOT WARN があっても続行するので 0 か ssot error で 1


# ─── --skip-check ─────────────────────────────────────────────────────────────

def test_skip_check_bypasses_ssot():
    """--skip-check は SSOT チェックを実行しない"""
    code, out = run("1", "--skip-check")
    # ssot_check の出力が混入しないことを確認
    assert "SSOT Quality Check" not in out


# ─── 対話プロンプト（stdin から入力） ─────────────────────────────────────────

def test_interactive_n_for_check_skips_ssot():
    """対話モードで SSOT チェック=n → チェックをスキップしてループに進む"""
    # SSOT チェック: n, ループ回数: 1
    code, out = run(stdin_text="n\n1\n")
    assert code in (0, 1)
    assert "SSOT Quality Check" not in out


def test_interactive_enter_means_unlimited():
    """対話モードでループ回数を Enter → 無制限（999）で起動"""
    # SSOT チェック: n, ループ回数: Enter（空）
    code, out = run(stdin_text="n\n\n")
    assert code in (0, 1)
    assert "無制限" in out
