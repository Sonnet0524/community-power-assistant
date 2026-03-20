# Field Info Agent - 部署操作手册

> 🚀 从零开始部署 Field Info Agent 到生产环境

---

## 📋 部署前检查清单

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 20GB | 50GB+ SSD |
| 网络 | 10Mbps | 100Mbps+ |

### 软件要求

- [ ] Docker Engine 20.10+
- [ ] Docker Compose 2.0+
- [ ] Git
- [ ] curl/wget

### 网络要求

- [ ] 公网IP（用于企业微信回调）
- [ ] 域名（建议配置SSL证书）
- [ ] 端口开放：5432, 9000, 9001, 6379, 8080

---

## 🚀 快速部署（5分钟）

### 步骤1: 克隆代码

```bash
# 克隆仓库
git clone https://github.com/Sonnet0524/community-power-assistant.git
cd community-power-assistant/field-info-agent
```

### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
vim .env
```

**必须配置的环境变量**:

```bash
# PostgreSQL
POSTGRES_USER=field_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=field_agent

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_strong_password_here
MINIO_BUCKET=field-documents

# Redis
REDIS_PASSWORD=your_redis_password_here

# KIMI API
KIMI_API_KEY=sk-your-kimi-api-key-here
KIMI_BASE_URL=https://api.kimi.com/coding/
KIMI_MODEL=kimi-for-coding

# 企业微信（后续配置）
# WECOM_CORP_ID=xxx
# WECOM_AGENT_ID=xxx
# WECOM_SECRET=xxx
```

⚠️ **重要**: 使用强密码（16位以上，包含大小写、数字、特殊字符）

### 步骤3: 启动服务

```bash
# 使用启动脚本
./scripts/start.sh

# 或者使用 Docker Compose 直接启动
docker-compose up -d
```

### 步骤4: 验证部署

```bash
# 运行环境验证脚本
./scripts/verify-env.sh

# 或者手动检查
docker-compose ps
```

**预期输出**:
```
NAME                COMMAND                  SERVICE             STATUS              PORTS
field-postgres      "docker-entrypoint.s…"   postgres            running (healthy)   5432/tcp
field-minio         "/usr/bin/docker-ent…"   minio               running (healthy)   9000/tcp, 9001/tcp
field-redis         "docker-entrypoint.s…"   redis               running (healthy)   6379/tcp
```

### 步骤5: 访问服务

| 服务 | 地址 | 默认账号 | 默认密码 |
|------|------|---------|---------|
| PostgreSQL | `localhost:5432` | field_user | `.env中配置` |
| MinIO Console | `http://localhost:9001` | minioadmin | `.env中配置` |
| MinIO API | `http://localhost:9000` | - | - |
| Redis | `localhost:6379` | - | `.env中配置` |

---

## 🔧 详细部署指南

### 1. 服务器准备

#### 1.1 系统更新

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 1.2 安装 Docker

```bash
# 使用官方脚本安装
curl -fsSL https://get.docker.com | sh

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组（免sudo）
sudo usermod -aG docker $USER
```

#### 1.3 安装 Docker Compose

```bash
# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 2. 代码部署

#### 2.1 下载代码

```bash
# 创建项目目录
mkdir -p /opt/field-info-agent
cd /opt/field-info-agent

