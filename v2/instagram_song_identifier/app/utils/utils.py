import time
from functools import wraps

def retry(exceptions, tries=4, delay=3, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

def format_song_info(result):
    # Check if this is a cached result (which doesn't have a 'status' key)
    if 'status' not in result:
        song_info = result['result']
    elif result['status'] == 'success':
        song_info = result['result']
    else:
        return "No song recognized."

    spotify_link = song_info.get('spotify', {}).get('external_urls', {}).get('spotify', 'N/A')
    formatted_output = f"""
🎵 *Song Identified!* 🎵

🎤 *Artist:* {song_info['artist']}
🎶 *Track:* {song_info['title']}
💿 *Album:* {song_info['album']}
📅 *Release Date:* {song_info['release_date']}

🔗 *Listen on Spotify:* {spotify_link}
"""
    return formatted_output