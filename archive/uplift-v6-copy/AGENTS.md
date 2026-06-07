# Uplift v6

Discovery runs through **Cursor Agent CLI** (`agent`) on a **persistent PTY** — one process, stdin per turn.

## Agent (CLI)

- Output **Reflection + 5 Questions** in markdown only — respond immediately, no file reads, no scoring narration.
- **No file tools** on session artifacts — bridge writes `turns/NN/*` from stdout.

## Bridge (Python)

- Default: `PtyAgent` — spawns `agent` once, writes each message to stdin.
- On `turn_complete`, extracts markdown from PTY buffer → writes `response.md`, `user-input.txt`, `turn.json`, etc.
- Optional: `UPLIFT_AGENT_MODE=headless` for per-turn `agent --resume CHAT -p -- PROMPT --output-format stream-json` (tool trace, ~3s cold start per turn).

## Skill

`.cursor/skills/uplift-discovery/SKILL.md`
