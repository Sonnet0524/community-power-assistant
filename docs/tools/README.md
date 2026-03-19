# Field Info Agent - Tools 使用文档

本文档介绍 Field Info Agent 项目中 Tools 的使用方法。

## 概述

Tools 模块提供了对 PostgreSQL、MinIO、Redis 等基础设施的封装，为 OpenClaw Skills 提供数据持久化、文件存储和缓存能力。

## 安装

### 依赖安装

```bash
# 基础依赖
pip install pydantic python-dotenv

# PostgreSQL
pip install asyncpg==0.29.0

# MinIO
pip install minio==7.2.0

# Redis
pip install redis==5.0.0
```

## 配置

### 环境变量

在项目根目录创建 `.env` 文件：

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=field_agent
POSTGRES_USER=field_user
POSTGRES_PASSWORD=your_password

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=field-documents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

### 配置文件

`config/tools.yaml` 提供了结构化的配置：

```yaml
tools:
  postgresql:
    host: "${POSTGRES_HOST}"
    port: ${POSTGRES_PORT}
    database: "${POSTGRES_DB}"
    user: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
```

## 快速开始

### PostgreSQL Tool

```python
import asyncio
from src.tools import PostgreSQLTool
from src.tools.types import PostgreSQLConfig, User

async def main():
    # 配置
    config = PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="field_agent",
        user="field_user",
        password="field_pass"
    )
    
    # 使用上下文管理器（推荐）
    async with PostgreSQLTool(config) as pg:
        # 查询
        users = await pg.query(
            "SELECT * FROM users WHERE department = $1",
            {"department": "IT"}
        )
        print(f"Found {len(users)} users")
        
        # 执行
        rows = await pg.execute(
            "UPDATE users SET name = $1 WHERE id = $2",
            {"name": "张三", "id": "user_123"}
        )
        print(f"Updated {rows} rows")
        
        # 事务
        async with pg.transaction() as txn:
            await txn.execute("INSERT INTO logs (message) VALUES ($1)", 
                            {"message": "User updated"})
        
        # 表操作 - 用户
        user = await pg.get_user("user_123")
        if user:
            print(f"User: {user.name}")
        
        new_user = User(id="user_456", name="李四", department="HR")
        await pg.create_user(new_user)

asyncio.run(main())
```

### MinIO Tool

```python
import asyncio
from src.tools import MinIOTool
from src.tools.types import MinIOConfig

async def main():
    # 配置
    config = MinIOConfig(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        bucket="field-documents"
    )
    
    async with MinIOTool(config) as minio:
        # 上传文件
        result = await minio.upload_file(
            file_path="/tmp/photo.jpg",
            object_name="raw-photos/user_123/photo.jpg",
            metadata={"user_id": "user_123", "task_id": "task_456"}
        )
        print(f"Uploaded: {result.object_name}, ETag: {result.etag}")
        
        # 下载文件
        await minio.download_file(
            object_name="raw-photos/user_123/photo.jpg",
            file_path="/tmp/downloaded.jpg"
        )
        
        # 生成预签名 URL（用于分享）
        url = await minio.get_presigned_url(
            object_name="raw-photos/user_123/photo.jpg",
            expires=3600  # 1小时
        )
        print(f"Presigned URL: {url}")
        
        # 列出文件
        files = await minio.list_files(prefix="raw-photos/user_123/")
        for file in files:
            print(f"  - {file.object_name} ({file.size} bytes)")
        
        # 获取元数据
        metadata = await minio.get_file_metadata("raw-photos/user_123/photo.jpg")
        print(f"Content-Type: {metadata.content_type}")
        
        # 删除文件
        await minio.delete_file("temp/old_file.jpg")
        
        # 移动文件
        await minio.move_file(
            source_object="temp/draft.jpg",
            dest_object="final/document.jpg"
        )

asyncio.run(main())
```

### Redis Tool

