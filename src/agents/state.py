# src/agents/state.py
from typing import Annotated, Sequence, TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RetrievedDocument:
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    rerank_score: Optional[float] = None
    compressed_content: Optional[str] = None

class AgentState(TypedDict):

    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration: int

    query: str
    expanded_queries: List[str]
    retrieved_docs: List[RetrievedDocument]
    filtered_docs: List[RetrievedDocument]
    reranked_docs: List[RetrievedDocument]
    compressed_context: str
    metadata_filters: Optional[Dict[str, Any]]

    retrieval_metrics: Dict[str, float]
    start_time: Optional[datetime]