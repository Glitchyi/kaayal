#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_NAME="${1:-kaayal}"
if [[ "$TARGET_NAME" == -* || "$TARGET_NAME" == */* || "$TARGET_NAME" == .* || -z "$TARGET_NAME" ]]; then
  echo 'Usage: bash scripts/bootstrap.sh <simple-directory-name>' >&2
  exit 2
fi
if ! command -v specify >/dev/null 2>&1; then
  echo 'Specify CLI missing. Install: uv tool install specify-cli' >&2
  exit 1
fi
if [[ -e "$ROOT/$TARGET_NAME" ]]; then
  echo "Refusing to overwrite $ROOT/$TARGET_NAME" >&2
  exit 1
fi
cd "$ROOT"
specify init "$TARGET_NAME" --integration devin --script sh --non-interactive --ignore-agent-tools
TARGET="$ROOT/$TARGET_NAME"
cp -a "$ROOT/starter/." "$TARGET/"
echo "Kaayal ready in $TARGET"
echo "Review first: $TARGET/devin-prompts/00-review.md"
echo "Then: cd $TARGET && devin"
