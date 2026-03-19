#!/bin/bash
# =============================================================================
# Field Info Agent - 环境验证脚本
# =============================================================================
# 文件名: verify-env.sh
# 作用: 验证所有服务（PostgreSQL、MinIO、Redis）是否正常运行
# 使用方法: ./scripts/verify-env.sh
# 返回码: 0 成功，1 失败
# 作者: Field Core Team
# 创建日期: 2026-03-19
# 版本: 1.0.0
# =============================================================================

set -e  # 遇到错误立即退出

# =============================================================================
# 颜色配置（用于美化输出）
# =============================================================================

# 颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# 日志函数
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# =============================================================================
# 配置变量
# =============================================================================

# 服务配置（从环境变量读取，默认值为开发环境配置）
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-field_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-field_pass}"
POSTGRES_DB="${POSTGRES_DB:-field_agent}"

MINIO_HOST="${MINIO_HOST:-localhost}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin123}"
MINIO_BUCKET="${MINIO_BUCKET:-field-documents}"

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-redispass}"

# 测试结果统计
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# 测试函数
# =============================================================================

test_passed() {
    log_success "✓ $1"
    ((TESTS_PASSED++))
}

test_failed() {
    log_error "✗ $1"
    ((TESTS_FAILED++))
}

# =============================================================================
# 检查 Docker Compose 状态
# =============================================================================

check_docker_compose() {
    log_info "============================================"
    log_info "检查 Docker Compose 状态"
    log_info "============================================"
    
    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        test_failed "Docker 服务未运行"
        return 1
    fi
    test_passed "Docker 服务运行正常"
    
    # 检查容器状态
    local containers=("field-postgres" "field-minio" "field-redis")
    for container in "${containers[@]}"; do
        local status
        status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
        
        if [ "$status" == "running" ]; then
            test_passed "容器 $container 运行正常"
        elif [ "$status" == "not_found" ]; then
            test_failed "容器 $container 不存在"
        else
            test_failed "容器 $container 状态异常: $status"
        fi
    done
    
    # 检查健康状态
    log_info "检查容器健康状态..."
    docker-compose -f docker-compose.yml ps
    
    return 0
}

# =============================================================================
# 测试 PostgreSQL 连接
# =============================================================================

test_postgres() {
    log_info "============================================"
    log_info "测试 PostgreSQL 连接"
    log_info "============================================"
    log_info "主机: $POSTGRES_HOST:$POSTGRES_PORT"
    log_info "数据库: $POSTGRES_DB"
    log_info "用户: $POSTGRES_USER"
    log_info "============================================"
    
    # 检查 psql 命令是否存在
    if ! command -v psql &> /dev/null; then
        log_warning "psql 命令未找到，尝试使用 Docker 执行..."
        
        # 使用 Docker 容器执行测试
        if docker exec field-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" >/dev/null 2>&1; then
            test_passed "PostgreSQL 连接成功"
        else
            test_failed "PostgreSQL 连接失败"
            return 1
        fi
    else
        # 使用本地 psql 测试
        export PGPASSWORD="$POSTGRES_PASSWORD"
        if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" >/dev/null 2>&1; then
            test_passed "PostgreSQL 连接成功"
        else
            test_failed "PostgreSQL 连接失败"
            return 1
        fi
        unset PGPASSWORD
    fi
    
    # 测试数据库查询
    log_info "测试数据库查询..."
    if docker exec field-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM users;" >/dev/null 2>&1; then
        test_passed "数据库查询执行成功"
    else
        test_failed "数据库查询执行失败"
    fi
    
    # 列出数据库表
    log_info "数据库表列表:"
    docker exec field-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" 2>/dev/null || log_warning "无法获取表列表"
    
    return 0
}

# =============================================================================
# 测试 MinIO 连接
# =============================================================================

test_minio() {
    log_info "============================================"
    log_info "测试 MinIO 连接"
    log_info "============================================"
    log_info "API 地址: http://$MINIO_HOST:$MINIO_PORT"
    log_info "控制台: http://$MINIO_HOST:$MINIO_CONSOLE_PORT"
    log_info "Bucket: $MINIO_BUCKET"
    log_info "============================================"
    
    # 测试 API 端口
    if curl -sf "http://$MINIO_HOST:$MINIO_PORT/minio/health/live" >/dev/null 2>&1; then
        test_passed "MinIO API 服务正常"
    else
        test_failed "MinIO API 服务异常"
        return 1
    fi
    
    # 测试控制台端口
    if curl -sf "http://$MINIO_HOST:$MINIO_CONSOLE_PORT" >/dev/null 2>&1; then
        test_passed "MinIO 控制台可访问"
    else
        test_warning "MinIO 控制台可能不可访问（这是正常的，控制台需要浏览器访问）"
    fi
    
    # 测试 mc 命令
    if command -v mc &> /dev/null; then
        log_info "使用 mc 命令验证 MinIO..."
        
        # 配置别名
        mc alias set test-local "http://$MINIO_HOST:$MINIO_PORT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" --api s3v4 >/dev/null 2>&1
        
        # 列出 buckets
        if mc ls test-local >/dev/null 2>&1; then
            test_passed "MinIO 认证成功"
            log_info "Bucket 列表:"
            mc ls test-local 2>/dev/null || log_warning "无法列出 buckets"
            
            # 检查特定 bucket
            if mc ls "test-local/$MINIO_BUCKET" >/dev/null 2>&1; then
                test_passed "Bucket '$MINIO_BUCKET' 存在"
            else
                test_failed "Bucket '$MINIO_BUCKET' 不存在"
            fi
        else
            test_failed "MinIO 认证失败"
        fi
        
        # 删除测试别名
        mc alias remove test-local >/dev/null 2>&1 || true
    else
        log_warning "mc 命令未安装，跳过详细验证"
    fi
    
    return 0
}

