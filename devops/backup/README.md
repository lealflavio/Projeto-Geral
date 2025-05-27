# Guia de Backup e Recuperação

Este documento descreve como implementar e utilizar o sistema de backup e recuperação configurado para o Projeto Wondercom Automation.

## Estrutura de Arquivos

Os scripts de backup e recuperação estão localizados no diretório `/home/ubuntu/Projeto-Geral/devops/backup/`:

- `backup-script.sh`: Script para realizar backups automáticos
- `restore-script.sh`: Script para restaurar dados a partir de um backup

## Configuração do Backup Automático

### Pré-requisitos

- PostgreSQL Client instalado
- Acesso ao banco de dados
- Diretório de backup com permissões adequadas

### Implementação

1. Copie os scripts para o servidor:
   ```bash
   mkdir -p /opt/wondercom/scripts
   cp /home/ubuntu/Projeto-Geral/devops/backup/*.sh /opt/wondercom/scripts/
   chmod +x /opt/wondercom/scripts/*.sh
   ```

2. Configure as variáveis de ambiente necessárias:
   ```bash
   export DB_PASSWORD=sua_senha_segura
   ```

3. Configure um cron job para execução diária:
   ```bash
   crontab -e
   ```
   
   Adicione a linha:
   ```
   0 2 * * * DB_PASSWORD=sua_senha_segura /opt/wondercom/scripts/backup-script.sh >> /var/log/wondercom-backup.log 2>&1
   ```

## Processo de Backup

O script de backup realiza as seguintes operações:

1. Cria um dump completo do banco de dados PostgreSQL
2. Comprime o arquivo para economizar espaço
3. Remove backups antigos (mais de 7 dias)
4. Registra o resultado no log

## Processo de Restauração

Para restaurar um backup:

1. Execute o script de restauração com o caminho do arquivo de backup:
   ```bash
   DB_PASSWORD=sua_senha_segura /opt/wondercom/scripts/restore-script.sh /backups/backup_20250524_120000.dump.gz
   ```

2. O script irá:
   - Descomprimir o arquivo se necessário
   - Criar um banco de dados temporário para teste
   - Testar a restauração no banco temporário
   - Solicitar confirmação para restaurar no banco principal
   - Realizar a restauração no banco principal se confirmado
   - Limpar o banco temporário

## Boas Práticas

1. **Segurança**
   - Nunca armazene senhas diretamente nos scripts
   - Use variáveis de ambiente ou arquivos de credenciais seguros
   - Restrinja o acesso aos arquivos de backup

2. **Verificação**
   - Teste regularmente o processo de restauração
   - Verifique a integridade dos backups periodicamente
   - Monitore o espaço em disco disponível para backups

3. **Retenção**
   - Mantenha backups diários por pelo menos 7 dias
   - Considere manter backups semanais por 1 mês
   - Para dados críticos, mantenha backups mensais por 1 ano

## Recuperação de Desastres

Em caso de falha completa do sistema:

1. Provisione um novo servidor de banco de dados
2. Instale o PostgreSQL com a mesma versão
3. Execute o script de restauração com o backup mais recente
4. Verifique a integridade dos dados restaurados
5. Atualize as configurações de conexão no backend

## Troubleshooting

### Falha no Backup

Se o backup falhar:
1. Verifique os logs em `/var/log/wondercom-backup.log`
2. Confirme que as credenciais do banco de dados estão corretas
3. Verifique o espaço em disco disponível
4. Tente executar o backup manualmente para diagnóstico

### Falha na Restauração

Se a restauração falhar:
1. Verifique se o arquivo de backup existe e não está corrompido
2. Confirme que as credenciais do banco de dados estão corretas
3. Verifique se há espaço suficiente para a restauração
4. Verifique a compatibilidade de versão do PostgreSQL
