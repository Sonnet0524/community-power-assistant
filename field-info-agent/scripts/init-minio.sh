#!/bin/sh
# =============================================================================
# Field Info Agent - MinIO 初始化脚本
# =============================================================================
# 文件名: init-minio.sh
# 作用: 初始化 MinIO 服务，创建 bucket 和设置权限
# 执行时机: Docker Compose 启动时自动执行
# 依赖: MinIO 服务已启动且健康
# 作者: Field Core Team
# 创建日期: 2026-03-19
# 版本: 1.0.0
# =============================================================================

set -e  # 遇到错误立即退出

# =============================================================================
# 配置变量
# =============================================================================

# MinIO 服务地址（Docker 网络内部）
MINIO_ENDPOINT="http://field-minio:9000"

# 管理员凭据（从环境变量获取，默认值为开发环境配置）
MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin123}"

# 默认 Bucket 名称
MINIO_BUCKET="${MINIO_BUCKET:-field-documents}"

# 重试配置
MAX_RETRIES=30
RETRY_INTERVAL=2

# =============================================================================
# 日志函数
# =============================================================================

log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# =============================================================================
# 等待 MinIO 就绪
# =============================================================================

wait_for_minio() {
    log_info "等待 MinIO 服务就绪..."
    
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        # 检查 MinIO 健康端点
        if curl -sf "${MINIO_ENDPOINT}/minio/health/live" > /dev/null 2>&1; then
            log_success "MinIO 服务已就绪"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log_info "等待中... ($retry_count/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    log_error "MinIO 服务未能在预期时间内就绪"
    return 1
}

# =============================================================================
# 配置 MinIO Client (mc)
# =============================================================================

configure_mc() {
    log_info "配置 MinIO Client..."
    
    # 设置 MinIO 别名
    mc alias set local \
        "$MINIO_ENDPOINT" \
        "$MINIO_ROOT_USER" \
        "$MINIO_ROOT_PASSWORD" \
        --api s3v4
    
    log_success "MinIO Client 配置完成"
}

# =============================================================================
# 创建 Bucket
# =============================================================================

create_bucket() {
    local bucket_name="$1"
    
    log_info "检查 Bucket: $bucket_name"
    
    # 检查 bucket 是否已存在
    if mc ls local/"$bucket_name" > /dev/null 2>&1; then
        log_info "Bucket '$bucket_name' 已存在，跳过创建"
    else
        log_info "创建 Bucket: $bucket_name"
        mc mb local/"$bucket_name"
        log_success "Bucket '$bucket_name' 创建成功"
    fi
    
    # 设置 bucket 版本控制（可选）
    log_info "启用 Bucket 版本控制..."
    mc version enable local/"$bucket_name" || log_info "版本控制已启用或不可用"
}

# =============================================================================
# 设置 Bucket 策略
# =============================================================================

set_bucket_policy() {
    local bucket_name="$1"
    
    log_info "设置 Bucket 策略..."
    
    # 创建匿名只读策略（允许公开访问）
    # 注意：生产环境应根据实际需求调整策略
    cat > /tmp/bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::%s/*"]
        }
    ]
}
EOF
    
    # 替换 bucket 名称
    sed -i "s/%s/$bucket_name/g" /tmp/bucket-policy.json
    
    # 应用策略
    mc policy set-json /tmp/bucket-policy.json local/"$bucket_name" || {
        log_info "使用替代方法设置策略..."
        mc anonymous set download local/"$bucket_name"
    }
    
    log_success "Bucket 策略设置完成"
}

# =============================================================================
# 创建目录结构
# =============================================================================

create_directory_structure() {
    local bucket_name="$1"
    
    log_info "创建目录结构..."
    
    # 定义目录结构
    directories=(
        "raw-photos/"              # 原始照片存储
        "raw-photos/$(date +%Y)/"  # 按年份分类
        "raw-photos/$(date +%Y/%m)/"
        "analysis-outputs/"         # 分析输出
        "analysis-outputs/$(date +%Y)/"
        "analysis-outputs/$(date +%Y/%m)/"
        "generated-docs/"           # 生成的文档
        "generated-docs/reports/"
        "generated-docs/forms/"
        "generated-docs/guides/"
        "temp/"                     # 临时文件
        "backups/"                  # 备份文件
    )
    
    # 创建每个目录
    for dir in "${directories[@]}"; do
        log_info "创建目录: $dir"
        mc mb local/"$bucket_name/$dir" || log_info "目录 $dir 已存在"
    done
    
    log_success "目录结构创建完成"
}

# =============================================================================
# 创建示例文件
# =============================================================================

create_sample_files() {
    local bucket_name="$1"
    
    log_info "创建示例 README 文件..."
    
    # 创建目录说明文件
    echo "# Field Documents Storage

This bucket contains field operation documents and media files.

## Directory Structure

- raw-photos/: Original photos taken in the field
- analysis-outputs/: AI analysis results and outputs
- generated-docs/: Generated reports, forms, and guides
- temp/: Temporary files (auto-cleaned)
- backups/: System backups

## Created
$(date)

## Version
1.0.0
" > /tmp/README.md
    
    mc cp /tmp/README.md local/"$bucket_name"/README.md
    
    log_success "示例文件创建完成"
}

# =============================================================================
# 验证配置
# =============================================================================

verify_setup() {
    local bucket_name="$1"
    
    log_info "验证 MinIO 配置..."
    
    # 列出 bucket 内容
    log_info "Bucket 内容:"
    mc ls -r local/"$bucket_name" | head -20
    
    # 验证策略
    log_info "Bucket 策略:"
    mc anonymous get local/"$bucket_name"
    
    log_success "验证完成"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    log_info "============================================"
    log_info "MinIO 初始化脚本启动"
    log_info "============================================"
    log_info "MinIO 端点: $MINIO_ENDPOINT"
    log_info "Bucket 名称: $MINIO_BUCKET"
    log_info "============================================"
    
    # 步骤 1: 等待 MinIO 就绪
    wait_for_minio || exit 1
    
    # 步骤 2: 配置 mc
    configure_mc
    
    # 步骤 3: 创建 bucket
    create_bucket "$MINIO_BUCKET"
    
    # 步骤 4: 设置 bucket 策略
    set_bucket_policy "$MINIO_BUCKET"
    
    # 步骤 5: 创建目录结构
    create_directory_structure "$MINIO_BUCKET"
    
    # 步骤 6: 创建示例文件
    create_sample_files "$MINIO_BUCKET"
    
    # 步骤 7: 验证配置
    verify_setup "$MINIO_BUCKET"
    
    log_info "============================================"
    log_success "MinIO 初始化完成"
    log_info "============================================"
    log_info "访问信息:"
    log_info "  - API 地址: http://localhost:9000"
    log_info "  - 控制台: http://localhost:9001"
    log_info "  - Bucket: $MINIO_BUCKET"
    log_info "============================================"
    
    return 0
}

# =============================================================================
# 执行主函数
# =============================================================================

main "$@"
