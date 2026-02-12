import os
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage

from src.agents.graph import create_agent_graph
from src.infra.llm.openai_adapter import OpenAIAdapter
from src.infra.tools.search import tools

load_dotenv()


def main():
    llm = OpenAIAdapter(
        model="gpt-4o",
        tools=tools
    )

    agent = create_agent_graph(llm)

    inputs = {
        "messages": [
            HumanMessage(content="Qual a cotação atual do Bitcoin?")
        ]
    }

    for output in agent.stream(inputs, stream_mode="updates"):
        for key, value in output.items():
            print(f"--- Nodo Executado: {key} ---")

    print(output["agent"]["messages"][-1].content)


if __name__ == "__main__":
    main()