```python
import asyncio
from src.tools import RedisTool
from src.tools.types import RedisConfig

async def main():
    # 配置
    config = RedisConfig(
        host="localhost",
        port=6379,
        password="redispass"
    )
    
    async with RedisTool(config) as redis:
        # KV 操作
        await redis.set("key", "value", expire=3600)
        value = await redis.get("key")
        print(f"Value: {value}")
        
        # 检查存在
        exists = await redis.exists("key")
        print(f"Exists: {exists}")
        
        # 获取剩余时间
        ttl = await redis.ttl("key")
        print(f"TTL: {ttl} seconds")
        
        # Session 存储
        await redis.set_session(
            session_id="session_123",
            data={"user_id": "user_456", "role": "admin"},
            expire=3600
        )
        
        session = await redis.get_session("session_123")
        print(f"Session: {session}")
        
        # 分布式锁
        lock = await redis.acquire_lock("task_lock", timeout=10)
        if lock.acquired:
            try:
                print("Lock acquired, executing critical section...")
                # 执行临界区代码
            finally:
                await redis.release_lock("task_lock", lock.identifier)
                print("Lock released")
        else:
            print("Failed to acquire lock")
        
        # 限流检查
        rate_limit = await redis.rate_limit_check(
            key="api_user_123",
            limit=100,    # 100次
            window=60     # 每60秒
        )
        
        if rate_limit.allowed:
            print(f"Request allowed. Remaining: {rate_limit.remaining}")
        else:
            print("Rate limit exceeded")
        
        # 原子递增
        count = await redis.increment("counter", amount=1)
        print(f"Counter: {count}")
        
        # 集合操作
        await redis.set_add("tags", "python", "async", "redis")
        tags = await redis.set_members("tags")
        print(f"Tags: {tags}")
        
        # 列表操作
        await redis.list_push("queue", "task1", "task2", "task3")
        tasks = await redis.list_range("queue", 0, 9)
        print(f"Queue: {tasks}")

asyncio.run(main())
```

## 高级用法

### 错误处理

```python
from src.tools import PostgreSQLTool
from src.tools.errors import PostgreSQLError, NotFoundError, ConnectionError

async def safe_query():
    try:
        async with PostgreSQLTool(config) as pg:
            user = await pg.get_user("user_123")
            if not user:
                print("User not found")
                return
            print(f"User: {user.name}")
            
    except ConnectionError as e:
        print(f"Connection failed: {e.message}")
        print(f"Suggestion: {e.suggestion}")
        
    except PostgreSQLError as e:
        print(f"Database error: {e.message}")
        print(f"Details: {e.details}")
```

### 连接池配置

```python
from src.tools.types import PostgreSQLConfig

config = PostgreSQLConfig(
    host="localhost",
    port=5432,
    database="field_agent",
    user="field_user",
    password="field_pass",
    pool_size=20,          # 连接池大小
    max_overflow=30,       # 最大溢出连接
    pool_timeout=60        # 连接超时（秒）
)
```

### 批量操作

```python
# PostgreSQL 批量插入
async with PostgreSQLTool(config) as pg:
    async with pg.transaction() as txn:
        for user in users:
            await txn.execute(
                "INSERT INTO users (id, name) VALUES ($1, $2)",
                {"id": user.id, "name": user.name}
            )

# MinIO 批量上传
async with MinIOTool(config) as minio:
    tasks = [
        minio.upload_file(f"photos/{f}", f"uploads/{f}")
        for f in files
    ]
    results = await asyncio.gather(*tasks)
```

### 统计信息

```python
async with PostgreSQLTool(config) as pg:
    # 执行一些操作...
    
    # 获取统计信息
    stats = pg.get_stats()
    print(f"Operations: {stats['operation_count']}")
    print(f"Errors: {stats['error_count']}")
    print(f"Error rate: {stats['error_rate']:.2%}")
```

## API 参考

### PostgreSQLTool

