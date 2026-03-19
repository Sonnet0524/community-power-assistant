-- =============================================================================
-- Field Info Agent - 测试数据种子脚本
-- =============================================================================
-- 文件名: 03-seed.sql
-- 作用: 插入测试数据用于开发和演示
-- 执行顺序: 第三个执行
-- 作者: Field Core Team
-- 创建日期: 2026-03-19
-- 版本: 1.0.0
-- 注意: 仅用于开发和测试环境，生产环境请勿执行
-- =============================================================================

-- 连接到 field_agent 数据库
\c field_agent;

-- =============================================================================
-- 插入测试用户
-- =============================================================================

INSERT INTO users (
    id, wecom_user_id, username, display_name, email, phone, 
    status, role, avatar_url, metadata
) VALUES 
-- 管理员用户
(
    '11111111-1111-1111-1111-111111111111',
    'admin001',
    'admin',
    '系统管理员',
    'admin@field.local',
    '13800000001',
    'active',
    'admin',
    'https://example.com/avatars/admin.png',
    '{"department": "技术部", "employee_id": "A001"}'::jsonb
),
-- 主管用户
(
    '22222222-2222-2222-2222-222222222222',
    'supervisor001',
    'supervisor',
    '现场主管',
    'supervisor@field.local',
    '13800000002',
    'active',
    'supervisor',
    'https://example.com/avatars/supervisor.png',
    '{"department": "现场部", "employee_id": "S001"}'::jsonb
),
-- 现场工作人员1
(
    '33333333-3333-3333-3333-333333333333',
    'field001',
    'field_worker_1',
    '张三',
    'zhangsan@field.local',
    '13800000003',
    'active',
    'field_worker',
    'https://example.com/avatars/zhangsan.png',
    '{"department": "现场一组", "employee_id": "F001"}'::jsonb
),
-- 现场工作人员2
(
    '44444444-4444-4444-4444-444444444444',
    'field002',
    'field_worker_2',
    '李四',
    'lisi@field.local',
    '13800000004',
    'active',
    'field_worker',
    'https://example.com/avatars/lisi.png',
    '{"department": "现场二组", "employee_id": "F002"}'::jsonb
),
-- 非活跃用户
(
    '55555555-5555-5555-5555-555555555555',
    'field003',
    'field_worker_3',
    '王五（已停用）',
    'wangwu@field.local',
    '13800000005',
    'inactive',
    'field_worker',
    NULL,
    '{"department": "现场一组", "employee_id": "F003", "inactive_reason": "离职"}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 插入测试会话
-- =============================================================================

INSERT INTO sessions (
    id, user_id, session_token, channel, status, context,
    current_skill, skill_state, location_lat, location_lng, location_address,
    created_at, updated_at, expires_at, last_activity_at
) VALUES
-- 张三的活跃会话
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '33333333-3333-3333-3333-333333333333',
    'sess_token_zhangsan_001',
    'wecom',
    'active',
    '{
        "current_task": null,
        "input_history": [],
        "preferences": {"language": "zh-CN"}
    }'::jsonb,
    NULL,
    'idle',
    31.2304,
    121.4737,
    '上海市黄浦区',
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    CURRENT_TIMESTAMP
),
-- 李四的活跃会话
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '44444444-4444-4444-4444-444444444444',
    'sess_token_lisi_001',
    'wecom',
    'active',
    '{
        "current_task": "vision_analysis",
        "input_history": [
            {"type": "photo", "description": "现场设备照片"}
        ],
        "preferences": {"language": "zh-CN", "auto_save": true}
    }'::jsonb,
    'vision_analysis',
    'waiting_input',
    31.2456,
    121.5123,
    '上海市浦东新区',
    CURRENT_TIMESTAMP - INTERVAL '30 minutes',
    CURRENT_TIMESTAMP - INTERVAL '5 minutes',
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    CURRENT_TIMESTAMP - INTERVAL '5 minutes'
),
-- 过期的会话示例
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '33333333-3333-3333-3333-333333333333',
    'sess_token_expired_001',
    'wecom',
    'expired',
    '{}'::jsonb,
    NULL,
    'idle',
    NULL,
    NULL,
    NULL,
    CURRENT_TIMESTAMP - INTERVAL '48 hours',
    CURRENT_TIMESTAMP - INTERVAL '24 hours',
    CURRENT_TIMESTAMP - INTERVAL '24 hours',
    CURRENT_TIMESTAMP - INTERVAL '24 hours'
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 插入测试任务
-- =============================================================================

