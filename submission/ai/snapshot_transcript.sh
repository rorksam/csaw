#!/usr/bin/env bash
# Snapshot the live Claude Code transcript for THIS project into the project
# folder (which is mounted from the Mac and survives container teardown), so the
# required AI log can never be lost and is captured inside the submission.
#
# Usage: submission/ai/snapshot_transcript.sh
# Safe to run repeatedly (idempotent overwrite). Can be wired to a Stop hook.
set -euo pipefail

PROJ_DIR="/home/researcher/.claude-state/projects/-home-researcher-work-csaw"
OUT_DIR="/home/researcher/work/csaw/submission/ai"
mkdir -p "$OUT_DIR"

RENDER="$OUT_DIR/render_transcript.py"

shopt -s nullglob
copied=0
for tx in "$PROJ_DIR"/*.jsonl; do
    sid="$(basename "$tx" .jsonl)"
    cp -f "$tx" "$OUT_DIR/transcript_${sid}.jsonl"
    # Also emit a human-readable Markdown rendering for the ai/ deliverable.
    if [ -f "$RENDER" ]; then
        python "$RENDER" "$OUT_DIR/transcript_${sid}.jsonl" \
            "$OUT_DIR/transcript_${sid}.md" || true
    fi
    copied=$((copied+1))
done
shopt -u nullglob

echo "Snapshotted $copied transcript(s) to $OUT_DIR at $(date -u +%FT%TZ)"
ls -la "$OUT_DIR"/transcript_*.jsonl "$OUT_DIR"/transcript_*.md 2>/dev/null || echo "  (no transcripts found yet)"
