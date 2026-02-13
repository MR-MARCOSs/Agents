from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .nodes.nodes import call_model, should_continue
from infra.tools.gooble_tools.goobe_tools import goobe_tools
from src.infra.llm.base import BaseLLM


def create_agent_graph(llm: BaseLLM):
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", lambda state: call_model(state, llm))
    workflow.add_node("tools", ToolNode(goobe_tools))

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_edge("tools", "agent")

    return workflow.compile()
