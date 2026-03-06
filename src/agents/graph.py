
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Dict, Any
import logging
from datetime import datetime
from langchain_core.messages import HumanMessage
from .state import AgentState
from .nodes.query_processor import MultiQueryProcessor
from src.agents.rag.retrievers import AdvancedRetriever
from .nodes.reranker import ReRanker
from .nodes.compressor import ContextCompressor
from src.infra.llm.base import BaseLLM
from src.agents.rag.vector_store import PGVectorStore
from src.agents.rag.embeddings import QwenEmbeddings

logger = logging.getLogger(__name__)

class RAGAgentGraph:
    
    def __init__(
        self,
        llm: BaseLLM,
        vector_store: PGVectorStore,
        embeddings: QwenEmbeddings,
        tools: list = None
    ):
        self.llm = llm
        self.tools = tools or []
        
        self.query_processor = MultiQueryProcessor(llm, num_queries=3)
        self.retriever = AdvancedRetriever(vector_store, embeddings)
        self.reranker = ReRanker()
        self.compressor = ContextCompressor(llm)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:        
        workflow = StateGraph(AgentState)

        workflow.add_node("process_query", self.query_processor)
        workflow.add_node("retrieve", self.retriever)
        workflow.add_node("rerank", self.reranker)
        workflow.add_node("compress", self.compressor)
        workflow.add_node("generate_response", self._generate_response)
        
        if self.tools:
            workflow.add_node("tools", ToolNode(self.tools))
        
        workflow.set_entry_point("process_query")
        workflow.add_edge("process_query", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "compress")
        workflow.add_edge("compress", "generate_response")
        
        if self.tools:
            workflow.add_conditional_edges(
                "generate_response",
                self._should_use_tools,
                {
                    "tools": "tools",
                    "end": END,
                }
            )
            workflow.add_edge("tools", "generate_response")
        else:
            workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        context = state.get("compressed_context", "")
        
        
        if not query and state.get("messages"):
            for msg in reversed(state["messages"]):
                if msg.type == "human":
                    query = msg.content
                    break
        
        system_prompt = f"""Você é um assistente especializado em cardiologia.
        Use o contexto abaixo para responder à pergunta do usuário.
        
        Contexto:
        {context}
        
        Diretrizes:
        1. Baseie-se ESTRITAMENTE no contexto fornecido
        2. Se a informação não estiver no contexto, diga que não sabe
        3. Cite as fontes quando relevante (seção do documento)
        4. Use linguagem clara e acessível
        5. Seja preciso e evite alucinações
        
        Pergunta: {query}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=system_prompt)])
            
            
            messages = list(state.get("messages", []))
            messages.append(response)
            
            return {
                "messages": messages,
                "iteration": state.get("iteration", 0) + 1
            }
            
        except Exception as e:
            logger.error(f"Erro na geração: {e}")
            return {"messages": state.get("messages", [])}
    
    def _should_use_tools(self, state: Dict[str, Any]) -> str:
        """Decide se deve usar tools"""
        
        last_message = state["messages"][-1] if state["messages"] else None
        
        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return "end"
    
    def query(
        self,
        question: str,
        metadata_filters: Dict[str, Any] = None,
        stream: bool = False
    ):
        """
        Interface principal para fazer queries ao agente RAG
        """
        start_time = datetime.now()
        
        initial_state = {
            "messages": [],
            "query": question,
            "metadata_filters": metadata_filters or {},
            "expanded_queries": [],
            "retrieved_docs": [],
            "reranked_docs": [],
            "compressed_context": "",
            "iteration": 0,
            "retrieval_metrics": {},
            "start_time": start_time
        }
        
        if stream:
            return self.graph.stream(initial_state)
        else:
            final_state = self.graph.invoke(initial_state)
            
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Query processada em {elapsed:.2f}s")
            
            return final_state