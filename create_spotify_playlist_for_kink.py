"""Create a Spotify playlist from KINK-FM Lights Out recent tracks.

KINK exposes a global AmperWave recently-played feed, not a Lights Out archive.
Run this during or shortly after Lights Out to capture that show's tracks.
"""

import argparse
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests
import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import SCOPE, add_tracks_in_batches, create_playlist, find_spotify_tracks, load_spotify_config

KINK_PLAYLIST_ID = "5438"
DEFAULT_TIMEZONE = "America/Los_Angeles"


def in_time_window(dt: datetime, start_hour: Optional[int], end_hour: Optional[int]) -> bool:
    if start_hour is None or end_hour is None:
        return True
    hour = dt.hour
    if start_hour <= end_hour:
        return start_hour <= hour < end_hour
    return hour >= start_hour or hour < end_hour


def get_kink_rows(limit: int = 100, start_hour: Optional[int] = None, end_hour: Optional[int] = None, timezone: str = DEFAULT_TIMEZONE) -> List[Dict[str, str]]:
    # The second-to-last path component is the number of recent performances to return.
    url = f"https://api-nowplaying.amperwave.net/prt/nowplaying/2/{limit}/{KINK_PLAYLIST_ID}/nowplaying.json"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=30)
    response.raise_for_status()
    rows = []
    seen = set()
    tz = ZoneInfo(timezone)
    for item in response.json().get("performances", []):
        played_at = datetime.strptime(item["time"], "%Y-%m-%dT%H:%M:%S%z").astimezone(tz)
        if not in_time_window(played_at, start_hour, end_hour):
            continue
        artist, title = item.get("artist", ""), item.get("title", "")
        key = (artist.lower(), title.lower())
        if artist and title and key not in seen:
            seen.add(key)
            rows.append({"artist": artist, "title": title, "album": item.get("album", ""), "played_at": played_at.isoformat()})
    window = f" between {start_hour}:00 and {end_hour}:00 {timezone}" if start_hour is not None and end_hour is not None else ""
    print(f"Obtained {len(rows)} recent KINK-FM tracks for Lights Out capture{window}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100, help="Number of recent KINK plays to request. Try up to 1000 for a few days of history.")
    parser.add_argument("--start-hour", type=int, help="Only include tracks played at/after this local hour, e.g. 22")
    parser.add_argument("--end-hour", type=int, help="Only include tracks played before this local hour, e.g. 1")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.62)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    rows = get_kink_rows(args.limit, args.start_hour, args.end_hour, args.timezone)
    for row in rows[:10]:
        played_at = f" ({row['played_at']})" if row.get("played_at") else ""
        print(f"- {row['artist']} - {row['title']}{played_at}")
    if args.dry_run:
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)
    track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
    if args.match_only:
        print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
        raise SystemExit(0)

    pl_name = "KINK-FM Lights Out"
    pl_id = create_playlist(sp, username, pl_name, "KINK-FM Lights Out tracks captured from the recent-played feed", overwrite=not args.no_overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)}/{len(rows)} to playlist {pl_name}")
