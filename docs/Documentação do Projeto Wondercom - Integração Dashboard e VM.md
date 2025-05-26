# Documentação do Projeto Wondercom - Integração Dashboard e VM

## Sumário

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Trabalho Realizado](#trabalho-realizado)
   - [Fase 1: Análise e Planejamento](#fase-1-análise-e-planejamento)
   - [Fase 2: Implementação da API na VM](#fase-2-implementação-da-api-na-vm)
   - [Fase 3: Integração com WondercomClient](#fase-3-integração-com-wondercomclient)
   - [Fase 4: Configuração de Serviços](#fase-4-configuração-de-serviços)
   - [Fase 5: Integração Backend-Frontend](#fase-5-integração-backend-frontend)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Componentes Implementados](#componentes-implementados)
5. [Fluxos de Comunicação](#fluxos-de-comunicação)
6. [Próximos Passos](#próximos-passos)
7. [Recomendações Técnicas](#recomendações-técnicas)
8. [Apêndices](#apêndices)

## Visão Geral do Projeto

O projeto Wondercom consiste em um sistema de automação e dashboard para técnicos de telecomunicações em Portugal. O sistema é composto por três componentes principais:

1. **VM de Automação**: Executa scripts Python para automação do portal Wondercom, incluindo alocação de ordens de trabalho (WO) e extração de dados.
2. **Backend API**: Implementado em Flask, gerencia a comunicação entre o frontend e a VM, além de processar e armazenar dados.
3. **Frontend Dashboard**: Desenvolvido em React, fornece interface para os técnicos interagirem com o sistema.

O objetivo principal do projeto é automatizar tarefas repetitivas no portal Wondercom, como alocação de WO e extração de dados, além de fornecer ferramentas úteis para os técnicos, como cálculo de quilômetros percorridos e simulação de ganhos.

## Trabalho Realizado

### Fase 1: Análise e Planejamento

#### Análise do Repositório e Documentação Existente

Foi realizada uma análise detalhada do repositório GitHub do projeto, incluindo:
- Estrutura de diretórios e arquivos
- Documentação existente
- Scripts de automação (M1-M6)
- Componentes do backend e frontend

#### Elaboração de Planos de Integração

Foram criados documentos detalhados para guiar a implementação:
- **Fluxos de Comunicação**: Mapeamento dos fluxos de dados entre frontend, backend e VM
- **Arquitetura de Integração**: Proposta de arquitetura técnica com componentes e mecanismos de comunicação
- **Etapas de Implementação**: Roteiro prático com código de exemplo para implementar a integração

### Fase 2: Implementação da API na VM

#### Estrutura de Diretórios e Arquivos

Foi implementada uma estrutura organizada na VM:
```
/home/flavioleal/Sistema/vm_api/
├── adapters/
│   ├── __init__.py
│   ├── extrator_adapter.py
│   ├── orquestrador_adapter.py
│   ├── notificacao_adapter.py
│   └── wondercom_integration.py
├── routes/
│   ├── __init__.py
│   ├── allocate.py
│   ├── process.py
│   └── status.py
├── queue/
│   ├── __init__.py
│   ├── producer.py
│   └── worker.py
├── app.py
├── auth.py
├── config.py
└── wondercom_client.py
```

#### Implementação dos Componentes da API

Foram desenvolvidos os seguintes componentes:
- **app.py**: Aplicação principal Flask que expõe os endpoints da API
- **config.py**: Configurações centralizadas da API
- **auth.py**: Sistema de autenticação e autorização
- **adapters/**: Adaptadores para integração com scripts existentes
- **routes/**: Endpoints da API
- **queue/**: Sistema de filas com Redis para processamento assíncrono

### Fase 3: Integração com WondercomClient

#### Análise do WondercomClient

Foi realizada uma análise detalhada do `wondercom_client.py`, identificando:
- Seletores XPath e IDs de elementos HTML
- Método de extração de detalhes da WO
- Lógica de tratamento de diferentes estados da WO
- Método `clicar_por_texto()` para navegação

#### Implementação da Integração Direta

Foi implementada uma abordagem de integração direta entre o OrquestradorAdapter e o WondercomClient:
- Eliminação de camadas intermediárias de adaptação
- Preservação de todos os seletores XPath e IDs de elementos HTML
- Manutenção da lógica de tratamento de estados e fluxo de automação

#### Testes de Integração

Foram desenvolvidos scripts de teste para validar a integração:
- **teste_integracao_direct.py**: Teste da integração direta entre OrquestradorAdapter e WondercomClient
- **teste_simples.py**: Teste simplificado do WondercomClient

### Fase 4: Configuração de Serviços

#### Configuração de Serviços Systemd

Foram criados e configurados serviços systemd para garantir que a API e o worker sejam iniciados automaticamente:
- **wondercom-api.service**: Serviço para a API REST
- **wondercom-worker.service**: Serviço para o worker de processamento de filas

#### Configuração de Inicialização Automática

Os serviços foram habilitados para iniciar automaticamente na inicialização da VM:
```bash
sudo systemctl enable wondercom-api
sudo systemctl enable wondercom-worker
```

### Fase 5: Integração Backend-Frontend

#### Implementação do Cliente para VM API no Backend

Foi implementado um cliente no backend para comunicação com a VM API:
- **dashboard/backend/app/services/vm_api/client.py**: Cliente para comunicação com a VM API

#### Implementação de Endpoints de Callback

Foram implementados endpoints de callback no backend para receber resultados assíncronos da VM:
- **dashboard/backend/app/routes/callbacks.py**: Endpoints para receber callbacks da VM

#### Extensão dos Endpoints do Backend

Foram estendidos os endpoints existentes no backend para utilizar a VM API:
- **dashboard/backend/app/routes/wondercom.py**: Rotas estendidas para alocação de WO e cálculo de KMs

#### Implementação de Componentes no Frontend

Foram implementados componentes no frontend para interagir com o backend:
- **dashboard/frontend/src/components/WorkOrderAllocation.jsx**: Componente de alocação de WO
- **dashboard/frontend/src/components/TaskMonitor.jsx**: Monitor de tarefas
- **dashboard/frontend/src/components/KilometersCalculator.jsx**: Calculadora de KMs
- **dashboard/frontend/src/components/EarningsSimulator.jsx**: Simulador de ganhos

## Arquitetura do Sistema

### Diagrama de Arquitetura

```
+-------------------+       +-------------------+       +-------------------+
|                   |       |                   |       |                   |
|     Frontend      |       |     Backend       |       |       VM API      |
|    (React/Netlify)|------>|    (Flask/Render) |------>|  (Flask/Redis)    |
|                   |       |                   |       |                   |
+-------------------+       +-------------------+       +--------+----------+
                                                                 |
                                                                 v
                                                        +-------------------+
                                                        |                   |
                                                        |  WondercomClient  |
                                                        |    (Selenium)     |
                                                        |                   |
                                                        +--------+----------+
                                                                 |
                                                                 v
                                                        +-------------------+
                                                        |                   |
                                                        |  Portal Wondercom |
                                                        |                   |
                                                        +-------------------+
```

### Fluxo de Comunicação

1. O usuário interage com o frontend para alocar uma WO
2. O frontend envia uma requisição para o backend
3. O backend envia uma requisição para a VM API
4. A VM API coloca a tarefa na fila Redis
5. O worker processa a tarefa, utilizando o WondercomClient para interagir com o portal
6. O resultado é retornado através da cadeia de componentes até o frontend

## Componentes Implementados

### VM API

#### app.py
```python
"""
Aplicação principal da VM API.
"""
from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

from .routes.allocate import AllocateResource
from .routes.process import ProcessResource
from .routes.status import StatusResource, HealthResource

app = Flask(__name__)
CORS(app)
api = Api(app, prefix='/api')

# Registrar recursos
api.add_resource(AllocateResource, '/allocate')
api.add_resource(ProcessResource, '/process')
api.add_resource(StatusResource, '/status/<task_id>')
api.add_resource(HealthResource, '/health')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### orquestrador_adapter.py
```python
"""
Adaptador para o módulo orquestrador de PDFs.
Este arquivo conecta a API REST aos scripts existentes de orquestração,
utilizando o cliente Selenium existente para alocação de WO.
"""
import sys
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar os scripts existentes
try:
    import M2_Orquestrador_PDFs as orquestrador
    logger.info("Módulo M2_Orquestrador_PDFs importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar M2_Orquestrador_PDFs: {e}")
    raise

# Importar o WondercomClient diretamente
try:
    from vm_api.wondercom_client import WondercomClient
    logger.info("Módulo WondercomClient importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar WondercomClient: {e}")
    raise

# Importar configurações
from .. import config

class OrquestradorAdapter:
    @staticmethod
    def processar_pdf(caminho_pdf, tecnico_id, credenciais=None):
        """
        Adaptador para a função de processamento de PDF.
        """
        logger.info(f"Iniciando processamento do PDF: {caminho_pdf} para técnico: {tecnico_id}")
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(caminho_pdf):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_pdf}")
            
            # Chamar a função do script existente
            resultado = orquestrador.processar_pdf(caminho_pdf, tecnico_id)
            logger.info(f"Processamento concluído com sucesso para: {caminho_pdf}")
            
            # Formatar o resultado conforme esperado pela API
            return {
                "status": "success",
                "data": resultado
            }
        except Exception as e:
            logger.error(f"Erro no processamento do PDF {caminho_pdf}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def alocar_wo(work_order_id, credenciais):
        """
        Adaptador para a função de alocação de WO.
        Utiliza o WondercomClient diretamente para realizar a alocação.
        """
        logger.info(f"Iniciando alocação da WO: {work_order_id}")
        
        # Obter configurações do arquivo config.py ou usar valores padrão
        chrome_driver_path = getattr(config, 'CHROME_DRIVER_PATH', '/usr/bin/chromedriver')
        portal_url = getattr(config, 'WONDERCOM_PORTAL_URL', 'https://portal.wondercom.pt')
        
        # Extrair credenciais
        username = credenciais.get('username')
        password = credenciais.get('password')
        
        if not username or not password:
            return {
                "status": "error",
                "error": "Credenciais incompletas",
                "error_type": "ValueError"
            }
        
        client = None
        try:
            # Inicializar o cliente Selenium diretamente
            client = WondercomClient(
                chrome_driver_path=chrome_driver_path,
                portal_url=portal_url,
                username=username,
                password=password
            )
            
            # Iniciar o driver
            client.start_driver()
            
            # Realizar login
            login_success = client.login()
            if not login_success:
                raise Exception("Falha no login")
            
            # Alocar a ordem de trabalho
            result = client.allocate_work_order(work_order_id)
            
            if result.get("success"):
                # Extrair dados relevantes
                dados_wo = result.get('dados', {})
                
                # Formatar o resultado conforme esperado pela API
                formatted_result = {
                    "status": "success",
                    "data": {
                        "endereco": dados_wo.get('morada', 'N/A'),
                        "pdo": dados_wo.get('slid', 'N/A'),
                        "cor_fibra": dados_wo.get('fibra', 'N/A'),
                        "cor_fibra_hex": "#0000FF",
                        "latitude": None,
                        "longitude": None,
                        "estado": dados_wo.get('estado', 'N/A'),
                        "descricao": dados_wo.get('descricao', 'N/A')
                    }
                }
                
                # Extrair coordenadas se disponíveis
                coordenadas = dados_wo.get('coordenadas')
                if coordenadas:
                    try:
                        lat, lng = coordenadas.split(',')
                        formatted_result["data"]["latitude"] = float(lat.strip())
                        formatted_result["data"]["longitude"] = float(lng.strip())
                    except Exception as e:
                        logger.warning(f"Erro ao extrair coordenadas: {e}")
                
                logger.info(f"Alocação concluída com sucesso para WO: {work_order_id}")
                return formatted_result
            else:
                # Retornar erro
                error_message = result.get('message', 'Erro desconhecido na alocação')
                logger.error(f"Erro na alocação da WO {work_order_id}: {error_message}")
                return {
                    "status": "error",
                    "error": error_message,
                    "error_type": "AllocationError"
                }
        except Exception as e:
            logger.error(f"Erro na alocação da WO {work_order_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            # Garantir que o navegador seja fechado em caso de erro
            try:
                if client:
                    client.close_driver()
            except Exception as e:
                logger.warning(f"Erro ao fechar o navegador: {e}")
```

### Backend

#### client.py
```python
"""
Cliente para comunicação com a VM API.
"""
import requests
import logging
import os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class VMApiClient:
    def __init__(self):
        self.base_url = os.environ.get('VM_API_URL', 'http://localhost:5000')
        self.api_key = os.environ.get('VM_API_KEY', 'api-key-temporaria')
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
    
    def allocate_work_order(self, work_order_id, credentials):
        """
        Aloca uma ordem de trabalho.
        """
        url = urljoin(self.base_url, '/api/allocate')
        payload = {
            'work_order_id': work_order_id,
            'credentials': credentials
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao alocar WO {work_order_id}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def process_pdf(self, pdf_path, technician_id, credentials=None):
        """
        Processa um PDF.
        """
        url = urljoin(self.base_url, '/api/process')
        payload = {
            'pdf_path': pdf_path,
            'technician_id': technician_id
        }
        
        if credentials:
            payload['credentials'] = credentials
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao processar PDF {pdf_path}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def check_task_status(self, task_id):
        """
        Verifica o status de uma tarefa.
        """
        url = urljoin(self.base_url, f'/api/status/{task_id}')
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao verificar status da tarefa {task_id}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
```

### Serviços Systemd

#### wondercom-api.service
```ini
[Unit]
Description=Wondercom VM API
After=network.target

[Service]
User=flavioleal
WorkingDirectory=/home/flavioleal/Sistema
ExecStart=/home/flavioleal/Sistema/venv/bin/python -m vm_api.app
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=wondercom-api
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

#### wondercom-worker.service
```ini
[Unit]
Description=Wondercom VM Worker
After=network.target

[Service]
User=flavioleal
WorkingDirectory=/home/flavioleal/Sistema
ExecStart=/home/flavioleal/Sistema/venv/bin/python -m vm_api.queue.worker
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=wondercom-worker
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## Fluxos de Comunicação

### Fluxo de Alocação de WO

1. **Frontend → Backend**:
   - Usuário insere ID da WO e credenciais no frontend
   - Frontend envia requisição POST para `/api/wondercom/allocate`

2. **Backend → VM API**:
   - Backend recebe requisição e chama o cliente VM API
   - Cliente VM API envia requisição POST para `http://<vm-ip>:5000/api/allocate`

3. **VM API → Redis**:
   - VM API recebe requisição e coloca tarefa na fila Redis
   - Worker pega tarefa da fila e inicia processamento

4. **Worker → WondercomClient**:
   - Worker chama OrquestradorAdapter.alocar_wo()
   - OrquestradorAdapter inicializa WondercomClient
   - WondercomClient executa automação no portal

5. **WondercomClient → Worker → VM API → Backend → Frontend**:
   - WondercomClient retorna resultado da alocação
   - Worker atualiza status da tarefa
   - Backend consulta status e retorna para frontend
   - Frontend exibe resultado para o usuário

### Fluxo de Processamento de PDF

1. **Frontend → Backend**:
   - Usuário seleciona PDF para processamento
   - Frontend envia requisição POST para `/api/wondercom/process`

2. **Backend → VM API**:
   - Backend recebe requisição e chama o cliente VM API
   - Cliente VM API envia requisição POST para `http://<vm-ip>:5000/api/process`

3. **VM API → Redis**:
   - VM API recebe requisição e coloca tarefa na fila Redis
   - Worker pega tarefa da fila e inicia processamento

4. **Worker → OrquestradorAdapter**:
   - Worker chama OrquestradorAdapter.processar_pdf()
   - OrquestradorAdapter chama script M2_Orquestrador_PDFs

5. **OrquestradorAdapter → Worker → VM API → Backend → Frontend**:
   - OrquestradorAdapter retorna resultado do processamento
   - Worker atualiza status da tarefa
   - Backend consulta status e retorna para frontend
   - Frontend exibe resultado para o usuário

## Próximos Passos

### 1. Validação do Fluxo Ponta a Ponta

- **Verificar configuração do backend**:
  - Confirmar que a variável de ambiente `VM_API_URL` no Render aponta para o IP correto da VM (34.88.3.237:5000)
  - Verificar se a chave de API está configurada corretamente

- **Testar o fluxo completo através do frontend**:
  - Acessar o dashboard no Netlify
  - Utilizar o componente de alocação de WO
  - Verificar se a solicitação chega ao backend e é encaminhada para a VM
  - Confirmar que a VM executa o WondercomClient corretamente
  - Validar que o resultado retorna ao frontend e é exibido para o usuário

- **Monitorar logs em todos os componentes**:
  - Logs do frontend para verificar chamadas à API
  - Logs do backend para verificar comunicação com a VM
  - Logs da VM para verificar execução do WondercomClient

### 2. Correção do Frontend

- **Localizar e corrigir componentes que ainda usam dados de teste**:
  - Identificar arquivos que contêm dados mockados
  - Substituir por chamadas reais à API
  - Testar as alterações

### 3. Implementação de Funcionalidades Adicionais

- **Calculadora de KMs**:
  - Implementar integração com API de mapas
  - Desenvolver algoritmo de cálculo de distância
  - Integrar com o frontend

- **Simulador de Ganhos**:
  - Implementar lógica de cálculo de ganhos
  - Integrar com o frontend
  - Testar com diferentes cenários

### 4. Melhorias de Robustez e Escalabilidade

- **Implementar mecanismo de retry**:
  - Adicionar lógica de retry para operações que falham
  - Configurar backoff exponencial

- **Melhorar tratamento de erros**:
  - Implementar tratamento de erros mais detalhado
  - Adicionar logs mais informativos

- **Implementar monitoramento**:
  - Configurar sistema de monitoramento para detectar falhas
  - Implementar alertas para problemas críticos

## Recomendações Técnicas

### Manutenção do WondercomClient

- **Alterações no WondercomClient**:
  - Ao modificar o WondercomClient, mantenha os nomes dos métodos e parâmetros
  - Se alterar seletores XPath, atualize a documentação
  - Teste exaustivamente após qualquer alteração

- **Alterações na Interface do Portal**:
  - Se a interface do Portal Wondercom mudar, atualize os seletores XPath
  - Verifique todos os fluxos de alocação após atualizações do portal

### Configuração do Ambiente

- **ChromeDriver**:
  - Certifique-se de que o ChromeDriver está instalado e configurado corretamente
  - O caminho do ChromeDriver deve ser especificado no arquivo de configuração

- **Redis**:
  - Monitore o uso de memória do Redis
  - Configure persistência para evitar perda de dados

- **Serviços Systemd**:
  - Verifique regularmente o status dos serviços
  - Configure rotação de logs para evitar arquivos muito grandes

### Segurança

- **API Key**:
  - Substitua a API key temporária por uma chave segura em produção
  - Armazene a chave em variáveis de ambiente, não no código

- **Credenciais**:
  - Não armazene credenciais em texto plano
  - Considere implementar um sistema de gerenciamento de segredos

## Apêndices

### Comandos Úteis

#### Verificar Status dos Serviços
```bash
sudo systemctl status wondercom-api
sudo systemctl status wondercom-worker
```

#### Reiniciar Serviços
```bash
sudo systemctl restart wondercom-api
sudo systemctl restart wondercom-worker
```

#### Ver Logs dos Serviços
```bash
sudo journalctl -u wondercom-api -f
sudo journalctl -u wondercom-worker -f
```

#### Testar a API Diretamente
```bash
curl -X GET http://localhost:5000/api/health -H "X-API-Key: api-key-temporaria"
```

### Estrutura de Arquivos Completa

```
/home/flavioleal/Sistema/
├── M1_Criar_Tecnico.py
├── M1_Extrator_PDF.py
├── M2_Orquestrador_PDFs.py
├── M3_Leitura_Drive.py
├── M4_Manipulacao_Arquivos.py
├── M5_Config_Tecnicos.py
├── M6_Notificacao_Status.py
├── M7_Busca_Equipamentos.py
├── venv/
└── vm_api/
    ├── adapters/
    │   ├── __init__.py
    │   ├── extrator_adapter.py
    │   ├── orquestrador_adapter.py
    │   ├── notificacao_adapter.py
    │   └── wondercom_integration.py
    ├── routes/
    │   ├── __init__.py
    │   ├── allocate.py
    │   ├── process.py
    │   └── status.py
    ├── queue/
    │   ├── __init__.py
    │   ├── producer.py
    │   └── worker.py
    ├── app.py
    ├── auth.py
    ├── config.py
    ├── __init__.py
    └── wondercom_client.py
```

### Variáveis de Ambiente

#### Backend (Render)
- `VM_API_URL`: URL da VM API (ex: http://34.88.3.237:5000)
- `VM_API_KEY`: Chave de API para autenticação (ex: api-key-temporaria)

#### VM API
- `REDIS_URL`: URL do servidor Redis (padrão: localhost:6379)
- `CHROME_DRIVER_PATH`: Caminho para o ChromeDriver (padrão: /usr/bin/chromedriver)
- `WONDERCOM_PORTAL_URL`: URL do portal Wondercom (padrão: https://portal.wondercom.pt)
