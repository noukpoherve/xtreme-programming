#!/usr/bin/env bash
# Validate Conventional Commits format (commit-msg hook).
# Usage: validate-commit-msg.sh <path-to-commit-msg-file>
set -euo pipefail

MSG_FILE="${1:-}"
if [[ -z "$MSG_FILE" || ! -f "$MSG_FILE" ]]; then
  echo "commit-msg hook: missing commit message file" >&2
  exit 1
fi

# First non-empty, non-comment line is the subject.
SUBJECT="$(grep -v '^[[:space:]]*$' "$MSG_FILE" | grep -v '^#' | head -n 1 || true)"

if [[ -z "$SUBJECT" ]]; then
  echo "commit-msg hook: empty commit message" >&2
  exit 1
fi

# Allow automated merge commits from Git.
if [[ "$SUBJECT" =~ ^Merge ]]; then
  exit 0
fi

PATTERN='^(feat|fix|chore|docs|ci|test|refactor|perf|build|style|revert)(\([a-z0-9._-]+\))?!?: .+'

if [[ ! "$SUBJECT" =~ $PATTERN ]]; then
  echo "❌ Invalid commit message:" >&2
  echo "   $SUBJECT" >&2
  echo "" >&2
  echo "Expected Conventional Commits, e.g.:" >&2
  echo "  feat(iot): add ingestion status endpoint" >&2
  echo "  fix: handle null sensor id" >&2
  echo "  docs: update changelog" >&2
  echo "" >&2
  echo "Allowed types: feat, fix, chore, docs, ci, test, refactor, perf, build, style, revert" >&2
  exit 1
fi

exit 0
