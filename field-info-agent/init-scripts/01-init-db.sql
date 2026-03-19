-- =============================================================================
-- Field Info Agent - PostgreSQL 数据库初始化脚本
-- =============================================================================
-- 文件名: 01-init-db.sql
-- 作用: 创建数据库和用户
-- 执行顺序: 第一个执行（Docker 初始化时按文件名排序）
-- 作者: Field Core Team
-- 创建日期: 2026-03-19
-- 版本: 1.0.0
-- =============================================================================

-- =============================================================================
-- 创建应用程序专用角色（用户）
-- =============================================================================

-- 检查并创建 field_user 用户
-- 如果不存在则创建，已存在则跳过
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'field_user') THEN
        CREATE USER field_user WITH 
            PASSWORD 'field_pass'      -- 默认密码，生产环境应在 .env 中配置
            LOGIN                       -- 允许登录
            NOSUPERUSER                 -- 非超级用户
            NOCREATEDB                  -- 不能创建数据库
            NOCREATEROLE                -- 不能创建角色
            NOREPLICATION;              -- 不用于复制
        
        RAISE NOTICE '用户 field_user 已创建';
    ELSE
        RAISE NOTICE '用户 field_user 已存在，跳过创建';
    END IF;
END
$$;

-- =============================================================================
-- 创建应用程序数据库
-- =============================================================================

-- 检查并创建 field_agent 数据库
-- 如果不存在则创建，已存在则跳过
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'field_agent') THEN
        CREATE DATABASE field_agent
            WITH 
            OWNER = field_user           -- 设置数据库所有者
            ENCODING = 'UTF8'            -- 使用 UTF-8 编码
            LC_COLLATE = 'en_US.utf8'    -- 排序规则
            LC_CTYPE = 'en_US.utf8'      -- 字符分类
            TABLESPACE = pg_default      -- 使用默认表空间
            CONNECTION LIMIT = -1;       -- 无连接限制
        
        RAISE NOTICE '数据库 field_agent 已创建';
    ELSE
        RAISE NOTICE '数据库 field_agent 已存在，跳过创建';
    END IF;
END
$$;

-- =============================================================================
-- 授权
-- =============================================================================

-- 为 field_user 授予 field_agent 数据库的所有权限
GRANT ALL PRIVILEGES ON DATABASE field_agent TO field_user;

-- 授予 schema 创建权限（用于后续初始化）
ALTER USER field_user WITH CREATEROLE;

-- =============================================================================
-- 配置数据库参数（可选优化）
-- =============================================================================

-- 设置默认时区为中国标准时间
ALTER DATABASE field_agent SET timezone TO 'Asia/Shanghai';

-- 设置日志记录级别（开发环境）
ALTER DATABASE field_agent SET log_statement = 'mod';

-- =============================================================================
-- 输出初始化完成信息
-- =============================================================================

\echo '============================================'
\echo '数据库初始化完成'
\echo '============================================'
\echo '数据库: field_agent'
\echo '用户: field_user'
\echo '密码: field_pass（请在生产环境修改）'
\echo '============================================'
