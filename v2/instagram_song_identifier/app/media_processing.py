import logging
from moviepy.editor import VideoFileClip
from app.logger import setup_logger

logger = setup_logger(log_level=logging.DEBUG)  # Set to logging.INFO to disable debug messages

def extract_audio_from_video(video_path, audio_path):
    logger.info(f"Extracting audio from video: {video_path}")
    video_path_str = str(video_path)  # Convert WindowsPath to string
    video = VideoFileClip(video_path_str)
    audio = video.audio
    audio.write_audiofile(audio_path)
    return audio_path