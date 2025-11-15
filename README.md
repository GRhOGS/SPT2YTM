> [!CAUTION]
> This Project is no longer under development since YouTube Music now [officially endorses](https://support.google.com/youtubemusic/answer/14729358) the use of [TuneMyMusic](https://www.tunemymusic.com/?mode=ytm&fsource=spotify) (free with YT Premium) to transfer Playlists from Spotify to YT Music. This service seems to work quite good for its purpose and does not have the same technical restrictions this project has in regards to the amount of playlists you can create per day.

# SPT2YTM - Spotify to YouTube Music Playlist Converter

SPT2YTM helps you migrate your entire Spotify library—playlists and liked tracks—to YouTube Music, with no limits on the number of songs. While it’s a command-line tool, this guide will walk you through installation and setup step by step.

---

## Table of Contents

- [Installation](#installation)
  - [Windows](#windows)
  - [Linux & macOS](#linux--macos)
- [Quick Start](#quick-start)
  - [YouTube Music Credentials](#youtube-music-credentials)
  - [Spotify Credentials](#spotify-credentials)
- [Running & Rerunning](#running--rerunning)
- [Error Margin & Troubleshooting](#error-margin--troubleshooting)
- [Advanced: Custom YouTube Music Headers](#advanced-custom-youtube-music-headers)
- [Dependencies](#dependencies)

---

## Installation

Clone or download this repo, then install dependencies.

```bash
git clone https://github.com/GRhOGS/SPT2YTM.git
cd SPT2YTM
pip install -r requirements.txt      # or: pip3 install -r requirements.txt
```

> **Note:** The main script is `converter.py`. If you prefer a standalone exe on Windows, see below.

### Windows
1. Download the pre-built `converter.exe` from the [dist folder](https://github.com/GRhOGS/SPT2YTM/raw/main/dist/converter.exe).
2. Place `converter.exe` in a dedicated folder— it will generate JSON files alongside it.
3. Double-click `converter.exe` and follow the prompts.

_To build your own executable:_
```bash
pip install pyinstaller
pyinstaller -c -F -i media/icon.ico --collect-all ytmusicapi converter.py
```

### Linux & macOS

After cloning and installing dependencies:
```bash
python3 converter.py
```  
or, if your default `python` is 3.x:
```bash
python converter.py
```

---

## Quick Start

1. **Run the converter**:
   ```bash
   python converter.py
   ```
2. **Follow on-screen prompts** for YouTube Music and Spotify credentials (tokens).
3. Sit back while your playlists transfer with progress bars!

### YouTube Music Credentials

When prompted, a browser window will open asking you to grant access:
1. Log in to your desired YouTube account.
2. Allow SPT2YTM to manage your music library.
3. When you see “Continue on your device,” close the tab and return to the terminal.

Your OAuth tokens store in `browser.json` for future runs.

### Spotify Credentials

SPT2YTM needs a **Client ID** and **Client Secret**. To obtain them:
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Click **Create an App**.
   - **Name**: any name you like
   - **Description**: your choice
   - **Redirect URI**: `http://127.0.0.1:3000/` (note the trailing slash)
   - Check **Web API** in the API options.
3. In your new app, click **Settings** (top right).
4. Copy **Client ID** and then click **Show Client Secret** to copy it.
5. Paste both values when prompted in the terminal.

They’ll save in `credentials.json` for reuse.

---

## Running & Rerunning

- **First run**: fetches Spotify playlists, searches YouTube Music IDs, and creates new YTM playlists.
- **Subsequent runs**: skips fetching if `spotify_playlists.json` exists; skips creation if `yt_playlists.json` or `remaining.json` exists.
- To **start over**, delete all generated `*.json` files except `browser.json` and `credentials.json`.


---

## Error Margin & Troubleshooting

- **Song matching** uses “track name + artist” search on YouTube Music. ~95% accuracy, but some tracks may be missing or mismatch.
- Missing tracks list exports to `not_found_songs.json`.
- If you hit the YouTube Music limit (25 playlists per 6 hours), the script stops and saves remaining playlists to `remaining.json`. Rerun after 6 hours to complete.

---

## Advanced: Custom YouTube Music Headers

To improve search reliability, you can extract your browser’s YouTube Music headers:
1. Open [music.youtube.com](https://music.youtube.com) and **log in**.
2. Press **F12** (or right-click → Inspect) to open Developer Tools.
3. Go to the **Network** tab and refresh the page.
4. In the filter box, type `get_search_suggestions`.
5. Click the matching request, then **Copy → Copy Request Headers** (not response).
6. Paste the raw headers JSON into `headers_auth.json` in this folder.

SPT2YTM will automatically use them if present.

---

## Dependencies

- Python 3.11+
- `spotipy`
- `ytmusicapi`
- `tqdm`

Install all via:
```bash
pip install -r requirements.txt
```

---

Enjoy seamless migration of your favorite tunes from Spotify to YouTube Music! If you encounter issues, please open an issue on GitHub.
