#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/build"

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME assembler is required. Install it with: brew install acme" >&2
  exit 1
fi

cd "$ROOT_DIR"
acme src/main.a

echo "Built build/shanghai.prg"
