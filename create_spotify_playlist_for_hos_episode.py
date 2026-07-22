"""Create a Spotify playlist from a Hearts of Space episode."""

import argparse
import configparser as ConfigParser
import difflib
import html
import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple

import requests
import spotipy
import spotipy.util as util


SCOPE = [
    "playlist-modify-public",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-read-playback-state",
    "user-modify-playback-state",
]


def _headers() -> Dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://v4.hos.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 Chrome Safari/537.36",
    }


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()


def get_hos_playlist(episode_id: int) -> Tuple[List[Dict[str, str]], str, str]:
    response = requests.get(
        f"https://api.hos.com/api/v1/programs/{episode_id}",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    program = response.json()

    title = program.get("title") or f"Episode {episode_id}"
    genre = ""
    if program.get("genres"):
        genre = program["genres"][0].get("name", "")
    description = _strip_html(
        f"Title: {title}. Short Description: {program.get('shortDescription', '')}. "
        f"Genre: {genre}. Description: {program.get('description', '')}"
    )

    rows: List[Dict[str, str]] = []
    for album in program.get("albums", []):
        for track in album.get("tracks", []):
            artists = track.get("artists") or album.get("artists") or []
            artist = artists[0].get("name", "") if artists else ""
            track_title = track.get("title", "")
            if track_title:
                rows.append({"title": track_title, "artist": artist})

    print(f"Obtained {len(rows)} tracks for HOS episode {episode_id}: {title}")
    return rows, title, description


def load_spotify_config(config_file: str = "spotify.cfg"):
    config = ConfigParser.RawConfigParser()
    if config.read(config_file):
        os.environ["SPOTIPY_CLIENT_ID"] = config.get("spotify", "client_id")
        os.environ["SPOTIPY_CLIENT_SECRET"] = config.get("spotify", "client_secret")
        os.environ["SPOTIPY_REDIRECT_URI"] = config.get("spotify", "redirect_uri")
        return config.get("spotify", "username")

    # Optional local fallback used by spotify-mcp-server. Do not print secrets.
    mcp_config = os.path.expanduser("~/spotify-mcp-server/spotify-config.json")
    if os.path.exists(mcp_config):
        with open(mcp_config) as handle:
            data = json.load(handle)
        os.environ["SPOTIPY_CLIENT_ID"] = data["clientId"]
        os.environ["SPOTIPY_CLIENT_SECRET"] = data["clientSecret"]
        os.environ["SPOTIPY_REDIRECT_URI"] = data["redirectUri"]
        return os.environ.get("USER", "spotify-user")

    raise FileNotFoundError(f"Spotify config not found: {config_file} or {mcp_config}")


def create_playlist(sp, username: str, plname: str, description: str, overwrite: bool):
    playlist_id = None
    playlists = sp.user_playlists(username)
    while playlists:
        for playlist in playlists["items"]:
            if playlist["name"] == plname:
                playlist_id = playlist["id"]
                break
        if playlist_id or not playlists.get("next"):
            break
        playlists = sp.next(playlists)

    if playlist_id and overwrite:
        print("Playlist exists, deleting:", playlist_id)
        sp.user_playlist_unfollow(username, playlist_id)
        playlist_id = None

    if not playlist_id:
        print("Creating new playlist:", plname)
        playlist = sp.user_playlist_create(username, plname, public=True, description=description[:300])
        playlist_id = playlist["id"]
    else:
        print("Reusing:", playlist_id)

    return playlist_id


def clean_track_title(track: str) -> str:
    track = html.unescape(track or "")
    track = re.sub(r"\s*\([^)]*(excerpt|edit|remaster|version|feat\.?)[^)]*\)\s*$", "", track, flags=re.I)
    track = re.sub(r"\s*\[[^]]*\]\s*$", "", track)
    return re.sub(r"\s+", " ", track).strip()


def normalize(value: str) -> str:
    value = html.unescape(value or "").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"\b(feat|featuring|ft)\.?\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def split_hos_artists(artist: str) -> List[str]:
    artist = re.sub(r"\([^)]*\)", " ", artist or "")
    parts = re.split(r"\s*(?:/|,|;|\+|\band\b|&)\s*", artist, flags=re.I)
    return [part.strip() for part in parts if part.strip()]


def similarity(left: str, right: str) -> float:
    left_norm = normalize(left)
    right_norm = normalize(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    if left_norm in right_norm or right_norm in left_norm:
        return 0.9
    return difflib.SequenceMatcher(None, left_norm, right_norm).ratio()


def spotify_artist_string(item: Dict) -> str:
    return " ".join(artist.get("name", "") for artist in item.get("artists", []))


def score_spotify_candidate(item: Dict, hos_track: str, hos_artist: str) -> float:
    title_score = similarity(hos_track, item.get("name", ""))
    spotify_artists = spotify_artist_string(item)
    hos_artist_parts = split_hos_artists(hos_artist) or [hos_artist]
    artist_score = max((similarity(part, spotify_artists) for part in hos_artist_parts if part), default=0.0)

    # HOS often lists collaborations as "A / B / C" while Spotify may credit only
    # one contributor, so title is weighted more heavily than artist.
    return (0.72 * title_score) + (0.28 * artist_score)


def spotify_search_queries(track: str, artist: str) -> List[str]:
    artist_parts = split_hos_artists(artist)
    queries = []
    if artist:
        queries.append(f"track:{track} artist:{artist}")
    for part in artist_parts[:3]:
        queries.append(f"track:{track} artist:{part}")
    queries.append(f"track:{track}")
    queries.append(f"{track} {artist_parts[0] if artist_parts else artist}".strip())

    deduped = []
    seen = set()
    for query in queries:
        if query and query not in seen:
            seen.add(query)
            deduped.append(query)
    return deduped


def spotify_search_with_retries(sp, query: str, retries: int = 3, timeout_sleep: float = 2.0) -> Dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return sp.search(q=query, type="track", limit=10)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            print(f"Spotify search timeout/error on attempt {attempt}/{retries}: {query}")
            if attempt < retries:
                time.sleep(timeout_sleep * attempt)
    print(f"Spotify search failed after {retries} attempts: {query} ({last_error})")
    return {"tracks": {"items": []}}


def search_best_spotify_match(sp, track: str, artist: str, min_score: float) -> Tuple[Optional[Dict], float, str]:
    candidates: Dict[str, Dict] = {}
    last_query = ""
    for query in spotify_search_queries(track, artist):
        last_query = query
        results = spotify_search_with_retries(sp, query)
        for item in results.get("tracks", {}).get("items", []):
            candidates[item["id"]] = item

    best_item = None
    best_score = 0.0
    for item in candidates.values():
        score = score_spotify_candidate(item, track, artist)
        if score > best_score:
            best_item = item
            best_score = score

    if best_item and best_score >= min_score:
        return best_item, best_score, last_query
    return None, best_score, last_query


def find_spotify_tracks(sp, rows: List[Dict[str, str]], min_score: float = 0.62) -> List[str]:
    track_ids: List[str] = []
    seen = set()
    for row in rows:
        track = clean_track_title(row["title"])
        artist = row.get("artist", "")
        item, score, _ = search_best_spotify_match(sp, track, artist, min_score)
        if item:
            track_id = item["id"]
            spotify_artists = ", ".join(a["name"] for a in item.get("artists", []))
            if track_id not in seen:
                seen.add(track_id)
                track_ids.append(track_id)
                print(f"MATCH {score:.2f}: {artist} - {track} -> {spotify_artists} - {item['name']}")
            else:
                print(f"DUPLICATE {score:.2f}: {artist} - {track} -> {spotify_artists} - {item['name']}")
        else:
            print(f"NO MATCH {score:.2f}: {artist} - {track}")
    return track_ids


def add_tracks_in_batches(sp, username: str, playlist_id: str, track_ids: List[str]):
    for start in range(0, len(track_ids), 100):
        sp.user_playlist_add_tracks(username, playlist_id, track_ids[start:start + 100])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_id", type=int)
    parser.add_argument("--dry-run", action="store_true", help="Only scrape and print HOS tracks; do not use Spotify")
    parser.add_argument("--match-only", action="store_true", help="Search Spotify and print matches; do not create a playlist")
    parser.add_argument("--min-score", type=float, default=0.62, help="Minimum fuzzy match score, from 0.0 to 1.0")
    parser.add_argument("--no-overwrite", action="store_true", help="Reuse an existing playlist instead of replacing it")
    args = parser.parse_args()

    rows, title, description = get_hos_playlist(args.episode_id)
    print(title)
    for row in rows[:10]:
        print(f"- {row['artist']} - {row['title']}")
    if args.dry_run:
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
    if args.match_only:
        print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
        raise SystemExit(0)

    pl_name = f"HOS_{args.episode_id}: {title}"
    pl_id = create_playlist(sp, username, pl_name, description, overwrite=not args.no_overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)}/{len(rows)} to playlist {pl_name}")
