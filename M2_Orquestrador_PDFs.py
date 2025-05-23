#!/usr/bin/env python3
"""
Orquestrador de Processamento de PDFs

Este script coordena o processamento de PDFs para múltiplos técnicos,
extraindo dados e enviando notificações.
Refatorado para usar caminhos relativos através do sistema centralizado de configurações.
"""

import os
import json
import shutil
import time
import logging
import sys
import concurrent.futures
from datetime import datetime

# Suprimir logs internos excessivos do Twilio
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

# Configurar logging principal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('orquestrador_pdfs')

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
    # Definir caminhos padrão para compatibilidade
    TECNICOS_DIR = "/home/flavioleal_souza/Sistema/tecnicos"
    CONFIG_TECNICOS_JSON_PATH = "/home/flavioleal_souza/Sistema/config/tecnicos.json"

# Importar módulos do projeto
from M1_Extrator_PDF import extrair_dados_pdf_relevantes
from M6_Notificacao_Status import (
    enviar_notificacao_boas_vindas,
    enviar_notificacao_wo_iniciada,
    enviar_notificacao_wo_sucesso,
    enviar_notificacao_wo_erro
)

# --- Configurações ---
NUM_THREADS = 4

# --- Logger por técnico ---
def configurar_logger(tecnico_nome):
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        log_path = join_path('tecnicos_dir', tecnico_nome, "logs", f"{data_hoje}.log", create=True)
    else:
        # Fallback para caminho absoluto
        log_path = os.path.join(TECNICOS_DIR, tecnico_nome, "logs", f"{data_hoje}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger(tecnico_nome)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # <- Isso impede mensagens duplicadas

    # Evita adicionar múltiplos handlers se já existirem
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# --- Processamento do PDF ---
def processar_pdf_tecnico(pdf_path, tecnico_nome, tecnico_info):
    logger = configurar_logger(tecnico_nome)
    nome_pdf = os.path.basename(pdf_path)
    numero_wo = nome_pdf.replace(".pdf", "")

    logger.info(f"\n========================= INÍCIO DA WO {numero_wo} =========================")
    logger.info(f"[WO {numero_wo}] Iniciando processamento...")

    try:
        dados = extrair_dados_pdf_relevantes(pdf_path)
        if not dados or not dados.get("dados_intervencao"):
            logger.error(f"[WO {numero_wo}] Falha na extração dos dados.")
            enviar_notificacao_wo_erro(tecnico_info["whatsapp"], numero_wo)
            logger.info(f"========================= FIM DA WO {numero_wo} =========================\n")
            return False

        # Obter caminho de saída dos dados extraídos
        if USING_PATH_UTILS:
            extracao_dados_dir = get_path('extracao_dados_dir')
        else:
            extracao_dados_dir = "/home/flavioleal_souza/Sistema/extracao_dados"
            
        logger.info(f"Dados extraídos salvos em: {os.path.join(extracao_dados_dir, f'{numero_wo}_dados.json')}")
        logger.info(f"[WO {numero_wo}] Dados extraídos com sucesso. Enviando notificação...")

        enviar_notificacao_wo_iniciada(tecnico_info["whatsapp"], tecnico_info["nome_completo"], numero_wo, dados["dados_intervencao"])
        logger.info(f"[WO {numero_wo}] Notificação de início enviada.")

        time.sleep(1)  # Simulação de envio ao portal
        logger.info(f"[WO {numero_wo}] Submissão simulada concluída. Enviando notificação final...")

        enviar_notificacao_wo_sucesso(tecnico_info["whatsapp"], numero_wo)
        logger.info(f"[WO {numero_wo}] Notificação de sucesso enviada.")
        logger.info(f"========================= FIM DA WO {numero_wo} =========================\n")
        return True

    except Exception as e:
        logger.exception(f"[WO {numero_wo}] Erro inesperado durante o processamento: {e}")
        enviar_notificacao_wo_erro(tecnico_info["whatsapp"], numero_wo)
        logger.info(f"========================= FIM DA WO {numero_wo} =========================\n")
        return False

# --- Movimentar arquivo ---
def mover_pdf(pdf_path, tecnico_nome, sucesso):
    destino = "processados" if sucesso else "erro"
    
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        base_dir = join_path('tecnicos_dir', tecnico_nome, "pdfs", destino, create=True)
    else:
        # Fallback para caminho absoluto
        base_dir = os.path.join(TECNICOS_DIR, tecnico_nome, "pdfs", destino)
        os.makedirs(base_dir, exist_ok=True)
        
    shutil.move(pdf_path, os.path.join(base_dir, os.path.basename(pdf_path)))

# --- Processar técnico ---
def processar_tecnico(tecnico_nome, tecnico_info, executor):
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        pasta_novos = join_path('tecnicos_dir', tecnico_nome, "pdfs", "novos")
    else:
        # Fallback para caminho absoluto
        pasta_novos = os.path.join(TECNICOS_DIR, tecnico_nome, "pdfs", "novos")
        
    logging.info(f"Verificando PDFs na pasta: {pasta_novos}")

    if not os.path.exists(pasta_novos):
        logging.warning(f"Pasta não encontrada: {pasta_novos}")
        return []

    arquivos = [f for f in os.listdir(pasta_novos) if f.lower().endswith(".pdf")]
    logging.info(f"Arquivos encontrados para {tecnico_nome}: {arquivos}")

    futuros = []
    for arq in arquivos:
        caminho_pdf = os.path.join(pasta_novos, arq)
        logging.info(f"Enviando {arq} para processamento...")
        futuro = executor.submit(processar_pdf_tecnico, caminho_pdf, tecnico_nome, tecnico_info)
        futuros.append((futuro, caminho_pdf, tecnico_nome))
    return futuros

# --- Obter técnicos ---
def get_tecnicos():
    if USING_PATH_UTILS:
        # Usar utilitários de caminho
        config_path = join_path('config_dir', "tecnicos.json")
    else:
        # Fallback para caminho absoluto
        config_path = CONFIG_TECNICOS_JSON_PATH
        
    if not os.path.exists(config_path):
        return {}
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Main ---
def main():
    tecnicos = get_tecnicos()
    ativos = [(nome, info) for nome, info in tecnicos.items() if info.get("ativo")]

    if not ativos:
        logging.info("Nenhum técnico ativo encontrado.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        todas = []
        for nome, info in ativos:
            todas += processar_tecnico(nome, info, executor)

        for futuro, caminho_pdf, tecnico_nome in todas:
            try:
                sucesso = futuro.result()
                mover_pdf(caminho_pdf, tecnico_nome, sucesso)
            except Exception as e:
                logging.error(f"Erro ao mover arquivo para {tecnico_nome}: {e}")
                mover_pdf(caminho_pdf, tecnico_nome, False)

if __name__ == "__main__":
    main()
