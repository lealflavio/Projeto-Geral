#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_relatorios_metricas.py
Testes unitários para o sistema de relatórios e métricas de desempenho.

Este módulo implementa testes unitários para validar o funcionamento do sistema
de coleta, análise e visualização de métricas de desempenho do processamento de PDFs.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from M7_Relatorios_Metricas import (
    MetricasColetorPDF,
    RelatoriosGeradorPDF,
    inicializar_sistema_metricas,
    registrar_metrica_simples,
    gerar_relatorio_completo
)

class TestMetricasColetorPDF(unittest.TestCase):
    """Testes para a classe MetricasColetorPDF."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria um diretório temporário para os testes
        self.test_dir = tempfile.mkdtemp()
        self.coletor = MetricasColetorPDF(storage_dir=self.test_dir)
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
    
    def test_registrar_inicio_processamento(self):
        """Testa o registro de início de processamento."""
        # Registra o início do processamento
        registro = self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste.pdf",
            tamanho_arquivo=1024.5,
            paginas=10,
            metadados={"autor": "Teste"}
        )
        
        # Verifica se o registro foi criado corretamente
        self.assertEqual(registro["numero_wo"], "WO123")
        self.assertEqual(registro["nome_arquivo"], "teste.pdf")
        self.assertEqual(registro["tamanho_arquivo"], 1024.5)
        self.assertEqual(registro["paginas"], 10)
        self.assertEqual(registro["status"], "iniciado")
        self.assertEqual(registro["metadados"]["autor"], "Teste")
        self.assertIn("timestamp_inicio", registro)
        self.assertIn("etapas", registro)
        self.assertIn("inicio", registro["etapas"])
        
        # Verifica se o arquivo foi salvo
        metricas_dir = os.path.join(self.test_dir, "metricas")
        self.assertTrue(os.path.exists(metricas_dir))
        self.assertTrue(os.path.exists(os.path.join(metricas_dir, "WO123.json")))
    
    def test_registrar_etapa(self):
        """Testa o registro de uma etapa de processamento."""
        # Registra o início do processamento
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        # Registra uma etapa
        registro = self.coletor.registrar_etapa(
            numero_wo="WO123",
            nome_etapa="extracao",
            status="concluido",
            duracao=5.2,
            detalhes={"campos_extraidos": 15}
        )
        
        # Verifica se a etapa foi registrada corretamente
        self.assertIn("etapas", registro)
        self.assertIn("extracao", registro["etapas"])
        self.assertEqual(registro["etapas"]["extracao"]["status"], "concluido")
        self.assertEqual(registro["etapas"]["extracao"]["duracao"], 5.2)
        self.assertEqual(registro["etapas"]["extracao"]["detalhes"]["campos_extraidos"], 15)
    
    def test_registrar_conclusao(self):
        """Testa o registro de conclusão de processamento."""
        # Registra o início do processamento
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        # Registra a conclusão
        registro = self.coletor.registrar_conclusao(
            numero_wo="WO123",
            status_final="sucesso",
            tempo_total=15.7,
            detalhes={"campos_validados": True}
        )
        
        # Verifica se a conclusão foi registrada corretamente
        self.assertEqual(registro["status"], "sucesso")
        self.assertEqual(registro["tempo_total"], 15.7)
        self.assertIn("timestamp_fim", registro)
        self.assertTrue(registro["detalhes_conclusao"]["campos_validados"])
        self.assertIn("etapas", registro)
        self.assertIn("conclusao", registro["etapas"])
    
    def test_obter_metrica(self):
        """Testa a obtenção de uma métrica específica."""
        # Registra o início e conclusão do processamento
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO123",
            status_final="sucesso",
            tempo_total=15.7
        )
        
        # Obtém a métrica
        metrica = self.coletor.obter_metrica("WO123")
        
        # Verifica se a métrica foi obtida corretamente
        self.assertEqual(metrica["numero_wo"], "WO123")
        self.assertEqual(metrica["nome_arquivo"], "teste.pdf")
        self.assertEqual(metrica["status"], "sucesso")
        self.assertEqual(metrica["tempo_total"], 15.7)
    
    def test_listar_metricas(self):
        """Testa a listagem de métricas com filtros."""
        # Registra múltiplas métricas
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste1.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO123",
            status_final="sucesso",
            tempo_total=15.7
        )
        
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO456",
            nome_arquivo="teste2.pdf",
            tamanho_arquivo=2048.3,
            paginas=20
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO456",
            status_final="erro",
            tempo_total=8.2
        )
        
        # Lista todas as métricas
        metricas = self.coletor.listar_metricas()
        self.assertEqual(len(metricas), 2)
        
        # Lista métricas com filtro de status
        metricas_sucesso = self.coletor.listar_metricas(filtro_status="sucesso")
        self.assertEqual(len(metricas_sucesso), 1)
        self.assertEqual(metricas_sucesso[0]["numero_wo"], "WO123")
        
        metricas_erro = self.coletor.listar_metricas(filtro_status="erro")
        self.assertEqual(len(metricas_erro), 1)
        self.assertEqual(metricas_erro[0]["numero_wo"], "WO456")
    
    def test_calcular_estatisticas(self):
        """Testa o cálculo de estatísticas gerais."""
        # Registra múltiplas métricas
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="teste1.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO123",
            status_final="sucesso",
            tempo_total=15.7
        )
        
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO456",
            nome_arquivo="teste2.pdf",
            tamanho_arquivo=2048.3,
            paginas=20
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO456",
            status_final="erro",
            tempo_total=8.2
        )
        
        # Calcula estatísticas
        estatisticas = self.coletor.calcular_estatisticas()
        
        # Verifica as estatísticas calculadas
        self.assertEqual(estatisticas["total_processados"], 2)
        self.assertEqual(estatisticas["concluidos"], 2)
        self.assertIn("sucesso", estatisticas["status"])
        self.assertIn("erro", estatisticas["status"])
        self.assertEqual(estatisticas["status"]["sucesso"]["quantidade"], 1)
        self.assertEqual(estatisticas["status"]["erro"]["quantidade"], 1)
        self.assertEqual(estatisticas["paginas_processadas"], 30)
        self.assertAlmostEqual(estatisticas["tempo_medio_processamento"], (15.7 + 8.2) / 2, places=2)
        self.assertAlmostEqual(estatisticas["tamanho_medio"], (1024.5 + 2048.3) / 2, places=2)
        self.assertGreater(estatisticas["pdfs_por_hora"], 0)

class TestRelatoriosGeradorPDF(unittest.TestCase):
    """Testes para a classe RelatoriosGeradorPDF."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria um diretório temporário para os testes
        self.test_dir = tempfile.mkdtemp()
        self.coletor = MetricasColetorPDF(storage_dir=self.test_dir)
        self.gerador = RelatoriosGeradorPDF(self.coletor)
        
        # Registra algumas métricas para os testes
        self._registrar_metricas_teste()
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
    
    def _registrar_metricas_teste(self):
        """Registra métricas de teste para os relatórios."""
        # Registra métricas com datas diferentes
        data_hoje = datetime.now()
        data_ontem = data_hoje - timedelta(days=1)
        
        # Métrica de hoje
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO123",
            nome_arquivo="hoje1.pdf",
            tamanho_arquivo=1024.5,
            paginas=10
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO123",
            status_final="sucesso",
            tempo_total=15.7
        )
        
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO124",
            nome_arquivo="hoje2.pdf",
            tamanho_arquivo=2048.3,
            paginas=20
        )
        
        self.coletor.registrar_conclusao(
            numero_wo="WO124",
            status_final="erro",
            tempo_total=8.2
        )
        
        # Simula métricas de ontem (modifica o timestamp manualmente)
        self.coletor.registrar_inicio_processamento(
            numero_wo="WO456",
            nome_arquivo="ontem1.pdf",
            tamanho_arquivo=1536.7,
            paginas=15
        )
        
        # Modifica o timestamp para ontem
        metrica = self.coletor.obter_metrica("WO456")
        metrica["timestamp_inicio"] = data_ontem.isoformat()
        self.coletor._salvar_metrica("WO456", metrica)
        
        self.coletor.registrar_conclusao(
            numero_wo="WO456",
            status_final="sucesso",
            tempo_total=12.3
        )
        
        # Modifica o timestamp para ontem
        metrica = self.coletor.obter_metrica("WO456")
        metrica["timestamp_fim"] = data_ontem.isoformat()
        self.coletor._salvar_metrica("WO456", metrica)
    
    def test_gerar_relatorio_diario(self):
        """Testa a geração de relatório diário."""
        # Gera relatório para hoje
        data_hoje = datetime.now().date().isoformat()
        caminho_relatorio = self.gerador.gerar_relatorio_diario(data=data_hoje, formato="json")
        
        # Verifica se o relatório foi gerado
        self.assertTrue(os.path.exists(caminho_relatorio))
        
        # Verifica o conteúdo do relatório
        with open(caminho_relatorio, "r", encoding="utf-8") as f:
            relatorio = json.load(f)
            
        self.assertEqual(relatorio["tipo"], "diario")
        self.assertEqual(relatorio["data"], data_hoje)
        self.assertEqual(relatorio["estatisticas"]["total_processados"], 2)
        self.assertEqual(len(relatorio["detalhes"]), 2)
    
    def test_gerar_relatorio_periodo(self):
        """Testa a geração de relatório para um período específico."""
        # Define o período (últimos 2 dias)
        data_hoje = datetime.now().date()
        data_ontem = (data_hoje - timedelta(days=1)).isoformat()
        data_hoje = data_hoje.isoformat()
        
        # Gera relatório para o período
        caminho_relatorio = self.gerador.gerar_relatorio_periodo(
            data_inicio=data_ontem,
            data_fim=data_hoje,
            formato="json"
        )
        
        # Verifica se o relatório foi gerado
        self.assertTrue(os.path.exists(caminho_relatorio))
        
        # Verifica o conteúdo do relatório
        with open(caminho_relatorio, "r", encoding="utf-8") as f:
            relatorio = json.load(f)
            
        self.assertEqual(relatorio["tipo"], "periodo")
        self.assertEqual(relatorio["data_inicio"], data_ontem)
        self.assertEqual(relatorio["data_fim"], data_hoje)
        self.assertEqual(relatorio["estatisticas"]["total_processados"], 3)
        self.assertEqual(len(relatorio["detalhes"]), 3)
    
    def test_gerar_relatorio_desempenho(self):
        """Testa a geração de relatório de desempenho geral."""
        # Gera relatório de desempenho
        caminho_relatorio = self.gerador.gerar_relatorio_desempenho(formato="json")
        
        # Verifica se o relatório foi gerado
        self.assertTrue(os.path.exists(caminho_relatorio))
        
        # Verifica o conteúdo do relatório
        with open(caminho_relatorio, "r", encoding="utf-8") as f:
            relatorio = json.load(f)
            
        self.assertEqual(relatorio["tipo"], "desempenho")
        self.assertIn("estatisticas_gerais", relatorio)
        self.assertIn("estatisticas_diarias", relatorio)
        self.assertIn("metricas_chave", relatorio)
        
        # Verifica se os gráficos foram gerados
        graficos_dir = os.path.join(self.test_dir, "graficos")
        self.assertTrue(os.path.exists(graficos_dir))
        self.assertTrue(any(f.endswith(".png") for f in os.listdir(graficos_dir)))
    
    def test_gerar_relatorio_wo(self):
        """Testa a geração de relatório para uma WO específica."""
        # Gera relatório para uma WO
        caminho_relatorio = self.gerador.gerar_relatorio_wo(numero_wo="WO123", formato="json")
        
        # Verifica se o relatório foi gerado
        self.assertTrue(os.path.exists(caminho_relatorio))
        
        # Verifica o conteúdo do relatório
        with open(caminho_relatorio, "r", encoding="utf-8") as f:
            relatorio = json.load(f)
            
        self.assertEqual(relatorio["tipo"], "wo")
        self.assertEqual(relatorio["numero_wo"], "WO123")
        self.assertEqual(relatorio["resumo"]["nome_arquivo"], "hoje1.pdf")
        self.assertEqual(relatorio["resumo"]["status"], "sucesso")
        self.assertEqual(relatorio["resumo"]["tempo_total"], 15.7)
    
    @patch('M7_Relatorios_Metricas.pd.ExcelWriter')
    def test_exportar_relatorio_formatos(self, mock_excel_writer):
        """Testa a exportação de relatórios em diferentes formatos."""
        # Testa formatos que não dependem de bibliotecas externas
        formatos_simples = ["json", "csv", "html", "markdown"]
        
        for formato in formatos_simples:
            # Gera relatório no formato específico
            caminho_relatorio = self.gerador.gerar_relatorio_diario(
                data=datetime.now().date().isoformat(),
                formato=formato
            )
            
            # Verifica se o relatório foi gerado
            self.assertTrue(os.path.exists(caminho_relatorio))
            # Verifica se o caminho contém o formato (não necessariamente como extensão)
            self.assertIn(formato, caminho_relatorio)
        
        # Testa o formato Excel separadamente com mock
        mock_excel_writer.return_value.__enter__.return_value = MagicMock()
        
        caminho_relatorio = self.gerador.gerar_relatorio_diario(
            data=datetime.now().date().isoformat(),
            formato="excel"
        )
        
        # Verifica se o mock foi chamado
        mock_excel_writer.assert_called_once()

