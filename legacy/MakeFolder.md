You are creating a NEW repository (do not modify any existing repo).
Repo name: ai-orchestrator-loop_claude

GOAL:
Create a Claude Code style project skeleton that can later host/drive the existing AI Orchestrator Loop via CLI, but for now only scaffolds structure + docs + placeholders (no runtime secrets, no Discord integration).

HARD RULES:
- One cause / one fix.
- No external dependencies.
- Do NOT copy tools/orchestrator_runtime contents (runtime is not tracked).
- Keep it OSS-safe: no tokens, no secrets, no private paths.
- Windows-friendly commands in docs.
- All scripts must be safe and non-destructive.

MUST CREATE (project structure):
/
  README.md
  LICENSE (MIT placeholder ok)
  SECURITY.md
  CLAUDE.md
  docs/
    architecture.md
    decisions/
      ADR-0001-claude-adapter.md
    runbooks/
      env-check.md
      observe-patch-verify.md
      release-checklist.md
    mapping/
      orchestrator-loop-mapping.md
  .claude/
    settings.json
    hooks/
      README.md
      ssot_integrity_hook.md
      ssot_compliance_gate_hook.md
      prompt_qa_gate_hook.md
      prompt_eval_hook.md
      notify_policy_hook.md
    skills/
      observe/
        SKILL.md
      patch/
        SKILL.md
      verify/
        SKILL.md
      release/
        SKILL.md
  policy/
    policy.json
    notifications.json
    ssot_integrity.json
    prompt_eval.json
  tools/
    scripts/
      orch_env_check.ps1
      orch_health_check.ps1
      orch_report_wrapper.ps1
    prompts/
      observe.md
      patch.md
      verify.md
  src/
    placeholder.txt

CONTENT REQUIREMENTS (important):

1) CLAUDE.md
- Acts as project memory for Claude:
  - Standards: One cause/One fix, evidence-based reporting (exit code, stdout/stderr tail, evidence_paths)
  - Constraints: no runtime tracked, no .git access, Windows-safe commands
  - Workflow: Observe -> Patch -> Verify -> Report
  - Where configs live: policy/*.json
  - How to run: examples of PowerShell scripts under tools/scripts/
  - Note: this repo is an adapter/skeleton to drive an external orchestrator repo later.

2) docs/runbooks/env-check.md
- Explain what “env check” means and how to run it (PowerShell).
- Mention future artifacts approach: env_check.json, health.txt, reports.

3) docs/mapping/orchestrator-loop-mapping.md
- Map existing Orchestrator Loop concepts to Claude Code:
  - SSOT -> CLAUDE.md + docs/architecture + policy
  - prompts -> .claude/skills + tools/prompts
  - gates/hooks -> .claude/hooks (conceptually) + future scripts
  - runtime -> out-of-repo artifacts directory (ORCH_RUNTIME_DIR)

4) policy files (placeholders with sane defaults):
- policy/policy.json:
  - loop_defaults: interval_minutes=20, max_auto_loops=3 (enabled true)
  - decision_policy: ask_no_action_overrides_all=true (document)
- policy/notifications.json:
  - enabled true, channels ["none"], quality_warning thresholds, loop_end reasons
- policy/ssot_integrity.json:
  - enabled true, files baseline empty for now (to be filled after first commit)
- policy/prompt_eval.json:
  - enabled true, threshold 0.85, weights for checks (D1..D6, E1..)

5) .claude/skills/*
- Each SKILL.md must be reusable workflow steps:
  - MUST READ FIRST list
  - Inputs
  - Steps
  - Outputs (artifact paths)
  - Failure modes / remediation
- observe skill outputs: "issue candidates" + what to check in reports/logs
- patch skill: minimal diff, target file specification
- verify skill: required commands, exit codes, evidence_paths
- release skill: OSS readiness checklist (README/LICENSE/SECURITY + runtime not tracked)

6) tools/scripts/*.ps1
- Simple, dependency-free wrappers (placeholders are fine) that print what they would do:
  - orch_env_check.ps1: checks for required files + prints repo_root
  - orch_health_check.ps1: placeholder for calling /health (no network required yet)
  - orch_report_wrapper.ps1: placeholder to call make orch-report in the target repo later
- Scripts must be safe if run in this repo (no destructive actions).

VERIFY (must do):
- List the created file tree in the report.
- Ensure no secrets or private absolute paths are included.
- Provide a brief “how to start” in README.md.

REPORT (output format):
- hypothesis_one_cause
- one_fix
- files_created (full list)
- verify_commands + exit codes (e.g., tree/dir listing, optional git status)
- evidence_paths (paths to the key docs created)
- decision