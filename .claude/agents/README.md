# .claude/agents — Subagent Definitions (v2+)

This directory is reserved for **Subagent definitions** — a v2 feature for parallel task execution.

## Status

**Not implemented in v1.** This directory is a placeholder.

## What Subagents Will Enable (v2)

Claude Code supports spawning specialized subagents via the `Agent` tool.
Subagents can run independently in parallel, each with their own context window.

Planned subagent roles:

| Agent | Role |
|-------|------|
| `observer.md` | Runs Observe phase in isolation |
| `patcher.md` | Applies minimal diffs based on Observer output |
| `verifier.md` | Runs verification commands and reports results |

## Design Principles for v2

- Subagents must not modify `SSOT.md` or `policy/ssot_integrity.json`
- All outputs go to `runtime/` only
- Parent agent coordinates; subagents execute
- Each subagent reads a scoped context (not the full session history)

## Reference

See [docs/decisions/ADR-0001-claude-adapter.md](../../docs/decisions/ADR-0001-claude-adapter.md)
for the v1 decision that defers subagents to v2.
