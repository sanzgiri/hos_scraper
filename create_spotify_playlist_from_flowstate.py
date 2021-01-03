import sys
import urllib.parse
import requests
import pandas as pd
import re
import os
from bs4 import BeautifulSoup
import urllib.request


def get_flowstate_episodes():

    headers = {
        'authority': 'www.flowstate.fm',
        'sec-ch-ua': '"Google Chrome";v="87", "\\"Not;A\\\\Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36',
        'accept': '*/*',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.flowstate.fm/?sort=community',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': '__cfduid=dee264ec9fe48d6f92f4d3d04a08872711608540634; ajs_anonymous_id=%2267ec80dc-dfbd-4d38-b215-ad63f6e21990%22; connect.sid=s%3Ay5t_8VnDKK9cWORJRqLv6b409tk4aVO6.QJVERYniXuqc0sDqZttfeOPa9ZiJcCNEvZYJEIFu9JQ; intro_popup_last_hidden_at=2020-12-21T08:50:37.925Z',
        'if-none-match': 'W/"4925-TMPhAWZhblWFsFPypzTLr7CRVDA"',
    }

    response = requests.get('https://www.flowstate.fm/api/v1/archive?sort=new', headers=headers)
    x = response.json()

    episodes = []
    for i in range(len(x)):
        episodes.append(x[i]['slug'])

    return episodes


def get_playlists_for_episode(e):

    headers = {
        'authority': 'www.flowstate.fm',
        'sec-ch-ua': '"Google Chrome";v="87", "\\"Not;A\\\\Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36',
        'accept': '*/*',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.flowstate.fm/p/laraaji',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': '__cfduid=dee264ec9fe48d6f92f4d3d04a08872711608540634; ajs_anonymous_id=%2267ec80dc-dfbd-4d38-b215-ad63f6e21990%22; connect.sid=s%3Ay5t_8VnDKK9cWORJRqLv6b409tk4aVO6.QJVERYniXuqc0sDqZttfeOPa9ZiJcCNEvZYJEIFu9JQ; intro_popup_last_hidden_at=2020-12-30T08:04:52.166Z',
    }

    response = requests.get(f'https://www.flowstate.fm/api/v1/posts/{e}', headers=headers)
    y = response.json()
    soup = BeautifulSoup(y['body_html'], "html.parser")
    found = False
    for link in soup.findAll('a'):
        href = link.get('href')
        m = re.match('(https://open.spotify.com/album/.*)', href)
        if m:
            print(f"{e}: {m.groups()[0]}")
            found = True

    if (found == False):
        print(f"No spotify playlist for episode {e}")



if __name__ == '__main__':

    episodes = get_flowstate_episodes()
    #print(episodes)

    for e in episodes:
        get_playlists_for_episode(e)