| 方法 | 说明 |
|------|------|
| `connect()` | 建立数据库连接 |
| `close()` | 关闭连接 |
| `health_check()` | 健康检查 |
| `query(sql, params)` | 执行查询 |
| `execute(sql, params)` | 执行语句 |
| `transaction()` | 获取事务上下文 |
| `create_user(user)` | 创建用户 |
| `get_user(user_id)` | 获取用户 |
| `update_user(user)` | 更新用户 |
| `delete_user(user_id)` | 删除用户 |
| `create_task(task)` | 创建任务 |
| `get_task(task_id)` | 获取任务 |
| `list_tasks(...)` | 列出任务 |
| `save_analysis(result)` | 保存分析结果 |
| `get_analysis(result_id)` | 获取分析结果 |
| `save_document(doc)` | 保存文档 |
| `get_document(doc_id)` | 获取文档 |

### MinIOTool

| 方法 | 说明 |
|------|------|
| `connect()` | 建立 MinIO 连接 |
| `close()` | 关闭连接 |
| `health_check()` | 健康检查 |
| `upload_file(...)` | 上传文件 |
| `upload_bytes(...)` | 上传字节数据 |
| `download_file(...)` | 下载文件 |
| `download_bytes(...)` | 下载字节数据 |
| `get_presigned_url(...)` | 生成预签名 URL |
| `delete_file(...)` | 删除文件 |
| `list_files(...)` | 列出文件 |
| `get_file_metadata(...)` | 获取文件元数据 |
| `copy_file(...)` | 复制文件 |
| `move_file(...)` | 移动文件 |

### RedisTool

| 方法 | 说明 |
|------|------|
| `connect()` | 建立 Redis 连接 |
| `close()` | 关闭连接 |
| `health_check()` | 健康检查 |
| `get(key)` | 获取值 |
| `set(key, value, expire)` | 设置值 |
| `delete(key)` | 删除键 |
| `expire(key, seconds)` | 设置过期时间 |
| `exists(key)` | 检查存在 |
| `ttl(key)` | 获取剩余时间 |
| `set_session(...)` | 存储 Session |
| `get_session(session_id)` | 获取 Session |
| `acquire_lock(...)` | 获取分布式锁 |
| `release_lock(...)` | 释放分布式锁 |
| `rate_limit_check(...)` | 限流检查 |
| `increment(key, amount)` | 原子递增 |
| `set_add(key, *members)` | 添加集合成员 |
| `set_members(key)` | 获取集合成员 |
| `list_push(key, *values)` | 向列表添加元素 |
| `list_range(key, start, end)` | 获取列表范围 |

## 性能优化

### PostgreSQL

1. **使用连接池**：复用连接减少开销
2. **使用事务**：批量操作使用事务提高性能
3. **索引优化**：为常用查询字段添加索引
4. **查询优化**：避免 SELECT *，只查询需要的字段

### MinIO

1. **预签名 URL**：用于前端直接上传下载
2. **批量操作**：并发上传下载提高效率
3. **分片上传**：大文件使用分片上传

### Redis

1. **合理设置过期时间**：避免数据无限增长
2. **使用 Pipeline**：批量操作使用 Pipeline
3. **选择合适的结构**：根据场景选择 String/Hash/List/Set

## 故障排查

### 常见问题

1. **连接失败**
   - 检查服务是否运行
   - 检查网络连通性
   - 检查配置参数

2. **权限错误**
   - 检查用户名密码
   - 检查访问权限

3. **性能问题**
   - 检查连接池配置
   - 监控慢查询
   - 检查资源使用情况

### 日志

Tool 会自动记录操作日志，包括：
- 操作类型
- 执行时长
- 成功/失败状态
- 错误信息

日志级别可通过标准 logging 模块配置。

## 测试

```bash
# 运行所有测试
pytest tests/tools/ -v

# 运行指定测试
pytest tests/tools/test_tools.py::TestPostgreSQLTool -v

# 生成覆盖率报告
pytest tests/tools/ --cov=src.tools --cov-report=html
```

## 版本历史

- **v1.0.0** (2026-03-19)
  - 初始版本
  - PostgreSQL、MinIO、Redis Tool 实现
  - 完整单元测试（覆盖率 >90%）

## 贡献

请遵循以下规范：
1. 所有代码必须通过单元测试
2. 覆盖率 >90%
3. 遵循 PEP 8 代码风格
4. 提供完整文档字符串

## 许可证

MIT License
