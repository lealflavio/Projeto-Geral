#!/bin/bash

# Configurações
BACKUP_DIR="/backups"
RESTORE_FILE=$1
DB_NAME="wondercom_db"
DB_USER="wondercom_db_user"
DB_HOST="dpg-d0i9fd24d50c73b84nj0-a.oregon-postgres.render.com"

# Verificar se o arquivo foi fornecido
if [ -z "$RESTORE_FILE" ]; then
  echo "Uso: ./restore.sh <arquivo_backup>"
  echo "Exemplo: ./restore.sh /backups/backup_20250524_120000.dump.gz"
  exit 1
fi

# Verificar se o arquivo existe
if [ ! -f "$RESTORE_FILE" ]; then
  echo "Arquivo de backup não encontrado: $RESTORE_FILE"
  exit 1
fi

# Descomprimir se necessário
if [[ "$RESTORE_FILE" == *.gz ]]; then
  echo "Descomprimindo arquivo..."
  gunzip -c "$RESTORE_FILE" > "${RESTORE_FILE%.gz}"
  RESTORE_FILE="${RESTORE_FILE%.gz}"
fi

# Criar banco temporário para teste de restauração
TEMP_DB="${DB_NAME}_restore_test"
echo "Criando banco de dados temporário para teste: $TEMP_DB"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -c "CREATE DATABASE $TEMP_DB;"

# Testar restauração no banco temporário
echo "Testando restauração no banco temporário..."
PGPASSWORD=$DB_PASSWORD pg_restore -h $DB_HOST -U $DB_USER -d $TEMP_DB "$RESTORE_FILE"

# Verificar sucesso do teste
if [ $? -eq 0 ]; then
  echo "Teste de restauração bem-sucedido."
  
  # Confirmar restauração para banco principal
  read -p "Deseja restaurar para o banco principal? (s/n): " CONFIRM
  if [ "$CONFIRM" = "s" ]; then
    echo "Restaurando para banco principal: $DB_NAME"
    PGPASSWORD=$DB_PASSWORD pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME --clean "$RESTORE_FILE"
    
    if [ $? -eq 0 ]; then
      echo "Restauração concluída com sucesso!"
    else
      echo "Erro na restauração para banco principal."
      exit 1
    fi
  else
    echo "Restauração para banco principal cancelada pelo usuário."
  fi
else
  echo "Erro no teste de restauração."
  exit 1
fi

# Limpar banco temporário
echo "Removendo banco de dados temporário..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -c "DROP DATABASE $TEMP_DB;"

echo "Processo de restauração finalizado."
