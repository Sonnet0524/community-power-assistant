# Task-002: PostgreSQL/MinIO Tool 开发

## 任务概述

**任务ID**: TASK-002  
**任务名称**: PostgreSQL/MinIO Tool 开发  
**优先级**: 🔴 最高  
**预计工期**: 3-4天  
**依赖**: TASK-001  
**负责团队**: Field Core Team

## 任务目标

开发 PostgreSQL 和 MinIO Tool，封装数据库和对象存储操作，为 OpenClaw Skills 提供数据持久化能力。

## 详细工作内容

### 1. PostgreSQL Tool

**功能需求**:
- 数据库连接池管理
- CRUD 操作封装
- 事务支持
- 连接健康检查
- SQL 注入防护

**接口设计**:
```python
class PostgreSQLTool:
    async def connect(self) -> Connection
    async def query(self, sql: str, params: dict = None) -> List[Dict]
    async def execute(self, sql: str, params: dict = None) -> int
    async def transaction(self) -> TransactionContext
    async def health_check(self) -> bool
    async def close(self)
```

**数据库表操作**:
- [ ] 用户表操作（users）
  - create_user(), get_user(), update_user(), delete_user()
- [ ] 会话表操作（sessions）
  - create_session(), get_session(), update_session(), delete_session()
- [ ] 任务表操作（tasks）
  - create_task(), get_task(), update_task(), list_tasks()
- [ ] 分析结果表操作（analysis_results）
  - save_analysis(), get_analysis(), list_analysis()
- [ ] 文档表操作（documents）
  - save_document(), get_document(), update_document()

**验收标准**:
- ✅ 连接池正常工作
- ✅ 所有 CRUD 操作正常
- ✅ 事务支持 ACID
- ✅ SQL 注入防护完善
- ✅ 性能满足要求（查询 < 100ms）

### 2. MinIO Tool

**功能需求**:
- MinIO 客户端封装
- 文件上传/下载
- 预签名 URL 生成
- 文件元数据管理
- 分片上传支持（大文件）

**接口设计**:
```python
class MinIOTool:
    async def upload_file(self, file_path: str, object_name: str, 
                         metadata: dict = None) -> str
    async def download_file(self, object_name: str, file_path: str)
    async def get_presigned_url(self, object_name: str, 
                               expires: int = 3600) -> str
    async def delete_file(self, object_name: str)
    async def list_files(self, prefix: str = None) -> List[Dict]
    async def get_file_metadata(self, object_name: str) -> Dict
    async def health_check(self) -> bool
```

**Bucket 结构**:
```
field-documents/
├── raw-photos/          # 原始照片
│   ├── {user_id}/
│   └── {task_id}/
├── analysis-outputs/    # 分析结果
│   ├── {task_id}/
│   └── json/
├── generated-docs/      # 生成的文档
│   ├── {user_id}/
│   └── {date}/
├── temp/               # 临时文件
└── backups/            # 备份文件
```

**工作内容**:
- [ ] 实现文件上传（支持元数据）
- [ ] 实现文件下载
- [ ] 实现预签名 URL 生成（用于分享）
- [ ] 实现文件删除
- [ ] 实现文件列表查询
- [ ] 实现分片上传（支持大文件）
- [ ] 实现文件元数据管理

**验收标准**:
- ✅ 文件上传/下载正常
- ✅ 预签名 URL 可访问
- ✅ 元数据正确存储
- ✅ 大文件分片上传正常

### 3. Redis Tool

**功能需求**:
- 缓存操作封装
- Session 存储
- 分布式锁
- 限流支持

**接口设计**:
```python
class RedisTool:
    async def get(self, key: str) -> Any
    async def set(self, key: str, value: Any, expire: int = None)
    async def delete(self, key: str)
    async def expire(self, key: str, seconds: int)
    async def exists(self, key: str) -> bool
    async def acquire_lock(self, lock_name: str, 
                          timeout: int = 10) -> bool
    async def release_lock(self, lock_name: str)
    async def rate_limit_check(self, key: str, 
                              limit: int, window: int) -> bool
    async def health_check(self) -> bool
```

**工作内容**:
- [ ] 实现 KV 操作
- [ ] 实现 Session 存储
- [ ] 实现分布式锁
- [ ] 实现限流检查

**验收标准**:
- ✅ KV 操作正常
- ✅ Session 可正常读写
- ✅ 分布式锁工作正常
- ✅ 限流功能正常

### 4. 配置管理

**配置文件**:
```yaml
# config/tools.yaml
tools:
  postgresql:
    host: "${POSTGRES_HOST}"
    port: "${POSTGRES_PORT}"
    database: "${POSTGRES_DB}"
    user: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
    
  minio:
    endpoint: "${MINIO_ENDPOINT}"
    access_key: "${MINIO_ACCESS_KEY}"
    secret_key: "${MINIO_SECRET_KEY}"
    bucket: "${MINIO_BUCKET}"
    secure: false
    region: "us-east-1"
    
  redis:
    host: "${REDIS_HOST}"
    port: "${REDIS_PORT}"
    password: "${REDIS_PASSWORD}"
    db: 0
    decode_responses: true
```

