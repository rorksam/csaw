#!/usr/bin/env python3
"""Render a Claude Code .jsonl transcript into a human-readable Markdown log.

Usage: render_transcript.py <input.jsonl> <output.md>

Produces a plaintext/Markdown rendering of the conversation suitable for the
CSAW submission's ai/ deliverable: user prompts, assistant thinking + replies,
tool calls (with inputs), and tool results. Bookkeeping records
(queue-operation, atis-latch, last-prompt, attachment) are skipped.
"""
import json
import sys


def _clip(s, n=4000):
    s = s if isinstance(s, str) else str(s)
    if len(s) > n:
        return s[:n] + f"\n... [truncated {len(s) - n} chars]"
    return s


def _render_blocks(content, out):
    """content may be a plain string or a list of typed blocks."""
    if isinstance(content, str):
        if content.strip():
            out.append(content.rstrip())
        return
    if not isinstance(content, list):
        out.append(_clip(repr(content)))
        return
    for b in content:
        if not isinstance(b, dict):
            out.append(_clip(str(b)))
            continue
        bt = b.get("type")
        if bt == "text":
            out.append(b.get("text", "").rstrip())
        elif bt == "thinking":
            th = (b.get("thinking") or "").rstrip()
            if th:
                out.append("> **[thinking]**\n>\n" + "\n".join("> " + l for l in th.splitlines()))
        elif bt == "tool_use":
            name = b.get("name", "?")
            inp = b.get("input", {})
            try:
                inp_s = json.dumps(inp, indent=2, ensure_ascii=False)
            except Exception:
                inp_s = str(inp)
            out.append(f"**[tool_use: {name}]**\n```json\n{_clip(inp_s)}\n```")
        elif bt == "tool_result":
            c = b.get("content", "")
            if isinstance(c, list):
                parts = []
                for p in c:
                    if isinstance(p, dict):
                        parts.append(p.get("text", "") if p.get("type") == "text" else json.dumps(p))
                    else:
                        parts.append(str(p))
                c = "\n".join(parts)
            err = " (error)" if b.get("is_error") else ""
            out.append(f"**[tool_result{err}]**\n```\n{_clip(c)}\n```")
        else:
            out.append(_clip(json.dumps(b)))


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_transcript.py <input.jsonl> <output.md>")
    src, dst = sys.argv[1], sys.argv[2]
    lines_out = [f"# Claude Code transcript\n\n_Rendered from `{src.split('/')[-1]}`_\n"]
    with open(src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            ts = d.get("timestamp", "")
            if t == "user":
                msg = d.get("message") or {}
                lines_out.append(f"\n---\n\n## 🧑 User  <sub>{ts}</sub>\n")
                _render_blocks(msg.get("content", ""), lines_out)
            elif t == "assistant":
                msg = d.get("message") or {}
                model = d.get("requestedModel") or (msg.get("model") if isinstance(msg, dict) else "") or ""
                lines_out.append(f"\n---\n\n## 🤖 Assistant <sub>{model} · {ts}</sub>\n")
                _render_blocks(msg.get("content", ""), lines_out)
            elif t == "system":
                sub = d.get("subtype", "")
                content = d.get("content", "")
                if isinstance(content, str) and content.strip():
                    lines_out.append(f"\n> _[system/{sub}]_ {_clip(content, 500)}\n")
            # else: skip bookkeeping records
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out) + "\n")
    print(f"  rendered -> {dst}")


if __name__ == "__main__":
    main()
