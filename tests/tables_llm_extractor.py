import fitz
import pytesseract
from PIL import Image
import io
import base64
import json
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

def gerar_descricoes_inteligentes(caminho_pdf):
    descricoes = []
    doc = fitz.open(caminho_pdf)

    todas_imagens = []

    for pagina_num in range(len(doc)):
        pagina = doc[pagina_num]
        imagens = pagina.get_images()

        for img in imagens:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            todas_imagens.append({
                "pagina": pagina_num + 1,
                "image_bytes": image_bytes
            })

    if len(todas_imagens) > 4:
        imagens_filtradas = todas_imagens[2:-2]
    else:
        imagens_filtradas = []
    
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    else:
        client = None

    for item in imagens_filtradas:
        pagina_num = item["pagina"]
        image_bytes = item["image_bytes"]

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        if client:
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": """
Analise esta imagem médica de cardiologia e gere uma descrição estruturada para indexação em base vetorial.

Siga rigorosamente o formato abaixo:

TIPO:
CONTEXTO CLÍNICO:
DADOS OBSERVADOS:
INTERPRETAÇÃO MÉDICA:
CONCEITOS RELACIONADOS:
PALAVRAS-CHAVE:

Use linguagem técnica médica.
Não faça suposições além do que está visível.
Seja altamente específico.
                                """
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{image_base64}",
                            },
                        ],
                    }
                ],
            )

            descricao = response.output[0].content[0].text

        else:
            descricao = pytesseract.image_to_string(
                Image.open(io.BytesIO(image_bytes))
            )

        descricao_lower = descricao.lower()

        if "gráfico" in descricao_lower or "grafico" in descricao_lower:
            tipo = "grafico"
        elif "tabela" in descricao_lower:
            tipo = "tabela"
        elif "eletrocardiograma" in descricao_lower:
            tipo = "ecg"
        else:
            tipo = "imagem_medica"

        descricoes.append({
            "id": str(uuid.uuid4()),
            "pagina": pagina_num,
            "tipo": tipo,
            "conteudo": descricao
        })

    doc.close()
    return descricoes


if __name__ == "__main__":

    caminho_pdf = "cardiologia.pdf"
    descricoes = gerar_descricoes_inteligentes(caminho_pdf)
    nome_saida = "cardiologia_rag.jsonl"

    with open(nome_saida, "w", encoding="utf-8") as f:
        for item in descricoes:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nArquivo salvo como {nome_saida}")