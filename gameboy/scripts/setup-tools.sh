#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAMEBOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$GAMEBOY_DIR/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/.tools/gameboy"
DOWNLOAD_DIR="$TOOLS_DIR/downloads"

GBDK_VERSION="4.5.0"
HUGETRACKER_VERSION="1.0.11"
HUGETRACKER_SHA256="259a694fd93ae5f6c430e13ca7fcca0c86c83b7b2bfd50c38394cbdbd5f8a5d0"

host_os="$(uname -s)"
host_arch="$(uname -m)"

case "$host_os:$host_arch" in
    Darwin:arm64)
        gbdk_archive="gbdk-macos-arm64.tar.gz"
        gbdk_sha256="289ee60e46c5a2785a21e35533f84a5131ed4a063b21b0dbdedc9a10af15bf78"
        ;;
    Darwin:x86_64)
        gbdk_archive="gbdk-macos.tar.gz"
        gbdk_sha256="1aa549d12032d8f6509d11923bb28b1a453098f42597feb378e9a42541f8fd89"
        ;;
    Linux:aarch64|Linux:arm64)
        gbdk_archive="gbdk-linux-arm64.tar.gz"
        gbdk_sha256="31eb2235f0fdb60163d0b1e9574a022098d6069cd56606a1daca4478a46e0439"
        ;;
    Linux:x86_64)
        gbdk_archive="gbdk-linux64.tar.gz"
        gbdk_sha256="d7857a5f6d135ee4c249043ca26aad9f2ec8ab5d4106d97720d404114f42605c"
        ;;
    *)
        echo "Unsupported GBDK host: $host_os $host_arch" >&2
        exit 1
        ;;
esac

sha256_file() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

verify_download() {
    local file_path="$1"
    local expected_sha="$2"
    local actual_sha

    actual_sha="$(sha256_file "$file_path")"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
        echo "Checksum mismatch for $file_path" >&2
        echo "Expected: $expected_sha" >&2
        echo "Actual:   $actual_sha" >&2
        exit 1
    fi
}

install_gbdk() {
    local install_dir="$TOOLS_DIR/gbdk-$GBDK_VERSION-$host_os-$host_arch"
    local archive_path="$DOWNLOAD_DIR/$gbdk_archive"
    local staging_dir

    if [[ ! -x "$install_dir/bin/lcc" ]]; then
        if [[ -e "$install_dir" ]]; then
            echo "Incomplete GBDK install found at $install_dir" >&2
            echo "Move it aside and rerun this script." >&2
            exit 1
        fi

        mkdir -p "$DOWNLOAD_DIR"
        if [[ ! -f "$archive_path" ]]; then
            curl --fail --location --retry 3 --show-error \
                "https://github.com/gbdk-2020/gbdk-2020/releases/download/$GBDK_VERSION/$gbdk_archive" \
                --output "$archive_path"
        fi
        verify_download "$archive_path" "$gbdk_sha256"

        staging_dir="$(mktemp -d "$TOOLS_DIR/gbdk-stage.XXXXXX")"
        tar -xzf "$archive_path" -C "$staging_dir"
        mv "$staging_dir/gbdk" "$install_dir"
        rmdir "$staging_dir"
    fi

    ln -sfn "$(basename "$install_dir")" "$TOOLS_DIR/gbdk"
}

install_brew_formula() {
    local formula="$1"
    if ! brew list --versions "$formula" >/dev/null 2>&1; then
        brew install "$formula"
    fi
}

install_brew_cask() {
    local cask="$1"
    if ! brew list --cask --versions "$cask" >/dev/null 2>&1; then
        brew install --cask "$cask"
    fi
}

install_hugetracker() {
    local tracker_dir="$TOOLS_DIR/hUGETracker-$HUGETRACKER_VERSION"
    local archive_path="$DOWNLOAD_DIR/hUGETracker-$HUGETRACKER_VERSION-mac.zip"
    local staging_dir

    if [[ ! -x "$tracker_dir/hUGETracker.app/Contents/MacOS/hUGETracker" ]]; then
        if [[ -e "$tracker_dir" ]]; then
            echo "Incomplete hUGETracker install found at $tracker_dir" >&2
            echo "Move it aside and rerun this script." >&2
            exit 1
        fi

        if [[ ! -f "$archive_path" ]]; then
            curl --fail --location --retry 3 --show-error \
                "https://github.com/SuperDisk/hUGETracker/releases/download/v$HUGETRACKER_VERSION/hUGETracker-$HUGETRACKER_VERSION-mac.zip" \
                --output "$archive_path"
        fi
        verify_download "$archive_path" "$HUGETRACKER_SHA256"

        staging_dir="$(mktemp -d "$TOOLS_DIR/huge-stage.XXXXXX")"
        unzip -q "$archive_path" -d "$staging_dir"
        mv "$staging_dir" "$tracker_dir"
    fi

    ln -sfn "$(basename "$tracker_dir")" "$TOOLS_DIR/hUGETracker"
}

mkdir -p "$TOOLS_DIR" "$DOWNLOAD_DIR"
install_gbdk

if [[ "$host_os" == "Darwin" && "${GAMEBOY_SKIP_DESKTOP:-0}" != "1" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew is required for the macOS Game Boy desktop tools." >&2
        exit 1
    fi

    install_brew_formula rgbds
    install_brew_cask sameboy
    install_brew_cask mgba-app
    install_brew_cask tiled
    install_hugetracker
fi

if [[ "${GAMEBOY_SKIP_DESKTOP:-0}" == "1" ]]; then
    "$GAMEBOY_DIR/scripts/doctor.sh" --core
else
    "$GAMEBOY_DIR/scripts/doctor.sh"
fi
