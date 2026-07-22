"""Create Spotify playlists from recent NTS episode tracklists.

Uses the public NTS v2 API. The default mode creates combined playlists from
recent guest episodes whose genre tags match an ambient/experimental or global
preset.
"""

import argparse
from typing import Dict, Iterable, List, Set

import requests
import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import (
    SCOPE,
    add_tracks_in_batches,
    create_playlist,
    find_spotify_tracks,
    load_spotify_config,
)

BASE_URL = "https://www.nts.live/api/v2"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

PRESETS = {
    "ambient": {
        "playlist": "NTS Ambient Experimental Recent",
        "genre_prefixes": {
            "genres-ambientnewage",
            "genres-avantgarde",
            "genres-housetechno-techno-ambienttechno",
            "genres-jazz-ambientjazz",
            "genres-classicalopera-minimalism",
            "genres-classicalopera-modern-classical",
        },
    },
    "global": {
        "playlist": "NTS Global Recent",
        "genre_prefixes": {
            "genres-caribbean",
            "genres-latinbrazil",
            "genres-africanmiddleeast",
            "genres-asia",
            "genres-other-bhajan",
            "genres-other-balkan",
            "genres-other-celtic",
        },
    },
}


def api_get(path_or_url: str, **params) -> Dict:
    url = path_or_url if path_or_url.startswith("http") else f"{BASE_URL}/{path_or_url.lstrip('/')}"
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def genre_ids(item: Dict) -> Set[str]:
    return {genre.get("id", "") for genre in item.get("genres", []) if genre.get("id")}


def matches_preset(item: Dict, preset: str) -> bool:
    ids = genre_ids(item)
    prefixes = PRESETS[preset]["genre_prefixes"]
    return any(any(genre_id.startswith(prefix) for prefix in prefixes) for genre_id in ids)


def get_recent_matching_episodes(preset: str, latest_episodes: int, scan_limit: int = 250) -> List[Dict]:
    episodes: List[Dict] = []
    offset = 0
    page_size = 50
    while len(episodes) < latest_episodes and offset < scan_limit:
        data = api_get("shows/guests/episodes", limit=page_size, offset=offset)
        results = data.get("results", [])
        if not results:
            break
        for episode in results:
            if matches_preset(episode, preset):
                episodes.append(episode)
                if len(episodes) >= latest_episodes:
                    break
        offset += page_size
    return episodes


def tracklist_url(episode: Dict) -> str:
    for link in episode.get("links", []):
        if link.get("rel") == "tracklist":
            return link["href"]
    return f"{BASE_URL}/shows/{episode['show_alias']}/episodes/{episode['episode_alias']}/tracklist"


def get_episode_rows(episode: Dict) -> List[Dict[str, str]]:
    data = api_get(tracklist_url(episode))
    rows: List[Dict[str, str]] = []
    for item in data.get("results", []):
        artist = (item.get("artist") or "").strip()
        title = (item.get("title") or "").strip()
        if not artist or not title:
            continue
        if artist.lower() in {"unknown", "unidentified"} or title.lower() in {"unknown", "unidentified", "intro"}:
            continue
        rows.append({
            "artist": artist,
            "title": title,
            "episode": episode.get("name", ""),
            "broadcast": episode.get("broadcast", ""),
        })
    print(f"Obtained {len(rows)} tracks from NTS episode: {episode.get('name')} ({episode.get('broadcast', '')[:10]})")
    return rows


def dedupe_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    deduped: List[Dict[str, str]] = []
    seen = set()
    for row in rows:
        key = (row["artist"].lower(), row["title"].lower())
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped


def create_nts_playlist(preset: str, latest_episodes: int, scan_limit: int, dry_run: bool, match_only: bool, min_score: float, overwrite: bool):
    episodes = get_recent_matching_episodes(preset, latest_episodes, scan_limit)
    print(f"Selected {len(episodes)} NTS {preset} episodes")
    for episode in episodes:
        genres = ", ".join(g.get("value", "") for g in episode.get("genres", []))
        print(f"- {episode.get('broadcast', '')[:10]} | {episode.get('name')} | {genres}")

    rows = dedupe_rows(row for episode in episodes for row in get_episode_rows(episode))
    print(f"NTS {preset}: {len(rows)} unique tracks")
    for row in rows[:20]:
        print(f"- {row['artist']} - {row['title']}")

    if dry_run:
        return

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)
    track_ids = find_spotify_tracks(sp, rows, min_score=min_score)
    if match_only:
        print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
        return

    playlist_name = PRESETS[preset]["playlist"]
    description = f"Recent NTS {preset} tracks from {len(episodes)} matching guest episodes"
    pl_id = create_playlist(sp, username, playlist_name, description, overwrite=overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)}/{len(rows)} to playlist {playlist_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=sorted(PRESETS), action="append", help="Preset to build. Can be repeated. Default: ambient and global")
    parser.add_argument("--latest-episodes", type=int, default=10)
    parser.add_argument("--scan-limit", type=int, default=250, help="How many recent NTS guest episodes to scan for matching genre tags")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.55)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    presets = args.preset or ["ambient", "global"]
    for preset in presets:
        create_nts_playlist(
            preset=preset,
            latest_episodes=args.latest_episodes,
            scan_limit=args.scan_limit,
            dry_run=args.dry_run,
            match_only=args.match_only,
            min_score=args.min_score,
            overwrite=not args.no_overwrite,
        )
