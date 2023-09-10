"""
Todo:
- Remove deprecated functions
- Add Description to Playlist
"""

import spotipy
import spotipy.util as util
from bs4 import BeautifulSoup
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

stations = ['chuchoscubabeyond', 'siriusxmchill', 'watercolors', 'spa', 'steveaokisremixradio', 'astateofarmin', 'luna']


def get_xm_playlist(station: str):

    url = f"https://xmplaylist.com/station/{station}/most-heard"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    x = soup.findAll('a', href=re.compile(r'https://open.spotify.com/track/.*'))
    playlist = [u['href'] for u in x]
    tracks = [re.match('https://open.spotify.com/track/(.*)$', u).groups()[0] for u in playlist]
    return tracks


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

    station = sys.argv[1]
    token = util.prompt_for_user_token(username, scope)
    print(token)

    sp = spotipy.Spotify(auth=token)
    tracks = get_xm_playlist(station)
    pl_name = f'XM {station}'
    description = f'XM {station} by APS'
    pl_id = create_playlist(username, pl_name, description, overwrite)
    sp.user_playlist_add_tracks(username, pl_id, tracks)
    print(f"Added {len(tracks)} to playlist {pl_name}")

