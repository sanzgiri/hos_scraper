"""Create Spotify playlists from the historical KINK Lights Out compilation albums.

Source: MusicBrainz release-group series "KINK Lights Out". This covers the
benefit compilation albums, not the original radio show's unarchived nightly logs.
"""

import argparse
import time
from typing import Dict, List, Optional

import requests
import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import SCOPE, add_tracks_in_batches, create_playlist, find_spotify_tracks, load_spotify_config

MUSICBRAINZ = "https://musicbrainz.org/ws/2"
SERIES_ID = "c8beeeb7-24c2-4b93-969a-927464f196e7"
HEADERS = {"User-Agent": "hos_scraper/1.0 (local playlist generator)"}


def mb_get(path: str, **params):
    params.setdefault("fmt", "json")
    response = requests.get(f"{MUSICBRAINZ}/{path}", params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    time.sleep(1.0)  # Be polite to MusicBrainz.
    return response.json()


def artist_credit_name(credits) -> str:
    if not credits:
        return ""
    return "".join(part.get("name", "") + part.get("joinphrase", "") for part in credits).strip()


def get_lights_out_albums() -> List[Dict]:
    series = mb_get(f"series/{SERIES_ID}", inc="release-group-rels")
    albums = []
    for relation in series.get("relations", []):
        rg = relation.get("release_group") or {}
        albums.append({
            "volume": int(relation.get("ordering-key") or 0),
            "title": rg.get("title", ""),
            "year": (rg.get("first-release-date") or "")[:4],
            "release_group_id": rg.get("id"),
        })
    return sorted(albums, key=lambda album: album["volume"])


def choose_release(release_group_id: str) -> Optional[Dict]:
    data = mb_get("release", **{"release-group": release_group_id, "limit": 20})
    releases = data.get("releases", [])
    if not releases:
        return None
    # Prefer releases with dates and US country, then first listed.
    releases.sort(key=lambda r: (r.get("country") != "US", not bool(r.get("date")), r.get("date", "9999")))
    return releases[0]


def get_album_rows(album: Dict) -> List[Dict[str, str]]:
    release = choose_release(album["release_group_id"])
    if not release:
        return []
    full = mb_get(f"release/{release['id']}", inc="recordings+artist-credits")
    rows = []
    for medium in full.get("media", []):
        for track in medium.get("tracks", []):
            artist = artist_credit_name(track.get("artist-credit")) or artist_credit_name((track.get("recording") or {}).get("artist-credit"))
            title = track.get("title") or (track.get("recording") or {}).get("title", "")
            if artist and title:
                rows.append({
                    "artist": artist,
                    "title": title,
                    "album": album["title"],
                    "year": album["year"],
                    "volume": str(album["volume"]),
                })
    print(f"Obtained {len(rows)} tracks for {album['title']} ({album['year']})")
    return rows


def playlist_title(album: Dict) -> str:
    return f"KINK Lights Out {album['volume']:02d} - {album['year']}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, action="append", help="Only create this volume. Can be repeated.")
    parser.add_argument("--combined", action="store_true", help="Create one combined playlist instead of one playlist per volume")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.62)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    albums = get_lights_out_albums()
    if args.volume:
        wanted = set(args.volume)
        albums = [album for album in albums if album["volume"] in wanted]

    print(f"KINK Lights Out compilation series: {len(albums)} albums")
    for album in albums:
        print(f"{album['volume']:>2}: {album['year']} - {album['title']}")

    album_rows = [(album, get_album_rows(album)) for album in albums]
    if args.dry_run:
        for _, rows in album_rows:
            for row in rows[:10]:
                print(f"- {row['artist']} - {row['title']} [{row['album']}]")
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    if args.combined:
        rows = [row for _, volume_rows in album_rows for row in volume_rows]
        track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
        if args.match_only:
            print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks")
            raise SystemExit(0)
        pl_id = create_playlist(sp, username, "KINK Lights Out Compilations", "KINK Lights Out benefit compilation albums, 1985-2008", overwrite=not args.no_overwrite)
        add_tracks_in_batches(sp, username, pl_id, track_ids)
        print(f"Added {len(track_ids)}/{len(rows)} to playlist KINK Lights Out Compilations")
    else:
        for album, rows in album_rows:
            track_ids = find_spotify_tracks(sp, rows, min_score=args.min_score)
            if args.match_only:
                print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks for {album['title']}")
                continue
            pl_name = playlist_title(album)
            pl_id = create_playlist(sp, username, pl_name, f"{album['title']} ({album['year']}) from the KINK Lights Out compilation series", overwrite=not args.no_overwrite)
            add_tracks_in_batches(sp, username, pl_id, track_ids)
            print(f"Added {len(track_ids)}/{len(rows)} to playlist {pl_name}")
