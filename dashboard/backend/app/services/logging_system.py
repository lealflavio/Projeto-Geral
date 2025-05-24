import structlog
import logging
import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import threading
import queue
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server

# Configuração do logger estruturado
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

# Configuração do logging padrão
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ]
)

class LogLevel:
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory:
    SYSTEM = "system"
    SECURITY = "security"
    USER = "user"
    NOTIFICATION = "notification"
    AUTOMATION = "automation"
    DATABASE = "database"
    API = "api"
    PERFORMANCE = "performance"

class LogEntry:
    """Classe para representar uma entrada de log."""
    def __init__(self, 
                message: str, 
                level: str = LogLevel.INFO, 
                category: str = LogCategory.SYSTEM,
                user_id: Optional[int] = None,
                request_id: Optional[str] = None,
                extra: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.message = message
        self.level = level
        self.category = category
        self.user_id = user_id
        self.request_id = request_id
        self.extra = extra or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entrada de log para dicionário."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "message": self.message,
            "level": self.level,
            "category": self.category,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "extra": self.extra
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Cria uma entrada de log a partir de um dicionário."""
        entry = cls(
            message=data["message"],
            level=data["level"],
            category=data["category"],
            user_id=data.get("user_id"),
            request_id=data.get("request_id"),
            extra=data.get("extra", {})
        )
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        return entry

class LoggingSystem:
    """Sistema centralizado de logging."""
    
    def __init__(self, max_memory_logs: int = 1000, log_dir: Optional[str] = None):
        self.logger = structlog.get_logger()
        self.memory_logs: List[LogEntry] = []
        self.max_memory_logs = max_memory_logs
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Métricas Prometheus
        self.log_counter = Counter(
            'wondercom_logs_total', 
            'Total de logs gerados', 
            ['level', 'category']
        )
        self.log_processing_time = Histogram(
            'wondercom_log_processing_seconds', 
            'Tempo de processamento de logs',
            ['level', 'category']
        )
        
        # Fila de logs para processamento assíncrono
        self.log_queue = queue.Queue()
        self.log_processor_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        self.log_processor_thread.start()
        
    def _get_log_file_path(self, date: Optional[str] = None) -> str:
        """Retorna o caminho do arquivo de log para uma data específica."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"wondercom-{date}.log")
    
    def _process_log_queue(self):
        """Processa a fila de logs em background."""
        while True:
            try:
                log_entry = self.log_queue.get(block=True, timeout=1)
                
                # Registra métricas
                self.log_counter.labels(
                    level=log_entry.level, 
                    category=log_entry.category
                ).inc()
                
                # Adiciona à memória
                self.memory_logs.append(log_entry)
                if len(self.memory_logs) > self.max_memory_logs:
                    self.memory_logs.pop(0)
                
                # Salva em arquivo
                self._save_log_to_file(log_entry)
                
                # Marca como processado
                self.log_queue.task_done()
                
            except queue.Empty:
                # Timeout da fila, continua o loop
                continue
            except Exception as e:
                print(f"Erro no processamento da fila de logs: {e}")
                time.sleep(1)  # Evita consumo excessivo de CPU em caso de erros
    
    def _save_log_to_file(self, log_entry: LogEntry):
        """Salva uma entrada de log em arquivo."""
        try:
            log_date = datetime.fromisoformat(log_entry.timestamp).strftime("%Y-%m-%d")
            log_file = self._get_log_file_path(log_date)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry.to_dict()) + "\n")
                
        except Exception as e:
            print(f"Erro ao salvar log em arquivo: {e}")
    
    def log(self, 
           message: str, 
           level: str = LogLevel.INFO, 
           category: str = LogCategory.SYSTEM,
           user_id: Optional[int] = None,
           request_id: Optional[str] = None,
           extra: Optional[Dict[str, Any]] = None) -> str:
        """
        Registra uma entrada de log.
        
        Args:
            message: Mensagem de log
            level: Nível de log (debug, info, warning, error, critical)
            category: Categoria de log
            user_id: ID do usuário relacionado (opcional)
            request_id: ID da requisição relacionada (opcional)
            extra: Dados adicionais (opcional)
            
        Returns:
            str: ID da entrada de log
        """
        start_time = time.time()
        
        log_entry = LogEntry(
            message=message,
            level=level,
            category=category,
            user_id=user_id,
            request_id=request_id,
            extra=extra
        )
        
        # Adiciona à fila para processamento assíncrono
        self.log_queue.put(log_entry)
        
        # Registra o tempo de processamento
        processing_time = time.time() - start_time
        self.log_processing_time.labels(
            level=level, 
            category=category
        ).observe(processing_time)
        
        # Também registra no logger estruturado
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(
            message,
            category=category,
            user_id=user_id,
            request_id=request_id,
            **({} if extra is None else extra)
        )
        
        return log_entry.id
    
    def debug(self, message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
        """Registra um log de nível debug."""
        return self.log(message, LogLevel.DEBUG, category, **kwargs)
    
    def info(self, message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
        """Registra um log de nível info."""
        return self.log(message, LogLevel.INFO, category, **kwargs)
    
    def warning(self, message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
        """Registra um log de nível warning."""
        return self.log(message, LogLevel.WARNING, category, **kwargs)
    
    def error(self, message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
        """Registra um log de nível error."""
        return self.log(message, LogLevel.ERROR, category, **kwargs)
    
    def critical(self, message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
        """Registra um log de nível critical."""
        return self.log(message, LogLevel.CRITICAL, category, **kwargs)
    
    def get_logs(self, 
                level: Optional[str] = None, 
                category: Optional[str] = None,
                user_id: Optional[int] = None,
                request_id: Optional[str] = None,
                start_time: Optional[str] = None,
                end_time: Optional[str] = None,
                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém logs com filtros opcionais.
        
        Args:
            level: Filtrar por nível de log
            category: Filtrar por categoria
            user_id: Filtrar por ID de usuário
            request_id: Filtrar por ID de requisição
            start_time: Timestamp inicial (formato ISO)
            end_time: Timestamp final (formato ISO)
            limit: Número máximo de logs a retornar
            
        Returns:
            List[Dict[str, Any]]: Lista de logs filtrados
        """
        filtered = self.memory_logs
        
        if level is not None:
            filtered = [log for log in filtered if log.level == level]
            
        if category is not None:
            filtered = [log for log in filtered if log.category == category]
            
        if user_id is not None:
            filtered = [log for log in filtered if log.user_id == user_id]
            
        if request_id is not None:
            filtered = [log for log in filtered if log.request_id == request_id]
            
        if start_time is not None:
            filtered = [log for log in filtered if log.timestamp >= start_time]
            
        if end_time is not None:
            filtered = [log for log in filtered if log.timestamp <= end_time]
            
        # Ordena por timestamp (mais recentes primeiro)
        filtered = sorted(filtered, key=lambda x: x.timestamp, reverse=True)
        
        # Limita o número de resultados
        filtered = filtered[:limit]
        
        return [log.to_dict() for log in filtered]
    
    def get_logs_from_file(self, 
                          date: Optional[str] = None, 
                          level: Optional[str] = None,
                          category: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém logs de um arquivo específico.
        
        Args:
            date: Data no formato YYYY-MM-DD (padrão: hoje)
            level: Filtrar por nível de log
            category: Filtrar por categoria
            limit: Número máximo de logs a retornar
            
        Returns:
            List[Dict[str, Any]]: Lista de logs filtrados
        """
        log_file = self._get_log_file_path(date)
        
        if not os.path.exists(log_file):
            return []
            
        logs = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        log_entry = LogEntry.from_dict(log_data)
                        
                        # Aplica filtros
                        if level is not None and log_entry.level != level:
                            continue
                            
                        if category is not None and log_entry.category != category:
                            continue
                            
                        logs.append(log_entry.to_dict())
                        
                        if len(logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
            # Ordena por timestamp (mais recentes primeiro)
            logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)
            
            return logs
            
        except Exception as e:
            print(f"Erro ao ler logs do arquivo {log_file}: {e}")
            return []
    
    def start_metrics_server(self, port: int = 8000):
        """Inicia servidor HTTP para métricas Prometheus."""
        try:
            start_http_server(port)
            self.info(f"Servidor de métricas Prometheus iniciado na porta {port}")
        except Exception as e:
            self.error(f"Erro ao iniciar servidor de métricas: {e}")

# Instância singleton do sistema de logging
logging_system = LoggingSystem()

# Funções de conveniência para uso global
def debug(message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
    """Registra um log de nível debug."""
    return logging_system.debug(message, category, **kwargs)

def info(message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
    """Registra um log de nível info."""
    return logging_system.info(message, category, **kwargs)

def warning(message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
    """Registra um log de nível warning."""
    return logging_system.warning(message, category, **kwargs)

def error(message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
    """Registra um log de nível error."""
    return logging_system.error(message, category, **kwargs)

def critical(message: str, category: str = LogCategory.SYSTEM, **kwargs) -> str:
    """Registra um log de nível critical."""
    return logging_system.critical(message, category, **kwargs)

# Inicia o servidor de métricas em uma thread separada
def start_metrics_server(port: int = 8000):
    """Inicia servidor HTTP para métricas Prometheus."""
    thread = threading.Thread(
        target=logging_system.start_metrics_server,
        args=(port,),
        daemon=True
    )
    thread.start()
    return thread
