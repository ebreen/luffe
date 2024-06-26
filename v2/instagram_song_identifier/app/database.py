import sqlite3
from contextlib import contextmanager
from datetime import datetime
import pytz

DATABASE_NAME = "luffe.db"
CURRENT_DB_VERSION = 3  # Incremented for new schema changes
PARIS_TZ = pytz.timezone('Europe/Paris')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def initialize_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create or update version table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS db_version (
            version INTEGER PRIMARY KEY
        )
        ''')
        
        # Check current version
        cursor.execute('SELECT version FROM db_version')
        result = cursor.fetchone()
        if result is None:
            # New database, insert current version
            cursor.execute('INSERT INTO db_version (version) VALUES (?)', (CURRENT_DB_VERSION,))
            db_version = CURRENT_DB_VERSION
        else:
            db_version = result[0]
        
        # Perform migrations if necessary
        if db_version < CURRENT_DB_VERSION:
            perform_migrations(cursor, db_version)
            cursor.execute('UPDATE db_version SET version = ?', (CURRENT_DB_VERSION,))
        
        # Create tables (existing tables won't be affected)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            instagram_id TEXT UNIQUE,
            username TEXT,
            first_interaction TIMESTAMP,
            last_interaction TIMESTAMP,
            total_interactions INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            artist TEXT,
            album TEXT,
            release_date TEXT,
            spotify_link TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_songs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            song_id INTEGER,
            request_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (song_id) REFERENCES songs (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reel_cache (
            reel_id TEXT PRIMARY KEY,
            song_id INTEGER,
            cache_time TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs (id)
        )
        ''')
        
        conn.commit()

def perform_migrations(cursor, from_version):
    if from_version < 2:
        # Migration to version 2: Add reel_cache table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reel_cache (
            reel_id TEXT PRIMARY KEY,
            song_id INTEGER,
            cache_time TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs (id)
        )
        ''')
    if from_version < 3:
        # Migration to version 3: Update users table
        cursor.execute('''
        ALTER TABLE users ADD COLUMN first_interaction TIMESTAMP
        ''')
        cursor.execute('''
        ALTER TABLE users ADD COLUMN total_interactions INTEGER DEFAULT 0
        ''')
        # Set first_interaction to last_interaction for existing users
        cursor.execute('''
        UPDATE users SET first_interaction = last_interaction WHERE first_interaction IS NULL
        ''')
    # Add more migration steps here for future versions

def add_user(instagram_id, username):
    current_time = datetime.now(PARIS_TZ)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO users 
        (instagram_id, username, first_interaction, last_interaction, total_interactions)
        VALUES (?, ?, 
                COALESCE((SELECT first_interaction FROM users WHERE instagram_id = ?), ?),
                ?,
                COALESCE((SELECT total_interactions FROM users WHERE instagram_id = ?), 0) + 1
        )
        ''', (instagram_id, username, instagram_id, current_time, current_time, instagram_id))
        conn.commit()
        user_id = cursor.lastrowid
        return {
            'id': user_id,
            'instagram_id': instagram_id,
            'username': username,
            'first_interaction': current_time,
            'last_interaction': current_time,
            'total_interactions': 1
        }

def update_user(instagram_id, username):
    current_time = datetime.now(PARIS_TZ)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users SET 
            username = ?,
            last_interaction = ?,
            total_interactions = total_interactions + 1
        WHERE instagram_id = ?
        ''', (username, current_time, instagram_id))
        conn.commit()

def get_user(instagram_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE instagram_id = ?', (instagram_id,))
        user = cursor.fetchone()
        if user:
            return dict(user)
        return None

def add_song(title, artist, album, release_date, spotify_link):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO songs (title, artist, album, release_date, spotify_link) VALUES (?, ?, ?, ?, ?)', 
                       (title, artist, album, release_date, spotify_link))
        conn.commit()
        return cursor.lastrowid

def add_user_song(user_id, song_id):
    current_time = datetime.now(PARIS_TZ)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_songs (user_id, song_id, request_time) VALUES (?, ?, ?)', 
                       (user_id, song_id, current_time))
        conn.commit()

def get_user_song_history(instagram_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT s.title, s.artist, us.request_time
        FROM user_songs us
        JOIN users u ON us.user_id = u.id
        JOIN songs s ON us.song_id = s.id
        WHERE u.instagram_id = ?
        ORDER BY us.request_time DESC
        LIMIT 10
        ''', (instagram_id,))
        return cursor.fetchall()

def get_cached_song(reel_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT s.id, s.title, s.artist, s.album, s.release_date, s.spotify_link
        FROM reel_cache rc
        JOIN songs s ON rc.song_id = s.id
        WHERE rc.reel_id = ?
        ''', (reel_id,))
        return cursor.fetchone()

def cache_reel_song(reel_id, song_id):
    current_time = datetime.now(PARIS_TZ)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO reel_cache (reel_id, song_id, cache_time) VALUES (?, ?, ?)', 
                       (reel_id, song_id, current_time))
        conn.commit()