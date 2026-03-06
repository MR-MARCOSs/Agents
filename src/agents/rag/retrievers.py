
from typing import List, Dict, Any, Optional
from src.agents.rag.vector_store import PGVectorStore
from src.agents.rag.embeddings import QwenEmbeddings
from src.agents.state import RetrievedDocument
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedRetriever:

    def __init__(
        self,
        vector_store: PGVectorStore,
        embeddings: QwenEmbeddings,
        default_k: int = 15,
        min_score: float = 0.5
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.default_k = default_k
        self.min_score = min_score
    
    def _parse_metadata_filters(self, query: str) -> Dict[str, Any]:
        
        filters = {}
        
        
        keywords = {
            "secao": ["capítulo", "seção", "parte"],
            "ano": ["2023", "2024", "recente"],
            "especialidade": ["cardiologia", "pediatria", "clínica"]
        }
        
        for field, terms in keywords.items():
            if any(term in query.lower() for term in terms):
                if field == "ano":
                    
                    import re
                    year_match = re.search(r'\b(202[0-9])\b', query)
                    if year_match:
                        filters[field] = year_match.group(1)
                else:
                    
                    pass
        
        return filters
    
    def retrieve_with_filters(
        self,
        query: str,
        query_vector: np.ndarray,
        metadata_filters: Optional[Dict] = None,
        k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """
        Recupera documentos com filtros de metadados
        """
        k = k or self.default_k
        
        if not metadata_filters:
            metadata_filters = self._parse_metadata_filters(query)
        
        logger.info(f"Buscando com filtros: {metadata_filters}")
        results = self.vector_store.similarity_search(
            query_vector=query_vector,
            k=k,
            metadata_filter=metadata_filters,
            threshold=self.min_score
        )

        documents = [
            RetrievedDocument(
                content=r["content"],
                metadata=r["metadata"],
                similarity_score=r["similarity"]
            )
            for r in results
        ]
        
        logger.info(f"Recuperados {len(documents)} documentos com filtros")
        return documents
    
    def multi_query_retrieval(
        self,
        queries: List[str],
        metadata_filters: Optional[Dict] = None
    ) -> List[RetrievedDocument]:

        all_docs = []
        seen_contents = set()
        
        logger.info(f"Iniciando multi-query retrieval com {len(queries)} queries")
        
        for i, query in enumerate(queries):
            logger.info(f"Processando query {i+1}/{len(queries)}: {query[:50]}...")
            logger.info("Gerando embedding...")
            query_vector = self.embeddings.embed_query(query)
            logger.info(f"Embedding gerado: shape={query_vector.shape}")
            logger.info("Buscando documentos no vector store...")
            docs = self.retrieve_with_filters(
                query=query,
                query_vector=query_vector,
                metadata_filters=metadata_filters,
                k=self.default_k // len(queries)  
            )
            logger.info(f"Encontrados {len(docs)} documentos para query {i+1}")

            for doc in docs:
                if doc.content not in seen_contents:
                    seen_contents.add(doc.content)
                    all_docs.append(doc)
        
        logger.info(f"Total documentos após multi-query: {len(all_docs)}")
        return all_docs
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó do LangGraph para retrieval"""
        
        queries = state.get("expanded_queries", [])
        if not queries and state.get("query"):
            queries = [state["query"]]
        
        metadata_filters = state.get("metadata_filters", {})
        documents = self.multi_query_retrieval(queries, metadata_filters)
        
        return {
            "retrieved_docs": documents,
            "retrieval_metrics": {
                "num_docs": len(documents),
                "num_queries": len(queries)
            }
        }