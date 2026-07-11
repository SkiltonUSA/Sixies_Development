#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${CONDUCTOR_PORT:-12765}"
HOST="127.0.0.1"
BUILD_DIR="$ROOT_DIR/build"
VICE_STATE_DIR="${HOME}/.local/state/vice"
PRG_PATH="$BUILD_DIR/transition_browser.prg"

find_listener_pid() {
  lsof -tiTCP:"$PORT" -sTCP:LISTEN -nP 2>/dev/null | head -n 1
}

process_cwd() {
  lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
}

ensure_port_available() {
  local listener_pid
  local command_line
  local listener_cwd
  local attempts

  listener_pid="$(find_listener_pid || true)"
  [[ -n "$listener_pid" ]] || return 0

  command_line="$(ps -p "$listener_pid" -o command= 2>/dev/null || true)"
  listener_cwd="$(process_cwd "$listener_pid" || true)"
  if [[ "$command_line" == *"http.server $PORT --bind $HOST"* ]] &&
     [[ "$listener_cwd" == "$BUILD_DIR" ]]; then
    echo "Stopping stale local server on $HOST:$PORT"
    kill "$listener_pid" 2>/dev/null || true
    for attempts in 1 2 3 4 5; do
      sleep 0.5
      listener_pid="$(find_listener_pid || true)"
      [[ -z "$listener_pid" ]] && return 0
    done
    kill -9 "$listener_pid" 2>/dev/null || true
  fi

  echo "Port $HOST:$PORT is already in use." >&2
  if [[ -n "$command_line" ]]; then
    echo "Listener: $command_line" >&2
  fi
  exit 1
}

stop_existing_vice() {
  local pids

  pids="$(pgrep -f '/x64sc|/x64' || true)"
  [[ -n "$pids" ]] || return 0

  echo "Stopping existing VICE instances"
  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    kill "$pid" 2>/dev/null || true
  done <<<"$pids"

  sleep 1

  pids="$(pgrep -f '/x64sc|/x64' || true)"
  [[ -z "$pids" ]] && return 0

  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    kill -9 "$pid" 2>/dev/null || true
  done <<<"$pids"
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to serve the build directory." >&2
  exit 1
fi

"$ROOT_DIR/scripts/build_transition_browser.sh"
VICE_BIN="$("$ROOT_DIR/scripts/find-vice.sh")"

cat >"$ROOT_DIR/build/transition_browser.html" <<EOF
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Transition Browser</title>
    <style>
      body {
        margin: 0;
        background: #0a111d;
        color: #eef4ff;
        font-family: "Iowan Old Style", serif;
      }
      main {
        max-width: 720px;
        margin: 48px auto;
        padding: 0 20px;
      }
      .card {
        padding: 28px;
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(16, 34, 58, 0.95), rgba(8, 14, 24, 0.95));
        border: 1px solid rgba(150, 210, 255, 0.18);
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
      }
      a {
        color: #91e3ff;
      }
      code {
        font-family: "SF Mono", "Menlo", monospace;
      }
    </style>
  </head>
  <body>
    <main>
      <section class="card">
        <h1>Transition Browser</h1>
        <p>The transition browser build is ready and VICE should be opening on this Mac.</p>
        <p>Artifact: <a href="/transition_browser.prg">transition_browser.prg</a></p>
        <p>Address: <code>http://$HOST:$PORT/</code></p>
      </section>
    </main>
  </body>
</html>
EOF

ensure_port_available

mkdir -p "$VICE_STATE_DIR"
stop_existing_vice

echo "Serving build directory at http://$HOST:$PORT/"
cd "$BUILD_DIR"
echo "Launching VICE with $PRG_PATH"
"$VICE_BIN" +logtofile -logfile "$VICE_STATE_DIR/vice.log" \
  -autostartprgmode 1 -autostart-warp -autostart "$PRG_PATH" >/dev/null 2>&1 &

exec python3 -m http.server "$PORT" --bind "$HOST"
