Null > 0

"122 registros não possuíam valor de produção na fonte PAM/IBGE. Esses valores foram substituídos por 0 (zero)."


Produção Total (ton)
Calcula a soma total de toneladas produzidas no período filtrado.
= SUM(fato_producao[qtd_produzida_ton])

Área Colhida Total (ha)
Soma total da área colhida em hectares.
= SUM(fato_producao[area_colhida_ha])

Produtividade Média (ton/ha)
Divide a produção total pela área colhida — indica eficiência agrícola.
= DIVIDE(SUM(fato_producao[qtd_produzida_ton]), SUM(fato_producao[area_colhida_ha]), 0)

Valor Total (R$)
Soma do valor financeiro da produção.
= SUM(fato_producao[valor_producao_reais])

Produção Ano Anterior
Retorna a produção do ano imediatamente anterior ao contexto de filtro.
= CALCULATE([Produção Total (ton)], FILTER(ALL(fato_producao), fato_producao[ano] = MAX(fato_producao[ano]) - 1))

Variação YoY (%)
Calcula o crescimento percentual em relação ao ano anterior.
= DIVIDE([Produção Total (ton)] - [Produção Ano Anterior], [Produção Ano Anterior], 0)

Rank Produtividade Estado
Classifica os estados do mais produtivo para o menos produtivo (ton/ha).
= RANKX(ALL(fato_producao[uf]), [Produtividade Média (ton/ha)], , DESC, DENSE)