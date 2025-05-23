#!/usr/bin/env python3
"""
Manipulação de Arquivos PDF

Este script realiza operações de manipulação de arquivos PDF,
incluindo extração de dados e processamento.
Refatorado para usar caminhos relativos através do sistema centralizado de configurações.
"""

import os
import shutil
import time
import logging
import json
import sys
from datetime import datetime
import subprocess

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('manipulacao_arquivos')

# Adicionar diretório raiz ao path para importação
try:
    # Determinar o diretório base do projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
except Exception as e:
    logger.error(f"Erro ao configurar path: {str(e)}")

# Importar utilitários de caminho
try:
    from config.path_utils import get_path, join_path, ensure_dir_exists
    USING_PATH_UTILS = True
except ImportError:
    logger.warning("Utilitários de caminho não encontrados. Usando caminhos padrão.")
    USING_PATH_UTILS = False

# Função para extrair os dados do PDF
def extrair_dados_pdf_relevantes(caminho_pdf):
    """Extrai os dados relevantes de um arquivo PDF usando pdftotext e regex."""
    dados_relevantes = {
        "dados_intervencao": {},
        "observacoes_tecnico": None,
        "equipamentos_entregues": [],
        "materiais_usados": []
    }

    try:
        process = subprocess.run(["pdftotext", "-layout", caminho_pdf, "-"], capture_output=True, text=True, check=True, encoding='utf-8')
        texto_completo = process.stdout
    except FileNotFoundError:
        logging.error("Comando pdftotext não encontrado. Verifique se poppler-utils está instalado e no PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar pdftotext para {caminho_pdf}: {e}. Output: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao processar {caminho_pdf} com pdftotext: {e}")
        return None

    # Processamento dos dados extraídos
    # Aqui você pode chamar as funções de extração específicas para cada tipo de dado do PDF

    # Exemplo de extração (personalize com as suas funções de regex)
    dados_relevantes["dados_intervencao"]["numero_intervencao"] = "12345"
    dados_relevantes["dados_intervencao"]["tipo_intervencao"] = "Instalação"
    dados_relevantes["dados_intervencao"]["data_inicio"] = "2025-05-14"
    
    # Criar diretório para salvar os arquivos se não existir
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        saida_dir = join_path('extracao_dados_dir', create=True)
    else:
        # Fallback para caminho absoluto
        saida_dir = "/home/flavioleal_souza/Sistema/extracao_dados"
        os.makedirs(saida_dir, exist_ok=True)

    # Salvar os dados extraídos em um arquivo JSON
    nome_pdf = os.path.basename(caminho_pdf).replace('.pdf', '')
    caminho_saida = os.path.join(saida_dir, f"{nome_pdf}_dados.json")
    
    with open(caminho_saida, "w", encoding="utf-8") as f_out:
        json.dump(dados_relevantes, f_out, indent=2, ensure_ascii=False)
    
    logging.info(f"Dados extraídos salvos em: {caminho_saida}")
    return dados_relevantes


# Função para processar o arquivo
def processar_pdf(caminho_pdf):
    """
    Processa um arquivo PDF, extraindo seus dados.
    
    Args:
        caminho_pdf: Caminho completo para o arquivo PDF.
        
    Returns:
        Dicionário com os dados extraídos do PDF.
    """
    logging.info(f"Iniciando o processamento do PDF: {caminho_pdf}")
    return extrair_dados_pdf_relevantes(caminho_pdf)


# Função principal
def main():
    """Função principal do script."""
    # Definir caminho da pasta de PDFs
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        pasta_pdf = join_path('tecnicos_dir', 'Teste', 'pdfs', 'novos')
    else:
        # Fallback para caminho absoluto
        pasta_pdf = '/home/flavioleal_souza/Sistema/tecnicos/Teste/pdfs/novos'
    
    # Verificar se a pasta existe
    if not os.path.exists(pasta_pdf):
        logging.error(f"Pasta não encontrada: {pasta_pdf}")
        return
    
    # Listar arquivos PDF
    arquivos_pdf = [f for f in os.listdir(pasta_pdf) if f.lower().endswith(".pdf")]
    logging.info(f"Encontrados {len(arquivos_pdf)} arquivos PDF para processamento.")

    # Processar cada arquivo
    for arq in arquivos_pdf:
        caminho_pdf = os.path.join(pasta_pdf, arq)
        processar_pdf(caminho_pdf)

if __name__ == "__main__":
    main()
