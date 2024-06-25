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
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        result = response.json()
        logger.debug(f"API response: {result}")  # Log the entire API response for debugging
        if result.get('status') == 'success':
            if result.get('result') is not None:
                return result
            else:
                logger.info("No song recognized in the audio file.")
                return {'status': 'success', 'result': None, 'message': "Could not identify song in reel"}
        else:
            logger.error(f"Song recognition failed: {result.get('error', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None