"""Create Spotify playlists from a manually curated early Songlines CSV.

CSV columns: issue,year,artist,title,album,source
Use this for Songlines early issues #1-24, which are not available in
MusicBrainz as structured Top of the World releases.
"""

import argparse
import csv
from collections import defaultdict
from typing import Dict, Iterable, List

import spotipy
import spotipy.util as util

from create_spotify_playlist_for_hos_episode import (
    SCOPE,
    add_tracks_in_batches,
    create_playlist,
    find_spotify_tracks,
    load_spotify_config,
)


def load_rows(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            artist = (row.get("artist") or "").strip()
            title = (row.get("title") or "").strip()
            if not artist or not title:
                continue
            rows.append({
                "artist": artist,
                "title": title,
                "album": (row.get("album") or "").strip(),
                "issue": (row.get("issue") or "").strip(),
                "year": (row.get("year") or "").strip(),
                "source": (row.get("source") or "").strip(),
            })
    return rows


def dedupe_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    deduped: List[Dict[str, str]] = []
    seen = set()
    for row in rows:
        key = (row["artist"].lower(), row["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


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
    parser.add_argument("--csv", default="data/songlines_early_issues.csv")
    parser.add_argument("--combined", action="store_true", help="Create one combined early Songlines playlist")
    parser.add_argument("--by-year", action="store_true", help="Create one playlist per year")
    parser.add_argument("--by-issue", action="store_true", help="Create one playlist per issue where issue is present")
    parser.add_argument("--year", action="append", help="Only include this year. Can be repeated")
    parser.add_argument("--issue", action="append", help="Only include this issue. Can be repeated")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.55)
    parser.add_argument("--no-overwrite", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.csv)
    if args.year:
        wanted = set(args.year)
        rows = [row for row in rows if row.get("year") in wanted]
    if args.issue:
        wanted = set(args.issue)
        rows = [row for row in rows if row.get("issue") in wanted]
    rows = dedupe_rows(rows)

    print(f"Loaded {len(rows)} early Songlines rows from {args.csv}")
    for row in rows[:25]:
        tag = f"issue {row['issue']}" if row.get("issue") else row.get("year", "")
        print(f"- {tag}: {row['artist']} - {row['title']}")

    if args.dry_run:
        raise SystemExit(0)

    username = load_spotify_config()
    token = util.prompt_for_user_token(username, SCOPE)
    sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    overwrite = not args.no_overwrite
    if args.by_year:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row.get("year") or "unknown"].append(row)
        for year, year_rows in sorted(grouped.items()):
            update_playlist(sp, username, f"Songlines Early {year}", f"Manually curated early Songlines tracks from {year}", year_rows, args.min_score, args.match_only, overwrite)
    elif args.by_issue:
        grouped = defaultdict(list)
        for row in rows:
            if row.get("issue"):
                grouped[row["issue"]].append(row)
        for issue, issue_rows in sorted(grouped.items(), key=lambda item: int(item[0])):
            update_playlist(sp, username, f"Songlines Top of the World Early Issue {issue}", f"Manually curated Songlines early issue {issue}", issue_rows, args.min_score, args.match_only, overwrite)
    else:
        update_playlist(sp, username, "Songlines Early Issues", "Manually curated Songlines early issues #1-24 and related 1999-2003 tracks", rows, args.min_score, args.match_only, overwrite)
