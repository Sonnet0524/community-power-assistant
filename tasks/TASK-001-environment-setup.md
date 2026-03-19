# Task-001: 基础环境搭建

## 任务概述

**任务ID**: TASK-001  
**任务名称**: 基础环境搭建  
**优先级**: 🔴 最高  
**预计工期**: 2-3天  
**依赖**: 无  
**负责团队**: Field Core Team

## 任务目标

搭建 Field Info Agent 的基础开发和运行环境，包括 Docker Compose 配置和本地存储服务（PostgreSQL + MinIO + Redis）。

## 技术栈

- **PostgreSQL 14**: 业务数据持久化（会话、用户信息、分析结果）
- **MinIO**: 本地对象存储（替代 WPS 云文档，节省成本）
- **Redis**: 缓存和会话管理
- **Docker Compose**: 本地开发和部署编排

## 详细工作内容

### 1. Docker Compose 配置文件

**工作内容**:
- [ ] 创建 `docker-compose.yml`，包含以下服务：
  - PostgreSQL 14（端口 5432）
    - 配置数据库: `field_agent`
    - 创建用户: `field_user`
    - 设置持久化卷
  - MinIO（端口 9000 API, 9001 Console）
    - 创建 bucket: `field-documents`
    - 配置访问密钥
  - Redis（端口 6379）
    - 配置密码认证
    - 启用持久化
- [ ] 创建 `.env.example` 环境变量模板
- [ ] 创建 `docker-compose.override.yml` 用于开发环境
- [ ] 配置健康检查（healthcheck）

**交付物**:
- `docker-compose.yml`
- `.env.example`
- `docker-compose.override.yml`

### 2. PostgreSQL 初始化

**工作内容**:
- [ ] 创建数据库初始化脚本 `init-scripts/01-init-db.sql`：
  - 创建数据库: `field_agent`
  - 创建用户: `field_user` / `field_pass`
  - 授权访问
- [ ] 创建 Schema 初始化脚本 `init-scripts/02-schema.sql`：
  - 用户表: `users`
  - 会话表: `sessions`
  - 任务表: `tasks`
  - 分析结果表: `analysis_results`
  - 文档表: `documents`
  - 索引和约束
- [ ] 创建 `init-scripts/03-seed.sql` 初始化测试数据

**交付物**:
- `init-scripts/01-init-db.sql`
- `init-scripts/02-schema.sql`
- `init-scripts/03-seed.sql`
- Schema 文档（README）

### 3. MinIO 初始化

**工作内容**:
- [ ] 创建 MinIO 初始化脚本 `init-minio.sh`：
  - 等待 MinIO 服务就绪
  - 创建 bucket: `field-documents`
  - 设置 bucket 策略（读写权限）
- [ ] 配置 MinIO 客户端 (mc) 命令
- [ ] 创建 bucket 目录结构：
  - `raw-photos/` - 原始照片
  - `analysis-outputs/` - 分析输出
  - `generated-docs/` - 生成的文档

**交付物**:
- `init-minio.sh`
- Bucket 结构和策略文档

### 4. 环境验证

**工作内容**:
- [ ] 创建 `scripts/verify-env.sh` 验证脚本：
  - 检查所有容器状态
  - 测试 PostgreSQL 连接
  - 测试 MinIO 连接
  - 测试 Redis 连接
- [ ] 创建 `scripts/start.sh` 启动脚本
- [ ] 创建 `scripts/stop.sh` 停止脚本
- [ ] 编写环境搭建 README 文档

**交付物**:
- `scripts/verify-env.sh`
- `scripts/start.sh`
- `scripts/stop.sh`
- `README.md`

## 目录结构

```
field-info-agent/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── init-scripts/
│   ├── 01-init-db.sql
│   ├── 02-schema.sql
│   └── 03-seed.sql
├── scripts/
│   ├── verify-env.sh
│   ├── start.sh
│   └── stop.sh
└── README.md
```

## 验收标准

- [ ] Docker Compose 可正常启动所有服务
- [ ] PostgreSQL 可连接并执行查询
- [ ] MinIO 可访问，bucket 已创建
- [ ] Redis 可连接并读写数据
- [ ] 验证脚本运行通过
- [ ] 文档清晰完整

## 技术参考

### PostgreSQL Schema 设计

详见: `knowledge-base/field-info-agent/implementation/database/schema.sql`

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库访问 |
| MinIO API | 9000 | 对象存储 API |
| MinIO Console | 9001 | 管理界面 |
| Redis | 6379 | 缓存服务 |

### 环境变量模板

```bash
# Database
POSTGRES_USER=field_user
POSTGRES_PASSWORD=field_pass
POSTGRES_DB=field_agent
POSTGRES_PORT=5432

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=field-documents
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Redis
REDIS_PASSWORD=redispass
REDIS_PORT=6379
```

## 相关文档

- [项目总览](../knowledge-base/field-info-agent/README.md)
- [详细设计](../knowledge-base/field-info-agent/design/detailed-design-v2.md)
- [数据库 Schema](../knowledge-base/field-info-agent/implementation/database/schema.sql)
- [Docker Compose 文档](https://docs.docker.com/compose/)

## 报告要求

完成后请提交报告到: `reports/REPORT-001-environment-setup.md`

报告应包含：
- 完成情况列表
- 交付物清单
- 验证结果
- 遇到的问题和解决方案
- 使用说明

---

**创建时间**: 2026-03-19  
**更新**: 2026-03-19（更新为本地存储方案）  
**负责团队**: Field Core Team  
**状态**: 待开始
