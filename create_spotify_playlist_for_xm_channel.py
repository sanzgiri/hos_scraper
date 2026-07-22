"""Create a Spotify playlist from xmplaylist.com's most-heard list."""

import argparse
import configparser as ConfigParser
import json
import os
from typing import List

import requests
import spotipy
import spotipy.util as util


SCOPE = "playlist-modify-public"
DEFAULT_DAYS = 30
RECOMMENDED_STATIONS = [
    "siriusxmchill",
    "watercolors",
    "spa",
    "steveaokisremixradio",
    "astateofarmin",
    "luna",
    "bpm",
    "diplosrevolution",
    "studio54radio",
    "radiomonaco",
    "utopia",
    "expertsonlyradio",
    "oneworldradio",
    "escape",
    "realjazz",
    "siriusxmdhamaka",
]


def get_xm_playlist(station: str, days: int = DEFAULT_DAYS) -> List[str]:
    """Return Spotify track IDs for a station's most-heard songs.

    xmplaylist.com is now a JS app; Spotify links are no longer present in the
    initial HTML. Use the same JSON endpoint the app uses.
    """
    url = f"https://xmplaylist.com/api/station/{station}/most-heard"
    response = requests.get(
        url,
        params={"days": days},
        headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    tracks: List[str] = []
    seen = set()
    for result in data.get("results", []):
        spotify_id = (result.get("spotify") or {}).get("id")
        if not spotify_id:
            for link in result.get("links", []):
                url = link.get("url", "")
                if "open.spotify.com/track/" in url:
                    spotify_id = url.split("/track/", 1)[1].split("?", 1)[0]
                    break
        if spotify_id and spotify_id not in seen:
            seen.add(spotify_id)
            tracks.append(spotify_id)

    station_name = (data.get("channel") or {}).get("name", station)
    print(f"Obtained {len(tracks)} Spotify tracks for {station_name} ({station}, {days} days)")
    return tracks


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


def create_playlist(sp, username: str, plname: str, description: str):
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

    if not playlist_id:
        print("Creating new playlist:", plname)
        playlist = sp.user_playlist_create(username, plname, public=True, description=description)
        playlist_id = playlist["id"]
    else:
        print("Updating existing playlist:", playlist_id)
        sp.playlist_change_details(playlist_id, description=description)

    return playlist_id


def add_tracks_in_batches(sp, username: str, playlist_id: str, track_ids: List[str], replace: bool = True):
    if replace:
        sp.playlist_replace_items(playlist_id, track_ids[:100])
        start = 100
    else:
        start = 0
    for index in range(start, len(track_ids), 100):
        sp.user_playlist_add_tracks(username, playlist_id, track_ids[index:index + 100])


def update_xm_playlist(sp, username: str, station: str, days: int, replace: bool, dry_run: bool):
    tracks = get_xm_playlist(station, days)
    for track in tracks[:10]:
        print(f"- https://open.spotify.com/track/{track}")
    if dry_run:
        return

    pl_name = f"XM {station}"
    description = f"XM {station} most heard tracks over {days} days by APS"
    pl_id = create_playlist(sp, username, pl_name, description)
    add_tracks_in_batches(sp, username, pl_id, tracks, replace=replace)
    action = "Replaced" if replace else "Added"
    print(f"{action} {len(tracks)} tracks in playlist {pl_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stations", nargs="*", help="xmplaylist station slugs, e.g. siriusxmchill watercolors")
    parser.add_argument("--recommended", action="store_true", help="Update the recommended chill/electronic/jazz station set")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--dry-run", action="store_true", help="Only scrape and print track IDs; do not use Spotify")
    parser.add_argument("--append", action="store_true", help="Append to existing playlists instead of replacing their contents")
    args = parser.parse_args()

    stations = list(args.stations)
    if args.recommended:
        stations.extend(RECOMMENDED_STATIONS)
    stations = list(dict.fromkeys(stations))
    if not stations:
        parser.error("provide at least one station slug or use --recommended")

    if args.dry_run:
        sp = None
        username = ""
    else:
        username = load_spotify_config()
        token = util.prompt_for_user_token(username, SCOPE)
        sp = spotipy.Spotify(auth=token, requests_timeout=20, retries=5)

    for station in stations:
        update_xm_playlist(sp, username, station, args.days, replace=not args.append, dry_run=args.dry_run)
