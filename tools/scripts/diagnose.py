#!/usr/bin/env python3
"""
diagnose.py — AI Orchestrator Loop 自己診断スクリプト
使い方: python tools/scripts/diagnose.py
        make diagnose

チェック項目:
  1. Hooks 整合性     settings.json に登録されたHookファイルが実在するか
  2. Skill YAML 妥当性 各SKILL.mdのfrontmatterにname/descriptionがあるか
  3. 未対応 Proposal   runtime/proposals/ に未対応の提案が溜まっていないか
  4. 未使用 Skill      audit_log.jsonl でまったく呼ばれていないSkillがないか
  5. 停滞タスク        milestones.json に長期 pending のマイルストーンがないか
  6. Upstream ドリフト git remote との差分コミット数を確認する
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# --- 結果収集 ---

issues = []   # (level, label, message)

def ok(label, msg):
    print(f"  \033[32mOK\033[0m   {label}: {msg}")

def warn(label, msg):
    issues.append(("WARN", label, msg))
    print(f"  \033[33mWARN\033[0m {label}: {msg}")

def error(label, msg):
    issues.append(("ERROR", label, msg))
    print(f"  \033[31mERROR\033[0m {label}: {msg}")

def info(label, msg):
    print(f"  \033[36mINFO\033[0m {label}: {msg}")


# ============================================================
# Check 1: Hooks 整合性
# ============================================================

def check_hooks():
    print("\n[1] Hooks 整合性チェック")
    settings_path = ROOT / ".claude" / "settings.json"
    if not settings_path.exists():
        error("hooks", ".claude/settings.json が見つからない")
        return

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    hooks_config = settings.get("hooks", {})

    # settings.json に記載されたコマンドからスクリプトパスを抽出
    hook_commands = []
    for event, entries in hooks_config.items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                hook_commands.append((event, cmd))

    missing = []
    for event, cmd in hook_commands:
        # "python .claude/hooks/xxx.py" 形式から .py パスを抽出
        m = re.search(r'(\.claude/hooks/\S+\.py)', cmd)
        if m:
            rel_path = m.group(1)
            full_path = ROOT / rel_path
            if not full_path.exists():
                missing.append(f"{event}: {rel_path}")

    if missing:
        for m in missing:
            error("hooks", f"ファイルが存在しない — {m}")
    else:
        ok("hooks", f"{len(hook_commands)} 件のHookコマンド、全ファイル確認OK")


# ============================================================
# Check 2: Skill YAML 妥当性
# ============================================================

def check_skills():
    print("\n[2] Skill YAML 妥当性チェック")
    skills_dir = ROOT / ".claude" / "skills"
    skill_files = list(skills_dir.glob("*/SKILL.md"))

    if not skill_files:
        warn("skills", "SKILL.md が1件も見つからない")
        return

    for sf in sorted(skill_files):
        content = sf.read_text(encoding="utf-8")
        # YAML frontmatter を抽出
        m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not m:
            error("skills", f"{sf.parent.name}/SKILL.md — frontmatter がない")
            continue
        fm = m.group(1)
        if "name:" not in fm:
            error("skills", f"{sf.parent.name}/SKILL.md — 'name:' フィールドがない")
        elif "description:" not in fm:
            warn("skills", f"{sf.parent.name}/SKILL.md — 'description:' フィールドがない")
        else:
            ok("skills", f"{sf.parent.name}/SKILL.md — OK")


# ============================================================
# Check 3: 未対応 Proposal
# ============================================================

def check_proposals():
    print("\n[3] 未対応 Proposal チェック")
    proposals_dir = ROOT / "runtime" / "proposals"
    if not proposals_dir.exists():
        info("proposals", "runtime/proposals/ が存在しない（提案なし）")
        return

    proposals = list(proposals_dir.glob("SKILL_PROPOSAL_*.md"))
    if not proposals:
        ok("proposals", "未対応の提案なし")
        return

    warn("proposals", f"{len(proposals)} 件の未対応 Skill 提案が溜まっています:")
    for p in sorted(proposals):
        print(f"           → {p.name}")


# ============================================================
# Check 4: 未使用 Skill (audit_log.jsonl)
# ============================================================

def check_unused_skills():
    print("\n[4] 未使用 Skill チェック（audit_log から）")
    audit_log = ROOT / "runtime" / "logs" / "audit_log.jsonl"
    skills_dir = ROOT / ".claude" / "skills"

    skill_names = {sf.parent.name for sf in skills_dir.glob("*/SKILL.md")
                   if sf.parent.name != "INDEX"}

    if not audit_log.exists():
        info("unused_skills", "audit_log.jsonl が存在しない（スキップ）")
        return

    used_skills = set()
    try:
        lines = audit_log.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                skill = entry.get("skill") or entry.get("tool_name") or ""
                # audit_log の skill フィールドを確認
                if skill in skill_names:
                    used_skills.add(skill)
                # tool_input に skill 名が含まれる場合も検索
                tool_input = entry.get("tool_input", {})
                if isinstance(tool_input, dict):
                    skill_val = tool_input.get("skill", "")
                    if skill_val in skill_names:
                        used_skills.add(skill_val)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        warn("unused_skills", f"audit_log.jsonl の読み込みエラー: {e}")
        return

    unused = skill_names - used_skills
    if unused:
        warn("unused_skills", f"未使用の Skill: {', '.join(sorted(unused))}")
        print("           （audit_log に呼び出し記録なし — 削除または確認を検討）")
    else:
        ok("unused_skills", f"全 {len(skill_names)} Skill が使用記録あり")


# ============================================================
# Check 5: 停滞タスク
# ============================================================

def check_stale_milestones():
    print("\n[5] 停滞タスク チェック")
    milestones_path = ROOT / "tasks" / "milestones.json"
    if not milestones_path.exists():
        warn("milestones", "tasks/milestones.json が見つからない")
        return

    data = json.loads(milestones_path.read_text(encoding="utf-8"))
    milestones = data.get("milestones", [])

    # git log でタスクファイルの最終更新日を取得
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", "--", "tasks/milestones.json"],
            capture_output=True, text=True, cwd=ROOT
        )
        last_updated_str = result.stdout.strip()
        if last_updated_str:
            # "2026-03-20 10:00:00 +0900" 形式
            last_updated = datetime.fromisoformat(last_updated_str)
            now = datetime.now(tz=timezone.utc).astimezone(last_updated.tzinfo)
            days_since = (now - last_updated).days
        else:
            days_since = None
    except Exception:
        days_since = None

    pending_milestones = [m for m in milestones if m.get("status") != "done"]

    if not pending_milestones:
        ok("milestones", "全マイルストーン完了済み")
        return

    for m in pending_milestones:
        waves = m.get("waves", [])
        pending_tasks = []
        for w in waves:
            for t in w.get("tasks", []):
                if t.get("status") == "pending":
                    pending_tasks.append(t.get("id", "?"))

        msg = f"'{m['id']} {m.get('title', '')}' — pending タスク {len(pending_tasks)} 件"
        if days_since is not None and days_since >= 7:
            warn("milestones", f"{msg} （最終更新: {days_since}日前）")
        else:
            ok("milestones", msg)

    if days_since is not None and days_since >= 7:
        warn("milestones", f"milestones.json の最終コミットが {days_since}日前 — ループが止まっていないか確認を")


# ============================================================
# Check 6: Upstream ドリフト
# ============================================================

def check_upstream_drift():
    print("\n[6] Upstream ドリフト チェック")
    try:
        # リモートをフェッチ（--dry-run 相当で fetch のみ）
        fetch = subprocess.run(
            ["git", "fetch", "--dry-run"],
            capture_output=True, text=True, cwd=ROOT
        )
        # ahead/behind を確認
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
            capture_output=True, text=True, cwd=ROOT
        )
        if result.returncode != 0:
            info("upstream", "upstream ブランチが設定されていない（スキップ）")
            return

        parts = result.stdout.strip().split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])
            if behind > 0:
                warn("upstream", f"upstream より {behind} コミット遅れています（`git pull` を検討）")
            elif ahead > 0:
                info("upstream", f"upstream より {ahead} コミット先行（未プッシュ）")
            else:
                ok("upstream", "upstream と同期済み")
        else:
            info("upstream", "ドリフト情報を取得できなかった")
    except FileNotFoundError:
        info("upstream", "git コマンドが見つからない（スキップ）")
    except Exception as e:
        warn("upstream", f"ドリフト確認エラー: {e}")


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 50)
    print("  AI Orchestrator Loop — Diagnose")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    check_hooks()
    check_skills()
    check_proposals()
    check_unused_skills()
    check_stale_milestones()
    check_upstream_drift()

    # サマリ
    print("\n" + "=" * 50)
    errors = [i for i in issues if i[0] == "ERROR"]
    warns  = [i for i in issues if i[0] == "WARN"]

    if errors:
        print(f"  \033[31m判定: ERROR — {len(errors)} 件のエラーがあります\033[0m")
        sys.exit(2)
    elif warns:
        print(f"  \033[33m判定: WARN  — {len(warns)} 件の警告があります\033[0m")
        sys.exit(1)
    else:
        print("  \033[32m判定: OK    — 問題なし\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
