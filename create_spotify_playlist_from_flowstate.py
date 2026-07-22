"""List Spotify links referenced by recent Flow State posts."""

import argparse
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.flowstate.fm"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 Chrome Safari/537.36",
}
SPOTIFY_RE = re.compile(r'https://open\.spotify\.com/(album|playlist|track)/[^\s?&#)\]\"]+')


def _clean_spotify_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def get_flowstate_episodes(limit: Optional[int] = None) -> List[str]:
    response = requests.get(f"{BASE_URL}/api/v1/archive", params={"sort": "new"}, headers=HEADERS, timeout=30)
    response.raise_for_status()
    posts = response.json()
    episodes = [post["slug"] for post in posts if post.get("slug")]
    return episodes[:limit] if limit else episodes


def get_spotify_links_for_episode(slug: str) -> List[str]:
    response = requests.get(f"{BASE_URL}/api/v1/posts/{slug}", headers=HEADERS, timeout=30)
    response.raise_for_status()
    post = response.json()
    soup = BeautifulSoup(post.get("body_html", ""), "html.parser")

    links: List[str] = []
    seen = set()

    # Prefer hrefs, but also scan the text/html because Substack can rewrite links.
    candidates = [a.get("href", "") for a in soup.find_all("a")]
    candidates += [match.group(0) for match in SPOTIFY_RE.finditer(str(soup))]

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        match = SPOTIFY_RE.search(candidate)
        if not match:
            continue
        url = _clean_spotify_url(match.group(0))
        if url not in seen:
            seen.add(url)
            links.append(url)

    return links


def get_flowstate_spotify_links(limit: Optional[int] = None) -> Dict[str, List[str]]:
    return {slug: get_spotify_links_for_episode(slug) for slug in get_flowstate_episodes(limit)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only check the newest N posts")
    args = parser.parse_args()

    for slug, links in get_flowstate_spotify_links(args.limit).items():
        if links:
            for link in links:
                print(f"{slug}: {link}")
        else:
            print(f"No Spotify links for episode {slug}")
