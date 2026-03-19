-- =============================================================================
-- Field Info Agent - PostgreSQL Schema 初始化脚本
-- =============================================================================
-- 文件名: 02-schema.sql
-- 作用: 创建数据表、索引和约束
-- 执行顺序: 第二个执行
-- 作者: Field Core Team
-- 创建日期: 2026-03-19
-- 版本: 1.0.0
-- =============================================================================

-- 连接到 field_agent 数据库
\c field_agent;

-- =============================================================================
-- 创建扩展
-- =============================================================================

-- 启用 UUID 扩展（用于生成唯一标识符）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用时间戳扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. 用户表 (users)
-- =============================================================================
-- 存储系统用户信息，包括企业微信用户

CREATE TABLE IF NOT EXISTS users (
    -- 主键：使用 UUID
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 企业微信相关字段
    wecom_user_id VARCHAR(64) UNIQUE,           -- 企业微信用户ID
    wecom_department VARCHAR(255),               -- 所属部门
    
    -- 基本信息
    username VARCHAR(64) UNIQUE NOT NULL,        -- 用户名（登录用）
    display_name VARCHAR(128) NOT NULL,          -- 显示名称
    email VARCHAR(255),                          -- 邮箱
    phone VARCHAR(20),                           -- 手机号
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'active'          -- 状态: active, inactive, suspended
        CHECK (status IN ('active', 'inactive', 'suspended')),
    
    -- 角色权限
    role VARCHAR(20) DEFAULT 'field_worker'      -- 角色: admin, supervisor, field_worker
        CHECK (role IN ('admin', 'supervisor', 'field_worker')),
    
    -- 元数据
    avatar_url TEXT,                             -- 头像URL
    metadata JSONB DEFAULT '{}',                 -- 扩展元数据（JSON格式）
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE       -- 最后登录时间
);

