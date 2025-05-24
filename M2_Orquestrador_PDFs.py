#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M2_Orquestrador_PDFs.py
Sistema de filas para processamento de PDFs com mecanismos de retry e fallback.

Este módulo implementa um sistema robusto de filas para processamento ordenado de PDFs,
com mecanismos de priorização, retry com backoff exponencial e fallback para operações críticas.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import time
import json
import logging
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
from datetime import datetime

# Configuração de logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configuração do logger padrão
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler("orquestrador_pdfs.log"),
        logging.StreamHandler()
    ]
)

logger = structlog.get_logger()

# Definição de estados para tarefas
class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class PDFTask:
    """Representa uma tarefa de processamento de PDF com metadados e controle de estado."""
    
    def __init__(self, pdf_path, priority=0, task_id=None):
        """
        Inicializa uma nova tarefa de processamento de PDF.
        
        Args:
            pdf_path (str): Caminho completo para o arquivo PDF
            priority (int): Prioridade da tarefa (menor número = maior prioridade)
            task_id (str, optional): ID único da tarefa. Se None, será gerado automaticamente.
        """
        self.pdf_path = pdf_path
        self.priority = priority
        self.task_id = task_id or f"task_{int(time.time())}_{os.path.basename(pdf_path)}"
        self.status = TaskStatus.PENDING
        self.attempts = 0
        self.max_attempts = 3
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.result = None
        self.error = None
    
    def __lt__(self, other):
        """Permite comparação para ordenação baseada em prioridade."""
        return self.priority < other.priority
    
    def to_dict(self):
        """Converte a tarefa para um dicionário para serialização."""
        return {
            "task_id": self.task_id,
            "pdf_path": self.pdf_path,
            "priority": self.priority,
            "status": self.status.value,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria uma instância de PDFTask a partir de um dicionário."""
        task = cls(
            pdf_path=data["pdf_path"],
            priority=data["priority"],
            task_id=data["task_id"]
        )
        task.status = TaskStatus(data["status"])
        task.attempts = data["attempts"]
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.updated_at = datetime.fromisoformat(data["updated_at"])
        task.result = data["result"]
        task.error = data["error"]
        return task

class PDFQueue:
    """Sistema de filas para processamento ordenado de PDFs com priorização."""
    
    def __init__(self, max_workers=4, max_queue_size=100):
        """
        Inicializa o sistema de filas para processamento de PDFs.
        
        Args:
            max_workers (int): Número máximo de workers para processamento paralelo
            max_queue_size (int): Tamanho máximo da fila
        """
        self.task_queue = queue.PriorityQueue(maxsize=max_queue_size)
        self.processing_tasks = {}  # task_id -> PDFTask
        self.completed_tasks = {}   # task_id -> PDFTask
        self.failed_tasks = {}      # task_id -> PDFTask
        self.dead_letter_queue = {} # task_id -> PDFTask
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.RLock()
        self.running = False
        self.stats = {
            "enqueued": 0,
            "processed": 0,
            "completed": 0,
            "failed": 0,
            "retried": 0,
            "avg_processing_time_ms": 0
        }
        self.log = logger.bind(component="PDFQueue")
        self.log.info("Sistema de filas inicializado", max_workers=max_workers, max_queue_size=max_queue_size)
    
    def enqueue(self, pdf_path, priority=0):
        """
        Adiciona um PDF à fila de processamento.
        
        Args:
            pdf_path (str): Caminho completo para o arquivo PDF
            priority (int): Prioridade da tarefa (menor número = maior prioridade)
            
        Returns:
            str: ID da tarefa criada
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")
        
        task = PDFTask(pdf_path, priority)
        
        with self.lock:
            self.task_queue.put((priority, task))
            self.stats["enqueued"] += 1
        
        self.log.info("PDF adicionado à fila", 
                     task_id=task.task_id, 
                     pdf_path=pdf_path, 
                     priority=priority)
        
        return task.task_id
    
    def dequeue(self):
        """
        Obtém a próxima tarefa da fila com base na prioridade.
        
        Returns:
            PDFTask or None: A próxima tarefa a ser processada ou None se a fila estiver vazia
        """
        try:
            _, task = self.task_queue.get(block=False)
            
            with self.lock:
                task.status = TaskStatus.PROCESSING
                task.updated_at = datetime.now()
                self.processing_tasks[task.task_id] = task
            
            self.log.info("PDF removido da fila para processamento", 
                         task_id=task.task_id, 
                         pdf_path=task.pdf_path)
            
            return task
        except queue.Empty:
            return None
    
    def mark_completed(self, task_id, result=None):
        """
        Marca uma tarefa como concluída.
        
        Args:
            task_id (str): ID da tarefa
            result (dict, optional): Resultado do processamento
        """
        with self.lock:
            if task_id in self.processing_tasks:
                task = self.processing_tasks.pop(task_id)
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.now()
                task.result = result
                self.completed_tasks[task_id] = task
                self.stats["completed"] += 1
                self.stats["processed"] += 1
                
                self.log.info("Tarefa concluída com sucesso", 
                             task_id=task_id, 
                             pdf_path=task.pdf_path)
            else:
                self.log.warning("Tentativa de marcar como concluída uma tarefa inexistente", 
                                task_id=task_id)
    
    def mark_failed(self, task_id, error=None, retry=True):
        """
        Marca uma tarefa como falha e opcionalmente a coloca para retry.
        
        Args:
            task_id (str): ID da tarefa
            error (str, optional): Descrição do erro
            retry (bool): Se True, a tarefa será colocada para retry se não exceder o limite de tentativas
        """
        with self.lock:
            if task_id in self.processing_tasks:
                task = self.processing_tasks.pop(task_id)
                task.attempts += 1
                task.error = error
                task.updated_at = datetime.now()
                
                if retry and task.attempts < task.max_attempts:
                    task.status = TaskStatus.RETRY
                    # Cálculo de backoff exponencial para prioridade
                    retry_priority = task.priority + (2 ** (task.attempts - 1))
                    self.task_queue.put((retry_priority, task))
                    self.stats["retried"] += 1
                    
                    self.log.warning("Tarefa falhou e será reprocessada", 
                                    task_id=task_id, 
                                    pdf_path=task.pdf_path, 
                                    attempts=task.attempts, 
                                    error=error)
                else:
                    task.status = TaskStatus.FAILED
                    self.failed_tasks[task_id] = task
                    self.stats["failed"] += 1
                    
                    # Se excedeu o número máximo de tentativas, move para a dead letter queue
                    if task.attempts >= task.max_attempts:
                        self.dead_letter_queue[task_id] = task
                        self.log.error("Tarefa falhou permanentemente e foi movida para dead letter queue", 
                                      task_id=task_id, 
                                      pdf_path=task.pdf_path, 
                                      attempts=task.attempts, 
                                      error=error)
                    else:
                        self.log.error("Tarefa falhou sem retry", 
                                      task_id=task_id, 
                                      pdf_path=task.pdf_path, 
                                      error=error)
                
                self.stats["processed"] += 1
            else:
                self.log.warning("Tentativa de marcar como falha uma tarefa inexistente", 
                                task_id=task_id)
    
    def get_task_status(self, task_id):
        """
        Obtém o status atual de uma tarefa.
        
        Args:
            task_id (str): ID da tarefa
            
        Returns:
            dict: Status da tarefa ou None se não encontrada
        """
        with self.lock:
            # Verifica em todas as coleções possíveis
            for collection in [self.processing_tasks, self.completed_tasks, 
                              self.failed_tasks, self.dead_letter_queue]:
                if task_id in collection:
                    return collection[task_id].to_dict()
            
            # Verifica na fila (mais custoso)
            for _, task in list(self.task_queue.queue):
                if task.task_id == task_id:
                    return task.to_dict()
        
        return None
    
    def get_queue_status(self):
        """
        Obtém o status atual da fila.
        
        Returns:
            dict: Estatísticas e status da fila
        """
        with self.lock:
            status = {
                "stats": self.stats.copy(),
                "queue_size": self.task_queue.qsize(),
                "processing": len(self.processing_tasks),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "dead_letter": len(self.dead_letter_queue)
            }
        
        return status
    
    def start_processing(self, processor_func):
        """
        Inicia o processamento contínuo da fila em background.
        
        Args:
            processor_func (callable): Função que processa um PDF
                A função deve aceitar um parâmetro (pdf_path) e retornar um resultado ou lançar exceção
        """
        if self.running:
            self.log.warning("Tentativa de iniciar processamento quando já está em execução")
            return
        
        self.running = True
        self.log.info("Iniciando processamento contínuo da fila")
        
        def worker():
            while self.running:
                task = self.dequeue()
                if not task:
                    time.sleep(0.1)  # Evita consumo excessivo de CPU quando a fila está vazia
                    continue
                
                task_log = self.log.bind(task_id=task.task_id, pdf_path=task.pdf_path)
                task_log.info("Iniciando processamento de PDF")
                
                start_time = time.time()
                
                try:
                    # Executa o processamento com retry automático
                    result = self._process_with_retry(processor_func, task)
                    self.mark_completed(task.task_id, result)
                    
                    # Atualiza estatística de tempo médio de processamento
                    processing_time_ms = (time.time() - start_time) * 1000
                    with self.lock:
                        current_avg = self.stats["avg_processing_time_ms"]
                        processed = self.stats["processed"]
                        if processed > 1:  # Evita divisão por zero no primeiro processamento
                            self.stats["avg_processing_time_ms"] = (
                                (current_avg * (processed - 1) + processing_time_ms) / processed
                            )
                        else:
                            self.stats["avg_processing_time_ms"] = processing_time_ms
                    
                    task_log.info("Processamento de PDF concluído com sucesso", 
                                 processing_time_ms=processing_time_ms)
                    
                except Exception as e:
                    task_log.exception("Erro no processamento de PDF", 
                                      error=str(e))
                    self.mark_failed(task.task_id, str(e))
        
        # Inicia workers em threads separadas
        for _ in range(self.executor._max_workers):
            threading.Thread(target=worker, daemon=True).start()
    
    def stop_processing(self):
        """Para o processamento contínuo da fila."""
        if not self.running:
            return
        
        self.running = False
        self.log.info("Parando processamento da fila")
        
        # Aguarda a conclusão de todas as tarefas em andamento
        self.executor.shutdown(wait=True)
        
        self.log.info("Processamento da fila parado com sucesso")
    
    def _process_with_retry(self, processor_func, task):
        """
        Processa um PDF com retry automático usando backoff exponencial.
        
        Args:
            processor_func (callable): Função que processa um PDF
            task (PDFTask): Tarefa a ser processada
            
        Returns:
            dict: Resultado do processamento
            
        Raises:
            Exception: Se o processamento falhar após todas as tentativas
        """
        @retry(
            stop=stop_after_attempt(task.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type((IOError, ConnectionError, TimeoutError)),
            reraise=True
        )
        def _process():
            return processor_func(task.pdf_path)
        
        return _process()

class BackendIntegration:
    """Interface de comunicação com a API do backend."""
    
    def __init__(self, api_url, timeout=10):
        """
        Inicializa a integração com o backend.
        
        Args:
            api_url (str): URL base da API do backend
            timeout (int): Timeout para requisições em segundos
        """
        self.api_url = api_url
        self.timeout = timeout
        self.log = logger.bind(component="BackendIntegration")
        self.log.info("Integração com backend inicializada", api_url=api_url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True
    )
    def send_data(self, endpoint, data, headers=None):
        """
        Envia dados para o backend.
        
        Args:
            endpoint (str): Endpoint da API
            data (dict): Dados a serem enviados
            headers (dict, optional): Cabeçalhos HTTP adicionais
            
        Returns:
            dict: Resposta da API
            
        Raises:
            requests.RequestException: Se a requisição falhar após todas as tentativas
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        self.log.info("Enviando dados para backend", 
                     endpoint=endpoint, 
                     data_size=len(json.dumps(data)))
        
        response = requests.post(
            url, 
            json=data, 
            headers=default_headers, 
            timeout=self.timeout
        )
        
        response.raise_for_status()
        
        self.log.info("Dados enviados com sucesso para backend", 
                     endpoint=endpoint, 
                     status_code=response.status_code)
        
        return response.json()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True
    )
    def get_data(self, endpoint, params=None, headers=None):
        """
        Obtém dados do backend.
        
        Args:
            endpoint (str): Endpoint da API
            params (dict, optional): Parâmetros da query string
            headers (dict, optional): Cabeçalhos HTTP adicionais
            
        Returns:
            dict: Resposta da API
            
        Raises:
            requests.RequestException: Se a requisição falhar após todas as tentativas
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        default_headers = {
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        self.log.info("Obtendo dados do backend", 
                     endpoint=endpoint, 
                     params=params)
        
        response = requests.get(
            url, 
            params=params, 
            headers=default_headers, 
            timeout=self.timeout
        )
        
        response.raise_for_status()
        
        self.log.info("Dados obtidos com sucesso do backend", 
                     endpoint=endpoint, 
                     status_code=response.status_code)
        
        return response.json()

class PDFProcessor:
    """Processador de PDFs com integração ao backend."""
    
    def __init__(self, backend_url, output_dir="processados", error_dir="erros"):
        """
        Inicializa o processador de PDFs.
        
        Args:
            backend_url (str): URL base da API do backend
            output_dir (str): Diretório para PDFs processados com sucesso
            error_dir (str): Diretório para PDFs com erro
        """
        self.queue = PDFQueue(max_workers=4)
        self.backend = BackendIntegration(backend_url)
        self.output_dir = output_dir
        self.error_dir = error_dir
        self.log = logger.bind(component="PDFProcessor")
        
        # Cria diretórios de saída se não existirem
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(error_dir, exist_ok=True)
        
        self.log.info("Processador de PDFs inicializado", 
                     backend_url=backend_url, 
                     output_dir=output_dir, 
                     error_dir=error_dir)
    
    def start(self):
        """Inicia o processamento de PDFs."""
        self.queue.start_processing(self.process_pdf)
        self.log.info("Processador de PDFs iniciado")
    
    def stop(self):
        """Para o processamento de PDFs."""
        self.queue.stop_processing()
        self.log.info("Processador de PDFs parado")
    
    def add_pdf(self, pdf_path, priority=0):
        """
        Adiciona um PDF para processamento.
        
        Args:
            pdf_path (str): Caminho completo para o arquivo PDF
            priority (int): Prioridade da tarefa (menor número = maior prioridade)
            
        Returns:
            str: ID da tarefa criada
        """
        return self.queue.enqueue(pdf_path, priority)
    
    def process_pdf(self, pdf_path):
        """
        Processa um PDF e envia os dados para o backend.
        
        Args:
            pdf_path (str): Caminho completo para o arquivo PDF
            
        Returns:
            dict: Resultado do processamento
            
        Raises:
            Exception: Se o processamento falhar
        """
        pdf_log = self.log.bind(pdf_path=pdf_path)
        pdf_log.info("Iniciando processamento de PDF")
        
        try:
            # Aqui seria chamada a função de extração de dados do PDF
            # Implementação simulada para fins de exemplo
            pdf_data = self._extract_pdf_data(pdf_path)
            
            # Envia dados para o backend
            response = self.backend.send_data(
                "api/wondercom/allocate", 
                {
                    "pdf_data": pdf_data,
                    "pdf_name": os.path.basename(pdf_path)
                }
            )
            
            # Move o PDF para o diretório de processados
            output_path = os.path.join(
                self.output_dir, 
                os.path.basename(pdf_path)
            )
            os.rename(pdf_path, output_path)
            
            pdf_log.info("PDF processado com sucesso", 
                        output_path=output_path, 
                        response=response)
            
            return {
                "success": True,
                "pdf_data": pdf_data,
                "backend_response": response,
                "output_path": output_path
            }
            
        except Exception as e:
            pdf_log.exception("Erro no processamento de PDF", 
                             error=str(e))
            
            # Move o PDF para o diretório de erros
            error_path = os.path.join(
                self.error_dir, 
                os.path.basename(pdf_path)
            )
            os.rename(pdf_path, error_path)
            
            raise
    
    def _extract_pdf_data(self, pdf_path):
        """
        Extrai dados de um PDF.
        
        Args:
            pdf_path (str): Caminho completo para o arquivo PDF
            
        Returns:
            dict: Dados extraídos do PDF
        """
        # Implementação simulada - em um cenário real, isso chamaria
        # o módulo de extração de dados desenvolvido pelo Especialista em Automação #1
        self.log.info("Extraindo dados do PDF", pdf_path=pdf_path)
        
        # Simulação de extração de dados
        return {
            "numero_wo": f"WO-{int(time.time())}",
            "dados_intervencao": {
                "data": datetime.now().strftime("%Y-%m-%d"),
                "tecnico": "Técnico Exemplo",
                "tipo": "Instalação"
            },
            "observacoes": "Observações de exemplo extraídas do PDF",
            "materiais": [
                {"codigo": "MAT001", "quantidade": 2},
                {"codigo": "MAT002", "quantidade": 1}
            ],
            "equipamentos": [
                {"serial": "EQ001", "modelo": "Modelo A"},
                {"serial": "EQ002", "modelo": "Modelo B"}
            ]
        }

def monitor_directory(directory, processor, interval=5):
    """
    Monitora um diretório por novos PDFs e os adiciona à fila de processamento.
    
    Args:
        directory (str): Diretório a ser monitorado
        processor (PDFProcessor): Processador de PDFs
        interval (int): Intervalo de verificação em segundos
    """
    log = logger.bind(component="DirectoryMonitor", directory=directory)
    log.info("Iniciando monitoramento de diretório")
    
    os.makedirs(directory, exist_ok=True)
    
    while True:
        try:
            for filename in os.listdir(directory):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(directory, filename)
                    
                    # Verifica se o arquivo não está sendo escrito
                    # (tamanho estável por 2 segundos)
                    size1 = os.path.getsize(pdf_path)
                    time.sleep(2)
                    size2 = os.path.getsize(pdf_path)
                    
                    if size1 == size2:
                        log.info("Novo PDF detectado", filename=filename)
                        processor.add_pdf(pdf_path)
            
            time.sleep(interval)
        except Exception as e:
            log.exception("Erro ao monitorar diretório", error=str(e))
            time.sleep(interval)

def main():
    """Função principal."""
    # Configuração
    backend_url = "https://dashboard-backend-s1bx.onrender.com"
    input_dir = "pdfs_entrada"
    output_dir = "pdfs_processados"
    error_dir = "pdfs_erro"
    
    # Inicializa o processador
    processor = PDFProcessor(backend_url, output_dir, error_dir)
    
    # Inicia o processamento
    processor.start()
    
    try:
        # Inicia o monitoramento de diretório em uma thread separada
        monitor_thread = threading.Thread(
            target=monitor_directory,
            args=(input_dir, processor),
            daemon=True
        )
        monitor_thread.start()
        
        # Mantém o programa em execução
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nEncerrando processador...")
        processor.stop()
        print("Processador encerrado.")

if __name__ == "__main__":
    main()
