
import torch
import numpy as np
from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import logging
from functools import lru_cache
import hashlib
from contextlib import nullcontext

logger = logging.getLogger(__name__)

class QwenEmbeddings:
    
    def __init__(self, model_name: str = "Alibaba-NLP/gte-Qwen2-1.5B-instruct", device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Carregando modelo {model_name} no {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            trust_remote_code=False
        ).to(self.device)
        self.model.eval()
        
        self.cache = {}
        self.cache_size = 1000
    
    def _get_cache_key(self, text: str, is_query: bool) -> str:
        text_hash = hashlib.md5(f"{text}:{is_query}".encode()).hexdigest()
        return text_hash
    
    @lru_cache(maxsize=1000)
    def _encode_single(self, text: str, is_query: bool) -> np.ndarray:
        return self.encode([text], is_query)[0]
    
    def encode(
        self, 
        texts: List[str], 
        is_query: bool = False,
        batch_size: int = 32
    ) -> List[np.ndarray]:
        logger.info(f"Iniciando encode de {len(texts)} textos (is_query={is_query})")
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"Processando batch {i//batch_size + 1} com {len(batch_texts)} textos")
            
            
            if is_query:
                instruction = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "
                batch_texts = [f"{instruction}{text}" for text in batch_texts]
            
            
            logger.info("Tokenizando...")
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=1024,
                return_tensors="pt"
            ).to(self.device)
            logger.info(f"Tokenização completa: {inputs['input_ids'].shape}")
            
            
            logger.info("Gerando embeddings com o modelo...")
            autocast_context = torch.cuda.amp.autocast() if self.device == "cuda" else nullcontext()
            with torch.no_grad(), autocast_context:
                outputs = self.model(**inputs)
                
                
                attention_mask = inputs['attention_mask']
                token_embeddings = outputs.last_hidden_state
                
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                
                batch_embeddings = (sum_embeddings / sum_mask).cpu().numpy()
            logger.info(f"Embeddings gerados: shape={batch_embeddings.shape}")
            
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"Encode completo: {len(all_embeddings)} embeddings gerados")
        return all_embeddings
    
    def embed_query(self, text: str) -> np.ndarray:
        return self.encode([text], is_query=True)[0]
    
    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        return self.encode(texts, is_query=False)