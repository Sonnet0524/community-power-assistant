#!/bin/bash
# =============================================================================
# Field Info Agent - 启动脚本
# =============================================================================
# 文件名: start.sh
# 作用: 启动 Field Info Agent 的所有服务
# 使用方法: ./scripts/start.sh [选项]
# 选项:
#   --build    强制重新构建镜像
#   --clean    清理并重新启动（删除数据卷）
#   --logs     启动并查看日志
#   --help     显示帮助信息
# 作者: Field Core Team
# 创建日期: 2026-03-19
# 版本: 1.0.0
# =============================================================================

set -e  # 遇到错误立即退出

# =============================================================================
# 颜色配置
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
# 变量配置
# =============================================================================

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 默认选项
BUILD=false
CLEAN=false
LOGS=false

# =============================================================================
# 帮助信息
# =============================================================================

show_help() {
    cat << EOF
Field Info Agent 启动脚本

使用方法:
    ./scripts/start.sh [选项]

选项:
    --build    强制重新构建 Docker 镜像
    --clean    清理数据并重新启动（会删除所有数据卷！）
    --logs     启动后查看服务日志
    --help     显示此帮助信息

示例:
    ./scripts/start.sh           # 正常启动
    ./scripts/start.sh --build   # 重新构建后启动
    ./scripts/start.sh --clean   # 清理数据后重新启动
    ./scripts/start.sh --logs    # 启动并查看日志

EOF
}

# =============================================================================
# 解析命令行参数
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                BUILD=true
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --logs)
                LOGS=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# 检查前置条件
# =============================================================================

check_prerequisites() {
    log_info "检查前置条件..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    test_passed "前置条件检查通过"
}

# =============================================================================
# 检查环境文件
# =============================================================================

check_env_file() {
    log_info "检查环境配置文件..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f .env ]; then
        log_warning ".env 文件不存在"
        
        if [ -f .env.example ]; then
            log_info "从 .env.example 创建 .env..."
            cp .env.example .env
            log_success ".env 文件已创建"
            log_warning "请编辑 .env 文件配置实际参数"
        else
            log_error ".env.example 模板不存在"
            exit 1
        fi
    else
        log_success ".env 文件已存在"
    fi
}

# =============================================================================
# 清理数据
# =============================================================================

clean_data() {
    log_warning "============================================"
    log_warning "警告: 这将删除所有数据卷！"
    log_warning "包括: PostgreSQL 数据、MinIO 数据、Redis 数据"
    log_warning "============================================"
    
    read -p "是否确认删除所有数据并重新启动? (y/N): " confirm
    
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        log_info "停止并清理服务..."
        docker-compose down -v 2>/dev/null || true
        
        log_info "清理完成"
    else
        log_info "已取消清理操作"
        exit 0
    fi
}

# =============================================================================
# 启动服务
# =============================================================================

start_services() {
    log_info "============================================"
    log_info "启动 Field Info Agent 服务"
    log_info "============================================"
    
    cd "$PROJECT_DIR"
    
    # 构建选项
    if [ "$BUILD" = true ]; then
        log_info "重新构建镜像..."
        docker-compose build --no-cache
    fi
    
    # 启动服务
    log_info "启动服务..."
    if [ "$BUILD" = true ]; then
        docker-compose up -d --build
    else
        docker-compose up -d
    fi
    
    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 5
    
    # 显示容器状态
    log_info "容器状态:"
    docker-compose ps
}

# =============================================================================
# 等待服务健康检查
# =============================================================================

wait_for_healthy() {
    log_info "等待服务健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local healthy_count
        healthy_count=$(docker-compose ps -q | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null | grep -c "healthy" || echo "0")
        
        if [ "$healthy_count" -ge 3 ]; then
            log_success "所有服务已就绪"
            return 0
        fi
        
        log_info "等待中... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_warning "服务健康检查超时，但服务可能仍在启动中"
    return 1
}

# =============================================================================
# 显示服务信息
# =============================================================================

show_service_info() {
    log_info "============================================"
    log_success "Field Info Agent 启动完成！"
    log_info "============================================"
    echo ""
    echo "📊 PostgreSQL:"
    echo "   地址: localhost:5432"
    echo "   数据库: field_agent"
    echo "   用户: field_user"
    echo ""
    echo "📦 MinIO:"
    echo "   API: http://localhost:9000"
    echo "   控制台: http://localhost:9001"
    echo "   用户名: minioadmin"
    echo "   密码: minioadmin123"
    echo ""
    echo "🔄 Redis:"
    echo "   地址: localhost:6379"
    echo ""
    echo "📝 常用命令:"
    echo "   查看日志: docker-compose logs -f"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
    echo "   验证环境: ./scripts/verify-env.sh"
    echo "============================================"
}

# =============================================================================
# 查看日志
# =============================================================================

show_logs() {
    log_info "显示服务日志..."
    docker-compose logs -f
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║      Field Info Agent 启动工具           ║"
    echo "║         Environment Startup              ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 检查前置条件
    check_prerequisites
    
    # 检查环境文件
    check_env_file
    
    # 清理数据（如果指定了 --clean）
    if [ "$CLEAN" = true ]; then
        clean_data
    fi
    
    # 启动服务
    start_services
    
    # 等待服务就绪
    wait_for_healthy
    
    # 显示服务信息
    show_service_info
    
    # 查看日志（如果指定了 --logs）
    if [ "$LOGS" = true ]; then
        show_logs
    fi
}

# =============================================================================
# 执行主函数
# =============================================================================

main "$@"
