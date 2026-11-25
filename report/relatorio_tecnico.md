# Relatorio tecnico - Projeto de visualizacao de dados

**Estudante:** 23795  
**Unidade curricular:** Programacao para Visualizacao de Dados (MEI, 2026/2027)  
**Data da analise:** 25/11/2026

## 1. Dataset e objetivo

O projeto usa o dataset publico **Consumos por municipio por periodo tarifario**, publicado pela E-REDES no [Portal Open Data](https://e-redes.opendatasoft.com/explore/dataset/consumos-faturados-por-periodo-tarifario/information/), sob licenca CC BY 4.0. O CSV fornecido pelo estudante esta em `data/raw/consumos_faturados_por_periodo_tarifario.csv`. O snapshot contem 103 760 linhas, 16 colunas, 18 distritos, 278 concelhos e 36 meses, de janeiro de 2023 a dezembro de 2025. A data exata de recolha nao esta codificada no CSV; regista-la na atribuicao se conhecida.

As medidas sao energia ativa faturada em kWh: Simples, Vazio, Fora de Vazio, Super Vazio, Ponta, Cheias e Total. Periodos tarifarios nao sao setores economicos. O dataset nao contem populacao nem numero de clientes; nao se calculam valores per capita. Valores negativos sao mantidos como possiveis acertos contabilisticos.

## 2. Preparacao e auditoria

A preparacao foi executada em modo determinista, sem LLM. `logs/data_prep.json` regista 103 760 linhas de origem e 726 320 linhas canonicas (sete medidas por observacao), 278 concelhos, 18 distritos e 2 890 codigos de freguesia reconhecidos pela regra de validacao. Nao foram detetadas chaves duplicadas por data e freguesia. Foram reportadas zero datas invalidas e diferenca maxima zero entre o total e a soma das seis componentes, tratando valores ausentes como zero para esta verificacao.

Nulos por componente na origem: Simples 145, Vazio 6, Fora de Vazio 615, Super Vazio 13 787, Ponta 793 e Cheias 341; Total sem nulos. A transformacao preencheu 15 687 componentes ausentes com zero no formato canonico. Esta imputacao e uma convencao operacional, nao prova que o consumo real tenha sido zero. O mapeamento de nomes e determinista e preserva as chaves territoriais.

## 3. Visualizacoes

Foram renderizadas 12 figuras PNG com templates deterministas; os scripts-fonte estao em `figures/code/`. `logs/render_summary.json` regista cada render e indica que LangGraph nao foi invocado.

### Parte I

1. **Estetica e escalas:** dispersao municipal com escala logaritmica para comparar ordens de grandeza. Posicao representa consumo em vazio/super vazio e ponta/cheias; tamanho representa numero de freguesias com codigo reconhecido; cor e forma indicam tarifa dominante. A escala log permite comparar amplitudes, mas dificulta ler diferencas absolutas e nao representa valores nao positivos.
2. **Escalas de cor:** mapas de calor de consumo por freguesia codificada e de diferenca entre periodos, com escalas sequencial e divergente centrada no zero. Nao representam consumo per capita.
3. **Categorizacao:** barras para seis periodos, dot plot para 18 distritos e heatmap municipal para 278 concelhos. Regra por cardinalidade escolheu barras (6), dot plot (18) e heatmap (278); o agente LangGraph nao foi invocado.
4. **Distribuicoes:** histogramas/densidades, boxplot e violino para energia agregada. A agregacao usada esta indicada nas figuras.
5. **Multivariada e composicao:** violinos por tarifa, ridgeline por distrito e treemap hierarquico de tarifas e distritos. A hierarquia descreve reparticao dos totais e nao implica causalidade.

### Parte II

6. **Associacao:** numero de freguesias codificadas por concelho versus energia anual total (n=278): Pearson r=0,16 (p=0,0059), Spearman rho=0,22, R2=0,03. A associacao e fraca e nao causal; populacao e dimensao territorial sao fatores de confusao nao observados.
7. **Tempo:** serie mensal de 36 meses com suavizacao. Regressao dos totais anuais usa apenas tres observacoes (2023-2025): inclinacao +1 120,8 GWh/ano, variacao anualizada estimada +2,4%, R2=0,97 e p=0,11. Com tres pontos nao se conclui tendencia robusta. Suavizador mensal varia +6,9% entre extremos; maximo medio em janeiro, minimo em abril, razao 1,19. Estes valores descrevem este snapshot, nao sao previsoes.
8. **Integridade de barras:** barras horizontais para os 18 distritos com eixo quantitativo linear iniciado em zero; esta orientacao evita sobreposicao dos nomes e valores. A auditoria estatica dos 12 scripts atuais nao detetou alertas para cor, CVD ou eixo de barras; registo em `logs/visual_audit.json`. O auditor integrado no grafo ainda nao foi executado.
9. **Acessibilidade cromatica:** `figures/p2f2_cvd.png` e outras figuras mostram simulacoes normal, deuteranopia, protanopia e tritanopia. `figures/cvd_report.csv` regista ensaios com Delta E CIE76. Colorblind, viridis, cividis e coolwarm passaram os limiares configurados; Set2 e jet falharam. Sao aproximacoes, nao substituem avaliacao com utilizadores.

## 4. Agentes e estado observado

### Tres papeis agênticos implementados

1. **Agente de desenho da visualizacao** (`chart_design_agent` e seletor categorial): propõe geometria, codificacoes, escala e paleta; respeita os filtros/medidas da especificacao. O seletor aplica regras de cardinalidade e pode consultar o modelo de texto.
2. **Agente de codigo** (`code_agent`): escreve ou revê o script Python com base na especificacao, plano visual, alertas dos validadores e feedback anterior.
3. **Agente de critica visual** (`visual_critic_agent`): recebe a figura renderizada, examina legibilidade, sobreposicao, escalas, cor e unidades, e devolve aprovacao ou feedback ao agente de codigo. Configurado com `qwen2.5vl:3b`, modelo Ollama multimodal; se falhar, o historico regista a verificacao heuristica de recurso.

Validacao estatica (paletas, acessibilidade e eixo zero) e execucao isolada sao nos de suporte deterministas, nao agentes LLM. A critica devolve ao agente de codigo, fechando o ciclo de correcao. A cadeia LangChain/LCEL separada produz titulos/legendas a partir das estatisticas, com verificacao de numeros.

**Limite da evidencia:** a instalacao de dependencias completou-se em Python 3.14.7, mas a importacao do projeto falhou porque o Windows App Control bloqueou `pydantic_core._pydantic_core`, exigido por LangChain/LangGraph. Os modelos locais `qwen2.5:7b` e `qwen2.5vl:3b` foram confirmados; ambos responderam a pedidos diretos. O modelo visual identificou a figura de barras e o eixo iniciado em zero numa imagem redimensionada. Esses pedidos diretos nao equivalem a executar os agentes pelo projeto. As figuras incluidas foram produzidas por templates deterministas. A execucao ponta a ponta, incluindo a critica multimodal e a cadeia LCEL, ainda precisa de correr num ambiente autorizado a carregar as extensoes.

## 5. Matriz de requisitos

| Requisito | Evidencia | Estado observado |
|---|---|---|
| Fonte publica e reprodutibilidade | CSV E-REDES, `DATASET_SOURCE.md`, script de obtencao | Snapshot incluido; registar data de recolha |
| Parte I, Fase 1: estetica, variaveis, escalas e cor | `p1f1_aesthetics.png`, `p1f1_color_scales.png` e codigo | Artefactos produzidos |
| Parte I, Fase 2: categoricas, distribuicao, multivariada, proporcoes | Figuras categoricas, distribuicao e hierarquia | Artefactos produzidos |
| Agente de desenho visual | `chart_design_agent` e `pvd/selector_graph.py` | Implementado; execucao LangGraph pendente |
| Agente de codigo | `code_agent` e ciclo de feedback | Implementado; chamadas ao Ollama pelo projeto pendentes |
| Agente de critica visual | `visual_critic_agent`; `LLM_VISION_MODEL=qwen2.5vl:3b` | Configurado; modelo multimodal ainda nao validado dentro do grafo |
| Parte II, Fase 1: associacao, tempo e texto estatistico | Dispersao, serie e estatisticas; `pvd/trend_chain.py` | Figuras/estatisticas produzidas; cadeia LangChain nao executada |
| Parte II, Fase 2: proporcao, eixo zero, CVD e auditoria | Barra horizontal, painel CVD, `logs/visual_audit.json` | Auditoria estatica dos scripts atuais sem alertas; auditor integrado pendente |
| Relatorio tecnico | Este ficheiro | Incluido |
| Execucao completa | `run_all.py` | Pendente por bloqueio App Control |

## 6. Reproducibilidade e limitacoes

O projeto inclui dados de origem e transformados, dependencias, scripts, figuras e logs. A configuracao de exemplo aponta para Ollama local e modelos `qwen2.5:7b` e `qwen2.5vl:3b`, sem credenciais externas; noutro computador, sera preciso instalar Ollama e descarregar os dois modelos. `requirements-lock-win-py314.txt` regista o ambiente instalado nesta maquina Windows/Python 3.14.7; `requirements.txt` mantem intervalos de versao para instalacoes noutras plataformas. `download_dataset.py` requer ligacao ao portal, mas o snapshot esta incluido. Os dados podem ser corrigidos pelo publicador. Agregacao municipal esconde variacao interna. Delta E CIE76 e simulacoes CVD sao diagnosticos aproximados.

### Antes de submeter

- Confirmar se e exigido nome na capa; o numero 23795 esta integrado.
- Registar a data de recolha, se conhecida.
- Instalar `qwen2.5vl:3b` com Ollama antes de executar o critico visual.
- Executar o projeto num ambiente que permita importar a extensao nativa bloqueada. Chaves API nao sao necessarias para Ollama e nao estao no ZIP.

