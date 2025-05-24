#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_dashboard_monitoramento_pdfs.py
Testes unitários para o módulo de dashboard de monitoramento de PDFs.

Este módulo contém testes unitários para validar as funcionalidades do
dashboard de monitoramento de PDFs, incluindo métricas em tempo real,
histórico de processamento, alertas e relatórios.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import unittest
import tempfile
import datetime
from unittest.mock import patch, MagicMock, Mock
import threading
import time

# Mock para os módulos externos
import sys
sys.modules['M2_Orquestrador_PDFs'] = MagicMock()
sys.modules['M7_Relatorios_Metricas'] = MagicMock()
sys.modules['M8_Alertas_Condicoes_Criticas'] = MagicMock()
sys.modules['M6_Notificacao_Status'] = MagicMock()

# Importação do módulo a ser testado
from M9_Dashboard_Monitoramento_PDFs import (
    DashboardMonitoramento,
    inicializar_dashboard,
    iniciar_monitoramento_automatico
)


class TestDashboardMonitoramento(unittest.TestCase):
    """Testes para a classe DashboardMonitoramento."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        
        # Inicializa dashboard em modo simulação
        self.dashboard = DashboardMonitoramento(
            storage_dir=self.temp_dir,
            modo_simulacao=True
        )
        
        # Patch para evitar loops infinitos ou esperas longas
        self.original_loop = self.dashboard._loop_monitoramento
        self.dashboard._loop_monitoramento = self._mock_loop_monitoramento
        
    def _mock_loop_monitoramento(self):
        """Versão mockada do loop de monitoramento para evitar loops infinitos."""
        # Executa apenas uma iteração e retorna
        try:
            # Atualiza métricas em tempo real
            self.dashboard._atualizar_metricas_tempo_real()
            
            # Atualiza histórico de processamento
            self.dashboard._atualizar_historico_processamento()
            
            # Atualiza distribuição de status
            self.dashboard._atualizar_distribuicao_status()
            
            # Atualiza alertas recentes
            self.dashboard._atualizar_alertas_recentes()
            
            # Registra timestamp da última atualização
            self.dashboard.cache_metricas["ultima_atualizacao"] = datetime.datetime.now().isoformat()
            
            # Persiste cache para acesso rápido
            self.dashboard._persistir_cache()
            
        except Exception as e:
            print(f"Erro no loop mockado: {str(e)}")
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Para o monitoramento se estiver ativo
        if self.dashboard.monitoramento_ativo:
            self.dashboard.monitoramento_ativo = False
            if self.dashboard.thread_monitoramento and self.dashboard.thread_monitoramento.is_alive():
                self.dashboard.thread_monitoramento.join(timeout=0.5)
        
        # Remove arquivos temporários
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)
    
    def test_inicializacao(self):
        """Testa a inicialização do dashboard."""
        # Verifica se o dashboard foi inicializado corretamente
        self.assertIsNotNone(self.dashboard)
        self.assertEqual(self.dashboard.storage_dir, self.temp_dir)
        self.assertTrue(self.dashboard.modo_simulacao)
        self.assertFalse(self.dashboard.monitoramento_ativo)
        
        # Verifica se os diretórios foram criados
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "metricas")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "historico")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "cache")))
    
    @patch('threading.Thread')
    def test_iniciar_parar_monitoramento(self, mock_thread):
        """Testa iniciar e parar o monitoramento."""
        # Mock para Thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Inicia monitoramento
        resultado = self.dashboard.iniciar_monitoramento()
        self.assertTrue(resultado)
        self.assertTrue(self.dashboard.monitoramento_ativo)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Tenta iniciar novamente (deve falhar)
        resultado = self.dashboard.iniciar_monitoramento()
        self.assertFalse(resultado)
        
        # Para monitoramento
        resultado = self.dashboard.parar_monitoramento()
        self.assertTrue(resultado)
        self.assertFalse(self.dashboard.monitoramento_ativo)
        
        # Tenta parar novamente (deve falhar)
        resultado = self.dashboard.parar_monitoramento()
        self.assertFalse(resultado)
    
    def test_gerar_metricas_simuladas(self):
        """Testa a geração de métricas simuladas."""
        metricas = self.dashboard._gerar_metricas_simuladas()
        
        # Verifica se as métricas foram geradas corretamente
        self.assertIsInstance(metricas, dict)
        self.assertIn("pdfs_processados", metricas)
        self.assertIn("pdfs_na_fila", metricas)
        self.assertIn("pdfs_com_erro", metricas)
        self.assertIn("pdfs_com_sucesso", metricas)
        self.assertIn("tempo_medio_processamento", metricas)
        self.assertIn("tempo_total_processamento", metricas)
        self.assertIn("taxa_erro", metricas)
        self.assertIn("uso_cpu", metricas)
        self.assertIn("uso_memoria", metricas)
        self.assertIn("pdfs_por_hora", metricas)
        self.assertIn("status_sistema", metricas)
        
        # Verifica tipos de dados
        self.assertIsInstance(metricas["pdfs_processados"], int)
        self.assertIsInstance(metricas["tempo_medio_processamento"], float)
        self.assertIsInstance(metricas["status_sistema"], str)
    
    def test_gerar_item_historico_simulado(self):
        """Testa a geração de itens de histórico simulados."""
        item = self.dashboard._gerar_item_historico_simulado()
        
        # Verifica se o item foi gerado corretamente
        self.assertIsInstance(item, dict)
        self.assertIn("id", item)
        self.assertIn("tipo_documento", item)
        self.assertIn("status", item)
        self.assertIn("tempo_processamento", item)
        self.assertIn("timestamp", item)
        self.assertIn("usuario", item)
        self.assertIn("tamanho_kb", item)
        
        # Verifica tipos de dados
        self.assertIsInstance(item["id"], str)
        self.assertIsInstance(item["tipo_documento"], str)
        self.assertIsInstance(item["status"], str)
        self.assertIsInstance(item["tempo_processamento"], float)
        self.assertIsInstance(item["timestamp"], str)
    
    def test_gerar_distribuicao_simulada(self):
        """Testa a geração de distribuição simulada."""
        distribuicao = self.dashboard._gerar_distribuicao_simulada()
        
        # Verifica se a distribuição foi gerada corretamente
        self.assertIsInstance(distribuicao, dict)
        self.assertIn("por_status", distribuicao)
        self.assertIn("por_tipo_documento", distribuicao)
        self.assertIn("total_documentos", distribuicao)
        
        # Verifica estrutura de por_status
        self.assertIn("em_processamento", distribuicao["por_status"])
        self.assertIn("na_fila", distribuicao["por_status"])
        self.assertIn("com_erro", distribuicao["por_status"])
        self.assertIn("concluidos", distribuicao["por_status"])
        
        # Verifica tipos de documentos
        self.assertIsInstance(distribuicao["por_tipo_documento"], dict)
        self.assertTrue(len(distribuicao["por_tipo_documento"]) > 0)
    
    def test_gerar_alerta_simulado(self):
        """Testa a geração de alertas simulados."""
        alerta = self.dashboard._gerar_alerta_simulado()
        
        # Verifica se o alerta foi gerado corretamente
        self.assertIsInstance(alerta, dict)
        self.assertIn("id", alerta)
        self.assertIn("tipo_condicao", alerta)
        self.assertIn("nivel", alerta)
        self.assertIn("mensagem", alerta)
        self.assertIn("valor_atual", alerta)
        self.assertIn("valor_limite", alerta)
        self.assertIn("componente", alerta)
        self.assertIn("timestamp", alerta)
        
        # Verifica tipos de dados
        self.assertIsInstance(alerta["id"], str)
        self.assertIsInstance(alerta["tipo_condicao"], str)
        self.assertIsInstance(alerta["nivel"], str)
        self.assertIsInstance(alerta["mensagem"], str)
        self.assertIsInstance(alerta["timestamp"], str)
    
    def test_atualizar_metricas_tempo_real(self):
        """Testa a atualização de métricas em tempo real."""
        # Verifica estado inicial
        self.assertEqual(self.dashboard.cache_metricas["metricas_tempo_real"], {})
        
        # Atualiza métricas
        self.dashboard._atualizar_metricas_tempo_real()
        
        # Verifica se as métricas foram atualizadas
        self.assertNotEqual(self.dashboard.cache_metricas["metricas_tempo_real"], {})
        self.assertIn("pdfs_processados", self.dashboard.cache_metricas["metricas_tempo_real"])
    
    def test_atualizar_historico_processamento(self):
        """Testa a atualização do histórico de processamento."""
        # Verifica estado inicial
        self.assertEqual(self.dashboard.cache_metricas["historico_processamento"], [])
        
        # Atualiza histórico
        self.dashboard._atualizar_historico_processamento()
        
        # Verifica se o histórico foi atualizado
        self.assertEqual(len(self.dashboard.cache_metricas["historico_processamento"]), 1)
        self.assertIsInstance(self.dashboard.cache_metricas["historico_processamento"][0], dict)
    
    def test_atualizar_distribuicao_status(self):
        """Testa a atualização da distribuição de status."""
        # Verifica estado inicial
        self.assertEqual(self.dashboard.cache_metricas["distribuicao_status"], {})
        
        # Atualiza distribuição
        self.dashboard._atualizar_distribuicao_status()
        
        # Verifica se a distribuição foi atualizada
        self.assertNotEqual(self.dashboard.cache_metricas["distribuicao_status"], {})
        self.assertIn("por_status", self.dashboard.cache_metricas["distribuicao_status"])
    
    def test_atualizar_alertas_recentes(self):
        """Testa a atualização de alertas recentes."""
        # Configura alta probabilidade de alerta para teste
        self.dashboard.config["simulacao"]["probabilidade_alerta"] = 1.0
        
        # Verifica estado inicial
        self.assertEqual(self.dashboard.cache_metricas["alertas_recentes"], [])
        
        # Atualiza alertas
        self.dashboard._atualizar_alertas_recentes()
        
        # Verifica se os alertas foram atualizados
        self.assertEqual(len(self.dashboard.cache_metricas["alertas_recentes"]), 1)
        self.assertIsInstance(self.dashboard.cache_metricas["alertas_recentes"][0], dict)
    
    def test_persistir_cache(self):
        """Testa a persistência do cache."""
        # Adiciona dados ao cache
        self.dashboard.cache_metricas["metricas_tempo_real"] = {"teste": 123}
        self.dashboard.cache_metricas["ultima_atualizacao"] = datetime.datetime.now().isoformat()
        
        # Persiste cache
        self.dashboard._persistir_cache()
        
        # Verifica se o arquivo de cache foi criado
        cache_file = os.path.join(self.temp_dir, "cache", "dashboard_cache.json")
        self.assertTrue(os.path.exists(cache_file))
        
        # Verifica conteúdo do cache
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        self.assertIn("metricas_tempo_real", cache_data)
        self.assertEqual(cache_data["metricas_tempo_real"]["teste"], 123)
    
    def test_obter_metricas_tempo_real(self):
        """Testa a obtenção de métricas em tempo real."""
        # Adiciona dados ao cache
        self.dashboard.cache_metricas["metricas_tempo_real"] = {"teste": 123}
        
        # Obtém métricas
        metricas = self.dashboard.obter_metricas_tempo_real()
        
        # Verifica resultado
        self.assertEqual(metricas, {"teste": 123})
    
    def test_obter_historico_processamento(self):
        """Testa a obtenção do histórico de processamento."""
        # Adiciona dados ao cache
        self.dashboard.cache_metricas["historico_processamento"] = [
            {"id": "1", "status": "sucesso", "tipo_documento": "Contrato"},
            {"id": "2", "status": "erro", "tipo_documento": "Nota Fiscal"},
            {"id": "3", "status": "sucesso", "tipo_documento": "Relatório"}
        ]
        
        # Testa sem filtros
        historico = self.dashboard.obter_historico_processamento()
        self.assertEqual(len(historico), 3)
        
        # Testa com limite
        historico = self.dashboard.obter_historico_processamento(limite=2)
        self.assertEqual(len(historico), 2)
        
        # Testa com offset
        historico = self.dashboard.obter_historico_processamento(offset=1)
        self.assertEqual(len(historico), 2)
        self.assertEqual(historico[0]["id"], "2")
        
        # Testa com filtros
        historico = self.dashboard.obter_historico_processamento(
            filtros={"status": "sucesso"}
        )
        self.assertEqual(len(historico), 2)
        self.assertEqual(historico[0]["status"], "sucesso")
        
        # Testa com filtros de lista
        historico = self.dashboard.obter_historico_processamento(
            filtros={"tipo_documento": ["Contrato", "Relatório"]}
        )
        self.assertEqual(len(historico), 2)
    
    def test_obter_distribuicao_status(self):
        """Testa a obtenção da distribuição de status."""
        # Adiciona dados ao cache
        self.dashboard.cache_metricas["distribuicao_status"] = {"teste": 123}
        
        # Obtém distribuição
        distribuicao = self.dashboard.obter_distribuicao_status()
        
        # Verifica resultado
        self.assertEqual(distribuicao, {"teste": 123})
    
    def test_obter_alertas_recentes(self):
        """Testa a obtenção de alertas recentes."""
        # Adiciona dados ao cache
        self.dashboard.cache_metricas["alertas_recentes"] = [
            {"id": "1", "nivel": "aviso", "tipo_condicao": "tempo_processamento"},
            {"id": "2", "nivel": "critico", "tipo_condicao": "uso_memoria"},
            {"id": "3", "nivel": "aviso", "tipo_condicao": "uso_cpu"}
        ]
        
        # Testa sem filtros
        alertas = self.dashboard.obter_alertas_recentes()
        self.assertEqual(len(alertas), 3)
        
        # Testa com limite
        alertas = self.dashboard.obter_alertas_recentes(limite=2)
        self.assertEqual(len(alertas), 2)
        
        # Testa com filtro de nível
        alertas = self.dashboard.obter_alertas_recentes(nivel="aviso")
        self.assertEqual(len(alertas), 2)
        self.assertEqual(alertas[0]["nivel"], "aviso")
        
        # Testa com filtro de tipo
        alertas = self.dashboard.obter_alertas_recentes(tipo="uso_memoria")
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["tipo_condicao"], "uso_memoria")
    
    def test_gerar_relatorio_desempenho(self):
        """Testa a geração de relatório de desempenho."""
        # Testa formato JSON
        relatorio_json = self.dashboard.gerar_relatorio_desempenho(
            periodo="dia",
            formato="json"
        )
        self.assertIsInstance(relatorio_json, str)
        dados_json = json.loads(relatorio_json)
        self.assertIn("periodo", dados_json)
        self.assertIn("dados", dados_json)
        
        # Testa formato CSV
        relatorio_csv = self.dashboard.gerar_relatorio_desempenho(
            periodo="dia",
            formato="csv"
        )
        self.assertIsInstance(relatorio_csv, str)
        self.assertIn("timestamp,intervalo,pdfs_processados", relatorio_csv)
        
        # Testa formato HTML
        relatorio_html = self.dashboard.gerar_relatorio_desempenho(
            periodo="dia",
            formato="html"
        )
        self.assertIsInstance(relatorio_html, str)
        self.assertIn("<!DOCTYPE html>", relatorio_html)
        
        # Testa formato Markdown
        relatorio_md = self.dashboard.gerar_relatorio_desempenho(
            periodo="dia",
            formato="markdown"
        )
        self.assertIsInstance(relatorio_md, str)
        self.assertIn("# Relatório de Desempenho", relatorio_md)
    
    def test_mesclar_dicts(self):
        """Testa a mesclagem de dicionários."""
        # Dicionários de teste
        dict_base = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        
        dict_novo = {
            "a": 10,
            "b": {
                "c": 20,
                "e": 30
            },
            "f": 40
        }
        
        # Mescla dicionários
        self.dashboard._mesclar_dicts(dict_base, dict_novo)
        
        # Verifica resultado
        self.assertEqual(dict_base["a"], 10)
        self.assertEqual(dict_base["b"]["c"], 20)
        self.assertEqual(dict_base["b"]["d"], 3)
        self.assertEqual(dict_base["b"]["e"], 30)
        self.assertEqual(dict_base["f"], 40)


class TestFuncoesUtilidade(unittest.TestCase):
    """Testes para as funções de utilidade."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch para evitar loops infinitos
        self.patcher = patch('M9_Dashboard_Monitoramento_PDFs.DashboardMonitoramento._loop_monitoramento')
        self.mock_loop = self.patcher.start()
        
        # Configura o mock para não fazer nada
        self.mock_loop.return_value = None
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o patch
        self.patcher.stop()
        
        # Remove arquivos temporários
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)
    
    def test_inicializar_dashboard(self):
        """Testa a função inicializar_dashboard."""
        # Inicializa dashboard
        dashboard = inicializar_dashboard(
            storage_dir=self.temp_dir,
            modo_simulacao=True
        )
        
        # Verifica se o dashboard foi inicializado corretamente
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.storage_dir, self.temp_dir)
        self.assertTrue(dashboard.modo_simulacao)
        self.assertFalse(dashboard.monitoramento_ativo)
    
    @patch('threading.Thread')
    def test_iniciar_monitoramento_automatico(self, mock_thread):
        """Testa a função iniciar_monitoramento_automatico."""
        # Mock para Thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Inicializa dashboard e inicia monitoramento
        dashboard = iniciar_monitoramento_automatico(
            storage_dir=self.temp_dir,
            modo_simulacao=True
        )
        
        # Verifica se o dashboard foi inicializado e o monitoramento iniciado
        self.assertIsNotNone(dashboard)
        self.assertTrue(dashboard.monitoramento_ativo)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Para o monitoramento para limpeza
        dashboard.monitoramento_ativo = False


if __name__ == "__main__":
    unittest.main()
