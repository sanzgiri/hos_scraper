# hos_scraper (Hearts of Space Scraper)
This repo contains code that generates a Spotify playlist from the tracks in a Hearts of Space episode. It works by scraping the playlist and finding matching tracks in the Spotify collection. Apart from Hearts of Space, there are python scripts that can be used to extract songs from specific artists, XM channels and flowstate

## Setup
* Create a conda 3.9 env and install packages listed in requirements.txt
* Copy spotify.cfg.template to spotify.cfg and set the Spotify creds
* The first time you run these scripts you will be prompted to enter the auth token. This will be the URL brought up in a browser window.
  
## Usage
* hos-scraper:
  ```
  python create_spotify_playlist_for_hos_episode.py <episode_id>
  ```
    You can get episode ids from https://www.hos.com/home. Listed as PGM nnnn. The playlist is named "HOS_nnnn: <episode_title>"

* XM-scraper
  ```
  python create_spotify_playlist_for_xm_channel.py <xm_channel>
  ```

    Here <xm_channel> is the name of the channel in lower case, with no spaces. e.g. channel "A State of Armin" has to be specified as "astateofarmin". The channel created is "XM astateofarmin"

* Flowstate
  ```
  python create_spotify_playlist_from_flowstate.py
  ```
  This actually does not create a playlist - it lists the spotify albums referenced in recent Flowstate episodes and you can add those albums to your saved lists

* Artist-specific
   ```
   python create_spotify_playlist_for_artist.py "<artist name>"
   ```
   where <artist name> can have spaces e.g. "Shailendra Singh"
   Creates a playlist called "APS Best of <artist name>
   There will likely be many duplicates and occassional songs from artists with similar names :-) 

   ```
   python create_spotify_playlist_for_artist_v2.py "<artist name>" <csv_file>
   ```
   where <artist name> can have spaces e.g. "Shailendra Singh"
   and <csvfile> is a file that has a list of song titles from the artist, one per line, with a header called "Song". These titles could be scraped, say from Wikipedia. 
   Creates a playlist called "APS Best of <artist name>
   There will likely be many duplicates and occassional songs from artists with similar names :-) 