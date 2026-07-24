#!/usr/bin/env bash
# RC ID: RC-121. Exercise the native Tauri window under Xvfb/Openbox.

set -euo pipefail

display_number="${RC_DISPLAY:-:99}"
desktop_binary="${RC_DESKTOP_BINARY:-/tmp/rabbit-target/debug/rabbit-code-desktop}"

cleanup() {
  if [[ -n "${app_pid:-}" ]] && kill -0 "$app_pid" 2>/dev/null; then
    kill "$app_pid" 2>/dev/null || true
  fi
  kill "${wm_pid:-}" "${xvfb_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT

Xvfb "$display_number" -screen 0 1536x1024x24 >/tmp/rc121-xvfb.log 2>&1 &
xvfb_pid=$!
export DISPLAY="$display_number"
openbox >/tmp/rc121-openbox.log 2>&1 &
wm_pid=$!
sleep 2

"$desktop_binary" >/tmp/rc121-rabbit.log 2>&1 &
app_pid=$!
window_id=""
for _ in $(seq 1 60); do
  window_id=$(xdotool search --name "Rabbit Code" 2>/dev/null | head -n 1 || true)
  [[ -n "$window_id" ]] && break
  sleep 0.25
done

if [[ -z "$window_id" ]]; then
  cat /tmp/rc121-rabbit.log >&2
  exit 1
fi

echo "WINDOW|id=$window_id"
xdotool getwindowgeometry "$window_id"
xdotool windowsize "$window_id" 1200 800
echo "RESIZED"
xdotool getwindowgeometry "$window_id"
xdotool windowactivate --sync "$window_id"
wmctrl -i -r "$window_id" -b add,maximized_vert,maximized_horz
sleep 1
echo "MAXIMIZED"
xdotool getwindowgeometry "$window_id"
xdotool windowclose "$window_id"

set +e
wait "$app_pid"
exit_code=$?
set -e
echo "EXIT|code=$exit_code"
test "$exit_code" -eq 0
