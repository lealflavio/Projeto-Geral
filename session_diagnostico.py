#!/usr/bin/env python3
"""
Sistema de cache de sessão e diagnóstico para o portal Wondercom.

Este módulo fornece funcionalidades para gerenciamento de sessões
e diagnóstico de problemas durante a interação com o portal Wondercom.
"""

import os
import time
import json
import logging
import shutil
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
from pathlib import Path
import threading
import pickle
import hashlib

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_diagnostico.log'))
    ]
)
logger = logging.getLogger('session_diagnostico')

# Constantes
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
DEFAULT_DIAGNOSTICO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostico")
DEFAULT_SESSION_EXPIRY_HOURS = 8
MAX_CACHE_SIZE_MB = 500  # Tamanho máximo do cache em MB
LOCK_TIMEOUT = 30  # Timeout para locks em segundos


class SessionCache:
    """
    Gerenciador de cache de sessão para o portal Wondercom.
    
    Esta classe fornece funcionalidades para armazenar e recuperar
    sessões de usuário, reduzindo a necessidade de logins frequentes.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de cache de sessão.
        
        Args:
            cache_dir: Diretório para armazenar dados de sessão
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Criar subdiretórios
        self.cookies_dir = os.path.join(self.cache_dir, "cookies")
        self.metadata_dir = os.path.join(self.cache_dir, "metadata")
        os.makedirs(self.cookies_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Lock para operações thread-safe
        self._lock = threading.RLock()
        
        # Inicializar cache
        self._initialize_cache()
    
    def _initialize_cache(self) -> None:
        """Inicializa o cache, limpando sessões expiradas."""
        try:
            with self._lock:
                # Verificar e limpar sessões expiradas
                self._clean_expired_sessions()
                
                # Verificar tamanho do cache
                self._check_cache_size()
                
                logger.info(f"Cache de sessão inicializado em {self.cache_dir}")
        except Exception as e:
            logger.error(f"Erro ao inicializar cache: {str(e)}")
    
    def _get_session_path(self, username: str) -> Tuple[str, str]:
        """
        Obtém caminhos para arquivos de sessão.
        
        Args:
            username: Nome de usuário
            
        Returns:
            Tupla com caminho para cookies e metadata
        """
        # Usar hash para evitar caracteres especiais em nomes de arquivo
        username_hash = hashlib.md5(username.encode()).hexdigest()
        cookies_path = os.path.join(self.cookies_dir, f"{username_hash}.pkl")
        metadata_path = os.path.join(self.metadata_dir, f"{username_hash}.json")
        return cookies_path, metadata_path
    
    def get_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
            
        Returns:
            Dados de sessão ou None se não existir ou estiver expirada
        """
        try:
            with self._lock:
                cookies_path, metadata_path = self._get_session_path(username)
                
                # Verificar se os arquivos existem
                if not os.path.exists(cookies_path) or not os.path.exists(metadata_path):
                    return None
                
                # Carregar metadata
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                
                # Verificar se a sessão expirou
                expiry = metadata.get("expiry", 0)
                if expiry < datetime.now().timestamp():
                    logger.info(f"Sessão expirada para {username}")
                    self.delete_session(username)
                    return None
                
                # Carregar cookies
                with open(cookies_path, "rb") as f:
                    cookies = pickle.load(f)
                
                session = {
                    "cookies": cookies,
                    "expiry": expiry,
                    "created_at": metadata.get("created_at"),
                    "last_used": datetime.now().timestamp()
                }
                
                # Atualizar last_used no metadata
                metadata["last_used"] = session["last_used"]
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f)
                
                logger.info(f"Sessão recuperada para {username}")
                return session
        except Exception as e:
            logger.error(f"Erro ao recuperar sessão para {username}: {str(e)}")
            return None
    
    def save_session(self, username: str, cookies: List[Dict[str, Any]], 
                    expiry_hours: int = DEFAULT_SESSION_EXPIRY_HOURS) -> bool:
        """
        Salva dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
            cookies: Lista de cookies do navegador
            expiry_hours: Horas até a expiração da sessão
            
        Returns:
            True se a sessão foi salva com sucesso, False caso contrário
        """
        try:
            with self._lock:
                cookies_path, metadata_path = self._get_session_path(username)
                
                # Calcular timestamp de expiração
                expiry = datetime.now().timestamp() + (expiry_hours * 3600)
                
                # Salvar cookies
                with open(cookies_path, "wb") as f:
                    pickle.dump(cookies, f)
                
                # Salvar metadata
                metadata = {
                    "username": username,
                    "expiry": expiry,
                    "created_at": datetime.now().timestamp(),
                    "last_used": datetime.now().timestamp()
                }
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f)
                
                logger.info(f"Sessão salva para {username} (expira em {expiry_hours}h)")
                
                # Verificar tamanho do cache após adicionar nova sessão
                self._check_cache_size()
                
                return True
        except Exception as e:
            logger.error(f"Erro ao salvar sessão para {username}: {str(e)}")
            return False
    
    def delete_session(self, username: str) -> bool:
        """
        Remove dados de sessão para um usuário.
        
        Args:
            username: Nome de usuário
            
        Returns:
            True se a sessão foi removida com sucesso, False caso contrário
        """
        try:
            with self._lock:
                cookies_path, metadata_path = self._get_session_path(username)
                
                # Remover arquivos se existirem
                if os.path.exists(cookies_path):
                    os.remove(cookies_path)
                
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                logger.info(f"Sessão removida para {username}")
                return True
        except Exception as e:
            logger.error(f"Erro ao remover sessão para {username}: {str(e)}")
            return False
    
    def _clean_expired_sessions(self) -> int:
        """
        Remove todas as sessões expiradas.
        
        Returns:
            Número de sessões removidas
        """
        try:
            removed = 0
            now = datetime.now().timestamp()
            
            # Listar todos os arquivos de metadata
            for filename in os.listdir(self.metadata_dir):
                if not filename.endswith(".json"):
                    continue
                
                metadata_path = os.path.join(self.metadata_dir, filename)
                
                try:
                    # Carregar metadata
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    # Verificar se a sessão expirou
                    if metadata.get("expiry", 0) < now:
                        # Obter caminho do arquivo de cookies
                        cookies_path = os.path.join(self.cookies_dir, filename.replace(".json", ".pkl"))
                        
                        # Remover arquivos
                        if os.path.exists(cookies_path):
                            os.remove(cookies_path)
                        
                        os.remove(metadata_path)
                        
                        removed += 1
                except Exception as e:
                    logger.warning(f"Erro ao processar {metadata_path}: {str(e)}")
            
            if removed > 0:
                logger.info(f"Removidas {removed} sessões expiradas")
            
            return removed
        except Exception as e:
            logger.error(f"Erro ao limpar sessões expiradas: {str(e)}")
            return 0
    
    def _check_cache_size(self) -> None:
        """
        Verifica o tamanho do cache e remove sessões antigas se necessário.
        """
        try:
            # Calcular tamanho total do cache
            total_size = 0
            for dirpath, _, filenames in os.walk(self.cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            # Converter para MB
            total_size_mb = total_size / (1024 * 1024)
            
            # Se o tamanho exceder o limite, remover sessões antigas
            if total_size_mb > MAX_CACHE_SIZE_MB:
                logger.warning(f"Tamanho do cache ({total_size_mb:.2f} MB) excede o limite ({MAX_CACHE_SIZE_MB} MB)")
                
                # Obter lista de metadados ordenados por último uso
                session_data = []
                for filename in os.listdir(self.metadata_dir):
                    if not filename.endswith(".json"):
                        continue
                    
                    metadata_path = os.path.join(self.metadata_dir, filename)
                    
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                        
                        session_data.append({
                            "filename": filename,
                            "last_used": metadata.get("last_used", 0),
                            "username": metadata.get("username", "unknown")
                        })
                    except Exception as e:
                        logger.warning(f"Erro ao processar {metadata_path}: {str(e)}")
                
                # Ordenar por último uso (mais antigo primeiro)
                session_data.sort(key=lambda x: x["last_used"])
                
                # Remover sessões até que o tamanho esteja abaixo do limite
                removed = 0
                for session in session_data:
                    # Não remover mais de 50% das sessões de uma vez
                    if removed >= len(session_data) / 2:
                        break
                    
                    username = session["username"]
                    self.delete_session(username)
                    removed += 1
                    
                    # Recalcular tamanho
                    total_size = 0
                    for dirpath, _, filenames in os.walk(self.cache_dir):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            total_size += os.path.getsize(fp)
                    
                    total_size_mb = total_size / (1024 * 1024)
                    if total_size_mb <= MAX_CACHE_SIZE_MB * 0.9:  # 90% do limite
                        break
                
                logger.info(f"Removidas {removed} sessões antigas. Novo tamanho: {total_size_mb:.2f} MB")
        except Exception as e:
            logger.error(f"Erro ao verificar tamanho do cache: {str(e)}")
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Obtém informações sobre todas as sessões armazenadas.
        
        Returns:
            Lista de informações de sessão
        """
        try:
            with self._lock:
                sessions = []
                
                # Listar todos os arquivos de metadata
                for filename in os.listdir(self.metadata_dir):
                    if not filename.endswith(".json"):
                        continue
                    
                    metadata_path = os.path.join(self.metadata_dir, filename)
                    
                    try:
                        # Carregar metadata
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                        
                        # Adicionar à lista
                        sessions.append({
                            "username": metadata.get("username", "unknown"),
                            "created_at": metadata.get("created_at", 0),
                            "last_used": metadata.get("last_used", 0),
                            "expiry": metadata.get("expiry", 0),
                            "expired": metadata.get("expiry", 0) < datetime.now().timestamp()
                        })
                    except Exception as e:
                        logger.warning(f"Erro ao processar {metadata_path}: {str(e)}")
                
                return sessions
        except Exception as e:
            logger.error(f"Erro ao listar sessões: {str(e)}")
            return []


class DiagnosticoManager:
    """
    Gerenciador de diagnóstico para o portal Wondercom.
    
    Esta classe fornece funcionalidades para capturar, organizar e
    analisar informações de diagnóstico durante a interação com o portal.
    """
    
    def __init__(self, diagnostico_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de diagnóstico.
        
        Args:
            diagnostico_dir: Diretório para armazenar dados de diagnóstico
        """
        self.diagnostico_dir = diagnostico_dir or DEFAULT_DIAGNOSTICO_DIR
        os.makedirs(self.diagnostico_dir, exist_ok=True)
        
        # Criar subdiretórios
        self.screenshots_dir = os.path.join(self.diagnostico_dir, "screenshots")
        self.logs_dir = os.path.join(self.diagnostico_dir, "logs")
        self.reports_dir = os.path.join(self.diagnostico_dir, "reports")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Inicializar logger específico para diagnóstico
        self._setup_logger()
        
        # Contexto atual
        self.current_context = {
            "session_id": self._generate_session_id(),
            "start_time": datetime.now(),
            "username": None,
            "task_id": None,
            "screenshots": [],
            "events": []
        }
    
    def _setup_logger(self) -> None:
        """Configura logger específico para diagnóstico."""
        self.logger = logging.getLogger('diagnostico')
        self.logger.setLevel(logging.DEBUG)
        
        # Criar arquivo de log para a sessão atual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.logs_dir, f"diagnostico_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info(f"Diagnóstico inicializado em {self.diagnostico_dir}")
    
    def _generate_session_id(self) -> str:
        """
        Gera um ID único para a sessão de diagnóstico.
        
        Returns:
            ID da sessão
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = base64.b32encode(os.urandom(5)).decode('utf-8').lower()
        return f"diag_{timestamp}_{random_suffix}"
    
    def set_context(self, username: Optional[str] = None, 
                   task_id: Optional[str] = None) -> None:
        """
        Define o contexto para a sessão de diagnóstico.
        
        Args:
            username: Nome de usuário
            task_id: ID da tarefa
        """
        if username:
            self.current_context["username"] = username
        
        if task_id:
            self.current_context["task_id"] = task_id
        
        self.logger.info(f"Contexto definido: username={username}, task_id={task_id}")
    
    def save_screenshot(self, screenshot_path: str, 
                       description: str = "") -> Optional[str]:
        """
        Salva uma cópia do screenshot no diretório de diagnóstico.
        
        Args:
            screenshot_path: Caminho para o arquivo de screenshot
            description: Descrição do screenshot
            
        Returns:
            Caminho para o arquivo salvo ou None em caso de erro
        """
        try:
            if not os.path.exists(screenshot_path):
                self.logger.error(f"Screenshot não encontrado: {screenshot_path}")
                return None
            
            # Criar subdiretório para a sessão atual
            session_dir = os.path.join(self.screenshots_dir, self.current_context["session_id"])
            os.makedirs(session_dir, exist_ok=True)
            
            # Obter nome do arquivo original
            filename = os.path.basename(screenshot_path)
            
            # Adicionar timestamp se não houver
            if not any(c.isdigit() for c in filename):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
            
            # Caminho para o novo arquivo
            new_path = os.path.join(session_dir, filename)
            
            # Copiar arquivo
            shutil.copy2(screenshot_path, new_path)
            
            # Registrar no contexto
            screenshot_info = {
                "path": new_path,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            self.current_context["screenshots"].append(screenshot_info)
            
            self.logger.info(f"Screenshot salvo: {new_path}")
            
            # Registrar evento
            self.log_event("screenshot", {
                "path": new_path,
                "description": description
            })
            
            return new_path
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {str(e)}")
            return None
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Registra um evento de diagnóstico.
        
        Args:
            event_type: Tipo de evento
            data: Dados do evento
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.current_context["events"].append(event)
        
        # Registrar no log
        self.logger.info(f"Evento: {event_type} - {json.dumps(data)}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None, 
                 screenshot_path: Optional[str] = None) -> None:
        """
        Registra um erro no diagnóstico.
        
        Args:
            message: Mensagem de erro
            exception: Exceção capturada
            screenshot_path: Caminho para screenshot relacionado ao erro
        """
        error_data = {
            "message": message
        }
        
        if exception:
            error_data["exception"] = str(exception)
            error_data["exception_type"] = type(exception).__name__
        
        if screenshot_path:
            saved_path = self.save_screenshot(screenshot_path, f"Erro: {message}")
            if saved_path:
                error_data["screenshot"] = saved_path
        
        self.log_event("error", error_data)
        self.logger.error(f"Erro: {message}")
        
        if exception:
            self.logger.exception(exception)
    
    def log_warning(self, message: str, screenshot_path: Optional[str] = None) -> None:
        """
        Registra um aviso no diagnóstico.
        
        Args:
            message: Mensagem de aviso
            screenshot_path: Caminho para screenshot relacionado ao aviso
        """
        warning_data = {
            "message": message
        }
        
        if screenshot_path:
            saved_path = self.save_screenshot(screenshot_path, f"Aviso: {message}")
            if saved_path:
                warning_data["screenshot"] = saved_path
        
        self.log_event("warning", warning_data)
        self.logger.warning(f"Aviso: {message}")
    
    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra uma informação no diagnóstico.
        
        Args:
            message: Mensagem informativa
            data: Dados adicionais
        """
        info_data = {
            "message": message
        }
        
        if data:
            info_data.update(data)
        
        self.log_event("info", info_data)
        self.logger.info(message)
    
    def generate_report(self, include_screenshots: bool = True) -> str:
        """
        Gera um relatório HTML com informações de diagnóstico.
        
        Args:
            include_screenshots: Se True, inclui screenshots no relatório
            
        Returns:
            Caminho para o arquivo de relatório
        """
        try:
            # Criar nome de arquivo para o relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = self.current_context.get("username", "unknown")
            task_id = self.current_context.get("task_id", "unknown")
            
            filename = f"report_{username}_{task_id}_{timestamp}.html"
            report_path = os.path.join(self.reports_dir, filename)
            
            # Gerar conteúdo HTML
            html_content = self._generate_html_report(include_screenshots)
            
            # Salvar arquivo
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.logger.info(f"Relatório gerado: {report_path}")
            return report_path
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {str(e)}")
            return ""
    
    def _generate_html_report(self, include_screenshots: bool) -> str:
        """
        Gera o conteúdo HTML do relatório.
        
        Args:
            include_screenshots: Se True, inclui screenshots no relatório
            
        Returns:
            Conteúdo HTML do relatório
        """
        # Informações básicas
        session_id = self.current_context["session_id"]
        start_time = self.current_context["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = self.current_context.get("username", "N/A")
        task_id = self.current_context.get("task_id", "N/A")
        
        # Calcular duração
        duration = datetime.now() - self.current_context["start_time"]
        duration_str = str(duration).split('.')[0]  # Remover microssegundos
        
        # Contar eventos por tipo
        event_counts = {}
        for event in self.current_context["events"]:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Gerar HTML
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Diagnóstico - {session_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background-color: #3498db;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .info-item {{
            padding: 10px;
            background-color: #eee;
            border-radius: 3px;
        }}
        .info-label {{
            font-weight: bold;
            color: #555;
        }}
        .event {{
            margin-bottom: 15px;
            padding: 10px;
            border-left: 4px solid #3498db;
            background-color: #ecf0f1;
        }}
        .event-error {{
            border-left-color: #e74c3c;
        }}
        .event-warning {{
            border-left-color: #f39c12;
        }}
        .event-info {{
            border-left-color: #2ecc71;
        }}
        .event-screenshot {{
            border-left-color: #9b59b6;
        }}
        .event-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }}
        .event-type {{
            font-weight: bold;
        }}
        .event-timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .event-data {{
            margin-top: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            background-color: #f5f5f5;
            padding: 5px;
            border-radius: 3px;
            max-height: 200px;
            overflow-y: auto;
        }}
        .screenshot {{
            margin: 10px 0;
            text-align: center;
        }}
        .screenshot img {{
            max-width: 100%;
            max-height: 500px;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .screenshot-caption {{
            margin-top: 5px;
            font-style: italic;
            color: #555;
        }}
        .summary {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .summary-item {{
            text-align: center;
            padding: 15px;
            background-color: #eee;
            border-radius: 5px;
            margin: 5px;
            min-width: 120px;
        }}
        .summary-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .summary-label {{
            color: #7f8c8d;
        }}
        .error-count {{
            color: #e74c3c;
        }}
        .warning-count {{
            color: #f39c12;
        }}
        .info-count {{
            color: #2ecc71;
        }}
        .screenshot-count {{
            color: #9b59b6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatório de Diagnóstico</h1>
            <p>Sessão: {session_id}</p>
        </div>
        
        <div class="section">
            <h2>Informações Gerais</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Usuário:</div>
                    <div>{username}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Tarefa:</div>
                    <div>{task_id}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Início:</div>
                    <div>{start_time}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Fim:</div>
                    <div>{end_time}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Duração:</div>
                    <div>{duration_str}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">ID da Sessão:</div>
                    <div>{session_id}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Resumo</h2>
            <div class="summary">
                <div class="summary-item">
                    <div class="summary-value">{len(self.current_context["events"])}</div>
                    <div class="summary-label">Total de Eventos</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value error-count">{event_counts.get("error", 0)}</div>
                    <div class="summary-label">Erros</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value warning-count">{event_counts.get("warning", 0)}</div>
                    <div class="summary-label">Avisos</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value info-count">{event_counts.get("info", 0)}</div>
                    <div class="summary-label">Informações</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value screenshot-count">{event_counts.get("screenshot", 0)}</div>
                    <div class="summary-label">Screenshots</div>
                </div>
            </div>
        </div>
"""
        
        # Adicionar screenshots se solicitado
        if include_screenshots and self.current_context["screenshots"]:
            html += """
        <div class="section">
            <h2>Screenshots</h2>
"""
            
            for screenshot in self.current_context["screenshots"]:
                path = screenshot["path"]
                description = screenshot["description"] or "Sem descrição"
                timestamp = datetime.fromisoformat(screenshot["timestamp"]).strftime("%H:%M:%S")
                
                # Usar caminho relativo para o HTML
                rel_path = os.path.relpath(path, self.reports_dir)
                
                html += f"""
            <div class="screenshot">
                <img src="{rel_path}" alt="{description}">
                <div class="screenshot-caption">{description} ({timestamp})</div>
            </div>
"""
            
            html += """
        </div>
"""
        
        # Adicionar eventos
        html += """
        <div class="section">
            <h2>Eventos</h2>
"""
        
        # Ordenar eventos por timestamp
        sorted_events = sorted(
            self.current_context["events"],
            key=lambda e: e["timestamp"]
        )
        
        for event in sorted_events:
            event_type = event["type"]
            timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
            data = event["data"]
            
            # Determinar classe CSS com base no tipo de evento
            event_class = f"event-{event_type}" if event_type in ["error", "warning", "info", "screenshot"] else ""
            
            html += f"""
            <div class="event {event_class}">
                <div class="event-header">
                    <span class="event-type">{event_type.upper()}</span>
                    <span class="event-timestamp">{timestamp}</span>
                </div>
"""
            
            # Adicionar conteúdo específico com base no tipo de evento
            if event_type == "error":
                html += f"""
                <div><strong>Erro:</strong> {data.get('message', 'Erro desconhecido')}</div>
"""
                if "exception" in data:
                    html += f"""
                <div><strong>Exceção:</strong> {data['exception_type']}: {data['exception']}</div>
"""
            elif event_type == "warning":
                html += f"""
                <div><strong>Aviso:</strong> {data.get('message', 'Aviso sem detalhes')}</div>
"""
            elif event_type == "info":
                html += f"""
                <div>{data.get('message', 'Informação sem detalhes')}</div>
"""
            elif event_type == "screenshot":
                html += f"""
                <div><strong>Screenshot:</strong> {data.get('description', 'Sem descrição')}</div>
"""
            
            # Adicionar dados JSON formatados
            html += f"""
                <div class="event-data">{json.dumps(data, indent=2, ensure_ascii=False)}</div>
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        return html


class IntegracaoPortalWondercom:
    """
    Classe para integração com o portal Wondercom.
    
    Esta classe combina as funcionalidades de cache de sessão e diagnóstico
    para fornecer uma interface unificada para interação com o portal.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, 
                diagnostico_dir: Optional[str] = None):
        """
        Inicializa a integração com o portal.
        
        Args:
            cache_dir: Diretório para armazenar dados de sessão
            diagnostico_dir: Diretório para armazenar dados de diagnóstico
        """
        self.session_cache = SessionCache(cache_dir)
        self.diagnostico = DiagnosticoManager(diagnostico_dir)
        
        # Importar utilitários Selenium se disponíveis
        try:
            from selenium_utils import PortalInteraction
            self.portal_interaction = PortalInteraction
            self._has_selenium = True
        except ImportError:
            logger.warning("Utilitários Selenium não encontrados. Funcionalidades de interação com o portal estarão indisponíveis.")
            self._has_selenium = False
    
    def iniciar_sessao(self, username: str, task_id: Optional[str] = None) -> None:
        """
        Inicia uma nova sessão de integração.
        
        Args:
            username: Nome de usuário
            task_id: ID da tarefa
        """
        # Configurar contexto de diagnóstico
        self.diagnostico.set_context(username=username, task_id=task_id)
        
        # Registrar início da sessão
        self.diagnostico.log_info(f"Sessão iniciada para {username}", {
            "username": username,
            "task_id": task_id
        })
    
    def login_portal(self, url: str, username: str, password: str, 
                    username_selector: str, password_selector: str, 
                    submit_selector: str, headless: bool = True) -> bool:
        """
        Realiza login no portal, utilizando cache de sessão quando disponível.
        
        Args:
            url: URL da página de login
            username: Nome de usuário
            password: Senha
            username_selector: Seletor CSS para o campo de usuário
            password_selector: Seletor CSS para o campo de senha
            submit_selector: Seletor CSS para o botão de submit
            headless: Se True, executa o navegador em modo headless
            
        Returns:
            True se o login foi bem-sucedido, False caso contrário
        """
        if not self._has_selenium:
            self.diagnostico.log_error("Utilitários Selenium não disponíveis para login")
            return False
        
        try:
            self.diagnostico.log_info(f"Tentando login para {username}")
            
            with self.portal_interaction(headless=headless) as portal:
                # Configurar diretório de screenshots
                portal.screenshots_dir = os.path.join(self.diagnostico.screenshots_dir, "temp")
                os.makedirs(portal.screenshots_dir, exist_ok=True)
                
                # Tentar login
                success = portal.login(
                    url=url,
                    username=username,
                    password=password,
                    username_selector=username_selector,
                    password_selector=password_selector,
                    submit_selector=submit_selector
                )
                
                # Processar screenshots gerados
                for filename in os.listdir(portal.screenshots_dir):
                    if filename.endswith(".png"):
                        screenshot_path = os.path.join(portal.screenshots_dir, filename)
                        self.diagnostico.save_screenshot(screenshot_path, f"Login: {filename}")
                
                if success:
                    self.diagnostico.log_info(f"Login bem-sucedido para {username}")
                else:
                    self.diagnostico.log_error(f"Falha no login para {username}")
                
                return success
        except Exception as e:
            self.diagnostico.log_error(f"Erro durante login", e)
            return False
    
    def processar_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Processa um arquivo PDF para extrair dados.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dados extraídos ou None em caso de erro
        """
        try:
            self.diagnostico.log_info(f"Processando PDF: {pdf_path}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(pdf_path):
                self.diagnostico.log_error(f"Arquivo PDF não encontrado: {pdf_path}")
                return None
            
            # Importar extrator de PDF
            try:
                from M1_Extrator_PDF_Otimizado import extrair_dados_pdf_relevantes
            except ImportError:
                self.diagnostico.log_error("Extrator de PDF não encontrado")
                return None
            
            # Extrair dados
            dados = extrair_dados_pdf_relevantes(pdf_path)
            
            if dados:
                self.diagnostico.log_info(f"PDF processado com sucesso: {pdf_path}", {
                    "numero_intervencao": dados.get("dados_intervencao", {}).get("numero_intervencao"),
                    "tipo_intervencao": dados.get("dados_intervencao", {}).get("tipo_intervencao")
                })
            else:
                self.diagnostico.log_warning(f"Nenhum dado extraído do PDF: {pdf_path}")
            
            return dados
        except Exception as e:
            self.diagnostico.log_error(f"Erro ao processar PDF", e)
            return None
    
    def gerar_relatorio_diagnostico(self) -> str:
        """
        Gera um relatório de diagnóstico para a sessão atual.
        
        Returns:
            Caminho para o arquivo de relatório
        """
        return self.diagnostico.generate_report()
    
    def limpar_sessoes_expiradas(self) -> int:
        """
        Remove todas as sessões expiradas do cache.
        
        Returns:
            Número de sessões removidas
        """
        return self.session_cache._clean_expired_sessions()


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Sistema de cache de sessão e diagnóstico')
    parser.add_argument('--test', action='store_true', help='Executar teste básico')
    args = parser.parse_args()
    
    if args.test:
        try:
            # Testar cache de sessão
            session_cache = SessionCache()
            session_cache.save_session("teste_usuario", [{"name": "cookie1", "value": "valor1"}])
            session = session_cache.get_session("teste_usuario")
            print(f"Sessão recuperada: {session is not None}")
            
            # Testar diagnóstico
            diagnostico = DiagnosticoManager()
            diagnostico.set_context(username="teste_usuario", task_id="teste_tarefa")
            diagnostico.log_info("Teste de diagnóstico")
            report_path = diagnostico.generate_report()
            print(f"Relatório gerado: {report_path}")
            
            print("Teste concluído com sucesso!")
        except Exception as e:
            print(f"Erro no teste: {str(e)}")