# =============================================================================
# 测试 Redis 连接
# =============================================================================

test_redis() {
    log_info "============================================"
    log_info "测试 Redis 连接"
    log_info "============================================"
    log_info "主机: $REDIS_HOST:$REDIS_PORT"
    log_info "============================================"
    
    # 检查 redis-cli 命令
    if command -v redis-cli &> /dev/null; then
        # 使用本地 redis-cli 测试
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping | grep -q "PONG"; then
            test_passed "Redis 连接成功"
        else
            test_failed "Redis 连接失败"
            return 1
        fi
        
        # 测试写入和读取
        local test_key="test_key_$(date +%s)"
        local test_value="test_value"
        
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" set "$test_key" "$test_value" >/dev/null 2>&1; then
            test_passed "Redis 写入成功"
            
            local retrieved_value
            retrieved_value=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" get "$test_key" 2>/dev/null)
            if [ "$retrieved_value" == "$test_value" ]; then
                test_passed "Redis 读取成功"
            else
                test_failed "Redis 读取失败"
            fi
            
            # 清理测试数据
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" del "$test_key" >/dev/null 2>&1
        else
            test_failed "Redis 写入失败"
        fi
        
        # 检查 Redis 信息
        log_info "Redis 服务器信息:"
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" info server 2>/dev/null | head -5 || log_warning "无法获取 Redis 信息"
        
    else
        log_warning "redis-cli 命令未找到，尝试使用 Docker 执行..."
        
        # 使用 Docker 容器执行测试
        if docker exec field-redis redis-cli -a "$REDIS_PASSWORD" ping | grep -q "PONG" 2>/dev/null; then
            test_passed "Redis 连接成功（Docker 模式）"
        else
            test_failed "Redis 连接失败"
            return 1
        fi
    fi
    
    return 0
}

# =============================================================================
# 生成测试报告
# =============================================================================

generate_report() {
    log_info "============================================"
    log_info "测试报告"
    log_info "============================================"
    
    local total=$((TESTS_PASSED + TESTS_FAILED))
    
    echo ""
    echo "┌─────────────────────────────────────────┐"
    echo "│           Field Info Agent              │"
    echo "│         环境验证测试报告                │"
    echo "├─────────────────────────────────────────┤"
    echo "│ 测试时间: $(date '+%Y-%m-%d %H:%M:%S')              │"
    echo "│ 总测试数: $total                                  │"
    echo "│ 通过: $TESTS_Passed                                      │"
    echo "│ 失败: $TESTS_Failed                                      │"
    echo "│                                         │"
    if [ $TESTS_FAILED -eq 0 ]; then
        echo "│ 结果: ${GREEN}全部通过${NC}                          │"
    else
        echo "│ 结果: ${RED}存在失败${NC}                          │"
    fi
    echo "└─────────────────────────────────────────┘"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "所有测试通过！环境就绪。"
        return 0
    else
        log_error "存在失败的测试，请检查配置。"
        return 1
    fi
}

# =============================================================================
# 打印服务访问信息
# =============================================================================

print_access_info() {
    log_info "============================================"
    log_info "服务访问信息"
    log_info "============================================"
    echo ""
    echo "📊 PostgreSQL:"
    echo "   主机: localhost:$POSTGRES_PORT"
    echo "   数据库: $POSTGRES_DB"
    echo "   用户: $POSTGRES_USER"
    echo "   密码: $POSTGRES_PASSWORD"
    echo ""
    echo "📦 MinIO:"
    echo "   API: http://localhost:$MINIO_PORT"
    echo "   控制台: http://localhost:$MINIO_CONSOLE_PORT"
    echo "   用户名: $MINIO_ROOT_USER"
    echo "   密码: $MINIO_ROOT_PASSWORD"
    echo ""
    echo "🔄 Redis:"
    echo "   主机: localhost:$REDIS_PORT"
    echo "   密码: $REDIS_PASSWORD"
    echo ""
    echo "📁 MinIO Bucket: $MINIO_BUCKET"
    echo "============================================"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║      Field Info Agent 环境验证工具       ║"
    echo "║         Environment Verification         ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    
    # 切换到项目目录
    cd "$(dirname "$0")/.." || exit 1
    
    # 检查 .env 文件
    if [ -f .env ]; then
        log_info "加载环境变量 (.env)..."
        export $(grep -v '^#' .env | xargs)
    else
        log_warning ".env 文件不存在，使用默认配置"
    fi
    
    # 执行测试
    check_docker_compose
    test_postgres
    test_minio
    test_redis
    
    # 生成报告
    generate_report
    local result=$?
    
    # 打印访问信息
    if [ $result -eq 0 ]; then
        print_access_info
    fi
    
    return $result
}

# =============================================================================
# 执行主函数
# =============================================================================

main "$@"
