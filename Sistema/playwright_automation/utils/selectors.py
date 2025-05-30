"""
Seletores centralizados para o cliente Playwright.
"""

class Selectors:
    """Classe para armazenar todos os seletores usados na automação."""
    
    # Seletores de login
    LOGIN_USERNAME = "#_58_login"
    LOGIN_PASSWORD = "#_58_password"
    LOGIN_BUTTON = "input[type='submit']"
    
    # Seletores de pesquisa
    SEARCH_PAGE_INDICATOR = "text=Pesquisa de Intervenções"
    SEARCH_FIELD = "input.v-textfield[aria-hidden='false']"
    SEARCH_BUTTON = "//span[normalize-space()='Pesquisar']/ancestor::div[contains(@class,'v-button') and not(contains(@class,'v-disabled'))]"
    
    @staticmethod
    def get_wo_row_selector(work_order_id):
        """Retorna o seletor para a linha da WO específica."""
        return f"//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
    
    @staticmethod
    def get_button_by_text_selector(texto):
        """Retorna o seletor para um botão com o texto específico."""
        return f"//span[@class='v-button-caption' and normalize-space()='{texto}']/ancestor::div[contains(@class, 'v-button') and not(contains(@class,'v-disabled'))]"