# Padrões de Código para o Projeto-Geral

Este documento define os padrões de código a serem seguidos no projeto Projeto-Geral, tanto para Python quanto para JavaScript/React. Estes padrões visam garantir consistência, legibilidade e manutenibilidade do código.

## Padrões para Python

### Estilo de Código

- **Guia de Estilo**: Seguir a [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **Comprimento de Linha**: Máximo de 88 caracteres (compatível com Black)
- **Indentação**: 4 espaços (sem tabs)
- **Codificação**: UTF-8

### Convenções de Nomenclatura

- **Arquivos**: `snake_case.py` (ex: `extrator_pdf.py`)
- **Classes**: `PascalCase` (ex: `class ExtratorPDF:`)
- **Funções/Métodos**: `snake_case` (ex: `def extrair_dados():`)
- **Variáveis**: `snake_case` (ex: `nome_arquivo = "relatorio.pdf"`)
- **Constantes**: `UPPER_SNAKE_CASE` (ex: `MAX_TENTATIVAS = 3`)
- **Módulos/Pacotes**: `snake_case` (ex: `import processamento_pdf`)

### Docstrings

- Usar docstrings no estilo Google para documentar funções, classes e métodos
- Incluir descrição, parâmetros, retorno e exceções quando relevante

```python
def extrair_dados_cliente(texto_pdf):
    """
    Extrai informações do cliente a partir do texto do PDF.
    
    Args:
        texto_pdf (str): Texto extraído do PDF
        
    Returns:
        dict: Dicionário com os dados do cliente
        
    Raises:
        ValueError: Se o texto não contiver as informações necessárias
    """
    # Implementação
    pass
```

### Imports

- Organizar imports na seguinte ordem, separados por uma linha em branco:
  1. Bibliotecas padrão do Python
  2. Bibliotecas de terceiros
  3. Imports locais da aplicação
- Dentro de cada grupo, ordenar alfabeticamente

```python
import os
import sys
from datetime import datetime

import pandas as pd
import requests
from selenium import webdriver

from config.config import config
from utils.helpers import formatar_data
```

### Comentários

- Usar comentários para explicar "por quê", não "o quê" ou "como"
- Manter comentários atualizados com o código
- Evitar comentários óbvios ou redundantes

### Estrutura de Arquivos

- Cada arquivo deve ter uma única responsabilidade
- Limitar o tamanho dos arquivos (máximo recomendado: 500 linhas)
- Seguir a estrutura:
  1. Docstring do módulo
  2. Imports
  3. Constantes
  4. Classes/Funções
  5. Bloco `if __name__ == "__main__":`

## Padrões para JavaScript/React

### Estilo de Código

- **Guia de Estilo**: Seguir o [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **Comprimento de Linha**: Máximo de 100 caracteres
- **Indentação**: 2 espaços (sem tabs)
- **Ponto e Vírgula**: Obrigatório ao final das declarações
- **Aspas**: Aspas simples para strings

### Convenções de Nomenclatura

- **Arquivos**:
  - Componentes React: `PascalCase.jsx` (ex: `UserProfile.jsx`)
  - Outros arquivos JS: `camelCase.js` (ex: `apiService.js`)
- **Componentes React**: `PascalCase` (ex: `function UserProfile() {}`)
- **Funções**: `camelCase` (ex: `function getUserData() {}`)
- **Variáveis**: `camelCase` (ex: `const userData = {}`)
- **Constantes**: `UPPER_SNAKE_CASE` (ex: `const MAX_RETRY_COUNT = 3`)
- **Props React**: `camelCase` (ex: `<Component userName="John" />`)

### Estrutura de Componentes React

- Preferir componentes funcionais com hooks
- Organizar imports, props, hooks e funções auxiliares de forma consistente
- Extrair lógica complexa para hooks personalizados

```javascript
// Exemplo de estrutura de componente
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

import { fetchUserData } from '../services/userService';
import UserAvatar from './UserAvatar';

const UserProfile = ({ userId, showDetails }) => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadUserData = async () => {
      try {
        setLoading(true);
        const data = await fetchUserData(userId);
        setUserData(data);
      } catch (error) {
        console.error('Failed to load user data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadUserData();
  }, [userId]);
  
  if (loading) return <div>Carregando...</div>;
  if (!userData) return <div>Usuário não encontrado</div>;
  
  return (
    <div className="user-profile">
      <UserAvatar src={userData.avatarUrl} alt={userData.name} />
      <h2>{userData.name}</h2>
      {showDetails && (
        <div className="user-details">
          <p>Email: {userData.email}</p>
          <p>Função: {userData.role}</p>
        </div>
      )}
    </div>
  );
};

UserProfile.propTypes = {
  userId: PropTypes.string.isRequired,
  showDetails: PropTypes.bool,
};

UserProfile.defaultProps = {
  showDetails: false,
};

export default UserProfile;
```

### Imports

- Organizar imports na seguinte ordem, separados por uma linha em branco:
  1. Bibliotecas React e pacotes de terceiros
  2. Imports de serviços, utils, etc.
  3. Imports de componentes
  4. Imports de estilos/CSS

### Estado e Props

- Desestruturar props e estado quando apropriado
- Usar prop-types para validação de props
- Definir valores padrão para props opcionais

### CSS/Estilização

- Preferir CSS-in-JS ou módulos CSS para evitar conflitos de nomes
- Seguir nomenclatura BEM (Block Element Modifier) para classes CSS quando aplicável
- Manter estilos próximos aos componentes que os utilizam

## Padrões Comuns (Python e JavaScript)

### Gestão de Erros

- Tratar erros de forma explícita e específica
- Evitar capturar exceções genéricas (`except:` ou `catch {}`)
- Registrar erros com informações de contexto suficientes

### Segurança

- Nunca armazenar credenciais ou segredos diretamente no código
- Usar o sistema centralizado de configurações para valores sensíveis
- Validar entradas de usuário e dados externos

### Logging

- Usar níveis de log apropriados (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Incluir informações de contexto relevantes nas mensagens de log
- Evitar logging excessivo em produção

### Testes

- Escrever testes unitários para funções e componentes
- Manter cobertura de testes adequada para código crítico
- Seguir o padrão AAA (Arrange, Act, Assert) para estruturar testes

## Ferramentas de Verificação

### Python

- **Linting**: flake8, pylint
- **Formatação**: black
- **Verificação de tipos**: mypy (opcional)

### JavaScript/React

- **Linting**: ESLint com configuração Airbnb
- **Formatação**: Prettier
- **Verificação de tipos**: PropTypes (obrigatório), TypeScript (opcional)

## Exceções aos Padrões

Algumas partes do código podem ter exceções justificadas aos padrões definidos:

1. **Código legado**: Aplicar padrões gradualmente durante refatorações
2. **Integrações com bibliotecas externas**: Adaptar ao estilo exigido pela biblioteca
3. **Otimizações de desempenho**: Documentar claramente quando otimizações violarem os padrões

Qualquer exceção deve ser documentada com comentários explicando o motivo.
