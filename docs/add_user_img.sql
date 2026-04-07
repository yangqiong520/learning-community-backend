-- 添加 user_img 字段到 users 表
ALTER TABLE `users` ADD COLUMN `user_img` VARCHAR(500) NULL COMMENT '用户头像URL' AFTER `role`;

-- 为现有用户设置默认头像（可选）
UPDATE `users` SET `user_img` = NULL WHERE `user_img` IS NULL;
