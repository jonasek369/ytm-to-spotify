import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from dotenv import load_dotenv
from typing import Optional
from tqdm import tqdm
import os

# Loads .env variables where spotify should be
load_dotenv(".env")
assert "oauth.json" in os.listdir(), "Oauth for Youtube music is not in directory!"


scope = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"

LIKED_MUSIC = "Liked Music"


class YtmToSpotify:
    def __init__(self):
        self.spotify_connection = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        self.youtube_connection = YTMusic("oauth.json")

    def get_ytm_playlist(self, playlist_name) -> Optional[dict]:
        playlists = self.youtube_connection.get_library_playlists()
        for playlist in playlists:
            if playlist["title"] == playlist_name:
                return playlist
        return None

    def get_ytm_playlist_songs(self, playlist_id):
        return self.youtube_connection.get_playlist(playlistId=playlist_id, limit=None)["tracks"]

    @staticmethod
    def _split_array(arr, n):
        """Splits an array into `n` equal parts (or as close to equal as possible)."""
        if n <= 0:
            raise ValueError("Number of parts must be greater than zero.")

        chunk_size, remainder = divmod(len(arr), n)

        result = []
        start = 0

        for i in range(n):
            end = start + chunk_size + (1 if i < remainder else 0)
            result.append(arr[start:end])
            start = end
        return result

    def clone_playlist(self, ytm_playlist_name: str, spotify_playlist_name: str, spotify_is_public: bool = True, artist_search: bool = True):
        songs = yts.get_ytm_playlist_songs(yts.get_ytm_playlist(ytm_playlist_name)["playlistId"])
        assert songs is not None, "Could not get ytm playlist or its songs make sure the name is right"

        suid = yts.spotify_connection.current_user()["id"]
        assert suid is not None, "Spotify user id should not be None!"
        splaylist = self.spotify_connection.user_playlist_create(suid, spotify_playlist_name, spotify_is_public)

        spotify_urls = []

        for song in tqdm(songs):
            if song is None:
                # Should not happen
                continue
            query = song["title"]
            if artist_search:
                for artist in song["artists"]:
                    query += f"artist:"+artist["name"]
            query_result = self.spotify_connection.search(q=query,limit=5)
            if query_result["tracks"]["items"]:
                if query_result["tracks"]["items"][0]["external_urls"]["spotify"]:
                    spotify_urls.append(query_result["tracks"]["items"][0]["external_urls"]["spotify"])
        # spotify dose not accept array bigger than 100
        for ids in self._split_array(spotify_urls, 100):
            self.spotify_connection.playlist_add_items(splaylist["id"], ids)


if __name__ == "__main__":
    yts = YtmToSpotify()
    ytm_name = input("Name of youtube music playlist (Leave blank for liked): ")
    spt_name = input("Name of the new spotify playlist: ")
    if not ytm_name:
        ytm_name = LIKED_MUSIC
    yts.clone_playlist(ytm_name, spt_name)
