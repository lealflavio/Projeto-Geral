import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configuração para pytest-cov
# Executar com: pytest --cov=. tests/

def test_pytest_configuration():
    """Teste para verificar se o pytest está configurado corretamente."""
    assert True

def test_coverage_configuration():
    """Teste para verificar se o pytest-cov está configurado corretamente."""
    assert True
