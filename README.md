# hos_scraper / Spotify playlist generators

Utilities for creating Spotify playlists or Spotify link lists from music sources you follow: Hearts of Space, Echoes, XM radio/xmplaylist, SomaFM, Radio Paradise, KINK-FM, Flow State, Coke Studio India, Putumayo, NTS, Songlines, and artist/title lists.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp spotify.cfg.template spotify.cfg
```

Edit `spotify.cfg`:

```ini
[spotify]
username=<your spotify username/user id>
client_id=<spotify app client id>
client_secret=<spotify app client secret>
redirect_uri=http://127.0.0.1:8888/callback
```

The first playlist-creation run opens Spotify authorization in a browser. The local loopback redirect `http://127.0.0.1:8888/callback` has been tested with Spotify. Paste the redirected URL back into the terminal when prompted, if requested.

Most scripts have a validation mode:

- `--dry-run`: scrape/list source data only; no Spotify use unless the source itself is Spotify.
- `--match-only`: search Spotify and print matches; do not create playlists.
- `--no-overwrite`: keep/reuse an existing playlist instead of replacing it.

## Scraper categories

| Category | Scraper | Source type | Matching style | Playlist output |
| --- | --- | --- | --- | --- |
| Ambient / space music | `create_spotify_playlist_for_hos_episode.py` | Hearts of Space episode API | Fuzzy Spotify search | One playlist per HOS episode |
| Ambient / chill / electronic | `create_spotify_playlist_for_echoes.py` | Echoes playlist page tables | Fuzzy Spotify search | One playlist per Echoes program, or one combined `Echoes Recent` playlist |
| Ambient / chill / electronic | `create_spotify_playlist_for_somafm.py` | SomaFM recent song history | Fuzzy Spotify search | One playlist per SomaFM channel |
| Eclectic radio / world / rock | `create_spotify_playlist_for_radio_paradise.py` | Radio Paradise playlist API | Fuzzy Spotify search | One playlist per RP channel |
| Portland AAA radio / Lights Out recent capture | `create_spotify_playlist_for_kink.py` | KINK-FM recent played API | Fuzzy Spotify search | KINK-FM Lights Out capture playlist |
| Portland new age / instrumental history | `create_spotify_playlists_for_kink_lights_out.py` | MusicBrainz KINK Lights Out compilation series | Fuzzy Spotify search | One playlist per compilation, or combined |
| SiriusXM radio | `create_spotify_playlist_for_xm_channel.py` | xmplaylist JSON API | Direct Spotify track IDs | One playlist per XM station |
| South Asian / Indian / folk-pop | `create_spotify_playlists_for_coke_studio_india.py` | Wikipedia Coke Studio tables | Fuzzy Spotify search | One playlist per release year |
| World music | `create_spotify_playlist_for_putumayo.py` | Spotify Putumayo album search | Direct Spotify album tracks | Putumayo playlist, optionally by year |
| World music / magazine CDs | `create_spotify_playlists_for_songlines.py` | MusicBrainz Songlines Top of the World releases | Fuzzy Spotify search | One playlist per issue, per year, or combined |
| World music / magazine CDs | `create_spotify_playlist_for_songlines_early_manual.py` | Manual CSV for early Songlines issues #1-24 | Fuzzy Spotify search | Combined early Songlines playlist, or by year/issue |
| Ambient / global / experimental radio | `create_spotify_playlist_for_nts.py` | NTS public episode/tracklist API | Fuzzy Spotify search | Combined recent NTS ambient/experimental and global playlists |
| Flow / ambient recommendations | `create_spotify_playlist_from_flowstate.py` | Flow State/Substack posts | Direct Spotify links | Link list only, no playlist yet |
| Artist collections | `create_spotify_playlist_for_artist.py` | Spotify artist search | Spotify search | Artist playlist |
| Artist collections from CSV | `create_spotify_playlist_for_artist_v2.py` | CSV titles + Spotify search | Spotify search | Artist/title-list playlist |

## Playlist count guide

The exact number depends on which variable inputs you run: HOS episode IDs, Echoes URLs, artist names, Putumayo years, etc. These are the predictable counts from the current scripts:

