# Mapeamento de Dependências e Fluxo Backend-Selenium

## Estrutura do Sistema
- **Cliente Selenium**: `wondercom_client.py` - Implementa a automação do portal Wondercom
- **Adapters de Integração**: 
  - `wondercom_integration.py` - Integra o OrquestradorAdapter com o WondercomClient
  - `orquestrador_adapter.py` - Conecta a API REST aos scripts de orquestração

## Fluxo de Comunicação
1. Backend recebe requisição para alocar WO
2. OrquestradorAdapter ou WondercomIntegration inicializa o WondercomClient
3. WondercomClient executa automação no portal Wondercom
4. Dados extraídos são formatados e retornados ao backend

## Parâmetros de Entrada
- **work_order_id**: ID da ordem de trabalho a ser processada
- **credenciais**: Dicionário com `username` e `password`
- **chrome_driver_path**: Caminho para o chromedriver (opcional)
- **portal_url**: URL do portal Wondercom (opcional)

## Parâmetros de Saída
- **success**: Boolean indicando sucesso da operação
- **message**: Mensagem descritiva do resultado
- **dados**: Dicionário com dados extraídos da WO
  - id: ID da WO
  - estado: Estado atual da WO
  - descricao: Descrição completa
  - fibra/plc_cor_fibra: Informação da fibra
  - slid/slid_username: Identificador SLID
  - morada: Endereço completo
  - coordenadas/latitude/longitude: Coordenadas geográficas
  - dona_rede: Informação da dona de rede
  - porto_primario: Porto primário do PDO
  - data_agendamento/data_inicio: Data de agendamento
  - estado_intervencao: Estado da intervenção

## Formato de Resposta para o Backend
```json
{
  "status": "success|error",
  "data": {
    "endereco": "...",
    "pdo": "...",
    "cor_fibra": "...",
    "cor_fibra_hex": "#RRGGBB",
    "latitude": 00.000000,
    "longitude": 00.000000,
    "estado": "...",
    "descricao": "...",
    "dona_rede": "...",
    "porto_primario": "...",
    "data_agendamento": "...",
    "estado_intervencao": "..."
  }
}
```

## Dependências e Configurações
- **Selenium**: Biblioteca para automação web
- **ChromeDriver**: Driver para controle do Chrome
- **BeautifulSoup**: Utilizado para parsing de HTML
- **Configurações**:
  - CHROME_DRIVER_PATH: Caminho para o chromedriver
  - WONDERCOM_PORTAL_URL: URL do portal Wondercom
  - DEFAULT_TIMEOUT: Timeout padrão para operações

## Pontos Críticos de Integração
1. Inicialização do driver (start_driver)
2. Login no portal (login)
3. Busca da WO (search_work_order)
4. Extração de dados (extract_work_order_details)
5. Formatação dos dados para o backend
6. Fechamento do driver (close_driver)

## Tratamento de Erros
- Erros de login: Retorna `{"success": false, "message": "Falha no login"}`
- WO não encontrada: Retorna `{"success": false, "message": "WO {id} não encontrada"}`
- Erros de extração: Registra warnings e continua com dados parciais
- Erros gerais: Captura exceção e retorna `{"success": false, "message": str(e)}`
