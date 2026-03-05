import os
CACHE_DIR = "E:/hf" 
os.environ["HF_HOME"] = CACHE_DIR
import json
import torch
from tqdm import tqdm
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModel
from psycopg import connect
from pgvector.psycopg import register_vector

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://meu_usuario:minha_senha@localhost:5432/banco_vetorial")
MODEL_NAME = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Carregando modelo no {device}...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32,
    trust_remote_code=False 
).to(device)
model.eval()

def get_query_embedding(text):

    instruction = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "
    full_text = f"{instruction}{text}"
    
    inputs = tokenizer(full_text, padding=True, truncation=True, max_length=1024, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)

    attention_mask = inputs['attention_mask']
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    embedding = (sum_embeddings / sum_mask).cpu().numpy()[0]
    
    return embedding

def search(query_text, limit=3):
    query_vector = get_query_embedding(query_text)
    with connect(DB_URL) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            
            cur.execute("""
                SELECT content, metadata, 1 - (embedding <=> %s::vector) AS similarity
                FROM embeddings_qwen
                ORDER BY similarity DESC
                LIMIT %s
            """, (query_vector, limit))
            
            return cur.fetchall()

if __name__ == "__main__":
    print("\n--- TESTE DE BUSCA SEMÂNTICA (QWEN OPEN SOURCE) ---")
    pergunta = input("Digite sua dúvida clínica: ")

    try:
        resultados = search(pergunta)
        
        print(f"\nResultados encontrados para: '{pergunta}'\n")
        if not resultados:
            print("Nenhum resultado encontrado na tabela 'embeddings_qwen'.")
            
        for i, (content, metadata, score) in enumerate(resultados, 1):
            print(f"Resultado {i} | Score de Similaridade: {score:.4f}")
            print(f"Seção: {metadata.get('secao', 'N/A')}")
            print(f"Conteúdo: {content[:400]}...") 
            print("-" * 60)

    except Exception as e:
        print(f"Erro ao buscar: {str(e)}")