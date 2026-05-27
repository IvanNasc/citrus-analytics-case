-- ============================================================
-- MODELAGEM CITRUS ANALYTICS
-- Compatível com: DuckDB, SQLite, PostgreSQL
-- Execute após carregar os CSVs como tabelas
-- ============================================================

-- ── PASSO 1: Carregar CSV bruto (DuckDB syntax) ─────────────
-- CREATE TABLE producao_bruta AS SELECT * FROM read_csv_auto('data/producao_citros_bruto.csv');
-- CREATE TABLE municipios_ibge AS SELECT * FROM read_csv_auto('data/municipios_ibge.csv');


-- ── PASSO 2: dim_municipio ────────────────────────────────────
CREATE TABLE dim_municipio AS
SELECT
    i.cod_municipio_ibge,
    -- Usa nome normalizado do IBGE como padrão (title case correto)
    i.nome_municipio                            AS nome_municipio,
    p.uf,
    p.estado,
    i.mesorregiao,
    i.regiao_brasil
FROM (
    -- Municípios únicos do CSV, com capitalização normalizada
    SELECT DISTINCT
        UPPER(SUBSTRING(LOWER(TRIM(municipio)), 1, 1))
            || LOWER(SUBSTRING(TRIM(municipio), 2))     AS municipio_norm,
        uf,
        estado
    FROM producao_bruta
    WHERE municipio IS NOT NULL
) p
LEFT JOIN municipios_ibge i
    ON LOWER(TRIM(i.nome_municipio)) = LOWER(TRIM(p.municipio_norm))
    AND i.uf = p.uf;
-- Decisão: LEFT JOIN mantém municípios do CSV mesmo sem match na API


-- ── PASSO 3: fato_producao ────────────────────────────────────
CREATE TABLE fato_producao AS
SELECT
    d.cod_municipio_ibge,
    CAST(b.cod_produto AS INTEGER)              AS cod_produto,
    b.produto,
    CAST(b.ano AS INTEGER)                      AS ano,
    CAST(b.qtd_produzida_ton AS DOUBLE)         AS qtd_produzida_ton,
    CAST(b.area_colhida_ha AS DOUBLE)           AS area_colhida_ha,
    CAST(b.valor_producao_reais AS DOUBLE)      AS valor_producao_reais,
    -- Métrica derivada obrigatória
    ROUND(
        CAST(b.qtd_produzida_ton AS DOUBLE) /
        CAST(b.area_colhida_ha AS DOUBLE),
        4
    )                                           AS produtividade_ton_ha,
    b.uf,
    -- Capitalização normalizada
    INITCAP(TRIM(b.municipio))                  AS municipio
FROM producao_bruta b
JOIN dim_municipio d
    ON LOWER(TRIM(b.municipio)) = LOWER(TRIM(d.nome_municipio))
    AND b.uf = d.uf
WHERE
    -- Regra 1: qtd não nula, não vazia, não '-', maior que zero
    b.qtd_produzida_ton IS NOT NULL
    AND TRIM(b.qtd_produzida_ton) != ''
    AND TRIM(b.qtd_produzida_ton) != '-'
    AND CAST(b.qtd_produzida_ton AS DOUBLE) > 0
    -- Regra 2: área não nula, não vazia, não '-', maior que zero
    AND b.area_colhida_ha IS NOT NULL
    AND TRIM(b.area_colhida_ha) != ''
    AND TRIM(b.area_colhida_ha) != '-'
    AND CAST(b.area_colhida_ha AS DOUBLE) > 0;
-- Decisão: área=0 com produção > 0 é registro inválido (impossível fisicamente)


-- ── VERIFICAÇÃO ───────────────────────────────────────────────
SELECT 'fato_producao'  AS tabela, COUNT(*) AS linhas FROM fato_producao
UNION ALL
SELECT 'dim_municipio'  AS tabela, COUNT(*) AS linhas FROM dim_municipio;

-- Produtividade média por produto (sanidade)
SELECT
    produto,
    ROUND(AVG(produtividade_ton_ha), 2) AS produtividade_media,
    ROUND(SUM(qtd_produzida_ton) / 1e6, 2) AS producao_total_milhoes_ton
FROM fato_producao
GROUP BY produto
ORDER BY producao_total_milhoes_ton DESC;
