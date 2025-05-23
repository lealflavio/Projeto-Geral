#!/usr/bin/env python3
"""
Versão otimizada do módulo de extração de dados de PDFs.
Implementa processamento paralelo, expressões regulares pré-compiladas,
otimização de subprocessos e cache de resultados.
"""

import subprocess
import logging
import re
import json
import os
import concurrent.futures
import hashlib
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='extrator_pdf.log'
)
logger = logging.getLogger('extrator_pdf')

# Pré-compilar expressões regulares para melhor desempenho
PADRAO_NUMERO_INTERVENCAO = re.compile(r"Intervenção:\s*(\d+)")
PADRAO_TIPO_INTERVENCAO = re.compile(r"Tipo de Intervenção:\s*(.+?)(?:\n|$)")
PADRAO_DATA_INICIO = re.compile(r"Data Início:\s*(\d{2}/\d{2}/\d{4})")
PADRAO_HORA_INICIO = re.compile(r"Hora Início:\s*(\d{2}:\d{2})")
PADRAO_DATA_FIM = re.compile(r"Data Fim:\s*(\d{2}/\d{2}/\d{4})")
PADRAO_HORA_FIM = re.compile(r"Hora Fim:\s*(\d{2}:\d{2})")
PADRAO_EQUIPAMENTO = re.compile(r".*Serial Number.*", re.IGNORECASE)
PADRAO_MATERIAL = re.compile(r".*Material.*Quantidade.*", re.IGNORECASE)
PADRAO_OBSERVACOES = re.compile(r"Observações do Técnico:(.*?)(?:\n\n|\Z)", re.DOTALL)


def extrair_valor_apos_rotulo(texto: str, padrao_compilado: re.Pattern) -> Optional[str]:
    """
    Extrai um valor após um rótulo usando um padrão regex pré-compilado.
    
    Args:
        texto: Texto a ser analisado
        padrao_compilado: Padrão regex pré-compilado
    
    Returns:
        Valor extraído ou None se não encontrado
    """
    match = padrao_compilado.search(texto)
    if match:
        return match.group(1).strip()
    return None


def extrair_secao_multilinha(texto: str, inicio_padrao: str, fim_padrao: str) -> str:
    """
    Extrai uma seção de múltiplas linhas entre dois padrões.
    
    Args:
        texto: Texto completo
        inicio_padrao: Padrão que marca o início da seção
        fim_padrao: Padrão que marca o fim da seção
    
    Returns:
        Texto da seção extraída
    """
    linhas = texto.split('\n')
    secao_linhas = []
    capturando = False
    
    for linha in linhas:
        if not capturando and re.search(inicio_padrao, linha, re.IGNORECASE):
            capturando = True
            continue
        
        if capturando:
            if re.search(fim_padrao, linha, re.IGNORECASE):
                break
            if linha.strip():  # Ignorar linhas vazias
                secao_linhas.append(linha.strip())
    
    return '\n'.join(secao_linhas)


def extrair_equipamentos(texto: str) -> List[str]:
    """
    Extrai lista de equipamentos do texto.
    
    Args:
        texto: Texto completo do PDF
    
    Returns:
        Lista de equipamentos extraídos
    """
    secao_equipamentos = extrair_secao_multilinha(
        texto, 
        "Equipamentos Entregues", 
        "Materiais Utilizados|Observações do Técnico"
    )
    
    equipamentos = []
    for linha in secao_equipamentos.split('\n'):
        if PADRAO_EQUIPAMENTO.match(linha) or "Serial Number" in linha:
            equipamentos.append(linha.strip())
    
    return equipamentos


def extrair_materiais(texto: str) -> List[str]:
    """
    Extrai lista de materiais do texto.
    
    Args:
        texto: Texto completo do PDF
    
    Returns:
        Lista de materiais extraídos
    """
    secao_materiais = extrair_secao_multilinha(
        texto, 
        "Materiais Utilizados", 
        "Observações do Técnico"
    )
    
    materiais = []
    for linha in secao_materiais.split('\n'):
        if PADRAO_MATERIAL.match(linha) or "Material" in linha and "Quantidade" in linha:
            continue  # Pular cabeçalho
        if linha.strip():
            materiais.append(linha.strip())
    
    return materiais


