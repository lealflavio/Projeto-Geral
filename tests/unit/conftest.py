import os
import sys
import pytest
from unittest.mock import MagicMock

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

@pytest.fixture
def mock_subprocess():
    """Fixture para simular o módulo subprocess."""
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_pdf_text():
    """Fixture para simular o texto extraído de um PDF."""
    return """
    Relatório de Intervenção Técnica
    
    Nº 12345
    Tipo de Intervenção: Instalação
    Data de Início: 24/05/2025
    Hora de Início: 09:30
    Data de Fim: 24/05/2025
    Hora de Fim: 11:45
    
    Observações do Técnico
    Instalação realizada com sucesso. Cliente satisfeito com o serviço.
    Configuração de rede concluída sem problemas.
    
    Equipamentos
    Entregues
    1x Router Fibra XYZ123
    1x Set-top Box HD
    2x Cabos Ethernet 2m
    
    Recolhidos
    1x Router antigo ABC456
    
    Materiais
    10m Cabo coaxial
    2x Conectores RJ45
    1x Adaptador de energia
    """

@pytest.fixture
def mock_pdf_text_alternative_format():
    """Fixture para simular o texto extraído de um PDF com formato alternativo."""
    return """
    Relatório de Intervenção Técnica
    
    Nº 54321
    Tipo de Intervenção: Manutenção
    Data de Início: 23/05/2025
    Hora de Início: 14:15
    Data de Fim: 23/05/2025
    Hora de Fim: 15:30
    
    Observações do Técnico
    Substituição de equipamento com defeito.
    Teste de conexão realizado com sucesso.
    
    Equipamentos
    1x Router Fibra XYZ123
    1x Cabo de alimentação
    
    Questionário do cliente
    Satisfação: 5/5
    """

@pytest.fixture
def mock_pdf_text_missing_sections():
    """Fixture para simular o texto extraído de um PDF com seções faltando."""
    return """
    Relatório de Intervenção Técnica
    
    Nº 67890
    Tipo de Intervenção: Suporte
    Data de Início: 22/05/2025
    Hora de Início: 10:00
    
    Observações do Técnico
    Visita de suporte para verificar problemas de conexão.
    Cliente não estava presente no horário agendado.
    """

@pytest.fixture
def mock_os_path():
    """Fixture para simular o módulo os.path."""
    mock = MagicMock()
    mock.basename.return_value = "test_pdf.pdf"
    mock.join.return_value = "/path/to/output/test_pdf_dados.json"
    return mock

@pytest.fixture
def mock_open_file():
    """Fixture para simular a abertura de arquivos."""
    mock = MagicMock()
    return mock
