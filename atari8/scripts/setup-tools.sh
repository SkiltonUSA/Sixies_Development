#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATARI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$ATARI_DIR/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/.tools/atari8"
BIN_DIR="$TOOLS_DIR/bin"
VENV_DIR="$TOOLS_DIR/venv"
ATARIOSIO_DIR="$TOOLS_DIR/AtariSIO"
SAPRTOOLS_DIR="$TOOLS_DIR/saprtools"
ROM_DIR="$TOOLS_DIR/roms"
ATARIOSIO_COMMIT="bbccb15265259a1408f36d7ed9b89bb08bbb711d"
SAPRTOOLS_COMMIT="92e51fc9187ad94f8d9e3e9531ef32948c31bf39"
ROM_SHA256="a77050b2d81db2d11eaa3dbafd8ec2531b478abcc3bcc4b0d846b634e885edb1"
CHECK_ONLY=0

if [[ "${1:-}" == "--check-only" ]]; then
    CHECK_ONLY=1
fi

need_commands=(ca65 ld65 exomizer atari800 python3 make git curl shasum)
missing=()
for command_name in "${need_commands[@]}"; do
    command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done

if [[ ${#missing[@]} -ne 0 && "$CHECK_ONLY" -eq 0 && "$(uname -s)" == "Darwin" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew is required to install: ${missing[*]}" >&2
        exit 1
    fi
    brew install cc65 exomizer atari800 python
    missing=()
    for command_name in "${need_commands[@]}"; do
        command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
    done
fi

if [[ ${#missing[@]} -ne 0 ]]; then
    echo "Missing Atari development commands: ${missing[*]}" >&2
    echo "On macOS run: brew install cc65 exomizer atari800 python" >&2
    exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "Atari host commands are available. Run make -C atari8 setup-tools for local assets and disk tools."
    exit 0
fi

mkdir -p "$BIN_DIR" "$ROM_DIR"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --quiet "Pillow==11.3.0" "py65==1.2.0"

if [[ ! -d "$ATARIOSIO_DIR/.git" ]]; then
    git clone --filter=blob:none https://github.com/HiassofT/AtariSIO.git "$ATARIOSIO_DIR"
fi
git -C "$ATARIOSIO_DIR" fetch --quiet origin "$ATARIOSIO_COMMIT"
git -C "$ATARIOSIO_DIR" checkout --quiet --detach "$ATARIOSIO_COMMIT"
make -C "$ATARIOSIO_DIR/tools" -f Makefile.posix >/dev/null
for tool_name in adir ataricom dir2atr; do
    cp "$ATARIOSIO_DIR/tools/$tool_name" "$BIN_DIR/$tool_name"
done

if [[ ! -d "$SAPRTOOLS_DIR/.git" ]]; then
    git clone --recurse-submodules https://github.com/ivop/saprtools.git "$SAPRTOOLS_DIR"
fi
git -C "$SAPRTOOLS_DIR" fetch --quiet origin "$SAPRTOOLS_COMMIT"
git -C "$SAPRTOOLS_DIR" checkout --quiet --detach "$SAPRTOOLS_COMMIT"
git -C "$SAPRTOOLS_DIR" submodule update --init --recursive --quiet
make -C "$SAPRTOOLS_DIR/sid2sapr" >/dev/null
make -C "$SAPRTOOLS_DIR/lzss-sap" >/dev/null

ROM_FILE="$ROM_DIR/ATARIXL.ROM"
if [[ ! -f "$ROM_FILE" ]] || ! printf '%s  %s\n' "$ROM_SHA256" "$ROM_FILE" | shasum -a 256 -c - >/dev/null 2>&1; then
    curl -L --fail --silent --show-error \
        "https://raw.githubusercontent.com/Abdess/retrobios/main/bios/Atari/400-800/ATARIXL.ROM" \
        -o "$ROM_FILE"
fi
printf '%s  %s\n' "$ROM_SHA256" "$ROM_FILE" | shasum -a 256 -c -

echo "Atari 8-bit development environment is ready."
echo "  assembler: $(ca65 --version 2>&1 | head -n 1)"
echo "  linker:    $(ld65 --version 2>&1 | head -n 1)"
echo "  emulator:  $(atari800 -version 2>&1 | head -n 1)"
echo "  cruncher:  $(exomizer -v 2>&1 | grep -m1 Exomizer)"
echo "  disk tool: $BIN_DIR/dir2atr"
echo "  SID tool:  $SAPRTOOLS_DIR/sid2sapr/sid2sapr"
echo "  SAPR LZSS: $SAPRTOOLS_DIR/lzss-sap/bin/lzss"
echo "  XL/XE ROM: $ROM_FILE"
