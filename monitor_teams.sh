#!/bin/bash

# 监控脚本 - Field Core Team 和 Field Integration Team
# 持续5分钟，每30秒检查一次

LOG_FILE="/tmp/monitor_$(date +%Y%m%d_%H%M%S).log"
REPORT_COUNT=0
CHECK_COUNT=0
MAX_CHECKS=10
SLEEP_INTERVAL=30

# 初始状态
INIT_PY_COUNT=28
INIT_CORE_LOG=285
INIT_INTEGRATION_LOG=447
INIT_TASK002_LOG=452

echo "========================================" | tee -a "$LOG_FILE"
echo "开始监控 - $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "初始状态: Python文件=$INIT_PY_COUNT" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 检查函数
check_process() {
    local pid=$1
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "运行中"
        return 0
    else
        echo "已结束"
        return 1
    fi
}

check_logs() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        wc -l < "$log_file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# 监控循环
while [ $CHECK_COUNT -lt $MAX_CHECKS ]; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查进程
    CORE_STATUS=$(check_process 78728)
    INTEGRATION_STATUS=$(check_process 78857)
    
    # 检查Python文件数量
    CURRENT_PY_COUNT=$(find . -name "*.py" -type f 2>/dev/null | wc -l)
    
    # 检查日志行数
    CORE_LOG_LINES=$(check_logs "logs/field-core.log")
    INTEGRATION_LOG_LINES=$(check_logs "logs/field-integration.log")
    TASK002_LOG_LINES=$(check_logs "logs/field-core-task002.log")
    
    # 检查reports目录
    REPORT_002_EXISTS=$(ls reports/REPORT-002* 2>/dev/null | head -1)
    REPORT_003_EXISTS=$(ls reports/REPORT-003* 2>/dev/null | head -1)
    
    # 输出状态
    echo "[$CURRENT_TIME] 状态汇报 #$CHECK_COUNT" | tee -a "$LOG_FILE"
    echo "- Field Core: [$CORE_STATUS] [进行中] [当前文件数:$CURRENT_PY_COUNT] [日志行数:$CORE_LOG_LINES]" | tee -a "$LOG_FILE"
    echo "- Field Integration: [$INTEGRATION_STATUS] [进行中] [当前文件数:$CURRENT_PY_COUNT] [日志行数:$INTEGRATION_LOG_LINES]" | tee -a "$LOG_FILE"
    
    # 检查警报条件
    ALERTS=""
    
    if [ "$CORE_STATUS" = "已结束" ] || [ "$INTEGRATION_STATUS" = "已结束" ]; then
        ALERTS="${ALERTS}⚠️ 警告: 有进程已结束! "
    fi
    
    if [ -n "$REPORT_002_EXISTS" ] && [ ! -f "/tmp/report_002_notified" ]; then
        ALERTS="${ALERTS}📄 新报告: REPORT-002 已生成! "
        touch /tmp/report_002_notified
        REPORT_COUNT=$((REPORT_COUNT + 1))
    fi
    
    if [ -n "$REPORT_003_EXISTS" ] && [ ! -f "/tmp/report_003_notified" ]; then
        ALERTS="${ALERTS}📄 新报告: REPORT-003 已生成! "
        touch /tmp/report_003_notified
        REPORT_COUNT=$((REPORT_COUNT + 1))
    fi
    
    if [ "$CURRENT_PY_COUNT" -gt 15 ]; then
        ALERTS="${ALERTS}📈 Python文件数量超过15个 ($CURRENT_PY_COUNT)! "
    fi
    
    if [ "$CORE_LOG_LINES" -gt 500 ] || [ "$INTEGRATION_LOG_LINES" -gt 500 ] || [ "$TASK002_LOG_LINES" -gt 500 ]; then
        ALERTS="${ALERTS}📝 某日志文件超过500行! "
    fi
    
    if [ -n "$ALERTS" ]; then
        echo "  $ALERTS" | tee -a "$LOG_FILE"
    fi
    
    echo "" | tee -a "$LOG_FILE"
    
    # 检查是否所有进程都已结束
    if [ "$CORE_STATUS" = "已结束" ] && [ "$INTEGRATION_STATUS" = "已结束" ]; then
        echo "所有进程已结束，提前终止监控" | tee -a "$LOG_FILE"
        break
    fi
    
    # 等待下一次检查
    if [ $CHECK_COUNT -lt $MAX_CHECKS ]; then
        sleep $SLEEP_INTERVAL
    fi
done

# 总结报告
echo "========================================" | tee -a "$LOG_FILE"
echo "监控结束 - $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📊 总结报告:" | tee -a "$LOG_FILE"
echo "- 总检查次数: $CHECK_COUNT" | tee -a "$LOG_FILE"
echo "- Field Core 进程状态: $CORE_STATUS" | tee -a "$LOG_FILE"
echo "- Field Integration 进程状态: $INTEGRATION_STATUS" | tee -a "$LOG_FILE"
echo "- Python文件变化: $INIT_PY_COUNT → $CURRENT_PY_COUNT" | tee -a "$LOG_FILE"
echo "- Field Core 日志: $INIT_CORE_LOG → $CORE_LOG_LINES 行" | tee -a "$LOG_FILE"
echo "- Field Integration 日志: $INIT_INTEGRATION_LOG → $INTEGRATION_LOG_LINES 行" | tee -a "$LOG_FILE"
echo "- 新报告文件数: $REPORT_COUNT" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "日志已保存到: $LOG_FILE" | tee -a "$LOG_FILE"

# 清理临时文件
rm -f /tmp/report_002_notified /tmp/report_003_notified 2>/dev/null
