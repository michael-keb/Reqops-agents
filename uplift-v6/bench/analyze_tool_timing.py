#!/usr/bin/env python3
"""Analyze agent.stream.jsonl — where wall-clock time goes per tool/phase."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = ROOT / "sessions"

SESSION_IDS = [
    "20260527-054303-pet-sitting-app",
    "20260527-055307-trace-test-app",
    "20260527-055322-trace-test-app-2",
    "20260527-055400-dog-walking-app",
    "20260527-120627-cosntruciton-app-for-tradies-to-find-oth",
    "20260527-124803-constuction-app-for-carpenters",
]


def tool_name(obj: dict) -> str:
    tc = obj.get("tool_call") or {}
    for key in tc:
        if key.endswith("ToolCall"):
            return key[: -len("ToolCall")]
    return "unknown"


def tool_target(obj: dict) -> str:
    tc = obj.get("tool_call") or {}
    for key, body in tc.items():
        if not key.endswith("ToolCall"):
            continue
        args = body.get("args") or {}
        path = args.get("path") or args.get("targetDirectory") or ""
        if path:
            p = Path(path)
            try:
                return str(p.relative_to(ROOT))
            except ValueError:
                parts = p.parts
                return "/".join(parts[-3:]) if len(parts) >= 3 else p.name
        cmd = args.get("command") or args.get("cmd") or ""
        if cmd:
            return cmd[:60]
        pat = args.get("globPattern") or args.get("pattern") or ""
        if pat:
            return pat[:40]
    return "?"


@dataclass
class ToolCall:
    call_id: str
    name: str
    target: str
    started_ms: int
    completed_ms: int | None = None

    @property
    def duration_ms(self) -> int | None:
        if self.completed_ms is None:
            return None
        return max(0, self.completed_ms - self.started_ms)


@dataclass
class TurnSlice:
    turn_idx: int
    user_preview: str = ""
    wall_s: float | None = None
    stream_start_ms: int | None = None
    stream_end_ms: int | None = None
    tools: list[ToolCall] = field(default_factory=list)
    thinking_ms: int = 0
    thinking_first_ms: int | None = None
    thinking_last_ms: int | None = None
    model_calls: set[str] = field(default_factory=set)

    @property
    def stream_span_ms(self) -> int | None:
        if self.stream_start_ms is None or self.stream_end_ms is None:
            return None
        return self.stream_end_ms - self.stream_start_ms

    def tool_total_ms(self) -> int:
        return sum(t.duration_ms or 0 for t in self.tools)

    def gap_ms(self) -> int | None:
        span = self.stream_span_ms
        if span is None:
            return None
        return max(0, span - self.tool_total_ms() - self.thinking_ms)


def parse_trace_turns(session_dir: Path) -> list[dict]:
    trace = session_dir / "agent.trace.jsonl"
    if not trace.is_file():
        return []
    turns: list[dict] = []
    current: dict | None = None
    for line in trace.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("kind") != "turn":
            continue
        action = (e.get("data") or {}).get("action")
        if action == "start":
            current = {
                "turn": (e.get("data") or {}).get("turn"),
                "preview": (e.get("data") or {}).get("text_preview", "")[:80],
                "start_ts": e.get("ts"),
            }
        elif action == "complete" and current:
            current["elapsed_s"] = (e.get("data") or {}).get("elapsed_s")
            current["preview"] = current.get("preview") or (e.get("data") or {}).get("text_preview", "")[:80]
            turns.append(current)
            current = None
    return turns


def parse_stream(session_dir: Path) -> list[TurnSlice]:
    stream = session_dir / "agent.stream.jsonl"
    if not stream.is_file():
        return []

    turns: list[TurnSlice] = []
    current: TurnSlice | None = None
    open_tools: dict[str, ToolCall] = {}
    turn_idx = 0

    for line in stream.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts = obj.get("timestamp_ms")
        etype = obj.get("type")
        subtype = obj.get("subtype")

        if etype == "user":
            # new turn boundary on user message (skip init echo on turn 1 bootstrap)
            text = ""
            msg = obj.get("message") or {}
            content = msg.get("content")
            if isinstance(content, list) and content:
                text = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
            elif isinstance(content, str):
                text = content
            if current and current.stream_end_ms is not None:
                turns.append(current)
            turn_idx += 1
            current = TurnSlice(
                turn_idx=turn_idx,
                user_preview=text.replace("\n", " ")[:100],
                stream_start_ms=ts,
            )
            open_tools.clear()
            continue

        if current is None:
            continue

        if ts is not None:
            if current.stream_start_ms is None:
                current.stream_start_ms = ts
            current.stream_end_ms = ts

        mc = obj.get("model_call_id")
        if mc:
            current.model_calls.add(mc)

        if etype == "tool_call":
            cid = obj.get("call_id") or ""
            if subtype == "started" and ts is not None:
                tc = ToolCall(call_id=cid, name=tool_name(obj), target=tool_target(obj), started_ms=ts)
                open_tools[cid] = tc
            elif subtype == "completed" and ts is not None:
                if cid in open_tools:
                    open_tools[cid].completed_ms = ts
                    current.tools.append(open_tools.pop(cid))
                else:
                    current.tools.append(
                        ToolCall(call_id=cid, name=tool_name(obj), target=tool_target(obj), started_ms=ts, completed_ms=ts)
                    )

        elif etype == "thinking" and subtype == "delta" and ts is not None:
            if current.thinking_first_ms is None:
                current.thinking_first_ms = ts
            if current.thinking_last_ms is not None and ts >= current.thinking_last_ms:
                # approximate delta between thinking tokens
                current.thinking_ms += ts - current.thinking_last_ms
            current.thinking_last_ms = ts

        elif etype == "result" and subtype == "success":
            if ts is not None:
                current.stream_end_ms = ts

    if current:
        turns.append(current)

    # merge wall clock from trace
    trace_turns = parse_trace_turns(session_dir)
    for i, sl in enumerate(turns):
        if i < len(trace_turns):
            sl.wall_s = trace_turns[i].get("elapsed_s")
            if not sl.user_preview:
                sl.user_preview = trace_turns[i].get("preview", "")

    return turns


def fmt_ms(ms: int | None) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.2f}s"


def fmt_pct(part: float, whole: float) -> str:
    if whole <= 0:
        return "—"
    return f"{100 * part / whole:.1f}%"


def aggregate_by_tool_name(turns: list[TurnSlice]) -> dict[str, int]:
    agg: dict[str, int] = defaultdict(int)
    for t in turns:
        for tool in t.tools:
            if tool.duration_ms:
                agg[tool.name] += tool.duration_ms
    return dict(agg)


def render_session(session_id: str) -> str:
    session_dir = SESSIONS / session_id
    lines: list[str] = []
    lines.append(f"### `{session_id}`")
    lines.append("")

    trace_turns = parse_trace_turns(session_dir)
    stream_turns = parse_stream(session_dir)
    has_stream = (session_dir / "agent.stream.jsonl").is_file()

    if not has_stream:
        # infer from trace only
        spawn_fmt = "unknown"
        for line in (session_dir / "agent.trace.jsonl").read_text(encoding="utf-8").splitlines():
            if "output-format text" in line:
                spawn_fmt = "text (no tool timing in stream)"
                break
            if "output-format stream-json" in line:
                spawn_fmt = "stream-json"
                break
        if "PTY" in (session_dir / "agent.trace.jsonl").read_text(encoding="utf-8")[:5000]:
            spawn_fmt = "PTY (no stream-json)"
        lines.append(f"- **Stream log:** none · format inferred: **{spawn_fmt}**")
        if trace_turns:
            lines.append(f"- **Turns (wall clock from trace):** {len(trace_turns)}")
            for tt in trace_turns:
                lines.append(f"  - Turn {tt.get('turn')}: **{tt.get('elapsed_s')}s** — `{tt.get('preview', '')}`")
        else:
            lines.append("- **Turns:** no complete turn in trace")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"- **Stream log:** `agent.stream.jsonl` · **{len(stream_turns)}** user-turn slice(s) parsed")
    lines.append("")

    session_tool_agg = aggregate_by_tool_name(stream_turns)
    session_span = sum(t.stream_span_ms or 0 for t in stream_turns)
    session_tool = sum(t.tool_total_ms() for t in stream_turns)
    session_think = sum(t.thinking_ms for t in stream_turns)

    if session_tool_agg:
        lines.append("**Session totals (stream timestamps)**")
        lines.append("")
        lines.append("| Tool | Total time | Share of tool time |")
        lines.append("|------|------------|-------------------|")
        for name, ms in sorted(session_tool_agg.items(), key=lambda x: -x[1]):
            lines.append(f"| `{name}` | {fmt_ms(ms)} | {fmt_pct(ms, session_tool)} |")
        lines.append("")
        gap = max(0, session_span - session_tool - session_think)
        lines.append("| Phase | Time | Share of stream span |")
        lines.append("|-------|------|---------------------|")
        lines.append(f"| Tool execution (started→completed) | {fmt_ms(session_tool)} | {fmt_pct(session_tool, session_span)} |")
        lines.append(f"| Thinking deltas (approx) | {fmt_ms(session_think)} | {fmt_pct(session_think, session_span)} |")
        lines.append(f"| LLM / orchestration gaps* | {fmt_ms(gap)} | {fmt_pct(gap, session_span)} |")
        lines.append(f"| **Stream span** | **{fmt_ms(session_span)}** | 100% |")
        lines.append("")
        lines.append("*Gaps = time between stream events minus tool duration and thinking deltas — mostly model reasoning between tool rounds and token generation.")
        lines.append("")

    for sl in stream_turns:
        wall = f"{sl.wall_s:.2f}s" if sl.wall_s else "—"
        lines.append(f"#### Turn {sl.turn_idx} (bridge wall: **{wall}**)")
        lines.append("")
        lines.append(f"User input: `{sl.user_preview}`")
        lines.append("")
        if not sl.tools and sl.stream_span_ms is None:
            lines.append("_No tool events captured (likely failed early)._")
            lines.append("")
            continue

        lines.append("| # | Tool | Target | Duration |")
        lines.append("|---|------|--------|----------|")
        for i, tool in enumerate(sorted(sl.tools, key=lambda t: t.started_ms), 1):
            lines.append(f"| {i} | `{tool.name}` | `{tool.target}` | **{fmt_ms(tool.duration_ms)}** |")
        lines.append("")

        span = sl.stream_span_ms or 0
        tools_ms = sl.tool_total_ms()
        think_ms = sl.thinking_ms
        gap_ms = sl.gap_ms() or 0
        lines.append("| Phase | Duration | % of stream |")
        lines.append("|-------|----------|-------------|")
        lines.append(f"| Tools | {fmt_ms(tools_ms)} | {fmt_pct(tools_ms, span)} |")
        lines.append(f"| Thinking | {fmt_ms(think_ms)} | {fmt_pct(think_ms, span)} |")
        lines.append(f"| LLM gaps | {fmt_ms(gap_ms)} | {fmt_pct(gap_ms, span)} |")
        lines.append(f"| Stream span | {fmt_ms(span)} | 100% |")
        if sl.wall_s and span:
            overhead = max(0, sl.wall_s * 1000 - span)
            lines.append(f"| Bridge overhead† | {fmt_ms(int(overhead))} | {fmt_pct(overhead, sl.wall_s * 1000)} |")
        lines.append("")
        lines.append("†Spawn, init, and tail after last stream event.")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    out_path = ROOT / "docs" / "tool-timing-analysis.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parts = [
        "# Uplift v6 — where time goes per tooling",
        "",
        "Generated from `sessions/*/agent.stream.jsonl` (NDJSON `timestamp_ms` on each event)",
        "cross-referenced with `agent.trace.jsonl` turn boundaries (`elapsed_s` wall clock).",
        "",
        "## How to read this",
        "",
        "| Metric | Source | Meaning |",
        "|--------|--------|---------|",
        "| **Tool duration** | `tool_call.started` → `tool_call.completed` same `call_id` | Actual file/tool execution time reported by agent CLI |",
        "| **Thinking** | Sum of deltas between consecutive `thinking/delta` events | Internal model reasoning stream (approximate) |",
        "| **LLM gaps** | Stream span − tools − thinking | Model turns between tool rounds, assistant text generation, scheduling |",
        "| **Bridge wall** | `turn complete.elapsed_s` in trace | Full subprocess lifetime including spawn + init + tail |",
        "",
        "## Architecture reminder",
        "",
        "```",
        "Each turn: spawn agent --resume CHAT -p PROMPT --output-format stream-json",
        "  → stdout NDJSON lines → agent.stream.jsonl (raw)",
        "  → stream_parser → agent.trace.jsonl (tool/assistant/result kinds)",
        "```",
        "",
        "---",
        "",
    ]

    all_agg: dict[str, int] = defaultdict(int)
    all_span = 0
    all_tool = 0
    all_think = 0

    for sid in SESSION_IDS:
        parts.append(render_session(sid))
        parts.append("---")
        parts.append("")
        for sl in parse_stream(SESSIONS / sid):
            all_span += sl.stream_span_ms or 0
            all_tool += sl.tool_total_ms()
            all_think += sl.thinking_ms
            for name, ms in aggregate_by_tool_name([sl]).items():
                all_agg[name] += ms

    parts.append("## Cross-session summary (stream-json sessions only)")
    parts.append("")
    if all_agg:
        parts.append("| Tool | Total across sessions | Share |")
        parts.append("|------|----------------------|-------|")
        for name, ms in sorted(all_agg.items(), key=lambda x: -x[1]):
            parts.append(f"| `{name}` | {fmt_ms(ms)} | {fmt_pct(ms, all_tool)} |")
        parts.append("")
        gap = max(0, all_span - all_tool - all_think)
        parts.append("| Phase | Total | Share of stream span |")
        parts.append("|-------|-------|---------------------|")
        parts.append(f"| Tool execution | {fmt_ms(all_tool)} | {fmt_pct(all_tool, all_span)} |")
        parts.append(f"| Thinking | {fmt_ms(all_think)} | {fmt_pct(all_think, all_span)} |")
        parts.append(f"| LLM gaps | {fmt_ms(gap)} | {fmt_pct(gap, all_span)} |")
        parts.append(f"| **All stream span** | **{fmt_ms(all_span)}** | 100% |")
        parts.append("")
        parts.append("### Typical turn 1 breakdown (pattern)")
        parts.append("")
        parts.append("1. **Reads (~0.1–0.2s each, often parallel):** SKILL.md, rubric, gap-legend, Memory.md")
        parts.append("2. **Glob (~0.1s):** list session dir / turns")
        parts.append("3. **LLM gap (~5–15s):** scoring gaps, drafting question")
        parts.append("4. **Edits (~0.2–0.5s each, serial):** user-input, turn.json, multiplier-audit, response.md, Memory.md")
        parts.append("5. **Result emit (~0s):** final Reflection + Question to stdout")
        parts.append("")
        parts.append("**Turn 2+** adds reads of prior `turn.json` / `Memory.md` but skips full rubric reload; still dominated by LLM gap.")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
