# Plano de Padronização Visual

## Análise do Arquivo de Tema

O arquivo `tailwind.config.js` foi identificado como a fonte central das cores do projeto. Atualmente, ele define as seguintes cores:

```javascript
colors: {
  primary: "#6C63FF",       // botão principal, destaque
  secondary: "#ECEBFF",     // plano de fundo leve
  background: "#FAFAFA",    // fundo geral
  text: "#2E2E2E",          // texto principal
  muted: "#888888",         // texto secundário
  card: "#FFFFFF",          // fundo dos cards
  danger: "#FF6F61",        // sair ou erros
}
```

## Estratégia de Padronização

### 1. Expansão do Arquivo de Tema

Transformaremos o `tailwind.config.js` em um arquivo de tema completo, adicionando:

- Variações de cores (hover, focus, disabled)
- Definições de sombras
- Arredondamento de bordas
- Espaçamentos padrão
- Tipografia consistente
- Transições e animações

### 2. Padronização de Componentes

Criaremos classes consistentes para:

- Botões (primário, secundário, perigo, desabilitado)
- Campos de formulário (input, select, checkbox, radio)
- Cards (padrão, destacado, informativo)
- Tabelas
- Modais e diálogos
- Menus e navegação

### 3. Correções Específicas

- **Menu Lateral Mobile**: Corrigir a visibilidade do botão "Sair" no menu lateral em dispositivos móveis
- **Botão de Menu Mobile**: Ajustar o comportamento do botão de menu durante a rolagem da página
- **Duplicidade de Títulos**: Remover a duplicidade de títulos nas páginas, mantendo apenas o título ao lado do botão de menu

### 4. Responsividade

- Garantir que todos os componentes sejam totalmente responsivos
- Otimizar a experiência em dispositivos móveis
- Melhorar a acessibilidade para todos os usuários

## Implementação

1. Criar um novo branch para as alterações
2. Expandir o arquivo de tema
3. Criar componentes padronizados
4. Aplicar o tema a todas as páginas
5. Corrigir problemas específicos
6. Testar em diferentes dispositivos
7. Criar pull request para a branch master

## Considerações Importantes

- Não alterar seletores de campo ou código importante
- Manter a integridade funcional do sistema
- Documentar todas as alterações
- Garantir que as mudanças sejam aplicadas de forma consistente em todo o projeto
