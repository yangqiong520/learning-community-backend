-- 创建制度规范表
CREATE TABLE IF NOT EXISTS regulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    document_file_id INT NOT NULL COMMENT '文档文件ID',
    image_file_id INT NOT NULL COMMENT '图片文件ID',
    uploader_id INT NOT NULL COMMENT '上传者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (document_file_id) REFERENCES files(id) ON DELETE RESTRICT,
    FOREIGN KEY (image_file_id) REFERENCES files(id) ON DELETE RESTRICT,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_uploader (uploader_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建收藏表
CREATE TABLE IF NOT EXISTS likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    regulation_id INT NOT NULL COMMENT '制度规范ID',
    user_id INT NOT NULL COMMENT '用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    FOREIGN KEY (regulation_id) REFERENCES regulations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_like (regulation_id, user_id) COMMENT '防止重复收藏',
    INDEX idx_regulation (regulation_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
