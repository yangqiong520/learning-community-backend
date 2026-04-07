-- 创建数据库
CREATE DATABASE IF NOT EXISTS learning_community CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE learning_community;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) NULL UNIQUE,
    real_name VARCHAR(50) NOT NULL,
    role INT NOT NULL DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_phone (phone),
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入测试数据（可选）
-- 密码：123456 (SHA256加密后: 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92)
INSERT INTO users (username, password, phone, email, real_name, role, is_active) VALUES
('admin', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '13800138000', 'admin@example.com', '超级管理员', 1, TRUE),
('teacher', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '13800138001', 'teacher@example.com', '教师', 3, TRUE),
('student', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '13800138002', NULL, '学生', 4, TRUE);

-- 授予权限（根据实际情况修改）
-- GRANT ALL PRIVILEGES ON learning_community.* TO 'your_username'@'localhost';
-- FLUSH PRIVILEGES;

-- 验证表结构
DESCRIBE users;