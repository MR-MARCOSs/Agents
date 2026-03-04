import re

def processar_relatorio(caminho_arquivo_md, texto_sumario):
    
    linhas_sumario = texto_sumario.split('\n')
    topicos_esperados = []
    buffer_titulo = ""
    for linha in linhas_sumario:
        linha = linha.strip()
        if not linha: continue
        linha_limpa = re.sub(r'\s*\.+\s*\d+$', '', linha)
        
        if re.match(r'^(\d+(\.\d+)*\.?|Introdução|Referências)', linha_limpa):
            if buffer_titulo:
                topicos_esperados.append(buffer_titulo.strip())
            buffer_titulo = linha_limpa
        else:
            
            buffer_titulo += " " + linha_limpa
    if buffer_titulo:
        topicos_esperados.append(buffer_titulo.strip())

    
    try:
        with open(caminho_arquivo_md, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except FileNotFoundError:
        return "Erro: Arquivo Markdown não encontrado."

    resultados = []
    posicoes = []
    for titulo in topicos_esperados:

        pattern = re.escape(titulo).replace(r'\ ', r'\s+')
        match = re.search(pattern, conteudo, re.IGNORECASE)
        
        if match:
            posicoes.append({
                'titulo': titulo,
                'inicio': match.start(),
                'fim_titulo': match.end(),
                'encontrado': True
            })
        else:
            posicoes.append({
                'titulo': titulo,
                'encontrado': False
            })

    encontrados = [p for p in posicoes if p['encontrado']]
    
    for i in range(len(posicoes)):
        item = posicoes[i]
        if not item['encontrado']:
            resultados.append(f"❌ [NÃO ENCONTRADO] {item['titulo']}")
            continue
        
        
        proximo_inicio = len(conteudo)
        for sucessor in encontrados:
            if sucessor['inicio'] > item['inicio']:
                proximo_inicio = sucessor['inicio']
                break
        
        
        total_chars = proximo_inicio - item['fim_titulo']
        resultados.append(f"✅ [OK] {item['titulo']} | Caracteres: {max(0, total_chars)}")

    
    print(f"{'='*60}")
    print(f"{'RELATÓRIO DE ANÁLISE DE DOCUMENTO':^60}")
    print(f"{'='*60}\n")
    
    for res in resultados:
        print(res)

sumario_raw = """
Introdução ............................................................................................795
1. Estratificação de Risco ..................................................................795
1.1. Estratificação de Risco Cardiovascular para Prevenção e Tratamento  
da Aterosclerose......................................................................................795
1.2. Risco Muito Alto ...............................................................................796
1.3. Risco Alto .........................................................................................796
1.4. Risco Intermediário ..........................................................................796
1.5. Risco Baixo ......................................................................................796
2. Dislipidemia .....................................................................................797
2.1. Introdução ........................................................................................797
2.1.1. Hipercolesterolemia Familiar .......................................................799
2.2. Tratamento das Dislipidemias ..........................................................800
2.2.1. Terapia Não-Farmacológica ..........................................................800
2.2.2. Tratamento Medicamentoso com Foco na Hipercolesterolemia ....800
2.2.3. Tratamento Medicamentoso com Foco em Hipertrigliceridemia ...802
3. Diabetes e Síndrome Metabólica .................................................803
3.1. Risco Miocárdico ..............................................................................803
3.1.1. Estimativa do Risco Miocárdico ...................................................804
3.1.2. Terapias Preventivas para Indivíduos de Alto e Muito Alto Risco 
para insuficiência cardíaca em 5 Anos e Prevenção Secundária para 
aqueles com insuficiência cardíaca Manifesta .......................................805
3.1.3. Terapias com Foco no Remodelamento Cardíaco ........................805
3.2. Risco Aterosclerótico ........................................................................806
3.2.1. Síndrome Metabólica, Diabetes Mellitus e o Corolário Contínuo da 
Doença Arterial Coronária .....................................................................806
3.2.2. Estratégias em Prevenção Primária para Doença Arterial Coronária 
nos Indivíduos com Síndrome Metabólica e Diabetes Mellitus .............806
3.2.3. Predição do Risco Individual de Doença Arterial Coronária em 
Pacientes com Síndrome Metabólica e Diabetes Mellitus .....................806
3.2.4. Calculadoras de Risco ..................................................................807
3.2.5. Escore de Cálcio Coronário ..........................................................807
3.2.6. Metas Lipídicas em Prevenção Primária para Indivíduos com 
Síndrome Metabólica e Diabetes Mellitus .............................................807
3.2.7. Aspirina em Prevenção Primária ..................................................808
3.2.8. Hipoglicemiantes em Pacientes com Diabetes Mellitus...............808
4. Obesidade e Sobrepeso .................................................................809
4.1. Introdução ........................................................................................809
4.2. Prevenção Primária ..........................................................................810
5. Hipertensão Arterial .......................................................................812
5.1. Introdução ........................................................................................812
5.2. Atividade Física e Hipertensão .........................................................813
5.3. Fatores Psicossociais .......................................................................813
5.4. Dietas que Favorecem a Prevenção e o Controle da Hipertensão 
Arterial ....................................................................................................814
5.5. Álcool e Hipertensão ........................................................................814
5.6. Redução do Peso e Prevenção da Hipertensão Arterial ....................815
5.7. Dieta Hipossódica na Prevenção da Hipertensão Arterial .................816
5.8. Controle Anti-Hipertensivo em Prevenção Primária na Síndrome 
Metabólica e Diabetes Mellitus ................................................................816
6. Vitaminas e Ácidos Graxos Ômega-3 ..........................................817
6.1. Introdução ........................................................................................817
6.2. Carotenoides ....................................................................................818
6.3. Vitamina E ........................................................................................818
6.4. Vitamina D .......................................................................................818
6.5. Vitamina K .......................................................................................819
6.6. Vitamina C........................................................................................819
6.7. Vitaminas B e Folato .........................................................................819
6.8. Ácidos Graxos Poliinsaturados Ômega-3 de Origem Marinha 
(Docosaexaenoico e Eicosapentaenoico) .................................................819
6.9. Efeitos do Ômega-3 sobre o Perfil Lipídico........................................819
6.10. Ômega-3 e Desfechos Cardiovasculares .........................................820
6.11. Ômega-3 na Insuficiência Cardíaca ................................................821
6.12. Ácidos Graxos Poliinsaturados Ômega-3 de Origem Vegetal ..........821
7. Tabagismo ........................................................................................822
7.1. Introdução ........................................................................................822
7.2. Estratégias no Combate à Iniciação de Fumar ..................................823
7.3. Como Tratar a Dependência Psicológica do Fumante .......................823
7.4. Tratamento Farmacológico do Tabagismo ........................................824
7.4.1. Intervenção Secundária Tabagismo ..............................................824
7.5. Associações de Medicamentos Antitabaco .......................................826
7.6. Propostas Futuras .............................................................................826
7.7. Dispositivos Eletrônicos com Nicotina (Cigarro Eletrônico, Cigarro 
Aquecido, Pen-Drives) ..............................................................................827
7.8. Narguilé ............................................................................................827
7.9. Conclusão .........................................................................................827
8. Atividade Física, Exercício Físico e Esporte ................................831
8.1. Introdução ........................................................................................831
8.2. Conceitos e Expressões Relevantes na Atividade Física ....................831
8.3. Principais Efeitos Agudos e Crônicos do Exercício.............................832
8.4. Fundamentação Epidemiológica dos Benefícios do Exercício 
Físico ......................................................................................................832
8.5. Riscos da Prática da Atividade Física, do Exercício Físico e do 
Esporte ....................................................................................................834
8.6. Recomendações de Exercício e Atividade Física ...............................834
8.7. Prescrição de Exercícios ...................................................................834
8.8. Atividade Física Formal e Informal: Incentivar o Encaminhamento, a 
Implementação e a Adesão .....................................................................835
8.9. Mensagens Finais .............................................................................836
9. Espiritualidade e Fatores Psicossociais em Medicina 
Cardiovascular .....................................................................................836
9.1. Conceitos, Definições e Racional ......................................................836 
9.1.1. Introdução ....................................................................................836
9.1.2. Conceitos e Definições .................................................................836
9.1.3. Racional e Mecanismos ................................................................837
9.2. Anamnese Espiritual e Escalas para Mensuração da Religiosidade e 
Espiritualidade ........................................................................................838
9.2.1. Porque Abordar a Espiritualidade e Religiosidade .......................838
9.2.2. Objetivos da Avaliação da Espiritualidade e Religiosidade .........838
9.2.3. Como Abordar a Espiritualidade e Religiosidade do Paciente .....838
9.2.4. Escalas e Instrumentos para Avaliar Espiritualidade e 
Religiosidade ..........................................................................................838
9.2.5. Atitudes e Condutas após a Anamnese Espiritual ........................839
9.3. Prevenção Primária ..........................................................................841
9.4. Prevenção Secundária ......................................................................841
9.5. Recomendações para a Prática Clínica ............................................843
10. Doenças Associadas, Fatores Socioeconômicos e Ambientais 
na Prevenção Cardiovascular ............................................................845
10.1. Introdução ......................................................................................845
10.2. Fatores Socioeconômicos e Risco Cardiovascular...........................845
10.3. Fatores Ambientais e Risco Cardiovascular ....................................846
10.4. Vacinação no Cardiopata ................................................................847
10.4.1. Prevenção das Infecções Respiratórias nos Cardiopatas ...........847
10.4.2. Quais Vacinas? ...........................................................................847
10.5. Doença Arterial Periférica de Extremidades Inferiores ...................848
10.5.1. Contexto .....................................................................................848
10.5.2. Inter-Relação entre e os Diversos Fatores de Risco Cardiovascular 
e a Doença Arterial Periférica de Extremidades Inferiores ....................849
10.5.3. Resumo da Localização Anatômica das Lesões Ateroscleróticas da 
Doença Arterial Periférica de Extremidades Inferiores ..........................850
10.5.4. Manejo Preventivo da Doença Arterial Periférica de Extremidades 
Inferiores ................................................................................................850
10.6. Doenças Autoimunes e Risco Cardiovascular .................................852
10.7. Doença Renal Crônica ....................................................................853
10.8. Apneia Obstrutiva do Sono .............................................................854
10.9. Disfunção Erétil ..............................................................................855
10.10. Prevenção da Cardiopatia Reumática ..........................................855
11. Infância e Adolescência ..............................................................858
11.1. Introdução......................................................................................858
11.2. Nutrição na Infância e Adolescência ..............................................858
11.3. Atividade Física na Infância e na Adolescência ..............................858
11.4. Tabagismo na Infância e na Adolescência ......................................859
11.5. Obesidade na Infância e na Adolescência ......................................860
11.5.1. Diagnóstico ................................................................................860
11.5.2. Consequências ...........................................................................860
11.5.3. Etiologia ......................................................................................860
11.5.4. Tratamento .................................................................................860
11.6. Hipertensão Arterial Sistêmica na Infância e na Adolescência .......860
11.7. Dislipidemia na Infância e na Adolescência ...................................861
11.7.1. Causas ........................................................................................862
11.7.2. Valores de Normalidade .............................................................862
11.7.3. Tratamento .................................................................................862
12. Abordagem Populacional dos Fatores de Risco para Doenças 
Cardiovasculares .................................................................................864
12.1. Introdução ......................................................................................864
12.2. Aspecto populacional do Tabagismo ..............................................865
12.3. Dia 31 de Maio – Dia Mundial Sem Tabaco ....................................865
12.4. Aspectos Populacionais da Obesidade e Sobrepeso .......................866
12.5. Aspectos Populacionais da Hipertensão Arterial ............................867
12.6. Aspectos Populacionais das Dislipidemias .....................................867
12.6.1. Medidas Práticas Gerais .............................................................868
12.7. Aspectos Populacionais da Atividade Física ....................................868
12.8. Abordagem Populacional para o Aumento da Atividade Física .......868
12.9. Fatores Socioeconômicos e Ambientais e Doenças Associadas na 
Prevenção Cardiovascular .......................................................................869
12.10. Saúde e Desenvolvimento Sustentável .........................................870
12.11. Prevenção Cardiovascular, Ambiente, Sustentabilidade e Doenças 
Associadas ..............................................................................................871
12.12. Conclusão ....................................................................................872
"""

processar_relatorio("diretriz_limpa.txt", sumario_raw)