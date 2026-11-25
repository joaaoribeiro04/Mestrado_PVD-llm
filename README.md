# MEI - Programacao para Visualizacao de Dados

**Estudante:** 23795  
**Unidade curricular:** Programacao para Visualizacao de Dados (MEI, 2026/2027)  
**Dados:** E-REDES, consumos faturados por periodo tarifario (snapshot incluido).

## Conteudo

Projeto baseado no dataset publico da E-REDES. Inclui 12 figuras PNG, scripts-fonte em `figures/code/`, CSV original e canonico, estatisticas, registos de preparacao e relatorio tecnico. A lista de requisitos e o estado observado estao em `report/relatorio_tecnico.md`.

## Execucao

Requer Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama list
ollama pull qwen2.5vl:3b
python check_setup.py --vision
python run_all.py
```

O CSV esta em `data/raw/consumos_faturados_por_periodo_tarifario.csv`. Para voltar a preparar os dados: `python -m pvd.data_prep`. Para executar uma visualizacao: `python run_all.py --only p1f2_distributions` (ou outro ID em `pvd/figures.py`). Os graficos incluidos foram renderizados com templates deterministas e estao disponiveis sem chave de API.

Os scripts em `figures/code/` usam caminhos relativos ao projeto; execute-os a partir da pasta raiz do projeto.

A execucao completa de `run_all.py` usa o fluxo LangGraph. Neste ambiente, a importacao de uma extensao nativa requerida pelo LangGraph foi bloqueada pela politica de seguranca do Windows (App Control). A execucao integral do grafo nao foi confirmada; ver o relatorio.

## Ollama / LLM

A configuracao usa tres papeis: o agente de desenho planeia geometria e codificacoes; o agente de codigo escreve/revisa Python; o critico visual recebe a imagem e devolve aprovacao ou correcoes. Validadores e executor sao ferramentas deterministas. O modelo de texto/codigo e `qwen2.5:7b` (ja instalado); o critico visual usa `qwen2.5vl:3b`, que aceita texto e imagem. O modelo visual e descarregado com `ollama pull qwen2.5vl:3b` uma vez. A pagina oficial do Ollama descreve o suporte a analise de graficos e imagens: [Qwen2.5-VL no Ollama](https://ollama.com/library/qwen2.5vl). Nao sao necessarias chaves API. Se o servidor nao estiver ativo, inicia-o numa consola separada com `ollama serve`.

O agente visual esta configurado para usar o modelo de visao; se a chamada falhar, o historico identifica a verificacao heuristica de recurso. Foram confirmados pedidos diretos aos modelos de texto e de visao; a analise direta da figura identificou barras e eixo iniciado em zero. Isso nao equivale a uma execucao integrada do projeto. Neste Windows, o App Control bloqueia a extensao nativa `pydantic_core`, necessaria ao LangChain/LangGraph; por isso, a cadeia de tres agentes ainda precisa de ser executada num ambiente autorizado. As figuras que ja estao no ZIP foram geradas deterministicamente, nao pelos agentes. Nunca inclua o ficheiro `.env` na submissao.

`python check_setup.py --vision` verifica as dependencias, o servidor/modelos Ollama e faz um pedido de teste com a figura de barras ao modelo visual antes do fluxo completo.

## Dados e atribuicao

Fonte: E-REDES, "Consumos por municipio por periodo tarifario", [Portal Open Data E-REDES](https://e-redes.opendatasoft.com/explore/dataset/consumos-faturados-por-periodo-tarifario/information/), licenca CC BY 4.0. O CSV incluido e um snapshot com 103 760 registos mensais de 2023-01 a 2025-12. Cite E-REDES como publicador e indique a data de recolha se a conhecer. O dataset nao inclui populacao nem setor economico: nao interpretar tarifas como setores nem calcular consumo per capita.

## Estrutura

- `pvd/data_prep.py`: mapeamento, transformacao longa e auditorias de integridade.
- `pvd/graph.py`, `pvd/selector_graph.py`: arquitetura LangGraph.
- `pvd/trend_chain.py`: estatisticas e cadeia LangChain para texto com verificacao numerica.
- `pvd/validators.py`, `pvd/cvd.py`: auditorias de eixos, escalas de cor e simulacao CVD.
- `pvd/templates/`: templates deterministas das figuras.
- `figures/`, `logs/`, `report/`: artefactos, evidencias e relatorio.

## Limites

Use `requirements-lock-win-py314.txt` para repetir as versoes instaladas nesta maquina Windows com Python 3.14.7; `requirements.txt` continua a ser a lista de dependencias com intervalos para outros sistemas. Simulacoes CVD e a metrica Delta E CIE76 sao aproximacoes, nao substituem testes com utilizadores. Renderizar templates nao equivale a executar integralmente os agentes LangGraph/LLM.
