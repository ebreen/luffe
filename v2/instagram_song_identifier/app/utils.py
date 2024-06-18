def format_song_info(result):
    if result['status'] == 'success':
        song_info = result['result']
        spotify_link = song_info.get('spotify', {}).get('external_urls', {}).get('spotify', 'N/A')
        formatted_output = f"""
        Track: {song_info['title']}
        Artist: {song_info['artist']}
        Album: {song_info['album']}
        Release Date: {song_info['release_date']}
        Label: {song_info['label']}
        Spotify Link: {spotify_link}
        """
        return formatted_output
    else:
        return "No song recognized."