INSERT INTO tasks (
    id, user_id, session_id, task_type, input_text, input_attachments,
    status, result, output_documents, started_at, completed_at, processing_time_ms,
    metadata
) VALUES
-- 已完成的视觉分析任务
(
    'task-1111-1111-1111-111111111111',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'vision_analysis',
    '请分析这张照片中的设备状态',
    '[
        {
            "type": "image",
            "filename": "equipment_001.jpg",
            "storage_key": "raw-photos/2026/03/equipment_001.jpg",
            "size": 2048576
        }
    ]'::jsonb,
    'completed',
    '{
        "analysis": "设备运行正常，无异常现象",
        "issues": [],
        "recommendations": ["继续保持当前维护频率"]
    }'::jsonb,
    '[
        {
            "document_id": "doc-1111-1111-1111-111111111111",
            "name": "设备分析报告.pdf"
        }
    ]'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '59 minutes',
    5000,
    '{"priority": "normal", "source": "field"}'::jsonb
),
-- 进行中的驻点工作引导任务
(
    'task-2222-2222-2222-222222222222',
    '44444444-4444-4444-4444-444444444444',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'station_guide',
    '外高桥电厂驻点工作',
    '[]'::jsonb,
    'processing',
    NULL,
    '[]'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '5 minutes',
    NULL,
    NULL,
    '{"priority": "high", "station_name": "外高桥电厂", "work_type": "日常巡检"}'::jsonb
),
-- 待处理的文档生成任务
(
    'task-3333-3333-3333-333333333333',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'doc_generation',
    '生成月度巡检报告',
    '[]'::jsonb,
    'pending',
    NULL,
    '[]'::jsonb,
    NULL,
    NULL,
    NULL,
    '{"priority": "normal", "report_type": "monthly", "month": "2026-02"}'::jsonb
),
-- 失败的应急任务
(
    'task-4444-4444-4444-444444444444',
    '44444444-4444-4444-4444-444444444444',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'emergency_guide',
    '设备突然停机，紧急求助',
    '[]'::jsonb,
    'failed',
    NULL,
    '[]'::jsonb,
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP - INTERVAL '1 hour 59 minutes',
    1000,
    '{"priority": "critical"}'::jsonb,
    'AI 服务暂时不可用，请稍后重试或联系管理员'
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 插入测试分析结果
-- =============================================================================

INSERT INTO analysis_results (
    id, task_id, user_id, session_id, analysis_type,
    source_url, source_type, result, summary, keywords,
    confidence_score, model_name, model_version,
    metadata
) VALUES
-- 照片分析结果
(
    'analysis-1111-1111-1111-111111111111',
    'task-1111-1111-1111-111111111111',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'photo_analysis',
    'minio://field-documents/raw-photos/2026/03/equipment_001.jpg',
    'image',
    '{
        "objects": [
            {"name": "变压器", "confidence": 0.98, "bbox": [100, 200, 300, 400]},
            {"name": "开关", "confidence": 0.95, "bbox": [500, 600, 700, 800]}
        ],
        "status": "normal",
        "anomalies": [],
        "environment": "室内，照明良好"
    }'::jsonb,
    '设备照片分析：检测到变压器和开关，状态正常，无异常现象',
    ARRAY['变压器', '开关', '正常', '设备检查'],
    0.965,
    'KIMI-Vision',
    '2.5',
    '{"image_size": [1920, 1080], "processing_mode": "detailed"}'::jsonb
),
-- 通用分析结果
(
    'analysis-2222-2222-2222-222222222222',
    NULL,
    '44444444-4444-4444-4444-444444444444',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'general',
    NULL,
    'text',
    '{
        "classification": "technical_inquiry",
        "intent": "request_guidance",
        "entities": [
            {"type": "location", "value": "外高桥电厂"},
            {"type": "task", "value": "驻点工作"}
        ]
    }'::jsonb,
    '用户询问关于外高桥电厂驻点工作的相关指导',
    ARRAY['外高桥电厂', '驻点工作', '指导'],
    0.92,
    'KIMI-Chat',
    '2.5',
    '{}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 插入测试文档
