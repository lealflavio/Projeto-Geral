import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar o módulo a ser testado
import M1_Extrator_PDF as extrator

class TestExtratorPDF:
    """Testes unitários para o módulo de extração de PDFs."""

    def test_extrair_valor_apos_rotulo(self, mock_pdf_text):
        """Testa a extração de valores após rótulos específicos."""
        # Arrange
        texto = mock_pdf_text
        
        # Act
        numero = extrator.extrair_valor_apos_rotulo(texto, "Nº")
        tipo = extrator.extrair_valor_apos_rotulo(texto, "Tipo de Intervenção")
        data_inicio = extrator.extrair_valor_apos_rotulo(texto, "Data de Início")
        hora_inicio = extrator.extrair_valor_apos_rotulo(texto, "Hora de Início")
        
        # Assert
        assert numero == "12345"
        assert tipo == "Instalação"
        assert data_inicio == "24/05/2025"
        assert hora_inicio == "09:30"

    def test_extrair_valor_apos_rotulo_inexistente(self, mock_pdf_text):
        """Testa a extração de valores para rótulos que não existem no texto."""
        # Arrange
        texto = mock_pdf_text
        
        # Act
        valor = extrator.extrair_valor_apos_rotulo(texto, "Rótulo Inexistente")
        
        # Assert
        assert valor is None

    def test_extrair_secao_multilinha(self, mock_pdf_text):
        """Testa a extração de seções de múltiplas linhas."""
        # Arrange
        texto = mock_pdf_text
        
        # Act
        observacoes = extrator.extrair_secao_multilinha(texto, "Observações do Técnico", "Equipamentos")
        equipamentos = extrator.extrair_secao_multilinha(texto, "Equipamentos", "Materiais")
        materiais = extrator.extrair_secao_multilinha(texto, "Materiais", "Questionário do cliente")
        
        # Assert
        assert "Instalação realizada com sucesso" in observacoes
        assert "Configuração de rede concluída" in observacoes
        assert "Entregues" in equipamentos
        assert "Router Fibra XYZ123" in equipamentos
        assert "Recolhidos" in equipamentos
        assert "Cabo coaxial" in materiais
        assert "Conectores RJ45" in materiais

    def test_extrair_secao_multilinha_ate_fim(self, mock_pdf_text_alternative_format):
        """Testa a extração de seções de múltiplas linhas até o fim do texto."""
        # Arrange
        texto = mock_pdf_text_alternative_format
        
        # Act
        observacoes = extrator.extrair_secao_multilinha(texto, "Observações do Técnico", "Equipamentos")
        equipamentos = extrator.extrair_secao_multilinha(texto, "Equipamentos", "Questionário do cliente")
        
        # Assert
        assert "Substituição de equipamento" in observacoes
        assert "Teste de conexão" in observacoes
        assert "Router Fibra XYZ123" in equipamentos
        assert "Cabo de alimentação" in equipamentos

    def test_extrair_secao_multilinha_inexistente(self, mock_pdf_text):
        """Testa a extração de seções que não existem no texto."""
        # Arrange
        texto = mock_pdf_text
        
        # Act
        secao = extrator.extrair_secao_multilinha(texto, "Seção Inexistente", "Outra Seção")
        
        # Assert
        assert secao is None

    def test_extrair_equipamentos(self):
        """Testa a extração de equipamentos a partir de texto."""
        # Arrange
        texto_equipamentos = """
        1x Router Fibra XYZ123
        2x Set-top Box HD
        3x Cabos Ethernet 2m
        """
        
        # Act
        equipamentos = extrator.extrair_equipamentos(texto_equipamentos)
        
        # Assert
        assert len(equipamentos) == 3
        assert {"quantidade": 1, "descricao": "Router Fibra XYZ123"} in equipamentos
        assert {"quantidade": 2, "descricao": "Set-top Box HD"} in equipamentos
        assert {"quantidade": 3, "descricao": "Cabos Ethernet 2m"} in equipamentos

    def test_extrair_equipamentos_formato_alternativo(self):
        """Testa a extração de equipamentos com formato alternativo."""
        # Arrange
        texto_equipamentos = """
        Router Fibra XYZ123 (1)
        Set-top Box HD (2)
        Cabos Ethernet 2m (3)
        """
        
        # Act
        equipamentos = extrator.extrair_equipamentos(texto_equipamentos)
        
        # Assert
        assert len(equipamentos) == 3
        assert {"quantidade": 1, "descricao": "Router Fibra XYZ123"} in equipamentos
        assert {"quantidade": 2, "descricao": "Set-top Box HD"} in equipamentos
        assert {"quantidade": 3, "descricao": "Cabos Ethernet 2m"} in equipamentos

    def test_extrair_materiais(self):
        """Testa a extração de materiais a partir de texto."""
        # Arrange
        texto_materiais = """
        10m Cabo coaxial
        2x Conectores RJ45
        1x Adaptador de energia
        """
        
        # Act
        materiais = extrator.extrair_materiais(texto_materiais)
        
        # Assert
        assert len(materiais) == 3
        assert {"quantidade": 10, "unidade": "m", "descricao": "Cabo coaxial"} in materiais
        assert {"quantidade": 2, "unidade": "x", "descricao": "Conectores RJ45"} in materiais
        assert {"quantidade": 1, "unidade": "x", "descricao": "Adaptador de energia"} in materiais

    @patch('M1_Extrator_PDF.subprocess')
    @patch('M1_Extrator_PDF.os')
    @patch('M1_Extrator_PDF.open', new_callable=mock_open)
    @patch('M1_Extrator_PDF.json.dump')
    def test_extrair_dados_pdf_relevantes_sucesso(self, mock_json_dump, mock_file, mock_os, mock_subprocess, mock_pdf_text):
        """Testa a extração completa de dados de um PDF com sucesso."""
        # Arrange
        mock_process = MagicMock()
        mock_process.stdout = mock_pdf_text
        mock_subprocess.run.return_value = mock_process
        mock_os.path.basename.return_value = "test_pdf.pdf"
        mock_os.path.join.return_value = "/path/to/output/test_pdf_dados.json"
        mock_os.makedirs.return_value = None
        
        # Act
        resultado = extrator.extrair_dados_pdf_relevantes("/path/to/test_pdf.pdf")
        
        # Assert
        assert resultado is not None
        assert resultado["dados_intervencao"]["numero_intervencao"] == "12345"
        assert resultado["dados_intervencao"]["tipo_intervencao"] == "Instalação"
        assert resultado["dados_intervencao"]["data_inicio"] == "24/05/2025"
        assert resultado["dados_intervencao"]["hora_inicio"] == "09:30"
        assert resultado["dados_intervencao"]["data_fim"] == "24/05/2025"
        assert resultado["dados_intervencao"]["hora_fim"] == "11:45"
        assert "Instalação realizada com sucesso" in resultado["observacoes_tecnico"]
        assert len(resultado["equipamentos_entregues"]) == 3
        assert len(resultado["materiais_usados"]) == 3
        mock_subprocess.run.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('M1_Extrator_PDF.subprocess')
    def test_extrair_dados_pdf_relevantes_erro_pdftotext(self, mock_subprocess, mock_pdf_text):
        """Testa o comportamento quando o comando pdftotext não é encontrado."""
        # Arrange
        mock_subprocess.run.side_effect = FileNotFoundError("Comando não encontrado")
        
        # Act
        resultado = extrator.extrair_dados_pdf_relevantes("/path/to/test_pdf.pdf")
        
        # Assert
        assert resultado is None
        mock_subprocess.run.assert_called_once()

    @patch('M1_Extrator_PDF.subprocess')
    def test_extrair_dados_pdf_relevantes_erro_processo(self, mock_subprocess, mock_pdf_text):
        """Testa o comportamento quando o processo de extração falha."""
        # Arrange
        mock_subprocess.run.side_effect = mock_subprocess.CalledProcessError(1, "pdftotext", stderr="Erro ao processar PDF")
        
        # Act
        resultado = extrator.extrair_dados_pdf_relevantes("/path/to/test_pdf.pdf")
        
        # Assert
        assert resultado is None
        mock_subprocess.run.assert_called_once()

    @patch('M1_Extrator_PDF.subprocess')
    @patch('M1_Extrator_PDF.os')
    @patch('M1_Extrator_PDF.open', new_callable=mock_open)
    @patch('M1_Extrator_PDF.json.dump')
    def test_extrair_dados_pdf_relevantes_formato_alternativo(self, mock_json_dump, mock_file, mock_os, mock_subprocess, mock_pdf_text_alternative_format):
        """Testa a extração de dados de um PDF com formato alternativo."""
        # Arrange
        mock_process = MagicMock()
        mock_process.stdout = mock_pdf_text_alternative_format
        mock_subprocess.run.return_value = mock_process
        mock_os.path.basename.return_value = "test_pdf_alt.pdf"
        mock_os.path.join.return_value = "/path/to/output/test_pdf_alt_dados.json"
        mock_os.makedirs.return_value = None
        
        # Act
        resultado = extrator.extrair_dados_pdf_relevantes("/path/to/test_pdf_alt.pdf")
        
        # Assert
        assert resultado is not None
        assert resultado["dados_intervencao"]["numero_intervencao"] == "54321"
        assert resultado["dados_intervencao"]["tipo_intervencao"] == "Manutenção"
        assert "Substituição de equipamento" in resultado["observacoes_tecnico"]
        assert len(resultado["equipamentos_entregues"]) > 0
        mock_subprocess.run.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('M1_Extrator_PDF.subprocess')
    @patch('M1_Extrator_PDF.os')
    @patch('M1_Extrator_PDF.open', new_callable=mock_open)
    @patch('M1_Extrator_PDF.json.dump')
    def test_extrair_dados_pdf_relevantes_secoes_faltando(self, mock_json_dump, mock_file, mock_os, mock_subprocess, mock_pdf_text_missing_sections):
        """Testa a extração de dados de um PDF com seções faltando."""
        # Arrange
        mock_process = MagicMock()
        mock_process.stdout = mock_pdf_text_missing_sections
        mock_subprocess.run.return_value = mock_process
        mock_os.path.basename.return_value = "test_pdf_missing.pdf"
        mock_os.path.join.return_value = "/path/to/output/test_pdf_missing_dados.json"
        mock_os.makedirs.return_value = None
        
        # Act
        resultado = extrator.extrair_dados_pdf_relevantes("/path/to/test_pdf_missing.pdf")
        
        # Assert
        assert resultado is not None
        assert resultado["dados_intervencao"]["numero_intervencao"] == "67890"
        assert resultado["dados_intervencao"]["tipo_intervencao"] == "Suporte"
        assert "data_fim" not in resultado["dados_intervencao"]
        assert "hora_fim" not in resultado["dados_intervencao"]
        assert "Visita de suporte" in resultado["observacoes_tecnico"]
        assert len(resultado["equipamentos_entregues"]) == 0
        assert len(resultado["materiais_usados"]) == 0
        mock_subprocess.run.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
