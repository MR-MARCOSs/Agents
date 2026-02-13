from typing import List
from googleapiclient.discovery import build
from langchain.tools import tool
import os


def search_youtube_videos(query: str, max_results: int = 5) -> List[str]:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    if not YOUTUBE_API_KEY:
        return ["Erro: YOUTUBE_API_KEY não configurada."]

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        response = youtube.search().list(
            q=query,
            part="id",
            type="video",
            maxResults=max_results,
            fields="items(id(videoId))"
        ).execute()

        links = [
            f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            for item in response.get("items", [])
        ]

        return links if links else ["Nenhum vídeo encontrado."]

    except Exception as e:
        return [f"Erro ao buscar vídeos: {str(e)}"]


def get_youtube_search_tool():
    @tool
    def youtube_search_tool(query: str) -> str:
        """
        Retorna links de vídeos do YouTube com base no input passado.
        """
        links = search_youtube_videos(query, max_results=5)
        return "\n".join(links)

    return youtube_search_tool
