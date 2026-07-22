"""Create a Spotify playlist from Radio Paradise recent playlist."""

import argparse
from typing import Dict, List

import requests
import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import SCOPE, add_tracks_in_batches, create_playlist, find_spotify_tracks, load_spotify_config

CHANNELS = {
    "main": 0,
    "mellow": 1,
    "rock": 2,
    "world": 3,
}


def get_radio_paradise_rows(channel: str = "main", limit: int = 100) -> List[Dict[str, str]]:
    chan = CHANNELS[channel]
    response = requests.get(
        "https://api.radioparadise.com/api/playlist",
        params={"chan": chan},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    rows = []
    seen = set()
    for item in response.json():
        artist, title = item.get("artist", ""), item.get("title", "")
        key = (artist.lower(), title.lower())
        if artist and title and key not in seen:
            seen.add(key)
            rows.append({"artist": artist, "title": title, "album": item.get("album", "")})
        if len(rows) >= limit:
            break
    print(f"Obtained {len(rows)} tracks for Radio Paradise {channel}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", choices=sorted(CHANNELS), default="main")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.62)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    rows = get_radio_paradise_rows(args.channel, args.limit)
    for row in rows[:10]:
        print(f"- {row['artist']} - {row['title']} [{row.get('album', '')}]")
    if args.dry_run:
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)
    track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
    if args.match_only:
        print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
        raise SystemExit(0)

    pl_name = f"Radio Paradise {args.channel.title()}"
    pl_id = create_playlist(sp, username, pl_name, f"Recent Radio Paradise {args.channel} playlist", overwrite=not args.no_overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)}/{len(rows)} to playlist {pl_name}")
