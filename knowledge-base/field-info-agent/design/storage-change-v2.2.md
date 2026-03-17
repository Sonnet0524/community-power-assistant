# 存储方案变更说明（v2.2）

**变更日期**: 2026-03-17  
**变更原因**: WPS云文档权限问题无法解决  
**新方案**: **本地存储 + MinIO对象存储 + PostgreSQL**

---

## 一、变更背景

### 原方案
- **文件存储**: WPS云文档
- **数据存储**: WPS多维表格
- **权限控制**: WPS内置权限

### 问题
- WPS权限配置复杂，无法满足供电所间数据隔离要求
- 企业级权限管理受限
- 审批流程长

### 新方案
- **文件存储**: MinIO对象存储（本地/私有云）
- **数据存储**: PostgreSQL数据库
- **权限控制**: 应用层实现，完全自主可控

---

## 二、新存储架构

```
┌──────────────────────────────────────────────────────────────┐
│                         用户层                                │
│              企业微信APP（拍照 + 文字输入）                    │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS回调
┌────────────────────────────▼─────────────────────────────────┐
│                   OpenClaw Gateway                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ WeCom Channel│ │Session Manager│ │     Skills          │  │
│  └──────────────┘ └──────────────┘ └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Tools: MinIO ⭐ | PostgreSQL ⭐ | KIMI Vision | WeCom  │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                      存储层（本地/私有云）                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ MinIO对象存储 │  │  PostgreSQL  │  │   Redis      │       │
│  │ - 照片文件   │  │  - 业务数据  │  │  - 会话缓存  │       │
│  │ - 生成文档   │  │  - 权限数据  │  │  - 临时数据  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、详细设计方案

### 3.1 MinIO对象存储

**用途**:
- 存储现场照片（原始照片）
- 存储生成的Word/PDF文档
- 存储文件模板

**存储结构**:
```
field-info-agent/
├── photos/                    # 现场照片
│   └── {date}/               # 按日期分区
│       └── {record_id}/      # 按记录ID
│           ├── {uuid}_entrance.jpg    # 入口照片
│           ├── {uuid}_nameplate.jpg   # 铭牌照片
│           └── {uuid}_equipment.jpg   # 设备照片
│
├── documents/                # 生成文档
│   └── {station_id}/        # 按供电所分区
│       └── {community_id}/  # 按小区分区
│           ├── {date}_供电简报.docx
│           ├── {date}_应急指引.docx
│           └── {date}_工作总结.docx
│
└── templates/               # 文档模板
    ├── power-briefing.docx
    ├── emergency-guide.docx
    ├── work-summary.docx
    └── service-report.docx
```

**MinIO配置**:
```yaml
# docker-compose.yaml
services:
  minio:
    image: minio/minio:latest
    container_name: field-info-minio
    ports:
      - "9000:9000"    # API端口
      - "9001:9001"    # 控制台端口
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    
  # 创建初始bucket
  minio-init:
    image: minio/mc:latest
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      sleep 10;
      mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD};
      mc mb myminio/field-info-agent;
      mc policy set download myminio/field-info-agent;
      "
```

**访问控制**:
- 内网访问，不对外开放
- 通过预签名URL分享（有时间限制）
- 供电所间物理隔离（通过路径前缀）

---

### 3.2 PostgreSQL数据库

**用途**:
- 存储所有业务数据（替代WPS多维表格）
- 存储用户、权限数据
- 存储配置信息

**数据库设计**:

```sql
-- 1. 供电所表
CREATE TABLE power_stations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_code VARCHAR(50) UNIQUE NOT NULL,  -- 供电所编码
    station_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 用户表（企业微信用户）
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wecom_user_id VARCHAR(100) UNIQUE NOT NULL,  -- 企业微信UserID
    station_id UUID REFERENCES power_stations(id),
    user_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'worker',  -- worker/supervisor/admin
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 小区信息表
CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID REFERENCES power_stations(id),
    community_name VARCHAR(100) NOT NULL,
    address TEXT,
    total_households INTEGER DEFAULT 0,
    power_room_count INTEGER DEFAULT 0,
    transformer_count INTEGER DEFAULT 0,
    property_company VARCHAR(100),
    property_contact VARCHAR(100),
    property_phone VARCHAR(50),
    sensitive_customer_count INTEGER DEFAULT 0,
    last_station_date DATE,
    station_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 驻点工作记录表