# 克隆代码
git clone https://github.com/Sonnet0524/community-power-assistant.git .
```

#### 2.2 配置文件权限

```bash
# 设置脚本执行权限
chmod +x field-info-agent/scripts/*.sh

# 设置数据目录权限
mkdir -p field-info-agent/data
chmod 755 field-info-agent/data
```

### 3. 环境配置

#### 3.1 生成强密码

```bash
# 生成随机密码（用于PostgreSQL和MinIO）
export PG_PASSWORD=$(openssl rand -base64 32)
export MINIO_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

echo "PostgreSQL Password: $PG_PASSWORD"
echo "MinIO Password: $MINIO_PASSWORD"
echo "Redis Password: $REDIS_PASSWORD"
```

#### 3.2 配置.env文件

```bash
cd field-info-agent

cat > .env << EOF
# PostgreSQL
POSTGRES_USER=field_user
POSTGRES_PASSWORD=$PG_PASSWORD
POSTGRES_DB=field_agent
POSTGRES_PORT=5432

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=$MINIO_PASSWORD
MINIO_BUCKET=field-documents
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_PORT=6379

# KIMI API
KIMI_API_KEY=your_kimi_api_key_here
KIMI_BASE_URL=https://api.kimi.com/coding/
KIMI_MODEL=kimi-for-coding

# Application
APP_ENV=production
APP_PORT=8080
LOG_LEVEL=INFO
EOF
```

#### 3.3 配置企业微信（可选，后续配置）

```bash
# 在.env文件末尾添加
cat >> .env << EOF

# 企业微信配置
WECOM_CORP_ID=your_corp_id
WECOM_AGENT_ID=your_agent_id
WECOM_SECRET=your_secret
WECOM_TOKEN=your_token
WECOM_ENCODING_AES_KEY=your_aes_key
WECOM_CALLBACK_URL=https://your-domain.com/webhook/wecom
EOF
```

### 4. 启动服务

#### 4.1 首次启动

```bash
# 启动所有服务
./scripts/start.sh

# 查看启动日志
docker-compose logs -f
```

#### 4.2 初始化数据

```bash
# 等待PostgreSQL就绪
sleep 10

# 验证数据库连接
docker exec -it field-postgres psql -U field_user -d field_agent -c "SELECT version();"

# 查看表结构
docker exec -it field-postgres psql -U field_user -d field_agent -c "\dt"
```

#### 4.3 初始化MinIO

```bash
# 等待MinIO就绪
sleep 10

# 运行初始化脚本
./scripts/init-minio.sh

# 验证bucket创建
mc alias set local http://localhost:9000 minioadmin $MINIO_PASSWORD
mc ls local
```

### 5. 验证部署

#### 5.1 运行验证脚本

```bash
./scripts/verify-env.sh
```

#### 5.2 手动验证

```bash
# 检查容器状态
docker-compose ps

# 检查日志
docker-compose logs --tail=100

# 测试数据库连接
docker exec field-postgres pg_isready -U field_user

# 测试Redis连接
docker exec field-redis redis-cli -a $REDIS_PASSWORD ping

# 测试MinIO
curl http://localhost:9000/minio/health/live
```

---

## 🔒 安全配置

### 1. 防火墙配置

```bash
# Ubuntu/Debian (ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
# 生产环境不要开放以下端口到公网
# sudo ufw allow 5432/tcp  # PostgreSQL（仅内网）
# sudo ufw allow 9000/tcp  # MinIO API（仅内网）
# sudo ufw allow 9001/tcp  # MinIO Console（仅内网）
# sudo ufw allow 6379/tcp  # Redis（仅内网）
sudo ufw enable
```

### 2. SSL证书配置（推荐）

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 3. Nginx反向代理（推荐）

```nginx
# /etc/nginx/sites-available/field-info-agent
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webhook/wecom {
        proxy_pass http://localhost:8080/webhook/wecom;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. 定期备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/field-info-agent/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份PostgreSQL
docker exec field-postgres pg_dump -U field_user field_agent > $BACKUP_DIR/database.sql

# 备份MinIO
docker run --rm -v field-info-agent_minio_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/minio.tar.gz -C /data .

# 备份Redis
docker exec field-redis redis-cli -a $REDIS_PASSWORD SAVE
docker cp field-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# 压缩备份
tar czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
EOF

chmod +x backup.sh

# 添加定时任务（每天凌晨2点备份）
echo "0 2 * * * /opt/field-info-agent/backup.sh" | sudo crontab -
```

---

## 🔍 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :5432
sudo lsof -i :9000
sudo lsof -i :9001
sudo lsof -i :6379

# 停止占用进程或修改端口
```

#### 2. 数据库连接失败

```bash
# 检查PostgreSQL日志
docker-compose logs postgres

# 重置数据库（会丢失数据）
./scripts/stop.sh --volumes
./scripts/start.sh
```

#### 3. MinIO无法访问

```bash
# 检查MinIO状态
docker-compose logs minio

# 检查健康状态
curl http://localhost:9000/minio/health/live
```

#### 4. 内存不足

```bash
# 检查内存使用
free -h

# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 运维操作

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f minio
docker-compose logs -f redis

# 查看最近100行
docker-compose logs --tail=100
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart postgres

# 重新构建并启动
docker-compose up -d --build
```

### 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建
docker-compose down
docker-compose up -d --build

# 验证更新
./scripts/verify-env.sh
```

### 停止服务

```bash
# 正常停止
./scripts/stop.sh

# 停止并删除数据卷（⚠️ 谨慎使用）
./scripts/stop.sh --volumes

# 完全清理
./scripts/stop.sh --all
```

---

## ✅ 部署完成检查清单

- [ ] 服务器满足硬件要求
- [ ] Docker和Docker Compose已安装
- [ ] 代码已克隆到服务器
- [ ] `.env`文件已配置（强密码）
- [ ] 服务已成功启动
- [ ] 验证脚本运行通过
- [ ] 数据库连接正常
- [ ] MinIO bucket已创建
- [ ] Redis连接正常
- [ ] 防火墙已配置
- [ ] SSL证书已配置（推荐）
- [ ] Nginx反向代理已配置（推荐）
- [ ] 备份脚本已配置
- [ ] 日志已检查无错误

---

## 📞 获取帮助

- **项目文档**: [knowledge-base/field-info-agent/README.md](../knowledge-base/field-info-agent/README.md)
- **API文档**: [docs/tools/](../docs/)
- **故障排查**: 查看 [TIME-TRACKING.md](../agents/pm/TIME-TRACKING.md)
- **GitHub Issues**: https://github.com/Sonnet0524/community-power-assistant/issues

---

**手册版本**: 1.0.0  
**最后更新**: 2026-03-20  
**维护者**: PM Agent
