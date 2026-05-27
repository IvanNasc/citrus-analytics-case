"""
Extração de dados geográficos via API do IBGE
Endpoint: GET https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios

Execução:
    pip install requests pandas
    python extrair_municipios_ibge.py

Saída:
    ../data/municipios_ibge.csv
"""

import requests
import pandas as pd
import time
import json
import os

# UFs presentes no CSV de produção
# Ajuste se quiser todos os 27 estados
UFS = ['BA', 'ES', 'GO', 'MG', 'MT', 'PR', 'RJ', 'RS', 'SC', 'SP']

BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"

def extrair_municipios(ufs: list) -> pd.DataFrame:
    registros = []
    erros = []

    for uf in ufs:
        url = BASE_URL.format(uf=uf)
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            municipios = response.json()

            for m in municipios:
                registros.append({
                    "cod_municipio_ibge": m["id"],
                    "nome_municipio": m["nome"],
                    "uf": uf,
                    "mesorregiao": m["microrregiao"]["mesorregiao"]["nome"],
                    "regiao_brasil": m["microrregiao"]["mesorregiao"]["UF"]["regiao"]["nome"]
                })

            print(f"  ✓ {uf}: {len(municipios)} municípios extraídos")
            time.sleep(0.2)  # respeitar rate limit

        except requests.exceptions.RequestException as e:
            print(f"  ✗ ERRO {uf}: {e}")
            erros.append(uf)

    if erros:
        print(f"\nAVISO: Falhou em {len(erros)} estados: {erros}")
        print("Tente novamente para esses estados.")

    return pd.DataFrame(registros)


def salvar_amostra_json(df: pd.DataFrame, caminho: str):
    """Salva amostra do retorno da API para documentação."""
    amostra = df.head(3).to_dict(orient='records')
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(amostra, f, ensure_ascii=False, indent=2)
    print(f"Amostra JSON salva em: {caminho}")


if __name__ == "__main__":
    print("=== Extraindo municípios da API do IBGE ===\n")

    df_municipios = extrair_municipios(UFS)

    if df_municipios.empty:
        print("Nenhum dado extraído. Verifique sua conexão.")
        exit(1)

    # Salvar CSV principal
    output_csv = os.path.join(os.path.dirname(__file__), '../data/municipios_ibge.csv')
    df_municipios.to_csv(output_csv, index=False)
    print(f"\nTotal: {len(df_municipios)} municípios")
    print(f"Arquivo salvo: {output_csv}")

    # Salvar amostra JSON para a pasta /data (documentação)
    output_json = os.path.join(os.path.dirname(__file__), '../data/amostra_api_ibge.json')
    salvar_amostra_json(df_municipios, output_json)

    print("\n=== Concluído ===")
