
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.state import RetrievedDocument
import logging
import tiktoken

logger = logging.getLogger(__name__)

class ContextCompressor:
    
    def __init__(
        self,
        llm,
        max_tokens: int = 2000,
        compression_ratio: float = 0.3
    ):
        self.llm = llm
        self.max_tokens = max_tokens
        self.compression_ratio = compression_ratio
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))
    
    def _compress_document(
        self,
        query: str,
        document: RetrievedDocument
    ) -> str:
        system_prompt = """Você é um compressor de documentos especializado.
        Sua tarefa é extrair APENAS as informações mais relevantes para responder à query.
        
        Regras:
        1. Mantenha FATOS e DADOS importantes
        2. Remova exemplos redundantes
        3. Preserve terminologia técnica
        4. Mantenha a coerência
        5. Seja CONCISO
        
        Query: {query}
        
        Documento original:
        {content}
        
        Versão comprimida (apenas informações relevantes):
        """
        
        prompt = system_prompt.format(
            query=query,
            content=document.content
        )
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            compressed = response.content.strip()
            original_tokens = self._count_tokens(document.content)
            compressed_tokens = self._count_tokens(compressed)
            ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0
            
            logger.info(f"Documento comprimido: {original_tokens} → {compressed_tokens} tokens (ratio: {ratio:.2f})")
            
            return compressed
            
        except Exception as e:
            logger.error(f"Erro na compressão: {e}")
            return document.content  
    
    def compress(
        self,
        query: str,
        documents: List[RetrievedDocument]
    ) -> str:
        compressed_docs = []
        total_tokens = 0
        
        for doc in documents:
            
            compressed = self._compress_document(query, doc)
            doc.compressed_content = compressed
            
            tokens = self._count_tokens(compressed)
            
            if total_tokens + tokens <= self.max_tokens:
                compressed_docs.append(compressed)
                total_tokens += tokens
            else:
                
                aggressive_prompt = f"Resuma em UMA frase: {compressed}"
                try:
                    response = self.llm.invoke([HumanMessage(content=aggressive_prompt)])
                    summary = response.content.strip()
                    
                    if total_tokens + self._count_tokens(summary) <= self.max_tokens:
                        compressed_docs.append(summary)
                        total_tokens += self._count_tokens(summary)
                except:
                    break
        
        context = "\n\n---\n\n".join(compressed_docs)
        
        logger.info(f"Contexto final: {total_tokens} tokens em {len(compressed_docs)} documentos")
        
        return context
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        documents = state.get("reranked_docs", [])
        
        if query and documents:
            compressed_context = self.compress(query, documents)
            return {"compressed_context": compressed_context}
        
        return {"compressed_context": ""}