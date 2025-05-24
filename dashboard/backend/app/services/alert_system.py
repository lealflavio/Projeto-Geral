import os
import json
import time
import threading
import queue
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import requests
import structlog

from ..services.logging_system import logging_system, LogLevel, LogCategory
from ..services.callmebot_service import send_whatsapp_message
from ..services.notification_system import NotificationSystem, NotificationChannel, NotificationPriority

logger = structlog.get_logger()

class AlertCondition:
    """Classe base para condições de alerta."""
    
    def __init__(self, name: str, description: str, severity: str = "warning"):
        """
        Inicializa uma condição de alerta.
        
        Args:
            name: Nome da condição
            description: Descrição da condição
            severity: Severidade do alerta (info, warning, error, critical)
        """
        self.name = name
        self.description = description
        self.severity = severity
        self.last_triggered = None
        self.is_active = False
        self.cooldown_period = 300  # 5 minutos padrão
        
    def check(self, context: Dict[str, Any] = None) -> bool:
        """
        Verifica se a condição foi atendida.
        
        Args:
            context: Contexto para avaliação da condição
            
        Returns:
            bool: True se a condição foi atendida, False caso contrário
        """
        raise NotImplementedError("Método deve ser implementado por subclasses")
    
    def can_trigger(self) -> bool:
        """
        Verifica se o alerta pode ser disparado novamente, respeitando o período de cooldown.
        
        Returns:
            bool: True se o alerta pode ser disparado, False caso contrário
        """
        if self.last_triggered is None:
            return True
            
        now = datetime.now()
        elapsed = (now - self.last_triggered).total_seconds()
        
        return elapsed > self.cooldown_period
    
    def trigger(self) -> None:
        """Marca o alerta como disparado."""
        self.last_triggered = datetime.now()
        self.is_active = True
        
    def resolve(self) -> None:
        """Marca o alerta como resolvido."""
        self.is_active = False
        
    def set_cooldown(self, seconds: int) -> None:
        """Define o período de cooldown em segundos."""
        self.cooldown_period = seconds


class ThresholdAlertCondition(AlertCondition):
    """Condição de alerta baseada em limiar."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        metric_name: str,
        threshold: float,
        comparison: str = "greater_than",
        severity: str = "warning"
    ):
        """
        Inicializa uma condição de alerta baseada em limiar.
        
        Args:
            name: Nome da condição
            description: Descrição da condição
            metric_name: Nome da métrica a ser monitorada
            threshold: Valor limiar para comparação
            comparison: Tipo de comparação (greater_than, less_than, equal_to)
            severity: Severidade do alerta (info, warning, error, critical)
        """
        super().__init__(name, description, severity)
        self.metric_name = metric_name
        self.threshold = threshold
        self.comparison = comparison
        
    def check(self, context: Dict[str, Any] = None) -> bool:
        """
        Verifica se a condição foi atendida.
        
        Args:
            context: Contexto para avaliação da condição, deve conter a métrica
            
        Returns:
            bool: True se a condição foi atendida, False caso contrário
        """
        if context is None or self.metric_name not in context:
            return False
            
        metric_value = context[self.metric_name]
        
        if self.comparison == "greater_than":
            return metric_value > self.threshold
        elif self.comparison == "greater_than_or_equal":
            return metric_value >= self.threshold
        elif self.comparison == "less_than":
            return metric_value < self.threshold
        elif self.comparison == "less_than_or_equal":
            return metric_value <= self.threshold
        elif self.comparison == "equal_to":
            return metric_value == self.threshold
        elif self.comparison == "not_equal_to":
            return metric_value != self.threshold
        else:
            return False


class PatternAlertCondition(AlertCondition):
    """Condição de alerta baseada em padrão de texto."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        log_pattern: str,
        log_level: Optional[str] = None,
        log_category: Optional[str] = None,
        severity: str = "warning"
    ):
        """
        Inicializa uma condição de alerta baseada em padrão de texto.
        
        Args:
            name: Nome da condição
            description: Descrição da condição
            log_pattern: Padrão de texto a ser procurado nos logs
            log_level: Nível de log a ser filtrado (opcional)
            log_category: Categoria de log a ser filtrada (opcional)
            severity: Severidade do alerta (info, warning, error, critical)
        """
        super().__init__(name, description, severity)
        self.log_pattern = log_pattern
        self.log_level = log_level
        self.log_category = log_category
        
    def check(self, context: Dict[str, Any] = None) -> bool:
        """
        Verifica se a condição foi atendida.
        
        Args:
            context: Contexto para avaliação da condição, deve conter a mensagem de log
            
        Returns:
            bool: True se a condição foi atendida, False caso contrário
        """
        if context is None or "log_message" not in context:
            return False
            
        # Verifica se o nível de log corresponde, se especificado
        if self.log_level is not None and context.get("log_level") != self.log_level:
            return False
            
        # Verifica se a categoria de log corresponde, se especificada
        if self.log_category is not None and context.get("log_category") != self.log_category:
            return False
            
        # Verifica se o padrão está presente na mensagem
        return self.log_pattern in context["log_message"]


