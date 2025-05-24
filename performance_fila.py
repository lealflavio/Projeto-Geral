#!/usr/bin/env python3
"""
Sistema de otimização de performance e integração com filas.

Este módulo fornece funcionalidades para monitorar performance,
processar tarefas em paralelo e integrar com um sistema de filas
persistente para o Projeto Wondercom Automation.
"""

import os
import time
import json
import logging
import sqlite3
import threading
import concurrent.futures
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Tuple
import queue
import uuid

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), \'performance_fila.log\'))
    ]
)
logger = logging.getLogger(\'performance_fila\')

# Constantes
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.db")
DEFAULT_MAX_WORKERS = 4
DEFAULT_TASK_TIMEOUT = 300  # 5 minutos

# Status da Tarefa
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_TIMEOUT = "timeout"

class PerformanceMonitor:
    """Monitor de performance para tarefas."""
    
    def __init__(self):
        self.metrics = {}
        self._lock = threading.RLock()
    
    def start_timer(self, task_id: str, metric_name: str) -> None:
        """Inicia um temporizador para uma métrica específica."""
        with self._lock:
            if task_id not in self.metrics:
                self.metrics[task_id] = {}
            
            self.metrics[task_id][metric_name] = {
                "start_time": time.perf_counter(),
                "end_time": None,
                "duration": None
            }
            logger.debug(f"Timer iniciado para {task_id} - {metric_name}")
    
    def stop_timer(self, task_id: str, metric_name: str) -> Optional[float]:
        """Para um temporizador e calcula a duração."""
        with self._lock:
            if task_id in self.metrics and metric_name in self.metrics[task_id]:
                metric = self.metrics[task_id][metric_name]
                if metric["start_time"] is not None and metric["end_time"] is None:
                    metric["end_time"] = time.perf_counter()
                    metric["duration"] = metric["end_time"] - metric["start_time"]
                    logger.debug(f"Timer parado para {task_id} - {metric_name}. Duração: {metric[\'duration\']:.4f}s")
                    return metric["duration"]
            
            logger.warning(f"Timer não encontrado ou já parado para {task_id} - {metric_name}")
            return None
    
    def get_metrics(self, task_id: str) -> Dict[str, Dict[str, Any]]:
        """Obtém todas as métricas para uma tarefa."""
        with self._lock:
            return self.metrics.get(task_id, {})
    
    def get_duration(self, task_id: str, metric_name: str) -> Optional[float]:
        """Obtém a duração de uma métrica específica."""
        with self._lock:
            metric = self.metrics.get(task_id, {}).get(metric_name)
            if metric and metric["duration"] is not None:
                return metric["duration"]
            return None
    
    def clear_metrics(self, task_id: str) -> None:
        """Limpa as métricas para uma tarefa."""
        with self._lock:
            if task_id in self.metrics:
                del self.metrics[task_id]
                logger.debug(f"Métricas limpas para {task_id}")


class PersistentQueue:
    """Fila persistente baseada em SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa a fila persistente.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados SQLite
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._lock = threading.RLock()  # Lock para acesso ao banco de dados
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializa o banco de dados e a tabela da fila."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                data TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT \'pending\',
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retries INTEGER DEFAULT 0,
                result TEXT,
                error_message TEXT
            )
            """)
            # Adicionar índice para otimizar busca por status e prioridade
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_priority ON queue (status, priority DESC, created_at)")
            conn.commit()
            conn.close()
            logger.info(f"Banco de dados da fila inicializado em {self.db_path}")
    
    def _execute_query(self, query: str, params: tuple = ()) -> Any:
        """Executa uma query no banco de dados de forma segura."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor
            except sqlite3.Error as e:
                logger.error(f"Erro no banco de dados: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def add_task(self, task_type: str, data: Dict[str, Any], priority: int = 0) -> str:
        """
        Adiciona uma nova tarefa à fila.
        
        Args:
            task_type: Tipo da tarefa (ex: \'process_pdf\', \'submit_form\')
            data: Dados da tarefa em formato JSON serializável
            priority: Prioridade da tarefa (maior = mais prioritário)
            
        Returns:
            ID da tarefa adicionada
        """
        task_id = str(uuid.uuid4())
        data_json = json.dumps(data)
        query = """
        INSERT INTO queue (id, task_type, data, priority, status)
        VALUES (?, ?, ?, ?, ?)
        """
        self._execute_query(query, (task_id, task_type, data_json, priority, STATUS_PENDING))
        logger.info(f"Tarefa adicionada à fila: {task_id} (Tipo: {task_type}, Prioridade: {priority})")
        return task_id
    
    def get_pending_task(self) -> Optional[Dict[str, Any]]:
        """
        Obtém a próxima tarefa pendente da fila (com maior prioridade e mais antiga).
        Marca a tarefa como \'processing\'.
        
        Returns:
            Dicionário com os dados da tarefa ou None se a fila estiver vazia
        """
        with self._lock:
            # Buscar a tarefa pendente com maior prioridade e mais antiga
            query_select = """
            SELECT id, task_type, data, retries FROM queue
            WHERE status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
            """
            cursor = self._execute_query(query_select, (STATUS_PENDING,))
            task_row = cursor.fetchone()
            
            if task_row:
                task_id, task_type, data_json, retries = task_row
                
                # Marcar a tarefa como processing
                query_update = """
                UPDATE queue SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = ?
                """
                cursor_update = self._execute_query(query_update, (STATUS_PROCESSING, task_id, STATUS_PENDING))
                
                # Verificar se a atualização foi bem-sucedida (evitar race condition)
                if cursor_update.rowcount > 0:
                    logger.info(f"Tarefa obtida da fila: {task_id} (Tipo: {task_type})")
                    return {
                        "id": task_id,
                        "task_type": task_type,
                        "data": json.loads(data_json),
                        "retries": retries
                    }
                else:
                    # A tarefa foi pega por outro worker, tentar novamente
                    logger.warning(f"Falha ao bloquear tarefa {task_id}, possivelmente pega por outro worker.")
                    return self.get_pending_task() # Recursivo, mas com lock deve ser raro
            else:
                # Fila vazia
                return None
    
    def update_task_status(self, task_id: str, status: str, 
                           result: Optional[Dict[str, Any]] = None, 
                           error_message: Optional[str] = None) -> None:
        """
        Atualiza o status de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            status: Novo status (completed, failed, pending)
            result: Resultado da tarefa (se completed)
            error_message: Mensagem de erro (se failed)
        """
        result_json = json.dumps(result) if result else None
        query = """
        UPDATE queue SET status = ?, result = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        self._execute_query(query, (status, result_json, error_message, task_id))
        logger.info(f"Status da tarefa {task_id} atualizado para: {status}")
    
    def increment_retry(self, task_id: str) -> int:
        """
        Incrementa o contador de retentativas para uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Novo número de retentativas
        """
        query = """
        UPDATE queue SET retries = retries + 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        self._execute_query(query, (task_id,))
        
        # Obter novo número de retries
        query_select = "SELECT retries FROM queue WHERE id = ?"
        cursor = self._execute_query(query_select, (task_id,))
        retries = cursor.fetchone()[0]
        logger.info(f"Contador de retentativas incrementado para {task_id}: {retries}")
        return retries
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o status e informações de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dicionário com informações da tarefa ou None se não encontrada
        """
        query = "SELECT id, task_type, status, created_at, updated_at, retries, result, error_message FROM queue WHERE id = ?"
        cursor = self._execute_query(query, (task_id,))
        row = cursor.fetchone()
        
        if row:
            task_id, task_type, status, created_at, updated_at, retries, result_json, error_message = row
            return {
                "id": task_id,
                "task_type": task_type,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
                "retries": retries,
                "result": json.loads(result_json) if result_json else None,
                "error_message": error_message
            }
        else:
            return None
    
    def count_tasks(self, status: Optional[str] = None) -> int:
        """
        Conta o número de tarefas na fila, opcionalmente filtrando por status.
        
        Args:
            status: Status para filtrar (opcional)
            
        Returns:
            Número de tarefas
        """
        if status:
            query = "SELECT COUNT(*) FROM queue WHERE status = ?"
            cursor = self._execute_query(query, (status,))
        else:
            query = "SELECT COUNT(*) FROM queue"
            cursor = self._execute_query(query)
            
        return cursor.fetchone()[0]
    
    def clear_queue(self, status: Optional[str] = None) -> int:
        """
        Remove tarefas da fila, opcionalmente filtrando por status.
        
        Args:
            status: Status para filtrar (se None, remove todas)
            
        Returns:
            Número de tarefas removidas
        """
        if status:
            query = "DELETE FROM queue WHERE status = ?"
            cursor = self._execute_query(query, (status,))
        else:
            query = "DELETE FROM queue"
            cursor = self._execute_query(query)
            
        removed_count = cursor.rowcount
        logger.info(f"Removidas {removed_count} tarefas da fila (Status: {status or \'Todos\'})")
        return removed_count


class TaskProcessor:
    """
    Processador de tarefas que utiliza a fila persistente e processamento paralelo.
    """
    
    def __init__(self, queue_manager: PersistentQueue, 
                 task_handlers: Dict[str, Callable], 
                 max_workers: int = DEFAULT_MAX_WORKERS,
                 max_retries: int = 3):
        """
        Inicializa o processador de tarefas.
        
        Args:
            queue_manager: Instância de PersistentQueue
            task_handlers: Dicionário mapeando task_type para funções de tratamento
            max_workers: Número máximo de workers paralelos
            max_retries: Número máximo de retentativas para tarefas falhadas
        """
        self.queue = queue_manager
        self.handlers = task_handlers
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.performance_monitor = PerformanceMonitor()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self._stop_event = threading.Event()
        self._workers = []
        logger.info(f"Processador de tarefas inicializado com {self.max_workers} workers")
    
    def _process_single_task(self, task: Dict[str, Any]) -> None:
        """Processa uma única tarefa."""
        task_id = task["id"]
        task_type = task["task_type"]
        data = task["data"]
        retries = task["retries"]
        
        logger.info(f"Processando tarefa: {task_id} (Tipo: {task_type}, Tentativa: {retries + 1})")
        self.performance_monitor.start_timer(task_id, "total_processing_time")
        
        try:
            # Verificar se o handler existe
            if task_type not in self.handlers:
                raise ValueError(f"Handler não encontrado para o tipo de tarefa: {task_type}")
            
            handler = self.handlers[task_type]
            
            # Executar o handler
            self.performance_monitor.start_timer(task_id, "handler_execution_time")
            result = handler(data, self.performance_monitor, task_id)
            self.performance_monitor.stop_timer(task_id, "handler_execution_time")
            
            # Atualizar status para completed
            self.queue.update_task_status(task_id, STATUS_COMPLETED, result=result)
            logger.info(f"Tarefa {task_id} concluída com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao processar tarefa {task_id}: {str(e)}", exc_info=True)
            
            # Verificar retentativas
            if retries < self.max_retries:
                # Incrementar retry e voltar para pending
                self.queue.increment_retry(task_id)
                self.queue.update_task_status(task_id, STATUS_PENDING, error_message=str(e))
                logger.warning(f"Tarefa {task_id} falhou, será tentada novamente (Tentativa {retries + 2})")
            else:
                # Marcar como failed
                self.queue.update_task_status(task_id, STATUS_FAILED, error_message=str(e))
                logger.error(f"Tarefa {task_id} falhou após {self.max_retries + 1} tentativas")
        finally:
            self.performance_monitor.stop_timer(task_id, "total_processing_time")
            # Opcional: Salvar métricas de performance
            metrics = self.performance_monitor.get_metrics(task_id)
            logger.info(f"Métricas para tarefa {task_id}: {json.dumps(metrics)}")
            self.performance_monitor.clear_metrics(task_id)
    
    def _worker_loop(self) -> None:
        """Loop principal para cada worker."""
        while not self._stop_event.is_set():
            task = None
            try:
                # Obter próxima tarefa da fila
                task = self.queue.get_pending_task()
                
                if task:
                    # Processar a tarefa
                    self._process_single_task(task)
                else:
                    # Fila vazia, esperar um pouco
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Erro inesperado no worker loop: {str(e)}", exc_info=True)
                if task:
                    # Se erro ocorreu após pegar a tarefa, marcar como falha para evitar loop infinito
                    try:
                        self.queue.update_task_status(task[\'id\'], STATUS_FAILED, error_message=f"Erro no worker: {str(e)}")
                    except Exception as db_err:
                        logger.error(f"Erro ao atualizar status da tarefa {task[\'id\']} após erro no worker: {db_err}")
                time.sleep(5) # Esperar mais tempo após erro
    
    def start(self) -> None:
        """Inicia os workers para processar tarefas."""
        if self._workers:
            logger.warning("Workers já estão em execução")
            return
        
        self._stop_event.clear()
        self._workers = []
        for i in range(self.max_workers):
            worker_thread = threading.Thread(target=self._worker_loop, name=f"Worker-{i+1}")
            worker_thread.daemon = True
            worker_thread.start()
            self._workers.append(worker_thread)
        logger.info(f"{self.max_workers} workers iniciados")
    
    def stop(self, wait: bool = True) -> None:
        """Para os workers."""
        if not self._workers:
            logger.warning("Workers não estão em execução")
            return
        
        logger.info("Parando workers...")
        self._stop_event.set()
        
        if wait:
            for worker in self._workers:
                worker.join(timeout=10) # Esperar um pouco para workers terminarem
            logger.info("Workers parados")
        
        self._executor.shutdown(wait=wait)
        self._workers = []
    
    def add_task(self, task_type: str, data: Dict[str, Any], priority: int = 0) -> str:
        """Adiciona uma tarefa à fila."""
        return self.queue.add_task(task_type, data, priority)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtém o status de uma tarefa."""
        return self.queue.get_task_status(task_id)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Obtém estatísticas da fila."""
        return {
            "pending": self.queue.count_tasks(STATUS_PENDING),
            "processing": self.queue.count_tasks(STATUS_PROCESSING),
            "completed": self.queue.count_tasks(STATUS_COMPLETED),
            "failed": self.queue.count_tasks(STATUS_FAILED),
            "total": self.queue.count_tasks()
        }

# --- Exemplo de Handlers --- 
def handle_process_pdf(data: Dict[str, Any], monitor: PerformanceMonitor, task_id: str) -> Dict[str, Any]:
    """Handler de exemplo para processar PDF."""
    pdf_path = data.get("pdf_path")
    if not pdf_path:
        raise ValueError("Caminho do PDF não fornecido")
    
    logger.info(f"[Handler] Processando PDF: {pdf_path}")
    monitor.start_timer(task_id, "pdf_extraction_time")
    
    # Simular processamento
    time.sleep(2)
    
    # Importar extrator real (se disponível)
    try:
        from M1_Extrator_PDF_Otimizado import extrair_dados_pdf_relevantes
        extracted_data = extrair_dados_pdf_relevantes(pdf_path)
    except ImportError:
        logger.warning("Extrator de PDF não encontrado, usando dados simulados.")
        extracted_data = {"numero_intervencao": "SIMULADO_123", "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro real na extração do PDF {pdf_path}: {e}")
        raise # Repassar a exceção para o processador de tarefas
        
    monitor.stop_timer(task_id, "pdf_extraction_time")
    logger.info(f"[Handler] PDF processado: {pdf_path}")
    
    return extracted_data

def handle_submit_form(data: Dict[str, Any], monitor: PerformanceMonitor, task_id: str) -> Dict[str, Any]:
    """Handler de exemplo para submeter formulário."""
    form_data = data.get("form_data")
    if not form_data:
        raise ValueError("Dados do formulário não fornecidos")
    
    logger.info(f"[Handler] Submetendo formulário para WO: {form_data.get(\'numero_wo\')}")
    monitor.start_timer(task_id, "form_submission_time")
    
    # Simular interação com Selenium
    time.sleep(5)
    
    # Importar interação real com portal (se disponível)
    try:
        from selenium_utils import PortalInteraction # Assumindo que existe
        # Código para usar PortalInteraction para submeter o formulário
        # Exemplo: portal.preencher_e_submeter(form_data)
        success = True # Simulado
    except ImportError:
        logger.warning("Utilitários Selenium não encontrados, submissão simulada.")
        success = True # Simulado
    except Exception as e:
        logger.error(f"Erro real na submissão do formulário: {e}")
        raise # Repassar a exceção
        
    monitor.stop_timer(task_id, "form_submission_time")
    
    if success:
        logger.info(f"[Handler] Formulário submetido com sucesso para WO: {form_data.get(\'numero_wo\')}")
        return {"status": "submetido", "wo": form_data.get(\'numero_wo\')}
    else:
        raise RuntimeError("Falha ao submeter formulário no portal")

# --- Exemplo de Uso --- 
if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description=\'Sistema de performance e integração com filas\')
    parser.add_argument(\'--test-add\', type=int, default=0, help=\'Adicionar N tarefas de teste à fila\')
    parser.add_argument(\'--run-workers\', action=\'store_true\', help=\'Iniciar workers para processar a fila\')
    parser.add_argument(\'--clear-failed\', action=\'store_true\', help=\'Limpar tarefas falhadas da fila\')
    parser.add_argument(\'--show-stats\', action=\'store_true\', help=\'Mostrar estatísticas da fila\')
    args = parser.parse_args()
    
    # Criar instância da fila
    persistent_queue = PersistentQueue()
    
    # Definir handlers
    handlers = {
        "process_pdf": handle_process_pdf,
        "submit_form": handle_submit_form
    }
    
    # Criar processador de tarefas
    task_processor = TaskProcessor(persistent_queue, handlers)
    
    # Adicionar tarefas de teste
    if args.test_add > 0:
        print(f"Adicionando {args.test_add} tarefas de teste...")
        for i in range(args.test_add):
            # Adicionar tarefa de PDF
            pdf_task_id = task_processor.add_task(
                task_type="process_pdf", 
                data={"pdf_path": f"/caminho/simulado/doc_{i+1}.pdf"}, 
                priority=1 # Prioridade maior para PDFs
            )
            print(f"  - Tarefa PDF adicionada: {pdf_task_id}")
            
            # Adicionar tarefa de formulário
            form_task_id = task_processor.add_task(
                task_type="submit_form", 
                data={"form_data": {"numero_wo": f"WO_{i+1}", "campo": "valor"}}
            )
            print(f"  - Tarefa Formulário adicionada: {form_task_id}")
        print("Tarefas de teste adicionadas.")
    
    # Mostrar estatísticas
    if args.show_stats:
        stats = task_processor.get_queue_stats()
        print("\nEstatísticas da Fila:")
        print(f"  - Pendentes: {stats[\'pending\']}")
        print(f"  - Processando: {stats[\'processing\']}")
        print(f"  - Concluídas: {stats[\'completed\']}")
        print(f"  - Falhadas: {stats[\'failed\']}")
        print(f"  - Total: {stats[\'total\']}")
    
    # Limpar tarefas falhadas
    if args.clear_failed:
        removed = persistent_queue.clear_queue(status=STATUS_FAILED)
        print(f"\n{removed} tarefas falhadas foram removidas.")
    
    # Iniciar workers
    if args.run_workers:
        print("\nIniciando workers... Pressione Ctrl+C para parar.")
        task_processor.start()
        try:
            # Manter o script principal rodando enquanto os workers processam
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nParando workers...")
            task_processor.stop()
            print("Workers parados.")

    print("\nExecução concluída.")

