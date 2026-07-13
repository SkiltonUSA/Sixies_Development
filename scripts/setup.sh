#!/usr/bin/env bash

set -euo pipefail

if command -v brew >/dev/null 2>&1; then
  brew install acme exomizer
else
  echo "Install ACME and optionally exomizer manually, then run ./scripts/build.sh." >&2
fi

./scripts/ensure_sparkle2.sh >/dev/null
echo "Sparkle2 prepared under .context/Sparkle2"
