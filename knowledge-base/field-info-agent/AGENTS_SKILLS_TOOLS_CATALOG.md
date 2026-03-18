# Field Info Agent - AGENTS + SKILLS + TOOLS 技术清单

> 完整的技术组件清单，定义系统架构中所有的Agent、Skill和Tool

**版本**: V1.0  
**更新日期**: 2026-03-18  
**状态**: 设计中

---

## 📋 目录

1. [架构概览](#一架构概览)
2. [AGENTS清单](#二agents清单)
3. [SKILLS清单](#三skills清单)
4. [TOOLS清单](#四tools清单)
5. [调用关系图](#五调用关系图)
6. [数据流定义](#六数据流定义)

---

## 一、架构概览

### 1.1 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENTS (智能体层)                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          FieldCollector (主Agent - L3应用层)             │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                      SKILLS (技能层)                          │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │StationWork   │Vision        │DocGeneration │Emergency   │ │
│  │Guide         │Analysis      │              │Guide       │ │
│  │(工作引导)     │(AI分析)      │(文档生成)    │(应急处理)  │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                      TOOLS (工具层)                           │
│  ┌────────────┬────────────┬────────────┬──────────────────┐ │
│  │kimi-vision │postgres-   │minio-      │docx-generator    │ │
│  │            │query       │storage     │                  │ │
│  │(AI分析)    │(数据库)    │(对象存储)  │(Word生成)       │ │
│  └────────────┴────────────┴────────────┴──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 组件统计

| 层级 | 数量 | 组件 |
|------|------|------|
| **AGENTS** | 1 | FieldCollector |
| **SKILLS** | 4 | StationWorkGuide, VisionAnalysis, DocGeneration, EmergencyGuide |
| **TOOLS** | 4 | kimi-vision, postgres-query, minio-storage, docx-generator |

---

## 二、AGENTS清单

### 2.1 FieldCollector（现场信息收集智能体）

#### 基本信息

```yaml
name: field-collector
emoji: 🔌
type: OpenClaw Agent (Channel-based)
level: L3应用Agent
version: 1.0.0
status: active
```

#### 角色定位

- **核心身份**: 供电所现场工作人员的AI助手
- **交互方式**: 企业微信自然语言对话（零命令交互）
- **工作模式**: 主动引导 + 被动响应
- **服务范围**: 驻点工作全流程、应急处置、知识管理

#### 核心职责

| 职责ID | 职责名称 | 职责描述 | 优先级 |
|--------|----------|----------|--------|
| AG-001 | 驻点工作引导 | 引导现场人员完成驻点工作的全流程信息采集 | P0 |
| AG-002 | 照片智能分析 | 接收并分析现场照片，识别设备、缺陷、状态 | P0 |
| AG-003 | 文档自动生成 | 根据采集数据自动生成标准化工作文档 | P1 |
| AG-004 | 应急处置辅助 | 在应急情况下快速响应，提供处置指引 | P1 |
| AG-005 | 知识沉淀管理 | 版本化管理所有数据，构建可复用知识库 | P2 |

#### 配置参数

```yaml
# openclaw.config.yaml
agent:
  name: FieldInfoCollector
  version: 1.0.0
  
  channels:
    wecom:
      enabled: true
      connection_mode: websocket
      websocket_url: "wss://openws.work.weixin.qq.com"
      bot_id: "${WECOM_BOT_ID}"
      secret: "${WECOM_SECRET}"
      heartbeat_interval: 30
      
  session:
    storage: redis
    timeout: 7200  # 2小时
    persistence: true
    
  skills:
    - station-work-guide
    - vision-analysis
    - doc-generation
    - emergency-guide
    
  tools:
    - kimi-vision
    - postgres-query
    - minio-storage
    - docx-generator
```

#### 权限配置

```yaml
permissions:
  data_access:
    - read:本供电所社区数据
    - read:本供电所客户数据
    - write:本供电所采集记录
    - read_write:本供电所Session
  
  admin_access:
    - read:所有供电所数据 (仅管理员)
    - write:系统配置 (仅管理员)
    
  file_access:
    - read_write:temp/
    - read:templates/
    - read_write:uploads/
```

---

## 三、SKILLS清单

### 3.1 Skill总体说明

| 属性 | 说明 |
|------|------|
| **触发方式** | 意图识别 / 消息类型 / 事件 / 命令 |
| **执行模式** | 同步 / 异步 |
| **依赖关系** | 可依赖其他Skill或Tool |
| **状态管理** | 可读写Session状态 |

### 3.2 StationWorkGuide（驻点工作引导）

#### 基本信息

```yaml
skill_id: station-work-guide
name: 驻点工作引导
version: 1.0.0
emoji: 📋
category: workflow
priority: high
status: active
```

#### 功能职责

| 功能ID | 功能名称 | 功能描述 | 输入 | 输出 |
|--------|----------|----------|------|------|
| SWG-001 | 意图识别 | 识别用户工作意图 | 用户消息 | 意图类型+置信度 |
| SWG-002 | 阶段管理 | 管理工作流程阶段 | Session状态 | 下一阶段 |
| SWG-003 | 清单生成 | 动态生成工作清单 | 社区ID+历史数据 | 工作清单 |
| SWG-004 | 对话引导 | 引导用户完成采集 | 当前阶段 | 引导消息 |
| SWG-005 | 进度追踪 | 实时追踪工作进度 | 采集数据 | 进度报告 |

#### 触发条件

```yaml
triggers:
  - type: intent
    patterns:
      - "驻点"
      - "去.*社区"
      - "配电房"
      - "客户走访"
      - "开始.*工作"
    confidence_threshold: 0.7
    
  - type: message_type
    value: "text"
    
  - type: event
    value: "session_state_change"
```

#### 工作流程

```
[用户输入] 
    ↓
[意图识别] → 识别为"开始驻点工作"
    ↓
[加载社区信息] → 查询历史记录、重点客户
    ↓
[生成工作清单] → 动态生成个性化清单
    ↓
[引导对话] → 发送引导消息
    ↓
[等待用户输入] ← 用户发送照片/文字
    ↓
[阶段判断] → 判断当前工作阶段
    ↓
[保存数据] → 保存到Session
    ↓
[检查完成度] → 是否完成当前阶段？
    ↓ 是
[进入下一阶段] / [生成报告]
```

#### 配置参数

```yaml
station_work_guide:
  max_session_duration: 7200    # 最大会话时长(秒)
  auto_save_interval: 300       # 自动保存间隔(秒)
  checklist_templates:
    power_room:
      - id: pr_001
        name: "变压器整体"
        required: true
      - id: pr_002
        name: "变压器高压侧"
        required: true
      - id: pr_003
        name: "变压器低压侧"
        required: true
    customer_visit:
      - id: cv_001
        name: "客户信息确认"
        required: true
      - id: cv_002
        name: "用电情况了解"
        required: true
```

#### 依赖关系

```yaml
dependencies:
  skills: []
  tools:
    - postgres-query    # 查询社区信息、历史记录
    - minio-storage     # 保存照片
  external:
    - wecom-api         # 发送消息
```

---

### 3.3 VisionAnalysis（AI照片分析）

#### 基本信息

```yaml
skill_id: vision-analysis
name: AI照片分析
version: 1.0.0
emoji: 🔍
category: ai
priority: high
status: active
```

#### 功能职责

| 功能ID | 功能名称 | 功能描述 | 输入 | 输出 |
|--------|----------|----------|------|------|
| VA-001 | 设备识别 | 识别电力设备类型 | 图片 | 设备类型+置信度 |
| VA-002 | 状态评估 | 评估设备运行状态 | 图片 | 状态等级(normal/attention/abnormal/danger) |
| VA-003 | 缺陷检测 | 检测设备缺陷 | 图片 | 缺陷列表+位置+严重程度 |
| VA-004 | 铭牌识别 | OCR识别铭牌信息 | 图片 | 型号/容量/厂家/日期 |
| VA-005 | 批量分析 | 批量处理多张照片 | 图片列表 | 综合分析报告 |

#### 触发条件

```yaml
triggers:
  - type: message_type
    value: "image"
    
  - type: command
    pattern: "分析.*照片|批量分析|开始分析"
    
  - type: event
    value: "collection_completed"
```

#### 分析流程

```
[接收图片]
    ↓
[下载图片] → 从企业微信下载到本地
    ↓
[预处理] → 格式转换、压缩
    ↓
[KIMI分析] → 调用kimi-vision工具
    ↓
[解析结果] → 解析JSON响应
    ↓
[保存结果] → 保存到photo_analysis表
    ↓
[生成摘要] → 生成用户友好的描述
    ↓
[返回结果] → 发送给用户
```

#### Prompt模板

```yaml
prompts:
  single_image: |
    你是电力设备检测专家。请分析用户上传的现场照片。
    
    分析要求：
    1. 识别设备类型（变压器/高压柜/低压柜/电缆/计量装置/其他）
    2. 评估整体状态（normal/attention/abnormal/danger）
    3. 检查以下缺陷：外观、连接、绝缘、运行、标识
    4. 识别安全隐患
    5. 给出处理建议
    
    按JSON格式输出：
    {
      "device_type": "设备类型",
      "status": "normal|attention|abnormal|danger",
      "confidence": 0-1,
      "findings": [
        {
          "category": "缺陷类别",
          "description": "具体描述",
          "severity": "low|medium|high|critical"
        }
      ],
      "recommendations": ["建议1", "建议2"],
      "summary": "一句话摘要"
    }
  
  batch_images: |
    你正在分析同一配电房的多张照片。请批量分析并给出整体评估。
    
    照片数量: {{photo_count}}
    社区: {{community_name}}
    
    按JSON格式输出整体评估...
```

#### 配置参数

```yaml
vision_analysis:
  auto_analyze: true            # 是否自动分析
  batch_size: 10                # 批量分析数量
  timeout: 300                  # 分析超时(秒)
  confidence_threshold: 0.7     # 置信度阈值
  save_results: true            # 是否保存结果
  use_llm_vision: true          # 使用OpenClaw LLM多模态
```

#### 依赖关系

```yaml
dependencies:
  skills: []
  tools:
    - kimi-vision       # AI图片分析
    - postgres-query    # 保存分析结果
    - minio-storage     # 保存图片
```

---

### 3.4 DocGeneration（文档自动生成）

#### 基本信息

```yaml
skill_id: doc-generation
name: 文档自动生成
version: 1.0.0
emoji: 📄
category: output
priority: medium
status: active
```

#### 功能职责

| 功能ID | 功能名称 | 功能描述 | 输入 | 输出 |
|--------|----------|----------|------|------|
| DG-001 | 模板选择 | 根据场景选择文档模板 | 文档类型 | 模板路径 |
| DG-002 | 数据填充 | 填充数据到模板 | 采集数据+模板 | 渲染后的文档 |
| DG-003 | 照片排版 | 自动排版照片到文档 | 照片列表 | 照片网格 |
| DG-004 | 表格生成 | 生成数据表格 | 结构化数据 | Word表格 |
| DG-005 | 版本管理 | 管理文档版本 | 文档数据 | 版本记录 |

#### 支持的文档类型

| 文档类型 | 类型ID | 用途 | 模板文件 |
|----------|--------|------|----------|
| 驻点工作记录表 | station-work-record | 记录完整驻点工作过程 | station-work-record.docx |
| 设备缺陷报告 | defect-report | 详细记录设备缺陷 | defect-report.docx |
| 安全隐患整改通知单 | safety-notice | 正式安全隐患整改通知 | safety-notice.docx |
| 应急通道位置图 | emergency-map | 记录应急通道位置信息 | emergency-map.docx |

#### 触发条件

```yaml
triggers:
  - type: event
    value: "collection_completed"
    
  - type: command
    pattern: "生成.*报告|导出.*文档"
```

#### 生成流程

```
[接收生成请求]
    ↓
[获取Session数据] → 基本信息、采集数据、分析结果
    ↓
[选择文档模板] → 根据文档类型选择模板
    ↓
[数据预处理] → 格式化数据、下载照片、生成表格
    ↓
[渲染文档] → 填充文本字段、插入照片、生成表格
    ↓
[保存文档] → 上传到MinIO
    ↓
[记录到数据库] → 记录文档信息
    ↓
[返回下载链接] → 发送给用户
```

#### 模板变量

```yaml
template_variables:
  basic_info:
    - "{{STATION_NAME}}"          # 供电所名称
    - "{{COMMUNITY_NAME}}"        # 社区名称
    - "{{WORK_DATE}}"            # 工作日期
    - "{{WORKER_NAME}}"          # 工作人员
    
  power_room:
    - "{{PR_CHECKLIST}}"         # 配电房检查清单
    - "{{PR_PHOTOS}}"           # 配电房照片
    - "{{PR_FINDINGS}}"         # 发现问题
    
  analysis:
    - "{{ANALYSIS_SUMMARY}}"    # 分析摘要
    - "{{ISSUES_LIST}}"         # 问题清单
```

#### 依赖关系

```yaml
dependencies:
  skills: []
  tools:
    - docx-generator    # Word文档生成
    - minio-storage     # 保存文档
    - postgres-query    # 记录文档信息
```

---

### 3.5 EmergencyGuide（应急处置指引）

#### 基本信息

```yaml
skill_id: emergency-guide
name: 应急处置指引
version: 1.0.0
emoji: 🚨
category: emergency
priority: high
status: active
```

#### 功能职责

| 功能ID | 功能名称 | 功能描述 | 输入 | 输出 |
|--------|----------|----------|------|------|
| EG-001 | 应急识别 | 识别应急场景 | 用户消息 | 应急类型 |
| EG-002 | 信息查询 | 查询应急相关资料 | 社区ID+应急类型 | 应急方案 |
| EG-003 | 影响分析 | 分析影响范围 | 停电范围 | 影响户数+敏感客户 |
| EG-004 | 敏感客户 | 识别并推送敏感客户清单 | 社区ID | 敏感客户列表 |
| EG-005 | 过程记录 | 记录应急处置过程 | 处理节点 | 处理记录 |

#### 应急类型

| 类型ID | 类型名称 | 触发关键词 | 响应级别 |
|--------|----------|-----------|---------|
| power_outage | 停电故障 | 停电、断电、没电 | P0 |
| equipment_failure | 设备故障 | 故障、损坏、跳闸 | P0 |
| customer_complaint | 紧急投诉 | 投诉、紧急、危险 | P1 |
| fire_hazard | 火灾隐患 | 火灾、冒烟、着火 | P0 |

#### 触发条件

```yaml
triggers:
  - type: intent
    patterns:
      - "停电"
      - "故障"
      - "抢修"
      - "应急"
      - "紧急"
      - "危险"
    confidence_threshold: 0.8
    
  - type: command
    pattern: "/emergency"
```

#### 应急处置流程

```
[用户报告应急]
    ↓
[识别应急类型] → 判断应急等级
    ↓
[查询应急资料] → 应急方案、接入点信息
    ↓
[分析影响范围] → 影响户数、敏感客户
    ↓
[推送敏感客户] → 生成关怀清单
    ↓
[展示应急指引] → 接入点、电缆信息
    ↓
[开始记录过程] → 记录处理节点
    ↓
[生成应急报告] → 总结处理过程
```

#### 依赖关系

```yaml
dependencies:
  skills: []
  tools:
    - postgres-query    # 查询应急资料、敏感客户
    - wecom-api         # 推送消息
```

---

## 四、TOOLS清单

### 4.1 Tool总体说明

| 属性 | 说明 |
|------|------|
| **接口协议** | JSON-RPC / REST API / Function Call |
| **输入输出** | 明确定义的参数和返回值 |
| **错误处理** | 标准化错误码和异常处理 |
| **超时控制** | 可配置的超时时间 |

### 4.2 kimi-vision（KIMI多模态分析）

#### 基本信息

```yaml
tool_id: kimi-vision
name: KIMI Vision
version: 1.0.0
category: ai
provider: Moonshot AI
```

#### 功能定义

```typescript
interface KimiVisionTool {
  name: 'kimi-vision'
  version: '1.0.0'
  
  /**
   * 单图分析
   */
  analyzeImage(params: {
    imageUrl: string           // 图片URL或base64
    prompt?: string            // 自定义提示词
    systemPrompt?: string      // 系统提示词
  }): Promise<{
    content: string            // 分析结果（JSON字符串）
    usage: {
      prompt_tokens: number
      completion_tokens: number
    }
  }>
  
  /**
   * 批量分析
   */
  analyzeBatch(params: {
    imageUrls: string[]        // 图片URL列表
    prompt?: string
    maxConcurrent?: number     // 最大并发数
  }): Promise<{
    results: Array<{
      imageUrl: string
      content: string
    }>
    summary: string            // 综合分析摘要
  }>
}
```

#### 配置参数

```yaml
kimi_vision:
  api_key: "${KIMI_API_KEY}"
  base_url: "https://api.moonshot.cn/v1"
  model: "kimi-k2.5"
  temperature: 0.3
  max_tokens: 4096
  timeout: 60                 # 单次请求超时(秒)
  retry_count: 3              # 重试次数
```

---

### 4.3 postgres-query（PostgreSQL数据库查询）

#### 基本信息

```yaml
tool_id: postgres-query
name: PostgreSQL Query
version: 1.0.0
category: database
provider: PostgreSQL
```

#### 功能定义

```typescript
interface PostgresQueryTool {
  name: 'postgres-query'
  version: '1.0.0'
  
  /**
   * 执行查询
   */
  query(params: {
    sql: string
    params?: any[]
  }): Promise<{
    rows: any[]
    rowCount: number
  }>
  
  /**
   * 插入记录
   */
  insert(params: {
    table: string
    data: Record<string, any>
  }): Promise<{
    id: string
    affectedRows: number
  }>
  
  /**
   * 更新记录
   */
  update(params: {
    table: string
    data: Record<string, any>
    where: string
    whereParams?: any[]
  }): Promise<{
    affectedRows: number
  }>
  
  /**
   * 事务执行
   */
  transaction(params: {
    operations: Array<{
      type: 'query' | 'insert' | 'update'
      params: any
    }>
  }): Promise<{
    results: any[]
    committed: boolean
  }>
}
```

#### 配置参数

```yaml
postgres_query:
  host: "${POSTGRES_HOST}"
  port: "${POSTGRES_PORT}"
  database: "${POSTGRES_DB}"
  username: "${POSTGRES_USER}"
  password: "${POSTGRES_PASSWORD}"
  pool_size: 10
  ssl: false
  timeout: 30
```

#### 数据库Schema

```sql
-- 核心表结构

-- 会话表
CREATE TABLE field_sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(100) NOT NULL,
  community_id VARCHAR(100) NOT NULL,
  state VARCHAR(50) NOT NULL,
  data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 照片分析表
CREATE TABLE photo_analysis (
  analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES field_sessions(session_id),
  photo_url VARCHAR(500) NOT NULL,
  result JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 生成文档表
CREATE TABLE generated_documents (
  doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES field_sessions(session_id),
  doc_type VARCHAR(50) NOT NULL,
  storage_path VARCHAR(500) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4.4 minio-storage（MinIO对象存储）

#### 基本信息

```yaml
tool_id: minio-storage
name: MinIO Storage
version: 1.0.0
category: storage
provider: MinIO
```

#### 功能定义

```typescript
interface MinioStorageTool {
  name: 'minio-storage'
  version: '1.0.0'
  
  /**
   * 上传文件
   */
  upload(params: {
    bucket: string
    key: string
    filePath: string | Buffer
    contentType?: string
  }): Promise<{
    etag: string
    url: string
  }>
  
  /**
   * 下载文件
   */
  download(params: {
    bucket: string
    key: string
    destinationPath: string
  }): Promise<{
    filePath: string
    size: number
  }>
  
  /**
   * 获取访问URL
   */
  getUrl(params: {
    bucket: string
    key: string
    expiry?: number          // 过期时间(秒)
  }): Promise<{
    url: string
    expiresAt: Date
  }>
  
  /**
   * 删除文件
   */
  delete(params: {
    bucket: string
    key: string
  }): Promise<{
    success: boolean
  }>
}
```

#### 配置参数

```yaml
minio_storage:
  endpoint: "${MINIO_ENDPOINT}"
  access_key: "${MINIO_ACCESS_KEY}"
  secret_key: "${MINIO_SECRET_KEY}"
  region: "us-east-1"
  use_ssl: false
  
  buckets:
    photos: "field-photos"
    documents: "field-documents"
    templates: "field-templates"
```

---

### 4.5 docx-generator（Word文档生成）

#### 基本信息

```yaml
tool_id: docx-generator
name: Docx Generator
version: 1.0.0
category: document
provider: OpenClaw
```

#### 功能定义

```typescript
interface DocxGeneratorTool {
  name: 'docx-generator'
  version: '1.0.0'
  
  /**
   * 基于模板生成文档
   */
  generateFromTemplate(params: {
    templatePath: string
    data: Record<string, any>
    outputPath: string
  }): Promise<{
    filePath: string
    fileSize: number
  }>
  
  /**
   * 创建新文档
   */
  createDocument(params: {
    content: Array<{
      type: 'paragraph' | 'table' | 'image'
      content: any
    }>
    outputPath: string
  }): Promise<{
    filePath: string
  }>
  
  /**
   * 填充占位符
   */
  fillPlaceholders(params: {
    templatePath: string
    placeholders: Record<string, string>
    outputPath: string
  }): Promise<{
    filePath: string
  }>
}
```

#### 配置参数

```yaml
docx_generator:
  template_path: "./templates"
  temp_path: "./temp"
  output_path: "./output"
  fonts:
    - "SimSun"
    - "SimHei"
    - "Microsoft YaHei"
```

---

## 五、调用关系图

### 5.1 Skill-Tool调用关系

```
┌─────────────────────┐
│ StationWorkGuide    │
│ (驻点工作引导)       │
└──────────┬──────────┘
           │
           ├──► postgres-query (查询社区信息)
           └──► minio-storage (保存照片)

┌─────────────────────┐
│ VisionAnalysis      │
│ (AI照片分析)        │
└──────────┬──────────┘
           │
           ├──► kimi-vision (AI分析)
           ├──► postgres-query (保存结果)
           └──► minio-storage (保存图片)

┌─────────────────────┐
│ DocGeneration       │
│ (文档生成)          │
└──────────┬──────────┘
           │
           ├──► docx-generator (生成Word)
           ├──► minio-storage (保存文档)
           └──► postgres-query (记录文档)

┌─────────────────────┐
│ EmergencyGuide      │
│ (应急处理)          │
└──────────┬──────────┘
           │
           └──► postgres-query (查询应急资料)
```

### 5.2 消息处理流程

```
[用户消息] 
    ↓
[WeCom Channel]
    ↓
[Session Manager] ──► [Redis缓存]
    ↓
[Intent Recognition]
    ↓
[Skill Router]
    ├──► StationWorkGuide
    ├──► VisionAnalysis
    ├──► DocGeneration
    └──► EmergencyGuide
         ↓
    [Tool调用]
         ↓
    [结果返回]
         ↓
    [WeCom回复]
```

---

## 六、数据流定义

### 6.1 核心数据流

#### 数据流1：照片采集与分析

```
用户上传照片
    ↓
WeCom Channel接收
    ↓
VisionAnalysis Skill触发
    ↓
├─► minio-storage: 保存照片到 field-photos/{session_id}/
├─► kimi-vision: 调用AI分析
└─► postgres-query: 保存分析结果到 photo_analysis表
    ↓
生成分析摘要
    ↓
通过WeCom返回用户
```

#### 数据流2：文档生成

```
用户触发"生成报告"
    ↓
DocGeneration Skill触发
    ↓
├─► postgres-query: 获取session数据
├─► minio-storage: 下载照片
└─► docx-generator: 渲染Word文档
    ↓
minio-storage: 上传文档到 field-documents/
    ↓
postgres-query: 记录到 generated_documents表
    ↓
返回文档下载链接
```

### 6.2 数据模型

#### Session数据模型

```typescript
interface FieldWorkSession {
  // 基础信息
  sessionId: string
  userId: string
  communityId: string
  communityName: string
  
  // 状态
  state: 'preparing' | 'collecting' | 'analyzing' | 'completed'
  phase: 'power_room' | 'customer_visit' | 'emergency' | null
  
  // 进度
  progress: {
    totalItems: number
    completedItems: number
    currentItem: string
  }
  
  // 采集数据
  data: {
    photos: PhotoItem[]
    photoAnalysis?: AnalysisResult
    powerRoom?: PowerRoomData
    customerVisits?: CustomerVisit[]
    emergencyPoints?: EmergencyPoint[]
    notes: string[]
  }
  
  // 元数据
  createdAt: timestamp
  updatedAt: timestamp
  completedAt?: timestamp
  version: number
}
```

#### PhotoItem数据模型

```typescript
interface PhotoItem {
  id: string
  url: string                    // MinIO访问URL
  localPath: string             // 本地存储路径
  type: 'power_room' | 'customer_visit' | 'emergency'
  description?: string
  takenAt: timestamp
  location?: {
    latitude: number
    longitude: number
  }
}
```

#### AnalysisResult数据模型

```typescript
interface AnalysisResult {
  analysisId: string
  photoId: string
  deviceType: string
  deviceSubtype?: string
  status: 'normal' | 'attention' | 'abnormal' | 'danger'
  confidence: number
  findings: FindingItem[]
  safetyIssues: string[]
  recommendations: string[]
  summary: string
  analyzedAt: timestamp
  modelVersion: string
}

interface FindingItem {
  category: 'appearance' | 'connection' | 'insulation' | 'operation' | 'label'
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  location?: string
}
```

---

## 附录A：配置汇总

### A.1 完整openclaw.config.yaml

```yaml
name: FieldInfoCollector
version: 1.0.0
description: 现场信息收集智能体

channels:
  wecom:
    enabled: true
    connection_mode: websocket
    websocket_url: "wss://openws.work.weixin.qq.com"
    bot_id: "${WECOM_BOT_ID}"
    secret: "${WECOM_SECRET}"
    heartbeat:
      enabled: true
      interval: 30
      timeout: 10
      max_retries: 3
    reconnection:
      enabled: true
      max_attempts: 10
      base_delay: 1000
      max_delay: 30000

skills:
  station_work_guide:
    enabled: true
    priority: high
    max_session_duration: 7200
    auto_save_interval: 300
    
  vision_analysis:
    enabled: true
    priority: high
    auto_analyze: true
    batch_size: 10
    timeout: 300
    confidence_threshold: 0.7
    
  doc_generation:
    enabled: true
    priority: medium
    default_format: docx
    template_dir: ./templates
    
  emergency_guide:
    enabled: true
    priority: high
    fast_track: true

tools:
  kimi_vision:
    enabled: true
    api_key: "${KIMI_API_KEY}"
    base_url: "https://api.moonshot.cn/v1"
    model: "kimi-k2.5"
    temperature: 0.3
    max_tokens: 4096
    
  postgres_query:
    enabled: true
    host: "${POSTGRES_HOST}"
    port: "${POSTGRES_PORT}"
    database: "${POSTGRES_DB}"
    username: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    pool_size: 10
    
  minio_storage:
    enabled: true
    endpoint: "${MINIO_ENDPOINT}"
    access_key: "${MINIO_ACCESS_KEY}"
    secret_key: "${MINIO_SECRET_KEY}"
    buckets:
      photos: field-photos
      documents: field-documents
      templates: field-templates
      
  docx_generator:
    enabled: true
    template_path: ./templates
    temp_path: ./temp

session:
  storage: redis
  redis:
    host: "${REDIS_HOST}"
    port: "${REDIS_PORT}"
    password: "${REDIS_PASSWORD}"
  timeout: 7200
  persistence: true
```

---

**文档版本**: V1.0  
**最后更新**: 2026-03-18  
**作者**: PM Agent
