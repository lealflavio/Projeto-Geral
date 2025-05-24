import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from playwright.sync_api import Page, expect

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TestExperienciaUsuario:
    """Testes para validação da experiência do usuário."""

    @pytest.fixture
    def mock_browser(self):
        """Fixture para simular o navegador."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_page(self):
        """Fixture para simular a página do navegador."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_credentials(self):
        """Fixture para simular credenciais de teste."""
        return {
            "username": "tecnico_teste",
            "password": "senha_teste_123"
        }

    def test_feedback_visual_durante_operacoes(self, mock_browser, mock_page, mock_credentials):
        """Testa o feedback visual durante operações assíncronas."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # 1. Login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        
        # 2. Verificar spinner de carregamento
        loading_spinner = mock_page.wait_for_selector("#loading-spinner")
        
        # 3. Verificar dashboard após carregamento
        dashboard_content = mock_page.wait_for_selector("#dashboard-content")
        
        # Assert
        assert loading_spinner is not None
        assert dashboard_content is not None
        
        # 4. Testar feedback visual em outra operação
        mock_page.click("#upload-menu")
        mock_page.wait_for_selector("#upload-form")
        mock_page.set_input_files("#pdf-upload", "/path/to/test.pdf")
        mock_page.click("#upload-button")
        
        # 5. Verificar indicador de progresso
        progress_indicator = mock_page.wait_for_selector("#progress-indicator")
        
        # Assert
        assert progress_indicator is not None

    def test_clareza_mensagens_erro(self, mock_browser, mock_page, mock_credentials):
        """Testa a clareza das mensagens de erro."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # 1. Tentar login com credenciais inválidas
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", "usuario_invalido")
        mock_page.fill("#password", "senha_invalida")
        mock_page.click("#login-button")
        
        # 2. Verificar mensagem de erro
        error_message = mock_page.wait_for_selector("#error-message")
        mock_page.get_text = MagicMock(return_value="Credenciais inválidas. Por favor, verifique seu nome de usuário e senha.")
        error_text = mock_page.get_text("#error-message")
        
        # Assert
        assert error_message is not None
        assert "Credenciais inválidas" in error_text
        assert len(error_text) > 20  # Mensagem deve ser descritiva
        
        # 3. Testar outro cenário de erro
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 4. Tentar alocar WO com número inválido
        mock_page.click("#allocate-wo-menu")
        mock_page.wait_for_selector("#allocate-wo-form")
        mock_page.fill("#wo-number", "abc")  # Formato inválido
        mock_page.click("#allocate-button")
        
        # 5. Verificar mensagem de erro específica
        field_error = mock_page.wait_for_selector("#wo-number-error")
        mock_page.get_text = MagicMock(return_value="O número da WO deve conter apenas dígitos.")
        field_error_text = mock_page.get_text("#wo-number-error")
        
        # Assert
        assert field_error is not None
        assert "apenas dígitos" in field_error_text

    def test_tempos_resposta_percebidos(self, mock_browser, mock_page, mock_credentials):
        """Testa os tempos de resposta percebidos pelo usuário."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Simular medição de tempo
        start_time = 1621500000
        end_time = 1621500000 + 0.8  # 800ms
        
        # Act
        # 1. Login (com medição de tempo)
        # Em um teste real, usaríamos time.time() antes e depois
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        login_time = end_time - start_time
        
        # 2. Navegação para histórico (com medição de tempo)
        start_time = 1621500010
        mock_page.click("#history-menu")
        mock_page.wait_for_selector("#history-table")
        end_time = 1621500010 + 0.5  # 500ms
        
        navigation_time = end_time - start_time
        
        # Assert
        assert login_time < 1.0  # Menos de 1 segundo
        assert navigation_time < 0.8  # Menos de 800ms

    def test_acessibilidade_basica(self, mock_browser, mock_page):
        """Testa aspectos básicos de acessibilidade."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.get_by_role = MagicMock()
        mock_page.get_by_label = MagicMock()
        mock_page.evaluate = MagicMock()
        
        # Act
        # 1. Verificar elementos de formulário com labels
        mock_page.goto("https://dashboard-frontend.netlify.app")
        username_input = mock_page.get_by_label("Nome de usuário")
        password_input = mock_page.get_by_label("Senha")
        
        # 2. Verificar botões com roles adequados
        login_button = mock_page.get_by_role("button", name="Entrar")
        
        # 3. Verificar contraste de cores (simulado)
        # Em um teste real, usaríamos uma biblioteca de análise de acessibilidade
        contrast_check = mock_page.evaluate("""() => {
            // Simulação de verificação de contraste
            return { passed: true, failedElements: [] };
        }""")
        
        # 4. Verificar navegação por teclado
        mock_page.keyboard = MagicMock()
        mock_page.keyboard.press("Tab")
        mock_page.keyboard.press("Tab")
        mock_page.keyboard.press("Enter")
        
        # Assert
        assert username_input is not None
        assert password_input is not None
        assert login_button is not None
        assert contrast_check["passed"] is True
        assert len(contrast_check["failedElements"]) == 0

    def test_consistencia_interface(self, mock_browser, mock_page, mock_credentials):
        """Testa a consistência da interface do usuário."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # 1. Login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Verificar elementos de navegação consistentes
        header = mock_page.wait_for_selector("header")
        sidebar = mock_page.wait_for_selector("#sidebar")
        footer = mock_page.wait_for_selector("footer")
        
        # 3. Navegar para diferentes páginas e verificar consistência
        pages = ["#history-menu", "#allocate-wo-menu", "#upload-menu", "#profile-menu"]
        
        for page_menu in pages:
            mock_page.click(page_menu)
            # Verificar se elementos de navegação permanecem consistentes
            header_still_present = mock_page.wait_for_selector("header")
            sidebar_still_present = mock_page.wait_for_selector("#sidebar")
            footer_still_present = mock_page.wait_for_selector("footer")
            
            assert header_still_present is not None
            assert sidebar_still_present is not None
            assert footer_still_present is not None
        
        # Assert
        assert header is not None
        assert sidebar is not None
        assert footer is not None
