import PyPDF2
import re

def extrair_e_limpar_diretriz(caminho_pdf, carac_pular, pag_ini_remover, pag_fim_remover, remover_final_chars):
    
    texto_bruto = ""
    print("Extraindo texto do PDF...")
    
    with open(caminho_pdf, "rb") as arquivo:
        leitor = PyPDF2.PdfReader(arquivo)
        
        total_paginas = len(leitor.pages)
        print(f"Total de páginas no PDF: {total_paginas}")
        
        for i, pagina in enumerate(leitor.pages):
            if pag_ini_remover - 1 <= i <= pag_fim_remover - 1:
                continue
            
            texto_bruto += pagina.extract_text() or ""
    
    total_antes = len(texto_bruto)
    texto_processado = texto_bruto[carac_pular:]
    if remover_final_chars <= len(texto_processado):
        texto_processado = texto_processado[:-remover_final_chars]
    else:
        print("tentativa de remover mais caracteres do que o texto possui.")
        texto_processado = ""
 
    header_str = "Atualização da Diretriz de Prevenção Cardiovascular da Sociedade Brasileira de Cardiologia – 2019"
    header_esc = re.escape(header_str)
    
    rodape_esc = re.escape("Arq Bras Cardiol. 2019; 113(4):787-891")
    extra = "Atualização"

    
    for num in range(795, 892):
        n = str(num)
        padrao_bloco = rf"({n}\s*{extra}\s*{header_esc}|{extra}\s*{n}\s*{header_esc}|{header_esc}\s*{extra}\s*{n}|{header_esc}\s*{extra}|{n}\s*{header_esc}|{header_esc}\s*{n})"
        texto_processado = re.sub(padrao_bloco, "", texto_processado)

    texto_processado = texto_processado.replace(header_str, "")
    texto_processado = re.sub(rodape_esc, "", texto_processado)

    for num in range(795, 892):
        texto_processado = re.sub(rf"\b{num}\b", "", texto_processado)

    texto_processado = re.sub(r'[ \t]+', ' ', texto_processado)
    texto_processado = re.sub(r'\n\s*\n', '\n\n', texto_processado)
    texto_processado = texto_processado.strip()

    total_apos = len(texto_processado)

    return texto_processado, total_antes, total_apos

pulo = 35063 + 174
pagina_inicio_remover = 87
pagina_fim_remover = 105
remover_ultimos_chars = 368+9+105

resultado, contagem_ini, contagem_fim = extrair_e_limpar_diretriz(
    "cardiologia.pdf",
    pulo,
    pagina_inicio_remover,
    pagina_fim_remover,
    remover_ultimos_chars
)

print("-" * 60)
print(f"CONTAGEM DE CARACTERES:")
print(f"Total após remover páginas: {contagem_ini}")
print(f"Total após limpeza final:   {contagem_fim}")
print(f"Diferença:                  {contagem_ini - contagem_fim}")
print("-" * 60)

print(f"Ocorrências de 'Atualização': {resultado.count('Atualização')}")
print("-" * 60)

with open("diretriz_limpa.txt", "w", encoding="utf-8") as f:
    f.write(resultado)

print("Arquivo salvo: 'diretriz_limpa.txt'.")

print("\nPrimeiros 500 caracteres:\n")
print(resultado[:500])

print("-" * 60)

print("\nÚltimos 1500 caracteres:\n")
print(resultado[-1500:])