# Caminho: /home/flavioleal_souza/Sistema/buscador_itens/M7_Busca_Equipamentos.py

import os
import json

ARQUIVO_LISTA_NEGRA = "/home/flavioleal_souza/Sistema/Procurar_equipamentos.txt"
PASTA_JSON = "/home/flavioleal_souza/Sistema/extracao_dados/"
ARQUIVO_LOG = "/home/flavioleal_souza/Sistema/log_busca_equipamentos.txt"

def carregar_lista_negra():
    with open(ARQUIVO_LISTA_NEGRA, "r") as f:
        return set(linha.strip() for linha in f if linha.strip())

def extrair_equipamentos(dados):
    return dados.get("equipamentos_entregues", []) + dados.get("equipamentos_recolhidos", [])

def extrair_numero_intervencao(dados):
    return dados.get("dados_intervencao", {}).get("numero_intervencao", "Desconhecido")

def verificar_equipamentos_na_lista(equipamentos, lista_negra):
    encontrados = []
    for eq in equipamentos:
        if "Serial Number" in eq:
            num_serie = eq.split("Serial Number")[-1].strip()
            if num_serie in lista_negra:
                encontrados.append((eq, num_serie))
    return encontrados

def processar_jsons():
    lista_negra = carregar_lista_negra()
    resultados = []

    for nome_arquivo in os.listdir(PASTA_JSON):
        if not nome_arquivo.endswith(".json"):
            continue

        caminho = os.path.join(PASTA_JSON, nome_arquivo)
        try:
            with open(caminho, "r") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    numero = extrair_numero_intervencao(dados)
                    equipamentos = extrair_equipamentos(dados)
                    encontrados = verificar_equipamentos_na_lista(equipamentos, lista_negra)

                    for nome_eq, num in encontrados:
                        resultados.append((numero, nome_eq, num))
        except:
            continue

    return resultados

def salvar_log(resultados):
    with open(ARQUIVO_LOG, "w") as f:
        for numero, nome_eq, num_serie in resultados:
            f.write(f"Intervenção Nº: {numero}\n")
            f.write(f"Equipamento: {nome_eq}\n")
            f.write(f"Número de Série: {num_serie}\n")
            f.write("-" * 40 + "\n")

if __name__ == "__main__":
    dados_filtrados = processar_jsons()
    salvar_log(dados_filtrados)
