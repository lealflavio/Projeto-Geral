# Alternativas de Automação para o Portal Wondercom

## Análise do Portal

Após análise detalhada do portal Wondercom, identificamos as seguintes características técnicas:

1. **Frameworks Utilizados**:
   - Vaadin: Framework Java para aplicações web
   - Liferay: Plataforma de portal empresarial
   - jQuery: Biblioteca JavaScript

2. **Estrutura da Aplicação**:
   - Interface baseada em componentes Vaadin (v-app, v-verticallayout, etc.)
   - Portlets Liferay para gerenciamento de conteúdo
   - Comunicação cliente-servidor possivelmente via UIDL (User Interface Definition Language)

3. **Desafios Identificados**:
   - Interface altamente dinâmica com muitos componentes JavaScript
   - Necessidade de cliques com botão direito em alguns elementos
   - Tempos de carregamento variáveis
   - Execução paralela de múltiplas instâncias

## Alternativas ao Selenium

### 1. Playwright (Recomendação Principal)

**Vantagens**:
- **Performance**: Significativamente mais rápido que o Selenium
- **Recursos Modernos**: Suporte nativo a cliques com botão direito, esperas inteligentes
- **Isolamento de Contexto**: Permite múltiplas instâncias isoladas com menor consumo de recursos
- **Headless Otimizado**: Melhor performance em modo headless
- **Esperas Automáticas**: Espera automaticamente pelos elementos ficarem prontos

**Exemplo de Código**:
```python
from playwright.sync_api import sync_playwright

def automate_wondercom():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto("https://portal.wondercom.pt/group/guest/intervencoes")
        page.fill("#_58_login", "flavio.leal")
        page.fill("#_58_password", "MFH8fQgAa4")
        page.click("input[type='submit']")
        
        # Pesquisa de WO
        page.wait_for_selector(".v-textfield")
        page.fill(".v-textfield", "16722483")
        
        # Clique com botão direito (suportado nativamente)
        page.click("selector", button="right")
        
        # Esperas inteligentes
        page.wait_for_load_state("networkidle")
```

### 2. Puppeteer

**Vantagens**:
- Mais rápido que Selenium
- Bom suporte para aplicações JavaScript
- Integração direta com Chrome DevTools Protocol

**Limitações**:
- Suporte apenas para navegadores baseados em Chromium
- Menos recursos que o Playwright

### 3. Requisições HTTP Diretas (Parcial)

**Análise**:
Após investigação, identificamos que o portal Wondercom utiliza comunicação UIDL do Vaadin, que é complexa e não facilmente replicável via requisições HTTP simples. No entanto, algumas operações específicas podem ser automatizadas:

- Login inicial via POST para `/c/portal/login`
- Algumas consultas simples via GET

**Limitações**:
- Não é possível replicar completamente a interação com componentes Vaadin
- Operações complexas como cliques com botão direito não são viáveis

### 4. Otimização do Selenium Atual

Se for necessário manter o Selenium, recomendamos:

1. **Pool de WebDrivers**: Implementar um sistema de pool que reutilize instâncias do navegador
2. **Recursos Compartilhados**: Compartilhar recursos entre múltiplas instâncias
3. **Esperas Adaptativas**: Implementar sistema de esperas que se ajuste ao tempo de resposta do portal
4. **Execução Paralela Otimizada**: Limitar o número de instâncias paralelas para evitar sobrecarga

## Recomendação para Execução Paralela

Para cenários com múltiplas execuções paralelas (5-6 instâncias):

1. **Playwright com Contextos Isolados**:
```python
async def run_multiple_instances():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Criar múltiplos contextos isolados (mais eficiente que múltiplos navegadores)
        contexts = [await browser.new_context() for _ in range(6)]
        
        # Criar páginas para cada contexto
        pages = [await context.new_page() for context in contexts]
        
        # Executar operações em paralelo
        await asyncio.gather(*[process_work_order(pages[i], f"WO_{i}") for i in range(6)])
```

2. **Sistema de Filas**:
   - Implementar um sistema de filas para distribuir o trabalho
   - Limitar o número de instâncias ativas com base nos recursos disponíveis
   - Priorizar tarefas críticas

## Conclusão

Baseado na análise do portal Wondercom e nos requisitos específicos (incluindo cliques com botão direito e execução paralela), recomendamos:

1. **Migrar para Playwright**: Oferece o melhor equilíbrio entre performance, recursos modernos e facilidade de implementação
2. **Implementar Contextos Isolados**: Para execução eficiente de múltiplas instâncias paralelas
3. **Manter Esperas Adaptativas**: Para lidar com tempos de carregamento variáveis do portal

Esta abordagem deve reduzir significativamente o tempo de processamento (estimativa de 50-70% de redução) e permitir execução paralela mais eficiente.
