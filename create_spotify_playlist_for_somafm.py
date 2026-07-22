"""Create Spotify playlists from SomaFM recent song history."""

import argparse
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import SCOPE, add_tracks_in_batches, create_playlist, find_spotify_tracks, load_spotify_config

CHANNELS = {
    "dronezone": "Drone Zone",
    "groovesalad": "Groove Salad",
    "spacestation": "Space Station Soma",
    "deepspaceone": "Deep Space One",
}


def get_somafm_rows(channel: str, limit: int = 100) -> List[Dict[str, str]]:
    url = f"https://somafm.com/{channel}/songhistory.html"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    rows = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True).replace("\xa0", " ") for c in tr.find_all("td")]
        if len(cells) < 4 or cells[0] == "Played At":
            continue
        _, artist, title, album = cells[:4]
        if artist and title:
            rows.append({"artist": artist, "title": title, "album": album})
        if len(rows) >= limit:
            break
    print(f"Obtained {len(rows)} tracks for SomaFM {CHANNELS.get(channel, channel)}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("channels", nargs="*", choices=sorted(CHANNELS), help="SomaFM channel slug(s)")
    parser.add_argument("--recommended", action="store_true", help="Use Drone Zone, Groove Salad, Space Station Soma, Deep Space One")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.62)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    channels = list(args.channels)
    if args.recommended:
        channels.extend(CHANNELS.keys())
    channels = list(dict.fromkeys(channels))
    if not channels:
        parser.error("provide channel(s) or --recommended")

    if args.dry_run:
        sp = None
        username = ""
    else:
        username = load_spotify_config()
        token = util.prompt_for_user_token(username, SCOPE)
        sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    for channel in channels:
        rows = get_somafm_rows(channel, args.limit)
        for row in rows[:10]:
            print(f"- {row['artist']} - {row['title']} [{row.get('album', '')}]")
        if args.dry_run:
            continue
        track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
        if args.match_only:
            print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
            continue
        pl_name = f"SomaFM {CHANNELS[channel]}"
        pl_id = create_playlist(sp, username, pl_name, f"Recent SomaFM {CHANNELS[channel]} tracks", overwrite=not args.no_overwrite)
        add_tracks_in_batches(sp, username, pl_id, track_ids)
        print(f"Added {len(track_ids)}/{len(rows)} to playlist {pl_name}")