| Script / command pattern | Playlists created |
| --- | ---: |
| `create_spotify_playlist_for_hos_episode.py <episode_id>` | 1 per episode |
| `create_spotify_playlist_for_echoes.py` | 1 by default; `--latest N` creates N; `--latest N --combined` creates 1 rolling `Echoes Recent` playlist |
| `create_spotify_playlist_for_somafm.py --recommended` | 4 |
| `create_spotify_playlist_for_radio_paradise.py --channel <channel>` | 1 per channel; 4 if you run `main`, `mellow`, `rock`, and `world` |
| `create_spotify_playlist_for_kink.py` | 1 recent Lights Out capture playlist |
| `create_spotify_playlists_for_kink_lights_out.py` | 11, or 1 if using `--combined` |
| `create_spotify_playlist_for_xm_channel.py --recommended` | 16 |
| `create_spotify_playlists_for_coke_studio_india.py` | 8 currently: 2011, 2012, 2013, 2015, 2023, 2024, 2025, 2026 |
| `create_spotify_playlist_for_putumayo.py` | 1; plus 1 per `--year` run |
| `create_spotify_playlists_for_songlines.py --by-year` | Up to 22 currently found in MusicBrainz, 2004–2025 |
| `create_spotify_playlists_for_songlines.py` | Up to 130 currently found issue playlists, issue 25–209 with gaps |
| `create_spotify_playlist_for_songlines_early_manual.py` | 1 combined early playlist by default, or one per CSV year/issue |
| `create_spotify_playlist_for_nts.py` | 2 by default: ambient/experimental recent and global recent |
| `create_spotify_playlist_from_flowstate.py` | 0; prints Spotify links only |
| `create_spotify_playlist_for_artist.py "<artist>"` | 1 per artist |
| `create_spotify_playlist_for_artist_v2.py "<artist>" songs.csv` | 1 per artist/CSV run |

If you run the main curated/recommended set once — XM recommended, SomaFM recommended, all 4 Radio Paradise channels, Coke Studio all years, KINK Lights Out historical volumes, KINK recent capture, and Putumayo all-years — you would create **45 playlists**.

If you use a single combined KINK Lights Out compilation playlist instead of 11 volume playlists, that same set would create **35 playlists**.

Adding Songlines by year would add up to **22** more playlists from the MusicBrainz coverage currently found, bringing the curated set to **67** playlists, or **57** if using combined KINK Lights Out.

These totals exclude variable one-off playlists such as HOS episodes, Echoes episodes, artist playlists, Putumayo year-specific playlists, and Songlines per-issue playlists.

## Organizing playlists in Spotify

Spotify's desktop app supports playlist folders for manual organization. Use the desktop app and create folders from the playlist sidebar, then drag playlists into them. Suggested folders:

```text
Ambient / Space
  HOS_...
  Echoes Recent
  Echoes: ...
  NTS Ambient Experimental Recent
  NTS Global Recent
  SomaFM Drone Zone
  SomaFM Deep Space One

Radio
  XM ...
  Radio Paradise ...
  KINK-FM Lights Out

World / Global
  Putumayo World Music
  Coke Studio India ...
  Songlines Top of the World
  Songlines Early Issues
  Songlines ...

Artists
  APS Best of ...
```

Important limitation: Spotify's public Web API does **not** expose playlist-folder management, so these scripts can create/update playlists but cannot automatically put them into folders. Folder organization has to be done manually in Spotify Desktop.

## Hearts of Space

Source: public HOS JSON endpoint, e.g.:

```text
https://api.hos.com/api/v1/programs/1213
```

HOS gives title/artist text, so Spotify matching is fuzzy. The scraper tries full artist, split collaborators, track-only fallback, then scores candidates.

```bash
python create_spotify_playlist_for_hos_episode.py 1213 --dry-run
python create_spotify_playlist_for_hos_episode.py 1213 --match-only --min-score 0.62
python create_spotify_playlist_for_hos_episode.py 1213
```

Playlist name:

```text
HOS_1213: PROGRESSIVE AMBIENT
```

## Echoes with John Diliberto

