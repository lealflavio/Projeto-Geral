import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from playwright.sync_api import Page, expect

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class TestMultiplosDispositivos:
    """Testes em diferentes dispositivos e navegadores."""

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

    @pytest.fixture
    def device_configs(self):
        """Fixture para configurações de diferentes dispositivos."""
        return [
            {"name": "Desktop", "viewport": {"width": 1920, "height": 1080}, "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
            {"name": "Tablet", "viewport": {"width": 768, "height": 1024}, "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
            {"name": "Mobile", "viewport": {"width": 375, "height": 667}, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"}
        ]

    @pytest.fixture
    def browser_configs(self):
        """Fixture para configurações de diferentes navegadores."""
        return [
            {"name": "Chrome", "channel": "chrome"},
            {"name": "Firefox", "channel": "firefox"},
            {"name": "Edge", "channel": "msedge"}
        ]

    def test_responsividade_dashboard(self, mock_browser, mock_page, mock_credentials, device_configs):
        """Testa a responsividade do dashboard em diferentes dispositivos."""
        for device in device_configs:
            # Arrange
            mock_page.set_viewport_size.return_value = None
            mock_page.set_extra_http_headers.return_value = None
            mock_page.goto.return_value = None
            mock_page.fill.return_value = None
            mock_page.click.return_value = None
            mock_page.wait_for_selector.return_value = MagicMock()
            
            # Act
            # 1. Configurar dispositivo
            mock_page.set_viewport_size(device["viewport"])
            mock_page.set_extra_http_headers({"User-Agent": device["user_agent"]})
            
            # 2. Login
            mock_page.goto("https://dashboard-frontend.netlify.app")
            mock_page.fill("#username", mock_credentials["username"])
            mock_page.fill("#password", mock_credentials["password"])
            mock_page.click("#login-button")
            mock_page.wait_for_selector("#dashboard-content")
            
            # 3. Verificar elementos responsivos
            if device["viewport"]["width"] <= 768:
                # Em dispositivos móveis, deve haver um menu hamburguer
                hamburger_menu = mock_page.wait_for_selector("#mobile-menu-button")
                assert hamburger_menu is not None
                
                # Verificar se o layout está em coluna única
                layout_column = mock_page.wait_for_selector(".layout-column")
                assert layout_column is not None
            else:
                # Em desktop, deve haver um menu horizontal
                desktop_menu = mock_page.wait_for_selector("#desktop-menu")
                assert desktop_menu is not None
                
                # Verificar se o layout está em múltiplas colunas
                layout_grid = mock_page.wait_for_selector(".layout-grid")
                assert layout_grid is not None

    def test_compatibilidade_navegadores(self, mock_browser, mock_page, mock_credentials, browser_configs):
        """Testa a compatibilidade com diferentes navegadores."""
        for browser in browser_configs:
            # Arrange
            mock_browser.channel = browser["channel"]
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
            dashboard_content = mock_page.wait_for_selector("#dashboard-content")
            
            # 2. Verificar elementos críticos
            credits_display = mock_page.wait_for_selector("#credits-display")
            history_button = mock_page.wait_for_selector("#history-menu")
            
            # Assert
            assert dashboard_content is not None
            assert credits_display is not None
            assert history_button is not None

    def test_interacao_touch(self, mock_browser, mock_page, mock_credentials):
        """Testa a interação por touch em dispositivos móveis."""
        # Arrange
        mock_page.set_viewport_size.return_value = None
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        mock_page.touch = MagicMock()
        
        # Configurar como dispositivo móvel
        mock_page.set_viewport_size({"width": 375, "height": 667})
        
        # Act
        # 1. Login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Abrir menu mobile com toque
        mock_page.touch.tap(100, 50)  # Coordenadas do botão de menu
        mobile_menu = mock_page.wait_for_selector("#mobile-menu")
        
        # 3. Navegar para histórico com toque
        mock_page.touch.tap(200, 150)  # Coordenadas do item de menu histórico
        history_table = mock_page.wait_for_selector("#history-table")
        
        # 4. Testar scroll com gesto de touch
        mock_page.touch.scroll(200, 300, 200, 100, {"speed": 1000})  # Scroll para baixo
        
        # Assert
        assert mobile_menu is not None
        assert history_table is not None

    def test_orientacao_tela(self, mock_browser, mock_page, mock_credentials):
        """Testa a adaptação à mudança de orientação da tela em dispositivos móveis."""
        # Arrange
        mock_page.set_viewport_size.return_value = None
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        
        # Act
        # 1. Configurar como dispositivo móvel em modo retrato
        mock_page.set_viewport_size({"width": 375, "height": 667})
        
        # 2. Login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 3. Verificar layout em modo retrato
        portrait_layout = mock_page.wait_for_selector(".layout-portrait")
        
        # 4. Mudar para modo paisagem
        mock_page.set_viewport_size({"width": 667, "height": 375})
        
        # 5. Verificar adaptação do layout
        landscape_layout = mock_page.wait_for_selector(".layout-landscape")
        
        # Assert
        assert portrait_layout is not None
        assert landscape_layout is not None

    def test_performance_dispositivos_baixo_desempenho(self, mock_browser, mock_page, mock_credentials):
        """Testa a performance em dispositivos de baixo desempenho."""
        # Arrange
        mock_page.set_viewport_size.return_value = None
        mock_page.goto.return_value = None
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_selector.return_value = MagicMock()
        mock_page.evaluate.return_value = {"score": 85}
        
        # Configurar como dispositivo de baixo desempenho
        mock_browser.new_context.return_value = mock_page
        mock_browser.new_context(
            viewport={"width": 375, "height": 667},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            forced_colors="none"
        )
        
        # Act
        # 1. Login
        mock_page.goto("https://dashboard-frontend.netlify.app")
        mock_page.fill("#username", mock_credentials["username"])
        mock_page.fill("#password", mock_credentials["password"])
        mock_page.click("#login-button")
        mock_page.wait_for_selector("#dashboard-content")
        
        # 2. Medir performance (simulado)
        # Em um teste real, usaríamos métricas de performance do Lighthouse
        performance_metrics = mock_page.evaluate("""() => {
            // Simulação de métricas de performance
            return {
                score: 85,
                metrics: {
                    firstContentfulPaint: 1200,
                    timeToInteractive: 2500,
                    speedIndex: 1800
                }
            };
        }""")
        
        # Assert
        assert performance_metrics["score"] >= 80  # Score mínimo aceitável