class CompositeAlertCondition(AlertCondition):
    """Condição de alerta composta por múltiplas condições."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        conditions: List[AlertCondition],
        operator: str = "and",
        severity: str = "warning"
    ):
        """
        Inicializa uma condição de alerta composta.
        
        Args:
            name: Nome da condição
            description: Descrição da condição
            conditions: Lista de condições de alerta
            operator: Operador lógico para combinar condições (and, or)
            severity: Severidade do alerta (info, warning, error, critical)
        """
        super().__init__(name, description, severity)
        self.conditions = conditions
        self.operator = operator
        
    def check(self, context: Dict[str, Any] = None) -> bool:
        """
        Verifica se a condição foi atendida.
        
        Args:
            context: Contexto para avaliação da condição
            
        Returns:
            bool: True se a condição foi atendida, False caso contrário
        """
        if not self.conditions:
            return False
            
        if self.operator == "and":
            return all(condition.check(context) for condition in self.conditions)
        elif self.operator == "or":
            return any(condition.check(context) for condition in self.conditions)
        else:
            return False


class Alert:
    """Classe para representar um alerta."""
    
    def __init__(
        self, 
        condition: AlertCondition,
        actions: List[Callable] = None,
        auto_resolve: bool = False,
        auto_resolve_after: int = 3600  # 1 hora padrão
    ):
        """
        Inicializa um alerta.
        
        Args:
            condition: Condição de alerta
            actions: Lista de ações a serem executadas quando o alerta for disparado
            auto_resolve: Se o alerta deve ser resolvido automaticamente
            auto_resolve_after: Tempo em segundos para resolução automática
        """
        self.id = f"alert-{int(time.time())}-{id(self)}"
        self.condition = condition
        self.actions = actions or []
        self.auto_resolve = auto_resolve
        self.auto_resolve_after = auto_resolve_after
        self.triggered_at = None
        self.resolved_at = None
        self.status = "inactive"  # inactive, active, resolved
        
    def trigger(self, context: Dict[str, Any] = None) -> bool:
        """
        Dispara o alerta se a condição for atendida.
        
        Args:
            context: Contexto para avaliação da condição
            
        Returns:
            bool: True se o alerta foi disparado, False caso contrário
        """
        if self.status == "active":
            return False
            
        if not self.condition.can_trigger():
            return False
            
        if self.condition.check(context):
            self.condition.trigger()
            self.triggered_at = datetime.now()
            self.status = "active"
            
            # Executa as ações associadas
            for action in self.actions:
                try:
                    action(self, context)
                except Exception as e:
                    logger.error(
                        "Erro ao executar ação de alerta",
                        alert_id=self.id,
                        error=str(e),
                        alert_name=self.condition.name
                    )
            
            return True
        
        return False
    
    def resolve(self) -> bool:
        """
        Resolve o alerta.
        
        Returns:
            bool: True se o alerta foi resolvido, False caso contrário
        """
        if self.status != "active":
            return False
            
        self.condition.resolve()
        self.resolved_at = datetime.now()
        self.status = "resolved"
        
        return True
    
    def should_auto_resolve(self) -> bool:
        """
        Verifica se o alerta deve ser resolvido automaticamente.
        
        Returns:
            bool: True se o alerta deve ser resolvido, False caso contrário
        """
        if not self.auto_resolve or self.status != "active" or self.triggered_at is None:
            return False
            
        now = datetime.now()
        elapsed = (now - self.triggered_at).total_seconds()
        
        return elapsed > self.auto_resolve_after
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o alerta para dicionário.
        
        Returns:
            Dict[str, Any]: Representação do alerta como dicionário
        """
        return {
            "id": self.id,
            "name": self.condition.name,
            "description": self.condition.description,
            "severity": self.condition.severity,
            "status": self.status,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """Gerenciador de alertas."""
    
    def __init__(self, notification_system: NotificationSystem = None):
        """
        Inicializa o gerenciador de alertas.
        
        Args:
            notification_system: Sistema de notificações para envio de alertas
        """
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.notification_system = notification_system
        self.check_interval = 60  # 1 minuto padrão
        self.max_history_size = 1000
        self.running = False
        self.check_thread = None
        self.context_providers = []
        
        # Diretório para persistência
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carrega histórico de alertas
        self._load_history()
    
    def register_alert(self, alert: Alert) -> str:
        """
        Registra um alerta no gerenciador.
        
        Args:
            alert: Alerta a ser registrado
            
        Returns:
            str: ID do alerta registrado
        """
        self.alerts[alert.id] = alert
        return alert.id
    
    def unregister_alert(self, alert_id: str) -> bool:
        """
        Remove um alerta do gerenciador.
        
        Args:
            alert_id: ID do alerta a ser removido
            
        Returns:
            bool: True se o alerta foi removido, False caso contrário
        """
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Obtém um alerta pelo ID.
        
        Args:
            alert_id: ID do alerta
            
        Returns:
            Optional[Alert]: Alerta encontrado ou None
        """
        return self.alerts.get(alert_id)
    
    def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém todos os alertas, opcionalmente filtrados por status.
        
        Args:
            status: Status para filtrar alertas (inactive, active, resolved)
            
        Returns:
            List[Dict[str, Any]]: Lista de alertas como dicionários
        """
        result = []
        
        for alert in self.alerts.values():
            if status is None or alert.status == status:
                result.append(alert.to_dict())
                
        return result
    
    def get_alert_history(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de alertas com filtros opcionais.
        
        Args:
            start_time: Timestamp inicial
            end_time: Timestamp final
            severity: Severidade para filtrar
            limit: Número máximo de alertas a retornar
            
        Returns:
            List[Dict[str, Any]]: Lista de alertas históricos
        """
        filtered = self.alert_history
        
        if start_time is not None:
            filtered = [
                a for a in filtered 
                if datetime.fromisoformat(a["triggered_at"]) >= start_time
            ]
            
        if end_time is not None:
            filtered = [
                a for a in filtered 
                if datetime.fromisoformat(a["triggered_at"]) <= end_time
            ]
            
        if severity is not None:
            filtered = [a for a in filtered if a["severity"] == severity]
            
        # Ordena por timestamp (mais recentes primeiro)
        filtered = sorted(
            filtered, 
            key=lambda x: x["triggered_at"], 
            reverse=True
        )
        
        # Limita o número de resultados
        return filtered[:limit]
    
    def register_context_provider(self, provider: Callable[[], Dict[str, Any]]) -> None:
        """
        Registra um provedor de contexto para avaliação de alertas.
        
        Args:
            provider: Função que retorna um dicionário de contexto
        """
        self.context_providers.append(provider)
    
    def _get_context(self) -> Dict[str, Any]:
        """
        Obtém o contexto combinado de todos os provedores.
        
        Returns:
            Dict[str, Any]: Contexto combinado
        """
        context = {}
        
        for provider in self.context_providers:
            try:
                provider_context = provider()
                if isinstance(provider_context, dict):
                    context.update(provider_context)
            except Exception as e:
                logger.error(
                    "Erro ao obter contexto de provedor",
                    error=str(e),
                    provider=str(provider)
                )
                
        return context
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Verifica todos os alertas registrados.
        
        Returns:
            List[Dict[str, Any]]: Lista de alertas disparados
        """
        triggered_alerts = []
        context = self._get_context()
        
        for alert in self.alerts.values():
            # Verifica se o alerta deve ser resolvido automaticamente
            if alert.should_auto_resolve():
                if alert.resolve():
                    logger.info(
                        "Alerta resolvido automaticamente",
                        alert_id=alert.id,
                        alert_name=alert.condition.name
                    )
                    
                    # Adiciona ao histórico
                    alert_dict = alert.to_dict()
                    self.alert_history.append(alert_dict)
                    self._save_history()
                    
            # Verifica se o alerta deve ser disparado
            if alert.trigger(context):
                logger.info(
                    "Alerta disparado",
                    alert_id=alert.id,
                    alert_name=alert.condition.name,
                    severity=alert.condition.severity
                )
                
                # Adiciona ao histórico
                alert_dict = alert.to_dict()
                self.alert_history.append(alert_dict)
                self._trim_history()
                self._save_history()
                
                triggered_alerts.append(alert_dict)
                
        return triggered_alerts
    
    def _check_alerts_loop(self):
        """Loop de verificação de alertas em background."""
        while self.running:
            try:
                self.check_alerts()
            except Exception as e:
                logger.error("Erro ao verificar alertas", error=str(e))
                
            time.sleep(self.check_interval)
    
    def start(self) -> None:
        """Inicia o monitoramento de alertas em background."""
        if self.running:
            return
            
        self.running = True
        self.check_thread = threading.Thread(
            target=self._check_alerts_loop,
            daemon=True
        )
        self.check_thread.start()
        
        logger.info("Monitoramento de alertas iniciado")
    
    def stop(self) -> None:
        """Para o monitoramento de alertas."""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
            self.check_thread = None
            
        logger.info("Monitoramento de alertas parado")
    
    def _save_history(self) -> None:
        """Salva o histórico de alertas em arquivo."""
        history_file = os.path.join(self.data_dir, 'alert_history.json')
        
        try:
            with open(history_file, 'w') as f:
                json.dump(self.alert_history, f)
        except Exception as e:
            logger.error("Erro ao salvar histórico de alertas", error=str(e))
    
    def _load_history(self) -> None:
        """Carrega o histórico de alertas de arquivo."""
        history_file = os.path.join(self.data_dir, 'alert_history.json')
        
        if not os.path.exists(history_file):
            self.alert_history = []
            return
            
        try:
            with open(history_file, 'r') as f:
                self.alert_history = json.load(f)
        except Exception as e:
            logger.error("Erro ao carregar histórico de alertas", error=str(e))
            self.alert_history = []
    
    def _trim_history(self) -> None:
        """Limita o tamanho do histórico de alertas."""
        if len(self.alert_history) > self.max_history_size:
            # Mantém apenas os alertas mais recentes
            self.alert_history = sorted(
                self.alert_history,
                key=lambda x: x["triggered_at"],
                reverse=True
            )[:self.max_history_size]


# Ações de alerta predefinidas

def log_alert_action(alert: Alert, context: Dict[str, Any] = None) -> None:
    """
    Ação para registrar um alerta no sistema de logs.
    
    Args:
        alert: Alerta disparado
        context: Contexto do alerta
    """
    severity_map = {
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR,
        "critical": LogLevel.CRITICAL
    }
    
    log_level = severity_map.get(alert.condition.severity, LogLevel.INFO)
    
    logging_system.log(
        message=f"Alerta: {alert.condition.name} - {alert.condition.description}",
        level=log_level,
        category=LogCategory.AUTOMATION,
        extra={
            "alert_id": alert.id,
            "alert_name": alert.condition.name,
            "alert_severity": alert.condition.severity,
            "context": context
        }
    )


def notification_alert_action(
    alert: Alert, 
    context: Dict[str, Any] = None,
    notification_system: NotificationSystem = None,
    channels: List[str] = None
) -> None:
    """
    Ação para enviar notificação de alerta.
    
    Args:
        alert: Alerta disparado
        context: Contexto do alerta
        notification_system: Sistema de notificações
        channels: Canais para envio da notificação
    """
    if notification_system is None:
        return
        
    severity_map = {
        "info": NotificationPriority.LOW,
        "warning": NotificationPriority.MEDIUM,
        "error": NotificationPriority.HIGH,
        "critical": NotificationPriority.URGENT
    }
    
    priority = severity_map.get(alert.condition.severity, NotificationPriority.MEDIUM)
    
    notification_system.send_notification(
        title=f"Alerta: {alert.condition.name}",
        message=alert.condition.description,
        priority=priority,
        channels=channels or [NotificationChannel.ALL],
        metadata={
            "alert_id": alert.id,
            "alert_severity": alert.condition.severity,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "context": context
        }
    )


def whatsapp_alert_action(
    alert: Alert, 
    context: Dict[str, Any] = None,
    phone_numbers: List[str] = None
) -> None:
    """
    Ação para enviar alerta via WhatsApp.
    
    Args:
        alert: Alerta disparado
        context: Contexto do alerta
        phone_numbers: Lista de números de telefone para envio
    """
    if not phone_numbers:
        return
        
    severity_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "🔴",
        "critical": "🚨"
    }
    
    emoji = severity_emoji.get(alert.condition.severity, "⚠️")
    
    message = (
        f"{emoji} *ALERTA: {alert.condition.name}* {emoji}\n\n"
        f"{alert.condition.description}\n\n"
        f"Severidade: {alert.condition.severity.upper()}\n"
        f"Horário: {alert.triggered_at.strftime('%d/%m/%Y %H:%M:%S') if alert.triggered_at else 'N/A'}"
    )
    
    for phone in phone_numbers:
        try:
            send_whatsapp_message(phone, message)
        except Exception as e:
            logger.error(
                "Erro ao enviar alerta via WhatsApp",
                error=str(e),
                phone=phone,
                alert_id=alert.id
            )


def webhook_alert_action(
    alert: Alert, 
    context: Dict[str, Any] = None,
    webhook_url: str = None,
    headers: Dict[str, str] = None
) -> None:
    """
    Ação para enviar alerta via webhook.
    
    Args:
        alert: Alerta disparado
        context: Contexto do alerta
        webhook_url: URL do webhook
        headers: Cabeçalhos HTTP adicionais
    """
    if not webhook_url:
        return
        
    payload = {
        "alert": alert.to_dict(),
        "context": context
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers or {},
            timeout=10
        )
        
        if response.status_code >= 400:
            logger.error(
                "Erro ao enviar alerta via webhook",
                status_code=response.status_code,
                response=response.text,
                alert_id=alert.id
            )
    except Exception as e:
        logger.error(
            "Erro ao enviar alerta via webhook",
            error=str(e),
            webhook_url=webhook_url,
            alert_id=alert.id
        )


# Provedores de contexto predefinidos

def system_metrics_provider() -> Dict[str, Any]:
    """
    Provedor de métricas do sistema.
    
    Returns:
        Dict[str, Any]: Métricas do sistema
    """
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "system_uptime": time.time() - psutil.boot_time()
    }