Source: Echoes playlist pages with start time / artist / song / album tables.

Latest playlist:

```bash
python create_spotify_playlist_for_echoes.py --dry-run
python create_spotify_playlist_for_echoes.py --match-only --min-score 0.62
python create_spotify_playlist_for_echoes.py
```

Latest N playlists:

```bash
python create_spotify_playlist_for_echoes.py --latest 3 --dry-run
```

Rolling combined recent playlist, recommended to avoid playlist sprawl:

```bash
python create_spotify_playlist_for_echoes.py --latest 10 --combined --dry-run
python create_spotify_playlist_for_echoes.py --latest 10 --combined --min-score 0.55
```

Combined playlist name:

```text
Echoes Recent
```

Specific playlist page:

```bash
python create_spotify_playlist_for_echoes.py "https://echoes.org/2026/07/15/wednesday-july-15-2026-echoes-program-2628c/"
```

Playlist name:

```text
Echoes: <program title>
```

## Batch radio runner

To create/update the **curated radio stations selected earlier** — 16 XM stations, 4 SomaFM channels, and 4 Radio Paradise channels:

```bash
source .venv/bin/activate
./run_radio_playlists.sh
```

Dry-run first:

```bash
DRY_RUN=1 ./run_radio_playlists.sh
```

Tunable settings:

```bash
XM_DAYS=30 SOMAFM_LIMIT=100 RP_LIMIT=100 MIN_SCORE=0.55 ./run_radio_playlists.sh
```

What it does:

- creates one playlist for each selected XM station:
  `siriusxmchill`, `watercolors`, `spa`, `steveaokisremixradio`, `astateofarmin`, `luna`, `bpm`, `diplosrevolution`, `studio54radio`, `radiomonaco`, `utopia`, `expertsonlyradio`, `oneworldradio`, `escape`, `realjazz`, `siriusxmdhamaka`
- creates one playlist for each selected SomaFM channel:
  `dronezone`, `groovesalad`, `spacestation`, `deepspaceone`
- creates Radio Paradise playlists for `main`, `mellow`, `rock`, and `world`

This creates **24 radio playlists** total.

## XM radio / xmplaylist

Source: xmplaylist JSON API. XM matching is direct because xmplaylist returns Spotify track IDs.

One station:

```bash
python create_spotify_playlist_for_xm_channel.py siriusxmchill --days 30 --dry-run
python create_spotify_playlist_for_xm_channel.py siriusxmchill --days 30
```

Multiple stations:

```bash
python create_spotify_playlist_for_xm_channel.py siriusxmchill watercolors spa --days 30
```

Recommended set:

```bash
python create_spotify_playlist_for_xm_channel.py --recommended --days 30 --dry-run
python create_spotify_playlist_for_xm_channel.py --recommended --days 30
```

Recommended currently includes:

```text
siriusxmchill
watercolors
spa
steveaokisremixradio
astateofarmin
luna
bpm
diplosrevolution
studio54radio
radiomonaco
utopia
expertsonlyradio
oneworldradio
escape
realjazz
siriusxmdhamaka
```

Playlist name:

```text
XM <station_slug>
```

XM playlists are based on a rolling play-count window. With `--days 30`, expect small changes daily; weekly updates are a good default, daily if you want close tracking.

## SomaFM

Source: SomaFM `songhistory.html` pages. These are recent-history playlists, not long-term archives.

Recommended ambient/chill channels:

```text
dronezone       Drone Zone
groovesalad     Groove Salad
spacestation    Space Station Soma
deepspaceone    Deep Space One
```

Validate:

```bash
python create_spotify_playlist_for_somafm.py --recommended --limit 100 --dry-run
python create_spotify_playlist_for_somafm.py dronezone --limit 100 --match-only
```

Create/update playlists:

```bash
python create_spotify_playlist_for_somafm.py --recommended --limit 100
python create_spotify_playlist_for_somafm.py dronezone groovesalad --limit 100
```

Playlist names:

```text
SomaFM Drone Zone
SomaFM Groove Salad
SomaFM Space Station Soma
SomaFM Deep Space One
```

