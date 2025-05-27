#!/bin/bash

# Configurações
DB_NAME="wondercom_db"
DB_USER="wondercom_db_user"
DB_HOST="dpg-d0i9fd24d50c73b84nj0-a.oregon-postgres.render.com"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Realizar backup
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f $BACKUP_DIR/backup_$DATE.dump

# Limpar backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -name "backup_*.dump" -type f -mtime +7 -delete

# Verificar sucesso
if [ $? -eq 0 ]; then
  echo "Backup realizado com sucesso: $BACKUP_DIR/backup_$DATE.dump"
else
  echo "Erro ao realizar backup"
  exit 1
fi

# Comprimir backup para economizar espaço
gzip $BACKUP_DIR/backup_$DATE.dump

# Enviar para armazenamento secundário (opcional)
# rclone copy $BACKUP_DIR/backup_$DATE.dump.gz remote:wondercom-backups/
