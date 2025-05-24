#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
M7_Relatorios_Metricas.py
Sistema de relatórios e métricas de desempenho para processamento de PDFs.

Este módulo implementa um sistema completo para coleta, análise e visualização
de métricas de desempenho do processamento de PDFs, com geração de relatórios
detalhados e exportação em diversos formatos.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import csv
import time
import logging
import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
import pandas as pd
import structlog
from tabulate import tabulate

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
        logging.FileHandler("relatorios_metricas.log"),
        logging.StreamHandler()
    ]
)

logger = structlog.get_logger()

# --- Constantes e configurações ---
DEFAULT_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "metricas_storage"
)

METRIC_TYPES = {
    "tempo_processamento": "float",
    "tempo_extracao": "float",
    "tempo_enfileiramento": "float",
    "tempo_total": "float",
    "paginas_processadas": "int",
    "tamanho_arquivo": "float",
    "status": "str",
    "erros": "int",
    "tentativas": "int"
}

EXPORT_FORMATS = ["json", "csv", "html", "markdown", "excel"]

# --- Classes principais ---
class MetricasColetorPDF:
    """Sistema de coleta de métricas para processamento de PDFs."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Inicializa o coletor de métricas.
        
        Args:
            storage_dir (str, optional): Diretório para armazenamento das métricas.
                Se None, usa o diretório padrão.
        """
        self.log = logger.bind(component="MetricasColetorPDF")
        
        if storage_dir is None:
            self.storage_dir = DEFAULT_STORAGE_DIR
        else:
            self.storage_dir = storage_dir
            
        # Cria diretório de armazenamento se não existir
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Cria subdiretórios para diferentes tipos de dados
        self.metricas_dir = os.path.join(self.storage_dir, "metricas")
        self.relatorios_dir = os.path.join(self.storage_dir, "relatorios")
        self.graficos_dir = os.path.join(self.storage_dir, "graficos")
        
        os.makedirs(self.metricas_dir, exist_ok=True)
        os.makedirs(self.relatorios_dir, exist_ok=True)
        os.makedirs(self.graficos_dir, exist_ok=True)
        
        self.log.info("Coletor de métricas inicializado", 
                     storage_dir=self.storage_dir)
        
        # Cache para métricas em memória
        self._metricas_cache = {}
        self._ultima_atualizacao_cache = None
    
    def registrar_inicio_processamento(self, 
                                      numero_wo: str, 
                                      nome_arquivo: str, 
                                      tamanho_arquivo: float,
                                      paginas: int,
                                      metadados: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Registra o início do processamento de um PDF.
        
        Args:
            numero_wo (str): Número da WO
            nome_arquivo (str): Nome do arquivo PDF
            tamanho_arquivo (float): Tamanho do arquivo em KB
            paginas (int): Número de páginas do PDF
            metadados (dict, optional): Metadados adicionais
            
        Returns:
            dict: Dados do registro de início
        """
        timestamp = datetime.datetime.now().isoformat()
        
        registro = {
            "numero_wo": numero_wo,
            "nome_arquivo": nome_arquivo,
            "tamanho_arquivo": tamanho_arquivo,
            "paginas": paginas,
            "timestamp_inicio": timestamp,
            "metadados": metadados or {},
            "status": "iniciado",
            "etapas": {
                "inicio": {
                    "timestamp": timestamp,
                    "status": "concluido"
                }
            }
        }
        
        # Salva o registro
        self._salvar_metrica(numero_wo, registro)
        
        self.log.info("Início de processamento registrado", 
                     numero_wo=numero_wo, 
                     nome_arquivo=nome_arquivo)
        
        return registro
    
    def registrar_etapa(self, 
                       numero_wo: str, 
                       nome_etapa: str, 
                       status: str, 
                       duracao: Optional[float] = None,
                       detalhes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Registra uma etapa do processamento.
        
        Args:
            numero_wo (str): Número da WO
            nome_etapa (str): Nome da etapa (extracao, validacao, etc.)
            status (str): Status da etapa (concluido, erro, etc.)
            duracao (float, optional): Duração da etapa em segundos
            detalhes (dict, optional): Detalhes adicionais da etapa
            
        Returns:
            dict: Dados atualizados do registro
        """
        # Carrega o registro atual
        registro = self._carregar_metrica(numero_wo)
        if not registro:
            self.log.error("Tentativa de registrar etapa para WO não iniciada", 
                          numero_wo=numero_wo, 
                          nome_etapa=nome_etapa)
            return None
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Adiciona a etapa ao registro
        if "etapas" not in registro:
            registro["etapas"] = {}
            
        registro["etapas"][nome_etapa] = {
            "timestamp": timestamp,
            "status": status,
            "duracao": duracao,
            "detalhes": detalhes or {}
        }
        
        # Salva o registro atualizado
        self._salvar_metrica(numero_wo, registro)
        
        self.log.info("Etapa de processamento registrada", 
                     numero_wo=numero_wo, 
                     nome_etapa=nome_etapa,
                     status=status,
                     duracao=duracao)
        
        return registro
    
    def registrar_conclusao(self, 
                           numero_wo: str, 
                           status_final: str, 
                           tempo_total: float,
                           detalhes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Registra a conclusão do processamento.
        
        Args:
            numero_wo (str): Número da WO
            status_final (str): Status final (sucesso, erro, etc.)
            tempo_total (float): Tempo total de processamento em segundos
            detalhes (dict, optional): Detalhes adicionais da conclusão
            
        Returns:
            dict: Dados finais do registro
        """
        # Carrega o registro atual
        registro = self._carregar_metrica(numero_wo)
        if not registro:
            self.log.error("Tentativa de registrar conclusão para WO não iniciada", 
                          numero_wo=numero_wo)
            return None
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Atualiza o registro com os dados de conclusão
        registro["status"] = status_final
        registro["timestamp_fim"] = timestamp
        registro["tempo_total"] = tempo_total
        registro["detalhes_conclusao"] = detalhes or {}
        
        # Adiciona a etapa de conclusão
        if "etapas" not in registro:
            registro["etapas"] = {}
            
        registro["etapas"]["conclusao"] = {
            "timestamp": timestamp,
            "status": status_final,
            "duracao": None,
            "detalhes": detalhes or {}
        }
        
        # Salva o registro atualizado
        self._salvar_metrica(numero_wo, registro)
        
        # Invalida o cache
        self._ultima_atualizacao_cache = None
        
        self.log.info("Conclusão de processamento registrada", 
                     numero_wo=numero_wo, 
                     status_final=status_final,
                     tempo_total=tempo_total)
        
        return registro
    
    def obter_metrica(self, numero_wo: str) -> Dict[str, Any]:
        """
        Obtém as métricas de uma WO específica.
        
        Args:
            numero_wo (str): Número da WO
            
        Returns:
            dict: Dados da métrica ou None se não encontrada
        """
        return self._carregar_metrica(numero_wo)
    
    def listar_metricas(self, 
                       filtro_status: Optional[str] = None, 
                       data_inicio: Optional[str] = None,
                       data_fim: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todas as métricas coletadas, com opção de filtro.
        
        Args:
            filtro_status (str, optional): Filtrar por status
            data_inicio (str, optional): Data de início no formato ISO
            data_fim (str, optional): Data de fim no formato ISO
            
        Returns:
            list: Lista de métricas
        """
        # Verifica se o cache está atualizado
        if self._ultima_atualizacao_cache is None:
            self._atualizar_cache_metricas()
        
        # Filtra as métricas conforme os parâmetros
        metricas = list(self._metricas_cache.values())
        
        if filtro_status:
            metricas = [m for m in metricas if m.get("status") == filtro_status]
            
        if data_inicio:
            data_inicio_dt = datetime.datetime.fromisoformat(data_inicio)
            metricas = [m for m in metricas if "timestamp_inicio" in m and 
                       datetime.datetime.fromisoformat(m["timestamp_inicio"]) >= data_inicio_dt]
            
        if data_fim:
            data_fim_dt = datetime.datetime.fromisoformat(data_fim)
            metricas = [m for m in metricas if "timestamp_inicio" in m and 
                       datetime.datetime.fromisoformat(m["timestamp_inicio"]) <= data_fim_dt]
        
        return metricas
    
    def calcular_estatisticas(self) -> Dict[str, Any]:
        """
        Calcula estatísticas gerais das métricas coletadas.
        
        Returns:
            dict: Estatísticas calculadas
        """
        metricas = self.listar_metricas()
        
        if not metricas:
            return {
                "total_processados": 0,
                "status": {},
                "tempo_medio_processamento": 0,
                "paginas_processadas": 0,
                "tamanho_medio": 0
            }
        
        # Contadores e acumuladores
        total = len(metricas)
        status_counter = Counter(m.get("status", "desconhecido") for m in metricas)
        tempo_total = sum(m.get("tempo_total", 0) for m in metricas if "tempo_total" in m)
        paginas_total = sum(m.get("paginas", 0) for m in metricas if "paginas" in m)
        tamanho_total = sum(m.get("tamanho_arquivo", 0) for m in metricas if "tamanho_arquivo" in m)
        
        # Métricas concluídas (com tempo_total)
        metricas_concluidas = [m for m in metricas if "tempo_total" in m]
        total_concluidos = len(metricas_concluidas)
        
        # Cálculo de médias
        tempo_medio = tempo_total / total_concluidos if total_concluidos > 0 else 0
        tamanho_medio = tamanho_total / total if total > 0 else 0
        
        # Cálculo de taxa de processamento
        pdfs_por_hora = (total_concluidos / (tempo_total / 3600)) if tempo_total > 0 else 0
        
        # Estatísticas por status
        status_stats = {
            status: {
                "quantidade": count,
                "percentual": (count / total) * 100 if total > 0 else 0
            }
            for status, count in status_counter.items()
        }
        
        # Estatísticas de tempo por etapa
        etapas_tempo = defaultdict(list)
        for m in metricas:
            if "etapas" in m:
                for etapa, dados in m["etapas"].items():
                    if "duracao" in dados and dados["duracao"] is not None:
                        etapas_tempo[etapa].append(dados["duracao"])
        
        tempo_medio_etapas = {
            etapa: sum(tempos) / len(tempos) if tempos else 0
            for etapa, tempos in etapas_tempo.items()
        }
        
        return {
            "total_processados": total,
            "concluidos": total_concluidos,
            "status": status_stats,
            "tempo_medio_processamento": tempo_medio,
            "tempo_medio_etapas": tempo_medio_etapas,
            "paginas_processadas": paginas_total,
            "tamanho_medio": tamanho_medio,
            "pdfs_por_hora": pdfs_por_hora
        }
    
    def _salvar_metrica(self, numero_wo: str, dados: Dict[str, Any]) -> bool:
        """
        Salva os dados de métrica em arquivo.
        
        Args:
            numero_wo (str): Número da WO
            dados (dict): Dados da métrica
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            # Gera o caminho do arquivo
            filepath = os.path.join(self.metricas_dir, f"{numero_wo}.json")
            
            # Salva os dados em formato JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            # Atualiza o cache se existir
            if self._ultima_atualizacao_cache is not None:
                self._metricas_cache[numero_wo] = dados
            
            return True
            
        except Exception as e:
            self.log.error("Erro ao salvar métrica", 
                          numero_wo=numero_wo, 
                          error=str(e))
            return False
    
    def _carregar_metrica(self, numero_wo: str) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados de métrica de um arquivo.
        
        Args:
            numero_wo (str): Número da WO
            
        Returns:
            dict: Dados da métrica ou None se não encontrada
        """
        # Verifica se está no cache
        if self._ultima_atualizacao_cache is not None and numero_wo in self._metricas_cache:
            return self._metricas_cache[numero_wo]
        
        try:
            # Gera o caminho do arquivo
            filepath = os.path.join(self.metricas_dir, f"{numero_wo}.json")
            
            # Verifica se o arquivo existe
            if not os.path.exists(filepath):
                return None
            
            # Carrega os dados do arquivo JSON
            with open(filepath, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            return dados
            
        except Exception as e:
            self.log.error("Erro ao carregar métrica", 
                          numero_wo=numero_wo, 
                          error=str(e))
            return None
    
    def _atualizar_cache_metricas(self) -> None:
        """Atualiza o cache de métricas em memória."""
        try:
            self._metricas_cache = {}
            
            # Lista todos os arquivos de métrica
            for filename in os.listdir(self.metricas_dir):
                if filename.endswith(".json"):
                    numero_wo = filename.replace(".json", "")
                    filepath = os.path.join(self.metricas_dir, filename)
                    
                    with open(filepath, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        
                    self._metricas_cache[numero_wo] = dados
            
            self._ultima_atualizacao_cache = datetime.datetime.now()
            
            self.log.info("Cache de métricas atualizado", 
                         total_metricas=len(self._metricas_cache))
                
        except Exception as e:
            self.log.error("Erro ao atualizar cache de métricas", 
                          error=str(e))
            self._ultima_atualizacao_cache = None


class RelatoriosGeradorPDF:
    """Sistema de geração de relatórios para processamento de PDFs."""
    
    def __init__(self, coletor_metricas: MetricasColetorPDF):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            coletor_metricas (MetricasColetorPDF): Instância do coletor de métricas
        """
        self.log = logger.bind(component="RelatoriosGeradorPDF")
        self.coletor = coletor_metricas
        self.relatorios_dir = coletor_metricas.relatorios_dir
        self.graficos_dir = coletor_metricas.graficos_dir
        
        self.log.info("Gerador de relatórios inicializado")
    
    def gerar_relatorio_diario(self, 
                              data: Optional[str] = None, 
                              formato: str = "json") -> str:
        """
        Gera um relatório diário de processamento.
        
        Args:
            data (str, optional): Data no formato ISO (YYYY-MM-DD).
                Se None, usa a data atual.
            formato (str): Formato de saída (json, csv, html, markdown, excel)
            
        Returns:
            str: Caminho do arquivo de relatório gerado
        """
        # Define a data do relatório
        if data is None:
            data_relatorio = datetime.datetime.now().date()
        else:
            data_relatorio = datetime.datetime.fromisoformat(data).date()
        
        # Define o período do relatório (um dia)
        data_inicio = datetime.datetime.combine(data_relatorio, datetime.time.min).isoformat()
        data_fim = datetime.datetime.combine(data_relatorio, datetime.time.max).isoformat()
        
        # Obtém as métricas do período
        metricas = self.coletor.listar_metricas(data_inicio=data_inicio, data_fim=data_fim)
        
        # Calcula estatísticas
        estatisticas = self._calcular_estatisticas_periodo(metricas)
        
        # Prepara os dados do relatório
        dados_relatorio = {
            "tipo": "diario",
            "data": data_relatorio.isoformat(),
            "gerado_em": datetime.datetime.now().isoformat(),
            "estatisticas": estatisticas,
            "detalhes": self._preparar_detalhes_metricas(metricas)
        }
        
        # Gera o nome do arquivo
        nome_arquivo = f"relatorio_diario_{data_relatorio.isoformat()}"
        
        # Exporta o relatório no formato solicitado
        caminho_arquivo = self._exportar_relatorio(dados_relatorio, nome_arquivo, formato)
        
        self.log.info("Relatório diário gerado", 
                     data=data_relatorio.isoformat(), 
                     formato=formato,
                     arquivo=caminho_arquivo)
        
        return caminho_arquivo
    
    def gerar_relatorio_periodo(self, 
                               data_inicio: str, 
                               data_fim: str, 
                               formato: str = "json") -> str:
        """
        Gera um relatório para um período específico.
        
        Args:
            data_inicio (str): Data de início no formato ISO (YYYY-MM-DD)
            data_fim (str): Data de fim no formato ISO (YYYY-MM-DD)
            formato (str): Formato de saída (json, csv, html, markdown, excel)
            
        Returns:
            str: Caminho do arquivo de relatório gerado
        """
        # Converte as datas para objetos datetime
        data_inicio_dt = datetime.datetime.fromisoformat(data_inicio)
        data_fim_dt = datetime.datetime.fromisoformat(data_fim)
        
        # Ajusta para início e fim do dia
        data_inicio_iso = datetime.datetime.combine(data_inicio_dt.date(), datetime.time.min).isoformat()
        data_fim_iso = datetime.datetime.combine(data_fim_dt.date(), datetime.time.max).isoformat()
        
        # Obtém as métricas do período
        metricas = self.coletor.listar_metricas(data_inicio=data_inicio_iso, data_fim=data_fim_iso)
        
        # Calcula estatísticas
        estatisticas = self._calcular_estatisticas_periodo(metricas)
        
        # Prepara os dados do relatório
        dados_relatorio = {
            "tipo": "periodo",
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "gerado_em": datetime.datetime.now().isoformat(),
            "estatisticas": estatisticas,
            "detalhes": self._preparar_detalhes_metricas(metricas)
        }
        
        # Gera o nome do arquivo
        nome_arquivo = f"relatorio_periodo_{data_inicio_dt.date().isoformat()}_{data_fim_dt.date().isoformat()}"
        
        # Exporta o relatório no formato solicitado
        caminho_arquivo = self._exportar_relatorio(dados_relatorio, nome_arquivo, formato)
        
        self.log.info("Relatório de período gerado", 
                     data_inicio=data_inicio, 
                     data_fim=data_fim,
                     formato=formato,
                     arquivo=caminho_arquivo)
        
        return caminho_arquivo
    
    def gerar_relatorio_desempenho(self, formato: str = "json") -> str:
        """
        Gera um relatório de desempenho geral do sistema.
        
        Args:
            formato (str): Formato de saída (json, csv, html, markdown, excel)
            
        Returns:
            str: Caminho do arquivo de relatório gerado
        """
        # Obtém todas as métricas
        metricas = self.coletor.listar_metricas()
        
        # Calcula estatísticas gerais
        estatisticas = self.coletor.calcular_estatisticas()
        
        # Calcula estatísticas por dia
        estatisticas_diarias = self._calcular_estatisticas_diarias(metricas)
        
        # Prepara os dados do relatório
        dados_relatorio = {
            "tipo": "desempenho",
            "gerado_em": datetime.datetime.now().isoformat(),
            "estatisticas_gerais": estatisticas,
            "estatisticas_diarias": estatisticas_diarias,
            "metricas_chave": {
                "pdfs_por_hora": estatisticas["pdfs_por_hora"],
                "tempo_medio_processamento": estatisticas["tempo_medio_processamento"],
                "taxa_sucesso": estatisticas["status"].get("sucesso", {}).get("percentual", 0) if "sucesso" in estatisticas["status"] else 0
            }
        }
        
        # Gera o nome do arquivo
        nome_arquivo = f"relatorio_desempenho_{datetime.datetime.now().date().isoformat()}"
        
        # Exporta o relatório no formato solicitado
        caminho_arquivo = self._exportar_relatorio(dados_relatorio, nome_arquivo, formato)
        
        # Gera gráficos para o relatório
        self._gerar_graficos_desempenho(dados_relatorio, nome_arquivo)
        
        self.log.info("Relatório de desempenho gerado", 
                     formato=formato,
                     arquivo=caminho_arquivo)
        
        return caminho_arquivo
    
    def gerar_relatorio_wo(self, numero_wo: str, formato: str = "json") -> str:
        """
        Gera um relatório detalhado para uma WO específica.
        
        Args:
            numero_wo (str): Número da WO
            formato (str): Formato de saída (json, csv, html, markdown, excel)
            
        Returns:
            str: Caminho do arquivo de relatório gerado
        """
        # Obtém as métricas da WO
        metrica = self.coletor.obter_metrica(numero_wo)
        
        if not metrica:
            self.log.error("WO não encontrada para gerar relatório", 
                          numero_wo=numero_wo)
            return None
        
        # Prepara os dados do relatório
        dados_relatorio = {
            "tipo": "wo",
            "numero_wo": numero_wo,
            "gerado_em": datetime.datetime.now().isoformat(),
            "dados": metrica,
            "resumo": {
                "nome_arquivo": metrica.get("nome_arquivo", ""),
                "status": metrica.get("status", ""),
                "tempo_total": metrica.get("tempo_total", 0),
                "paginas": metrica.get("paginas", 0),
                "tamanho_arquivo": metrica.get("tamanho_arquivo", 0),
                "inicio": metrica.get("timestamp_inicio", ""),
                "fim": metrica.get("timestamp_fim", "")
            }
        }
        
        # Adiciona análise de etapas
        if "etapas" in metrica:
            etapas_resumo = {}
            for nome_etapa, dados_etapa in metrica["etapas"].items():
                etapas_resumo[nome_etapa] = {
                    "status": dados_etapa.get("status", ""),
                    "duracao": dados_etapa.get("duracao", 0),
                    "timestamp": dados_etapa.get("timestamp", "")
                }
            
            dados_relatorio["etapas"] = etapas_resumo
        
        # Gera o nome do arquivo
        nome_arquivo = f"relatorio_wo_{numero_wo}"
        
        # Exporta o relatório no formato solicitado
        caminho_arquivo = self._exportar_relatorio(dados_relatorio, nome_arquivo, formato)
        
        self.log.info("Relatório de WO gerado", 
                     numero_wo=numero_wo,
                     formato=formato,
                     arquivo=caminho_arquivo)
        
        return caminho_arquivo
    
    def _calcular_estatisticas_periodo(self, metricas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas para um conjunto de métricas.
        
        Args:
            metricas (list): Lista de métricas
            
        Returns:
            dict: Estatísticas calculadas
        """
        if not metricas:
            return {
                "total_processados": 0,
                "status": {},
                "tempo_medio_processamento": 0,
                "paginas_processadas": 0,
                "tamanho_medio": 0
            }
        
        # Contadores e acumuladores
        total = len(metricas)
        status_counter = Counter(m.get("status", "desconhecido") for m in metricas)
        tempo_total = sum(m.get("tempo_total", 0) for m in metricas if "tempo_total" in m)
        paginas_total = sum(m.get("paginas", 0) for m in metricas if "paginas" in m)
        tamanho_total = sum(m.get("tamanho_arquivo", 0) for m in metricas if "tamanho_arquivo" in m)
        
        # Métricas concluídas (com tempo_total)
        metricas_concluidas = [m for m in metricas if "tempo_total" in m]
        total_concluidos = len(metricas_concluidas)
        
        # Cálculo de médias
        tempo_medio = tempo_total / total_concluidos if total_concluidos > 0 else 0
        tamanho_medio = tamanho_total / total if total > 0 else 0
        
        # Cálculo de taxa de processamento
        pdfs_por_hora = (total_concluidos / (tempo_total / 3600)) if tempo_total > 0 else 0
        
        # Estatísticas por status
        status_stats = {
            status: {
                "quantidade": count,
                "percentual": (count / total) * 100 if total > 0 else 0
            }
            for status, count in status_counter.items()
        }
        
        return {
            "total_processados": total,
            "concluidos": total_concluidos,
            "status": status_stats,
            "tempo_medio_processamento": tempo_medio,
            "paginas_processadas": paginas_total,
            "tamanho_medio": tamanho_medio,
            "pdfs_por_hora": pdfs_por_hora
        }
    
    def _calcular_estatisticas_diarias(self, metricas: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Calcula estatísticas agrupadas por dia.
        
        Args:
            metricas (list): Lista de métricas
            
        Returns:
            dict: Estatísticas diárias
        """
        # Agrupa métricas por dia
        metricas_por_dia = defaultdict(list)
        
        for metrica in metricas:
            if "timestamp_inicio" in metrica:
                data = datetime.datetime.fromisoformat(metrica["timestamp_inicio"]).date().isoformat()
                metricas_por_dia[data].append(metrica)
        
        # Calcula estatísticas para cada dia
        estatisticas_diarias = {}
        for data, metricas_dia in metricas_por_dia.items():
            estatisticas_diarias[data] = self._calcular_estatisticas_periodo(metricas_dia)
        
        return estatisticas_diarias
    
    def _preparar_detalhes_metricas(self, metricas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepara detalhes simplificados das métricas para relatórios.
        
        Args:
            metricas (list): Lista de métricas completas
            
        Returns:
            list: Lista de detalhes simplificados
        """
        detalhes = []
        
        for metrica in metricas:
            detalhe = {
                "numero_wo": metrica.get("numero_wo", ""),
                "nome_arquivo": metrica.get("nome_arquivo", ""),
                "status": metrica.get("status", ""),
                "paginas": metrica.get("paginas", 0),
                "tamanho_arquivo": metrica.get("tamanho_arquivo", 0),
                "tempo_total": metrica.get("tempo_total", 0),
                "inicio": metrica.get("timestamp_inicio", ""),
                "fim": metrica.get("timestamp_fim", "")
            }
            
            detalhes.append(detalhe)
        
        return detalhes
    
    def _exportar_relatorio(self, 
                           dados: Dict[str, Any], 
                           nome_base: str, 
                           formato: str) -> str:
        """
        Exporta um relatório no formato especificado.
        
        Args:
            dados (dict): Dados do relatório
            nome_base (str): Nome base do arquivo
            formato (str): Formato de saída
            
        Returns:
            str: Caminho do arquivo gerado
        """
        if formato not in EXPORT_FORMATS:
            self.log.warning("Formato de exportação não suportado, usando json", 
                            formato=formato)
            formato = "json"
        
        # Define o caminho do arquivo
        caminho_arquivo = os.path.join(self.relatorios_dir, f"{nome_base}.{formato}")
        
        try:
            if formato == "json":
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                    
            elif formato == "csv":
                # Para CSV, precisamos aplainar os dados
                if "detalhes" in dados:
                    df = pd.DataFrame(dados["detalhes"])
                    df.to_csv(caminho_arquivo, index=False)
                else:
                    # Tenta aplainar a estrutura de dados
                    flat_data = self._aplainar_dados(dados)
                    df = pd.DataFrame([flat_data])
                    df.to_csv(caminho_arquivo, index=False)
                    
            elif formato == "html":
                if "detalhes" in dados:
                    df = pd.DataFrame(dados["detalhes"])
                    html_content = f"""
                    <html>
                    <head>
                        <title>Relatório - {dados.get('tipo', 'Desconhecido')}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1 {{ color: #2c3e50; }}
                            table {{ border-collapse: collapse; width: 100%; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        </style>
                    </head>
                    <body>
                        <h1>Relatório - {dados.get('tipo', 'Desconhecido')}</h1>
                        <p>Gerado em: {dados.get('gerado_em', '')}</p>
                        <h2>Estatísticas</h2>
                        <pre>{json.dumps(dados.get('estatisticas', {}), indent=2)}</pre>
                        <h2>Detalhes</h2>
                        {df.to_html()}
                    </body>
                    </html>
                    """
                else:
                    html_content = f"""
                    <html>
                    <head>
                        <title>Relatório - {dados.get('tipo', 'Desconhecido')}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1 {{ color: #2c3e50; }}
                            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; }}
                        </style>
                    </head>
                    <body>
                        <h1>Relatório - {dados.get('tipo', 'Desconhecido')}</h1>
                        <p>Gerado em: {dados.get('gerado_em', '')}</p>
                        <pre>{json.dumps(dados, indent=2)}</pre>
                    </body>
                    </html>
                    """
                
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    f.write(html_content)
                    
            elif formato == "markdown":
                md_content = f"# Relatório - {dados.get('tipo', 'Desconhecido')}\n\n"
                md_content += f"Gerado em: {dados.get('gerado_em', '')}\n\n"
                
                if "estatisticas" in dados:
                    md_content += "## Estatísticas\n\n"
                    
                    stats = dados["estatisticas"]
                    md_content += f"- Total processados: {stats.get('total_processados', 0)}\n"
                    md_content += f"- Concluídos: {stats.get('concluidos', 0)}\n"
                    md_content += f"- Tempo médio de processamento: {stats.get('tempo_medio_processamento', 0):.2f} segundos\n"
                    md_content += f"- Páginas processadas: {stats.get('paginas_processadas', 0)}\n"
                    md_content += f"- PDFs por hora: {stats.get('pdfs_por_hora', 0):.2f}\n\n"
                    
                    if "status" in stats:
                        md_content += "### Status\n\n"
                        for status, dados_status in stats["status"].items():
                            md_content += f"- {status}: {dados_status.get('quantidade', 0)} ({dados_status.get('percentual', 0):.2f}%)\n"
                        md_content += "\n"
                
                if "detalhes" in dados:
                    md_content += "## Detalhes\n\n"
                    
                    # Cria tabela markdown
                    if dados["detalhes"]:
                        df = pd.DataFrame(dados["detalhes"])
                        md_content += tabulate(df, headers="keys", tablefmt="pipe", showindex=False)
                        md_content += "\n\n"
                
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    f.write(md_content)
                    
            elif formato == "excel":
                # Cria um Excel com múltiplas abas
                with pd.ExcelWriter(caminho_arquivo) as writer:
                    # Aba de resumo
                    resumo_data = {
                        "Propriedade": ["Tipo de Relatório", "Gerado em", "Total Processados"],
                        "Valor": [
                            dados.get("tipo", ""),
                            dados.get("gerado_em", ""),
                            dados.get("estatisticas", {}).get("total_processados", 0)
                        ]
                    }
                    pd.DataFrame(resumo_data).to_excel(writer, sheet_name="Resumo", index=False)
                    
                    # Aba de estatísticas
                    if "estatisticas" in dados:
                        stats_flat = self._aplainar_dados(dados["estatisticas"])
                        stats_df = pd.DataFrame([stats_flat])
                        stats_df.to_excel(writer, sheet_name="Estatísticas", index=False)
                    
                    # Aba de detalhes
                    if "detalhes" in dados and dados["detalhes"]:
                        pd.DataFrame(dados["detalhes"]).to_excel(writer, sheet_name="Detalhes", index=False)
            
            return caminho_arquivo
            
        except Exception as e:
            self.log.error("Erro ao exportar relatório", 
                          formato=formato, 
                          error=str(e))
            
            # Tenta salvar como JSON em caso de erro
            fallback_path = os.path.join(self.relatorios_dir, f"{nome_base}_fallback.json")
            try:
                with open(fallback_path, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                return fallback_path
            except:
                return None
    
    def _aplainar_dados(self, dados: Dict[str, Any], prefixo: str = "") -> Dict[str, Any]:
        """
        Aplaina uma estrutura de dados aninhada para formato tabular.
        
        Args:
            dados (dict): Dados aninhados
            prefixo (str): Prefixo para as chaves
            
        Returns:
            dict: Dados aplainados
        """
        resultado = {}
        
        for chave, valor in dados.items():
            chave_completa = f"{prefixo}_{chave}" if prefixo else chave
            
            if isinstance(valor, dict) and not any(isinstance(v, (dict, list)) for v in valor.values()):
                # Dicionário simples, aplaina
                for sub_chave, sub_valor in valor.items():
                    resultado[f"{chave_completa}_{sub_chave}"] = sub_valor
            elif isinstance(valor, dict):
                # Dicionário complexo, recursão
                sub_resultado = self._aplainar_dados(valor, chave_completa)
                resultado.update(sub_resultado)
            elif isinstance(valor, list) and all(isinstance(item, (int, float, str, bool, type(None))) for item in valor):
                # Lista de valores simples
                resultado[chave_completa] = ", ".join(str(item) for item in valor)
            elif not isinstance(valor, (list, dict)):
                # Valor simples
                resultado[chave_completa] = valor
        
        return resultado
    
    def _gerar_graficos_desempenho(self, dados: Dict[str, Any], nome_base: str) -> List[str]:
        """
        Gera gráficos para o relatório de desempenho.
        
        Args:
            dados (dict): Dados do relatório
            nome_base (str): Nome base para os arquivos
            
        Returns:
            list: Lista de caminhos dos gráficos gerados
        """
        caminhos_graficos = []
        
        try:
            # Gráfico de status
            if "estatisticas_gerais" in dados and "status" in dados["estatisticas_gerais"]:
                status_data = dados["estatisticas_gerais"]["status"]
                
                if status_data:
                    status_labels = list(status_data.keys())
                    status_values = [s["quantidade"] for s in status_data.values()]
                    
                    plt.figure(figsize=(10, 6))
                    plt.pie(status_values, labels=status_labels, autopct='%1.1f%%', startangle=90)
                    plt.axis('equal')
                    plt.title('Distribuição de Status')
                    
                    caminho_grafico = os.path.join(self.graficos_dir, f"{nome_base}_status_pie.png")
                    plt.savefig(caminho_grafico)
                    plt.close()
                    
                    caminhos_graficos.append(caminho_grafico)
            
            # Gráfico de desempenho diário
            if "estatisticas_diarias" in dados:
                estatisticas_diarias = dados["estatisticas_diarias"]
                
                if estatisticas_diarias:
                    datas = list(estatisticas_diarias.keys())
                    datas.sort()  # Ordena as datas
                    
                    # Extrai dados para o gráfico
                    total_por_dia = [estatisticas_diarias[d]["total_processados"] for d in datas]
                    tempo_medio_por_dia = [estatisticas_diarias[d]["tempo_medio_processamento"] for d in datas]
                    
                    # Cria gráfico de barras para total processado por dia
                    plt.figure(figsize=(12, 6))
                    plt.bar(datas, total_por_dia, color='skyblue')
                    plt.xlabel('Data')
                    plt.ylabel('Total Processado')
                    plt.title('Total de PDFs Processados por Dia')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    caminho_grafico = os.path.join(self.graficos_dir, f"{nome_base}_total_diario.png")
                    plt.savefig(caminho_grafico)
                    plt.close()
                    
                    caminhos_graficos.append(caminho_grafico)
                    
                    # Cria gráfico de linha para tempo médio por dia
                    plt.figure(figsize=(12, 6))
                    plt.plot(datas, tempo_medio_por_dia, marker='o', linestyle='-', color='orange')
                    plt.xlabel('Data')
                    plt.ylabel('Tempo Médio (segundos)')
                    plt.title('Tempo Médio de Processamento por Dia')
                    plt.xticks(rotation=45)
                    plt.grid(True, linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    
                    caminho_grafico = os.path.join(self.graficos_dir, f"{nome_base}_tempo_medio_diario.png")
                    plt.savefig(caminho_grafico)
                    plt.close()
                    
                    caminhos_graficos.append(caminho_grafico)
            
            return caminhos_graficos
            
        except Exception as e:
            self.log.error("Erro ao gerar gráficos", error=str(e))
            return caminhos_graficos


# --- Funções de utilidade ---
def inicializar_sistema_metricas(storage_dir: Optional[str] = None) -> Tuple[MetricasColetorPDF, RelatoriosGeradorPDF]:
    """
    Inicializa o sistema completo de métricas e relatórios.
    
    Args:
        storage_dir (str, optional): Diretório para armazenamento.
            Se None, usa o diretório padrão.
            
    Returns:
        tuple: (coletor_metricas, gerador_relatorios)
    """
    # Inicializa o coletor de métricas
    coletor = MetricasColetorPDF(storage_dir)
    
    # Inicializa o gerador de relatórios
    gerador = RelatoriosGeradorPDF(coletor)
    
    return coletor, gerador

def registrar_metrica_simples(numero_wo: str, 
                             nome_arquivo: str, 
                             status: str, 
                             tempo_total: float,
                             tamanho_kb: float,
                             paginas: int,
                             storage_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Registra uma métrica simplificada em uma única chamada.
    
    Args:
        numero_wo (str): Número da WO
        nome_arquivo (str): Nome do arquivo PDF
        status (str): Status final (sucesso, erro, etc.)
        tempo_total (float): Tempo total de processamento em segundos
        tamanho_kb (float): Tamanho do arquivo em KB
        paginas (int): Número de páginas do PDF
        storage_dir (str, optional): Diretório para armazenamento
        
    Returns:
        dict: Dados da métrica registrada
    """
    # Inicializa o coletor
    coletor = MetricasColetorPDF(storage_dir)
    
    # Registra início
    coletor.registrar_inicio_processamento(
        numero_wo=numero_wo,
        nome_arquivo=nome_arquivo,
        tamanho_arquivo=tamanho_kb,
        paginas=paginas
    )
    
    # Registra conclusão
    resultado = coletor.registrar_conclusao(
        numero_wo=numero_wo,
        status_final=status,
        tempo_total=tempo_total,
        detalhes={"registro_simplificado": True}
    )
    
    return resultado

def gerar_relatorio_completo(data_inicio: Optional[str] = None, 
                            data_fim: Optional[str] = None,
                            formato: str = "html",
                            storage_dir: Optional[str] = None) -> str:
    """
    Gera um relatório completo de desempenho com gráficos.
    
    Args:
        data_inicio (str, optional): Data de início no formato ISO
        data_fim (str, optional): Data de fim no formato ISO
        formato (str): Formato de saída
        storage_dir (str, optional): Diretório para armazenamento
        
    Returns:
        str: Caminho do relatório gerado
    """
    # Inicializa o sistema
    coletor, gerador = inicializar_sistema_metricas(storage_dir)
    
    # Define o período
    if data_inicio is None and data_fim is None:
        # Relatório de desempenho geral
        return gerador.gerar_relatorio_desempenho(formato=formato)
    elif data_inicio is not None and data_fim is None:
        # Relatório diário
        return gerador.gerar_relatorio_diario(data=data_inicio, formato=formato)
    else:
        # Relatório de período
        return gerador.gerar_relatorio_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            formato=formato
        )

# --- Função principal para testes ---
if __name__ == "__main__":
    # Exemplo de uso
    print("Sistema de Relatórios e Métricas de Desempenho")
    print("Módulo para importação - não possui função principal")
