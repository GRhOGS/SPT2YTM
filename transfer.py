import os
import json
from time import time, sleep
from functools import reduce

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from tqdm import tqdm

# ---------- CONFIG & CONSTANTS ----------
SPOTIFY_SCOPE = "user-library-read playlist-read-private"
BROWSER_FILE = "browser.json"
CREDENTIALS_FILE = "credentials.json"
SPOTIFY_PLAYLISTS_FILE = "spotify_playlists.json"
YT_PLAYLISTS_FILE = "yt_playlists.json"
NOT_FOUND_FILE = "not_found_songs.json"
REMAINING_FILE = "remaining.json"
LIKED_CACHE_FILE = "liked_songs_cache.json"
YT_ID_CACHE_FILE = "yt_id_cache.json"
COMPLETED_PLAYLISTS_FILE = "completed_playlists.json"

# ---------- UTILS ----------
def load_json(path, default=None):
    if os.path.isfile(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def try_request(fn, retries=5, delay=2):
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            print(f"[Retry {attempt+1}/{retries}] Error: {e}")
            if attempt < retries - 1:
                sleep(delay * (attempt + 1))
            else:
                raise e

# ---------- SPOTIFY HELPERS ----------
def get_all_spotify_songs_from_query_result(items):
    songs = []
    for item in items:
        track = item.get("track") or {}
        name = track.get("name", "")
        artists = track.get("artists", [])
        title = name + " " + " ".join(a["name"] for a in artists)
        if title.strip():
            songs.append(title)
    return songs

def find_all_spotify_songs_in_playlist(playlist_id, sp):
    songs, offset = [], 0
    with tqdm(desc="Songs in playlist", unit="song", leave=False) as pbar:
        while True:
            items = try_request(lambda: sp.playlist_items(playlist_id, limit=100, offset=offset)).get("items", [])
            if not items:
                break
            batch = get_all_spotify_songs_from_query_result(items)
            songs.extend(batch)
            offset += 100
            pbar.update(len(batch))
    return songs

def find_favorite_spotify_songs(sp):
    songs = load_json(LIKED_CACHE_FILE, [])
    offset = len(songs)
    print("Fetching liked tracks... This may take a while.")
    with tqdm(desc="Liked songs", unit="song", initial=offset) as pbar:
        while True:
            items = try_request(lambda: sp.current_user_saved_tracks(limit=50, offset=offset)).get('items', [])
            if not items:
                break
            batch = get_all_spotify_songs_from_query_result(items)
            songs.extend(batch)
            offset += 50
            pbar.update(len(batch))
            save_json(LIKED_CACHE_FILE, songs)
    if songs:
        return {"name": "Your Spotify Likes", "description": "All liked tracks", "songs": songs}
    return None

def find_all_spotify_playlists(sp):
    playlists = []
    fav = find_favorite_spotify_songs(sp)
    if fav:
        playlists.append(fav)

    print("Fetching user playlists list...")
    offset = 0
    all_items = []
    while True:
        resp = try_request(lambda: sp.current_user_playlists(limit=50, offset=offset))
        items = resp.get('items', [])
        if not items:
            break
        all_items.extend(items)
        offset += 50

    print(f"Found {len(all_items)} playlists. Gathering songs...")
    for item in tqdm(all_items, desc="Playlists", unit="playlist"):
        songs = find_all_spotify_songs_in_playlist(item['id'], sp)
        playlists.append({
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'songs': songs
        })
    return playlists

# ---------- YT MUSIC HELPERS ----------
def get_all_ytm_ids(spotify_playlists, ytmusic):
    found_cache = load_json(YT_ID_CACHE_FILE, {}) or {}
    output, missing = [], []
    total = sum(len(p['songs']) for p in spotify_playlists)
    print(f"Searching {total} songs on YouTube Music...")
    for pl in tqdm(spotify_playlists, desc="Playlists", unit="playlist"):
        ids = []
        not_found = []
        with tqdm(pl['songs'], desc=pl['name'], unit="song", leave=False) as pbar:
            for title in pl['songs']:
                if title in found_cache:
                    song_id = found_cache[title]
                    if song_id:
                        ids.append(song_id)
                else:
                    result = try_request(lambda: ytmusic.search(title, limit=1, filter='songs'))
                    if result:
                        vid = result[0]['videoId']
                        found_cache[title] = vid
                        ids.append(vid)
                    else:
                        found_cache[title] = None
                        not_found.append(title)
                    save_json(YT_ID_CACHE_FILE, found_cache)
                pbar.update(1)
        if not_found:
            missing.append({pl['name']: not_found})
        output.append({**pl, 'songs': ids})
    if missing:
        save_json(NOT_FOUND_FILE, missing)
    return output

def like_all_songs(songs, ytmusic):
    choice = input("Like all songs in your likes playlist? (y/n): ")
    if choice.lower().startswith('y'):
        for vid in tqdm(reversed(songs), desc="Liking songs", unit="song"):
            while True:
                resp = try_request(lambda: ytmusic.rate_song(vid, 'LIKE'))
                text = resp['actions'][0]['addToToastAction']['item']['notificationActionRenderer']['responseText']['runs'][0]['text']
                if text == 'Saved to liked songs':
                    break
                sleep(1)

def create_all_playlists(playlists, ytmusic):
    completed = set(p['name'] for p in load_json(COMPLETED_PLAYLISTS_FILE, []))
    queue = [p for p in reversed(playlists) if p['name'] not in completed]

    with tqdm(queue, desc="Creating playlists", unit="playlist") as pbar:
        for pl in queue:
            name = pl['name'].replace('<', '(').replace('>', ')')
            try:
                try_request(lambda: ytmusic.create_playlist(name, pl['description'], video_ids=pl['songs']))
                if pl['name'].lower().startswith('your spotify likes'):
                    like_all_songs(pl['songs'], ytmusic)
                completed.add(pl['name'])
                save_json(COMPLETED_PLAYLISTS_FILE, list(completed))
            except Exception as e:
                print("Rate limit hit, saving remaining...")
                save_json(REMAINING_FILE, queue[queue.index(pl):])
                break
            else:
                pbar.update(1)
    save_json(YT_PLAYLISTS_FILE, playlists)

# ---------- MAIN ----------
def main():
    print("""
    ███████╗██████╗ ████████╗██████╗ ██╗   ██╗████████╗███╗   ███╗
    ██╔════╝██╔══██╗╚══██╔══╝╚════██╗╚██╗ ██╔╝╚══██╔══╝████╗ ████║
    ███████╗██████╔╝   ██║    █████╔╝ ╚████╔╝    ██║   ██╔████╔██║
    ╚════██║██╔═══╝    ██║   ██╔═══╝   ╚██╔╝     ██║   ██║╚██╔╝██║
    ███████║██║        ██║   ███████╗   ██║      ██║   ██║ ╚═╝ ██║
    ╚══════╝╚═╝        ╚═╝   ╚══════╝   ╚═╝      ╚═╝   ╚═╝     ╚═╝
    """)
    print("Welcome to SPT2YTM — Spotify to YouTube Music Converter")

    if not os.path.isfile(BROWSER_FILE):
        os.system("ytmusicapi browser")
    ytmusic = YTMusic(BROWSER_FILE)

    creds = load_json(CREDENTIALS_FILE) or {}
    if not creds.get('spotify_client_id'):
        creds['spotify_client_id'] = input("Spotify Client ID: ")
        creds['spotify_client_secret'] = input("Spotify Client Secret: ")
        save_json(CREDENTIALS_FILE, creds)
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SPOTIFY_SCOPE,
        client_id=creds['spotify_client_id'],
        client_secret=creds['spotify_client_secret'],
        redirect_uri="http://127.0.0.1:3000"
    ))

    playlists = load_json(SPOTIFY_PLAYLISTS_FILE)
    if not playlists:
        playlists = find_all_spotify_playlists(sp)
        save_json(SPOTIFY_PLAYLISTS_FILE, playlists)

    yt_playlists = get_all_ytm_ids(playlists, ytmusic)
    create_all_playlists(yt_playlists, ytmusic)

    missing = load_json(NOT_FOUND_FILE)
    if missing:
        print("\nSongs not found:")
        for entry in missing:
            for pl_name, songs in entry.items():
                print(f"\n--- {pl_name} ---")
                for s in songs:
                    print(f"- {s}")

if __name__ == '__main__':
    main()
