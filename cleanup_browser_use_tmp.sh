#!/usr/bin/env bash
# cleanup_browser_use_tmp.sh

TMPDIR="/tmp"

# 삭제 대상 패턴
PATTERNS=(
  "browser-use-downloads-*"
  "browser-use-user-data-dir-*"
  "browser_use_agent_*"
  "xvfb-run.*"
)

if [[ "$1" == "-f" ]]; then
  echo "🧹 Deleting browser-use temp files from $TMPDIR ..."
  find "$TMPDIR" -maxdepth 1 -user "$USER" \
    \( -name 'browser-use-downloads-*' -o -name 'browser-use-user-data-dir-*' -o -name 'browser_use_agent_*' -o -name 'xvfb-run.*' \) \
    -exec rm -rf {} +
  echo "✅ Cleanup complete."
else
  echo "💡 Dry run (use -f to actually delete):"
  find "$TMPDIR" -maxdepth 1 -user "$USER" \
    \( -name 'browser-use-downloads-*' -o -name 'browser-use-user-data-dir-*' -o -name 'browser_use_agent_*' -o -name 'xvfb-run.*' \)
fi

