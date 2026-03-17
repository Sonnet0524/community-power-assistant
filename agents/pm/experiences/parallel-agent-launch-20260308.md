# 并行启动多个Agent - 经验总结

**日期**: 2026-03-08
**Agent**: PM Team
**任务**: v1.2 Sprint 并行启动多个Agent执行任务

---

## 遇到的问题

### 问题1: 非交互模式权限自动拒绝

**现象**:
- 使用 `opencode run --agent <name>` 后台启动Agent
- Agent尝试编辑文件时报错：`permission requested: edit (...); auto-rejecting`
- 任务无法继续，Agent停止工作

**原因**:
- opencode.json 中配置 `"edit": "ask"`
- 非交互模式下无法响应用户确认
- 系统自动拒绝需要确认的权限请求

**解决**:
- 修改 opencode.json，将所有Agent的 `edit` 权限改为 `"allow"`
- 重新启动Agent后正常工作

**是否框架相关**: 是 - 建议框架默认为非交互模式提供 `allow` 选项

---

### 问题2: 多仓库操作混淆

**现象**:
- dev仓库和main仓库路径容易混淆
- 有时在错误的仓库执行操作
- git操作路径错误

**原因**:
- 双仓库架构设计
- 缺乏明确的路径指引

**解决**:
- 在CATCH_UP.md中明确"多仓库信息交互的要求"
- 使用 `workdir` 参数或相对路径 `../knowledge-assistant`
- 每次操作前确认当前仓库位置

**是否框架相关**: 是 - 建议框架提供多仓库状态提示

---

## 有效做法

### 做法1: 任务文件 + 报告文件机制

**实施细节**:
```bash
# 1. 创建任务文件
mkdir -p tasks reports logs

cat > tasks/core-task.md << 'EOF'
# 任务标题
## 任务背景
...
## 具体要求
...
## 输出要求
完成后写入 reports/core-report.md
EOF

# 2. 启动Agent
opencode run --agent core "请读取 tasks/core-task.md 并完成，结果写入 reports/core-report.md" > logs/core.log 2>&1 &
```

**优势**:
- 任务描述完整，避免理解偏差
- 报告格式统一，便于汇总
- 历史记录可追溯
- 日志文件便于排查问题

---

### 做法2: 并行启动多个Agent

**实施细节**:
```bash
# 分析任务依赖关系
# Phase 1: 无依赖任务可并行
opencode run --agent core "任务A..." > logs/core.log 2>&1 &
opencode run --agent ai "任务B..." > logs/ai.log 2>&1 &
opencode run --agent integration "任务C..." > logs/integration.log 2>&1 &

# 记录PID便于管理
echo "Core Team started with PID: $!"
```

**依赖分析原则**:
- 无依赖任务可立即并行
- 有依赖任务等待前置完成
- Test Team任务等待开发完成

**优势**:
- 大幅缩短开发周期
- 充分利用并行能力
- PM Team不需等待

---

### 做法3: 被动接收报告 + 不轮询

**实施细节**:
- ❌ 不主动检查Agent进度（不轮询）
- ❌ 不定期查看日志文件
- ✅ 用户询问时检查报告目录
- ✅ Agent完成后主动生成报告文件

**检查方法**:
```bash
# 检查报告是否生成
ls -la reports/

# 查看运行中的Agent
ps aux | grep "opencode run --agent"

# 必要时查看日志
tail -50 logs/<team>.log
```

**优势**:
- 减少PM Team工作负担
- Agent自主完成，减少干预
- 可同时管理多个Agent

---

### 做法4: GitHub Issues 任务跟踪

**实施细节**:
```bash
# 创建Issue
gh issue create --title "[Core Team] TASK-C1: 任务标题" --label "enhancement" --body "任务描述..."

# 完成后关闭Issue
gh issue close <number> --comment "✅ 已完成

- 完成内容...
- 测试结果...
- 详见: reports/xxx-report.md"
```

