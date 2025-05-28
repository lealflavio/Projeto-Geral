import os
import json
import shutil
import time
import logging
# Suprimir logs internos excessivos do Twilio
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)
import concurrent.futures
from datetime import datetime
from M1_Extrator_PDF import extrair_dados_pdf_relevantes
#from M6_Notificacao_Status import (
#    enviar_notificacao_boas_vindas,
#    enviar_notificacao_wo_iniciada,
#    enviar_notificacao_wo_sucesso,
#    enviar_notificacao_wo_erro
#)

# --- Configurações ---
TECNICOS_DIR = "/home/flavioleal_souza/Sistema/tecnicos"
CONFIG_TECNICOS_JSON_PATH = "/home/flavioleal_souza/Sistema/config/tecnicos.json"
NUM_THREADS = 4

# --- Logger global ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Logger por técnico ---
def configurar_logger(tecnico_nome):
    data_hoje = datetime.now().strftime("%Y-%m-%d")
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

        logger.info(f"Dados extraídos salvos em: /home/flavioleal_souza/Sistema/extracao_dados/{numero_wo}_dados.json")
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
    base_dir = os.path.join(TECNICOS_DIR, tecnico_nome, "pdfs", destino)
    os.makedirs(base_dir, exist_ok=True)
    shutil.move(pdf_path, os.path.join(base_dir, os.path.basename(pdf_path)))

# --- Processar técnico ---
def processar_tecnico(tecnico_nome, tecnico_info, executor):
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
    if not os.path.exists(CONFIG_TECNICOS_JSON_PATH):
        return {}
    with open(CONFIG_TECNICOS_JSON_PATH, "r", encoding="utf-8") as f:
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
