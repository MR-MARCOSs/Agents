from src.infra.llm.base import BaseLLM
from typing import TypedDict, List
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: list
    iteration: int

def call_model(state: AgentState, llm: BaseLLM):
    messages = state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": list(messages) + [response],
        "iteration": state["iteration"] + 1
    }

MAX_ITERATIONS = 5

def should_continue(state: AgentState):
    if state["iteration"] >= MAX_ITERATIONS:
        return "end"

    last_message = state["messages"][-1] if state["messages"] else None
    if last_message and getattr(last_message, "tool_calls", None):
        return "tools"

    return "end"
