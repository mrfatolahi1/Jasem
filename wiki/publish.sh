#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wiki.md"
REMOTE="${WIKI_REMOTE:-https://github.com/mrfatolahi1/jasem.wiki.git}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git clone --quiet "$REMOTE" "$WORK"
cp "$SRC" "$WORK/Home.md"
cd "$WORK"
git add Home.md
if git diff --cached --quiet; then
  echo "wiki already up to date"
  exit 0
fi
git commit --quiet -m "Update wiki"
git push --quiet
echo "wiki updated"
