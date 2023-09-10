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
    token = util.prompt_for_user_token(username, scope)

    sp = spotipy.Spotify(auth=token)
    urn = get_artist(artist)['uri']
    print(urn)
    if not urn:
        print("Artist not found")
        exit(-1)

    pl_name = f'APS Best Of {artist}'
    description = f'APS Best Of {artist}'
    pl_id = create_playlist(username, pl_name, description, overwrite)

    query = f'artist:{artist}'
    results = sp.search(q=query, type='track', limit=50)
    items = results['tracks']['items']
    num_items = len(items)
    print(f"Found {num_items}")

    tracklist = []
    for i in range(num_items):
        print(i, items[i]['name'] )
        id = items[i]['id']
        tracklist.append(id)

    sp.user_playlist_add_tracks(username, pl_id, tracklist)
    print("Playlist created")


