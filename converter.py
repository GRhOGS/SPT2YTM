import os
import json
import tqdm
import spotipy
import ytmusicapi
from time import time
from time import sleep
from functools import reduce
from ytmusicapi import YTMusic
from spotipy.oauth2 import SpotifyOAuth

def get_all_spotify_songs_from_query_result(items):
    output = []
    for song in items:    
        title = song["track"]["name"]
        for artist in song["track"]["artists"]:
            title += " " + artist["name"]
        if(title.replace(" ", "") != ""): # filter deleted songs
            output.append(title)
    return output

def find_all_spotify_songs_in_playlist(playlist_id, sp):
    songs = []
    found_all = False
    offset = 0
    pbar = tqdm(desc="Fetching playlist songs", unit="songs")

    while not found_all:
        result = sp.playlist_items(playlist_id, limit=100, offset=offset)["items"]
        if not result:
            found_all = True
        else:
            tracks = get_all_spotify_songs_from_query_result(result)
            songs.extend(tracks)
            offset += 100
            pbar.update(len(tracks))

    pbar.close()
    return songs


def find_favorite_spotify_songs(sp):
    found_all = False
    favs = []
    offset = 0
    print("Fetching favorites (this may take a while)...")
    pbar = tqdm(desc="Liked Songs", unit="songs")

    while not found_all:
        result = sp.current_user_saved_tracks(offset=offset, limit=50)['items']
        if not result:
            found_all = True
        else:
            tracks = get_all_spotify_songs_from_query_result(result)
            favs.extend(tracks)
            offset += 50
            pbar.update(len(tracks))

    pbar.close()
    if favs:
        return {
            "name": "your favorites from spotify",
            "description": "this playlist contains all your liked songs from spotify",
            "songs": favs
        }
    return []

def find_all_spotify_playlists(sp):
    found_all = False
    offset = 0
    spotify_playlists = []

    fav_playlist = find_favorite_spotify_songs(sp)
    if fav_playlist:
        spotify_playlists.append(fav_playlist)

    print("Fetching playlists list...")
    all_playlists = []

    while not found_all:
        result = sp.current_user_playlists(limit=50, offset=offset)
        items = result['items']
        if not items:
            found_all = True
        else:
            all_playlists.extend(items)
            offset += 50

    print(f"{len(all_playlists)} playlists found. Fetching songs...")
    for item in tqdm(all_playlists, desc="Playlists", unit="playlist"):
        songs = find_all_spotify_songs_in_playlist(item["id"], sp)
        spotify_playlists.append({
            "name": item["name"],
            "description": item["description"],
            "songs": songs
        })

    print(f"{len(spotify_playlists)} playlists total (including favorites).")
    return spotify_playlists


def get_all_ytm_ids(spotify_playlists):
    output = []
    not_found_songs = []
    found_songs = {}

    total_songs = sum(len(p["songs"]) for p in spotify_playlists)
    estimated_time = int(total_songs * 0.005)
    print(f"Looking for all your Spotify songs on YouTube Music. This will take about {estimated_time} minutes to complete.")
    start_time = time()

    for playlist in tqdm(spotify_playlists, desc="Playlists", unit="playlist"):
        song_ids = []
        not_found = []

        print(f"\nFetching YouTube Music song IDs for songs in: {playlist['name']}")
        for song_title in tqdm(playlist["songs"], desc=playlist["name"], unit="song", leave=False):
            # skip query if song has been searched before
            if song_title in found_songs:
                song_ids.append(found_songs[song_title])
                continue

            # search on YT Music
            result = next(iter(ytmusic.search(song_title, limit=1, filter="songs")), None)
            if result is not None:
                song_id = result["videoId"]
                found_songs[song_title] = song_id
                song_ids.append(song_id)
            else:
                print(f"  Song not found: {song_title}")
                not_found.append(song_title)

        if not_found:
            not_found_songs.append({playlist["name"]: not_found})

        playlist["songs"] = song_ids
        output.append(playlist)

    print(f"\nDone fetching {len(found_songs)} individual songs in {round(time() - start_time, 2)} seconds.")
    
    if not_found_songs:
        with open("not_found_songs.json", "w") as f:
            json.dump(not_found_songs, f, indent=4)

    return output

def like_all_songs(songs):
    print("\nDo you want me to like all the songs in your 'favorite songs' playlist so that they appear in YouTube's auto-generated playlist?")
    print("Note: This may take a while due to YouTube's rate limits.")
    confirmation = input("Enter 'y' for yes, anything else for no: ")

    if confirmation.lower() in ['y', 'yes']:
        for song in tqdm(songs[::-1], desc="Liking songs", unit="song"):
            response = ytmusic.rate_song(song, "LIKE")
            text = response["actions"][0]["addToToastAction"]["item"]["notificationActionRenderer"]["responseText"]["runs"][0]["text"]
            while text != "Saved to liked songs":
                sleep(1)
                response = ytmusic.rate_song(song, "LIKE")
                text = response["actions"][0]["addToToastAction"]["item"]["notificationActionRenderer"]["responseText"]["runs"][0]["text"]