CREATE TABLE station_work_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID REFERENCES power_stations(id),
    community_id UUID REFERENCES communities(id),
    work_date DATE NOT NULL,
    worker_user_id VARCHAR(100) NOT NULL,
    worker_name VARCHAR(100),
    work_summary TEXT,
    power_room_checked BOOLEAN DEFAULT FALSE,
    customer_visit_count INTEGER DEFAULT 0,
    issue_found_count INTEGER DEFAULT 0,
    issue_resolved_count INTEGER DEFAULT 0,
    photo_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress/completed/reviewed
    photo_analysis JSONB,  -- AI分析结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 配电房信息表
CREATE TABLE power_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID REFERENCES power_stations(id),
    community_id UUID REFERENCES communities(id),
    room_name VARCHAR(100),
    location_description TEXT,
    transformer_count INTEGER DEFAULT 0,
    equipment_status VARCHAR(20) DEFAULT 'normal',  -- normal/abnormal/under_repair
    defect_description TEXT,
    last_check_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 变压器信息表
CREATE TABLE transformers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES power_rooms(id),
    station_id UUID REFERENCES power_stations(id),
    model VARCHAR(100),
    capacity INTEGER,  -- kVA
    manufacturer VARCHAR(100),
    install_date DATE,
    status VARCHAR(20) DEFAULT 'normal',
    last_maintenance_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 照片文件表
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID REFERENCES station_work_records(id),
    room_id UUID REFERENCES power_rooms(id),
    file_name VARCHAR(255) NOT NULL,
    minio_path VARCHAR(500) NOT NULL,  -- MinIO路径
    file_size INTEGER,
    photo_type VARCHAR(50),  -- entrance/nameplate/equipment/defect
    ai_analysis JSONB,  -- AI分析结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 客户走访记录表
CREATE TABLE customer_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID REFERENCES power_stations(id),
    community_id UUID REFERENCES communities(id),
    customer_address VARCHAR(100),
    visit_date DATE,
    worker_user_id VARCHAR(100),
    worker_name VARCHAR(100),
    visit_content TEXT,
    issue_type VARCHAR(50),  -- none/power_outage/electricity_fee/service/other
    satisfaction VARCHAR(20),  -- very_satisfied/satisfied/neutral/dissatisfied
    need_follow_up BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 应急接入信息表
CREATE TABLE emergency_access_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id UUID REFERENCES communities(id),
    station_id UUID REFERENCES power_stations(id),
    entry_point_description TEXT,
    parking_point_description TEXT,
    access_point_description TEXT,
    cable_model VARCHAR(100),
    cable_length INTEGER,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. 生成文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID REFERENCES power_stations(id),
    community_id UUID REFERENCES communities(id),
    record_id UUID REFERENCES station_work_records(id),
    doc_type VARCHAR(50),  -- power_briefing/emergency_guide/work_summary/service_report
    file_name VARCHAR(255),
    minio_path VARCHAR(500),
    file_size INTEGER,
    download_url VARCHAR(500),  -- 预签名URL
    expires_at TIMESTAMP,  -- URL过期时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_communities_station ON communities(station_id);
