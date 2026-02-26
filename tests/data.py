import PyPDF2

def extrair_texto_pdf(caminho_pdf):
    """
    Extrai o texto completo de um arquivo PDF.
    """
    texto = ""
    with open(caminho_pdf, "rb") as arquivo:
        leitor = PyPDF2.PdfReader(arquivo)
        for pagina in leitor.pages:
            texto += pagina.extract_text() or ""
    return texto

def pular_caracteres(texto, quantidade_caracteres):
    """
    Remove os primeiros N caracteres de um texto.
    """
    return texto[quantidade_caracteres:]

caracteres_para_pular = 35063+174

texto_completo = extrair_texto_pdf("cardiologia.pdf")

texto_sem_intro = pular_caracteres(texto_completo, caracteres_para_pular)

print("TEXTO SEM OS PRIMEIROS 35063 CARACTERES:\n")
print(texto_sem_intro[:1000])  