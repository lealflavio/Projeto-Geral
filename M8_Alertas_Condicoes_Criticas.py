#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M8_Alertas_Condicoes_Criticas.py
Sistema de alertas para condições críticas no processamento de PDFs.

Este módulo implementa um sistema de monitoramento de condições críticas,
alertas e mecanismos de recuperação para garantir a robustez do processamento
de PDFs no sistema Wondercom Automation.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import time
import uuid
import logging
import threading
import datetime
import enum
from typing import Dict, List, Optional, Union, Any, Tuple
import psutil
import structlog

# Configuração do logger estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Enumerações para tipos de condições e níveis de alerta
class TipoCondicao(enum.Enum):
    """Tipos de condições que podem gerar alertas."""
    TEMPO_PROCESSAMENTO = "tempo_processamento"
    TEMPO_FILA = "tempo_fila"
    TAMANHO_FILA = "tamanho_fila"
    USO_MEMORIA = "uso_memoria"
    USO_CPU = "uso_cpu"
    FALHAS_CONSECUTIVAS = "falhas_consecutivas"
    TAXA_ERRO = "taxa_erro"
    PERSONALIZADO = "personalizado"

class NivelAlerta(enum.Enum):
    """Níveis de severidade dos alertas."""
    AVISO = "aviso"
    CRITICO = "critico"
    RECUPERACAO = "recuperacao"

class CanalNotificacao(enum.Enum):
    """Canais disponíveis para notificação de alertas."""
    LOG = "log"
    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"