CREATE INDEX idx_records_station ON station_work_records(station_id);
CREATE INDEX idx_records_community ON station_work_records(community_id);
CREATE INDEX idx_photos_record ON photos(record_id);
CREATE INDEX idx_documents_station ON documents(station_id);
```

**PostgreSQL配置**:
```yaml
# docker-compose.yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: field-info-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: field_info_agent
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
```

---

### 3.3 权限控制实现

**应用层权限控制**:

```typescript
// src/auth/permission.ts
class PermissionService {
  constructor(private db: Database) {}
  
  // 检查用户是否有权访问某个供电所的数据
  async checkStationAccess(userId: string, stationId: string): Promise<boolean> {
    const user = await this.db.users.findOne({
      where: { wecom_user_id: userId }
    })
    
    if (!user) return false
    
    // 超级管理员可以访问所有
    if (user.role === 'admin') return true
    
    // 本供电所人员可以访问
    return user.station_id === stationId
  }
  
  // 数据查询自动添加权限过滤
  async queryWithPermission<T>(
    userId: string,
    table: string,
    conditions: any
  ): Promise<T[]> {
    const user = await this.db.users.findOne({
      where: { wecom_user_id: userId }
    })
    
    if (!user) throw new Error('用户不存在')
    
    // 自动添加供电所过滤
    const queryConditions = {
      ...conditions,
      station_id: user.station_id  // 数据隔离
    }
    
    return this.db[table].findAll({ where: queryConditions })
  }
}

// Middleware使用
async function permissionMiddleware(req, res, next) {
  const userId = req.session.userId
  const stationId = req.params.stationId
  
  const hasPermission = await permissionService.checkStationAccess(
    userId, 
    stationId
  )
  
  if (!hasPermission) {
    return res.status(403).json({
      error: '无权访问其他供电所的数据'
    })
  }
  
  next()
}
```

---

## 四、Tool层重新设计

### 4.1 StorageTool（替代WPS File）

```typescript
// src/tools/storage/index.ts
import { Client } from 'minio'

export class StorageTool implements Tool {
  name = 'storage'
  version = '1.0.0'
  
  private minioClient: Client
  private bucketName = 'field-info-agent'
  
  constructor() {
    this.minioClient = new Client({
      endPoint: process.env.MINIO_ENDPOINT || 'localhost',
      port: parseInt(process.env.MINIO_PORT || '9000'),
      useSSL: false,
      accessKey: process.env.MINIO_ACCESS_KEY,
      secretKey: process.env.MINIO_SECRET_KEY
    })
  }
  
  // 上传照片
  async uploadPhoto(params: {
    fileBuffer: Buffer
    fileName: string
    recordId: string
    photoType: string
  }): Promise<{ filePath: string; url: string }> {
    const date = new Date().toISOString().split('T')[0]
    const objectName = `photos/${date}/${params.recordId}/${params.fileName}`
    
    await this.minioClient.putObject(
      this.bucketName,
      objectName,
      params.fileBuffer,
      params.fileBuffer.length,
      {
        'Content-Type': 'image/jpeg',
        'X-Photo-Type': params.photoType,
        'X-Record-Id': params.recordId
      }
    )
    
    // 生成临时访问URL（7天有效）
    const url = await this.minioClient.presignedGetObject(
      this.bucketName,
      objectName,
      7 * 24 * 60 * 60  // 7天
    )
    
    return { filePath: objectName, url }
  }
  
  // 上传文档
  async uploadDocument(params: {
    fileBuffer: Buffer
    fileName: string
    stationId: string
    communityId: string
    docType: string
  }): Promise<{ filePath: string; url: string }> {
    const objectName = `documents/${params.stationId}/${params.communityId}/${params.fileName}`
    
    await this.minioClient.putObject(
      this.bucketName,
      objectName,
      params.fileBuffer,
      params.fileBuffer.length,
      {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'X-Doc-Type': params.docType
      }
    )
    
    // 生成临时下载URL（30天有效）
    const url = await this.minioClient.presignedGetObject(
      this.bucketName,
      objectName,
      30 * 24 * 60 * 60  // 30天
    )
    
    return { filePath: objectName, url }
  }
  
