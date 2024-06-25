import time
import os
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from threading import Thread
from queue import Queue
from json.decoder import JSONDecodeError
from app.services.instagram_service import login_to_instagram, get_direct_messages, download_reel, send_direct_message, get_pending_requests, accept_request
from app.services.media_service import extract_audio_from_video
from app.services.music_service import recognize_song
from app.logger import setup_logger
from app.utils.utils import format_song_info, retry
from app.database import initialize_db, add_user, add_song, add_user_song, get_cached_song, cache_reel_song, get_user, update_user

# Global queue for new messages
message_queue = Queue()

PARIS_TZ = pytz.timezone('Europe/Paris')

def check_messages(client, logger):
    last_processed_timestamp = datetime.now(PARIS_TZ) - timedelta(minutes=5)  # Start by checking messages from the last 5 minutes
    while True:
        try:
            logger.info("Fetching direct messages...")
            messages = get_direct_messages(client)
            current_time = datetime.now(PARIS_TZ)
            
            new_messages = [msg for msg in messages if msg.timestamp.replace(tzinfo=pytz.UTC).astimezone(PARIS_TZ) > last_processed_timestamp]
            if new_messages:
                # Only process the most recent message
                latest_message = max(new_messages, key=lambda msg: msg.timestamp)
                logger.info(f"New message detected: {latest_message.id} at {latest_message.timestamp}")
                message_queue.put(latest_message)
                last_processed_timestamp = latest_message.timestamp.replace(tzinfo=pytz.UTC).astimezone(PARIS_TZ)
            
            # Check for pending requests
            logger.info("Checking for pending requests...")
            pending_requests = get_pending_requests(client)
            for request, user_id in pending_requests:
                logger.info(f"Accepting request from user {user_id}...")
                accept_request(client, request.id)
            
            # Long polling: sleep for a short time before checking again
            time.sleep(1)  # Reduced sleep time for more frequent checks
        except Exception as e:
            logger.error(f"Error in message checking: {str(e)}", exc_info=True)
            time.sleep(5)  # If there's an error, wait a bit longer before retrying

@retry((JSONDecodeError,), tries=3, delay=1)
def get_user_info(client, user_id, logger):
    try:
        user = get_user(user_id)
        if user:
            update_user(user_id, user['username'])
            return user
        
        user_info = client.user_info(user_id)
        username = user_info.username
        user = add_user(user_id, username)
        return user
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        return {'id': user_id, 'username': str(user_id), 'instagram_id': user_id, 'total_interactions': 0, 'first_interaction': datetime.now(PARIS_TZ)}

def process_message(client, api_token, logger, message):
    try:
        if message.clip and message.clip.media_type == 2:
            reel_id = message.clip.id
            reel_url = message.clip.video_url
            logger.info(f"Processing reel with ID: {reel_id}")

            # Check if the reel is already in the cache
            cached_song = get_cached_song(reel_id)
            if cached_song:
                logger.info("Song found in cache.")
                song_id, title, artist, album, release_date, spotify_link = cached_song
                result = {
                    'result': {
                        'title': title,
                        'artist': artist,
                        'album': album,
                        'release_date': release_date,
                        'spotify': {'external_urls': {'spotify': spotify_link}}
                    }
                }
            else:
                logger.info("Song not in cache. Downloading and processing reel...")
                video_path = download_reel(client, reel_url)
                audio_path = extract_audio_from_video(video_path, "extracted_audio.mp3")
                result = recognize_song(audio_path, api_token)

                # Clean up temporary files
                if os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"Deleted video file: {video_path}")
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Deleted audio file: {audio_path}")

            if result is not None and result.get('result') is not None:
                formatted_result = format_song_info(result)
                logger.info(f"Recognized song:\n{formatted_result}")

                user_id = message.user_id
                user = get_user_info(client, user_id, logger)

                db_user_id = user['id']
                
                song_info = result['result']
                if not cached_song:
                    db_song_id = add_song(
                        song_info['title'],
                        song_info['artist'],
                        song_info['album'],
                        song_info['release_date'],
                        song_info.get('spotify', {}).get('external_urls', {}).get('spotify')
                    )
                    cache_reel_song(reel_id, db_song_id)
                else:
                    db_song_id = song_id
                
                add_user_song(db_user_id, db_song_id)
                
                # Add user info to the formatted result
                user_info = f"""
----------------------------
👤 *Your Info:*
Total Identifications: {user['total_interactions']}
First Used: {user['first_interaction']}

Thank you for using our Song Identifier! 🎉
"""
                complete_message = formatted_result + user_info
                
                logger.info(f"Sending result and user info back to user {user['username']}...")
                send_direct_message(client, user_id, complete_message)
                logger.info("Result and user info sent successfully.")
            elif result is not None and result.get('message') is not None:
                user_id = message.user_id
                logger.info(f"Sending message to user {user_id}...")
                send_direct_message(client, user_id, result['message'])
                logger.info("Message sent successfully.")
            else:
                logger.info("No song recognized, skipping message processing.")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)

def message_processor(client, api_token, logger):
    while True:
        message = message_queue.get()
        process_message(client, api_token, logger, message)
        message_queue.task_done()

def main():
    load_dotenv()
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    api_token = os.getenv("AUDD_API_TOKEN")

    logger = setup_logger(log_level=logging.INFO)
    logger.info("Initializing database...")
    initialize_db()

    logger.info("Logging into Instagram...")
    client = login_to_instagram(username, password)

    # Start the message checking thread
    message_checker = Thread(target=check_messages, args=(client, logger))
    message_checker.daemon = True
    message_checker.start()

    # Start the message processing thread
    processor = Thread(target=message_processor, args=(client, api_token, logger))
    processor.daemon = True
    processor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    main()