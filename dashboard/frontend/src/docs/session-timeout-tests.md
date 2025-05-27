# Documentação de Testes - Expiração Automática de Sessão

## Resumo
Este documento descreve os testes realizados para validar o funcionamento do mecanismo de expiração automática de sessão por inatividade implementado no frontend da aplicação Wondercom Automation.

## Componentes Implementados

1. **SessionTimeoutHandler.jsx**
   - Componente principal que monitora a inatividade do usuário
   - Exibe aviso 30 segundos antes da expiração
   - Realiza logout e redirecionamento para login após 5 minutos de inatividade

2. **Integração com App.jsx**
   - Aplicado a todas as rotas protegidas
   - Envolve o Layout principal da aplicação

3. **Componentes de Teste**
   - TestSessionTimeout.jsx para simulação visual
   - TestPage.jsx para documentação e validação de testes

## Casos de Teste

| ID | Descrição | Resultado Esperado | Resultado Obtido |
|----|-----------|-------------------|-----------------|
| 01 | Renderização do componente | O componente é renderizado sem erros | PASSOU |
| 02 | Detecção de inatividade | O sistema detecta corretamente a ausência de interação | PASSOU |
| 03 | Exibição de aviso | Aviso é exibido 30 segundos antes do timeout | PASSOU |
| 04 | Redirecionamento após expiração | Usuário é redirecionado para login após 5 minutos | PASSOU |
| 05 | Reset do timer com interação | Timer é reiniciado quando há interação do usuário | PASSOU |
| 06 | Fechamento do aviso com interação | Aviso é fechado quando há interação do usuário | PASSOU |

## Eventos Monitorados

O sistema monitora os seguintes eventos para detectar atividade do usuário:
- mousedown
- mousemove
- keypress
- scroll
- touchstart
- click
- keydown
- keyup

## Configurações

- **Tempo de inatividade**: 5 minutos (300.000 ms)
- **Tempo para aviso**: 4,5 minutos (270.000 ms)
- **Verificação de inatividade**: A cada 1 segundo

## Observações

1. O sistema funciona de forma transparente para o usuário, sem interferir na experiência normal de uso.
2. O aviso de expiração permite que o usuário continue a sessão com um simples clique.
3. A implementação é puramente frontend, não dependendo de alterações no backend.
4. O mecanismo é compatível com o sistema de autenticação existente baseado em JWT.

## Conclusão

O mecanismo de expiração automática de sessão por inatividade foi implementado com sucesso e validado através de testes. A solução atende ao requisito de expirar a sessão após 5 minutos de inatividade e redirecionar o usuário para a página de login.
