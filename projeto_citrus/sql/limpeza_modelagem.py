"""
Limpeza e Modelagem — Citrus Analytics
========================================
Lê o CSV bruto + CSV de municípios do IBGE e produz:
  - fato_producao.csv
  - dim_municipio.csv
  - relatorio_limpeza.txt  (documenta cada decisão)

Execução (após rodar extrair_municipios_ibge.py):
    python limpeza_modelagem.py
"""

import pandas as pd
import os

# ─── Caminhos ────────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)
CSV_BRUTO      = os.path.join(BASE, '../data/producao_citros_bruto.csv')
CSV_MUNICIPIOS = os.path.join(BASE, '../data/municipios_ibge.csv')
OUT_FATO       = os.path.join(BASE, '../data/fato_producao.csv')
OUT_DIM        = os.path.join(BASE, '../data/dim_municipio.csv')
OUT_LOG        = os.path.join(BASE, '../docs/relatorio_limpeza.txt')

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(msg)


# ─── 1. Leitura ───────────────────────────────────────────────────────────────
log("=" * 60)
log("RELATÓRIO DE LIMPEZA — CITRUS ANALYTICS")
log("=" * 60)

df = pd.read_csv(CSV_BRUTO, dtype=str)
log(f"\n[1] CSV bruto carregado: {len(df)} linhas, {df.shape[1]} colunas")


# ─── 2. Normalização de municípios ───────────────────────────────────────────
antes = df['municipio'].nunique()
df['municipio'] = df['municipio'].str.strip().str.title()
depois = df['municipio'].nunique()
log(f"\n[2] Normalização de capitalização dos municípios")
log(f"    Variações únicas antes : {antes}")
log(f"    Variações únicas depois: {depois}")
log(f"    Decisão: str.strip().str.title() — garante 'Araraquara' independente de 'ARARAQUARA' ou 'araraquara'")


# ─── 3. Limpeza de qtd_produzida_ton ─────────────────────────────────────────
n_traco = (df['qtd_produzida_ton'] == '-').sum()
n_vazio = (df['qtd_produzida_ton'] == '').sum()
n_nulo  = df['qtd_produzida_ton'].isna().sum()

df['qtd_produzida_ton'] = pd.to_numeric(
    df['qtd_produzida_ton'].replace({'-': None, '': None}),
    errors='coerce'
)
n_nulo_pos = df['qtd_produzida_ton'].isna().sum()

log(f"\n[3] Limpeza de qtd_produzida_ton")
log(f"    Strings '-' encontradas : {n_traco}")
log(f"    Strings vazias          : {n_vazio}")
log(f"    Nulos originais         : {n_nulo}")
log(f"    Total convertido p/ NaN : {n_nulo_pos}")
log(f"    Decisão: '-' e '' substituídos por NaN via pd.to_numeric")


# ─── 4. Limpeza de area_colhida_ha ───────────────────────────────────────────
df['area_colhida_ha'] = pd.to_numeric(
    df['area_colhida_ha'].replace({'-': None, '': None}),
    errors='coerce'
)
n_nulo_area = df['area_colhida_ha'].isna().sum()
log(f"\n[4] Limpeza de area_colhida_ha")
log(f"    Total convertido p/ NaN : {n_nulo_area}")
log(f"    Decisão: mesma abordagem que qtd_produzida_ton")


# ─── 5. Limpeza de valor_producao_reais ──────────────────────────────────────
df['valor_producao_reais'] = pd.to_numeric(
    df['valor_producao_reais'].replace({'-': None, '': None}),
    errors='coerce'
)
n_nulo_valor = df['valor_producao_reais'].isna().sum()
log(f"\n[5] Limpeza de valor_producao_reais")
log(f"    Nulos: {n_nulo_valor}")
log(f"    Decisão: mantidos como NaN — valor não é usado em KPIs obrigatórios mas está disponível para análise financeira")


# ─── 6. Tipagem ───────────────────────────────────────────────────────────────
df['ano']         = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')
df['cod_produto'] = pd.to_numeric(df['cod_produto'], errors='coerce').astype('Int64')
log(f"\n[6] Tipagem corrigida: ano e cod_produto → Int64")


# ─── 7. Filtro de registros inválidos ────────────────────────────────────────
total_antes = len(df)
df_valido = df[
    (df['qtd_produzida_ton'].notna()) & (df['qtd_produzida_ton'] > 0) &
    (df['area_colhida_ha'].notna())   & (df['area_colhida_ha'] > 0)
].copy()
descartados = total_antes - len(df_valido)

