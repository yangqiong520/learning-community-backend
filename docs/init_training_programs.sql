-- 创建培养方案表
CREATE TABLE IF NOT EXISTS training_programs (
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