**环境变量模板**（补充到 `.env.example`）:
```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=field_agent
POSTGRES_USER=field_user
POSTGRES_PASSWORD=field_pass

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=field-documents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redispass
```

### 5. 错误处理

**错误类型**:
```python
class ToolError(Exception):
    """Tool 基础错误"""
    pass

class PostgreSQLError(ToolError):
    """PostgreSQL 错误"""
    pass

class MinIOError(ToolError):
    """MinIO 错误"""
    pass

class RedisError(ToolError):
    """Redis 错误"""
    pass

class ConnectionError(ToolError):
    """连接错误"""
    pass

class ValidationError(ToolError):
    """参数校验错误"""
    pass
```

**错误处理要求**:
- 所有数据库操作必须有 try-except
- 连接失败自动重试（最多3次）
- 详细的错误日志
- 友好的错误信息

### 6. 日志记录

**日志格式**:
```python
{
    "timestamp": "2026-03-19T21:50:00Z",
    "tool": "postgresql|minio|redis",
    "operation": "query|upload|get",
    "duration_ms": 50,
    "status": "success|error",
    "error": null,
    "metadata": {
        "table": "users",
        "rows_affected": 1
    }
}
```

## 测试要求

### 单元测试
- [ ] PostgreSQL Tool 测试（覆盖率 >90%）
  - 连接测试
  - CRUD 操作测试
  - 事务测试
  - 错误处理测试
- [ ] MinIO Tool 测试（覆盖率 >90%）
  - 上传/下载测试
  - 预签名 URL 测试
  - 元数据测试
  - 大文件测试
- [ ] Redis Tool 测试（覆盖率 >90%）
  - KV 操作测试
  - Session 测试
  - 锁测试
  - 限流测试

### 集成测试
- [ ] 与 TASK-001 环境集成测试
- [ ] 并发操作测试
- [ ] 故障恢复测试
- [ ] 性能基准测试

### 性能要求
- PostgreSQL 查询: < 100ms (95th percentile)
- MinIO 上传: < 500ms (1MB 文件)
- MinIO 下载: < 300ms (1MB 文件)
- Redis 操作: < 10ms

## 技术规范

### 代码规范
- 使用 async/await 异步编程
- 类型注解（Python 3.9+）
- 文档字符串（Google Style）
- PEP 8 代码风格

### 依赖管理
```txt
# requirements.txt
asyncpg==0.29.0          # PostgreSQL 异步驱动
minio==7.2.0             # MinIO 客户端
redis==5.0.0             # Redis 客户端
python-dotenv==1.0.0     # 环境变量加载
pydantic==2.5.0          # 数据验证
```

## 交付物

1. **源代码**:
   - `src/tools/postgresql_tool.py`
   - `src/tools/minio_tool.py`
   - `src/tools/redis_tool.py`
   - `src/tools/__init__.py`
   - `src/tools/base.py` (Tool 基类)

2. **配置文件**:
   - `config/tools.yaml`
   - `.env.example`（更新）

3. **类型定义**:
   - `src/tools/types.py`

4. **单元测试**:
   - `tests/tools/test_postgresql_tool.py`
   - `tests/tools/test_minio_tool.py`
   - `tests/tools/test_redis_tool.py`

5. **使用文档**:
   - `docs/tools/README.md`

## 验收标准

- [ ] 所有 Tool 实现并通过测试
- [ ] 单元测试覆盖率 >90%
- [ ] 集成测试通过
- [ ] 性能测试达标
- [ ] 文档完整
- [ ] 代码审查通过

## 使用示例

```python
# PostgreSQL 使用示例
from tools import PostgreSQLTool

pg_tool = PostgreSQLTool()
user = await pg_tool.get_user(user_id="user_123")

# MinIO 使用示例
from tools import MinIOTool

minio_tool = MinIOTool()
url = await minio_tool.upload_file(
    file_path="/tmp/photo.jpg",
    object_name="raw-photos/user_123/photo.jpg",
    metadata={"user_id": "user_123", "task_id": "task_456"}
)

# Redis 使用示例
from tools import RedisTool

redis_tool = RedisTool()
await redis_tool.set("session:user_123", session_data, expire=3600)
```

## 相关文档

- [项目总览](../knowledge-base/field-info-agent/README.md)
- [数据库 Schema](../knowledge-base/field-info-agent/implementation/database/schema.sql)
- [TASK-001 环境搭建](./TASK-001-environment-setup.md)
- PostgreSQL 文档: https://www.postgresql.org/docs/14/
- MinIO Python SDK: https://min.io/docs/minio/linux/developers/python/minio-py.html
- Redis Python 客户端: https://redis-py.readthedocs.io/

## 报告要求

完成后请提交报告到: `reports/REPORT-002-postgresql-minio-tool.md`

---

**创建时间**: 2026-03-17  
**更新**: 2026-03-19（更新为 PostgreSQL/MinIO Tool，移除 WPS）  
**负责团队**: Field Core Team  
**状态**: 待开始  
**依赖**: TASK-001 ✅ 已完成