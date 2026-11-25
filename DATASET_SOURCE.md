# Fonte de dados

## Dataset

**Consumos por municipio por periodo tarifario**, Portal Open Data E-REDES. O dataset publica consumos mensais de energia ativa por concelho e freguesia, com medidas para os periodos tarifarios Simples, Vazio, Fora de Vazio, Super Vazio, Ponta e Cheias, mais Total. O snapshot utilizado contem 103 760 registos. Os dados sao dinamicos e podem ser corrigidos pelo publicador.

- Pagina do dataset: https://e-redes.opendatasoft.com/explore/dataset/consumos-faturados-por-periodo-tarifario/information/
- Exportacao CSV/API: `python download_dataset.py`
- Publicador: E-REDES - Distribuicao de Eletricidade
- Licenca indicada pelo portal: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Atribuicao: E-REDES - Distribuicao de Eletricidade, Portal Open Data E-REDES. CSV fornecido pelo estudante e recebido para este projeto em 19/11/2026; data original de recolha no portal desconhecida.
- Periodo no snapshot: 2023-01 a 2025-12.

## Limites e interpretacao

As medidas sao energia ativa faturada em kWh. Nao ha variaveis de populacao, numero de clientes ou setor economico; nao calcular consumo per capita nem descrever categorias tarifarias como setores. Algumas observacoes podem estar agregadas ou suprimidas por motivos de privacidade. O registo da preparacao indica numero de linhas, periodo efetivo e tratamentos aplicados.
