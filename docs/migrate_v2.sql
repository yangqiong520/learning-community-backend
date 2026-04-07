-- 数据库表结构更新脚本 v1 -> v2
-- 执行此脚本以更新 users 表结构

-- 添加 phone 字段
ALTER TABLE users ADD COLUMN phone VARCHAR(20) UNIQUE AFTER password;

-- 将 email 字段改为可选（允许 NULL）
ALTER TABLE users MODIFY COLUMN email VARCHAR(100) NULL;

-- 将 real_name 字段改为可选（允许 NULL）
ALTER TABLE users MODIFY COLUMN real_name VARCHAR(50) NULL;

-- 创建索引以提高查询性能
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_username ON users(username);

-- 验证表结构
DESCRIBE users;