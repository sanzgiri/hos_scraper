"""
Todo:
- Remove deprecated functions
- Add Description to Playlist
"""

import spotipy
import spotipy.util as util
import requests
import pandas as pd
import re
import configparser as ConfigParser
import os
import sys

configParser = ConfigParser.RawConfigParser()
configFile = 'spotify.cfg'
configParser.read(configFile)

os.environ['SPOTIPY_CLIENT_ID'] = configParser.get('spotify', 'client_id')
os.environ['SPOTIPY_CLIENT_SECRET'] = configParser.get('spotify', 'client_secret')
os.environ['SPOTIPY_REDIRECT_URI'] = configParser.get('spotify', 'redirect_uri')

username = configParser.get('spotify', 'username')
scope = 'playlist-modify-public'
overwrite = 1

def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found, return the string unchanged.
    """
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s

def get_artist(name):
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None


def create_playlist(username: str, plname: str, description: str, overwrite: int):

    sp = spotipy.Spotify(auth=token)
    playlist_id = 0
    playlists = sp.user_playlists(username)
    # multi-line description does not work, leave it empty for now
    description = ''

    for playlist in playlists['items']:
        if (playlist['name'] == plname):
            playlist_id = playlist['id']
            if (overwrite == 1):
                print("Playlist exists, deleting: ", playlist_id)
                sp.user_playlist_unfollow(username, playlist_id)
                print("Creating new playlist:")
                sp.user_playlist_create(username, plname, True, description)
                playlists = sp.user_playlists(username)
                for playlist in playlists['items']:
                    if (playlist['name'] == plname):
                        playlist_id = playlist['id']
            else:
                print("Reusing: ", playlist_id)
            break

    if (playlist_id == 0):
        print("Creating new playlist:")
        sp.user_playlist_create(username, plname, True, description)
        playlists = sp.user_playlists(username)
        for playlist in playlists['items']:
            if (playlist['name'] == plname):
                playlist_id = playlist['id']
                break

    return playlist_id


if __name__ == '__main__':

    artist = sys.argv[1]
    csvfile = sys.argv[2]

    df = pd.read_csv(csvfile, encoding='utf-8')
    token = util.prompt_for_user_token(username, scope)
    sp = spotipy.Spotify(auth=token)

    pl_name = f'APS - Hindi songs of {artist}'
    description = f'APS - Hindi songs of {artist}'
    pl_id = create_playlist(username, pl_name, description, overwrite)

    tracklist = []
    npassed = 0
    ntracks = len(df)

    for i in range(ntracks):
        track = df['Song'].iloc[i]
        track = dequote(track)
        query = f'artist:{artist}+track:{track}'
        results = sp.search(q=query, type='track', limit=1)
        items = results['tracks']['items']
        if len(items) > 0:
            id = items[0]['id']
            popularity = items[0]['popularity']
            if popularity > 40:
                if (id not in tracklist):
                    tracklist.append(id)
                    print(f"{query}: found {len(items)} {items[0]['name']}")
                    npassed += 1
        else:
            print(f"Track {track} not found")

    print(f"Added {npassed}/{ntracks} to playlist ")

    # break into chunks of 100
    chunks = [tracklist[x:x+100] for x in range(0, len(tracklist), 100)]
    for chunk in chunks:
        sp.user_playlist_add_tracks(username, pl_id, chunk)
        print(f"Added {len(chunk)} tracks to playlist")





