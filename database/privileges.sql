-- 创建专用数据库用户
CREATE USER IF NOT EXISTS 'mysql_practice'@'localhost' IDENTIFIED BY 'practice_pass_2024';

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS mysql_exercise_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 授予权限
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, EXECUTE
ON mysql_exercise_db.*
TO 'mysql_practice'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用新创建的数据库
USE mysql_exercise_db; 