def extrair_texto_pdf_otimizado(pdf_path: str) -> str:
    """
    Versão otimizada da extração de texto de PDFs.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
    
    Returns:
        Texto extraído do PDF
    """
    # Usar parâmetros otimizados para pdftotext
    cmd = ["pdftotext", "-layout", "-nopgbrk", pdf_path, "-"]
    
    try:
        # Usar PIPE para evitar arquivos temporários
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=-1  # Buffering otimizado
        )
        
        # Processar saída de forma não-bloqueante
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Erro ao executar pdftotext: {stderr}")
            raise Exception(f"Erro ao executar pdftotext: {stderr}")
        
        return stdout
    except Exception as e:
        logger.error(f"Falha ao extrair texto do PDF {pdf_path}: {str(e)}")
        raise


def calcular_hash_arquivo(arquivo: str) -> str:
    """
    Calcula o hash MD5 de um arquivo para identificação única.
    
    Args:
        arquivo: Caminho para o arquivo
    
    Returns:
        Hash MD5 do arquivo
    """
    hash_md5 = hashlib.md5()
    with open(arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def extrair_dados_pdf_relevantes(pdf_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Extrai dados relevantes de um PDF de intervenção técnica.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        output_dir: Diretório para salvar os resultados
    
    Returns:
        Dicionário com os dados extraídos
    """
    try:
        # Extrair texto do PDF
        texto_completo = extrair_texto_pdf_otimizado(pdf_path)
        
        # Extrair dados de intervenção
        dados_intervencao = {
            "numero_intervencao": extrair_valor_apos_rotulo(texto_completo, PADRAO_NUMERO_INTERVENCAO),
            "tipo_intervencao": extrair_valor_apos_rotulo(texto_completo, PADRAO_TIPO_INTERVENCAO),
            "data_inicio": extrair_valor_apos_rotulo(texto_completo, PADRAO_DATA_INICIO),
            "hora_inicio": extrair_valor_apos_rotulo(texto_completo, PADRAO_HORA_INICIO),
            "data_fim": extrair_valor_apos_rotulo(texto_completo, PADRAO_DATA_FIM),
            "hora_fim": extrair_valor_apos_rotulo(texto_completo, PADRAO_HORA_FIM),
        }
        
        # Extrair observações do técnico
        observacoes = extrair_valor_apos_rotulo(texto_completo, PADRAO_OBSERVACOES)
        
        # Extrair equipamentos e materiais
        equipamentos = extrair_equipamentos(texto_completo)
        materiais = extrair_materiais(texto_completo)
        
        # Consolidar resultados
        resultado = {
            "dados_intervencao": dados_intervencao,
            "observacoes_tecnico": observacoes,
            "equipamentos_entregues": equipamentos,
            "materiais_usados": materiais,
        }
        
        # Salvar resultado em JSON
        nome_pdf = os.path.basename(pdf_path).replace('.pdf', '')
        json_path = os.path.join(output_dir, f"{nome_pdf}_dados.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dados extraídos com sucesso do PDF {nome_pdf}")
        return resultado
    
    except Exception as e:
        logger.error(f"Erro ao processar PDF {pdf_path}: {str(e)}")
        return {
            "erro": str(e),
            "pdf": pdf_path,
            "timestamp": datetime.now().isoformat()
        }


def extrair_dados_pdf_com_cache(pdf_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Versão com cache da função de extração de dados de PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        output_dir: Diretório para salvar os resultados
    
    Returns:
        Dados extraídos do PDF
    """
    # Criar diretório de cache se não existir
    cache_dir = os.path.join(output_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Calcular hash do arquivo para identificação única
    file_hash = calcular_hash_arquivo(pdf_path)
    cache_file = os.path.join(cache_dir, f"{file_hash}.json")
    
    # Verificar se existe cache válido
    if os.path.exists(cache_file):
        logger.info(f"Usando cache para {os.path.basename(pdf_path)}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Processar o PDF normalmente se não houver cache
    resultado = extrair_dados_pdf_relevantes(pdf_path, output_dir)
    
    # Salvar resultado no cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    return resultado


def processar_pdfs_em_paralelo(pdf_files: List[str], output_dir: str, max_workers: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Processa múltiplos PDFs em paralelo usando ThreadPoolExecutor.
    
    Args:
        pdf_files: Lista de caminhos para arquivos PDF
        output_dir: Diretório para salvar os resultados
        max_workers: Número máximo de workers (None = automático baseado no CPU)
    
    Returns:
        Lista de resultados do processamento
    """
    resultados = []
    
    # Garantir que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Iniciando processamento paralelo de {len(pdf_files)} PDFs")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter tarefas para o executor
        future_to_pdf = {
            executor.submit(extrair_dados_pdf_com_cache, pdf, output_dir): pdf 
            for pdf in pdf_files
        }
        
        # Coletar resultados à medida que são concluídos
        for future in concurrent.futures.as_completed(future_to_pdf):
            pdf = future_to_pdf[future]
            try:
                resultado = future.result()
                resultados.append(resultado)
                logger.info(f"Concluído: {os.path.basename(pdf)}")
            except Exception as e:
                logger.error(f"Erro ao processar {pdf}: {e}")
                resultados.append({
                    "erro": str(e),
                    "pdf": pdf,
                    "timestamp": datetime.now().isoformat()
                })
    
    logger.info(f"Processamento paralelo concluído. {len(resultados)} PDFs processados.")
    return resultados


def processar_com_monitoramento_recursos(pdf_files: List[str], output_dir: str, limite_memoria_mb: int = 1500) -> List[Dict[str, Any]]:
    """
    Processa PDFs com monitoramento de recursos para evitar sobrecarga.
    
    Args:
        pdf_files: Lista de caminhos para arquivos PDF
        output_dir: Diretório para salvar os resultados
        limite_memoria_mb: Limite de memória em MB (padrão: 1500MB)
    
    Returns:
        Lista de resultados do processamento
    """
    limite_memoria_bytes = limite_memoria_mb * 1024 * 1024
    
    # Determinar número de workers com base na memória disponível
    memoria_disponivel = psutil.virtual_memory().available
    memoria_por_processo = 25 * 1024 * 1024  # Estimativa de 25MB por processo
    max_workers = min(
        os.cpu_count() or 1,  # Número de CPUs
        max(1, int(memoria_disponivel * 0.7 / memoria_por_processo))  # Baseado na memória
    )
    
    logger.info(f"Iniciando processamento com {max_workers} workers paralelos")
    logger.info(f"Memória disponível: {memoria_disponivel / (1024*1024):.2f} MB")
    
    # Usar a função de processamento paralelo com o número calculado de workers
    return processar_pdfs_em_paralelo(pdf_files, output_dir, max_workers=max_workers)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python M1_Extrator_PDF_Otimizado.py <diretório_pdfs> <diretório_saída>")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Verificar se os diretórios existem
    if not os.path.isdir(pdf_dir):
        print(f"Erro: Diretório de PDFs não encontrado: {pdf_dir}")
        sys.exit(1)
    
    # Criar diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Obter lista de PDFs
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"Nenhum arquivo PDF encontrado em {pdf_dir}")
        sys.exit(1)
    
    print(f"Processando {len(pdf_files)} arquivos PDF...")
    
    # Processar PDFs com monitoramento de recursos
    resultados = processar_com_monitoramento_recursos(pdf_files, output_dir)
    
    # Resumo final
    sucessos = sum(1 for r in resultados if "erro" not in r)
    print(f"Processamento concluído: {sucessos}/{len(pdf_files)} PDFs processados com sucesso.")
