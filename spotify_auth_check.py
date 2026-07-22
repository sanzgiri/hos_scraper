"""Authorize Spotify and create/remove a temporary test playlist.

This is a safe credential check. It does not print secrets. It updates spotify.cfg
with the authenticated Spotify user id after successful authorization.
"""

import configparser
import json
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = "playlist-modify-public playlist-modify-private"


def load_client_config():
    cfg = configparser.RawConfigParser()
    if cfg.read("spotify.cfg"):
        return {
            "client_id": cfg.get("spotify", "client_id"),
            "client_secret": cfg.get("spotify", "client_secret"),
            "redirect_uri": cfg.get("spotify", "redirect_uri"),
        }

    mcp = os.path.expanduser("~/spotify-mcp-server/spotify-config.json")
    with open(mcp) as handle:
        data = json.load(handle)
    return {
        "client_id": data["clientId"],
        "client_secret": data["clientSecret"],
        "redirect_uri": data["redirectUri"],
    }


def update_spotify_cfg(username, client):
    cfg = configparser.RawConfigParser()
    cfg["spotify"] = {
        "username": username,
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": client["redirect_uri"],
    }
    with open("spotify.cfg", "w") as handle:
        cfg.write(handle)
    os.chmod("spotify.cfg", 0o600)


if __name__ == "__main__":
    client = load_client_config()
    auth = SpotifyOAuth(
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        redirect_uri=client["redirect_uri"],
        scope=SCOPE,
        open_browser=False,
        cache_path=".spotify_token_cache",
        show_dialog=True,
    )
    token_info = auth.get_cached_token()
    if not token_info:
        url = auth.get_authorize_url()
        parsed_redirect = urlparse(client["redirect_uri"])
        code_holder = {"code": None}

        if parsed_redirect.hostname in {"localhost", "127.0.0.1"} and parsed_redirect.port:
            class CallbackHandler(BaseHTTPRequestHandler):
                def log_message(self, format, *args):
                    return

                def do_GET(self):
                    params = parse_qs(urlparse(self.path).query)
                    code_holder["code"] = params.get("code", [None])[0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h3>Spotify authorization received. You can close this tab.</h3></body></html>")

            try:
                server = HTTPServer((parsed_redirect.hostname, parsed_redirect.port), CallbackHandler)
                print("Opening Spotify authorization URL in browser...")
                print(url)
                webbrowser.open(url)
                print(f"Waiting for callback on {client['redirect_uri']} ...")
                server.handle_request()
                server.server_close()
            except OSError as exc:
                print(f"Could not listen on {client['redirect_uri']}: {exc}")

        code = code_holder["code"]
        if not code:
            print("Open this Spotify authorization URL:")
            print(url)
            redirected = input("Paste the FULL redirected URL here: ").strip()
            code = auth.parse_response_code(redirected)

        if not code:
            raise RuntimeError("No authorization code found. Paste the full redirect URL, not just part of it.")

        token_info = auth.get_access_token(code, as_dict=True, check_cache=False)

    sp = spotipy.Spotify(auth=token_info["access_token"], requests_timeout=20, retries=5)
    me = sp.current_user()
    update_spotify_cfg(me["id"], client)
    print(f"Authenticated Spotify user: {me.get('display_name') or me['id']} ({me['id']})")

    name = f"hos_scraper_test_{int(time.time())}"
    playlist = sp.user_playlist_create(me["id"], name, public=False, description="Temporary hos_scraper credential test")
    print(f"Created test playlist: {playlist['name']} ({playlist['id']})")
    sp.user_playlist_unfollow(me["id"], playlist["id"])
    print("Removed test playlist")
