# app/main.py
import os
import logging
from dotenv import load_dotenv
from app.instagram_api import login_to_instagram, get_direct_messages, download_reel, send_direct_message
from app.media_processing import extract_audio_from_video
from app.music_recognition import recognize_song
from app.logger import setup_logger
from app.utils import format_song_info


def main():
    load_dotenv()
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    api_token = os.getenv("AUDD_API_TOKEN")

    logger = setup_logger(log_level=logging.DEBUG)  # Set to logging.INFO to disable debug messages

    logger.info("Logging into Instagram...")
    client = login_to_instagram(username, password)

    logger.info("Fetching direct messages...")
    messages = get_direct_messages(client)

    latest_message = sorted(messages, key=lambda x: x.timestamp, reverse=True)[0]

    if latest_message.clip and latest_message.clip.media_type == 2:  # 2 corresponds to video
        reel_url = latest_message.clip.video_url
        logger.info(f"Downloading reel from URL: {reel_url}")
        video_path = download_reel(client, reel_url)

        logger.info("Extracting audio from video...")
        audio_path = extract_audio_from_video(video_path, "extracted_audio.mp3")

        logger.info("Recognizing song from audio...")
        result = recognize_song(audio_path, api_token)
        formatted_result = format_song_info(result)
        logger.info(f"Recognized song:\n{formatted_result}")

        # Send the result back to the user
        user_id = latest_message.user_id
        logger.info(f"Sending result back to user {user_id}...")
        send_direct_message(client, user_id, formatted_result)
        logger.info("Result sent successfully.")

if __name__ == "__main__":
    main()