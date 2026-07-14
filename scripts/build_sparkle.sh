#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/build.sh"

SPARKLE_DIR="$("$ROOT_DIR/scripts/ensure_sparkle2.sh")"
SPARKLE_EXE="$SPARKLE_DIR/bin/Sparkle2.exe"
SLS_PATH="$ROOT_DIR/build/StarwarsScrollerDemo.sls"
SPARKLE_TIMEOUT_SECONDS="${SPARKLE_TIMEOUT_SECONDS:-90}"
HEADLESS_EXE="$ROOT_DIR/.context/sparkle_headless/SparkleHeadless.exe"

rm -f "$ROOT_DIR/build/StarwarsScrollerDemo-sparkle.d64"

find_mono_visualbasic() {
  find \
    "$SPARKLE_DIR/bin" \
    "$ROOT_DIR/.context/mono-mdk-expanded" \
    "/Library/Frameworks/Mono.framework" \
    -path "*/gac/Microsoft.VisualBasic/10.0.0.0__b03f5f7f11d50a3a/Microsoft.VisualBasic.dll" \
    -print 2>/dev/null | head -n 1
}

ensure_mono_visualbasic() {
  if [[ -f "$SPARKLE_DIR/bin/Microsoft.VisualBasic.dll" ]]; then
    return 0
  fi

  local dll
  dll="$(find_mono_visualbasic || true)"

  if [[ -z "$dll" && -d "$ROOT_DIR/.context" && -x "$(command -v brew || true)" ]]; then
    brew fetch --cask mono-mdk >/dev/null || true
    local pkg
    pkg="$(find "$HOME/Library/Caches/Homebrew/downloads" -iname "*MonoFramework-MDK*.pkg" -print 2>/dev/null | head -n 1)"
    if [[ -n "$pkg" ]]; then
      rm -rf "$ROOT_DIR/.context/mono-mdk-expanded"
      pkgutil --expand-full "$pkg" "$ROOT_DIR/.context/mono-mdk-expanded" >/dev/null
      dll="$(find_mono_visualbasic)"
    fi
  fi

  if [[ -n "$dll" ]]; then
    cp "$dll" "$SPARKLE_DIR/bin/Microsoft.VisualBasic.dll"
    return 0
  fi

  echo "Mono is missing the Microsoft.VisualBasic runtime assembly required by Sparkle2." >&2
  echo "Install the Mono MDK package, or run the generated build/StarwarsScrollerDemo.sls with Sparkle2 on Windows." >&2
  return 1
}

build_mono_sls() {
  mkdir -p "$ROOT_DIR/.context/sparkle_headless"
  cat > "$ROOT_DIR/.context/sparkle_headless/StarwarsScrollerDemo-mono.sls" <<EOF
[Sparkle Loader Script]
Path:	$ROOT_DIR/build/StarwarsScrollerDemo-sparkle.d64
Header:	starwars demo
ID:	c64u
Name:	Starwars Demo
Start:	080d
File:	$ROOT_DIR/build/StarwarsScrollerDemo-sparkle-part.prg
EOF
  echo "$ROOT_DIR/.context/sparkle_headless/StarwarsScrollerDemo-mono.sls"
}

run_sparkle() {
  "$@" &
  local pid=$!
  local elapsed=0

  while kill -0 "$pid" 2>/dev/null; do
    if (( elapsed >= SPARKLE_TIMEOUT_SECONDS )); then
      echo "Sparkle2 timed out after ${SPARKLE_TIMEOUT_SECONDS}s." >&2
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  wait "$pid"
}

sparkle_status=0

if command -v mono >/dev/null 2>&1; then
  ensure_mono_visualbasic
  mkdir -p "$(dirname "$HEADLESS_EXE")"
  mcs -out:"$HEADLESS_EXE" "$ROOT_DIR/scripts/sparkle_headless.cs"
  run_sparkle mono "$HEADLESS_EXE" "$SPARKLE_EXE" "$(build_mono_sls)" || sparkle_status=$?
elif command -v wine >/dev/null 2>&1; then
  if command -v winepath >/dev/null 2>&1; then
    SLS_PATH_WIN="$(MVK_CONFIG_LOG_LEVEL=0 WINEDEBUG=-all winepath -w "$SLS_PATH")"
    run_sparkle env MVK_CONFIG_LOG_LEVEL=0 WINEDEBUG=-all wine "$SPARKLE_EXE" "$SLS_PATH_WIN" || sparkle_status=$?
  else
    run_sparkle env MVK_CONFIG_LOG_LEVEL=0 WINEDEBUG=-all wine "$SPARKLE_EXE" "$SLS_PATH" || sparkle_status=$?
  fi
else
  echo "Sparkle2 script prepared at build/StarwarsScrollerDemo.sls"
  echo "Skipping Sparkle2 disk build: install mono or wine, or run Sparkle2.exe on Windows with that .sls file."
  exit 0
fi

if [[ -f "$ROOT_DIR/build/StarwarsScrollerDemo-sparkle.d64" ]]; then
  echo "Built build/StarwarsScrollerDemo-sparkle.d64"
else
  if [[ "$sparkle_status" -eq 124 ]]; then
    echo "Sparkle2 did not finish before the timeout and build/StarwarsScrollerDemo-sparkle.d64 was not created." >&2
  else
    echo "Sparkle2 exited with status $sparkle_status but build/StarwarsScrollerDemo-sparkle.d64 was not created." >&2
  fi
  echo "If this used Wine on macOS, run the generated build/StarwarsScrollerDemo.sls with Sparkle2 on Windows or install Mono and rerun make sparkle." >&2
  exit 1
fi