def log_metrics_provider() -> Dict[str, Any]:
    """
    Provedor de métricas de logs.
    
    Returns:
        Dict[str, Any]: Métricas de logs
    """
    # Obtém estatísticas de logs dos últimos 15 minutos
    now = datetime.now()
    start_time = (now - timedelta(minutes=15)).isoformat()
    
    logs = logging_system.get_logs(start_time=start_time)
    
    # Conta logs por nível
    log_counts = {}
    error_count = 0
    
    for log in logs:
        level = log.get("level", "unknown")
        log_counts[level] = log_counts.get(level, 0) + 1
        
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            error_count += 1
    
    return {
        "log_count_total": len(logs),
        "log_count_error": error_count,
        "log_count_critical": log_counts.get(LogLevel.CRITICAL, 0),
        "log_count_warning": log_counts.get(LogLevel.WARNING, 0),
        "log_count_info": log_counts.get(LogLevel.INFO, 0),
        "log_count_debug": log_counts.get(LogLevel.DEBUG, 0),
        "log_error_rate": (error_count / len(logs) * 100) if logs else 0
    }


# Alertas predefinidos

def create_high_cpu_alert(threshold: float = 90.0, duration: int = 300) -> Alert:
    """
    Cria um alerta para CPU alta.
    
    Args:
        threshold: Percentual de CPU para disparar o alerta
        duration: Duração em segundos para auto-resolução
        
    Returns:
        Alert: Alerta configurado
    """
    condition = ThresholdAlertCondition(
        name="CPU Alta",
        description=f"Uso de CPU acima de {threshold}%",
        metric_name="cpu_percent",
        threshold=threshold,
        comparison="greater_than",
        severity="warning"
    )
    
    alert = Alert(
        condition=condition,
        actions=[log_alert_action, notification_alert_action],
        auto_resolve=True,
        auto_resolve_after=duration
    )
    
    return alert


