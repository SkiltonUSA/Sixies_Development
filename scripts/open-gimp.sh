#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -gt 1 ]]; then
  echo "usage: make gimp [GIMP_ASSET=path/to/source-master]" >&2
  exit 2
fi

if [[ "$#" -eq 1 && ! -f "$1" ]]; then
  printf 'GIMP source asset not found: %s\n' "$1" >&2
  exit 1
fi

if [[ -d /Applications/GIMP.app ]]; then
  open -a GIMP "$@"
  exit 0
fi

if command -v gimp >/dev/null 2>&1; then
  gimp "$@"
  exit 0
fi

echo "GIMP was not found. Install GIMP 3 and rerun make gimp." >&2
exit 1
