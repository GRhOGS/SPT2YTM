> [!CAUTION]
> This Project is no longer under development since YouTube Music now [officially endorses](https://support.google.com/youtubemusic/answer/14729358) the use of [TuneMyMusic](https://www.tunemymusic.com/?mode=ytm&fsource=spotify) (free with YT Premium) to transfer Playlists from Spotify to YT Music. This service seems to work quite good for its purpose and does not have the same technical restrictions this project has in regards to the amount of playlists you can create per day.

# SPT2YTM - Spotify to YouTube Music Playlist Converter
This project provides a way to migrate all of your playlists from Spotify to YouTube Music. Although it is not as user friendly as other online tools that advertise to do the same job, it does not[*](#limitations) have a limit on how many songs you can convert.

## Table of Contents

- [Installation](#installation)
    - [Windows](#windows)
    - [Linux](#linux)
- [Quick start guide](#quick-start-guide)
    - [YouTube Music API tokens](#youtube-music)
    - [Spotify API tokens](#spotify)
- [Rerunning SPT2YTM](#rerunning-spt2ytm)
- [Limitations](#limitations)
- [Dependencies](#dependencies)

## Installation

### Windows

You **only** need to download the file `converter.exe` (click [here](https://github.com/GRhOGS/SPT2YTM/raw/main/dist/converter.exe) to download) from the folder `dist/`. Make sure to put it in its own folder before running it, as it generates some extra files. Please make sure to read the [Quick start guide](#quick-start-guide) before running SPT2YTM, as it gives you a better idea on how to use it.

If you don't trust the executable, follow along with the linux section. If you additionaly want to create your own executable, install [pyinstaller](https://pyinstaller.org/en/stable/installation.html), open a command prompt, navigate to the folder containing `converter.py` and run the command:

```bash
pyinstaller -c -F -i media/icon.ico --collect-all ytmusicapi converter.py
```

### Linux

1. Download this github project.

2. Install [spotipy](https://spotipy.readthedocs.io/en/latest/#installation) :
    
```bash
pip install spotipy --upgrade
```

3. Install [ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/index.html) :
    
```bash
pip install ytmusicapi
```

4. Navigate to the download directory of this repo and run

```bash
python3 converter.py
```

## Quick start guide

To use SPT2YTM, simply open `converter.exe` if you're on windows, or run `python3 converter.py` once you completed all steps for the linux installation. When SPT2YTM runs for the first time, you need to provide API tokens for both YouTube Music and Spotify. Keep in mind, to never share these tokens with people you don't trust, because they basically function as a username/password combination for your Spotify and YouTube accounts. Here is how you get them:

### YouTube Music
When SPT2YTM asks you for your YouTube api tokens and a browser window pops up, just follow the instructions in the browser and select the YouTube account you want to transfer your music to. After it tells you to "Continue on your device", you can close the browser tab and go back into the command prompt, **proceeding by pressing the enter key**.

### Spotify

After getting your YouTube tokens, SPY2YTM will ask you to provide a Spotify client id and client secret. The process for getting those tokens from spotify is a bit tricky, here is how to get them: 

First, in your browser, you need to navigate to the <a href="https://developer.spotify.com/dashboard" target="_blank">Spotify developer dashboard</a>. Once you're logged into your Spotify account and on the dashbaord, click the "Create App" button on the top right. You then need to enter some details:

- App name: get my music
- App description: gets my music
- Redirect URI: `http://localhost:3000`
- Web API [x]

You can set the apps name and description as whatever you want, it's not important what you call them, as long as they're not left empty. The important parts are that you copy and paste the Redirect URI `http://localhost:3000` and that you check the `Web API` option in the "Which API/SDKs are you planning to use?" section.

After creating the app, it takes you to its dashboard. Here you need to click on the "Settings" button on the top right. On this page you can find the client id and client secret, which SPT2YTM needs. To view the client secret click the "View client secret" button, just under the client id field. Now just copy and paste both of them one by one into the command prompt and SPY2YTM should start doing its magic. Note, that you can paste content into the command prompt by simply right clicking inside of it, or pressing ctrl + v.

If SPT2YTM crashes or doesn't function correctly at this point, check if the client id and client secret are stored correctly. You can check and edit them in the file `credentials.json`, which will be created in the same folder as the executable, when you run it for the first time.

## Rerunning SPT2YTM

If you want to rerun the searches or add the playlists again, simply delete all `.json` files except `oauth.json` and `credentials.json`, since those contain your API Tokens. Note, that fetching from Spotify gets skipped, if a file `remaining.json` or `yt_playlists.json` exists.

## Limitations
YouTube Music allows all users to only create **25 playlists every 6 hours**. Because of that, SPT2YTM creates a file called `remaining.json`, once the maximum number of playlists are created. Once the 6 hours are passed, just run SPT2YTM again and it will create the remaining playlists automatically, without going through the lengthy process of fetching all the songs again.

The way of transfering a song from Spotify to YouTube Music still has room for improvement, because it simply searches for the songs name + artist and picks the first result. 95% of the time it gets the right song, but it can happen that the song just doesn't exist on YouTube Music. In that case, it gets the next best song fitting the name + artist criteria.

## Dependencies
- Python 3.11+
- spotipy 
- ytmusicapi
