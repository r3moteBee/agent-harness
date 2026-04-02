#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# bump_version.sh  —  Increment the date-based version and update all files.
#
# Format: yyyy-mm-dd-## (two-digit sequence resets to 01 each day)
#
# Usage:
#   ./bump_version.sh           # auto-increment
#   ./bump_version.sh --dry-run # show what the new version would be
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$DIR/VERSION"
DRY_RUN=false

for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
done

# ── Read current version ──────────────────────────────────────────────────────
if [[ -f "$VERSION_FILE" ]]; then
  CURRENT=$(cat "$VERSION_FILE" | tr -d '[:space:]')
else
  CURRENT="0000-00-00-00"
fi

CURRENT_DATE=$(echo "$CURRENT" | cut -d'-' -f1-3)
CURRENT_SEQ=$(echo  "$CURRENT" | cut -d'-' -f4)
TODAY=$(date +%Y-%m-%d)

# ── Calculate next sequence number ───────────────────────────────────────────
if [[ "$CURRENT_DATE" == "$TODAY" ]]; then
  SEQ=$(printf "%02d" $(( 10#$CURRENT_SEQ + 1 )) )
else
  SEQ="01"
fi

NEW_VERSION="${TODAY}-${SEQ}"

echo "Current version : $CURRENT"
echo "New version     : $NEW_VERSION"

[[ "$DRY_RUN" == true ]] && echo "(dry run — no files changed)" && exit 0

# ── Update VERSION file ───────────────────────────────────────────────────────
echo "$NEW_VERSION" > "$VERSION_FILE"

# ── Update backend/main.py (two occurrences) ─────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/version=\"[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}\"/version=\"${NEW_VERSION}\"/g" \
    "$DIR/backend/main.py"
  sed -i '' "s/\"version\": \"[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}\"/\"version\": \"${NEW_VERSION}\"/g" \
    "$DIR/backend/main.py"
else
  sed -i "s/version=\"[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}\"/version=\"${NEW_VERSION}\"/g" \
    "$DIR/backend/main.py"
  sed -i "s/\"version\": \"[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}\"/\"version\": \"${NEW_VERSION}\"/g" \
    "$DIR/backend/main.py"
fi

# ── Update frontend Layout.jsx ────────────────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}</>${NEW_VERSION}</g" \
    "$DIR/frontend/src/components/Layout.jsx"
else
  sed -i "s/>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}</>${NEW_VERSION}</g" \
    "$DIR/frontend/src/components/Layout.jsx"
fi

# ── Update frontend LoginPage.jsx ─────────────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}</>${NEW_VERSION}</g" \
    "$DIR/frontend/src/pages/LoginPage.jsx"
else
  sed -i "s/>[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-[0-9]\{2\}</>${NEW_VERSION}</g" \
    "$DIR/frontend/src/pages/LoginPage.jsx"
fi

# ── Update frontend package.json (dot-separated date, no sequence) ────────────
PKG_VER="${TODAY//-/.}"
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/\"version\": \"[0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}\"/\"version\": \"${PKG_VER}\"/g" \
    "$DIR/frontend/package.json"
else
  sed -i "s/\"version\": \"[0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}\"/\"version\": \"${PKG_VER}\"/g" \
    "$DIR/frontend/package.json"
fi

echo ""
echo "✓ Version bumped to $NEW_VERSION in:"
echo "  VERSION"
echo "  backend/main.py"
echo "  frontend/src/components/Layout.jsx"
echo "  frontend/src/pages/LoginPage.jsx"
echo "  frontend/package.json  (as ${PKG_VER})"
