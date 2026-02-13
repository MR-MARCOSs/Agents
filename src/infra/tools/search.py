from langchain_community.tools import DuckDuckGoSearchRun

def get_web_search_tool():
    return DuckDuckGoSearchRun(max_results=3)
