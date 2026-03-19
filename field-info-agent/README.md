# Field Info Agent - 基础环境

> Field Info Agent 的基础开发和运行环境，包含 PostgreSQL、MinIO 和 Redis 服务。

---

## 📋 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [架构说明](#架构说明)
- [目录结构](#目录结构)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [数据库设计](#数据库设计)
- [故障排查](#故障排查)
- [开发规范](#开发规范)

---

## 项目概述

Field Info Agent 是一个基于 OpenClaw 框架的现场信息收集智能体，用于企业微信场景下的现场工作支持。

### 技术栈

| 服务 | 版本 | 用途 | 端口 |
|------|------|------|------|
| PostgreSQL | 14 | 业务数据持久化 | 5432 |
| MinIO | Latest | 本地对象存储 | 9000 (API), 9001 (Console) |
| Redis | 7 | 缓存和会话管理 | 6379 |

### 特性

- ✅ Docker Compose 一键启动
- ✅ 完整的健康检查机制
- ✅ 自动化数据库初始化
- ✅ MinIO bucket 自动配置
- ✅ 环境验证脚本
- ✅ 完整的日志记录
- ✅ 开发/生产环境分离

---

## 快速开始

### 1. 环境要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 可用内存: 4GB+
- 可用磁盘空间: 10GB+

### 2. 安装步骤

```bash
# 克隆或进入项目目录
cd field-info-agent

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（可选，默认配置适用于开发环境）
vim .env

# 启动所有服务
./scripts/start.sh
```

### 3. 验证安装

```bash
# 运行环境验证
./scripts/verify-env.sh
```

### 4. 访问服务

| 服务 | 地址 | 默认凭据 |
|------|------|----------|
| PostgreSQL | `localhost:5432` | field_user / field_pass |
| MinIO API | `http://localhost:9000` | minioadmin / minioadmin123 |
| MinIO Console | `http://localhost:9001` | minioadmin / minioadmin123 |
| Redis | `localhost:6379` | redispass |

---

## 架构说明

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Field Info Agent                         │
│                    基础环境架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    MinIO     │  │    Redis     │      │
│  │  (Port 5432) │  │ (9000/9001)  │  │  (Port 6379) │      │
│  │              │  │              │  │              │      │
│  │  • 用户数据   │  │  • 原始照片   │  │  • 会话缓存   │      │
│  │  • 会话状态   │  │  • 分析结果   │  │  • 热点数据   │      │
│  │  • 任务记录   │  │  • 生成文档   │  │  • 分布式锁   │      │
│  │  • 分析结果   │  │  • 临时文件   │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
│                    ┌───────┴───────┐                       │
│                    │  Docker       │                       │
│                    │  Network      │                       │
│                    │  (Internal)   │                       │
│                    └───────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
┌──────────────┐
│  企业微信用户  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ OpenClaw     │────▶│   Redis      │
│ Gateway      │     │ (Session)    │
└──────┬───────┘     └──────────────┘
       │
       ├─────────────▶┌──────────────┐
       │              │ PostgreSQL   │
       │              │ (Business)   │
       │              └──────────────┘
       │
       └─────────────▶┌──────────────┐
                      │ MinIO        │
                      │ (Files)      │
                      └──────────────┘
```

---

## 目录结构

```
field-info-agent/
├── docker-compose.yml              # Docker Compose 主配置
├── docker-compose.override.yml     # 开发环境覆盖配置
├── .env.example                    # 环境变量模板
├── .env                            # 环境变量（本地创建，不提交Git）
├── README.md                       # 本文档
│
├── init-scripts/                   # PostgreSQL 初始化脚本
│   ├── 01-init-db.sql             # 数据库和用户创建
│   ├── 02-schema.sql              # 表结构和索引
│   └── 03-seed.sql                # 测试数据
│
└── scripts/                        # 运维脚本
    ├── start.sh                   # 启动服务
    ├── stop.sh                    # 停止服务
    ├── verify-env.sh              # 环境验证
    └── init-minio.sh              # MinIO 初始化
```

---

## 配置说明

### 环境变量 (.env)

```bash
# =============================================================================
# PostgreSQL 数据库配置
# =============================================================================
POSTGRES_USER=field_user
POSTGRES_PASSWORD=field_pass
POSTGRES_DB=field_agent
POSTGRES_PORT=5432

# =============================================================================
# MinIO 对象存储配置
# =============================================================================
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=field-documents
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# =============================================================================
# Redis 缓存配置
# =============================================================================
REDIS_PASSWORD=redispass
REDIS_PORT=6379
```

### 安全配置建议

**生产环境必须修改：**
- 所有默认密码
- 使用强密码（16位以上，包含大小写、数字、特殊字符）
- 启用 SSL/TLS
- 配置防火墙规则
- 定期备份数据

---

## 使用指南

### 启动服务

```bash
# 正常启动
./scripts/start.sh

# 重新构建后启动
./scripts/start.sh --build

# 清理数据后重新启动
./scripts/start.sh --clean

# 启动并查看日志
./scripts/start.sh --logs
```

### 停止服务

```bash
# 正常停止
./scripts/stop.sh

# 停止并删除数据卷（谨慎使用）
./scripts/stop.sh --volumes

# 完全清理
./scripts/stop.sh --all
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f minio
docker-compose logs -f redis

# 查看最近100行日志
docker-compose logs --tail=100
```

### 数据库操作

```bash
# 连接到 PostgreSQL
docker exec -it field-postgres psql -U field_user -d field_agent

# 执行 SQL 文件
docker exec -i field-postgres psql -U field_user -d field_agent < your-script.sql

# 备份数据库
docker exec field-postgres pg_dump -U field_user field_agent > backup.sql

# 恢复数据库
docker exec -i field-postgres psql -U field_user -d field_agent < backup.sql
```

### MinIO 操作

```bash
# 配置 mc 客户端
mc alias set local http://localhost:9000 minioadmin minioadmin123

# 列出 buckets
mc ls local

# 查看 bucket 内容
mc ls -r local/field-documents

# 上传文件
mc cp local-file.jpg local/field-documents/raw-photos/

# 下载文件
mc cp local/field-documents/generated-docs/report.pdf ./
```

### Redis 操作

```bash
# 连接到 Redis
redis-cli -h localhost -p 6379 -a redispass

# 或使用 Docker
docker exec -it field-redis redis-cli -a redispass

# 常用命令
KEYS *                    # 列出所有键
GET key_name             # 获取值
SET key_name value       # 设置值
DEL key_name             # 删除键
FLUSHALL                 # 清空所有数据（谨慎使用）
INFO                     # 查看服务器信息
```

---

## 数据库设计

### 实体关系图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │   sessions  │       │    tasks    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ username    │  │    │ user_id(FK) │──┘    │ user_id(FK) │
│ email       │  └──▶ │ session_id  │        │ session_id  │
│ phone       │       │ status      │        │ status      │
│ status      │       │ context     │        │ result      │
│ role        │       └─────────────┘        └──────┬──────┘
└─────────────┘                                     │
       │                                            │
       │    ┌─────────────┐       ┌─────────────┐   │
       └───▶│  documents  │       │analysis_res │◀──┘
            ├─────────────┤       ├─────────────┤
            │ id (PK)     │       │ id (PK)     │
            │ user_id(FK) │       │ task_id(FK) │
            │ task_id(FK) │       │ user_id(FK) │
            │ storage_key │       │ result      │
            │ file_format │       │ summary     │
            └─────────────┘       └─────────────┘
```

### 表说明

| 表名 | 用途 | 核心字段 |
|------|------|----------|
| `users` | 用户管理 | id, wecom_user_id, username, role |
| `sessions` | 会话管理 | id, user_id, context, current_skill |
| `tasks` | 任务记录 | id, user_id, task_type, status, result |
| `analysis_results` | AI分析结果 | id, task_id, analysis_type, result |
| `documents` | 文档管理 | id, storage_key, file_format, status |
| `system_logs` | 系统日志 | id, log_level, source, message |

### 索引设计

- 所有表都有 `created_at` 索引，支持时间范围查询
- 外键字段都有索引，支持关联查询
- 常用查询字段（status, task_type）都有索引
- JSONB 字段支持 GIN 索引（按需添加）

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :9000  # MinIO API
lsof -i :9001  # MinIO Console
lsof -i :6379  # Redis

# 停止占用端口的进程或修改 .env 中的端口配置
```

#### 2. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker-compose ps postgres
docker-compose logs postgres

# 检查用户是否存在
docker exec field-postgres psql -U postgres -c "\du"

# 重置数据库（会丢失数据）
./scripts/stop.sh --volumes
./scripts/start.sh
```

#### 3. MinIO 无法访问

```bash
# 检查 MinIO 状态
docker-compose ps minio
docker-compose logs minio

# 检查健康状态
curl http://localhost:9000/minio/health/live

# 重新初始化 MinIO
docker-compose restart minio-init
```

#### 4. 权限问题

```bash
# 修复脚本权限
chmod +x scripts/*.sh

# 修复数据目录权限
sudo chown -R $USER:$USER data/
```

### 日志分析

```bash
# 查看错误日志
docker-compose logs | grep ERROR
docker-compose logs | grep -i error

# 查看启动日志
docker-compose logs | grep -i "start\|init\|ready"
```

### 重置环境

```bash
# 完全重置（删除所有数据）
./scripts/stop.sh --all
./scripts/start.sh --clean
```

---

## 开发规范

### 代码规范

1. **SQL 文件**
   - 使用大写关键字
   - 添加完整注释
   - 遵循 01-, 02-, 03- 命名约定

2. **Shell 脚本**
   - 使用 `#!/bin/bash`
   - 添加 `set -e`
   - 包含详细的注释头
   - 使用颜色输出增强可读性

3. **配置文件**
   - 使用 YAML 格式（Docker Compose）
   - 添加详细注释
   - 敏感信息使用环境变量

### Git 规范

```bash
# .gitignore 内容
.env
data/
logs/
*.log
.DS_Store
```

### 提交信息

```
[TASK-001] 添加 PostgreSQL 初始化脚本
[TASK-001] 修复 MinIO 健康检查配置
[TASK-001] 更新 README 文档
```

---

## 性能优化

### PostgreSQL

```sql
-- 定期分析表
ANALYZE users;
ANALYZE tasks;

-- 查看慢查询
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

### MinIO

```bash
# 监控磁盘使用
mc admin info local

# 检查存储桶统计
mc stat local/field-documents
```

### Redis

```bash
# 监控内存使用
redis-cli -a redispass INFO memory

# 查看慢查询
redis-cli -a redispass SLOWLOG get 10
```

---

## 备份策略

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 PostgreSQL
docker exec field-postgres pg_dump -U field_user field_agent > "backup/db_$DATE.sql"

# 备份 MinIO
mc mirror local/field-documents "backup/minio_$DATE/"

# 备份 Redis
redis-cli -a redispass SAVE
docker cp field-redis:/data/dump.rdb "backup/redis_$DATE.rdb"

# 压缩备份
tar -czf "backup_$DATE.tar.gz" backup/
```

---

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/TASK-XXX`)
3. 提交更改 (`git commit -am '[TASK-XXX] 描述'`)
4. 推送到分支 (`git push origin feature/TASK-XXX`)
5. 创建 Pull Request

---

## 许可证

本项目采用 [LICENSE](../LICENSE) 许可证。

---

## 联系方式

- **项目主页**: [Field Info Agent](../../knowledge-base/field-info-agent/README.md)
- **问题反馈**: [Issues](../../issues)
- **开发团队**: Field Core Team
- **维护者**: PM Agent

---

**最后更新**: 2026-03-19  
**版本**: 1.0.0
