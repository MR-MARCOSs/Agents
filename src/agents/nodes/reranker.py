
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import torch
import numpy as np
from src.agents.state import RetrievedDocument
import logging

logger = logging.getLogger(__name__)

class ReRanker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = None,
        batch_size: int = 32
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Carregando reranker {model_name} no {self.device}")
        
        self.model = CrossEncoder(model_name, device=self.device)
        self.batch_size = batch_size
    
    def rerank(
        self,
        query: str,
        documents: List[RetrievedDocument],
        top_k: int = 5
    ) -> List[RetrievedDocument]:
        if not documents:
            return documents
        
        pairs = [[query, doc.content] for doc in documents]
        
        all_scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch_pairs = pairs[i:i + self.batch_size]
            batch_scores = self.model.predict(batch_pairs)
            all_scores.extend(batch_scores)
        
        scores = np.array(all_scores)
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
        
        for doc, score in zip(documents, scores):
            doc.rerank_score = float(score)
        
        reranked = sorted(
            documents,
            key=lambda x: x.rerank_score or 0,
            reverse=True
        )
        
        logger.info(f"Re-ranking completo: top score = {reranked[0].rerank_score:.4f}")
        
        return reranked[:top_k]
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        documents = state.get("retrieved_docs", [])
        
        if query and documents:
            reranked = self.rerank(query, documents)
            return {"reranked_docs": reranked}
        
        return {"reranked_docs": documents}