#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M9_Dashboard_Monitoramento_PDFs.py
Dashboard para monitoramento em tempo real do processamento de PDFs.

Este módulo implementa uma API para fornecer dados em tempo real sobre o
processamento de PDFs, incluindo métricas de desempenho, status de processamento,
alertas e histórico de operações para visualização no dashboard frontend.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import time
import datetime
import threading
import logging
import random
from typing import Dict, List, Optional, Union, Any, Tuple
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import structlog
import pandas as pd
import numpy as np

# Importações dos módulos do sistema
try:
    from M2_Orquestrador_PDFs import FilaProcessamento, StatusProcessamento
    from M7_Relatorios_Metricas import RelatorioMetricas
    from M8_Alertas_Condicoes_Criticas import MonitorCondicoesCriticas, AlertaCondicaoCritica, NivelAlerta
    MODULOS_INTEGRADOS = True
except ImportError:
    # Modo standalone para desenvolvimento e testes
    MODULOS_INTEGRADOS = False
    logging.warning("Executando em modo standalone sem integração com outros módulos")

# Configuração do logger estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

class DashboardMonitoramento:
    """
    Classe principal para o dashboard de monitoramento de PDFs.
    
    Esta classe gerencia a coleta, processamento e disponibilização de dados
    para o dashboard de monitoramento, incluindo métricas em tempo real,
    histórico de processamento e alertas.
    
    Atributos:
        config_path (str): Caminho para o arquivo de configuração.
        storage_dir (str): Diretório para armazenamento de dados.
        config (dict): Configurações carregadas.
        cache_metricas (dict): Cache de métricas para otimização.
        monitor_alertas (MonitorCondicoesCriticas): Monitor de alertas.
        relatorio_metricas (RelatorioMetricas): Gerador de relatórios.
        fila_processamento (FilaProcessamento): Fila de processamento.
        monitoramento_ativo (bool): Indica se o monitoramento está ativo.
        thread_monitoramento (Thread): Thread de monitoramento.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        storage_dir: Optional[str] = None,
        modo_simulacao: bool = not MODULOS_INTEGRADOS
    ):
        """
        Inicializa o dashboard de monitoramento.
        
        Args:
            config_path: Caminho para o arquivo de configuração.
            storage_dir: Diretório para armazenamento de dados.
            modo_simulacao: Se True, gera dados simulados para testes.
        """
        self.config_path = config_path
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), "dashboard_storage")
        self.modo_simulacao = modo_simulacao
        
        # Carrega configurações
        self.config = self._carregar_configuracoes()
        
        # Inicializa estruturas de dados
        self.cache_metricas = {
            "ultima_atualizacao": None,
            "metricas_tempo_real": {},
            "historico_processamento": [],
            "distribuicao_status": {},
            "alertas_recentes": []
        }
        
        # Inicializa componentes integrados
        if MODULOS_INTEGRADOS and not modo_simulacao:
            self.monitor_alertas = MonitorCondicoesCriticas(storage_dir=self.storage_dir)
            self.relatorio_metricas = RelatorioMetricas(storage_dir=self.storage_dir)
            self.fila_processamento = FilaProcessamento()
        else:
            self.monitor_alertas = None
            self.relatorio_metricas = None
            self.fila_processamento = None
        
        # Estado do monitoramento
        self.monitoramento_ativo = False
        self.thread_monitoramento = None
        
        # Cria diretórios de armazenamento
        self._criar_diretorios()
        
        logger.info(
            "Dashboard de monitoramento inicializado",
            config_path=self.config_path,
            storage_dir=self.storage_dir,
            modo_simulacao=self.modo_simulacao
        )
    
    def _criar_diretorios(self) -> None:
        """Cria os diretórios necessários para armazenamento."""
        os.makedirs(os.path.join(self.storage_dir, "metricas"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "historico"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "cache"), exist_ok=True)
    
    def _carregar_configuracoes(self) -> Dict[str, Any]:
        """
        Carrega as configurações do dashboard.
        
        Returns:
            Dict[str, Any]: Configurações carregadas.
        """
        # Configurações padrão
        config_padrao = {
            "dashboard": {
                "intervalo_atualizacao": 5,  # segundos
                "max_itens_historico": 1000,
                "max_alertas_recentes": 50,
                "periodo_cache": 60,  # segundos
                "modo_debug": False
            },
            "visualizacao": {
                "mostrar_alertas": True,
                "mostrar_metricas": True,
                "mostrar_historico": True,
                "mostrar_distribuicao": True,
                "tema": "claro"
            },
            "simulacao": {
                "num_pdfs_simulados": 100,
                "taxa_erro_simulada": 0.05,
                "variacao_tempo_processamento": [1, 10],  # segundos
                "probabilidade_alerta": 0.1
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
                # Atualiza métricas em tempo real
                self._atualizar_metricas_tempo_real()
                
                # Atualiza histórico de processamento
                self._atualizar_historico_processamento()
                
                # Atualiza distribuição de status
                self._atualizar_distribuicao_status()
                
                # Atualiza alertas recentes
                self._atualizar_alertas_recentes()
                
                # Registra timestamp da última atualização
                self.cache_metricas["ultima_atualizacao"] = datetime.datetime.now().isoformat()
                
                # Persiste cache para acesso rápido
                self._persistir_cache()
                
                # Aguarda o próximo ciclo
                time.sleep(self.config["dashboard"]["intervalo_atualizacao"])
                
            except Exception as e:
                logger.error(
                    "Erro no loop de monitoramento",
                    erro=str(e)
                )
                time.sleep(1)  # Evita loop infinito em caso de erro
    
    def _atualizar_metricas_tempo_real(self) -> None:
        """Atualiza métricas em tempo real."""
        if self.modo_simulacao:
            # Gera dados simulados
            self.cache_metricas["metricas_tempo_real"] = self._gerar_metricas_simuladas()
        elif MODULOS_INTEGRADOS:
            # Obtém dados reais dos módulos integrados
            self.cache_metricas["metricas_tempo_real"] = self._obter_metricas_reais()
        else:
            # Modo standalone sem simulação (não deve ocorrer)
            logger.warning("Não foi possível atualizar métricas: modo não suportado")
    
    def _gerar_metricas_simuladas(self) -> Dict[str, Any]:
        """
        Gera métricas simuladas para testes.
        
        Returns:
            Dict[str, Any]: Métricas simuladas.
        """
        # Configurações de simulação
        num_pdfs = self.config["simulacao"]["num_pdfs_simulados"]
        taxa_erro = self.config["simulacao"]["taxa_erro_simulada"]
        var_tempo = self.config["simulacao"]["variacao_tempo_processamento"]
        
        # Calcula valores simulados
        pdfs_processados = random.randint(int(num_pdfs * 0.7), num_pdfs)
        pdfs_na_fila = num_pdfs - pdfs_processados
        pdfs_com_erro = int(pdfs_processados * taxa_erro)
        pdfs_com_sucesso = pdfs_processados - pdfs_com_erro
        
        # Tempos de processamento
        tempo_medio = random.uniform(var_tempo[0], var_tempo[1])
        tempo_total = pdfs_processados * tempo_medio
        
        # Uso de recursos
        uso_cpu = random.uniform(20, 90)
        uso_memoria = random.uniform(30, 85)
        
        # Monta dicionário de métricas
        return {
            "pdfs_processados": pdfs_processados,
            "pdfs_na_fila": pdfs_na_fila,
            "pdfs_com_erro": pdfs_com_erro,
            "pdfs_com_sucesso": pdfs_com_sucesso,
            "tempo_medio_processamento": round(tempo_medio, 2),
            "tempo_total_processamento": round(tempo_total, 2),
            "taxa_erro": round(pdfs_com_erro / pdfs_processados * 100 if pdfs_processados > 0 else 0, 2),
            "uso_cpu": round(uso_cpu, 1),
            "uso_memoria": round(uso_memoria, 1),
            "pdfs_por_hora": int(3600 / tempo_medio) if tempo_medio > 0 else 0,
            "status_sistema": "online" if random.random() > 0.05 else "offline"
        }
    
    def _obter_metricas_reais(self) -> Dict[str, Any]:
        """
        Obtém métricas reais dos módulos integrados.
        
        Returns:
            Dict[str, Any]: Métricas reais.
        """
        # Obtém dados da fila de processamento
        fila_info = self.fila_processamento.obter_estatisticas_fila()
        
        # Obtém dados de relatórios e métricas
        metricas_info = self.relatorio_metricas.obter_metricas_atuais()
        
        # Obtém dados de uso de recursos
        recursos_info = self.monitor_alertas._obter_uso_recursos()
        
        # Monta dicionário de métricas
        return {
            "pdfs_processados": fila_info.get("total_processados", 0),
            "pdfs_na_fila": fila_info.get("tamanho_atual", 0),
            "pdfs_com_erro": fila_info.get("total_erros", 0),
            "pdfs_com_sucesso": fila_info.get("total_sucessos", 0),
            "tempo_medio_processamento": metricas_info.get("tempo_medio_processamento", 0),
            "tempo_total_processamento": metricas_info.get("tempo_total_processamento", 0),
            "taxa_erro": metricas_info.get("taxa_erro", 0),
            "uso_cpu": recursos_info.get("cpu", 0),
            "uso_memoria": recursos_info.get("memoria", 0),
            "pdfs_por_hora": metricas_info.get("pdfs_por_hora", 0),
            "status_sistema": "online" if fila_info.get("status", "") == "ativo" else "offline"
        }
    
    def _atualizar_historico_processamento(self) -> None:
        """Atualiza histórico de processamento."""
        if self.modo_simulacao:
            # Gera dados simulados
            novo_item = self._gerar_item_historico_simulado()
            self.cache_metricas["historico_processamento"].append(novo_item)
        elif MODULOS_INTEGRADOS:
            # Obtém dados reais dos módulos integrados
            novos_itens = self._obter_historico_real()
            self.cache_metricas["historico_processamento"].extend(novos_itens)
        else:
            # Modo standalone sem simulação (não deve ocorrer)
            logger.warning("Não foi possível atualizar histórico: modo não suportado")
        
        # Limita tamanho do histórico
        max_itens = self.config["dashboard"]["max_itens_historico"]
        if len(self.cache_metricas["historico_processamento"]) > max_itens:
            self.cache_metricas["historico_processamento"] = self.cache_metricas["historico_processamento"][-max_itens:]
    
    def _gerar_item_historico_simulado(self) -> Dict[str, Any]:
        """
        Gera um item de histórico simulado.
        
        Returns:
            Dict[str, Any]: Item de histórico simulado.
        """
        # Tipos de documentos simulados
        tipos_documentos = ["Contrato", "Nota Fiscal", "Relatório", "Formulário", "Recibo"]
        
        # Status possíveis
        status_possiveis = ["sucesso", "erro", "cancelado"]
        status_pesos = [0.85, 0.1, 0.05]  # Probabilidades
        
        # Gera dados aleatórios
        tipo_documento = random.choice(tipos_documentos)
        status = random.choices(status_possiveis, weights=status_pesos, k=1)[0]
        tempo_processamento = random.uniform(1, 10)
        
        # Monta item de histórico
        return {
            "id": f"PDF-{random.randint(1000, 9999)}",
            "tipo_documento": tipo_documento,
            "status": status,
            "tempo_processamento": round(tempo_processamento, 2),
            "timestamp": datetime.datetime.now().isoformat(),
            "usuario": f"usuario_{random.randint(1, 10)}",
            "tamanho_kb": random.randint(100, 5000)
        }
    
    def _obter_historico_real(self) -> List[Dict[str, Any]]:
        """
        Obtém histórico real dos módulos integrados.
        
        Returns:
            List[Dict[str, Any]]: Lista de itens de histórico.
        """
        # Obtém histórico da fila de processamento
        return self.fila_processamento.obter_historico_processamento(
            limite=10,  # Obtém apenas os 10 mais recentes por vez
            offset=0
        )
    
    def _atualizar_distribuicao_status(self) -> None:
        """Atualiza distribuição de status."""
        if self.modo_simulacao:
            # Gera dados simulados
            self.cache_metricas["distribuicao_status"] = self._gerar_distribuicao_simulada()
        elif MODULOS_INTEGRADOS:
            # Obtém dados reais dos módulos integrados
            self.cache_metricas["distribuicao_status"] = self._obter_distribuicao_real()
        else:
            # Modo standalone sem simulação (não deve ocorrer)
            logger.warning("Não foi possível atualizar distribuição: modo não suportado")
    
    def _gerar_distribuicao_simulada(self) -> Dict[str, Any]:
        """
        Gera distribuição de status simulada.
        
        Returns:
            Dict[str, Any]: Distribuição simulada.
        """
        # Gera contagens aleatórias
        total = 100
        em_processamento = random.randint(5, 20)
        na_fila = random.randint(10, 30)
        com_erro = random.randint(3, 10)
        concluidos = total - (em_processamento + na_fila + com_erro)
        
        # Distribuição por tipo de documento
        tipos_documentos = {
            "Contrato": random.randint(20, 40),
            "Nota Fiscal": random.randint(15, 30),
            "Relatório": random.randint(10, 25),
            "Formulário": random.randint(5, 15),
            "Recibo": random.randint(5, 15)
        }
        
        # Normaliza para total = 100%
        total_tipos = sum(tipos_documentos.values())
        for tipo in tipos_documentos:
            tipos_documentos[tipo] = round(tipos_documentos[tipo] / total_tipos * 100, 1)
        
        # Monta distribuição
        return {
            "por_status": {
                "em_processamento": em_processamento,
                "na_fila": na_fila,
                "com_erro": com_erro,
                "concluidos": concluidos
            },
            "por_tipo_documento": tipos_documentos,
            "total_documentos": total
        }
    
    def _obter_distribuicao_real(self) -> Dict[str, Any]:
        """
        Obtém distribuição real dos módulos integrados.
        
        Returns:
            Dict[str, Any]: Distribuição real.
        """
        # Obtém estatísticas da fila
        fila_info = self.fila_processamento.obter_estatisticas_fila()
        
        # Obtém distribuição por tipo de documento
        metricas_info = self.relatorio_metricas.obter_distribuicao_por_tipo()
        
        # Monta distribuição
        return {
            "por_status": {
                "em_processamento": fila_info.get("em_processamento", 0),
                "na_fila": fila_info.get("tamanho_atual", 0),
                "com_erro": fila_info.get("total_erros", 0),
                "concluidos": fila_info.get("total_sucessos", 0)
            },
            "por_tipo_documento": metricas_info.get("distribuicao_por_tipo", {}),
            "total_documentos": fila_info.get("total_processados", 0) + fila_info.get("tamanho_atual", 0)
        }
    
    def _atualizar_alertas_recentes(self) -> None:
        """Atualiza alertas recentes."""
        if self.modo_simulacao:
            # Gera dados simulados
            if random.random() < self.config["simulacao"]["probabilidade_alerta"]:
                novo_alerta = self._gerar_alerta_simulado()
                self.cache_metricas["alertas_recentes"].append(novo_alerta)
        elif MODULOS_INTEGRADOS:
            # Obtém dados reais dos módulos integrados
            novos_alertas = self._obter_alertas_reais()
            self.cache_metricas["alertas_recentes"].extend(novos_alertas)
        else:
            # Modo standalone sem simulação (não deve ocorrer)
            logger.warning("Não foi possível atualizar alertas: modo não suportado")
        
        # Limita número de alertas
        max_alertas = self.config["dashboard"]["max_alertas_recentes"]
        if len(self.cache_metricas["alertas_recentes"]) > max_alertas:
            self.cache_metricas["alertas_recentes"] = self.cache_metricas["alertas_recentes"][-max_alertas:]
    
    def _gerar_alerta_simulado(self) -> Dict[str, Any]:
        """
        Gera um alerta simulado.
        
        Returns:
            Dict[str, Any]: Alerta simulado.
        """
        # Tipos de alertas
        tipos_alertas = ["tempo_processamento", "uso_memoria", "uso_cpu", "falhas_consecutivas", "taxa_erro"]
        niveis_alertas = ["aviso", "critico", "recuperacao"]
        niveis_pesos = [0.6, 0.3, 0.1]  # Probabilidades
        
        # Gera dados aleatórios
        tipo_alerta = random.choice(tipos_alertas)
        nivel_alerta = random.choices(niveis_alertas, weights=niveis_pesos, k=1)[0]
        
        # Mensagens por tipo e nível
        mensagens = {
            "tempo_processamento": {
                "aviso": "Tempo de processamento próximo do limite",
                "critico": "Tempo de processamento excedeu o limite configurado",
                "recuperacao": "Tempo de processamento normalizado"
            },
            "uso_memoria": {
                "aviso": "Uso de memória próximo do limite",
                "critico": "Uso de memória excedeu o limite configurado",
                "recuperacao": "Uso de memória normalizado"
            },
            "uso_cpu": {
                "aviso": "Uso de CPU próximo do limite",
                "critico": "Uso de CPU excedeu o limite configurado",
                "recuperacao": "Uso de CPU normalizado"
            },
            "falhas_consecutivas": {
                "aviso": "Número de falhas consecutivas próximo do limite",
                "critico": "Número de falhas consecutivas excedeu o limite",
                "recuperacao": "Falhas consecutivas resetadas"
            },
            "taxa_erro": {
                "aviso": "Taxa de erro próxima do limite",
                "critico": "Taxa de erro excedeu o limite configurado",
                "recuperacao": "Taxa de erro normalizada"
            }
        }
        
        # Valores por tipo
        valores = {
            "tempo_processamento": random.uniform(50, 150),
            "uso_memoria": random.uniform(50, 95),
            "uso_cpu": random.uniform(50, 95),
            "falhas_consecutivas": random.randint(1, 5),
            "taxa_erro": random.uniform(5, 15)
        }
        
        # Limites por tipo
        limites = {
            "tempo_processamento": 100,
            "uso_memoria": 80,
            "uso_cpu": 90,
            "falhas_consecutivas": 3,
            "taxa_erro": 10
        }
        
        # Monta alerta
        return {
            "id": f"alerta-{random.randint(1000, 9999)}",
            "tipo_condicao": tipo_alerta,
            "nivel": nivel_alerta,
            "mensagem": mensagens[tipo_alerta][nivel_alerta],
            "valor_atual": valores[tipo_alerta],
            "valor_limite": limites[tipo_alerta],
            "componente": "extrator_pdf",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _obter_alertas_reais(self) -> List[Dict[str, Any]]:
        """
        Obtém alertas reais dos módulos integrados.
        
        Returns:
            List[Dict[str, Any]]: Lista de alertas.
        """
        # Obtém alertas do monitor
        alertas_obj = self.monitor_alertas.obter_alertas(
            data_inicio=(datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat()
        )
        
        # Converte para dicionários
        return [alerta.to_dict() for alerta in alertas_obj]
    
    def _persistir_cache(self) -> None:
        """Persiste cache para acesso rápido."""
        try:
            # Caminho do arquivo de cache
            cache_file = os.path.join(self.storage_dir, "cache", "dashboard_cache.json")
            
            # Salva cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_metricas, f, ensure_ascii=False)
                
        except Exception as e:
            logger.error(
                "Erro ao persistir cache",
                erro=str(e)
            )
    
    def obter_metricas_tempo_real(self) -> Dict[str, Any]:
        """
        Obtém métricas em tempo real.
        
        Returns:
            Dict[str, Any]: Métricas em tempo real.
        """
        return self.cache_metricas["metricas_tempo_real"]
    
    def obter_historico_processamento(
        self,
        limite: Optional[int] = None,
        offset: int = 0,
        filtros: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém histórico de processamento com filtros.
        
        Args:
            limite: Limite de itens a retornar.
            offset: Deslocamento para paginação.
            filtros: Filtros a aplicar.
            
        Returns:
            List[Dict[str, Any]]: Histórico filtrado.
        """
        historico = self.cache_metricas["historico_processamento"]
        
        # Aplica filtros
        if filtros:
            for chave, valor in filtros.items():
                if isinstance(valor, list):
                    historico = [item for item in historico if item.get(chave) in valor]
                else:
                    historico = [item for item in historico if item.get(chave) == valor]
        
        # Aplica paginação
        if limite is not None:
            return historico[offset:offset + limite]
        
        return historico[offset:]
    
    def obter_distribuicao_status(self) -> Dict[str, Any]:
        """
        Obtém distribuição de status.
        
        Returns:
            Dict[str, Any]: Distribuição de status.
        """
        return self.cache_metricas["distribuicao_status"]
    
    def obter_alertas_recentes(
        self,
        limite: Optional[int] = None,
        nivel: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém alertas recentes com filtros.
        
        Args:
            limite: Limite de alertas a retornar.
            nivel: Filtro por nível de alerta.
            tipo: Filtro por tipo de alerta.
            
        Returns:
            List[Dict[str, Any]]: Alertas filtrados.
        """
        alertas = self.cache_metricas["alertas_recentes"]
        
        # Aplica filtros
        if nivel:
            alertas = [a for a in alertas if a.get("nivel") == nivel]
        
        if tipo:
            alertas = [a for a in alertas if a.get("tipo_condicao") == tipo]
        
        # Aplica limite
        if limite is not None:
            return alertas[-limite:]
        
        return alertas
    
    def gerar_relatorio_desempenho(
        self,
        periodo: str = "dia",
        formato: str = "json"
    ) -> str:
        """
        Gera relatório de desempenho para o período especificado.
        
        Args:
            periodo: Período do relatório (hora, dia, semana, mes).
            formato: Formato do relatório (json, csv, html, markdown).
            
        Returns:
            str: Relatório gerado.
        """
        if self.modo_simulacao:
            # Gera relatório simulado
            return self._gerar_relatorio_simulado(periodo, formato)
        elif MODULOS_INTEGRADOS:
            # Obtém relatório real
            return self.relatorio_metricas.gerar_relatorio_desempenho(periodo, formato)
        else:
            # Modo standalone sem simulação
            return json.dumps({"erro": "Geração de relatório não disponível no modo atual"})
    
    def _gerar_relatorio_simulado(self, periodo: str, formato: str) -> str:
        """
        Gera relatório simulado para testes.
        
        Args:
            periodo: Período do relatório.
            formato: Formato do relatório.
            
        Returns:
            str: Relatório simulado.
        """
        # Determina número de pontos com base no período
        pontos = {
            "hora": 60,
            "dia": 24,
            "semana": 7,
            "mes": 30
        }.get(periodo, 24)
        
        # Gera dados simulados
        dados = []
        data_base = datetime.datetime.now()
        
        for i in range(pontos):
            if periodo == "hora":
                timestamp = (data_base - datetime.timedelta(minutes=i)).isoformat()
                intervalo = "minuto"
            elif periodo == "dia":
                timestamp = (data_base - datetime.timedelta(hours=i)).isoformat()
                intervalo = "hora"
            elif periodo == "semana":
                timestamp = (data_base - datetime.timedelta(days=i)).isoformat()
                intervalo = "dia"
            else:  # mes
                timestamp = (data_base - datetime.timedelta(days=i)).isoformat()
                intervalo = "dia"
            
            # Valores simulados
            pdfs_processados = random.randint(10, 50)
            tempo_medio = random.uniform(1, 10)
            taxa_erro = random.uniform(1, 10)
            
            dados.append({
                "timestamp": timestamp,
                "intervalo": intervalo,
                "pdfs_processados": pdfs_processados,
                "tempo_medio_processamento": round(tempo_medio, 2),
                "taxa_erro": round(taxa_erro, 2),
                "uso_cpu_medio": round(random.uniform(20, 80), 1),
                "uso_memoria_medio": round(random.uniform(30, 70), 1)
            })
        
        # Formata relatório
        if formato == "json":
            return json.dumps({
                "periodo": periodo,
                "dados": dados,
                "total_pdfs_processados": sum(d["pdfs_processados"] for d in dados),
                "tempo_medio_geral": round(sum(d["tempo_medio_processamento"] for d in dados) / len(dados), 2),
                "taxa_erro_media": round(sum(d["taxa_erro"] for d in dados) / len(dados), 2)
            }, indent=2)
        elif formato == "csv":
            # Gera CSV
            csv_linhas = ["timestamp,intervalo,pdfs_processados,tempo_medio_processamento,taxa_erro,uso_cpu_medio,uso_memoria_medio"]
            for d in dados:
                csv_linhas.append(f"{d['timestamp']},{d['intervalo']},{d['pdfs_processados']},{d['tempo_medio_processamento']},{d['taxa_erro']},{d['uso_cpu_medio']},{d['uso_memoria_medio']}")
            return "\n".join(csv_linhas)
        elif formato == "html":
            # Gera HTML simples
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Relatório de Desempenho</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>Relatório de Desempenho - Período: """ + periodo + """</h1>
                <table>
                    <tr>
                        <th>Timestamp</th>
                        <th>Intervalo</th>
                        <th>PDFs Processados</th>
                        <th>Tempo Médio (s)</th>
                        <th>Taxa de Erro (%)</th>
                        <th>CPU Médio (%)</th>
                        <th>Memória Média (%)</th>
                    </tr>
            """
            
            for d in dados:
                html += f"""
                    <tr>
                        <td>{d['timestamp']}</td>
                        <td>{d['intervalo']}</td>
                        <td>{d['pdfs_processados']}</td>
                        <td>{d['tempo_medio_processamento']}</td>
                        <td>{d['taxa_erro']}</td>
                        <td>{d['uso_cpu_medio']}</td>
                        <td>{d['uso_memoria_medio']}</td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            return html
        else:  # markdown
            # Gera Markdown
            md = f"# Relatório de Desempenho - Período: {periodo}\n\n"
            md += "| Timestamp | Intervalo | PDFs Processados | Tempo Médio (s) | Taxa de Erro (%) | CPU Médio (%) | Memória Média (%) |\n"
            md += "|-----------|-----------|------------------|-----------------|-----------------|---------------|-------------------|\n"
            
            for d in dados:
                md += f"| {d['timestamp']} | {d['intervalo']} | {d['pdfs_processados']} | {d['tempo_medio_processamento']} | {d['taxa_erro']} | {d['uso_cpu_medio']} | {d['uso_memoria_medio']} |\n"
            
            return md


# API Flask para o dashboard
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Instância global do dashboard
dashboard = None

@app.route('/api/dashboard/metricas', methods=['GET'])
def get_metricas():
    """Endpoint para obter métricas em tempo real."""
    global dashboard
    if not dashboard:
        dashboard = DashboardMonitoramento(modo_simulacao=True)
        dashboard.iniciar_monitoramento()
    
    return jsonify(dashboard.obter_metricas_tempo_real())

@app.route('/api/dashboard/historico', methods=['GET'])
def get_historico():
    """Endpoint para obter histórico de processamento."""
    global dashboard
    if not dashboard:
        dashboard = DashboardMonitoramento(modo_simulacao=True)
        dashboard.iniciar_monitoramento()
    
    # Parâmetros de paginação e filtros
    limite = request.args.get('limite', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Filtros
    filtros = {}
    for param in ['status', 'tipo_documento', 'usuario']:
        if param in request.args:
            filtros[param] = request.args.get(param)
    
    return jsonify(dashboard.obter_historico_processamento(limite, offset, filtros))

@app.route('/api/dashboard/distribuicao', methods=['GET'])
def get_distribuicao():
    """Endpoint para obter distribuição de status."""
    global dashboard
    if not dashboard:
        dashboard = DashboardMonitoramento(modo_simulacao=True)
        dashboard.iniciar_monitoramento()
    
    return jsonify(dashboard.obter_distribuicao_status())

@app.route('/api/dashboard/alertas', methods=['GET'])
def get_alertas():
    """Endpoint para obter alertas recentes."""
    global dashboard
    if not dashboard:
        dashboard = DashboardMonitoramento(modo_simulacao=True)
        dashboard.iniciar_monitoramento()
    
    # Parâmetros
    limite = request.args.get('limite', type=int)
    nivel = request.args.get('nivel')
    tipo = request.args.get('tipo')
    
    return jsonify(dashboard.obter_alertas_recentes(limite, nivel, tipo))

@app.route('/api/dashboard/relatorio', methods=['GET'])
def get_relatorio():
    """Endpoint para gerar relatório de desempenho."""
    global dashboard
    if not dashboard:
        dashboard = DashboardMonitoramento(modo_simulacao=True)
        dashboard.iniciar_monitoramento()
    
    # Parâmetros
    periodo = request.args.get('periodo', 'dia')
    formato = request.args.get('formato', 'json')
    
    # Gera relatório
    relatorio = dashboard.gerar_relatorio_desempenho(periodo, formato)
    
    # Define tipo de conteúdo com base no formato
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'html': 'text/html',
        'markdown': 'text/markdown'
    }
    
    return Response(
        relatorio,
        mimetype=content_types.get(formato, 'application/json')
    )

def iniciar_api(host='0.0.0.0', port=5000, debug=False):
    """
    Inicia a API Flask para o dashboard.
    
    Args:
        host: Host para a API.
        port: Porta para a API.
        debug: Modo debug.
    """
    global dashboard
    dashboard = DashboardMonitoramento(modo_simulacao=True)
    dashboard.iniciar_monitoramento()
    
    app.run(host=host, port=port, debug=debug)


# Funções de utilidade para uso externo

def inicializar_dashboard(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None,
    modo_simulacao: bool = not MODULOS_INTEGRADOS
) -> DashboardMonitoramento:
    """
    Inicializa o dashboard de monitoramento.
    
    Args:
        config_path: Caminho para o arquivo de configuração.
        storage_dir: Diretório para armazenamento de dados.
        modo_simulacao: Se True, gera dados simulados para testes.
        
    Returns:
        DashboardMonitoramento: Dashboard inicializado.
    """
    return DashboardMonitoramento(
        config_path=config_path,
        storage_dir=storage_dir,
        modo_simulacao=modo_simulacao
    )

def iniciar_monitoramento_automatico(
    config_path: Optional[str] = None,
    storage_dir: Optional[str] = None,
    modo_simulacao: bool = not MODULOS_INTEGRADOS
) -> DashboardMonitoramento:
    """
    Inicializa o dashboard e inicia o monitoramento automático.
    
    Args:
        config_path: Caminho para o arquivo de configuração.
        storage_dir: Diretório para armazenamento de dados.
        modo_simulacao: Se True, gera dados simulados para testes.
        
    Returns:
        DashboardMonitoramento: Dashboard inicializado e ativo.
    """
    dashboard = inicializar_dashboard(
        config_path=config_path,
        storage_dir=storage_dir,
        modo_simulacao=modo_simulacao
    )
    dashboard.iniciar_monitoramento()
    return dashboard


# Exemplo de uso
if __name__ == "__main__":
    # Inicia a API
    iniciar_api(debug=True)