  // 获取文件
  async getFile(objectName: string): Promise<Buffer> {
    const stream = await this.minioClient.getObject(
      this.bucketName,
      objectName
    )
    return this.streamToBuffer(stream)
  }
  
  // 删除文件
  async deleteFile(objectName: string): Promise<void> {
    await this.minioClient.removeObject(this.bucketName, objectName)
  }
  
  private async streamToBuffer(stream: Readable): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = []
      stream.on('data', chunk => chunks.push(chunk))
      stream.on('end', () => resolve(Buffer.concat(chunks)))
      stream.on('error', reject)
    })
  }
}
```

### 4.2 DatabaseTool（替代WPS KSheet）

```typescript
// src/tools/database/index.ts
import { Pool } from 'pg'

export class DatabaseTool implements Tool {
  name = 'database'
  version = '1.0.0'
  
  private pool: Pool
  
  constructor() {
    this.pool = new Pool({
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD
    })
  }
  
  // CRUD操作封装
  
  async create(table: string, data: any): Promise<any> {
    const fields = Object.keys(data).join(', ')
    const values = Object.values(data)
    const placeholders = values.map((_, i) => `$${i + 1}`).join(', ')
    
    const query = `INSERT INTO ${table} (${fields}) VALUES (${placeholders}) RETURNING *`
    const result = await this.pool.query(query, values)
    return result.rows[0]
  }
  
  async findOne(table: string, conditions: any): Promise<any> {
    const whereClause = this.buildWhereClause(conditions)
    const values = Object.values(conditions)
    
    const query = `SELECT * FROM ${table} WHERE ${whereClause} LIMIT 1`
    const result = await this.pool.query(query, values)
    return result.rows[0]
  }
  
  async findMany(table: string, conditions: any): Promise<any[]> {
    const whereClause = this.buildWhereClause(conditions)
    const values = Object.values(conditions)
    
    const query = `SELECT * FROM ${table} WHERE ${whereClause}`
    const result = await this.pool.query(query, values)
    return result.rows
  }
  
  async update(table: string, id: string, data: any): Promise<any> {
    const setClause = Object.keys(data)
      .map((key, i) => `${key} = $${i + 1}`)
      .join(', ')
    const values = [...Object.values(data), id]
    
    const query = `UPDATE ${table} SET ${setClause}, updated_at = CURRENT_TIMESTAMP WHERE id = $${values.length} RETURNING *`
    const result = await this.pool.query(query, values)
    return result.rows[0]
  }
  
  async delete(table: string, id: string): Promise<void> {
    await this.pool.query(`DELETE FROM ${table} WHERE id = $1`, [id])
  }
  
  // 复杂查询
  async query(sql: string, params?: any[]): Promise<any[]> {
    const result = await this.pool.query(sql, params)
    return result.rows
  }
  
  private buildWhereClause(conditions: any): string {
    return Object.keys(conditions)
      .map((key, i) => `${key} = $${i + 1}`)
      .join(' AND ')
  }
}
```

---

## 五、Docker Compose完整配置

```yaml
version: '3.8'

services:
  # OpenClaw Gateway
  openclaw-gateway:
    image: field-info-agent:latest
    build: .
    container_name: field-info-agent
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REDIS_URL=redis://redis:6379
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=field_info_agent
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - MINIO_ENDPOINT=minio
      - MINIO_PORT=9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - KIMI_API_KEY=${KIMI_API_KEY}
      - WECOM_CORP_ID=${WECOM_CORP_ID}
      - WECOM_AGENT_ID=${WECOM_AGENT_ID}
      - WECOM_SECRET=${WECOM_SECRET}
    depends_on:
      - redis
      - postgres
      - minio
    restart: always
    networks:
      - agent-network

  # Redis - 会话缓存
  redis:
    image: redis:7-alpine
    container_name: field-info-redis
    volumes:
      - redis_data:/data
    restart: always
    networks:
      - agent-network

  # PostgreSQL - 业务数据库
  postgres:
    image: postgres:15-alpine
    container_name: field-info-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: field_info_agent
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: always
    networks:
      - agent-network

  # MinIO - 对象存储
  minio:
    image: minio/minio:latest
    container_name: field-info-minio
    ports:
      - "9000:9000"    # API端口
      - "9001:9001"    # 控制台端口
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: always
    networks:
      - agent-network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: field-info-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - openclaw-gateway
    restart: always
    networks:
      - agent-network