class TestFuncoesUtilidade(unittest.TestCase):
    """Testes para as funções de utilidade."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria um diretório temporário para os testes
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
    
    def test_inicializar_sistema_metricas(self):
        """Testa a inicialização do sistema completo."""
        # Inicializa o sistema
        coletor, gerador = inicializar_sistema_metricas(self.test_dir)
        
        # Verifica se as instâncias foram criadas corretamente
        self.assertIsInstance(coletor, MetricasColetorPDF)
        self.assertIsInstance(gerador, RelatoriosGeradorPDF)
        self.assertEqual(coletor.storage_dir, self.test_dir)
    
    def test_registrar_metrica_simples(self):
        """Testa o registro simplificado de métricas."""
        # Registra uma métrica simplificada
        resultado = registrar_metrica_simples(
            numero_wo="WO123",
            nome_arquivo="teste.pdf",
            status="sucesso",
            tempo_total=15.7,
            tamanho_kb=1024.5,
            paginas=10,
            storage_dir=self.test_dir
        )
        
        # Verifica se a métrica foi registrada corretamente
        self.assertEqual(resultado["numero_wo"], "WO123")
        self.assertEqual(resultado["nome_arquivo"], "teste.pdf")
        self.assertEqual(resultado["status"], "sucesso")
        self.assertEqual(resultado["tempo_total"], 15.7)
        
        # Verifica se o arquivo foi salvo
        metricas_dir = os.path.join(self.test_dir, "metricas")
        self.assertTrue(os.path.exists(os.path.join(metricas_dir, "WO123.json")))
    
    @patch("M7_Relatorios_Metricas.RelatoriosGeradorPDF.gerar_relatorio_desempenho")
    @patch("M7_Relatorios_Metricas.RelatoriosGeradorPDF.gerar_relatorio_diario")
    @patch("M7_Relatorios_Metricas.RelatoriosGeradorPDF.gerar_relatorio_periodo")
    def test_gerar_relatorio_completo(self, mock_periodo, mock_diario, mock_desempenho):
        """Testa a geração de relatório completo."""
        # Configura os mocks
        mock_desempenho.return_value = "/path/to/desempenho.html"
        mock_diario.return_value = "/path/to/diario.html"
        mock_periodo.return_value = "/path/to/periodo.html"
        
        # Testa diferentes cenários
        
        # Sem datas (relatório de desempenho)
        resultado = gerar_relatorio_completo(formato="html", storage_dir=self.test_dir)
        mock_desempenho.assert_called_once()
        self.assertEqual(resultado, "/path/to/desempenho.html")
        
        # Com data_inicio apenas (relatório diário)
        data_hoje = datetime.now().date().isoformat()
        resultado = gerar_relatorio_completo(data_inicio=data_hoje, formato="html", storage_dir=self.test_dir)
        mock_diario.assert_called_once_with(data=data_hoje, formato="html")
        self.assertEqual(resultado, "/path/to/diario.html")
        
        # Com data_inicio e data_fim (relatório de período)
        data_ontem = (datetime.now().date() - timedelta(days=1)).isoformat()
        resultado = gerar_relatorio_completo(
            data_inicio=data_ontem,
            data_fim=data_hoje,
            formato="html",
            storage_dir=self.test_dir
        )
        mock_periodo.assert_called_once_with(data_inicio=data_ontem, data_fim=data_hoje, formato="html")
        self.assertEqual(resultado, "/path/to/periodo.html")

if __name__ == "__main__":
    unittest.main()