-- =============================================================================

INSERT INTO documents (
    id, task_id, user_id, document_name, document_type, file_format,
    storage_provider, storage_bucket, storage_key, storage_url,
    file_size_bytes, content_summary, content_hash,
    version, parent_document_id, status, is_public, metadata
) VALUES
-- 设备分析报告
(
    'doc-1111-1111-1111-111111111111',
    'task-1111-1111-1111-111111111111',
    '33333333-3333-3333-3333-333333333333',
    '设备状态分析报告_20260319.pdf',
    'report',
    'pdf',
    'minio',
    'field-documents',
    'generated-docs/reports/equipment_analysis_20260319.pdf',
    'http://localhost:9000/field-documents/generated-docs/reports/equipment_analysis_20260319.pdf',
    1024000,
    '设备运行状态正常，建议继续保持当前维护策略',
    'a1b2c3d4e5f6789012345678901234567890abcdef',
    1,
    NULL,
    'active',
    FALSE,
    '{"pages": 5, "language": "zh-CN", "generated_by": "ai"}'::jsonb
),
-- 工作指南
(
    'doc-2222-2222-2222-222222222222',
    NULL,
    '44444444-4444-4444-4444-444444444444',
    '外高桥电厂驻点工作指南.md',
    'guide',
    'md',
    'minio',
    'field-documents',
    'generated-docs/guides/waigaoqiao_station_guide.md',
    'http://localhost:9000/field-documents/generated-docs/guides/waigaoqiao_station_guide.md',
    51200,
    '包含外高桥电厂的基本信息、驻点流程、注意事项和联系方式',
    'b2c3d4e5f6a7890123456789012345678901abcdef',
    1,
    NULL,
    'active',
    TRUE,
    '{"pages": 3, "language": "zh-CN", "generated_by": "ai"}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 插入测试日志
-- =============================================================================

INSERT INTO system_logs (
    id, log_level, source, message,
    user_id, session_id, task_id,
    details, request_id, ip_address
) VALUES
(
    'log-1111-1111-1111-111111111111',
    'INFO',
    'auth',
    '用户登录成功',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    NULL,
    '{"login_method": "wecom", "device": "mobile"}'::jsonb,
    'req-001',
    '192.168.1.100'::inet
),
(
    'log-2222-2222-2222-222222222222',
    'INFO',
    'skill.vision_analysis',
    '视觉分析任务开始',
    '33333333-3333-3333-3333-333333333333',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'task-1111-1111-1111-111111111111',
    '{"image_count": 1, "model": "KIMI-Vision"}'::jsonb,
    'req-002',
    '192.168.1.100'::inet
),
(
    'log-3333-3333-3333-333333333333',
    'WARNING',
    'db.connection',
    '数据库连接池使用率超过80%',
    NULL,
    NULL,
    NULL,
    '{"pool_size": 10, "active_connections": 8}'::jsonb,
    'req-003',
    NULL
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 输出完成信息
-- =============================================================================

\echo '============================================'
\echo '测试数据插入完成'
\echo '============================================'
\echo '已插入测试数据:'
\echo '  - 用户: 5 条'
\echo '  - 会话: 3 条'
\echo '  - 任务: 4 条'
\echo '  - 分析结果: 2 条'
\echo '  - 文档: 2 条'
\echo '  - 系统日志: 3 条'
\echo '============================================'
\echo '测试账号:'
\echo '  - 管理员: admin / (通过企业微信登录)'
\echo '  - 现场人员: field_worker_1 / (通过企业微信登录)'
\echo '============================================'
