#!/usr/bin/env bash
set -euo pipefail

# Create/update the curated radio playlists we selected earlier:
#   - selected XM stations
#   - selected SomaFM channels
#   - Radio Paradise main/mellow/rock/world
#
# Usage:
#   ./run_radio_playlists.sh
#   DRY_RUN=1 ./run_radio_playlists.sh
#   XM_DAYS=14 SOMAFM_LIMIT=50 RP_LIMIT=50 ./run_radio_playlists.sh
#
# Requires:
#   source .venv/bin/activate
#   python spotify_auth_check.py   # once, to authorize Spotify

PYTHON_BIN="${PYTHON_BIN:-python}"
XM_DAYS="${XM_DAYS:-30}"
SOMAFM_LIMIT="${SOMAFM_LIMIT:-100}"
RP_LIMIT="${RP_LIMIT:-100}"
DRY_RUN="${DRY_RUN:-0}"
MIN_SCORE="${MIN_SCORE:-0.55}"

# XM stations selected earlier. Includes old favorites, newer electronic/chill/jazz
# additions, and SiriusXM Dhamaka for South Asian music.
XM_STATIONS=(
  siriusxmchill
  watercolors
  spa
  steveaokisremixradio
  astateofarmin
  luna
  bpm
  diplosrevolution
  studio54radio
  radiomonaco
  utopia
  expertsonlyradio
  oneworldradio
  escape
  realjazz
  siriusxmdhamaka
)

# SomaFM channels selected earlier.
SOMAFM_CHANNELS=(
  dronezone
  groovesalad
  spacestation
  deepspaceone
)

# Radio Paradise channels to keep separate.
RADIO_PARADISE_CHANNELS=(
  main
  mellow
  rock
  world
)

extra_args=()
if [[ "$DRY_RUN" == "1" ]]; then
  extra_args+=(--dry-run)
fi

run_cmd() {
  echo
  echo "+ $*"
  "$@"
}

echo "Curated radio playlist update starting"
echo "XM_DAYS=$XM_DAYS SOMAFM_LIMIT=$SOMAFM_LIMIT RP_LIMIT=$RP_LIMIT DRY_RUN=$DRY_RUN MIN_SCORE=$MIN_SCORE"
echo "XM stations: ${#XM_STATIONS[@]}"
echo "SomaFM channels: ${#SOMAFM_CHANNELS[@]}"
echo "Radio Paradise channels: ${#RADIO_PARADISE_CHANNELS[@]}"

for station in "${XM_STATIONS[@]}"; do
  run_cmd "$PYTHON_BIN" create_spotify_playlist_for_xm_channel.py "$station" --days "$XM_DAYS" "${extra_args[@]}"
done

for channel in "${SOMAFM_CHANNELS[@]}"; do
  run_cmd "$PYTHON_BIN" create_spotify_playlist_for_somafm.py "$channel" --limit "$SOMAFM_LIMIT" --min-score "$MIN_SCORE" "${extra_args[@]}"
done

for channel in "${RADIO_PARADISE_CHANNELS[@]}"; do
  run_cmd "$PYTHON_BIN" create_spotify_playlist_for_radio_paradise.py --channel "$channel" --limit "$RP_LIMIT" --min-score "$MIN_SCORE" "${extra_args[@]}"
done

echo
echo "Curated radio playlist update complete"
