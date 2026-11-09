#!/usr/bin/env bash
# Ping the Anthropic API to confirm $ANTHROPIC_API_KEY works for the pipeline.
# RUN THIS IN YOUR ENVIRONMENT (where ANTHROPIC_API_KEY is set) — not inside the
# container session, which cannot see the key. Mirrors the OpenAI ping already done.
#
#   bash ping_anthropic.sh
#
# Never prints the key value; only a safe prefix/length.
set -u

MODEL="${ANTHROPIC_MODEL:-claude-opus-4-8}"
VERSION="2023-06-01"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ANTHROPIC_API_KEY is NOT set in this shell -> cannot ping Anthropic." >&2
  echo "Set it (e.g. in ~/.config/llm4eda/env) and run again." >&2
  exit 1
fi
echo "ANTHROPIC_API_KEY present: prefix=${ANTHROPIC_API_KEY:0:7}... len=${#ANTHROPIC_API_KEY}"
echo "Model under test: ${MODEL}"
echo

echo "=== 1) Auth ping: GET /v1/models (free, no tokens) ==="
code=$(curl -sS -o /tmp/anthropic_models.json -w "%{http_code}" https://api.anthropic.com/v1/models \
  -H "x-api-key: ${ANTHROPIC_API_KEY}" \
  -H "anthropic-version: ${VERSION}")
echo "HTTP ${code}"
if [ "${code}" = "200" ]; then
  python3 -c "import json;d=json.load(open('/tmp/anthropic_models.json'));ids=[m['id'] for m in d.get('data',[])];print('models:',len(ids));[print(' ',i) for i in ids[:8]];print('  '+'-'*10);print('${MODEL} present:', '${MODEL}' in ids)" 2>/dev/null \
    || head -c 500 /tmp/anthropic_models.json
else
  echo "Auth failed — body:"; head -c 500 /tmp/anthropic_models.json; echo
  exit 1
fi
echo

echo "=== 2) Generation ping: POST /v1/messages (tiny, ~5 tokens) ==="
code=$(curl -sS -o /tmp/anthropic_msg.json -w "%{http_code}" https://api.anthropic.com/v1/messages \
  -H "x-api-key: ${ANTHROPIC_API_KEY}" \
  -H "anthropic-version: ${VERSION}" \
  -H "content-type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"max_tokens\":5,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly the word: PONG\"}]}")
echo "HTTP ${code}"
if [ "${code}" = "200" ]; then
  python3 -c "import json;d=json.load(open('/tmp/anthropic_msg.json'));print('reply:',repr(''.join(b.get('text','') for b in d.get('content',[]))));print('model:',d.get('model'));print('usage:',d.get('usage'));print('stop_reason:',d.get('stop_reason'))" 2>/dev/null \
    || head -c 500 /tmp/anthropic_msg.json
  echo; echo "RESULT: Anthropic key works as expected."
else
  echo "Generation failed — body:"; head -c 500 /tmp/anthropic_msg.json; echo
  exit 1
fi