-- 为用户表创建索引
CREATE INDEX IF NOT EXISTS idx_users_wecom_user_id ON users(wecom_user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 添加表注释
COMMENT ON TABLE users IS '系统用户表，包含企业微信用户信息';
COMMENT ON COLUMN users.wecom_user_id IS '企业微信用户唯一标识';
COMMENT ON COLUMN users.metadata IS 'JSON格式扩展字段，可存储额外信息';

-- =============================================================================
-- 2. 会话表 (sessions)
-- =============================================================================
-- 存储用户会话信息，用于状态管理和上下文保持

CREATE TABLE IF NOT EXISTS sessions (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联用户
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 会话标识
    session_token VARCHAR(255) UNIQUE NOT NULL,  -- 会话令牌
    channel VARCHAR(32) NOT NULL                 -- 渠道: wecom, web, api
        CHECK (channel IN ('wecom', 'web', 'api')),
    
    -- 会话状态
    status VARCHAR(20) DEFAULT 'active'          -- 状态: active, expired, terminated
        CHECK (status IN ('active', 'expired', 'terminated')),
    
    -- 上下文数据
    context JSONB DEFAULT '{}',                  -- 会话上下文（当前技能、输入历史等）
    current_skill VARCHAR(64),                   -- 当前激活的 Skill
    skill_state VARCHAR(32),                     -- Skill 状态: idle, waiting_input, processing
    
    -- 地理位置（现场工作相关）
    location_lat DECIMAL(10, 8),                 -- 纬度
    location_lng DECIMAL(11, 8),                 -- 经度
    location_address TEXT,                       -- 地址描述
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,-- 过期时间
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为会话表创建索引
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_current_skill ON sessions(current_skill);

-- 添加表注释
COMMENT ON TABLE sessions IS '用户会话表，管理用户状态和上下文';
COMMENT ON COLUMN sessions.context IS 'JSON格式，存储会话上下文和临时数据';

-- =============================================================================
-- 3. 任务表 (tasks)
-- =============================================================================
-- 存储用户提交的任务和处理结果

CREATE TABLE IF NOT EXISTS tasks (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联信息
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    -- 任务类型和内容
    task_type VARCHAR(32) NOT NULL               -- 任务类型
        CHECK (task_type IN ('vision_analysis', 'station_guide', 'doc_generation', 'emergency_guide')),
    input_text TEXT,                             -- 用户输入文本
    input_attachments JSONB DEFAULT '[]',        -- 附件列表（照片、文档等）
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending'         -- 状态: pending, processing, completed, failed
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    
    -- 处理结果
    result JSONB,                                -- 处理结果（JSON格式）
    output_documents JSONB DEFAULT '[]',         -- 输出文档列表
    
    -- 时间和性能
    started_at TIMESTAMP WITH TIME ZONE,         -- 开始处理时间
    completed_at TIMESTAMP WITH TIME ZONE,       -- 完成时间
    processing_time_ms INTEGER,                  -- 处理耗时（毫秒）
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                 -- 扩展元数据
    error_message TEXT,                          -- 错误信息（失败时）
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为任务表创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);

-- 添加表注释
COMMENT ON TABLE tasks IS '任务表，记录用户提交的任务和处理结果';
COMMENT ON COLUMN tasks.input_attachments IS 'JSON数组，存储输入附件信息';
COMMENT ON COLUMN tasks.output_documents IS 'JSON数组，存储生成的文档信息';

-- =============================================================================
-- 4. 分析结果表 (analysis_results)
-- =============================================================================
-- 存储 AI 分析结果（照片分析、文档分析等）

CREATE TABLE IF NOT EXISTS analysis_results (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联信息
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    
    -- 分析类型
    analysis_type VARCHAR(32) NOT NULL           -- 分析类型
        CHECK (analysis_type IN ('photo_analysis', 'document_analysis', 'location_analysis', 'general')),
    
    -- 输入信息
    source_url TEXT,                             -- 源文件 URL（MinIO 地址）
    source_type VARCHAR(32)                      -- 源文件类型: image, document, audio
        CHECK (source_type IN ('image', 'document', 'audio', 'video', 'text')),
    
    -- 分析结果
    result JSONB NOT NULL,                       -- 分析结果（JSON格式）
    summary TEXT,                                -- 结果摘要
    keywords TEXT[],                             -- 关键词数组
    confidence_score DECIMAL(3, 2),              -- 置信度分数 (0.00 - 1.00)
    
    -- AI 模型信息
    model_name VARCHAR(64),                      -- 使用的 AI 模型
    model_version VARCHAR(32),                   -- 模型版本
    
    -- 验证状态
    verified BOOLEAN DEFAULT FALSE,              -- 是否已人工验证
    verified_by UUID REFERENCES users(id),       -- 验证人
    verified_at TIMESTAMP WITH TIME ZONE,        -- 验证时间
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                 -- 扩展元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为分析结果表创建索引
CREATE INDEX IF NOT EXISTS idx_analysis_results_task_id ON analysis_results(task_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_user_id ON analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at ON analysis_results(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_confidence ON analysis_results(confidence_score);

-- 添加表注释
COMMENT ON TABLE analysis_results IS 'AI 分析结果表，存储照片、文档等分析结果';
COMMENT ON COLUMN analysis_results.result IS 'JSON格式，包含详细的分析结果';
COMMENT ON COLUMN analysis_results.keywords IS '关键词数组，用于快速检索';

-- =============================================================================
-- 5. 文档表 (documents)
-- =============================================================================
-- 存储生成的文档和文件元数据

CREATE TABLE IF NOT EXISTS documents (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联信息
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 文档基本信息
    document_name VARCHAR(255) NOT NULL,         -- 文档名称
    document_type VARCHAR(32) NOT NULL           -- 文档类型
        CHECK (document_type IN ('report', 'form', 'summary', 'guide', 'other')),
    file_format VARCHAR(10) NOT NULL             -- 文件格式: pdf, docx, xlsx, txt
        CHECK (file_format IN ('pdf', 'docx', 'xlsx', 'txt', 'md', 'json')),
    
    -- 存储信息
    storage_provider VARCHAR(32) DEFAULT 'minio' -- 存储提供商
        CHECK (storage_provider IN ('minio', 's3', 'local')),
    storage_bucket VARCHAR(64) NOT NULL,         -- 存储桶名称
    storage_key TEXT NOT NULL,                   -- 存储键（对象路径）
    storage_url TEXT,                            -- 访问 URL
    file_size_bytes BIGINT,                      -- 文件大小（字节）
    
    -- 内容摘要
    content_summary TEXT,                        -- 内容摘要
    content_hash VARCHAR(64),                    -- 内容哈希（用于去重）
    
    -- 版本控制
    version INTEGER DEFAULT 1,                   -- 版本号
    parent_document_id UUID REFERENCES documents(id), -- 父文档（版本链）
    
    -- 状态
    status VARCHAR(20) DEFAULT 'active'          -- 状态: active, archived, deleted
        CHECK (status IN ('active', 'archived', 'deleted')),
    
    -- 访问控制
    is_public BOOLEAN DEFAULT FALSE,             -- 是否公开
    shared_with UUID[],                          -- 共享用户列表
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                 -- 扩展元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE          -- 过期时间（临时文档）
);

-- 为文档表创建索引
CREATE INDEX IF NOT EXISTS idx_documents_task_id ON documents(task_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

-- 添加表注释
COMMENT ON TABLE documents IS '文档表，存储生成的文件元数据';
COMMENT ON COLUMN documents.storage_key IS 'MinIO/S3 中的对象键（路径）';
COMMENT ON COLUMN documents.content_hash IS '文件内容哈希值，用于重复检测';

-- =============================================================================
-- 6. 系统日志表 (system_logs)
-- =============================================================================
-- 存储系统操作日志和审计日志

CREATE TABLE IF NOT EXISTS system_logs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 日志信息
    log_level VARCHAR(10) NOT NULL               -- 日志级别
        CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    source VARCHAR(64) NOT NULL,                 -- 日志来源（模块/组件）
    message TEXT NOT NULL,                       -- 日志消息
    
    -- 上下文信息
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- 详细信息
    details JSONB,                               -- 详细信息（JSON格式）
    stack_trace TEXT,                            -- 错误堆栈（如果是错误）
    
    -- 请求信息
    request_id VARCHAR(64),                      -- 请求ID（用于追踪）
    ip_address INET,                             -- IP地址
    user_agent TEXT,                             -- 用户代理
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为日志表创建索引
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(source);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_request_id ON system_logs(request_id);

-- 添加表注释
COMMENT ON TABLE system_logs IS '系统日志表，用于审计和故障排查';

-- =============================================================================
-- 创建更新时间戳触发器函数
-- =============================================================================

-- 创建自动更新 updated_at 的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有需要自动更新 updated_at 的表创建触发器
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_results_updated_at 
    BEFORE UPDATE ON analysis_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 授予权限
-- =============================================================================

-- 授予 field_user 对所有表的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO field_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO field_user;

-- =============================================================================
-- 输出完成信息
-- =============================================================================

\echo '============================================'
\echo 'Schema 初始化完成'
\echo '============================================'
\echo '已创建表:'
\echo '  - users (用户表)'
\echo '  - sessions (会话表)'
\echo '  - tasks (任务表)'
\echo '  - analysis_results (分析结果表)'
\echo '  - documents (文档表)'
\echo '  - system_logs (系统日志表)'
\echo '============================================'
