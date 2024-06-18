# app/main.py
import time
import os
import logging
from dotenv import load_dotenv
from app.instagram_api import login_to_instagram, get_direct_messages, download_reel, send_direct_message, get_pending_requests, accept_request
from app.media_processing import extract_audio_from_video
from app.music_recognition import recognize_song
from app.logger import setup_logger
from app.utils import format_song_info


def main_loop(client, api_token, logger):
    while True:
        try:
            logger.info("Checking for pending requests...")
            pending_requests = get_pending_requests(client)
            for request, user_id in pending_requests:
                logger.info(f"Accepting request from user {user_id}...")
                accept_request(client, request.id)  # Use request.id instead of request.thread_id

            logger.info("Fetching direct messages...")
            messages = get_direct_messages(client)

            # Filter out the acceptance messages and get the latest relevant message
            relevant_messages = [msg for msg in messages if not (msg.text and "Your request has been accepted" in msg.text)]
            if relevant_messages:
                latest_message = sorted(relevant_messages, key=lambda x: x.timestamp, reverse=True)[0]

                if latest_message.clip and latest_message.clip.media_type == 2:  # 2 corresponds to video
                    reel_url = latest_message.clip.video_url
                    logger.info(f"Downloading reel from URL: {reel_url}")
                    video_path = download_reel(client, reel_url)

                    logger.info("Extracting audio from video...")
                    audio_path = extract_audio_from_video(video_path, "extracted_audio.mp3")

                    logger.info("Recognizing song from audio...")
                    result = recognize_song(audio_path, api_token)
                    if result is not None and result.get('result') is not None:
                        formatted_result = format_song_info(result)
                        logger.info(f"Recognized song:\n{formatted_result}")

                        # Send the result back to the user
                        user_id = latest_message.user_id
                        logger.info(f"Sending result back to user {user_id}...")
                        send_direct_message(client, user_id, formatted_result)
                        logger.info("Result sent successfully.")
                    elif result is not None and result.get('message') is not None:
                        user_id = latest_message.user_id
                        logger.info(f"Sending message to user {user_id}...")
                        send_direct_message(client, user_id, result['message'])
                        logger.info("Message sent successfully.")
                    else:
                        logger.info("No song recognized, skipping message processing.")

                    # Delete the .mp4 and .mp3 files after processing
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        logger.info(f"Deleted video file: {video_path}")
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                        logger.info(f"Deleted audio file: {audio_path}")
            else:
                logger.info("No relevant messages found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        logger.info("Sleeping for 60 seconds before next iteration...")
        time.sleep(60)

if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    api_token = os.getenv("AUDD_API_TOKEN")

    logger = setup_logger(log_level=logging.INFO)  # Set to logging.INFO to disable debug messages

    logger.info("Logging into Instagram...")
    client = login_to_instagram(username, password)

    main_loop(client, api_token, logger)