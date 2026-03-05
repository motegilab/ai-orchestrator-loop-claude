# Skill: release

**Auto-invoke triggers**: "release", "publish", "OSS readiness check", "リリース", "公開チェック"

## Purpose

Verify OSS readiness of this template repository before pushing to GitHub.
Checks safety, required files, template neutrality, and SSOT integrity.

## Must Read First

1. `SSOT.md` §1 (absolute rules)
2. `policy/ssot_integrity.json` (current hash)
3. `docs/runbooks/release-checklist.md` (full checklist)

## Inputs

- Current working directory (repo root)
- `policy/ssot_integrity.json`
- `CLAUDE.md`, `SSOT.md`, `README.md`, `LICENSE`, `SECURITY.md`

## Steps

### 1. Safety Check
- Verify `runtime/` is not tracked by Git
  - Evidence: `git status` output — `runtime/` must not appear
- Scan all tracked files for secrets patterns (`password`, `token`, `webhook`, `Bearer`, private paths)
- Confirm `policy/notifications.json` has `"enabled": false`

### 2. Required Files Check
- Verify all required files exist:
  - `README.md`, `LICENSE`, `SECURITY.md`
  - `CLAUDE.md` (max 200 lines)
  - `SSOT.md`
  - `Makefile`
  - `.gitignore`
  - `.claude/settings.json`
  - `policy/policy.json`
  - `policy/ssot_integrity.json`

### 3. Template Neutrality Check
- `CLAUDE.md` and `SSOT.md` must not contain project-specific names or hardcoded paths
- `tasks/milestones.json` must reflect template tasks, not project tasks

### 4. Integrity Verification
- Run: `python .claude/hooks/ssot_gate.py`
- Expected: exit code 0 (no output to stderr)
- If hash mismatch: run `python .claude/hooks/ssot_gate.py --update-hash` after confirming SSOT.md is correct

### 5. Functional Smoke Test
- Confirm all Hook scripts are syntactically valid:
  ```bash
  python -m py_compile .claude/hooks/on_session_start.py
  python -m py_compile .claude/hooks/on_stop.py
  python -m py_compile .claude/hooks/ssot_gate.py
  python -m py_compile .claude/hooks/post_tool_quality.py
  ```
- Expected: exit code 0 for each

## Outputs

- Report written to `runtime/reports/REPORT_LATEST.md`
- Section: `## release_check_results` with pass/fail per item
- `evidence_paths`: git status output, syntax check results
- `decision`: `ready` | `blocked` (with reasons)

## Failure Modes

| Failure | Remediation |
|---------|-------------|
| `runtime/` appears in git status | Check `.gitignore` — `runtime/**` must be present |
| Secret pattern found | Remove from source, rotate the credential |
| SSOT hash mismatch | Run `--update-hash` after confirming SSOT.md is intentionally changed |
| Syntax error in Hook | Fix the Hook script before release |
| CLAUDE.md > 200 lines | Trim — move details to `docs/` |
