#!/usr/bin/env python3
"""
Testes unitários para o extrator otimizado de PDFs.

Este módulo contém testes para validar o funcionamento do extrator
otimizado de PDFs de intervenção técnica.
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Adicionar diretório raiz ao path para importação
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Importar o módulo a ser testado
from M1_Extrator_PDF_Otimizado import ExtratorPDF, extrair_dados_pdf_relevantes

class TestExtratorPDF(unittest.TestCase):
    """Testes para a classe ExtratorPDF."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar diretórios temporários para testes
        self.temp_dir = tempfile.mkdtemp()
        self.saida_dir = os.path.join(self.temp_dir, "extracao_dados")
        self.diagnostico_dir = os.path.join(self.temp_dir, "diagnostico")
        os.makedirs(self.saida_dir, exist_ok=True)
        os.makedirs(self.diagnostico_dir, exist_ok=True)
        
        # Criar um mock para o PDF
        self.mock_pdf_path = os.path.join(self.temp_dir, "teste.pdf")
        with open(self.mock_pdf_path, "w") as f:
            f.write("Mock PDF")
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remover diretórios temporários
        shutil.rmtree(self.temp_dir)
    
    @patch('fitz.open')
    def test_carregar_pdf(self, mock_fitz_open):
        """Testa o carregamento do PDF."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Texto da página de teste"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Verificar se o método foi chamado corretamente
            mock_fitz_open.assert_called_once_with(self.mock_pdf_path)
            
            # Verificar se o texto foi extraído
            self.assertEqual(extrator.texto_completo, "Texto da página de teste")
            self.assertEqual(len(extrator.paginas_texto), 1)
            self.assertEqual(extrator.paginas_texto[0], "Texto da página de teste")
    
    @patch('fitz.open')
    def test_extrair_campo_com_fallback(self, mock_fitz_open):
        """Testa a extração de campos com fallback."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Nº: ABC123 Tipo de Intervenção: Instalação"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Testar extração com padrões válidos
            numero = extrator._extrair_campo_com_fallback([r"Nº\s*[:\-]?\s*(\w+)"])
            self.assertEqual(numero, "ABC123")
            
            tipo = extrator._extrair_campo_com_fallback([r"Tipo de Intervenção\s*[:\-]?\s*(.*?)(?=\s+[A-Za-z]|$)"])
            self.assertEqual(tipo, "Instalação")
            
            # Testar fallback quando o primeiro padrão falha
            resultado = extrator._extrair_campo_com_fallback([r"Padrão Inválido", r"Nº\s*[:\-]?\s*(\w+)"])
            self.assertEqual(resultado, "ABC123")
            
            # Testar quando todos os padrões falham
            resultado = extrator._extrair_campo_com_fallback([r"Padrão Inválido", r"Outro Padrão Inválido"])
            self.assertIsNone(resultado)
    
    @patch('fitz.open')
    def test_extrair_secao_com_fallback(self, mock_fitz_open):
        """Testa a extração de seções com fallback."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Observações do Técnico
        Instalação realizada com sucesso.
        Cliente satisfeito com o serviço.
        
        Equipamentos
        Router XYZ Serial Number 123456
        """
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Testar extração de seção
            observacoes = extrator._extrair_secao_com_fallback("observacoes_tecnico")
            self.assertIn("Instalação realizada com sucesso", observacoes)
            self.assertIn("Cliente satisfeito com o serviço", observacoes)
            
            # Testar seção inexistente
            resultado = extrator._extrair_secao_com_fallback("secao_inexistente")
            self.assertIsNone(resultado)
    
    @patch('fitz.open')
    def test_extrair_equipamentos(self, mock_fitz_open):
        """Testa a extração de equipamentos."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Equipamentos
        Entregues
        Router XYZ Serial Number 123456
        Modem ABC Serial Number 789012
        Recolhidos
        Router Antigo Serial Number 654321
        """
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Extrair seção de equipamentos
            secao_equipamentos = extrator._extrair_secao_com_fallback("equipamentos")
            
            # Testar extração de equipamentos
            equipamentos = extrator._extrair_equipamentos(secao_equipamentos)
            self.assertEqual(len(equipamentos), 2)
            self.assertIn("Router XYZ Serial Number 123456", equipamentos)
            self.assertIn("Modem ABC Serial Number 789012", equipamentos)
    
    @patch('fitz.open')
    def test_extrair_materiais(self, mock_fitz_open):
        """Testa a extração de materiais."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Materiais
        Cabo Ethernet 2
        Conector RJ45 4
        Fita Isolante 1.5
        """
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Extrair seção de materiais
            secao_materiais = extrator._extrair_secao_com_fallback("materiais")
            
            # Testar extração de materiais
            materiais = extrator._extrair_materiais(secao_materiais)
            self.assertEqual(len(materiais), 3)
            self.assertIn("Cabo Ethernet 2", materiais)
            self.assertIn("Conector RJ45 4", materiais)
            self.assertIn("Fita Isolante 1.5", materiais)
    
    @patch('fitz.open')
    def test_validar_dados(self, mock_fitz_open):
        """Testa a validação de dados."""
        # Configurar o mock
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Texto de teste"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            extrator._carregar_pdf()
            
            # Dados válidos
            dados_validos = {
                "dados_intervencao": {
                    "numero_intervencao": "ABC123",
                    "tipo_intervencao": "Instalação",
                    "data_inicio": "01/05/2025",
                    "hora_inicio": "09:30",
                    "data_fim": "01/05/2025",
                    "hora_fim": "11:45"
                },
                "observacoes_tecnico": "Instalação realizada com sucesso.",
                "equipamentos_entregues": ["Router XYZ Serial Number 123456"],
                "materiais_usados": ["Cabo Ethernet 2"]
            }
            
            # Testar validação de dados válidos
            extrator._validar_dados(dados_validos)
            self.assertEqual(len(extrator.diagnostico_info["avisos"]), 0)
            
            # Dados inválidos
            dados_invalidos = {
                "dados_intervencao": {
                    "tipo_intervencao": "Instalação",
                    "data_inicio": "01-05-2025",
                    "hora_inicio": "9:30",  # Formato inválido
                    "data_fim": "2025/05/01",  # Formato inválido
                    "hora_fim": "11h45"  # Formato inválido
                },
                "observacoes_tecnico": None,
                "equipamentos_entregues": [],
                "materiais_usados": []
            }
            
            # Testar validação de dados inválidos
            extrator.diagnostico_info["avisos"] = []  # Limpar avisos anteriores
            extrator._validar_dados(dados_invalidos)
            self.assertGreater(len(extrator.diagnostico_info["avisos"]), 0)
            self.assertTrue(any("Número de intervenção não encontrado" in aviso for aviso in extrator.diagnostico_info["avisos"]))
            self.assertTrue(any("Formato de hora inválido" in aviso for aviso in extrator.diagnostico_info["avisos"]))
            self.assertTrue(any("Observações do técnico não encontradas" in aviso for aviso in extrator.diagnostico_info["avisos"]))
    
    @patch('fitz.open')
    @patch('json.dump')
    def test_salvar_dados(self, mock_json_dump, mock_fitz_open):
        """Testa o salvamento de dados."""
        # Configurar os mocks
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Texto de teste"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Criar o extrator com o mock
        with ExtratorPDF(self.mock_pdf_path) as extrator:
            # Substituir os diretórios de saída pelos temporários
            extrator.saida_dir = self.saida_dir
            extrator.diagnostico_dir = self.diagnostico_dir
            
            # Dados de teste
            dados_teste = {
                "dados_intervencao": {"numero_intervencao": "ABC123"},
                "observacoes_tecnico": "Teste",
                "equipamentos_entregues": [],
                "materiais_usados": []
            }
            
            # Testar salvamento de dados
            extrator._salvar_dados(dados_teste)
            
            # Verificar se json.dump foi chamado
            mock_json_dump.assert_called_once()
            
            # Verificar se os argumentos estão corretos
            args, kwargs = mock_json_dump.call_args
            self.assertEqual(args[0], dados_teste)
            self.assertTrue(kwargs["ensure_ascii"] is False)
    
    @patch('fitz.open')
    @patch('M1_Extrator_PDF_Otimizado.ExtratorPDF.extrair_dados')
    @patch('M1_Extrator_PDF_Otimizado.ExtratorPDF.salvar_screenshot_pagina')
    def test_extrair_dados_pdf_relevantes(self, mock_screenshot, mock_extrair_dados, mock_fitz_open):
        """Testa a função principal de extração."""
        # Configurar os mocks
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        mock_extrair_dados.return_value = {"dados_teste": "valor_teste"}
        mock_screenshot.return_value = "/caminho/para/screenshot.png"
        
        # Testar a função principal
        resultado = extrair_dados_pdf_relevantes(self.mock_pdf_path)
        
        # Verificar se os métodos foram chamados
        mock_screenshot.assert_called_once_with(0)
        mock_extrair_dados.assert_called_once()
        
        # Verificar o resultado
        self.assertEqual(resultado, {"dados_teste": "valor_teste"})


if __name__ == "__main__":
    unittest.main()
