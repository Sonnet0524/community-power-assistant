-- ============================================================
-- Field Info Collector - 数据库Schema
-- 现场信息收集智能体 - PostgreSQL数据库结构
-- ============================================================

-- 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. 基础数据表
-- ============================================================

-- 供电所表
CREATE TABLE stations (
    station_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    station_code VARCHAR(20) UNIQUE NOT NULL,  -- 供电所编码
    station_name VARCHAR(100) NOT NULL,        -- 供电所名称
    region VARCHAR(50),                        -- 所属区域
    address TEXT,
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 社区表
CREATE TABLE communities (
    community_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    station_id UUID NOT NULL REFERENCES stations(station_id),
    community_code VARCHAR(20) UNIQUE NOT NULL,  -- 社区编码
    community_name VARCHAR(100) NOT NULL,        -- 社区名称
    address TEXT,
    area_type VARCHAR(20),                       -- 住宅/商业/工业/混合
    population INTEGER,                          -- 人口数量
    priority_customers JSONB,                    -- 重点客户列表
    geo_boundary JSONB,                          -- 地理边界
    emergency_contacts JSONB,                    -- 应急联系人
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 用户表（企业微信用户）
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wecom_user_id VARCHAR(100) UNIQUE NOT NULL,  -- 企业微信UserID
    station_id UUID REFERENCES stations(station_id),
    username VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'field_worker',     -- 角色：field_worker/admin
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ============================================================
-- 2. 会话与工作记录表
-- ============================================================

-- 现场工作会话表
CREATE TABLE field_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    station_id UUID NOT NULL REFERENCES stations(station_id),
    community_id UUID NOT NULL REFERENCES communities(community_id),
    
    -- 工作信息
    work_type VARCHAR(20) DEFAULT 'routine',     -- routine/emergency/special
    work_date DATE NOT NULL,
    
    -- 状态
    state VARCHAR(20) DEFAULT 'preparing',       -- preparing/collecting/analyzing/completed
    current_phase VARCHAR(20),                   -- power_room/customer_visit/emergency
    
    -- 进度
    progress JSONB DEFAULT '{"total_items": 0, "completed_items": 0, "current_item": null}'::jsonb,
    
    -- 采集数据（JSON存储灵活结构）
    collected_data JSONB DEFAULT '{}'::jsonb,
    
    -- 时间戳
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    is_archived BOOLEAN DEFAULT false
);

-- 会话历史版本表
CREATE TABLE session_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    version INTEGER NOT NULL,
    collected_data JSONB NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

-- ============================================================
-- 3. 照片与分析表
-- ============================================================

-- 照片表
CREATE TABLE photos (
    photo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 照片信息
    photo_url VARCHAR(500) NOT NULL,             -- MinIO存储路径
    photo_hash VARCHAR(64),                      -- 图片哈希（去重用）
    photo_type VARCHAR(20),                      -- 照片类型
    description TEXT,                            -- 描述
    
    -- 位置信息
    location JSONB,                              -- {latitude, longitude, address}
    taken_at TIMESTAMP,                          -- 拍摄时间
    
    -- 文件信息
    file_size INTEGER,                           -- 文件大小（字节）
    mime_type VARCHAR(50),
    width INTEGER,
    height INTEGER,
    
    -- 分析关联
    analysis_id UUID,                            -- 关联分析结果
    
    created_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT false
);

-- 照片分析结果表
CREATE TABLE photo_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    photo_id UUID REFERENCES photos(photo_id),
    
    -- 分析结果（JSON存储）
    result JSONB NOT NULL,
    
    -- 关键字段（冗余存储便于查询）
    device_type VARCHAR(50),
    device_subtype VARCHAR(50),
    status VARCHAR(20),                          -- normal/attention/abnormal/danger
    confidence DECIMAL(3,2),
    has_issues BOOLEAN DEFAULT false,
    issue_count INTEGER DEFAULT 0,
    
    -- 元数据
    analyzed_at TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(20),                   -- AI模型版本
    processing_time_ms INTEGER                   -- 处理耗时
);

