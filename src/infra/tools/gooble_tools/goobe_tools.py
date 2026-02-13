from src.infra.tools.google_trends import get_google_trends_tool
from src.infra.tools.search import get_web_search_tool
from src.infra.tools.youtube_link import get_youtube_search_tool


goobe_tools = [get_web_search_tool(), get_google_trends_tool(), get_youtube_search_tool()]