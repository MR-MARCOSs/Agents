
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging

logger = logging.getLogger(__name__)

class MultiQueryProcessor:
    
    def __init__(self, llm, num_queries: int = 3):
        self.llm = llm
        self.num_queries = num_queries
    
    def generate_queries(self, original_query: str) -> List[str]:
        system_prompt = """Você é um especialista em expandir queries de busca para recuperar documentos relevantes.
        Gere {num_queries} versões diferentes da query original que capturem diferentes perspectivas e sinônimos.
        
        Regras:
        1. Mantenha o significado central
        2. Use terminologia médica apropriada
        3. Varie a estrutura gramatical
        4. Inclua sinônimos relevantes
        5. Retorne apenas as queries, uma por linha
        
        Query original: {query}
        """
        
        prompt = system_prompt.format(
            num_queries=self.num_queries,
            query=original_query
        )
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            queries = response.content.strip().split('\n')
            queries = [q.strip() for q in queries if q.strip()]
            queries = queries[:self.num_queries]
            all_queries = [original_query] + queries
            
            logger.info(f"Geradas {len(all_queries)} queries: {all_queries}")
            return all_queries
            
        except Exception as e:
            logger.error(f"Erro ao gerar queries: {e}")
            return [original_query]  
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        if not query and state.get("messages"):
            
            for msg in reversed(state["messages"]):
                if msg.type == "human":
                    query = msg.content
                    break
        
        if query:
            expanded_queries = self.generate_queries(query)
            return {"expanded_queries": expanded_queries}
        
        return {"expanded_queries": [query]}