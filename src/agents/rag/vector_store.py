
import os
from typing import List, Dict, Any, Optional
import numpy as np
from psycopg import connect
from pgvector.psycopg import register_vector
from contextlib import contextmanager
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class PGVectorStore:
    
    def __init__(self, connection_string: str, table_name: str = "embeddings_qwen"):
        self.connection_string = connection_string
        self.table_name = table_name
        
    @contextmanager
    def get_connection(self):
        conn = connect(self.connection_string)
        try:
            register_vector(conn)
            yield conn
        finally:
            conn.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def similarity_search(
        self, 
        query_vector: np.ndarray, 
        k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        logger.info(f"Iniciando similarity_search: k={k}, threshold={threshold}")
        logger.info(f"Query vector shape: {query_vector.shape}")
        
        try:
            logger.info("Tentando conectar ao banco...")
            with self.get_connection() as conn:
                logger.info("Conexão estabelecida!")
                with conn.cursor() as cur:
                    logger.info("Cursor criado, construindo query...")
                    
                    base_query = f"""
                        SELECT 
                            content, 
                            metadata, 
                            1 - (embedding <=> %s::vector) AS similarity
                        FROM {self.table_name}
                        WHERE 1=1
                    """
                    params = [query_vector.tolist()]  
                    
                    logger.info(f"Filtros de metadata: {metadata_filter}")
                    
                    if metadata_filter:
                        for key, value in metadata_filter.items():
                            if isinstance(value, dict):
                                
                                for op, val in value.items():
                                    if op == "$gt":
                                        base_query += f" AND (metadata->>'{key}')::float > %s"
                                    elif op == "$gte":
                                        base_query += f" AND (metadata->>'{key}')::float >= %s"
                                    elif op == "$lt":
                                        base_query += f" AND (metadata->>'{key}')::float < %s"
                                    elif op == "$lte":
                                        base_query += f" AND (metadata->>'{key}')::float <= %s"
                                    params.append(val)
                            else:
                                
                                base_query += f" AND metadata->>'{key}' = %s"
                                params.append(value)

                    base_query += """
                        AND (1 - (embedding <=> %s::vector)) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s
                    """
                    params.extend([query_vector.tolist(), threshold, k])
                    
                    logger.info(f"Executando query SQL com {len(params)} parâmetros...")
                    
                    cur.execute(base_query, params)
                    logger.info("Query executada, buscando resultados...")
                    results = cur.fetchall()
                    logger.info(f"Encontrados {len(results)} resultados")
                    formatted = [
                        {
                            "content": r[0],
                            "metadata": r[1],
                            "similarity": float(r[2])
                        }
                        for r in results
                    ]
                    logger.info("Resultados formatados com sucesso")
                    return formatted
        except Exception as e:
            logger.error(f"Erro na similarity_search: {type(e).__name__}: {str(e)}")
            raise
    
    def hybrid_search(
        self,
        query_text: str,
        query_vector: np.ndarray,
        k: int = 10,
        alpha: float = 0.5  
    ) -> List[Dict[str, Any]]:
        """
        Busca híbrida combinando texto e vetores
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH vector_scores AS (
                        SELECT 
                            content,
                            metadata,
                            1 - (embedding <=> %s::vector) AS vector_score
                        FROM {self.table_name}
                        ORDER BY vector_score DESC
                        LIMIT %s
                    ),
                    text_scores AS (
                        SELECT 
                            content,
                            metadata,
                            ts_rank(to_tsvector('portuguese', content), plainto_tsquery('portuguese', %s)) AS text_score
                        FROM {self.table_name}
                        WHERE to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', %s)
                    )
                    SELECT 
                        COALESCE(v.content, t.content) as content,
                        COALESCE(v.metadata, t.metadata) as metadata,
                        (COALESCE(v.vector_score, 0) * %s + COALESCE(t.text_score, 0) * (1 - %s)) AS hybrid_score
                    FROM vector_scores v
                    FULL OUTER JOIN text_scores t ON v.content = t.content
                    ORDER BY hybrid_score DESC
                    LIMIT %s
                """, (query_vector, k * 2, query_text, query_text, alpha, alpha, k))
                
                return [{"content": r[0], "metadata": r[1], "score": float(r[2])} for r in cur.fetchall()]