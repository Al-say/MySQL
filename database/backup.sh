#!/bin/bash

# 配置信息
DB_USER="mysql_practice"
DB_PASS="practice_pass_2024"
DB_NAME="mysql_exercise_db"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
mysqldump -u "$DB_USER" -p"$DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# 压缩备份文件
gzip "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# 删除30天前的备份
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${DB_NAME}_${DATE}.sql.gz" 