def create_all_playlists(playlists_in, ytmusic):
    print("\nCreating YouTube Music playlists. You're almost done!")

    playlists = playlists_in[::-1]  # oldest first
    with tqdm(total=len(playlists), desc="Creating playlists", unit="playlist") as pbar:
        i = 0
        while i < len(playlists):
            playlist = playlists[i]
            try:
                ytmusic.create_playlist(
                    playlist["name"].replace("<", "(").replace(">", ")"),
                    playlist["description"],
                    video_ids=playlist["songs"]
                )
                print("Created playlist:", playlist["name"])
                if playlist["name"] == "your favorites from spotify":
                    like_all_songs(playlist["songs"])
                i += 1
                pbar.update(1)
            except Exception as error:
                print("An error occurred:", error)
                print("You probably hit YouTube Music's 25 playlists / 6 hours limit.")
                with open("remaining.json", "w") as f:
                    json.dump(playlists[i:], f, indent=4)
                print("You can rerun this script after 6h to finish. Remaining playlists saved to 'remaining.json'.")
                break
        else:
            # Clear the file if no errors
            with open("remaining.json", "w") as f:
                json.dump([], f, indent=4)

def print_not_added_songs():
    if os.path.isfile("not_found_songs.json"):
        with open("not_found_songs.json", "r") as json_file:
            not_found_songs = json.load(json_file)

        print("\nCouldn't find the following songs:")
        for playlist in not_found_songs:
            for playlist_name, songs in playlist.items():
                print(f"\n----- {playlist_name} -----")
                for song in songs:
                    print(f"- {song}")
        print("\nThis has also been saved for later use in the file 'not_found_songs.json'.")

# --------------
# PROGRAMM START
# --------------

print("""
███████╗██████╗ ████████╗██████╗ ██╗   ██╗████████╗███╗   ███╗
██╔════╝██╔══██╗╚══██╔══╝╚════██╗╚██╗ ██╔╝╚══██╔══╝████╗ ████║
███████╗██████╔╝   ██║    █████╔╝ ╚████╔╝    ██║   ██╔████╔██║
╚════██║██╔═══╝    ██║   ██╔═══╝   ╚██╔╝     ██║   ██║╚██╔╝██║
███████║██║        ██║   ███████╗   ██║      ██║   ██║ ╚═╝ ██║
╚══════╝╚═╝        ╚═╝   ╚══════╝   ╚═╝      ╚═╝   ╚═╝     ╚═╝
""")
print("Welcome to SPT2YTM, the Spotify to YouTube Music converter.")
total_time = time()

# get or generate yt music credentials
print("Getting YouTube Music credentials...")
if(not os.path.isfile("browser.json")):
    print("Generating YouTube API tokens, please follow the instructions in the browser window, which will pop up shortly. After completion, continue here.")
    sleep(10)
    os.system("ytmusicapi browser")
ytmusic = YTMusic("browser.json")

# skip fetching playlists if they have already been fetched
if(os.path.isfile("remaining.json") or os.path.isfile("yt_playlists.json")):
    yt_playlists = []
    if(os.path.isfile("remaining.json")):
        with open("remaining.json") as json_file:
            yt_playlists = json.load(json_file)
            print("Loaded remaining playlists from file.")
    else:
        with open("yt_playlists.json") as json_file:
                yt_playlists = json.load(json_file)
                print("Loaded yt music playlists from file.")        
    create_all_playlists(yt_playlists, ytmusic)
else:   # start fetching needed data
    start_time = time()
    # get all the users playlists from spotify
    print("Finding all playlists on spotify...")
    playlists = []
    if(os.path.isfile("spotify_playlists.json")):
        with open("spotify_playlists.json") as json_file:
            playlists = json.load(json_file)
            print("Loaded spotify playlists from file.")
    else:
        print("Getting spotify credentials...")
        credentials = {}
        if(os.path.isfile("credentials.json")):
            with open("credentials.json") as json_file:
                credentials = json.load(json_file)
        else:
            # create spotify credentials file
            print("Creating spotify credentials file. If you don't know where to find your spotify client id and client secret, please check the readme.md file.")
            print("Please enter the following from your app in the developer dashboard:")
            client_id = input("Enter your client id:")
            client_secret = input("Enter your client secret:")
            credentials = {
                "spotify_client_id": client_id,
                "spotify_client_secret": client_secret
            }
            with open("credentials.json", "w") as json_file:
                json_file.write(json.dumps(credentials, indent=4))

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                            scope = "user-library-read",
                            client_id = credentials["spotify_client_id"],
                            client_secret = credentials["spotify_client_secret"],
                            redirect_uri = "http://127.0.0.1:3000"))

        playlists = find_all_spotify_playlists(sp)
        with open("spotify_playlists.json", "w") as json_file:
                json_file.write(json.dumps(playlists, indent=4))
        print("Finished fetching all playlists from spotify!")
        print("Fetched", len(playlists), "playlists containing a total of", 
            reduce(lambda x,y: x+y, map(lambda x: len(x["songs"]), playlists)),
            "songs in", time()-start_time, "s.")

    # create new playlists in youtube music
    yt_playlists = get_all_ytm_ids(playlists)
    with open("yt_playlists.json", "w") as json_file:
        json_file.write(json.dumps(yt_playlists, indent=4))
    create_all_playlists(yt_playlists, ytmusic)
    print_not_added_songs()

print("Finished in", time() - total_time, "s.")
input("Press enter to close this programm.")