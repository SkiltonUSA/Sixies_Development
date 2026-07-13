#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPARKLE_DIR="${SPARKLE2_DIR:-$ROOT_DIR/.context/Sparkle2}"
SPARKLE_REPO="${SPARKLE2_REPO:-https://github.com/SkiltonUSA/Sparkle2.git}"

if [[ -x "$SPARKLE_DIR/bin/Sparkle2.exe" || -f "$SPARKLE_DIR/bin/Sparkle2.exe" ]]; then
  echo "$SPARKLE_DIR"
  exit 0
fi

if [[ -d "$SPARKLE_DIR/.git" ]]; then
  git -C "$SPARKLE_DIR" pull --ff-only >/dev/null
else
  mkdir -p "$(dirname "$SPARKLE_DIR")"
  git clone --depth 1 "$SPARKLE_REPO" "$SPARKLE_DIR" >/dev/null
fi

echo "$SPARKLE_DIR"

