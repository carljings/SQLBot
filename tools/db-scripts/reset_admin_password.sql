-- 重置 admin 用户密码为默认密码 SQLBot@123456
-- MD5("SQLBot@123456") = 8f32d1e371702c1b1b7346f4b07a701d

-- 首先，让我们查看当前的 admin 用户
SELECT id, account, name, email, status FROM sys_user WHERE account = 'admin';

-- 重置密码为默认密码 SQLBot@123456
UPDATE sys_user
SET password = '8f32d1e371702c1b1b7346f4b07a701d'
WHERE account = 'admin';

-- 验证更新
SELECT id, account, name, email, status FROM sys_user WHERE account = 'admin';
