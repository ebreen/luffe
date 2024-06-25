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
    Track: {song_info['title']}
    Artist: {song_info['artist']}
    Album: {song_info['album']}
    Release Date: {song_info['release_date']}
    Spotify Link: {spotify_link}
    """
    return formatted_output