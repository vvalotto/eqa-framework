#!/bin/bash

PROJECT_DIR="$CLAUDE_PROJECT_DIR"
MEMORY_DIR="$HOME/.claude/projects/-Users-victor-PycharmProjects-eqa-framework/memory"

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
REASON=$(echo "$INPUT" | jq -r '.reason // "other"')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HUMAN_TIMESTAMP=$(date +"%Y-%m-%d %H:%M")

cd "$PROJECT_DIR" 2>/dev/null || exit 0
GIT_STATUS=$(git status --short 2>/dev/null || echo 'N/A')
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo 'N/A')

LAST_TIMESTAMP=""
if [ -f "$MEMORY_DIR/session-metadata.json" ]; then
  LAST_TIMESTAMP=$(jq -r '.timestamp // ""' "$MEMORY_DIR/session-metadata.json" 2>/dev/null)
fi

COMMITS=""
if [ -n "$LAST_TIMESTAMP" ]; then
  COMMITS=$(git log --since="$LAST_TIMESTAMP" --pretty=format:"- %h %s" 2>/dev/null)
fi

if [ -z "$COMMITS" ]; then
  COMMITS=$(git log --since="24 hours ago" --pretty=format:"- %h %s" -20 2>/dev/null)
fi

mkdir -p "$MEMORY_DIR"
jq -n \
  --arg session_id "$SESSION_ID" \
  --arg reason "$REASON" \
  --arg transcript "$TRANSCRIPT" \
  --arg timestamp "$TIMESTAMP" \
  --arg git_status "$GIT_STATUS" \
  --arg git_branch "$GIT_BRANCH" \
  '{
    session_id: $session_id,
    exit_reason: $reason,
    transcript_path: $transcript,
    timestamp: $timestamp,
    git_status: $git_status,
    git_branch: $git_branch
  }' > "$MEMORY_DIR/session-metadata.json" 2>/dev/null

if [ -n "$COMMITS" ]; then
  cat >> "$MEMORY_DIR/session-current.md" <<EOF

---

## 📝 Sesión Finalizada: $HUMAN_TIMESTAMP

**Branch:** $GIT_BRANCH
**Exit Reason:** $REASON

### Commits en esta sesión:
$COMMITS

**Próxima sesión:** Ejecutar \`/resume\` para restaurar contexto completo.

EOF
fi

touch "$MEMORY_DIR/session-needs-summary.flag"

echo "✅ Session saved with $(echo "$COMMITS" | wc -l | tr -d ' ') commits tracked." >&2
exit 0
