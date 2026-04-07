-- 为files表添加pdf_file_id字段
ALTER TABLE files ADD COLUMN pdf_file_id INT NULL;

-- 添加外键约束
ALTER TABLE files ADD CONSTRAINT fk_files_pdf_file_id FOREIGN KEY (pdf_file_id) REFERENCES files(id);

-- 添加索引
CREATE INDEX idx_files_pdf_file_id ON files(pdf_file_id);