## Radio Paradise

Source: Radio Paradise public playlist API. This is recent playlist history.

Channels:

```text
main
mellow
rock
world
```

Validate:

```bash
python create_spotify_playlist_for_radio_paradise.py --channel main --limit 100 --dry-run
python create_spotify_playlist_for_radio_paradise.py --channel world --match-only
```

Create/update:

```bash
python create_spotify_playlist_for_radio_paradise.py --channel main --limit 100
python create_spotify_playlist_for_radio_paradise.py --channel mellow --limit 100
```

Playlist names:

```text
Radio Paradise Main
Radio Paradise Mellow
Radio Paradise Rock
Radio Paradise World
```

## KINK-FM Lights Out

There are two KINK/Lights Out tools:

### Historical compilation albums

Source: MusicBrainz release-group series `KINK Lights Out`. This covers the **11 benefit compilation albums**, not the complete nightly radio-show logs.

The compilation series found is:

```text
1   1985  Lights Out
2   1988  Lights Out II
3   1991  Lights Out III
4   1993  Lights Out IV
5   1995  Lights Out V
6   1997  Lights Out VI
7   1999  Lights Out VII
8   2002  Lights Out VIII
9   2005  Lights Out Nine
10  2006  Lights Out 10
11  2008  Lights Out 11
```

Validate:

```bash
python create_spotify_playlists_for_kink_lights_out.py --dry-run
python create_spotify_playlists_for_kink_lights_out.py --volume 1 --dry-run
python create_spotify_playlists_for_kink_lights_out.py --combined --match-only
```

Create one playlist per volume:

```bash
python create_spotify_playlists_for_kink_lights_out.py
```

Create one combined playlist:

```bash
python create_spotify_playlists_for_kink_lights_out.py --combined
```

Playlist names:

```text
KINK Lights Out 01 - 1985
KINK Lights Out 02 - 1988
...
KINK Lights Out Compilations
```

### Recent feed capture

Source: KINK-FM recently played page / AmperWave now-playing API.

KINK does not appear to expose a complete historical Lights Out show playlist archive. The recent API is a global recently-played feed. It can return up to roughly a few days of plays by increasing `--limit`, and you can filter by local time window.

Validate recent overnight/Lights-Out-style plays, for example 10pm-1am Pacific:

```bash
python create_spotify_playlist_for_kink.py --limit 1000 --start-hour 22 --end-hour 1 --dry-run
python create_spotify_playlist_for_kink.py --limit 1000 --start-hour 22 --end-hour 1 --match-only
```

Create/update:

```bash
python create_spotify_playlist_for_kink.py --limit 1000 --start-hour 22 --end-hour 1
```

Playlist name:

```text
KINK-FM Lights Out
```

## NTS

Source: NTS public v2 API for recent guest episodes and episode tracklists.

The script currently supports two presets:

```text
ambient  -> NTS Ambient Experimental Recent
global   -> NTS Global Recent
```

By default it creates/updates both playlists by scanning recent guest episodes and selecting episodes whose genre tags match the preset.

Validate:

```bash
python create_spotify_playlist_for_nts.py --dry-run
python create_spotify_playlist_for_nts.py --preset ambient --latest-episodes 5 --dry-run
python create_spotify_playlist_for_nts.py --preset global --latest-episodes 10 --match-only --min-score 0.55
```

Create/update both recommended NTS playlists:

```bash
python create_spotify_playlist_for_nts.py --latest-episodes 10 --min-score 0.55
```

Create/update one preset:

```bash
python create_spotify_playlist_for_nts.py --preset ambient --latest-episodes 10 --min-score 0.55
python create_spotify_playlist_for_nts.py --preset global --latest-episodes 10 --min-score 0.55
```

Playlist names:

```text
NTS Ambient Experimental Recent
NTS Global Recent
```

Notes:

- NTS tracklists include obscure, unreleased, DJ, and Bandcamp-only music, so Spotify match rates vary.
- The preset logic is tag-based and scans recent guest episodes; adjust `--latest-episodes` and `--scan-limit` if you want more/less material.

## Flow State

