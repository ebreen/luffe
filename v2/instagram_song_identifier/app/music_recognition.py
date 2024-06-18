import logging
import requests
from app.logger import setup_logger

logger = setup_logger(log_level=logging.DEBUG)  # Set to logging.INFO to disable debug messages

def recognize_song(audio_path, api_token):
    logger.info(f"Recognizing song from audio: {audio_path}")
    url = "https://api.audd.io/"
    data = {
        'api_token': api_token,
        'return': 'apple_music,spotify',
    }
    files = {
        'file': open(audio_path, 'rb')
    }
    response = requests.post(url, data=data, files=files)
    return response.json()