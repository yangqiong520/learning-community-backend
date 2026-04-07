-- 删除不需要的字段
ALTER TABLE `users` DROP COLUMN `email`;
ALTER TABLE `users` DROP COLUMN `real_name`;
ALTER TABLE `users` DROP COLUMN `is_active`;
ALTER TABLE `users` DROP COLUMN `updated_at`;

-- 可选：将role字段改名为role_id（如果数据库字段名是role）
-- ALTER TABLE `users` CHANGE COLUMN `role` `role_id` INT NOT NULL DEFAULT 3;