Source: Flow State/Substack post API. Flow State usually links directly to Spotify albums/playlists/tracks, so no fuzzy matching is needed.

This script currently prints Spotify links; it does not create a playlist.

```bash
python create_spotify_playlist_from_flowstate.py
python create_spotify_playlist_from_flowstate.py --limit 5
```

## Coke Studio India / Bharat / Tamil

Source: Wikipedia song tables for:

- Coke Studio @ MTV seasons 1-4
- Coke Studio Bharat
- Coke Studio Tamil

The script groups songs by release year and creates one playlist per year.

Coke Studio India/Bharat/Tamil currently has releases in **8 calendar years**:

```text
2011, 2012, 2013, 2015, 2023, 2024, 2025, 2026
```

Validate scrape:

```bash
python create_spotify_playlists_for_coke_studio_india.py --dry-run
```

Validate Spotify matches only:

```bash
python create_spotify_playlists_for_coke_studio_india.py --match-only --min-score 0.62
python create_spotify_playlists_for_coke_studio_india.py --year 2023 --match-only
```

Create/update playlists for all years:

```bash
python create_spotify_playlists_for_coke_studio_india.py
```

Create/update a specific year:

```bash
python create_spotify_playlists_for_coke_studio_india.py --year 2024
```

Playlist names:

```text
Coke Studio India 2011
Coke Studio India 2012
...
```

## Songlines Top of the World

Source: MusicBrainz releases titled `Songlines: Top of the World <issue>`.

Important historical note:

- The Songlines Top of the World CD series began with **Spring 1999, issue #1**.
- The retail cover-CD run appears to be **Spring 1999 through January/February 2024, issue #194**.
- From March 2024 onward, the CD/download appears to continue for qualifying subscribers/digital subscribers.
- MusicBrainz currently gives usable structured tracklists from approximately **issue #25 / 2004** onward, with gaps.
- The old issues **#1-24, 1999-2003** are important but not yet covered by the current structured MusicBrainz source.

Validate a known issue:

```bash
python create_spotify_playlists_for_songlines.py --issue 25 --dry-run
```

Validate discovered MusicBrainz coverage:

```bash
python create_spotify_playlists_for_songlines.py --dry-run
```

Create one playlist per issue found in MusicBrainz:

```bash
python create_spotify_playlists_for_songlines.py
```

Create one playlist per year:

```bash
python create_spotify_playlists_for_songlines.py --by-year
```

Create one combined playlist:

```bash
python create_spotify_playlists_for_songlines.py --combined
```

Playlist names:

```text
Songlines Top of the World 25
Songlines Top of the World 2004
Songlines Top of the World
```

### Songlines early-years research

The missing/high-priority target is:

```text
Songlines Top of the World issues #1-24
Date range: Spring 1999-2003
Especially: Central and South American tracks from 1999
```

Sources investigated so far:

- MusicBrainz: structured and usable from issue #25/2004 onward; early issues not found.
- Songlines current website: current issue pages only; no public early issue track tables found yet.
- Exact Editions: has searchable page images/OCR for Songlines, but issue-list/plaintext endpoints are protected by WAF. Search pages can reveal some issue/page hits, but not clean full tracklists yet.
- Discogs: likely useful for CD tracklists, but direct scraping is Cloudflare-protected from this environment.
- Internet Archive: no useful Songlines Top of the World issue/CD tracklists found yet.

Potential next steps for early Songlines:

1. Manually search Discogs in a browser for `Songlines Top of the World 1`, `Songlines Top of the World 2`, etc.
2. Use Exact Editions search/browser access to locate issue #1 pages around the CD listing.
3. If you can export, photograph, OCR, or paste early CD tracklists, add them as CSV files and feed them to a Songlines CSV importer.
4. Search by suspected regions/artists: Brazil, Cuba, Peru, Argentina, Colombia, Venezuela, Mexico, Susana Baca, Rubén González, Orishas, Virginia Rodrigues, Gilberto Gil, Caetano Veloso, etc.

A manual CSV importer is available for these early issues:

```bash
python create_spotify_playlist_for_songlines_early_manual.py --dry-run
python create_spotify_playlist_for_songlines_early_manual.py --min-score 0.55
```

