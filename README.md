# 🍊 Citrus Analytics — Case Técnico Analista BI

Case técnico para vaga de Analista de Business Intelligence.
Análise da produção nacional de citros (2015–2023) com dados do IBGE.

## Estrutura do Repositório

projeto_citrus/
├── data/           → CSVs bruto, limpo e dados da API IBGE
├── extraction/     → Script de consumo da API do IBGE
├── sql/            → Script de limpeza e modelagem
├── dashboard/      → Arquivo .pbix (Power BI)
└── docs/           → Documentação e prints do painel

## Como Reproduzir

### 1. Instalar dependências
pip install requests pandas

### 2. Extrair municípios da API IBGE
python extraction/extrair_municipios_ibge.py

### 3. Executar limpeza e modelagem
python sql/limpeza_modelagem.py

### 4. Abrir o dashboard
Abrir dashboard/citrus_analytics.pbix no Power BI Desktop

## Decisões de Limpeza

| Problema | Ocorrências | Tratamento |
|---|---|---|
| Capitalização inconsistente nos municípios | 99 municípios | str.strip().str.title() |
| Valores '-' em qtd_produzida_ton | 97 linhas | Substituídos por NaN |
| Valores ausentes em area_colhida_ha | 162 linhas | Excluídos da fato |
| Valores nulos em valor_producao_reais | 122 linhas | Mantidos como NaN |
| Registros com área = 0 | Regra aplicada | Excluídos da fato |

Total descartado: 366 registros (10,2%)
Total válido: 3.234 registros

## Modelagem

- **fato_producao** — uma linha por município + produto + ano
- **dim_municipio** — uma linha por município com dados geográficos do IBGE
- Relacionamento via cod_municipio_ibge (Muitos para Um)

## Medidas DAX

| Medida | Fórmula |
|---|---|
| Produção Total (ton) | SUM(fato_producao[qtd_produzida_ton]) |
| Área Colhida Total (ha) | SUM(fato_producao[area_colhida_ha]) |
| Produtividade Média (ton/ha) | DIVIDE(SUM(qtd_produzida_ton), SUM(area_colhida_ha), 0) |
| Valor Total (R$) | SUM(fato_producao[valor_producao_reais]) |
| Produção Ano Anterior | CALCULATE com FILTER ano -1 |
| Variação YoY (%) | DIVIDE(atual - anterior, anterior, 0) |
| Rank Produtividade Estado | RANKX por produtividade média DESC |

## Principais Insights

- **SP domina**: São Paulo responde por ~63% da produção total
- **Laranja é o principal produto**: 63% do volume total
- **Produção estável**: Entre 2,3 e 2,5 milhões de ton/ano
- **Queda em 2019**: Menor produção do período (2,3M ton)
- **Sudeste lidera**: 63% da produção nacional

## Fonte dos Dados

- CSV: PAM (Pesquisa Agrícola Municipal) — IBGE
- Geográfico: API de Localidades IBGE
