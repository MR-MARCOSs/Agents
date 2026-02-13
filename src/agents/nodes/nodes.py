from src.infra.llm.base import BaseLLM
from typing import TypedDict

class AgentState(TypedDict):
    messages: list

def call_model(state: AgentState, llm: BaseLLM):
    """Nodo responsável por decidir o que fazer."""
    
    messages = state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response]}

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return "end"
