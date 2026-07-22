"""Create a Spotify playlist from Putumayo albums found on Spotify.

This script searches Spotify albums for "Putumayo", filters likely Putumayo World
Music releases, collects album tracks, and creates one playlist. It can also limit
to one release year.
"""

import argparse
from typing import Dict, List, Optional

import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import (
    SCOPE,
    add_tracks_in_batches,
    create_playlist,
    load_spotify_config,
)


def album_looks_like_putumayo(album: Dict) -> bool:
    haystack = " ".join(
        [
            album.get("name", ""),
            album.get("label", ""),
            " ".join(artist.get("name", "") for artist in album.get("artists", [])),
        ]
    ).lower()
    return "putumayo" in haystack


def search_putumayo_albums(sp, year: Optional[str] = None, limit: int = 50) -> List[Dict]:
    albums_by_id: Dict[str, Dict] = {}
    queries = ["Putumayo", "label:Putumayo", "Putumayo World Music"]
    if year:
        queries.extend([f"Putumayo year:{year}", f"label:Putumayo year:{year}"])

    for query in queries:
        for offset in range(0, 1000, limit):
            results = sp.search(q=query, type="album", limit=limit, offset=offset)
            items = results.get("albums", {}).get("items", [])
            if not items:
                break
            for album in items:
                album_id = album["id"]
                if album_id in albums_by_id:
                    continue
                full_album = sp.album(album_id)
                if year and not full_album.get("release_date", "").startswith(str(year)):
                    continue
                if album_looks_like_putumayo(full_album):
                    albums_by_id[album_id] = full_album
            if len(items) < limit:
                break

    return sorted(albums_by_id.values(), key=lambda album: (album.get("release_date", ""), album.get("name", "")))


def album_track_ids(sp, album: Dict) -> List[str]:
    tracks: List[str] = []
    page = sp.album_tracks(album["id"], limit=50)
    while page:
        tracks.extend(track["id"] for track in page.get("items", []) if track.get("id"))
        page = sp.next(page) if page.get("next") else None
    return tracks


def collect_putumayo_tracks(sp, albums: List[Dict]) -> List[str]:
    track_ids: List[str] = []
    seen = set()
    for album in albums:
        ids = album_track_ids(sp, album)
        print(f"{album.get('release_date', '')[:4]}: {album['name']} ({len(ids)} tracks)")
        for track_id in ids:
            if track_id not in seen:
                seen.add(track_id)
                track_ids.append(track_id)
    return track_ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", help="Only include Putumayo albums released in this year")
    parser.add_argument("--dry-run", action="store_true", help="List matching albums/tracks; do not create playlist")
    parser.add_argument("--no-overwrite", action="store_true", help="Reuse existing playlist instead of replacing it")
    args = parser.parse_args()

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    albums = search_putumayo_albums(sp, year=args.year)
    print(f"Found {len(albums)} Putumayo albums" + (f" for {args.year}" if args.year else ""))
    track_ids = collect_putumayo_tracks(sp, albums)
    print(f"Collected {len(track_ids)} unique Putumayo tracks")

    if args.dry_run:
        raise SystemExit(0)

    pl_name = f"Putumayo {args.year}" if args.year else "Putumayo World Music"
    description = f"Putumayo tracks found on Spotify" + (f" for {args.year}" if args.year else "")
    pl_id = create_playlist(sp, username, pl_name, description, overwrite=not args.no_overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)} tracks to playlist {pl_name}")