def create_high_memory_alert(threshold: float = 90.0, duration: int = 300) -> Alert:
    """
    Cria um alerta para memória alta.
    
    Args:
        threshold: Percentual de memória para disparar o alerta
        duration: Duração em segundos para auto-resolução
        
    Returns:
        Alert: Alerta configurado
    """
    condition = ThresholdAlertCondition(
        name="Memória Alta",
        description=f"Uso de memória acima de {threshold}%",
        metric_name="memory_percent",
        threshold=threshold,
        comparison="greater_than",
        severity="warning"
    )
    
    alert = Alert(
        condition=condition,
        actions=[log_alert_action, notification_alert_action],
        auto_resolve=True,
        auto_resolve_after=duration
    )
    
    return alert


def create_high_disk_alert(threshold: float = 90.0, duration: int = 3600) -> Alert:
    """
    Cria um alerta para disco cheio.
    
    Args:
        threshold: Percentual de disco para disparar o alerta
        duration: Duração em segundos para auto-resolução
        
    Returns:
        Alert: Alerta configurado
    """
    condition = ThresholdAlertCondition(
        name="Disco Cheio",
        description=f"Uso de disco acima de {threshold}%",
        metric_name="disk_percent",
        threshold=threshold,
        comparison="greater_than",
        severity="error"
    )
    
    alert = Alert(
        condition=condition,
        actions=[
            log_alert_action,
            lambda a, c: notification_alert_action(
                a, c, channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP]
            )
        ],
        auto_resolve=True,
        auto_resolve_after=duration
    )
    
    return alert


