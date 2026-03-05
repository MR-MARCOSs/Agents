import os

CACHE_DIR = "E:/hf" 
os.environ["HF_HOME"] = CACHE_DIR

import json
import torch
from tqdm import tqdm
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModel, AutoConfig
from psycopg import connect
from pgvector.psycopg import register_vector

load_dotenv()
MODEL_NAME = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"
DB_URL = os.getenv("DATABASE_URL", "postgresql://meu_usuario:minha_senha@localhost:5432/banco_vetorial")
BATCH_SIZE = 4 

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Usando dispositivo: {device}")

print("Carregando Tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Carregando Modelo (Implementação Nativa)...")

config = AutoConfig.from_pretrained(MODEL_NAME)

model = AutoModel.from_pretrained(
    MODEL_NAME,
    config=config,
    torch_dtype=torch.float32, 
    trust_remote_code=False    
).to(device)
model.eval()

def get_embeddings(texts):
    """Gera embeddings usando Mean Pooling"""
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=1024, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    attention_mask = inputs['attention_mask']
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return (sum_embeddings / sum_mask).cpu().numpy()

def run_ingestion(json_path):
    if not os.path.exists(json_path):
        print(f"Erro: Arquivo {json_path} não encontrado.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Iniciando ingestão de {len(data)} chunks...")

    with connect(DB_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        register_vector(conn)
        
        
        dim = model.config.hidden_size 
        
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS embeddings_qwen (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    embedding vector({dim})
                )
            """)

        with conn.cursor() as cur:
            for i in tqdm(range(0, len(data), BATCH_SIZE), desc="Processando"):
                batch = data[i:i + BATCH_SIZE]
                texts = [item['text'] for item in batch]
                metadatas = [json.dumps(item['metadata']) for item in batch]
                
                embeddings = get_embeddings(texts)

                with cur.copy("COPY embeddings_qwen (content, metadata, embedding) FROM STDIN") as copy:
                    for text, meta, emb in zip(texts, metadatas, embeddings):
                        copy.write_row((text, meta, str(emb.tolist())))

    print(f"\nConcluído! Tabela: embeddings_qwen | Dimensão: {dim}")

if __name__ == "__main__":
    run_ingestion("arquivo_filtrado.json")