Default CSV path:

```text
data/songlines_early_issues.csv
```

CSV format:

```csv
issue,year,artist,title,album,source
1,1999,Artist Name,Track Name,Songlines Top of the World 1,discogs/back-cover/etc
```

Playlist names:

```text
Songlines Early Issues
Songlines Early <year>                         # with --by-year
Songlines Top of the World Early Issue <issue> # with --by-issue
```

The seed CSV currently contains only the confirmed/known early-era candidates below, so it is a starting point rather than complete issue #1-24 coverage:

```text
Jimmy Bosch - Impacto Tendremos
Virgínia Rodrigues - Male Debale
Orishas - 537 C.U.B.A
Toto Bissainthe - Dey
Susana Baca - La Macorina
Rubén González - Choco's Guajira
Cheo Hurtado - Gavilan
```

## Putumayo World Music

Source: Spotify album search. The script searches for Putumayo albums, collects album tracks, and creates a Putumayo playlist.

Because the source is Spotify itself, even `--dry-run` requires valid Spotify credentials.

```bash
python create_spotify_playlist_for_putumayo.py --dry-run
python create_spotify_playlist_for_putumayo.py
```

Limit to a release year:

```bash
python create_spotify_playlist_for_putumayo.py --year 2004 --dry-run
python create_spotify_playlist_for_putumayo.py --year 2004
```

Playlist names:

```text
Putumayo World Music
Putumayo 2004
```

## Artist-specific scripts

Search Spotify by artist:

```bash
python create_spotify_playlist_for_artist.py "Shailendra Singh"
```

CSV/title-list version:

```bash
python create_spotify_playlist_for_artist_v2.py "Shailendra Singh" songs.csv
```

The CSV file should have one song title per line with a header named `Song`.

Playlist name:

```text
APS Best of <artist name>
```

These older artist scripts may produce duplicates or occasional songs from similarly named artists.

## Remaining / not yet processed

High priority:

1. **Songlines early issues #1-24 (1999-2003)**
   - Goal: find complete tracklists, especially Central/South America / Caribbean tracks from 1999.
   - Current structured source, MusicBrainz, starts usefully at issue #25 / 2004.
   - Need another source: Discogs browser lookup, Exact Editions OCR/browser access, scans, pasted tracklists, or CSV.

2. **Flow State playlist creation**
   - Current script extracts Spotify album/playlist/track links only.
   - Next step: expand album links into track IDs and create playlists.

3. **KCRW Eclectic 24 / Morning Becomes Eclectic**
   - KCRW web app/API was not straightforward from this environment.
   - Needs further API discovery or an alternate source.
   - Suggested path: open the Eclectic 24 playlist page in a browser, inspect Network/XHR requests, and copy the JSON/cURL request containing artist/title rows.

4. **NPR Tiny Desk**
   - Not yet implemented.
   - Needs parsing of recent Tiny Desk pages and mapping performances to Spotify tracks.

5. **Bandcamp Daily**
   - Not yet implemented.
   - Harder because Bandcamp recommendations do not always map cleanly to Spotify.

6. **Master batch runner**
   - Not yet implemented.
   - Would run selected playlist sets from one config file, e.g. XM recommended, SomaFM recommended, Radio Paradise, Coke Studio, KINK Lights Out, Putumayo, Songlines.

7. **Match reports**
   - Not yet implemented.
   - Useful output: matched, low-confidence, unmatched CSVs for fuzzy-match sources.

## Spotify credentials

The scripts normally read `spotify.cfg` in this repo. There is also a Spotify MCP config on this machine at:

```text
~/spotify-mcp-server/spotify-config.json
```

That file appears to contain Spotify client credentials and OAuth tokens. Do not paste those values into chat. A safe next step is to either:

1. copy `clientId`, `clientSecret`, and `redirectUri` into `spotify.cfg`, adding your Spotify username/user id, or
2. update the scripts to automatically fall back to the MCP config without printing secrets.

Spotify playlist folders can only be managed manually in Spotify Desktop; the public Spotify Web API does not support creating or moving playlists into folders.