def create_error_rate_alert(threshold: float = 5.0, duration: int = 1800) -> Alert:
    """
    Cria um alerta para taxa de erros alta.
    
    Args:
        threshold: Percentual de erros para disparar o alerta
        duration: Duração em segundos para auto-resolução
        
    Returns:
        Alert: Alerta configurado
    """
    condition = ThresholdAlertCondition(
        name="Taxa de Erros Alta",
        description=f"Taxa de erros nos logs acima de {threshold}%",
        metric_name="log_error_rate",
        threshold=threshold,
        comparison="greater_than",
        severity="error"
    )
    
    alert = Alert(
        condition=condition,
        actions=[
            log_alert_action,
            lambda a, c: notification_alert_action(
                a, c, channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
            )
        ],
        auto_resolve=True,
        auto_resolve_after=duration
    )
    
    return alert


def create_security_alert(pattern: str = "acesso não autorizado", duration: int = 0) -> Alert:
    """
    Cria um alerta para eventos de segurança.
    
    Args:
        pattern: Padrão de texto para buscar nos logs
        duration: Duração em segundos para auto-resolução (0 = sem auto-resolução)
        
    Returns:
        Alert: Alerta configurado
    """
    condition = PatternAlertCondition(
        name="Alerta de Segurança",
        description=f"Evento de segurança detectado: {pattern}",
        log_pattern=pattern,
        log_category=LogCategory.SECURITY,
        severity="critical"
    )
    
    alert = Alert(
        condition=condition,
        actions=[
            log_alert_action,
            lambda a, c: notification_alert_action(
                a, c, channels=[NotificationChannel.ALL]
            ),
            lambda a, c: whatsapp_alert_action(
                a, c, phone_numbers=["+5511999999999"]  # Número do administrador
            )
        ],
        auto_resolve=(duration > 0),
        auto_resolve_after=duration
    )
    
    return alert


# Inicialização do gerenciador de alertas
alert_manager = AlertManager()

# Registra provedores de contexto
alert_manager.register_context_provider(system_metrics_provider)
alert_manager.register_context_provider(log_metrics_provider)

# Registra alertas predefinidos
alert_manager.register_alert(create_high_cpu_alert())
alert_manager.register_alert(create_high_memory_alert())
alert_manager.register_alert(create_high_disk_alert())
alert_manager.register_alert(create_error_rate_alert())
alert_manager.register_alert(create_security_alert())

# Inicia o monitoramento de alertas
alert_manager.start()
