# app/main.py
import time
import os
import logging
from dotenv import load_dotenv
from app.services.instagram_service import login_to_instagram, get_direct_messages, download_reel, send_direct_message, get_pending_requests, accept_request
from app.services.media_service import extract_audio_from_video
from app.services.music_service import recognize_song
from app.logger import setup_logger
from app.utils.utils import format_song_info
from app.database import initialize_db, add_user, add_song, add_user_song, get_user_song_history, get_cached_song, cache_reel_song

def main_loop(client, api_token, logger):
    initialize_db()  # Initialize the database when starting the app

    while True:
        try:
            logger.info("Checking for pending requests...")
            pending_requests = get_pending_requests(client)
            for request, user_id in pending_requests:
                logger.info(f"Accepting request from user {user_id}...")
                accept_request(client, request.id)

            logger.info("Fetching direct messages...")
            messages = get_direct_messages(client)

            relevant_messages = [msg for msg in messages if not (msg.text and "Your request has been accepted" in msg.text)]
            if relevant_messages:
                latest_message = sorted(relevant_messages, key=lambda x: x.timestamp, reverse=True)[0]

                if latest_message.clip and latest_message.clip.media_type == 2:
                    reel_id = latest_message.clip.id
                    reel_url = latest_message.clip.video_url
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

                        user_id = latest_message.user_id
                        username = client.user_info(user_id).username
                        db_user_id = add_user(user_id, username)
                        
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
                        
                        # Get user's song history
                        song_history = get_user_song_history(user_id)
                        history_message = "\n\nYour recent song identifications:\n" + "\n".join([f"{title} by {artist} ({request_time})" for title, artist, request_time in song_history])
                        
                        logger.info(f"Sending result and history back to user {user_id}...")
                        send_direct_message(client, user_id, formatted_result + history_message)
                        logger.info("Result and history sent successfully.")
                    elif result is not None and result.get('message') is not None:
                        user_id = latest_message.user_id
                        logger.info(f"Sending message to user {user_id}...")
                        send_direct_message(client, user_id, result['message'])
                        logger.info("Message sent successfully.")
                    else:
                        logger.info("No song recognized, skipping message processing.")
            else:
                logger.info("No relevant messages found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

        logger.info("Sleeping for 15 seconds before next iteration...")
        time.sleep(15)

if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    api_token = os.getenv("AUDD_API_TOKEN")

    logger = setup_logger(log_level=logging.INFO)  # Set to logging.INFO to disable debug messages

    logger.info("Logging into Instagram...")
    client = login_to_instagram(username, password)

    main_loop(client, api_token, logger)