-- 批量分析结果表
CREATE TABLE batch_analysis (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 分析范围
    photo_count INTEGER NOT NULL,
    photo_ids UUID[],
    
    -- 整体结果
    overall_status VARCHAR(20),
    total_devices INTEGER,
    issues_found INTEGER,
    critical_issues INTEGER,
    overall_score INTEGER,                       -- 0-100
    
    -- 详细结果
    result JSONB NOT NULL,
    
    -- 元数据
    analyzed_at TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(20),
    processing_time_ms INTEGER
);

-- ============================================================
-- 4. 工作记录明细表
-- ============================================================

-- 配电房检查记录
CREATE TABLE power_room_checks (
    check_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 检查项
    check_item_code VARCHAR(20) NOT NULL,        -- 检查项编码
    check_item_name VARCHAR(100) NOT NULL,       -- 检查项名称
    status VARCHAR(20) DEFAULT 'pending',        -- pending/completed/skipped
    
    -- 检查结果
    result VARCHAR(20),                          -- normal/abnormal
    findings TEXT,                               -- 发现的问题
    notes TEXT,                                  -- 备注
    photo_ids UUID[],                            -- 关联照片
    
    -- 时间戳
    checked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 客户走访记录
CREATE TABLE customer_visits (
    visit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 客户信息
    customer_name VARCHAR(100) NOT NULL,
    customer_address TEXT,
    customer_type VARCHAR(20),                   -- residential/commercial/industrial
    contact_phone VARCHAR(20),
    contact_name VARCHAR(50),
    
    -- 走访内容
    is_present BOOLEAN,                          -- 客户是否在家
    visit_purpose TEXT,                          -- 走访目的
    findings TEXT,                               -- 发现的问题
    customer_needs TEXT,                         -- 客户需求
    safety_issues JSONB,                         -- 安全隐患
    
    -- 照片
    photo_ids UUID[],
    
    -- 时间戳
    visited_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 应急通道记录
CREATE TABLE emergency_points (
    point_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 位置信息
    point_name VARCHAR(100) NOT NULL,            -- 点位名称
    point_type VARCHAR(20),                      -- entrance/exit/access_point
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address TEXT,
    
    -- 描述
    description TEXT,
    access_instructions TEXT,                    -- 进入说明
    contact_info JSONB,                          -- 联系人信息
    
    -- 照片
    photo_ids UUID[],
    
    -- 时间戳
    recorded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. 文档生成表
-- ============================================================

-- 生成的文档表
CREATE TABLE generated_documents (
    doc_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES field_sessions(session_id),
    
    -- 文档信息
    doc_type VARCHAR(50) NOT NULL,               -- station-work-record/defect-report/etc
    doc_name VARCHAR(255) NOT NULL,
    doc_title TEXT,
    
    -- 存储信息
    storage_path VARCHAR(500) NOT NULL,          -- MinIO路径
    download_url VARCHAR(500) NOT NULL,
    file_size BIGINT,
    page_count INTEGER,
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    metadata JSONB                               -- 额外元数据
);

-- 文档版本表
CREATE TABLE document_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES generated_documents(doc_id),
    version INTEGER NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    changes TEXT,                                -- 变更说明
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

-- ============================================================
-- 6. 知识库表
-- ============================================================

-- 社区知识库表
CREATE TABLE community_knowledge (
    knowledge_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(community_id),
    
    -- 知识内容
    knowledge_type VARCHAR(20),                  -- facility/customer/emergency/history
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    
    -- 来源
    source_session_id UUID REFERENCES field_sessions(session_id),
    source_type VARCHAR(20),                     -- manual/auto/ai-generated
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT true,             -- 是否当前版本
    
    -- 统计
    view_count INTEGER DEFAULT 0,
    use_count INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT true
);

-- 知识库历史版本
CREATE TABLE knowledge_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_id UUID NOT NULL REFERENCES community_knowledge(knowledge_id),
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

-- ============================================================
-- 7. 审计日志表
-- ============================================================

-- 操作审计日志
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 操作信息
    operation VARCHAR(50) NOT NULL,              -- CREATE/UPDATE/DELETE/DOWNLOAD
    resource_type VARCHAR(50) NOT NULL,          -- session/photo/document/etc
    resource_id UUID,
    
    -- 用户
    user_id UUID REFERENCES users(user_id),
    wecom_user_id VARCHAR(100),
    
    -- 详情
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 索引创建
-- ============================================================

-- 会话表索引
CREATE INDEX idx_sessions_user ON field_sessions(user_id);
CREATE INDEX idx_sessions_community ON field_sessions(community_id);
CREATE INDEX idx_sessions_state ON field_sessions(state);
CREATE INDEX idx_sessions_date ON field_sessions(work_date);
CREATE INDEX idx_sessions_created ON field_sessions(created_at);

-- 照片表索引
CREATE INDEX idx_photos_session ON photos(session_id);
CREATE INDEX idx_photos_analysis ON photos(analysis_id);
CREATE INDEX idx_photos_hash ON photos(photo_hash);

-- 分析结果索引
CREATE INDEX idx_analysis_session ON photo_analysis(session_id);
CREATE INDEX idx_analysis_status ON photo_analysis(status);
CREATE INDEX idx_analysis_device ON photo_analysis(device_type);
CREATE INDEX idx_analysis_photo ON photo_analysis(photo_id);

-- 文档表索引
CREATE INDEX idx_docs_session ON generated_documents(session_id);
CREATE INDEX idx_docs_type ON generated_documents(doc_type);
CREATE INDEX idx_docs_created ON generated_documents(created_at);

-- 知识库索引
CREATE INDEX idx_knowledge_community ON community_knowledge(community_id);
CREATE INDEX idx_knowledge_type ON community_knowledge(knowledge_type);
CREATE INDEX idx_knowledge_current ON community_knowledge(community_id, is_current);

-- 审计日志索引
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_time ON audit_logs(created_at);

-- ============================================================
-- 视图创建
-- ============================================================

-- 会话完整信息视图
CREATE VIEW v_session_full AS
SELECT 
    s.*,
    u.username as worker_name,
    st.station_name,
    c.community_name,
    c.address as community_address,
    (SELECT COUNT(*) FROM photos WHERE session_id = s.session_id AND NOT is_deleted) as photo_count,
    (SELECT COUNT(*) FROM photo_analysis WHERE session_id = s.session_id) as analyzed_count
FROM field_sessions s
JOIN users u ON s.user_id = u.user_id
JOIN stations st ON s.station_id = st.station_id
JOIN communities c ON s.community_id = c.community_id;

-- 社区统计视图
CREATE VIEW v_community_stats AS
SELECT 
    c.*,
    COUNT(DISTINCT fs.session_id) as total_visits,
    MAX(fs.work_date) as last_visit_date,
    (SELECT COUNT(*) FROM photos p 
     JOIN field_sessions s ON p.session_id = s.session_id 
     WHERE s.community_id = c.community_id AND NOT p.is_deleted) as total_photos
FROM communities c
LEFT JOIN field_sessions fs ON c.community_id = fs.community_id AND fs.state = 'completed'
WHERE c.is_active = true
GROUP BY c.community_id;

-- ============================================================
-- 触发器创建（更新时间戳）
-- ============================================================

-- 自动更新updated_at的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表创建触发器
CREATE TRIGGER update_stations_updated_at BEFORE UPDATE ON stations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON field_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_updated_at BEFORE UPDATE ON community_knowledge
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 初始数据
-- ============================================================

-- 插入示例供电所
INSERT INTO stations (station_code, station_name, region) VALUES
('ST001', '城东供电所', '东城区'),
('ST002', '城西供电所', '西城区');

-- 插入示例社区
INSERT INTO communities (station_id, community_code, community_name, address, area_type) 
SELECT 
    station_id,
    'CM001',
    '阳光社区',
    '阳光路100号',
    'residential'
FROM stations WHERE station_code = 'ST001';

-- ============================================================
-- 权限设置（可选）
-- ============================================================

-- 创建应用专用角色
-- CREATE ROLE field_collector_app WITH LOGIN PASSWORD 'your-password';
-- GRANT CONNECT ON DATABASE field_info_db TO field_collector_app;
-- GRANT USAGE ON SCHEMA public TO field_collector_app;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO field_collector_app;
