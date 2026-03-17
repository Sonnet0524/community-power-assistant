# Agent 启动快速参考

> ⚡ 一页式快速参考卡片

---

## 📋 标准启动命令

```bash
opencode run --agent {team} "请读取 tasks/{task}.md 并完成，结果写入 reports/{report}.md" > logs/{team}.log 2>&1 &
```

---

## ✅ 必需步骤（5步）

### Step 1: 创建任务文件
```bash
mkdir -p tasks reports logs
cat > tasks/{team}-{task}.md << 'EOF'
# Task: [任务名称]
## Requirements
[具体要求]
## Output
完成后写入 reports/{team}-{task}-report.md
EOF
```

### Step 2: 配置权限
```json
// opencode.json
{
  "agent": {
    "{team}": {
      "permission": {
        "edit": "allow"  // 必须为allow
      }
    }
  }
}
```

### Step 3: 启动Agent
```bash
opencode run --agent {team} "请读取 tasks/{team}-{task}.md 并完成，结果写入 reports/{team}-{task}-report.md" > logs/{team}.log 2>&1 &
```

### Step 4: PM Agent继续工作
- ❌ 不轮询进度
- ✅ 继续其他任务

### Step 5: 被动接收报告
```bash
# 用户询问时检查
ls -la reports/
cat reports/{team}-{task}-report.md
```

---

## 🆚 Team Agent vs 临时Agent

| 类型 | 启动方式 | 适用场景 | PM Agent行为 |
|------|---------|---------|-------------|
| **Team Agent** | `opencode run --agent {team}` | 复杂、专业任务 | 后台运行，继续工作 |
| **临时Agent** | `task("...")` | 简单、一次性任务 | 同步等待结果 |

---

## ❌ 常见错误对照表

| 错误示例 | 正确示例 | 问题说明 |
|---------|---------|---------|
| `opencode --agent core` | `opencode run --agent core` | 交互式vs非交互式 |
| 忘记 `&` | 添加 `&` | 后台运行 |
| message不清晰 | 包含任务和报告文件路径 | Agent不知道做什么 |
| `task("启动Team")` | `opencode run --agent team` | task只用于临时Agent |
| `"edit": "ask"` | `"edit": "allow"` | 非交互模式权限 |

---

## 🚀 并行启动模板

```bash
# Phase 1: 并行启动无依赖任务
opencode run --agent core "请读取 tasks/core-task.md 并完成，结果写入 reports/core-report.md" > logs/core.log 2>&1 &
opencode run --agent ai "请读取 tasks/ai-task.md 并完成，结果写入 reports/ai-report.md" > logs/ai.log 2>&1 &
opencode run --agent test "请读取 tasks/test-task.md 并完成，结果写入 reports/test-report.md" > logs/test.log 2>&1 &

# Phase 2: 等待Phase 1完成后启动依赖任务
if [ -f reports/core-report.md ] && [ -f reports/ai-report.md ]; then
    opencode run --agent integration "集成任务..." > logs/integration.log 2>&1 &
fi
```

---

## 📊 依赖分析原则

```
✅ 无依赖任务 → 立即并行
✅ 有依赖任务 → 等待前置完成
✅ Test任务 → 等待开发完成
✅ Integration任务 → 等待各模块完成
```

---

## 🔍 检查和调试

### 检查Agent是否在运行
```bash
ps aux | grep "opencode run --agent"
```

### 查看Agent日志
```bash
tail -50 logs/{team}.log
```

### 检查报告生成
```bash
ls -la reports/
```

---

## 📈 实践效果数据

来自 knowledge-assistant v1.1 & v1.2 项目：

| 指标 | 传统方式 | 实践优化后 | 改进 |
|------|---------|-----------|------|
| 开发周期 | 6周 | 3天 | ↓93% |
| PM工作量 | 高 | 低 | ↓80% |
| 并行任务数 | 1 | 3-5 | ↑300% |
| 任务成功率 | 70% | 95% | ↑36% |

---

## 📚 详细文档

- **详细规范**: `agents/pm/ESSENTIALS.md` → "Agent启动规范"
- **工作流程**: `agents/pm/WORKFLOW.md`
- **实践经验**: `agents/pm/experiences/parallel-agent-launch-20260308.md`

---

## 🎯 核心原则

```
主动启动 + 后台运行 + 被动接收
```

1. ✅ **主动启动** - 分配任务后立即启动
2. ✅ **后台运行** - 使用 `&` 不阻塞PM
3. ✅ **被动接收** - 不轮询，等待报告

---

**快速参考**: 本文档  
**维护者**: PM Agent Framework  
**最后更新**: 2026-03-09  
**基于**: knowledge-assistant v1.1 & v1.2 实践经验
