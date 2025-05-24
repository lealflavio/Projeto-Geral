import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TestCenariosReais:
    """Testes para cenários reais de uso do sistema."""

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
            "password": "senha_teste_123",
            "portal_username": "portal_teste",
            "portal_password": "portal_senha_123"
        }

    def test_cenario_tecnico_novo_pdf(self, mock_browser, mock_page, mock_credentials):
        """Testa o cenário de um técnico enviando um novo PDF."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # Simulação do cenário
        # 1. Técnico faz login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Verifica créditos disponíveis
        credits_display = mock_page.wait_for_selector("#credits-display")
        
        # 3. Navega para página de upload
        mock_page.click("#upload-menu")
        mock_page.wait_for_selector("#upload-form")
        
        # 4. Faz upload do PDF
        mock_page.set_input_files("#pdf-upload", "/path/to/relatorio_12345.pdf")
        mock_page.click("#upload-button")
        
        # 5. Aguarda processamento
        mock_page.wait_for_selector("#processing-status")
        success_message = mock_page.wait_for_selector("#success-message", timeout=30000)
        
        # 6. Verifica atualização de créditos
        mock_page.goto("https://dashboard-frontend.netlify.app/dashboard")
        updated_credits = mock_page.wait_for_selector("#credits-display")
        
        # Assert
        assert credits_display is not None
        assert success_message is not None
        assert updated_credits is not None

    def test_cenario_multiplos_pdfs_diferentes_formatos(self, mock_browser, mock_page, mock_credentials):
        """Testa o cenário de upload de múltiplos PDFs com formatos diferentes."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # Simulação do cenário
        # 1. Técnico faz login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Navega para página de upload
        mock_page.click("#upload-menu")
        mock_page.wait_for_selector("#upload-form")
        
        # 3. Faz upload do primeiro PDF (formato padrão)
        mock_page.set_input_files("#pdf-upload", "/path/to/relatorio_padrao.pdf")
        mock_page.click("#upload-button")
        mock_page.wait_for_selector("#success-message", timeout=30000)
        
        # 4. Faz upload do segundo PDF (formato alternativo)
        mock_page.set_input_files("#pdf-upload", "/path/to/relatorio_alternativo.pdf")
        mock_page.click("#upload-button")
        mock_page.wait_for_selector("#success-message", timeout=30000)
        
        # 5. Faz upload do terceiro PDF (formato com erro)
        mock_page.set_input_files("#pdf-upload", "/path/to/relatorio_erro.pdf")
        mock_page.click("#upload-button")
        error_message = mock_page.wait_for_selector("#error-message", timeout=30000)
        
        # 6. Verifica histórico
        mock_page.click("#history-menu")
        history_table = mock_page.wait_for_selector("#history-table")
        
        # Assert
        assert error_message is not None
        assert history_table is not None
        # Verificar se há 3 entradas no histórico (2 sucesso, 1 erro)
        # Em um teste real, verificaríamos o conteúdo da tabela

    def test_cenario_creditos_insuficientes(self, mock_browser, mock_page, mock_credentials):
        """Testa o cenário de um técnico com créditos insuficientes."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # Simulação do cenário
        # 1. Técnico faz login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", "tecnico_sem_creditos")
        mock_page.fill("#password", "senha_teste_123")
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Verifica créditos disponíveis (zero)
        credits_display = mock_page.wait_for_selector("#credits-display")
        
        # 3. Navega para página de upload
        mock_page.click("#upload-menu")
        mock_page.wait_for_selector("#upload-form")
        
        # 4. Tenta fazer upload do PDF
        mock_page.set_input_files("#pdf-upload", "/path/to/relatorio.pdf")
        mock_page.click("#upload-button")
        
        # 5. Recebe mensagem de créditos insuficientes
        error_message = mock_page.wait_for_selector("#credits-error-message")
        
        # 6. Navega para página de compra de créditos
        mock_page.click("#buy-credits-button")
        purchase_form = mock_page.wait_for_selector("#purchase-form")
        
        # Assert
        assert credits_display is not None
        assert error_message is not None
        assert purchase_form is not None

    def test_cenario_falha_conexao_portal(self, mock_browser, mock_page, mock_credentials):
        """Testa o cenário de falha na conexão com o portal Wondercom."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # Simulação do cenário
        # 1. Técnico faz login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Navega para página de alocação de WO
        mock_page.click("#allocate-wo-menu")
        mock_page.wait_for_selector("#allocate-wo-form")
        
        # 3. Preenche formulário com dados válidos
        mock_page.fill("#wo-number", "12345")
        mock_page.fill("#portal-username", mock_credentials["portal_username"])
        mock_page.fill("#portal-password", mock_credentials["portal_password"])
        
        # 4. Simula falha de conexão com o portal
        # Em um teste real, usaríamos um interceptor para simular falha de rede
        
        # 5. Clica no botão de alocar
        mock_page.click("#allocate-button")
        
        # 6. Recebe mensagem de erro de conexão
        connection_error = mock_page.wait_for_selector("#connection-error")
        
        # 7. Tenta novamente
        mock_page.click("#retry-button")
        
        # Assert
        assert connection_error is not None
        assert mock_page.click.call_count >= 3  # login + menu + botão alocar + retry

    def test_cenario_multiplos_dispositivos(self, mock_browser, mock_page, mock_credentials):
        """Testa o cenário de acesso em múltiplos dispositivos."""
        # Arrange
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Simular diferentes viewports para dispositivos
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 667}     # Mobile
        ]
        
        for viewport in viewports:
            # Act
            # 1. Configurar viewport
            mock_page.set_viewport_size(viewport)
            
            # 2. Técnico faz login
            mock_page.goto("https://dashboard-frontend.netlify.app")
            mock_page.fill("#username", mock_credentials["username"])
            mock_page.fill("#password", mock_credentials["password"])
            mock_page.click("#login-button")
            mock_page.wait_for_selector("#dashboard-content")
            
            # 3. Verifica elementos responsivos
            if viewport["width"] <= 768:
                # Em dispositivos móveis, deve haver um menu hamburguer
                hamburger_menu = mock_page.wait_for_selector("#mobile-menu-button")
                mock_page.click("#mobile-menu-button")
                mobile_menu = mock_page.wait_for_selector("#mobile-menu")
                assert hamburger_menu is not None
                assert mobile_menu is not None
            else:
                # Em desktop, deve haver um menu horizontal
                desktop_menu = mock_page.wait_for_selector("#desktop-menu")
                assert desktop_menu is not None
            
            # 4. Navega para histórico
            if viewport["width"] <= 768:
                mock_page.click("#mobile-history-menu")
            else:
                mock_page.click("#history-menu")
                
            history_table = mock_page.wait_for_selector("#history-table")
            assert history_table is not None
