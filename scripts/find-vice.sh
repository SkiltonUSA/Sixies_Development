#!/usr/bin/env bash

set -euo pipefail

for base_dir in "/Applications" "$HOME/Applications"; do
  for candidate in \
    "$base_dir/x64sc.app/Contents/MacOS/x64sc" \
    "$base_dir/x64.app/Contents/MacOS/x64" \
    "$base_dir/vice-arm64-sdl2-3.9/bin/x64sc" \
    "$base_dir/vice-arm64-sdl2-3.9/bin/x64" \
    "$base_dir/VICE.app/Contents/Resources/bin/x64sc" \
    "$base_dir/VICE.app/Contents/Resources/bin/x64" \
    "$base_dir/VICE.app/Contents/MacOS/x64sc" \
    "$base_dir/VICE.app/Contents/MacOS/x64" \
    "$base_dir/vice.app/Contents/MacOS/x64sc" \
    "$base_dir/vice.app/Contents/MacOS/x64"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      exit 0
    fi
  done
done

for base_dir in "/Applications" "$HOME/Applications"; do
  if [[ -d "$base_dir" ]]; then
    match="$(find "$base_dir" -maxdepth 5 -type f \( -name x64sc -o -name x64 \) 2>/dev/null | head -n 1 || true)"
    if [[ -n "$match" ]]; then
      printf '%s\n' "$match"
      exit 0
    fi
  fi
done

for candidate in x64sc x64; do
  if command -v "$candidate" >/dev/null 2>&1; then
    command -v "$candidate"
    exit 0
  fi
done

echo "Unable to find a VICE C64 binary. Install VICE for macOS or add x64sc/x64 to PATH." >&2
exit 1
