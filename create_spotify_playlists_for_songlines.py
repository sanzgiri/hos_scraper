"""Create Spotify playlists from Songlines: Top of the World compilations.

Source: MusicBrainz releases titled "Songlines: Top of the World <issue>".
MusicBrainz currently has useful coverage from roughly issue 25 (2004) onward;
the real Songlines CD series began with issue 1 in Spring 1999, but those early
issues are not consistently present in MusicBrainz.
"""

import argparse
import re
import time
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional

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

MUSICBRAINZ = "https://musicbrainz.org/ws/2"
HEADERS = {"User-Agent": "hos_scraper/1.0 (local playlist generator)"}
TITLE_RE = re.compile(r"Songlines:\s*Top of the World\s+(\d+)", re.I)


def mb_get(path: str, **params):
    params.setdefault("fmt", "json")
    url = f"{MUSICBRAINZ}/{path}"
    last_error = None
    for attempt in range(5):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=45)
            if response.status_code in {500, 502, 503, 504, 429}:
                raise requests.HTTPError(f"MusicBrainz transient HTTP {response.status_code}", response=response)
            response.raise_for_status()
            time.sleep(1.2)  # MusicBrainz asks clients not to exceed 1 request/sec.
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            wait = 3 * (attempt + 1)
            print(f"MusicBrainz request failed ({exc}); retrying in {wait}s [{attempt + 1}/5]")
            time.sleep(wait)
    raise last_error


def artist_credit_name(credits) -> str:
    if not credits:
        return ""
    return "".join(part.get("name", "") + part.get("joinphrase", "") for part in credits).strip()


def parse_issue(release: Dict) -> Optional[int]:
    match = TITLE_RE.search(release.get("title", ""))
    return int(match.group(1)) if match else None


def discover_songlines_releases() -> List[Dict]:
    releases: Dict[int, Dict] = {}
    query = '"Songlines: Top of the World"'
    first = mb_get("release", query=query, limit=100, offset=0)
    total = first.get("count", 0)
    pages = [first]
    for offset in range(100, total, 100):
        pages.append(mb_get("release", query=query, limit=100, offset=offset))

    for page in pages:
        for release in page.get("releases", []):
            issue = parse_issue(release)
            if issue is None:
                continue
            existing = releases.get(issue)
            # Prefer dated releases; otherwise keep the first result.
            if not existing or (release.get("date") and not existing.get("date")):
                releases[issue] = {
                    "issue": issue,
                    "id": release["id"],
                    "title": release.get("title", f"Songlines: Top of the World {issue}"),
                    "date": release.get("date", ""),
                    "year": (release.get("date") or "")[:4],
                }
    return sorted(releases.values(), key=lambda item: item["issue"])


def search_issue(issue: int) -> Optional[Dict]:
    query = f'"Songlines: Top of the World {issue}"'
    data = mb_get("release", query=query, limit=25)
    matches = []
    for release in data.get("releases", []):
        if parse_issue(release) == issue:
            matches.append(release)
    if not matches:
        return None
    matches.sort(key=lambda r: (not bool(r.get("date")), r.get("date", "9999")))
    release = matches[0]
    return {
        "issue": issue,
        "id": release["id"],
        "title": release.get("title", f"Songlines: Top of the World {issue}"),
        "date": release.get("date", ""),
        "year": (release.get("date") or "")[:4],
    }


def get_release_rows(release: Dict) -> List[Dict[str, str]]:
    full = mb_get(f"release/{release['id']}", inc="recordings+artist-credits")
    rows: List[Dict[str, str]] = []
    for medium in full.get("media", []):
        for track in medium.get("tracks", []):
            recording = track.get("recording") or {}
            artist = artist_credit_name(track.get("artist-credit")) or artist_credit_name(recording.get("artist-credit"))
            title = track.get("title") or recording.get("title", "")
            if artist and title:
                rows.append({
                    "artist": artist,
                    "title": title,
                    "album": release["title"],
                    "issue": str(release["issue"]),
                    "year": release.get("year", ""),
                })
    print(f"Obtained {len(rows)} tracks for {release['title']} ({release.get('date', '')})")
    return rows


def group_by_year(releases: List[Dict]) -> DefaultDict[str, List[Dict]]:
    grouped: DefaultDict[str, List[Dict]] = defaultdict(list)
    for release in releases:
        grouped[release.get("year") or "unknown"].append(release)
    return grouped


def print_release_summary(releases: List[Dict]):
    if not releases:
        print("No Songlines Top of the World releases found")
        return
    print(f"Found {len(releases)} Songlines Top of the World releases in MusicBrainz")
    print(f"Issue range: {releases[0]['issue']}–{releases[-1]['issue']}")
    years = sorted({release.get("year") for release in releases if release.get("year")})
    if years:
        print(f"Year range: {years[0]}–{years[-1]}")
    for release in releases:
        print(f"{release['issue']:>3}: {release.get('date', ''):<7} {release['title']}")


def update_playlist(sp, username: str, name: str, description: str, rows: List[Dict[str, str]], min_score: float, match_only: bool, overwrite: bool):
    track_ids = find_spotify_tracks(sp, rows, min_score=min_score)
    if match_only:
        print(f"Matched {len(track_ids)}/{len(rows)} Spotify tracks for {name}")
        return
    pl_id = create_playlist(sp, username, name, description, overwrite=overwrite)
    add_tracks_in_batches(sp, username, pl_id, track_ids)
    print(f"Added {len(track_ids)}/{len(rows)} to playlist {name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, action="append", help="Songlines Top of the World issue number. Can be repeated.")
    parser.add_argument("--year", action="append", help="Only include this release year. Can be repeated.")
    parser.add_argument("--by-year", action="store_true", help="Create one playlist per year instead of one per issue")
    parser.add_argument("--combined", action="store_true", help="Create one combined playlist for selected releases")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.62)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    if args.issue:
        releases = [release for issue in args.issue if (release := search_issue(issue))]
        missing = sorted(set(args.issue) - {release["issue"] for release in releases})
        for issue in missing:
            print(f"Issue {issue}: not found in MusicBrainz")
    else:
        releases = discover_songlines_releases()

    if args.year:
        wanted_years = set(args.year)
        releases = [release for release in releases if release.get("year") in wanted_years]

    print_release_summary(releases)
    release_rows = [(release, get_release_rows(release)) for release in releases]

    if args.dry_run:
        for _, rows in release_rows:
            for row in rows[:12]:
                print(f"- {row['artist']} - {row['title']} [{row['album']}]")
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    if args.combined:
        rows = [row for _, rs in release_rows for row in rs]
        update_playlist(
            sp,
            username,
            "Songlines Top of the World",
            "Songlines Top of the World tracks from MusicBrainz",
            rows,
            args.min_score,
            args.match_only,
            overwrite=not args.no_overwrite,
        )
    elif args.by_year:
        for year, year_releases in sorted(group_by_year(releases).items()):
            rows = [row for release, rs in release_rows if release in year_releases for row in rs]
            update_playlist(
                sp,
                username,
                f"Songlines Top of the World {year}",
                f"Songlines Top of the World tracks from {year}",
                rows,
                args.min_score,
                args.match_only,
                overwrite=not args.no_overwrite,
            )
    else:
        for release, rows in release_rows:
            update_playlist(
                sp,
                username,
                f"Songlines Top of the World {release['issue']}",
                f"{release['title']} ({release.get('date', '')})",
                rows,
                args.min_score,
                args.match_only,
                overwrite=not args.no_overwrite,
            )
