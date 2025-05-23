# Guia de Contribuição

## Introdução

Obrigado por considerar contribuir para o Projeto-Geral! Este documento fornece diretrizes e instruções para contribuir com o projeto de forma eficiente e consistente.

## Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Começar](#como-começar)
3. [Processo de Desenvolvimento](#processo-de-desenvolvimento)
4. [Padrões de Código](#padrões-de-código)
5. [Processo de Pull Request](#processo-de-pull-request)
6. [Estrutura do Projeto](#estrutura-do-projeto)
7. [Testes](#testes)
8. [Documentação](#documentação)

## Código de Conduta

Ao participar deste projeto, você concorda em manter um ambiente respeitoso e colaborativo. Esperamos que todos os contribuidores:

- Sejam respeitosos e inclusivos
- Aceitem críticas construtivas
- Foquem no que é melhor para a comunidade
- Mostrem empatia com outros membros da comunidade

## Como Começar

### Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/lealflavio/Projeto-Geral.git
   cd Projeto-Geral
   ```

2. Configure o ambiente para os scripts de automação:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure as credenciais necessárias seguindo as instruções no README.md

### Familiarize-se com o Projeto

Antes de começar a contribuir, recomendamos:

1. Ler o [README.md](README.md) para entender a visão geral do projeto
2. Revisar a [Documentação Detalhada](docs/documentacao_detalhada.md)
3. Entender o [Mapeamento da Estrutura](docs/mapeamento_estrutura.md)
4. Verificar as [Propostas de Melhorias](docs/propostas_melhorias.md)

## Processo de Desenvolvimento

### Fluxo de Trabalho com Git

1. **Crie um branch para sua feature ou correção**:
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```

2. **Faça commits frequentes e atômicos**:
   ```bash
   git commit -m "[Componente] Descrição clara da alteração"
   ```

3. **Mantenha seu branch atualizado**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Envie seu branch para o repositório remoto**:
   ```bash
   git push origin feature/nome-da-feature
   ```

### Sistema Centralizado de Configurações

Todas as novas implementações devem utilizar o sistema centralizado de configurações. Consulte o [Guia de Migração](docs/migracao_configuracoes.md) para mais detalhes.

### Caminhos Relativos

O projeto está migrando de caminhos absolutos para caminhos relativos. Todas as novas contribuições devem seguir este padrão.

## Padrões de Código

### Python

- Siga a [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use docstrings para documentar funções e classes
- Mantenha funções pequenas e com responsabilidade única
- Utilize nomes descritivos para variáveis e funções

Exemplo:
```python
def extrair_dados_cliente(texto_pdf):
    """
    Extrai informações do cliente a partir do texto do PDF.
    
    Args:
        texto_pdf (str): Texto extraído do PDF
        
    Returns:
        dict: Dicionário com os dados do cliente
    """
    # Implementação
    pass
```

### JavaScript/React

- Utilize ES6+ e hooks modernos do React
- Siga o estilo de código do Airbnb
- Prefira componentes funcionais e hooks
- Mantenha componentes pequenos e reutilizáveis

Exemplo:
```javascript
// Componente React
const TecnicoCard = ({ tecnico, onSelect }) => {
  return (
    <div className="tecnico-card" onClick={() => onSelect(tecnico.id)}>
      <h3>{tecnico.nome}</h3>
      <p>Total de relatórios: {tecnico.totalRelatorios}</p>
    </div>
  );
};
```

### Convenções de Nomenclatura

- **Arquivos Python**: snake_case (ex: `extrator_pdf.py`)
- **Classes Python**: PascalCase (ex: `class ExtratorPDF:`)
- **Funções/Variáveis Python**: snake_case (ex: `extrair_dados()`)
- **Arquivos JavaScript**: camelCase (ex: `tecnicoService.js`)
- **Componentes React**: PascalCase (ex: `TecnicoCard.jsx`)
- **Funções/Variáveis JavaScript**: camelCase (ex: `getDadosTecnico()`)

## Processo de Pull Request

1. **Crie um Pull Request (PR)** para o branch `main`
2. **Descreva claramente as alterações** realizadas
3. **Vincule issues relacionadas** usando palavras-chave (ex: "Closes #123")
4. **Aguarde a revisão** de pelo menos um mantenedor
5. **Responda a comentários** e faça as alterações solicitadas
6. **Atualize seu PR** se necessário com `git push --force-with-lease`

### Template de Pull Request

```markdown
## Descrição
Breve descrição das alterações realizadas.

## Tipo de Alteração
- [ ] Correção de bug
- [ ] Nova funcionalidade
- [ ] Melhoria de desempenho
- [ ] Refatoração de código
- [ ] Documentação

## Issues Relacionadas
Closes #123

## Checklist
- [ ] Código segue os padrões do projeto
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] Alterações são compatíveis com o sistema centralizado de configurações
```

## Estrutura do Projeto

Familiarize-se com a [estrutura do projeto](docs/mapeamento_estrutura.md) antes de contribuir. Respeite a organização existente e consulte os mantenedores antes de fazer alterações estruturais significativas.

## Testes

### Testes Unitários

- Escreva testes unitários para novas funcionalidades
- Mantenha ou melhore a cobertura de testes existente
- Execute os testes antes de enviar um PR

```bash
# Executar testes
python -m unittest discover tests
```

### Testes Manuais

Para funcionalidades que envolvem interação com serviços externos:

1. Documente os passos para teste manual
2. Inclua casos de teste e resultados esperados
3. Verifique diferentes cenários (sucesso, erro, limites)

## Documentação

### Documentação de Código

- Documente todas as funções, classes e módulos
- Mantenha a documentação atualizada com as alterações de código
- Inclua exemplos de uso quando apropriado

### Documentação do Projeto

- Atualize o README.md quando necessário
- Mantenha a documentação na pasta `docs/` atualizada
- Crie novos documentos para funcionalidades complexas

## Dúvidas e Suporte

Se tiver dúvidas sobre como contribuir, entre em contato com a equipe de desenvolvimento ou abra uma issue no GitHub.

---

Agradecemos sua contribuição para tornar o Projeto-Geral melhor!
