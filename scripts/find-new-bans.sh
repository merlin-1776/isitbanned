#!/bin/bash
# find-new-bans.sh — Search for new book ban news and add missing books
# Run manually or via cron. Outputs JSON for the agent to process.
#
# Usage: ./scripts/find-new-bans.sh
# The actual intelligence lives in the agent prompt below.
# This script is a wrapper that the OpenClaw cron system calls.

REPO_DIR="/tmp/isitbanned"
CONTENT_DIR="$REPO_DIR/src/content/books"

echo "=== Book Ban Monitor ==="
echo "Date: $(date)"
echo "Existing books:"
ls "$CONTENT_DIR"/*.md 2>/dev/null | while read f; do
  basename "$f" .md
done
echo "=== End existing books ==="
