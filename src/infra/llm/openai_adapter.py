from langchain_openai import ChatOpenAI
from src.infra.llm.base import BaseLLM

class OpenAIAdapter(BaseLLM):

    def __init__(self, model: str, tools: list | None = None):
        llm = ChatOpenAI(model=model)

        if tools:
            llm = llm.bind_tools(tools)

        self._model = llm

    def invoke(self, messages):
        return self._model.invoke(messages)