volumes:
  redis_data:
  postgres_data:
  minio_data:

networks:
  agent-network:
    driver: bridge
```

---

## 六、成本对比（更新）

### 原方案（WPS云文档）
| 项目 | 成本/月 |
|------|--------|
| 云服务器（4核8G） | ¥400 |
| Redis | ¥150 |
| WPS API | ¥300 |
| KIMI API | ¥250 |
| **总计** | **¥1100** |

### 新方案（本地存储）
| 项目 | 成本/月 | 变化 |
|------|--------|------|
| 云服务器（4核8G） | ¥400 | - |
| Redis | ¥150 | - |
| PostgreSQL | ¥0（同一服务器）| 节省¥0 |
| MinIO | ¥0（同一服务器）| 节省¥300 |
| ~~WPS API~~ | ~~¥0~~ | **-¥300** |
| KIMI API | ¥250 | - |
| **总计** | **¥800** | **节省¥300** |

**成本优势**:
- 移除WPS API费用：-¥300/月
- 无新增存储成本（共用服务器资源）
- **总成本降至¥800/月**

---

## 七、优势对比

### WPS方案 vs 本地存储方案

| 维度 | WPS方案 | 本地存储方案（新） |
|------|---------|------------------|
| **权限控制** | ❌ 受限 | ✅ 完全自主 |
| **数据隔离** | ⚠️ 复杂 | ✅ 应用层简单实现 |
| **成本** | ¥1100/月 | **¥800/月** ✅ |
| **部署复杂度** | 低 | 中等 |
| **运维成本** | 低 | 中等 |
| **数据安全** | ⚠️ 依赖第三方 | ✅ 完全自主可控 |
| **扩展性** | 受限 | ✅ 完全自主 |
| **备份恢复** | WPS提供 | 需自行实现 |

**结论**: 本地存储方案在**权限控制**、**成本**、**数据安全**方面更有优势，但需要承担更多运维责任。

---

## 八、迁移计划

### 8.1 数据迁移（如已有WPS数据）

```typescript
// 数据迁移脚本
async function migrateFromWPS() {
  // 1. 从WPS导出数据
  const wpsData = await wpsTool.exportAllData()
  
  // 2. 导入PostgreSQL
  for (const record of wpsData) {
    await dbTool.create('station_work_records', record)
  }
  
  // 3. 文件从WPS下载，上传到MinIO
  for (const file of wpsData.files) {
    const buffer = await wpsTool.downloadFile(file.url)
    await storageTool.uploadPhoto({
      fileBuffer: buffer,
      fileName: file.name,
      // ...
    })
  }
}
```

### 8.2 实施步骤

1. **部署基础服务**
   - 部署PostgreSQL
   - 部署MinIO
   - 初始化数据库表

2. **更新应用代码**
   - 替换WPS Tool为DatabaseTool + StorageTool
   - 更新所有Skill中的数据操作
   - 实现权限控制

3. **数据迁移**（如有）
   - 导出WPS数据
   - 导入本地数据库
   - 迁移文件到MinIO

4. **测试验证**
   - 数据读写测试
   - 权限控制测试
   - 文件上传下载测试
   - 性能测试

---

**创建时间**: 2026-03-17  
**版本**: v2.2  
**变更类型**: 重大架构调整（存储层）
