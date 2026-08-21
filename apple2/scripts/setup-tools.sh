#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="$ROOT_DIR/.tools"
VENV_DIR="$TOOLS_DIR/apple2-venv"
APPLECOMMANDER_DIR="$TOOLS_DIR/applecommander"
IZAPPLE2_DIR="$TOOLS_DIR/izapple2"
IZAPPLE2_BIN="$IZAPPLE2_DIR/izapple2"
IZAPPLE2_VERSION="2.4.0"
IZAPPLE2_ARCHIVE_SHA256="d3c0eba5021bbe1b1ff3ae4b98749169b41db6bc7cf14835b6a249fdf15e190d"
IZAPPLE2_URL="https://github.com/ivanizag/izapple2/releases/download/v${IZAPPLE2_VERSION}/izapple2-macos-universal.tar.gz"
PRODOS_DIR="$TOOLS_DIR/apple2-prodos"
PRODOS_TEMPLATE="$PRODOS_DIR/ProDOS_2_4_3.po"
PRODOS_TEMPLATE_SHA256="398d333cb2ab92df9f8bb2cf64b946f2567116910eb8359cf4bdee5d4194f0fa"
PRODOS_TEMPLATE_URL="https://raw.githubusercontent.com/ivanizag/izapple2/v${IZAPPLE2_VERSION}/resources/ProDOS_2_4_3.po"

if ! command -v cl65 >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install cc65
  fi
fi

if ! command -v exomizer >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install exomizer
  fi
fi

if ! command -v exomizer >/dev/null 2>&1; then
  echo "Exomizer 3.1.2 was not found on PATH and could not be installed." >&2
  exit 1
fi

if ! exomizer -v 2>&1 | grep -q "Exomizer v3.1.2"; then
  echo "SIXIES requires Exomizer 3.1.2." >&2
  exit 1
fi

if ! command -v cl65 >/dev/null 2>&1; then
  echo "cc65 was not found on PATH and could not be installed." >&2
  exit 1
fi

mkdir -p "$TOOLS_DIR" "$APPLECOMMANDER_DIR" "$IZAPPLE2_DIR" "$PRODOS_DIR"

if [[ ! -x /opt/homebrew/opt/openjdk/bin/java ]]; then
  if command -v brew >/dev/null 2>&1; then
    if ! brew list --versions openjdk >/dev/null 2>&1; then
      brew install openjdk
    fi
  fi
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install Pillow >/dev/null

if ! ls "$APPLECOMMANDER_DIR"/AppleCommander-ac-*.jar >/dev/null 2>&1; then
  release_json="$("$VENV_DIR/bin/python" - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("https://api.github.com/repos/AppleCommander/AppleCommander/releases/latest") as resp:
    data = json.load(resp)

assets = data.get("assets", [])
preferred = None
for asset in assets:
    name = asset.get("name", "")
    if name.endswith(".jar") and name.startswith("AppleCommander-ac-"):
        preferred = asset["browser_download_url"]
        break

print(preferred or "")
PY
)"
  if [[ -z "$release_json" ]]; then
    echo "Could not determine a downloadable AppleCommander jar." >&2
    exit 1
  fi
  curl -fL "$release_json" -o "$APPLECOMMANDER_DIR/$(basename "$release_json")"
fi

installed_izapple2_version=""
if [[ -f "$IZAPPLE2_DIR/VERSION" ]]; then
  installed_izapple2_version="$(<"$IZAPPLE2_DIR/VERSION")"
fi

if [[ ! -x "$IZAPPLE2_BIN" || "$installed_izapple2_version" != "$IZAPPLE2_VERSION" ]]; then
  download_dir="$(mktemp -d)"
  trap 'rm -rf "$download_dir"' EXIT
  archive="$download_dir/izapple2.tar.gz"

  curl -fL "$IZAPPLE2_URL" -o "$archive"
  actual_sha256="$(shasum -a 256 "$archive" | awk '{print $1}')"
  if [[ "$actual_sha256" != "$IZAPPLE2_ARCHIVE_SHA256" ]]; then
    echo "izapple2 archive checksum mismatch." >&2
    exit 1
  fi

  tar -xzf "$archive" -C "$download_dir" izapple2
  install -m 755 "$download_dir/izapple2" "$IZAPPLE2_BIN"
  printf '%s\n' "$IZAPPLE2_VERSION" > "$IZAPPLE2_DIR/VERSION"
fi

prodos_sha256=""
if [[ -f "$PRODOS_TEMPLATE" ]]; then
  prodos_sha256="$(shasum -a 256 "$PRODOS_TEMPLATE" | awk '{print $1}')"
fi
if [[ "$prodos_sha256" != "$PRODOS_TEMPLATE_SHA256" ]]; then
  curl -fL "$PRODOS_TEMPLATE_URL" -o "$PRODOS_TEMPLATE"
  prodos_sha256="$(shasum -a 256 "$PRODOS_TEMPLATE" | awk '{print $1}')"
  if [[ "$prodos_sha256" != "$PRODOS_TEMPLATE_SHA256" ]]; then
    echo "ProDOS template checksum mismatch." >&2
    exit 1
  fi
fi

echo "Apple II tools ready:"
echo "  cc65: $(command -v cl65)"
echo "  exomizer: $(command -v exomizer) (v3.1.2)"
echo "  python: $VENV_DIR/bin/python"
echo "  pillow: installed in $VENV_DIR"
echo "  applecommander: $(ls "$APPLECOMMANDER_DIR"/AppleCommander-ac-*.jar | head -n 1)"
echo "  izapple2: $IZAPPLE2_BIN (v$IZAPPLE2_VERSION)"
echo "  prodos: $PRODOS_TEMPLATE"
if [[ -x /opt/homebrew/opt/openjdk/bin/java ]]; then
  echo "  java: /opt/homebrew/opt/openjdk/bin/java"
fi
