import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time
import os
import sys
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

root = Tk()
root.geometry("300x150")
root.title("trueshuffle")

def config_wizard():
    def get_entry():
        global client_id
        client_id=entry.get()
        with open("config.txt", "w") as file:
            file.write("CLIENT_ID=" + client_id + "\n")
            file.write("CLIENT_SECRET=" + input("what is your client secret? "))
    label = Label(root, text="What is your client id:")
    label.pack(pady=10)
    entry = Entry(root, width=30)
    entry.pack(pady=5)
    button = Button(root, text="Submit", command=get_entry)
    button.pack(pady=10)

# Check if config.txt exists
if os.path.exists("config.txt"):
    print("config exists")
else:
    answer = messagebox.askquestion("trueshuffle","config does not exists, do you want to create one using the wizard? ")
    if answer == "yes" or answer == "y":
        print("starting wizard")
        config_wizard()
    elif answer == "no" or answer == "n":
        print("exiting")
        sys.exit(0)
    else:
        print("answer yes or no")
        sys.exit(1)
        
    
#get credentials
with open('config.txt', "r") as file:
    for line in file:
        line = line.strip()
        if line.startswith("CLIENT_ID="):
            client_id = line.split("=", 1)[1]
        elif line.startswith("CLIENT_SECRET="):
            client_secret = line.split("=", 1)[1]

# Set up Spotify OAuth with required scopes
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri="http://127.0.0.1:1234",
    scope="user-modify-playback-state user-read-playback-state playlist-read-private"
))

# Ask for a playlist to use

# Step 1: Get the playlists (list of playlist objects)
playlists = sp.current_user_playlists(limit=50, offset=0)
playlist_items = playlists['items']  # This is a list of playlist objects

# Step 2: Print playlist names with numbers
for i, item in enumerate(playlist_items, start=1):
    print(f"{i}. {item['name']}")

# Step 3: Ask the user to choose a playlist by number
number_of_playlist = int(input("Which playlist do you want to shuffle? "))

# Step 4: Get the playlist object the user chose
selected_playlist = playlist_items[number_of_playlist - 1]

# Step 5: Extract the URL of the selected playlist
playlist_url = selected_playlist['external_urls']['spotify']

def get_playlist_tracks(playlist_url):
    tracks = []
    results = sp.playlist_tracks(playlist_url)
    while results:
        tracks.extend(results["items"])
        results = sp.next(results) if results["next"] else None
    return tracks

tracks = get_playlist_tracks(playlist_url)

def choose_active_device():
    devices = sp.devices()["devices"]
    if not devices:
        print("No active devices found. Open Spotify on a device and try again.")
        return None

    print("\nAvailable devices:")
    for i, device in enumerate(devices):
        print(f"{i + 1}. {device['name']} (ID: {device['id']})")

    choice = input("Select device number to use: ")
    try:
        device_index = int(choice) - 1
        if device_index < 0 or device_index >= len(devices):
            print("Invalid choice, using the first available device.")
            return devices[0]["id"]
        return devices[device_index]["id"]
    except ValueError:
        print("Invalid input, using the first available device.")
        return devices[0]["id"]

def wait_for_track_end():
    # Wait a moment for playback to begin
    time.sleep(1)
    current_playback = sp.current_playback()
    if not current_playback or not current_playback.get("is_playing"):
        print("No track is currently playing.")
        return

    track = current_playback.get("item")
    if not track:
        print("No track info available.")
        return

    duration_ms = track["duration_ms"]
    print(f"\nNow playing: {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")
    print(f"Duration: {duration_ms/1500:.2f} seconds")

    while True:
        current_playback = sp.current_playback()
        if not current_playback:
            print("Playback stopped or no data available.")
            break

        progress_ms = current_playback.get("progress_ms", 0)
        # Optionally print the progress
        print(f"Progress: {progress_ms/1000:.2f}s / {duration_ms/1000:.2f}s", end="\r")

        # Check if the track is nearly finished (allowing a small threshold)
        if progress_ms >= duration_ms - 1000:
            print("\nTrack has ended.")
            break

        time.sleep(1)  # Poll every 1 second

# Choose a device
device_id = choose_active_device()

def choose(device_id):
    # Choose a random track from the playlist
    total_tracks = len(tracks)
    random_index = random.randint(0, total_tracks - 1)
    print(f"\nRandom track number: {random_index + 1}")

    # Play the random track (Spotify Premium and an active device are required)
    if device_id:
        track_uri = tracks[random_index]["track"]["uri"]
        sp.start_playback(device_id=device_id, uris=[track_uri])
        print(f"Playing track: {tracks[random_index]['track']['name']}")

        # Now wait until the track ends
        wait_for_track_end()
        choose(device_id)

choose(device_id)
root.mainloop()