"""
Seletores centralizados para o cliente Playwright.
Usando exatamente os mesmos seletores do Selenium para garantir compatibilidade.
"""

class Selectors:
    """Classe para armazenar todos os seletores usados na automação."""
    
    # Seletores de login - EXATAMENTE como no Selenium
    LOGIN_USERNAME = "id=_58_login"
    LOGIN_PASSWORD = "id=_58_password"
    LOGIN_BUTTON = "css=input[type='submit']"
    
    # Seletores de pesquisa - EXATAMENTE como no Selenium
    SEARCH_PAGE_INDICATOR = "xpath=//div[contains(text(), 'Pesquisa de Intervenções')]"
    SEARCH_FIELD = "xpath=//input[contains(@class, 'v-textfield') and not(contains(@style, 'display: none'))]"
    SEARCH_BUTTON = "xpath=//span[contains(text(), 'Pesquisar')]/parent::div[contains(@class, 'v-button')]"
    
    @staticmethod
    def get_wo_row_selector(work_order_id):
        """Retorna o seletor para a linha da WO específica."""
        return f"xpath=//tr[@class='v-table-row'][.//div[contains(text(), '{work_order_id}')]]"
    
    @staticmethod
    def get_button_by_text_selector(texto):
        """Retorna o seletor para um botão com o texto específico."""
        return f"xpath=//span[contains(@class, 'v-button-caption') and contains(text(), '{texto}')]/parent::div[contains(@class, 'v-button')]"
    
    # Seletores adicionais do Selenium
    DIALOG_WINDOW = "xpath=//div[contains(@class, 'v-window-modalitycurtain')]"
    DIALOG_CONTENT = "xpath=//div[contains(@class, 'v-window-contents')]"
    
    # Seletores de informações da WO
    MORADA_LABEL = "xpath=//div[contains(@class, 'v-label') and contains(text(), 'Morada:')]"
    SLID_LABEL = "xpath=//div[contains(@class, 'v-label') and contains(text(), 'SLID:')]"
    FIBRA_LABEL = "xpath=//div[contains(@class, 'v-label') and contains(text(), 'Fibra:')]"
    ESTADO_LABEL = "xpath=//div[contains(@class, 'v-label') and contains(text(), 'Estado:')]"
    
    # Botões específicos
    AVANCAR_BUTTON = "xpath=//span[contains(text(), 'Avançar')]/parent::div[contains(@class, 'v-button')]"
    EVOLUIR_BUTTON = "xpath=//span[contains(text(), 'Evoluir WorkOrder')]/parent::div[contains(@class, 'v-button')]"
    CONFIRMAR_BUTTON = "xpath=//span[contains(text(), 'Sim')]/parent::div[contains(@class, 'v-button')]"
    OK_BUTTON = "xpath=//span[contains(text(), 'Ok')]/parent::div[contains(@class, 'v-button')]"
