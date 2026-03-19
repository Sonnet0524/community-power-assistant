#!/bin/bash
# =============================================================================
# Field Info Agent - 停止脚本
# =============================================================================
# 文件名: stop.sh
# 作用: 停止 Field Info Agent 的所有服务
# 使用方法: ./scripts/stop.sh [选项]
# 选项:
#   --volumes  同时删除数据卷（清理所有数据）
#   --all      停止并删除所有相关容器和网络
#   --help     显示帮助信息
# 作者: Field Core Team
# 创建日期: 2026-03-19
# 版本: 1.0.0
# =============================================================================

set -e

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

REMOVE_VOLUMES=false
REMOVE_ALL=false

# =============================================================================
# 帮助信息
# =============================================================================

show_help() {
    cat << EOF
Field Info Agent 停止脚本

使用方法:
    ./scripts/stop.sh [选项]

选项:
    --volumes  同时删除数据卷（会丢失所有数据！）
    --all      停止并删除所有相关容器、网络和卷
    --help     显示此帮助信息

示例:
    ./scripts/stop.sh           # 正常停止
    ./scripts/stop.sh --volumes # 停止并删除数据卷
    ./scripts/stop.sh --all     # 完全清理

EOF
}

# =============================================================================
# 解析命令行参数
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --volumes)
                REMOVE_VOLUMES=true
                shift
                ;;
            --all)
                REMOVE_ALL=true
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
# 停止服务
# =============================================================================

stop_services() {
    log_info "============================================"
    log_info "停止 Field Info Agent 服务"
    log_info "============================================"
    
    cd "$PROJECT_DIR"
    
    # 检查是否有运行中的容器
    local running_containers
    running_containers=$(docker-compose ps -q 2>/dev/null | wc -l)
    
    if [ "$running_containers" -eq 0 ]; then
        log_warning "没有运行中的服务"
        return 0
    fi
    
    # 显示当前运行的容器
    log_info "当前运行的容器:"
    docker-compose ps
    
    # 停止服务
    log_info "正在停止服务..."
    
    if [ "$REMOVE_ALL" = true ]; then
        log_warning "将删除所有容器、网络和卷..."
        docker-compose down -v --remove-orphans
    elif [ "$REMOVE_VOLUMES" = true ]; then
        log_warning "将删除数据卷..."
        docker-compose down -v
    else
        docker-compose down
    fi
    
    log_success "服务已停止"
}

# =============================================================================
# 清理 dangling 资源
# =============================================================================

cleanup_dangling() {
    if [ "$REMOVE_ALL" = true ]; then
        log_info "清理 dangling 资源..."
        
        # 删除 dangling 卷
        local dangling_volumes
        dangling_volumes=$(docker volume ls -q -f dangling=true 2>/dev/null | wc -l)
        if [ "$dangling_volumes" -gt 0 ]; then
            docker volume prune -f >/dev/null 2>&1 || true
            log_info "已清理 dangling 卷"
        fi
        
        # 删除 dangling 镜像
        local dangling_images
        dangling_images=$(docker images -q -f dangling=true 2>/dev/null | wc -l)
        if [ "$dangling_images" -gt 0 ]; then
            docker image prune -f >/dev/null 2>&1 || true
            log_info "已清理 dangling 镜像"
        fi
    fi
}

# =============================================================================
# 显示停止后信息
# =============================================================================

show_stop_info() {
    log_info "============================================"
    log_success "Field Info Agent 已停止"
    log_info "============================================"
    echo ""
    
    if [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_ALL" = true ]; then
        echo "🗑️  数据卷已删除"
        echo "   注意: 所有数据（包括数据库）已丢失"
        echo ""
    fi
    
    echo "📝 如需重新启动:"
    echo "   ./scripts/start.sh"
    echo ""
    echo "📝 如需完全重置:"
    echo "   ./scripts/start.sh --clean"
    echo "============================================"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║      Field Info Agent 停止工具           ║"
    echo "║         Environment Shutdown             ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 停止服务
    stop_services
    
    # 清理资源
    cleanup_dangling
    
    # 显示信息
    show_stop_info
}

# =============================================================================
# 执行主函数
# =============================================================================

main "$@"
