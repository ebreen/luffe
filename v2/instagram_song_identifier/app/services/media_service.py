import logging
from moviepy.editor import VideoFileClip
from app.logger import setup_logger

logger = setup_logger(log_level=logging.DEBUG)  # Set to logging.INFO to disable debug messages

def extract_audio_from_video(video_path, audio_path):
    logger.info(f"Extracting audio from video: {video_path}")
    video_path_str = str(video_path)  # Convert WindowsPath to string
    with VideoFileClip(video_path_str) as video:
        video.audio.write_audiofile(audio_path)
    return audio_path