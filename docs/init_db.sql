-- 创建数据库
CREATE DATABASE IF NOT EXISTS learning_community CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE learning_community;

-- 用户表（由Flask-SQLAlchemy自动创建，这里仅作为参考）
-- CREATE TABLE users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     password VARCHAR(255) NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     real_name VARCHAR(50) NOT NULL,
--     role INT NOT NULL DEFAULT 3,
--     is_active BOOLEAN DEFAULT TRUE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
-- );

-- 插入默认超级管理员
-- 用户名: admin
-- 密码: admin123 (SHA256加密后: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9)
-- 注意：实际使用时，应通过API注册或使用更安全的方式创建用户

-- 可以使用以下SQL插入初始管理员（需要先计算密码的SHA256值）
-- INSERT INTO users (username, password, email, real_name, role, is_active) 
-- VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 
--         'admin@example.com', '系统管理员', 1, TRUE);

-- 授予权限
-- GRANT ALL PRIVILEGES ON learning_community.* TO 'your_username'@'localhost';
-- FLUSH PRIVILEGES;