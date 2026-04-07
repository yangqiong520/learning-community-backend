-- 修改likes表以支持两种类型（regulation和training_program）

-- 查看当前外键
-- SHOW CREATE TABLE likes;

-- 删除旧的外键约束
ALTER TABLE `likes` DROP FOREIGN KEY `likes_ibfk_1`;

-- 修改regulation_id允许为NULL
ALTER TABLE `likes` MODIFY COLUMN `regulation_id` INT NULL;

-- 添加training_program_id列
ALTER TABLE `likes` ADD COLUMN `training_program_id` INT NULL COMMENT '培养方案ID' AFTER `regulation_id`;

-- 添加新的外键约束
ALTER TABLE `likes` ADD CONSTRAINT `fk_likes_training_program` FOREIGN KEY (`training_program_id`) REFERENCES `training_programs` (`id`) ON DELETE CASCADE;

-- 重新添加regulation的外键约束（允许NULL）
ALTER TABLE `likes` ADD CONSTRAINT `fk_likes_regulation` FOREIGN KEY (`regulation_id`) REFERENCES `regulations` (`id`) ON DELETE CASCADE;

-- 删除旧的唯一约束
-- ALTER TABLE `likes` DROP INDEX `unique_like`;

-- 添加新的唯一约束（使用 IGNORE 忽略重复数据）
ALTER TABLE `likes` ADD UNIQUE KEY `unique_regulation_like` (`regulation_id`, `user_id`);
ALTER TABLE `likes` ADD UNIQUE KEY `unique_training_program_like` (`training_program_id`, `user_id`);