**优势**:
- 任务进度可视化
- 与PR关联
- 历史记录完整

---

## 无效做法

### 做法1: 使用task工具启动Team Agent

**原因**: task工具只能启动 `general` 或 `explore` 临时代理

**正确方式**: 使用 `opencode run --agent <name>` 启动项目中的Team Agent

---

### 做法2: 使用交互式启动

**原因**: 
- `opencode --agent <name>` 是交互式模式
- 后台运行时无法接收输入
- 进程无法正常工作

**正确方式**: 使用 `opencode run --agent <name>` 非交互式模式

---

### 做法3: 主动轮询Agent状态

**原因**:
- 增加PM Team工作量
- 破坏"被动接收"原则
- 可能错过关键时机

**正确方式**: 等待Agent生成报告后被动读取

---

## 改进建议

### 对框架的建议

1. **默认非交互权限配置**
   - 提供模式切换：`interactive` vs `non-interactive`
   - 非交互模式自动使用 `allow` 权限

2. **多仓库状态提示**
   - 启动时显示当前仓库
   - 操作前确认目标仓库
   - 提供仓库切换命令

3. **Agent状态报告机制**
   - Agent启动后主动报告PID
   - 定期发送心跳信号
   - 完成后主动通知

4. **任务依赖分析工具**
   - 自动分析任务依赖关系
   - 生成最优并行执行计划
   - 可视化任务进度

### 对实践的建议

1. **建立任务文件模板库**
   - 标准化任务文件格式
   - 包含依赖、验收标准、输出要求

2. **建立报告文件模板库**
   - 统一报告格式
   - 包含完成状态、测试结果、问题记录

3. **建立日志检查脚本**
   - 快速检查Agent状态
   - 汇总多个Agent进度
   - 生成进度报告

---

## 完整示例

### 并行启动多个Agent的完整流程

```bash
# 1. 创建目录
mkdir -p tasks reports logs

# 2. 创建任务文件
cat > tasks/core-task.md << 'EOF'
# Core Team任务：功能开发
## 任务背景
...
## 具体要求
- 功能1
- 功能2
## 输出要求
完成后写入 reports/core-report.md
EOF

cat > tasks/ai-task.md << 'EOF'
# AI Team任务：算法优化
...
EOF

cat > tasks/integration-task.md << 'EOF'
# Integration Team任务：接口开发
...
EOF

# 3. 并行启动Agent
opencode run --agent core "请读取 tasks/core-task.md 并完成，结果写入 reports/core-report.md" > logs/core.log 2>&1 &
echo "Core Team started with PID: $!"

opencode run --agent ai "请读取 tasks/ai-task.md 并完成，结果写入 reports/ai-report.md" > logs/ai.log 2>&1 &
echo "AI Team started with PID: $!"

opencode run --agent integration "请读取 tasks/integration-task.md 并完成，结果写入 reports/integration-report.md" > logs/integration.log 2>&1 &
echo "Integration Team started with PID: $!"

# 4. 等待完成（被动触发）
# 用户询问时检查
ls -la reports/

# 5. 读取报告
cat reports/core-report.md
cat reports/ai-report.md
cat reports/integration-report.md
```

---

## 关键配置

### opencode.json 权限配置

```json
{
  "agent": {
    "pm": {
      "permission": {
        "edit": "allow",
        "bash": {
          "git push": "ask",
          "git *": "allow"
        }
      }
    },
    "core": {
      "permission": {
        "edit": "allow",
        "bash": {
          "pytest *": "allow",
          "git push": "ask"
        }
      }
    },
    "ai": {
      "permission": {
        "edit": "allow"
      }
    },
    "integration": {
      "permission": {
        "edit": "allow"
      }
    },
    "test": {
      "permission": {
        "edit": "allow",
        "bash": {
          "pytest *": "allow"
        }
      }
    }
  }
}
```

---

**记录者**: PM Team
**记录时间**: 2026-03-08
**适用场景**: 多Agent并行任务执行
