import os
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.agents.graph import RAGAgentGraph
from src.infra.llm.openai_adapter import OpenAIAdapter
from src.agents.rag.vector_store import PGVectorStore
from src.agents.rag.embeddings import QwenEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    
    os.environ["HF_HOME"] = "E:/hf"

    logger.info("Inicializando componentes RAG...")

    embeddings = QwenEmbeddings(
        model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct"
    )
    
    vector_store = PGVectorStore(
        connection_string=os.getenv("DATABASE_URL"),
        table_name="embeddings_qwen"
    )
    
    llm = OpenAIAdapter(model="gpt-4o")
    
    
    logger.info("Criando agente RAG...")
    agent = RAGAgentGraph(
        llm=llm,
        vector_store=vector_store,
        embeddings=embeddings,
        tools=[]  
    )
    
    perguntas = [
        {
            "pergunta": "Quais os principais fatores de risco para insuficiência cardíaca?",
            "filtros": {"secao": "Insuficiência Cardíaca"}
        },
        {
            "pergunta": "Como diagnosticar endocardite infecciosa?",
            "filtros": {"secao": "Endocardite"}
        },
        {
            "pergunta": "Qual o tratamento para fibrilação atrial crônica?",
            "filtros": {"ano": "2023"}  
        }
    ]
    
    for item in perguntas:
        logger.info(f"\n--- Processando: {item['pergunta']} ---")
        
        
        result = agent.query(
            question=item['pergunta'],
            metadata_filters=item['filtros']
        )
        
        
        if result and result.get("messages"):
            resposta = result["messages"][-1].content
            print(f"\nPergunta: {item['pergunta']}")
            print(f"Resposta: {resposta}\n")
            print("-" * 80)
        
        
        if result.get("retrieval_metrics"):
            print(f"Métricas: {result['retrieval_metrics']}")
        
        
        if result.get("reranked_docs"):
            print(f"\nDocumentos utilizados: {len(result['reranked_docs'])}")
            for i, doc in enumerate(result['reranked_docs'][:2]):
                print(f"  {i+1}. Score: {doc.rerank_score:.3f} | Seção: {doc.metadata.get('secao', 'N/A')}")

def interactive_mode():
    """Modo interativo para testar o agente"""
    
    logger.info("Inicializando agente RAG para modo interativo...")
    
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("\nERRO: DATABASE_URL não encontrada no arquivo .env")
        print("\nAdicione a seguinte linha ao arquivo .env:")
        print("DATABASE_URL=postgresql://usuario:senha@host:porta/database")
        print("\nExemplo:")
        print("DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cardio_db\n")
        return
    
    embeddings = QwenEmbeddings()
    vector_store = PGVectorStore(db_url)
    llm = OpenAIAdapter(model="gpt-4o")
    
    agent = RAGAgentGraph(llm, vector_store, embeddings)
    
    print("\n" + "="*60)
    print("AGENTE RAG DE CARDIOLOGIA - MODO INTERATIVO")
    print("="*60)
    print("Comandos especiais:")
    print("  /filter [filtro] - aplicar filtro (ex: /filter secao='Cardiologia')")
    print("  /clear - limpar filtros")
    print("  /quit - sair")
    print("="*60 + "\n")
    
    current_filters = {}
    
    while True:
        pergunta = input("\nSua dúvida (ou comando): ").strip()
        
        if pergunta.lower() == '/quit':
            break
        elif pergunta.lower() == '/clear':
            current_filters = {}
            print("Filtros limpos!")
            continue
        elif pergunta.startswith('/filter'):
            try:
                
                filtro_str = pergunta[8:].strip()
                if '=' in filtro_str:
                    key, value = filtro_str.split('=', 1)
                    current_filters[key.strip()] = value.strip().strip("'\"")
                    print(f"Filtro aplicado: {key} = {value}")
            except:
                print("Formato inválido. Use: /filter chave='valor'")
            continue
        
        if not pergunta:
            continue
        
        print("\nProcessando...")
        
        
        result_stream = agent.query(
            question=pergunta,
            metadata_filters=current_filters if current_filters else None,
            stream=True  
        )
        
        
        etapas_mostradas = set()
        steps = []
        for step in result_stream:
            steps.append(step)
            for node, output in step.items():
                if node not in etapas_mostradas:
                    print(f"   ▶️  {node}")
                    etapas_mostradas.add(node)
        
        
        if steps and steps[-1].get("generate_response"):
            resposta = steps[-1]["generate_response"]["messages"][-1].content
            print(f"\n Resposta: {resposta}\n")
        
        
        if steps and steps[-1].get("generate_response"):
            state = steps[-1]["generate_response"]
            if state.get("retrieval_metrics"):
                print(f"📊 Documentos recuperados: {state['retrieval_metrics'].get('num_docs', 0)}")

if __name__ == "__main__":
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()