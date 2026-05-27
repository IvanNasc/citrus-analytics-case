import os
import requests
import pandas as pd



UFS = ['BA', 'ES', 'GO', 'MG', 'MT', 'PR', 'RJ', 'RS', 'SC', 'SP']

print("Iniciando extração DETALHADA da API do IBGE (incluindo Regiões e Mesorregiões)...")
lista_municipios = []

for uf in UFS:
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/distritos"
    print(f"Buscando dados completos de {uf}...", end=" ", flush=True)
    
    try:
        resposta = requests.get(url, timeout=20)
        if resposta.status_code == 200:
            dados_uf = resposta.json()
            
           
            ids_processados = set()
            contagem = 0
            
            for item in dados_uf:
                muni = item.get("municipio", {})
                id_muni = muni.get("id")
                
                if id_muni and id_muni not in ids_processados:
                    ids_processados.add(id_muni)
                    contagem += 1
                    
                  
                    meso = muni.get("microrregiao", {}).get("mesorregiao", {})
                    regiao = meso.get("UF", {}).get("regiao", {})
                    
                    lista_municipios.append({
                        "cod_municipio_ibge": id_muni,
                        "nome_municipio": muni.get("nome"),
                        "uf": uf,
                        "mesorregiao": meso.get("nome", "Não Informado"),
                        "regiao_brasil": regiao.get("nome", "Não Informado")
                    })
            print(f"✓ {contagem} municípios únicos mapeados.")
        else:
            print(f"✗ Erro na API (Status {resposta.status_code})")
    except Exception as e:
        print(f"✗ Falha: {e}")


if lista_municipios:
    print("\nSalvando banco de dados estruturado do IBGE...")
    df = pd.DataFrame(lista_municipios)
    df.to_csv(caminho_salvamento, index=False, encoding="utf-8-sig")
    print(f"Sucesso! Arquivo preparado com as colunas necessárias em: {caminho_salvamento}")
    
   
    print("\n" + "="*60)
    print("Disparando o script 'limpeza_modelagem.py' com a nova base...")
    print("="*60 + "\n")
    
    caminho_sql = r"C:\Users\Ivan\Downloads\projeto_citrus_case\projeto_citrus\sql"
    caminho_limpeza = os.path.join(caminho_sql, "limpeza_modelagem.py")
    
    os.chdir(caminho_sql)
    try:
        with open(caminho_limpeza, "r", encoding="utf-8") as f:
            codigo_fonte = f.read()
            
        variaveis_locais = {"__file__": caminho_limpeza}
        exec(codigo_fonte, variaveis_locais, variaveis_locais)
        print("\n[PROCESSO COMPLETO] O script de limpeza rodou até o final sem erros!")
    except Exception as e:
        print(f"\nErro ao rodar a limpeza: {e}")
else:
    print("Não foi possível gerar a nova base de dados.")