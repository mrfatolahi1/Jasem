#!/usr/bin/env bash
#
# Publish the Markdown pages in this folder to the jasem GitHub wiki.
#
# The GitHub wiki is a separate git repo (jasem.wiki.git). This script clones it
# into a temp directory, copies every *.md page from this folder into it, then
# commits and pushes.
#
# First-time setup: the wiki repo only exists once the wiki has at least one
# page. If the clone below fails, open the repo's Wiki tab on GitHub, click
# "Create the first page", save, and re-run this script. See README.md.
#
# Usage:  ./publish.sh
#
set -euo pipefail

# The wiki repo for this project. Override with WIKI_REMOTE if you forked it.
WIKI_REMOTE="${WIKI_REMOTE:-https://github.com/mrfatolahi1/jasem.wiki.git}"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "→ Cloning wiki: $WIKI_REMOTE"
if ! git clone --quiet "$WIKI_REMOTE" "$WORK_DIR/wiki"; then
  echo
  echo "Clone failed. The wiki may not be initialised yet."
  echo "On GitHub: open the repo's Wiki tab, click 'Create the first page',"
  echo "save it, then re-run this script. (See README.md.)"
  exit 1
fi

echo "→ Copying pages"
# Copy every page except this folder's own README (which documents publishing,
# not a wiki page) and the script itself.
for f in "$SRC_DIR"/*.md; do
  name="$(basename "$f")"
  [ "$name" = "README.md" ] && continue
  cp "$f" "$WORK_DIR/wiki/$name"
done

cd "$WORK_DIR/wiki"
if git diff --quiet && git diff --cached --quiet; then
  echo "→ No changes — wiki already up to date."
  exit 0
fi

git add .
git commit --quiet -m "Update wiki"
echo "→ Pushing"
git push --quiet
echo "✓ Published: ${WIKI_REMOTE%.wiki.git}/wiki"
