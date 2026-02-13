from langchain_community.utilities.google_trends import GoogleTrendsAPIWrapper
from langchain_community.tools.google_trends import GoogleTrendsQueryRun

def get_google_trends_tool():
    return GoogleTrendsQueryRun(
        api_wrapper=GoogleTrendsAPIWrapper()
    )