log(f"\n[7] Filtro de registros inválidos")
log(f"    Regra: qtd_produzida_ton > 0 E area_colhida_ha > 0 (ambos não-nulos)")
log(f"    Registros descartados : {descartados}")
log(f"    Registros mantidos    : {len(df_valido)}")
log(f"    Decisão: conforme especificação — área=0 com produção é inconsistência de coleta")


# ─── 8. Produtividade ─────────────────────────────────────────────────────────
df_valido['produtividade_ton_ha'] = (
    df_valido['qtd_produzida_ton'] / df_valido['area_colhida_ha']
).round(4)
log(f"\n[8] Métrica derivada: produtividade_ton_ha = qtd_produzida_ton / area_colhida_ha")
log(f"    Min: {df_valido['produtividade_ton_ha'].min():.2f} | Max: {df_valido['produtividade_ton_ha'].max():.2f} | Média: {df_valido['produtividade_ton_ha'].mean():.2f}")


# ─── 9. dim_municipio ─────────────────────────────────────────────────────────
log(f"\n[9] Construção de dim_municipio")

# Dimensão base vinda do CSV (sem API)
dim_csv = df_valido[['uf', 'estado', 'municipio']].drop_duplicates().copy()

try:
    df_ibge = pd.read_csv(CSV_MUNICIPIOS)
    df_ibge['nome_municipio_norm'] = df_ibge['nome_municipio'].str.strip().str.title()

    # Join por nome normalizado + UF
    dim_csv['municipio_norm'] = dim_csv['municipio'].str.strip().str.title()
    dim = dim_csv.merge(
        df_ibge[['cod_municipio_ibge', 'nome_municipio_norm', 'uf', 'mesorregiao', 'regiao_brasil']],
        left_on=['municipio_norm', 'uf'],
        right_on=['nome_municipio_norm', 'uf'],
        how='left'
    )
    sem_match = dim['cod_municipio_ibge'].isna().sum()
    log(f"    Municípios com match na API IBGE: {dim['cod_municipio_ibge'].notna().sum()}")
    log(f"    Sem match (cod = NaN)            : {sem_match}")
    log(f"    Decisão: registros sem match mantidos com cod_municipio_ibge = NaN")

    dim_final = dim[['cod_municipio_ibge', 'municipio', 'uf', 'estado', 'mesorregiao', 'regiao_brasil']].copy()
    dim_final.rename(columns={'municipio': 'nome_municipio'}, inplace=True)

except FileNotFoundError:
    log(f"    AVISO: municipios_ibge.csv não encontrado.")
    log(f"    Execute extraction/extrair_municipios_ibge.py primeiro.")
    log(f"    dim_municipio criada apenas com dados do CSV (sem cod_ibge, mesorregiao, regiao).")
    dim_final = dim_csv[['municipio', 'uf', 'estado']].copy()
    dim_final.rename(columns={'municipio': 'nome_municipio'}, inplace=True)
    dim_final['cod_municipio_ibge'] = None
    dim_final['mesorregiao'] = None
    dim_final['regiao_brasil'] = None


# ─── 10. fato_producao ────────────────────────────────────────────────────────
log(f"\n[10] Construção de fato_producao")

# Para usar cod_municipio_ibge na fato, fazemos join com dim
if 'cod_municipio_ibge' in dim_final.columns and dim_final['cod_municipio_ibge'].notna().any():
    mapa = dim_final[['nome_municipio', 'uf', 'cod_municipio_ibge']].dropna()
    df_valido2 = df_valido.merge(
        mapa,
        left_on=['municipio', 'uf'],
        right_on=['nome_municipio', 'uf'],
        how='left'
    )
else:
    df_valido2 = df_valido.copy()
    df_valido2['cod_municipio_ibge'] = None

fato = df_valido2[[
    'cod_municipio_ibge', 'cod_produto', 'produto', 'ano',
    'qtd_produzida_ton', 'area_colhida_ha', 'valor_producao_reais',
    'produtividade_ton_ha', 'uf', 'municipio'
]].copy()

log(f"    Linhas na fato_producao: {len(fato)}")


# ─── 11. Salvar ───────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_FATO), exist_ok=True)
fato.to_csv(OUT_FATO, index=False)
dim_final.to_csv(OUT_DIM, index=False)

log(f"\n[11] Arquivos gerados:")
log(f"    {OUT_FATO}")
log(f"    {OUT_DIM}")

# Salvar log
os.makedirs(os.path.dirname(OUT_LOG), exist_ok=True)
with open(OUT_LOG, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

log(f"\n[LOG] Relatório salvo em: {OUT_LOG}")
log("\n" + "=" * 60)
log("LIMPEZA CONCLUÍDA")
log("=" * 60)
