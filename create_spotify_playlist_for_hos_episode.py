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
scope = ['playlist-modify-public', 'user-read-currently-playing',
         'user-read-recently-played', 'user-read-playback-state',
         'user-modify-playback-state']
overwrite = 1

def get_hos_playlist(episode_id: int):

    headers = {
        'sec-ch-ua': '"Google Chrome";v="87", "\\"Not;A\\\\Brand";v="99", "Chromium";v="87"',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://v4.hos.com/',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36',
    }

    response = requests.get(f'https://api.hos.com/api/v1/programs/{episode_id}', headers=headers)
    df = pd.DataFrame()
    description = ""

    if response.status_code == 200:
        x = response.json()
        pgm_name = x['title']
        description = f"Title: {x['title']}, Short Description: {x['shortDescription']}, Genre: {x['genres'][0]['name']}, Description: {x['description']}"
        nsongs = len(x['albums'])
        for i in range(nsongs):
            tracks = x['albums'][i]['tracks']
            numtracks = len(tracks)
            for j in range(numtracks):
                title = tracks[j]['title']
                artists = tracks[j]['artists']
                df = df.append({'title': title,
                                'artist': artists[0]['name']}, ignore_index=True)
        print(f"Obtained playlist for episode {episode_id}")
    else:
        print(f"Failed getting playlist for episode {episode_id}")

    return df, pgm_name, description


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

    episode_id = sys.argv[1]
    token = util.prompt_for_user_token(username, scope)
    print(token)

    sp = spotipy.Spotify(auth=token)
    df_hos, title, description = get_hos_playlist(episode_id)
    print(title)

    pl_name = f'HOS_{episode_id}: {title}'
    #pl_name = f'HOS_{episode_id}'
    pl_id = create_playlist(username, pl_name, description, overwrite)

    if (~df_hos.empty):
        tracklist = []
        ntracks = len(df_hos)
        npassed = 0
        nfailed = 0
        for i in range(ntracks):
            track = df_hos['title'].iloc[i]
            m = re.match('(.*) \(.*\)', track)
            if (m):
                track = m.groups()[0]
            artist = df_hos['artist'].iloc[i]
            query = f'track:{track} artist:{artist}'
            results = sp.search(q=query, type='track')
            items = results['tracks']['items']
            if len(items) > 0:
                id = items[0]['id']
                if (id not in tracklist):
                    tracklist.append(id)
                    print(f"{query}: found {len(items)} {items[0]['name']}")
                    npassed += 1
                tracklist.append(id)
            else:
                print(f"{query}: not found")

    print(f"Added {npassed}/{ntracks} to playlist ")
    sp.user_playlist_add_tracks(username, pl_id, tracklist)
