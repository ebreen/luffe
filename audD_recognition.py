import requests
import subprocess
import json

def call_youtube_downloader_api(youtube_url, resolution):
    api_url = f'http://127.0.0.1:5000/download/{resolution}'
    data = {'url': youtube_url}
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        print("Video downloaded successfully.")
    else:
        raise Exception(f"Failed to download video: {response.json().get('error')}")

def extract_audio(video_path, audio_path):
    command = ['ffmpeg', '-y', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path]
    subprocess.run(command, check=True)
    print(f"Audio extracted successfully to {audio_path}")

def identify_song(audio_path, api_token):
    with open(audio_path, 'rb') as audio_file:
        files = {'file': audio_file}
        data = {'api_token': api_token, 'return': 'apple_music,spotify'}
        response = requests.post('https://api.audd.io/', files=files, data=data)
        print(f"API Response: {response.text}")  # Log the full response for debugging
        result = response.json()
        if result['status'] == 'success' and 'result' in result:
            song = result['result']
            print(f"Song identified: {song['title']} by {song['artist']}")
            return song
        else:
            raise Exception(f"Song identification failed: {result}")

if __name__ == '__main__':
    # Replace with actual values
    YOUTUBE_URL = "https://www.youtube.com/watch?v=O3eOsY45ndQ"
    RESOLUTION = "720p"
    VIDEO_PATH = "video.mp4"
    AUDIO_PATH = "audio.mp3"
    API_TOKEN = "744e3e3bf7862f59b820f3709fb9fb00"

    try:
        call_youtube_downloader_api(YOUTUBE_URL, RESOLUTION)
        extract_audio(VIDEO_PATH, AUDIO_PATH)
        song = identify_song(AUDIO_PATH, API_TOKEN)
        print(f"Identified Song: {song['title']} by {song['artist']}")
    except Exception as e:
        print(f"Error: {e}")
