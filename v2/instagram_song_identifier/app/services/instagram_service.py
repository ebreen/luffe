import logging
from instagrapi import Client
from app.logger import setup_logger

logger = setup_logger(log_level=logging.DEBUG)  # Set to logging.INFO to disable debug messages

def login_to_instagram(username, password):
    logger.info("Logging into Instagram...")
    client = Client()
    client.login(username, password)
    return client

def get_direct_messages(client):
    logger.info("Fetching direct messages...")
    messages = []
    for thread in client.direct_threads():
        for message in client.direct_messages(thread.id):
            messages.append(message)
    return messages

def download_reel(client, reel_url):
    logger.info(f"Downloading reel from URL: {reel_url}")
    media_id = client.media_id(reel_url)
    return client.video_download_by_url(reel_url)

def send_direct_message(client, user_id, message):
    client.direct_send(message, user_ids=[user_id])

def get_pending_requests(client):
    pending_requests = []
    for thread in client.direct_pending_inbox():
        for user in thread.users:
            pending_requests.append((thread, user.pk))  # Store the thread and user_id as a tuple
    return pending_requests

def accept_request(client, thread_id):
    # Simulate approval by marking the thread as read or sending a message
    client.direct_thread_mark_unread(thread_id)
    # Send a message to the thread to simulate acceptance
    client.direct_send('Your request has been accepted!', thread_ids=[thread_id])