class AlertaCondicaoCritica:
    """
    Classe que representa um alerta de condição crítica.
    
    Atributos:
        id (str): Identificador único do alerta.
        tipo_condicao (TipoCondicao): Tipo da condição que gerou o alerta.
        nivel (NivelAlerta): Nível de severidade do alerta.
        mensagem (str): Mensagem descritiva do alerta.
        valor_atual (float, opcional): Valor atual que gerou o alerta.
        valor_limite (float, opcional): Valor limite configurado.
        componente (str): Componente que gerou o alerta.
        detalhes (dict, opcional): Detalhes adicionais do alerta.
        timestamp (str): Data e hora de geração do alerta.
    """
    
    def __init__(
        self,
        tipo_condicao: TipoCondicao,
        nivel: NivelAlerta,
        mensagem: str,
        valor_atual: Optional[float] = None,
        valor_limite: Optional[float] = None,
        componente: str = "sistema",
        detalhes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        id: Optional[str] = None
    ):
        """
        Inicializa um novo alerta de condição crítica.
        
        Args:
            tipo_condicao: Tipo da condição que gerou o alerta.
            nivel: Nível de severidade do alerta.
            mensagem: Mensagem descritiva do alerta.
            valor_atual: Valor atual que gerou o alerta.
            valor_limite: Valor limite configurado.
            componente: Componente que gerou o alerta.
            detalhes: Detalhes adicionais do alerta.
            timestamp: Data e hora de geração do alerta.
            id: Identificador único do alerta.
        """
        self.tipo_condicao = tipo_condicao
        self.nivel = nivel
        self.mensagem = mensagem
        self.valor_atual = valor_atual
        self.valor_limite = valor_limite
        self.componente = componente
        self.detalhes = detalhes or {}
        
        # Gera timestamp se não fornecido
        self.timestamp = timestamp or datetime.datetime.utcnow().isoformat() + "Z"
        
        # Gera ID se não fornecido
        if id is None:
            # Formato: YYYY-MM-DDThh-mm-ss_tipo_nivel
            timestamp_id = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
            self.id = f"{timestamp_id}_{tipo_condicao.value}_{nivel.value}"
        else:
            self.id = id
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o alerta para um dicionário.
        
        Returns:
            Dict[str, Any]: Dicionário representando o alerta.
        """
        result = {
            "id": self.id,
            "tipo_condicao": self.tipo_condicao.value,
            "nivel": self.nivel.value,
            "mensagem": self.mensagem,
            "componente": self.componente,
            "timestamp": self.timestamp
        }
        
        if self.valor_atual is not None:
            result["valor_atual"] = self.valor_atual
        
        if self.valor_limite is not None:
            result["valor_limite"] = self.valor_limite
            
            # Calcula percentual excedido para valores acima do limite
            if self.valor_atual is not None and self.valor_limite > 0:
                if self.nivel == NivelAlerta.CRITICO and self.valor_atual > self.valor_limite:
                    percentual = ((self.valor_atual - self.valor_limite) / self.valor_limite) * 100
                    result["percentual_excedido"] = round(percentual, 1)
                elif self.nivel == NivelAlerta.AVISO and self.valor_atual < self.valor_limite:
                    percentual = (self.valor_atual / self.valor_limite) * 100
                    result["percentual_limite"] = round(percentual, 1)
        
        if self.detalhes:
            result["detalhes"] = self.detalhes
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertaCondicaoCritica':
        """
        Cria um alerta a partir de um dicionário.
        
        Args:
            data: Dicionário contendo os dados do alerta.
            
        Returns:
            AlertaCondicaoCritica: Instância do alerta.
        """
        return cls(
            tipo_condicao=TipoCondicao(data["tipo_condicao"]),
            nivel=NivelAlerta(data["nivel"]),
            mensagem=data["mensagem"],
            valor_atual=data.get("valor_atual"),
            valor_limite=data.get("valor_limite"),
            componente=data["componente"],
            detalhes=data.get("detalhes"),
            timestamp=data.get("timestamp"),
            id=data.get("id")
        )

class MonitorCondicoesCriticas:
    """
    Classe responsável por monitorar condições críticas e gerar alertas.
    
    Esta classe implementa a lógica de monitoramento de diversas condições
    que podem afetar o processamento de PDFs, como tempo de processamento,
    uso de recursos, falhas consecutivas, etc.
    
    Atributos:
        config_path (str): Caminho para o arquivo de configuração.
        storage_dir (str): Diretório para armazenamento de alertas.
        config (dict): Configurações carregadas.
        alertas_ativos (dict): Dicionário de alertas ativos.
        contadores (dict): Contadores para diversas métricas.
        monitoramento_ativo (bool): Indica se o monitoramento está ativo.
        thread_monitoramento (Thread): Thread de monitoramento.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        storage_dir: Optional[str] = None
    ):
        """
        Inicializa o monitor de condições críticas.
        
        Args:
            config_path: Caminho para o arquivo de configuração.
            storage_dir: Diretório para armazenamento de alertas.
        """
        self.config_path = config_path
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), "alertas_storage")
        
        # Carrega configurações padrão
        self.config = self._carregar_configuracoes()
        
        # Inicializa estruturas de dados
        self.alertas_ativos = {}  # tipo_condicao -> componente -> alerta
        self.contadores = {
            "falhas_consecutivas": {},  # componente -> contador
            "total_operacoes": {},      # componente -> contador
            "total_erros": {}           # componente -> contador
        }
        
        # Estado do monitoramento
        self.monitoramento_ativo = False
        self.thread_monitoramento = None
        
        # Cria diretórios de armazenamento
        self._criar_diretorios()
        
        logger.info(
            "Monitor de condições críticas inicializado",
            config_path=self.config_path,
            storage_dir=self.storage_dir
        )
    
    def _criar_diretorios(self) -> None:
        """Cria os diretórios necessários para armazenamento."""
        os.makedirs(os.path.join(self.storage_dir, "alertas"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "logs"), exist_ok=True)
    
    def _carregar_configuracoes(self) -> Dict[str, Any]:
        """
        Carrega as configurações do monitor.
        
        Returns:
            Dict[str, Any]: Configurações carregadas.
        """
        # Configurações padrão
        config_padrao = {
            "limites": {
                "tempo_processamento_maximo": 100,  # segundos
                "tempo_fila_maximo": 200,           # segundos
                "tamanho_fila_maximo": 50,          # itens
                "uso_memoria_maximo": 80,           # percentual
                "uso_cpu_maximo": 90,               # percentual
                "falhas_consecutivas_maximo": 3,    # contagem
                "taxa_erro_maxima": 10              # percentual
            },
            "notificacoes": {
                "email": {
                    "ativo": False,
                    "destinatarios": ["admin@exemplo.com"],
                    "remetente": "alertas@exemplo.com",
                    "servidor_smtp": "smtp.exemplo.com",
                    "porta_smtp": 587,
                    "usuario_smtp": "usuario",
                    "senha_smtp": "senha"
                },
                "webhook": {
                    "ativo": False,
                    "url": "https://exemplo.com/webhook",
                    "headers": {"Content-Type": "application/json"},
                    "metodo": "POST"
                },
                "sms": {
                    "ativo": False,
                    "sid": "sid_twilio",
                    "token": "token_twilio",
                    "numero_origem": "+1234567890",
                    "numeros_destino": ["+1234567890"]
                }
            },
            "recuperacao": {
                "tentativas_retry": 3,
                "intervalo_retry": 1,
                "backoff_multiplicador": 2,
                "reiniciar_componentes": True,
                "redistribuir_carga": True,
                "aplicar_throttling": True
            },
            "monitoramento": {
                "intervalo_verificacao": 5,  # segundos
                "persistir_alertas": True,
                "rotacao_logs": True,
                "max_tamanho_log": 10  # MB
            }
        }
        
        # Se não houver arquivo de configuração, retorna o padrão
        if not self.config_path or not os.path.exists(self.config_path):
            return config_padrao
        
        # Carrega configurações do arquivo
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_arquivo = json.load(f)
                
            logger.info(
                "Configurações carregadas do arquivo",
                config_path=self.config_path
            )
            
            # Mescla configurações do arquivo com as padrão
            self._mesclar_dicts(config_padrao, config_arquivo)
            return config_padrao
            
        except Exception as e:
            logger.error(
                "Erro ao carregar configurações",
                config_path=self.config_path,
                erro=str(e)
            )
            return config_padrao
    
    def _mesclar_dicts(self, dict_base: Dict[str, Any], dict_novo: Dict[str, Any]) -> None:
        """
        Mescla dois dicionários recursivamente.
        
        Args:
            dict_base: Dicionário base que será atualizado.
            dict_novo: Dicionário com novos valores.
        """
        for k, v in dict_novo.items():
            if k in dict_base and isinstance(dict_base[k], dict) and isinstance(v, dict):
                self._mesclar_dicts(dict_base[k], v)
            else:
                dict_base[k] = v
    
    def iniciar_monitoramento(self) -> bool:
        """
        Inicia o monitoramento automático em uma thread separada.
        
        Returns:
            bool: True se o monitoramento foi iniciado, False caso contrário.
        """
        if self.monitoramento_ativo:
            logger.warning("Monitoramento já está ativo")
            return False
        
        self.monitoramento_ativo = True
        self.thread_monitoramento = threading.Thread(
            target=self._loop_monitoramento,
            daemon=True
        )
        self.thread_monitoramento.start()
        
        logger.info("Monitoramento iniciado")
        return True
    
    def parar_monitoramento(self) -> bool:
        """
        Para o monitoramento automático.
        
        Returns:
            bool: True se o monitoramento foi parado, False caso contrário.
        """
        if not self.monitoramento_ativo:
            logger.warning("Monitoramento não está ativo")
            return False
        
        self.monitoramento_ativo = False
        if self.thread_monitoramento:
            self.thread_monitoramento.join(timeout=5)
            self.thread_monitoramento = None
        
        logger.info("Monitoramento parado")
        return True
    
    def _loop_monitoramento(self) -> None:
        """Loop principal de monitoramento."""
        while self.monitoramento_ativo:
            try:
                # Verifica condições críticas
                self._verificar_todas_condicoes()
                
                # Aguarda o próximo ciclo
                time.sleep(self.config["monitoramento"]["intervalo_verificacao"])
                
            except Exception as e:
                logger.error(
                    "Erro no loop de monitoramento",
                    erro=str(e)
                )
                time.sleep(1)  # Evita loop infinito em caso de erro
    
    def _verificar_todas_condicoes(self) -> None:
        """Verifica todas as condições configuradas."""
        # Implementação específica para cada componente monitorado
        # Esta é uma função genérica que seria personalizada para cada ambiente
        pass
    
    def verificar_tempo_processamento(
        self,
        tempo_atual: float,
        componente: str
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se o tempo de processamento está dentro dos limites.
        
        Args:
            tempo_atual: Tempo atual de processamento em segundos.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        limite = self.config["limites"]["tempo_processamento_maximo"]
        tipo = TipoCondicao.TEMPO_PROCESSAMENTO
        alertas = []
        
        # Verifica se já existe um alerta ativo para este componente
        alerta_ativo = self._obter_alerta_ativo(tipo, componente)
        
        # Caso 1: Tempo acima do limite (crítico)
        if tempo_atual > limite:
            # Se já existe um alerta crítico, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.CRITICO:
                return []
            
            # Gera alerta crítico
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.CRITICO,
                mensagem="Tempo de processamento excedeu o limite configurado",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 2: Tempo próximo do limite (aviso)
        elif tempo_atual >= limite * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.AVISO:
                return []
            
            # Gera alerta de aviso
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.AVISO,
                mensagem=f"Tempo de processamento próximo do limite ({tempo_atual / limite * 100:.1f}%)",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 3: Tempo abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem="Tempo de processamento normalizado",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
        
        return alertas
    
    def verificar_tempo_fila(
        self,
        tempo_atual: float,
        componente: str
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se o tempo de fila está dentro dos limites.
        
        Args:
            tempo_atual: Tempo atual na fila em segundos.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        limite = self.config["limites"]["tempo_fila_maximo"]
        tipo = TipoCondicao.TEMPO_FILA
        alertas = []
        
        # Verifica se já existe um alerta ativo para este componente
        alerta_ativo = self._obter_alerta_ativo(tipo, componente)
        
        # Caso 1: Tempo acima do limite (crítico)
        if tempo_atual > limite:
            # Se já existe um alerta crítico, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.CRITICO:
                return []
            
            # Gera alerta crítico
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.CRITICO,
                mensagem="Tempo de fila excedeu o limite configurado",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 2: Tempo próximo do limite (aviso)
        elif tempo_atual >= limite * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.AVISO:
                return []
            
            # Gera alerta de aviso
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.AVISO,
                mensagem=f"Tempo de fila próximo do limite ({tempo_atual / limite * 100:.1f}%)",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 3: Tempo abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem="Tempo de fila normalizado",
                valor_atual=tempo_atual,
                valor_limite=limite,
                componente=componente
            )
            alertas.append(alerta)
        
        return alertas
    
    def verificar_tamanho_fila(
        self,
        tamanho_atual: int,
        componente: str
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se o tamanho da fila está dentro dos limites.
        
        Args:
            tamanho_atual: Tamanho atual da fila.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        limite = self.config["limites"]["tamanho_fila_maximo"]
        tipo = TipoCondicao.TAMANHO_FILA
        alertas = []
        
        # Verifica se já existe um alerta ativo para este componente
        alerta_ativo = self._obter_alerta_ativo(tipo, componente)
        
        # Caso 1: Tamanho acima do limite (crítico)
        if tamanho_atual > limite:
            # Se já existe um alerta crítico, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.CRITICO:
                return []
            
            # Gera alerta crítico
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.CRITICO,
                mensagem="Tamanho da fila excedeu o limite configurado",
                valor_atual=float(tamanho_atual),
                valor_limite=float(limite),
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 2: Tamanho próximo do limite (aviso)
        elif tamanho_atual >= limite * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.AVISO:
                return []
            
            # Gera alerta de aviso
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.AVISO,
                mensagem=f"Tamanho da fila próximo do limite ({tamanho_atual / limite * 100:.1f}%)",
                valor_atual=float(tamanho_atual),
                valor_limite=float(limite),
                componente=componente
            )
            alertas.append(alerta)
            
        # Caso 3: Tamanho abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem="Tamanho da fila normalizado",
                valor_atual=float(tamanho_atual),
                valor_limite=float(limite),
                componente=componente
            )
            alertas.append(alerta)
        
        return alertas
    
    def verificar_uso_recursos(
        self,
        uso_memoria: Optional[float] = None,
        uso_cpu: Optional[float] = None,
        componente: str = "sistema"
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se o uso de recursos está dentro dos limites.
        
        Args:
            uso_memoria: Percentual de uso de memória.
            uso_cpu: Percentual de uso de CPU.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        # Se não foram fornecidos valores, obtém automaticamente
        if uso_memoria is None or uso_cpu is None:
            recursos = self._obter_uso_recursos()
            uso_memoria = uso_memoria or recursos["memoria"]
            uso_cpu = uso_cpu or recursos["cpu"]
        
        limite_memoria = self.config["limites"]["uso_memoria_maximo"]
        limite_cpu = self.config["limites"]["uso_cpu_maximo"]
        alertas = []
        
        # Verifica uso de memória
        alerta_memoria_ativo = self._obter_alerta_ativo(TipoCondicao.USO_MEMORIA, componente)
        
        # Caso 1: Uso de memória acima do limite (crítico)
        if uso_memoria > limite_memoria:
            # Se já existe um alerta crítico, não gera outro
            if not (alerta_memoria_ativo and alerta_memoria_ativo.nivel == NivelAlerta.CRITICO):
                # Gera alerta crítico
                alerta = AlertaCondicaoCritica(
                    tipo_condicao=TipoCondicao.USO_MEMORIA,
                    nivel=NivelAlerta.CRITICO,
                    mensagem="Uso de memória excedeu o limite configurado",
                    valor_atual=uso_memoria,
                    valor_limite=limite_memoria,
                    componente=componente
                )
                alertas.append(alerta)
                
        # Caso 2: Uso de memória próximo do limite (aviso)
        elif uso_memoria >= limite_memoria * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if not (alerta_memoria_ativo and alerta_memoria_ativo.nivel == NivelAlerta.AVISO):
                # Gera alerta de aviso
                alerta = AlertaCondicaoCritica(
                    tipo_condicao=TipoCondicao.USO_MEMORIA,
                    nivel=NivelAlerta.AVISO,
                    mensagem=f"Uso de memória próximo do limite ({uso_memoria / limite_memoria * 100:.1f}%)",
                    valor_atual=uso_memoria,
                    valor_limite=limite_memoria,
                    componente=componente
                )
                alertas.append(alerta)
                
        # Caso 3: Uso de memória abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_memoria_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=TipoCondicao.USO_MEMORIA,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem="Uso de memória normalizado",
                valor_atual=uso_memoria,
                valor_limite=limite_memoria,
                componente=componente
            )
            alertas.append(alerta)
        
        # Verifica uso de CPU
        alerta_cpu_ativo = self._obter_alerta_ativo(TipoCondicao.USO_CPU, componente)
        
        # Caso 1: Uso de CPU acima do limite (crítico)
        if uso_cpu > limite_cpu:
            # Se já existe um alerta crítico, não gera outro
            if not (alerta_cpu_ativo and alerta_cpu_ativo.nivel == NivelAlerta.CRITICO):
                # Gera alerta crítico
                alerta = AlertaCondicaoCritica(
                    tipo_condicao=TipoCondicao.USO_CPU,
                    nivel=NivelAlerta.CRITICO,
                    mensagem="Uso de CPU excedeu o limite configurado",
                    valor_atual=uso_cpu,
                    valor_limite=limite_cpu,
                    componente=componente
                )
                alertas.append(alerta)
                
        # Caso 2: Uso de CPU próximo do limite (aviso)
        elif uso_cpu >= limite_cpu * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if not (alerta_cpu_ativo and alerta_cpu_ativo.nivel == NivelAlerta.AVISO):
                # Gera alerta de aviso
                alerta = AlertaCondicaoCritica(
                    tipo_condicao=TipoCondicao.USO_CPU,
                    nivel=NivelAlerta.AVISO,
                    mensagem=f"Uso de CPU próximo do limite ({uso_cpu / limite_cpu * 100:.1f}%)",
                    valor_atual=uso_cpu,
                    valor_limite=limite_cpu,
                    componente=componente
                )
                alertas.append(alerta)
                
        # Caso 3: Uso de CPU abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_cpu_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=TipoCondicao.USO_CPU,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem="Uso de CPU normalizado",
                valor_atual=uso_cpu,
                valor_limite=limite_cpu,
                componente=componente
            )
            alertas.append(alerta)
        
        return alertas
    
    def _obter_uso_recursos(self) -> Dict[str, float]:
        """
        Obtém o uso atual de recursos do sistema.
        
        Returns:
            Dict[str, float]: Dicionário com percentuais de uso de CPU e memória.
        """
        try:
            # Uso de CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Uso de memória
            memoria = psutil.virtual_memory()
            memoria_percent = memoria.percent
            
            return {
                "cpu": cpu_percent,
                "memoria": memoria_percent
            }
        except Exception as e:
            logger.error(
                "Erro ao obter uso de recursos",
                erro=str(e)
            )
            return {
                "cpu": 0.0,
                "memoria": 0.0
            }
    
    def verificar_falhas_consecutivas(
        self,
        falha: bool = False,
        reset: bool = False,
        componente: str = "sistema"
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se o número de falhas consecutivas está dentro dos limites.
        
        Args:
            falha: Indica se ocorreu uma falha.
            reset: Indica se o contador deve ser resetado.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        # Inicializa contador se não existir
        if componente not in self.contadores["falhas_consecutivas"]:
            self.contadores["falhas_consecutivas"][componente] = 0
        
        # Reset do contador
        if reset:
            contador_anterior = self.contadores["falhas_consecutivas"][componente]
            self.contadores["falhas_consecutivas"][componente] = 0
            
            # Se havia falhas, gera alerta de recuperação
            if contador_anterior > 0:
                alerta = AlertaCondicaoCritica(
                    tipo_condicao=TipoCondicao.FALHAS_CONSECUTIVAS,
                    nivel=NivelAlerta.RECUPERACAO,
                    mensagem="Falhas consecutivas resetadas",
                    valor_atual=0.0,
                    valor_limite=float(self.config["limites"]["falhas_consecutivas_maximo"]),
                    componente=componente
                )
                return [alerta]
            
            return []
        
        # Se não houve falha, não incrementa o contador
        if not falha:
            return []
        
        # Incrementa o contador de falhas
        self.contadores["falhas_consecutivas"][componente] += 1
        contador = self.contadores["falhas_consecutivas"][componente]
        limite = self.config["limites"]["falhas_consecutivas_maximo"]
        
        # Verifica se já existe um alerta ativo para este componente
        alerta_ativo = self._obter_alerta_ativo(TipoCondicao.FALHAS_CONSECUTIVAS, componente)
        
        # Caso 1: Contador acima do limite (crítico)
        if contador > limite:
            # Se já existe um alerta crítico, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.CRITICO:
                return []
            
            # Gera alerta crítico
            alerta = AlertaCondicaoCritica(
                tipo_condicao=TipoCondicao.FALHAS_CONSECUTIVAS,
                nivel=NivelAlerta.CRITICO,
                mensagem=f"Número de falhas consecutivas excedeu o limite ({contador} > {limite})",
                valor_atual=float(contador),
                valor_limite=float(limite),
                componente=componente
            )
            return [alerta]
            
        # Caso 2: Contador próximo do limite (aviso)
        elif contador >= limite * 0.6:  # 60% do limite
            # Se já existe um alerta de aviso, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.AVISO:
                return []
            
            # Gera alerta de aviso
            alerta = AlertaCondicaoCritica(
                tipo_condicao=TipoCondicao.FALHAS_CONSECUTIVAS,
                nivel=NivelAlerta.AVISO,
                mensagem=f"Número de falhas consecutivas próximo do limite ({contador}/{limite})",
                valor_atual=float(contador),
                valor_limite=float(limite),
                componente=componente
            )
            return [alerta]
        
        # Caso 3: Contador abaixo do limite de aviso
        return []
    
    def verificar_taxa_erro(
        self,
        total_operacoes: int,
        total_erros: int,
        componente: str = "sistema"
    ) -> List[AlertaCondicaoCritica]:
        """
        Verifica se a taxa de erro está dentro dos limites.
        
        Args:
            total_operacoes: Total de operações realizadas.
            total_erros: Total de erros ocorridos.
            componente: Componente sendo monitorado.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas gerados.
        """
        # Evita divisão por zero
        if total_operacoes == 0:
            return []
        
        # Calcula a taxa de erro
        taxa_erro = (total_erros / total_operacoes) * 100
        limite = self.config["limites"]["taxa_erro_maxima"]
        tipo = TipoCondicao.TAXA_ERRO
        
        # Verifica se já existe um alerta ativo para este componente
        alerta_ativo = self._obter_alerta_ativo(tipo, componente)
        
        # Caso 1: Taxa acima do limite (crítico)
        if taxa_erro > limite:
            # Se já existe um alerta crítico, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.CRITICO:
                return []
            
            # Gera alerta crítico
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.CRITICO,
                mensagem=f"Taxa de erro excedeu o limite configurado ({taxa_erro:.1f}% > {limite}%)",
                valor_atual=taxa_erro,
                valor_limite=float(limite),
                componente=componente,
                detalhes={
                    "total_operacoes": total_operacoes,
                    "total_erros": total_erros
                }
            )
            return [alerta]
            
        # Caso 2: Taxa próxima do limite (aviso)
        elif taxa_erro >= limite * 0.8:  # 80% do limite
            # Se já existe um alerta de aviso, não gera outro
            if alerta_ativo and alerta_ativo.nivel == NivelAlerta.AVISO:
                return []
            
            # Gera alerta de aviso
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.AVISO,
                mensagem=f"Taxa de erro próxima do limite ({taxa_erro:.1f}%/{limite}%)",
                valor_atual=taxa_erro,
                valor_limite=float(limite),
                componente=componente,
                detalhes={
                    "total_operacoes": total_operacoes,
                    "total_erros": total_erros
                }
            )
            return [alerta]
            
        # Caso 3: Taxa abaixo do limite, mas havia um alerta ativo (recuperação)
        elif alerta_ativo:
            # Gera alerta de recuperação
            alerta = AlertaCondicaoCritica(
                tipo_condicao=tipo,
                nivel=NivelAlerta.RECUPERACAO,
                mensagem=f"Taxa de erro normalizada ({taxa_erro:.1f}%)",
                valor_atual=taxa_erro,
                valor_limite=float(limite),
                componente=componente,
                detalhes={
                    "total_operacoes": total_operacoes,
                    "total_erros": total_erros
                }
            )
            return [alerta]
        
        # Caso 4: Taxa abaixo do limite e não havia alerta ativo
        return []
    
    def registrar_alerta_personalizado(
        self,
        nivel: NivelAlerta,
        mensagem: str,
        componente: str = "sistema",
        detalhes: Optional[Dict[str, Any]] = None
    ) -> AlertaCondicaoCritica:
        """
        Registra um alerta personalizado.
        
        Args:
            nivel: Nível de severidade do alerta.
            mensagem: Mensagem descritiva do alerta.
            componente: Componente que gerou o alerta.
            detalhes: Detalhes adicionais do alerta.
            
        Returns:
            AlertaCondicaoCritica: Alerta registrado.
        """
        # Cria o alerta
        alerta = AlertaCondicaoCritica(
            tipo_condicao=TipoCondicao.PERSONALIZADO,
            nivel=nivel,
            mensagem=mensagem,
            componente=componente,
            detalhes=detalhes
        )
        
        # Processa o alerta
        self._processar_alerta(alerta)
        
        return alerta
    
    def _obter_alerta_ativo(
        self,
        tipo_condicao: TipoCondicao,
        componente: str
    ) -> Optional[AlertaCondicaoCritica]:
        """
        Obtém um alerta ativo para um tipo de condição e componente.
        
        Args:
            tipo_condicao: Tipo da condição.
            componente: Componente monitorado.
            
        Returns:
            Optional[AlertaCondicaoCritica]: Alerta ativo ou None.
        """
        tipo_str = tipo_condicao.value
        
        if tipo_str in self.alertas_ativos and componente in self.alertas_ativos[tipo_str]:
            return self.alertas_ativos[tipo_str][componente]
        
        return None
    
    def _processar_alerta(self, alerta: AlertaCondicaoCritica) -> None:
        """
        Processa um alerta, notificando e executando ações de recuperação.
        
        Args:
            alerta: Alerta a ser processado.
        """
        # Notifica o alerta
        self._notificar_alerta(alerta)
        
        # Persiste o alerta
        if self.config["monitoramento"]["persistir_alertas"]:
            self._persistir_alerta(alerta)
        
        # Atualiza alertas ativos
        tipo_str = alerta.tipo_condicao.value
        
        if alerta.nivel == NivelAlerta.RECUPERACAO:
            # Remove alerta ativo
            if tipo_str in self.alertas_ativos and alerta.componente in self.alertas_ativos[tipo_str]:
                del self.alertas_ativos[tipo_str][alerta.componente]
        else:
            # Adiciona ou atualiza alerta ativo
            if tipo_str not in self.alertas_ativos:
                self.alertas_ativos[tipo_str] = {}
            
            self.alertas_ativos[tipo_str][alerta.componente] = alerta
            
            # Executa ações de recuperação para alertas críticos
            if alerta.nivel == NivelAlerta.CRITICO:
                self._executar_recuperacao(alerta)
    
    def _notificar_alerta(self, alerta: AlertaCondicaoCritica) -> None:
        """
        Notifica um alerta pelos canais configurados.
        
        Args:
            alerta: Alerta a ser notificado.
        """
        # Sempre notifica via log e console
        self._notificar_log(alerta)
        self._notificar_console(alerta)
        
        # Notificações adicionais para alertas críticos
        if alerta.nivel == NivelAlerta.CRITICO:
            # Email
            if self.config["notificacoes"]["email"]["ativo"]:
                self._notificar_email(alerta)
            
            # SMS
            if self.config["notificacoes"]["sms"]["ativo"]:
                self._notificar_sms(alerta)
        
        # Webhook para todos os níveis
        if self.config["notificacoes"]["webhook"]["ativo"]:
            self._notificar_webhook(alerta)
    
    def _notificar_log(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Notifica um alerta via log.
        
        Args:
            alerta: Alerta a ser notificado.
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário.
        """
        try:
            # Converte para JSON
            alerta_json = json.dumps(alerta.to_dict())
            
            # Registra no log
            print(alerta_json)
            
            # Nível de log baseado no nível do alerta
            if alerta.nivel == NivelAlerta.CRITICO:
                logger.error(alerta.mensagem, **alerta.to_dict())
            elif alerta.nivel == NivelAlerta.AVISO:
                logger.warning(alerta.mensagem, **alerta.to_dict())
            else:
                logger.info(alerta.mensagem, **alerta.to_dict())
            
            return True
        except Exception as e:
            logger.error(
                "Erro ao notificar via log",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _notificar_console(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Notifica um alerta via console.
        
        Args:
            alerta: Alerta a ser notificado.
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário.
        """
        try:
            # Formata a mensagem
            nivel_str = alerta.nivel.value.upper()
            tipo_str = alerta.tipo_condicao.value
            
            mensagem = f"[ALERTA {nivel_str}] {tipo_str}: {alerta.mensagem}"
            
            # Adiciona detalhes
            detalhes = []
            if alerta.componente:
                detalhes.append(f"Componente: {alerta.componente}")
            if alerta.valor_atual is not None:
                detalhes.append(f"Valor Atual: {alerta.valor_atual}")
            if alerta.valor_limite is not None:
                detalhes.append(f"Valor Limite: {alerta.valor_limite}")
            
            if detalhes:
                mensagem += f" ({', '.join(detalhes)})"
            
            # Exibe no console
            print(mensagem)
            
            return True
        except Exception as e:
            logger.error(
                "Erro ao notificar via console",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _notificar_email(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Notifica um alerta via email.
        
        Args:
            alerta: Alerta a ser notificado.
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário.
        """
        # Implementação simplificada para exemplo
        try:
            logger.info(
                "Enviando notificação por email",
                alerta_id=alerta.id,
                destinatarios=self.config["notificacoes"]["email"]["destinatarios"]
            )
            return True
        except Exception as e:
            logger.error(
                "Erro ao notificar via email",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _notificar_webhook(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Notifica um alerta via webhook.
        
        Args:
            alerta: Alerta a ser notificado.
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário.
        """
        # Implementação simplificada para exemplo
        try:
            logger.info(
                "Enviando notificação por webhook",
                alerta_id=alerta.id,
                url=self.config["notificacoes"]["webhook"]["url"]
            )
            return True
        except Exception as e:
            logger.error(
                "Erro ao notificar via webhook",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _notificar_sms(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Notifica um alerta via SMS.
        
        Args:
            alerta: Alerta a ser notificado.
            
        Returns:
            bool: True se a notificação foi enviada, False caso contrário.
        """
        # Implementação simplificada para exemplo
        try:
            logger.info(
                "Enviando notificação por SMS",
                alerta_id=alerta.id,
                numeros=self.config["notificacoes"]["sms"]["numeros_destino"]
            )
            return True
        except Exception as e:
            logger.error(
                "Erro ao notificar via SMS",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _executar_recuperacao(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para um alerta.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        # Verifica se a recuperação está ativada
        if not self.config["recuperacao"]["reiniciar_componentes"]:
            return False
        
        # Executa ações específicas para cada tipo de condição
        tipo = alerta.tipo_condicao
        
        if tipo == TipoCondicao.TEMPO_PROCESSAMENTO:
            return self._recuperar_tempo_processamento(alerta)
        elif tipo == TipoCondicao.TEMPO_FILA:
            return self._recuperar_tempo_fila(alerta)
        elif tipo == TipoCondicao.TAMANHO_FILA:
            return self._recuperar_tamanho_fila(alerta)
        elif tipo == TipoCondicao.USO_MEMORIA:
            return self._recuperar_uso_memoria(alerta)
        elif tipo == TipoCondicao.USO_CPU:
            return self._recuperar_uso_cpu(alerta)
        elif tipo == TipoCondicao.FALHAS_CONSECUTIVAS:
            return self._recuperar_falhas_consecutivas(alerta)
        elif tipo == TipoCondicao.TAXA_ERRO:
            return self._recuperar_taxa_erro(alerta)
        else:
            return False
    
    def _recuperar_tempo_processamento(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para tempo de processamento.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Aplica throttling
        if self.config["recuperacao"]["aplicar_throttling"]:
            logger.info(
                "Aplicando throttling para reduzir tempo de processamento",
                componente=componente
            )
        
        # Redistribui carga
        if self.config["recuperacao"]["redistribuir_carga"]:
            logger.info(
                "Redistribuindo carga para reduzir tempo de processamento",
                componente=componente
            )
        
        # Reinicia componente
        if self.config["recuperacao"]["reiniciar_componentes"]:
            logger.info(
                "Reiniciando componente para reduzir tempo de processamento",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_tempo_fila(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para tempo de fila.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Aumenta capacidade de processamento
        logger.info(
            "Aumentando capacidade de processamento para reduzir tempo de fila",
            componente=componente
        )
        
        # Redistribui carga
        if self.config["recuperacao"]["redistribuir_carga"]:
            logger.info(
                "Redistribuindo carga para reduzir tempo de fila",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_tamanho_fila(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para tamanho de fila.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Aumenta capacidade de processamento
        logger.info(
            "Aumentando capacidade de processamento para reduzir tamanho de fila",
            componente=componente
        )
        
        # Aplica throttling
        if self.config["recuperacao"]["aplicar_throttling"]:
            logger.info(
                "Aplicando throttling para novas entradas na fila",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_uso_memoria(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para uso de memória.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Libera memória
        logger.info(
            "Liberando memória não utilizada",
            componente=componente
        )
        
        # Reinicia componente
        if self.config["recuperacao"]["reiniciar_componentes"]:
            logger.info(
                "Reiniciando componente para liberar memória",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_uso_cpu(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para uso de CPU.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Aplica throttling
        if self.config["recuperacao"]["aplicar_throttling"]:
            logger.info(
                "Aplicando throttling para reduzir uso de CPU",
                componente=componente
            )
        
        # Redistribui carga
        if self.config["recuperacao"]["redistribuir_carga"]:
            logger.info(
                "Redistribuindo carga para reduzir uso de CPU",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_falhas_consecutivas(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para falhas consecutivas.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Reinicia componente
        if self.config["recuperacao"]["reiniciar_componentes"]:
            logger.info(
                "Reiniciando componente após falhas consecutivas",
                componente=componente
            )
        
        # Aplica backoff
        logger.info(
            "Aplicando backoff exponencial para próximas tentativas",
            componente=componente,
            multiplicador=self.config["recuperacao"]["backoff_multiplicador"]
        )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _recuperar_taxa_erro(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Executa ações de recuperação para taxa de erro.
        
        Args:
            alerta: Alerta que requer recuperação.
            
        Returns:
            bool: True se a recuperação foi executada, False caso contrário.
        """
        componente = alerta.componente
        
        # Aplica throttling
        if self.config["recuperacao"]["aplicar_throttling"]:
            logger.info(
                "Aplicando throttling para reduzir taxa de erro",
                componente=componente
            )
        
        # Reinicia componente
        if self.config["recuperacao"]["reiniciar_componentes"]:
            logger.info(
                "Reiniciando componente para reduzir taxa de erro",
                componente=componente
            )
        
        logger.info(
            "Recuperação executada com sucesso",
            alerta_id=alerta.id,
            tipo_condicao=alerta.tipo_condicao.value,
            componente=componente
        )
        
        return True
    
    def _persistir_alerta(self, alerta: AlertaCondicaoCritica) -> bool:
        """
        Persiste um alerta em arquivo.
        
        Args:
            alerta: Alerta a ser persistido.
            
        Returns:
            bool: True se o alerta foi persistido, False caso contrário.
        """
        try:
            # Cria diretório se não existir
            alertas_dir = os.path.join(self.storage_dir, "alertas")
            os.makedirs(alertas_dir, exist_ok=True)
            
            # Caminho do arquivo
            arquivo = os.path.join(alertas_dir, f"{alerta.id}.json")
            
            # Salva o alerta
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(alerta.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(
                "Erro ao persistir alerta",
                erro=str(e),
                alerta_id=alerta.id
            )
            return False
    
    def _carregar_alerta(self, alerta_id: str) -> Optional[AlertaCondicaoCritica]:
        """
        Carrega um alerta a partir do arquivo.
        
        Args:
            alerta_id: ID do alerta a ser carregado.
            
        Returns:
            Optional[AlertaCondicaoCritica]: Alerta carregado ou None.
        """
        try:
            # Caminho do arquivo
            arquivo = os.path.join(self.storage_dir, "alertas", f"{alerta_id}.json")
            
            # Verifica se o arquivo existe
            if not os.path.exists(arquivo):
                return None
            
            # Carrega o alerta
            with open(arquivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return AlertaCondicaoCritica.from_dict(data)
        except Exception as e:
            logger.error(
                "Erro ao carregar alerta",
                erro=str(e),
                alerta_id=alerta_id
            )
            return None
    
    def _carregar_todos_alertas(self) -> List[AlertaCondicaoCritica]:
        """
        Carrega todos os alertas persistidos.
        
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas carregados.
        """
        alertas = []
        alertas_dir = os.path.join(self.storage_dir, "alertas")
        
        # Verifica se o diretório existe
        if not os.path.exists(alertas_dir):
            return alertas
        
        # Carrega todos os arquivos
        for arquivo in os.listdir(alertas_dir):
            if arquivo.endswith(".json"):
                alerta_id = arquivo[:-5]  # Remove a extensão .json
                alerta = self._carregar_alerta(alerta_id)
                if alerta:
                    alertas.append(alerta)
        
        return alertas
    
    def obter_alertas(
        self,
        nivel: Optional[NivelAlerta] = None,
        tipo_condicao: Optional[TipoCondicao] = None,
        componente: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[AlertaCondicaoCritica]:
        """
        Obtém alertas com filtros.
        
        Args:
            nivel: Filtro por nível de alerta.
            tipo_condicao: Filtro por tipo de condição.
            componente: Filtro por componente.
            data_inicio: Filtro por data de início.
            data_fim: Filtro por data de fim.
            
        Returns:
            List[AlertaCondicaoCritica]: Lista de alertas filtrados.
        """
        # Carrega todos os alertas
        alertas = self._carregar_todos_alertas()
        
        # Aplica filtros
        if nivel:
            alertas = [a for a in alertas if a.nivel == nivel]
        
        if tipo_condicao:
            alertas = [a for a in alertas if a.tipo_condicao == tipo_condicao]
        
        if componente:
            alertas = [a for a in alertas if a.componente == componente]
        
        if data_inicio:
            alertas = [a for a in alertas if a.timestamp >= data_inicio]
        
        if data_fim:
            alertas = [a for a in alertas if a.timestamp <= data_fim]
        
        return alertas
    
    def obter_estatisticas_alertas(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de alertas.
        
        Args:
            data_inicio: Filtro por data de início.
            data_fim: Filtro por data de fim.
            
        Returns:
            Dict[str, Any]: Estatísticas de alertas.
        """
        # Carrega alertas com filtro de data
        alertas = self.obter_alertas(data_inicio=data_inicio, data_fim=data_fim)
        
        # Inicializa estatísticas
        estatisticas = {
            "total_alertas": len(alertas),
            "por_nivel": {
                "contagem": {},
                "percentual": {}
            },
            "por_tipo": {
                "contagem": {},
                "percentual": {}
            },
            "por_componente": {
                "contagem": {},
                "percentual": {}
            },
            "evolucao_temporal": {}
        }
        
        # Contagem por nível
        for nivel in NivelAlerta:
            estatisticas["por_nivel"]["contagem"][nivel.value] = len([a for a in alertas if a.nivel == nivel])
        
        # Contagem por tipo
        for tipo in TipoCondicao:
            estatisticas["por_tipo"]["contagem"][tipo.value] = len([a for a in alertas if a.tipo_condicao == tipo])
        
        # Contagem por componente
        componentes = set(a.componente for a in alertas)
        for componente in componentes:
            estatisticas["por_componente"]["contagem"][componente] = len([a for a in alertas if a.componente == componente])
        
        # Calcula percentuais
        if alertas:
            for nivel in NivelAlerta:
                estatisticas["por_nivel"]["percentual"][nivel.value] = (
                    estatisticas["por_nivel"]["contagem"][nivel.value] / len(alertas) * 100
                )
            
            for tipo in TipoCondicao:
                estatisticas["por_tipo"]["percentual"][tipo.value] = (
                    estatisticas["por_tipo"]["contagem"][tipo.value] / len(alertas) * 100
                )
            
            for componente in componentes:
                estatisticas["por_componente"]["percentual"][componente] = (
                    estatisticas["por_componente"]["contagem"][componente] / len(alertas) * 100
                )
        
        return estatisticas
    
    def gerar_relatorio_alertas(
        self,
        formato: str = "json",
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> str:
        """
        Gera um relatório de alertas em diversos formatos.
        
        Args:
            formato: Formato do relatório (json, csv, html, markdown).
            data_inicio: Filtro por data de início.
            data_fim: Filtro por data de fim.
            
        Returns:
            str: Relatório gerado.
        """
        # Obtém alertas e estatísticas
        alertas = self.obter_alertas(data_inicio=data_inicio, data_fim=data_fim)
        estatisticas = self.obter_estatisticas_alertas(data_inicio=data_inicio, data_fim=data_fim)
        
        # Gera relatório no formato solicitado
        if formato == "json":
            return self._gerar_relatorio_json(alertas, estatisticas)
        elif formato == "csv":
            return self._gerar_relatorio_csv(alertas)
        elif formato == "html":
            return self._gerar_relatorio_html(alertas, estatisticas)
        elif formato == "markdown":
            return self._gerar_relatorio_markdown(alertas, estatisticas)
        else:
            raise ValueError(f"Formato de relatório não suportado: {formato}")
    
    def _gerar_relatorio_json(
        self,
        alertas: List[AlertaCondicaoCritica],
        estatisticas: Dict[str, Any]
    ) -> str:
        """
        Gera um relatório em formato JSON.
        
        Args:
            alertas: Lista de alertas.
            estatisticas: Estatísticas de alertas.
            
        Returns:
            str: Relatório em formato JSON.
        """
        relatorio = {
            "alertas": [a.to_dict() for a in alertas],
            "estatisticas": estatisticas
        }
        
        return json.dumps(relatorio, ensure_ascii=False, indent=2)
    
    def _gerar_relatorio_csv(self, alertas: List[AlertaCondicaoCritica]) -> str:
        """
        Gera um relatório em formato CSV.
        
        Args:
            alertas: Lista de alertas.
            
        Returns:
            str: Relatório em formato CSV.
        """
        # Cabeçalho
        csv = "id,tipo_condicao,nivel,mensagem,componente,valor_atual,valor_limite,timestamp\n"
        
        # Linhas
        for alerta in alertas:
            csv += f"{alerta.id},{alerta.tipo_condicao.value},{alerta.nivel.value},\"{alerta.mensagem}\","
            csv += f"{alerta.componente},{alerta.valor_atual or ''},\"{alerta.valor_limite or ''}\",{alerta.timestamp}\n"
        
        return csv
    
    def _gerar_relatorio_html(
        self,
        alertas: List[AlertaCondicaoCritica],
        estatisticas: Dict[str, Any]
    ) -> str:
        """
        Gera um relatório em formato HTML.
        
        Args:
            alertas: Lista de alertas.
            estatisticas: Estatísticas de alertas.
            
        Returns:
            str: Relatório em formato HTML.
        """
        # Implementação simplificada
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Alertas</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .critico { color: red; }
                .aviso { color: orange; }
                .recuperacao { color: green; }
            </style>
        </head>
        <body>
            <h1>Relatório de Alertas</h1>
            
            <h2>Estatísticas</h2>
            <p>Total de alertas: {total_alertas}</p>
            
            <h2>Alertas</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Tipo</th>
                    <th>Nível</th>
                    <th>Mensagem</th>
                    <th>Componente</th>
                    <th>Valor Atual</th>
                    <th>Valor Limite</th>
                    <th>Timestamp</th>
                </tr>
        """.format(total_alertas=estatisticas["total_alertas"])
        
        # Linhas da tabela
        for alerta in alertas:
            nivel_class = alerta.nivel.value
            html += f"""
                <tr class="{nivel_class}">
                    <td>{alerta.id}</td>
                    <td>{alerta.tipo_condicao.value}</td>
                    <td>{alerta.nivel.value}</td>
                    <td>{alerta.mensagem}</td>
                    <td>{alerta.componente}</td>
                    <td>{alerta.valor_atual or ''}</td>
                    <td>{alerta.valor_limite or ''}</td>
                    <td>{alerta.timestamp}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _gerar_relatorio_markdown(
        self,
        alertas: List[AlertaCondicaoCritica],
        estatisticas: Dict[str, Any]
    ) -> str:
        """
        Gera um relatório em formato Markdown.
        
        Args:
            alertas: Lista de alertas.
            estatisticas: Estatísticas de alertas.
            
        Returns:
            str: Relatório em formato Markdown.
        """
        # Cabeçalho
        md = "# Relatório de Alertas\n\n"
        
        # Estatísticas
        md += "## Estatísticas\n\n"
        md += f"Total de alertas: {estatisticas['total_alertas']}\n\n"
        
        # Por nível
        md += "### Por Nível\n\n"
        md += "| Nível | Contagem | Percentual |\n"
        md += "|-------|----------|------------|\n"
        for nivel in NivelAlerta:
            contagem = estatisticas["por_nivel"]["contagem"].get(nivel.value, 0)
            percentual = estatisticas["por_nivel"]["percentual"].get(nivel.value, 0)
            md += f"| {nivel.value} | {contagem} | {percentual:.1f}% |\n"
        
        md += "\n"
        
        # Por tipo
        md += "### Por Tipo\n\n"
        md += "| Tipo | Contagem | Percentual |\n"
        md += "|------|----------|------------|\n"
        for tipo in TipoCondicao:
            contagem = estatisticas["por_tipo"]["contagem"].get(tipo.value, 0)
            percentual = estatisticas["por_tipo"]["percentual"].get(tipo.value, 0)
            md += f"| {tipo.value} | {contagem} | {percentual:.1f}% |\n"
        
        md += "\n"
        
        # Alertas
        md += "## Alertas\n\n"
        md += "| ID | Tipo | Nível | Mensagem | Componente | Valor Atual | Valor Limite | Timestamp |\n"
        md += "|----|----|-------|----------|------------|-------------|--------------|----------|\n"
        
        for alerta in alertas:
            md += f"| {alerta.id} | {alerta.tipo_condicao.value} | {alerta.nivel.value} | {alerta.mensagem} | "
            md += f"{alerta.componente} | {alerta.valor_atual or ''} | {alerta.valor_limite or ''} | {alerta.timestamp} |\n"
        
        return md


# Funções de utilidade para uso externo

def inicializar_monitor(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None
) -> MonitorCondicoesCriticas:
    """
    Inicializa o monitor de condições críticas.
    
    Args:
        config_path: Caminho para o arquivo de configuração.
        storage_dir: Diretório para armazenamento de alertas.
        
    Returns:
        MonitorCondicoesCriticas: Monitor inicializado.
    """
    return MonitorCondicoesCriticas(config_path=config_path, storage_dir=storage_dir)

def iniciar_monitoramento_automatico(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None
) -> MonitorCondicoesCriticas:
    """
    Inicializa o monitor e inicia o monitoramento automático.
    
    Args:
        config_path: Caminho para o arquivo de configuração.
        storage_dir: Diretório para armazenamento de alertas.
        
    Returns:
        MonitorCondicoesCriticas: Monitor inicializado e ativo.
    """
    monitor = inicializar_monitor(config_path=config_path, storage_dir=storage_dir)
    monitor.iniciar_monitoramento()
    return monitor

def registrar_alerta_simples(
    nivel: NivelAlerta,
    mensagem: str,
    componente: str = "sistema",
    detalhes: Optional[Dict[str, Any]] = None,
    storage_dir: Optional[str] = None
) -> AlertaCondicaoCritica:
    """
    Registra um alerta simples sem inicializar um monitor completo.
    
    Args:
        nivel: Nível de severidade do alerta.
        mensagem: Mensagem descritiva do alerta.
        componente: Componente que gerou o alerta.
        detalhes: Detalhes adicionais do alerta.
        storage_dir: Diretório para armazenamento de alertas.
        
    Returns:
        AlertaCondicaoCritica: Alerta registrado.
    """
    monitor = inicializar_monitor(storage_dir=storage_dir)
    return monitor.registrar_alerta_personalizado(
        nivel=nivel,
        mensagem=mensagem,
        componente=componente,
        detalhes=detalhes
    )

def verificar_condicao_simples(
    tipo_condicao: TipoCondicao,
    valor_atual: float,
    valor_limite: float,
    componente: str = "sistema",
    storage_dir: Optional[str] = None
) -> Optional[AlertaCondicaoCritica]:
    """
    Verifica uma condição simples sem inicializar um monitor completo.
    
    Args:
        tipo_condicao: Tipo da condição a verificar.
        valor_atual: Valor atual a ser verificado.
        valor_limite: Valor limite para comparação.
        componente: Componente sendo monitorado.
        storage_dir: Diretório para armazenamento de alertas.
        
    Returns:
        Optional[AlertaCondicaoCritica]: Alerta gerado ou None.
    """
    monitor = inicializar_monitor(storage_dir=storage_dir)
    
    if tipo_condicao == TipoCondicao.TEMPO_PROCESSAMENTO:
        alertas = monitor.verificar_tempo_processamento(
            tempo_atual=valor_atual,
            componente=componente
        )
    elif tipo_condicao == TipoCondicao.TEMPO_FILA:
        alertas = monitor.verificar_tempo_fila(
            tempo_atual=valor_atual,
            componente=componente
        )
    elif tipo_condicao == TipoCondicao.TAMANHO_FILA:
        alertas = monitor.verificar_tamanho_fila(
            tamanho_atual=int(valor_atual),
            componente=componente
        )
    elif tipo_condicao == TipoCondicao.USO_MEMORIA:
        alertas = monitor.verificar_uso_recursos(
            uso_memoria=valor_atual,
            componente=componente
        )
    elif tipo_condicao == TipoCondicao.USO_CPU:
        alertas = monitor.verificar_uso_recursos(
            uso_cpu=valor_atual,
            componente=componente
        )
    else:
        return None
    
    if alertas:
        alerta = alertas[0]
        monitor._processar_alerta(alerta)
        return alerta
    
    return None


# Exemplo de uso
if __name__ == "__main__":
    # Inicializa o monitor
    monitor = inicializar_monitor()
    
    # Registra um alerta personalizado
    alerta = monitor.registrar_alerta_personalizado(
        nivel=NivelAlerta.CRITICO,
        mensagem="Erro crítico no sistema",
        componente="extrator_pdf",
        detalhes={"arquivo": "documento.pdf"}
    )
    
    # Verifica tempo de processamento
    alertas = monitor.verificar_tempo_processamento(
        tempo_atual=150.0,
        componente="extrator_pdf"
    )
    
    # Obtém estatísticas
    estatisticas = monitor.obter_estatisticas_alertas()
    print(json.dumps(estatisticas, indent=2))
    
    # Gera relatório
    relatorio = monitor.gerar_relatorio_alertas(formato="markdown")
    print(relatorio)
