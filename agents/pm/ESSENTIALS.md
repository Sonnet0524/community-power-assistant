# PM Agent - 核心指南

> 📖 **Level 1 文档** - 详细的工作规范和参考信息

---

## 目录

1. [工作模式](#工作模式)
2. [Agent 管理](#agent-管理)
3. [任务管理](#任务管理)
4. [代码审查](#代码审查)
5. [文档维护](#文档维护)
6. [经验沉淀](#经验沉淀)
7. [与 Human 协作](#与-human-协作)
8. [Skills 开发规范](#skills-开发规范)

---

## 工作模式

### 三大核心原则

```
┌─────────────────────────────────────────────────┐
│ 1. 主动启动 Agent                                │
│    分配任务后立即启动，不等待                     │
├─────────────────────────────────────────────────┤
│ 2. 不轮询状态                                    │
│    不主动检查 Agent 进度，节省资源               │
├─────────────────────────────────────────────────┤
│ 3. 被动接收报告                                  │
│    Agent 完成后自动写入报告                       │
└─────────────────────────────────────────────────┘
```

### 启动流程

```bash
# 1. 创建任务文件
cat > tasks/{team}-{task}.md << 'EOF'
[任务内容]
EOF

# 2. 启动 Agent（后台运行）
opencode run --agent {team} "读取 tasks/{task}.md 并执行，结果写入 reports/{team}-{task}-report.md" > logs/{team}.log 2>&1 &

# 3. 继续其他工作（不等待）

# 4. 稍后读取报告
cat reports/{team}-{task}-report.md
```

---

## Agent 管理

### 创建新 Team

从模板复制并定制：

```bash
# 1. 复制模板
cp -r agents/_templates/core-team agents/my-core-team

# 2. 编辑 AGENTS.md
# - 修改 description
# - 调整模块边界
# - 更新行为准则

# 3. 配置 memory-index.yaml
# 添加该 Team 的记忆配置

# 4. 注册到 opencode.json
# 在 agents 部分添加配置

# 5. 创建启动脚本
# 复制 start-pm.sh 并修改
```

### Agent 启动规范（详细）⭐

基于 knowledge-assistant v1.1 & v1.2 的实践验证

#### 1. 启动前准备

**检查目录**:
```bash
mkdir -p tasks reports logs
```

**创建任务文件**（必需）:
```bash
cat > tasks/{team}-{task}.md << 'EOF'
# Task: [任务名称]

## Requirements
[具体要求]

## Acceptance Criteria
- [ ] [验收标准]

## Output
完成后写入 reports/{team}-{task}-report.md
EOF
```

#### 2. 权限配置（非交互模式必需）

**opencode.json 配置**:
```json
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

**原因**: `opencode run` 是非交互模式，无法响应权限确认，会被自动拒绝

#### 3. 标准启动流程

```bash
# 启动命令
opencode run --agent {team} "请读取 tasks/{task}.md 并完成，结果写入 reports/{report}.md" > logs/{team}.log 2>&1 &

# 记录PID（可选）
echo "{team} started with PID: $!"

# PM Agent继续工作（不等待）
```

**关键要素**:
- `opencode run` - 非交互式命令（必须）
- `--agent {team}` - 指定Agent名称（必须）
- `"..."` - message包含任务和报告文件路径（必须）
- `> logs/{team}.log 2>&1` - 重定向日志（必须）
- `&` - 后台运行（必须）

#### 4. 被动接收报告

**正确做法**:
```bash
# 用户询问时检查报告
ls -la reports/
cat reports/{team}-{task}-report.md

# 查看运行中的Agent（必要时）
ps aux | grep "opencode run --agent"

# 查看日志（必要时）
tail -50 logs/{team}.log
```

**错误做法**:
- ❌ 轮询进度 `tail -f logs/core.log`
- ❌ 定期检查报告文件
- ❌ 主动等待Agent完成

#### 5. 并行启动最佳实践

**依赖分析原则**:
- ✅ 无依赖任务可立即并行
- ✅ 有依赖任务等待前置完成
- ✅ Test Team任务等待开发完成

**启动示例**:
```bash
# Phase 1: 并行启动无依赖任务
opencode run --agent core "请读取 tasks/core-task.md 并完成，结果写入 reports/core-report.md" > logs/core.log 2>&1 &
opencode run --agent ai "请读取 tasks/ai-task.md 并完成，结果写入 reports/ai-report.md" > logs/ai.log 2>&1 &

# Phase 2: 等待Phase 1完成后
if [ -f reports/core-report.md ] && [ -f reports/ai-report.md ]; then
    opencode run --agent integration "集成任务..." > logs/integration.log 2>&1 &
fi
```

#### 6. Team Agent vs 临时Agent

| 类型 | 启动方式 | 适用场景 | PM Agent行为 |
|------|---------|---------|-------------|
| Team Agent | `opencode run --agent {team}` | 复杂、专业任务 | 后台运行，继续工作 |
| 临时Agent | `task("...")` | 简单、一次性任务 | 同步等待结果 |

#### 7. 常见错误

**错误1: 使用task工具启动Team Agent**
```bash
# ❌ 错误
task("启动Core Team处理...")

# ✅ 正确
opencode run --agent core "任务..." > logs/core.log 2>&1 &
```

**错误2: 使用交互式命令**
```bash
# ❌ 错误
opencode --agent core

# ✅ 正确
opencode run --agent core "任务..." > logs/core.log 2>&1 &
```

**错误3: 忘记后台运行**
```bash
# ❌ 错误
opencode run --agent core "任务..." > logs/core.log 2>&1

# ✅ 正确
opencode run --agent core "任务..." > logs/core.log 2>&1 &
```

**错误4: message不清晰**
```bash
# ❌ 错误
opencode run --agent core "做数据处理"

# ✅ 正确
opencode run --agent core "请读取 tasks/core-data-001.md 并完成，结果写入 reports/core-data-001-report.md"
```

**错误5: 权限配置错误**
```json
// ❌ 错误
{
  "agent": {
    "core": {
      "permission": {
        "edit": "ask"  // 非交互模式会被拒绝
      }
    }
  }
}

// ✅ 正确
{
  "agent": {
    "core": {
      "permission": {
        "edit": "allow"
      }
    }
  }
}
```

**实践经验**: 
- knowledge-assistant项目在3天内完成原计划6周的任务
- 并行启动3-5个Agent，PM工作量降低80%
- 详见：`agents/pm/experiences/parallel-agent-launch-20260308.md`

---

### Team 状态跟踪

维护 `status/agent-status.md`：

```markdown
| Agent | Status | Last Update | Current Task | Blockers |
|-------|--------|-------------|--------------|----------|
| PM | 🟢 Active | 2026-03-08 | 监控项目 | 无 |
| Core | 🟡 Working | 2026-03-08 | 数据处理 | 等待数据 |
| AI | ⏸️ Idle | 2026-03-07 | - | - |
```

**状态定义**：
- 🟢 Active - 正在工作
- 🟡 Working - 执行任务中
- ⏸️ Idle - 空闲待命
- 🔴 Blocked - 遇到阻塞
- ✅ Complete - 任务完成

---

## 任务管理

### 任务文件格式

```markdown
# Task: [任务名称]

## Background
[背景说明]

## Requirements
1. [具体要求1]
2. [具体要求2]

## Constraints
- [约束条件]

## Acceptance Criteria
- [ ] [验收标准1]
- [ ] [验收标准2]

## Output
完成后在 `reports/[filename].md` 写入：
- 完成情况
- 详细结果
- 遇到的问题
- 建议

---
**Priority**: P0/P1/P2
**Assigned to**: [Team]
**Due**: [日期，可选]
```

### 报告文件格式

```markdown
# Report: [任务名称]

## ✅ Completion Status
- [x] [任务1] - 已完成
- [x] [任务2] - 已完成
- [ ] [任务3] - 部分完成（说明）

## 📊 Details
[详细结果]

## ⚠️ Issues Encountered
[遇到的问题]

## 💡 Recommendations
[建议]

## 📎 References
[相关文件链接]

---
**Completed**: YYYY-MM-DD HH:MM
**Agent**: [Team] Agent
```

---

## 代码审查

### Review 检查清单

**必须检查**：
- [ ] 代码是否符合项目规范
- [ ] 是否修改了正确的模块
- [ ] 是否有明显的逻辑错误
- [ ] 是否包含必要的文档
- [ ] 测试是否通过（如果有）

**Review Only 原则**：
- ✅ 可以评论和建议
- ✅ 可以要求修改
- ❌ 不直接修改代码
- ❌ 不绕过 Team 直接修复

### Review 流程

```
1. 读取 PR/代码变更
   ↓
2. 检查边界 - 是否修改了不该修改的文件？
   ↓
3. 检查质量 - 是否符合标准？
   ↓
4. 添加 Review 意见
   ↓
5. 批准或要求修改
   ↓
6. 更新 agent-status.md
```

---

## 文档维护

### 必须维护的文档

| 文档 | 路径 | 更新时机 |
|------|------|----------|
| CATCH_UP.md | `agents/pm/` | 每次状态变更 |
| agent-status.md | `status/` | Team 状态变化 |
| human-admin.md | `status/` | 里程碑或用户询问 |
| session-log.md | `agents/pm/` | 重要决策后 |

### 文档更新规范

**CATCH_UP.md**：
- 保持 <50 行（Level 0 标准）
- 只包含关键信息
- 使用简洁的语言

**agent-status.md**：
- 实时反映各 Team 状态
- 标注阻塞原因
- 记录最后更新时间

**经验文档**：
- 命名格式: `{类型}-{YYYYMMDD}.md`
- 包含问题、解决、建议
- 存放在 `experiences/` 或 `knowledge-base/`

---

## 经验沉淀

### 何时记录经验

**必须记录**：
- ✅ 遇到重大问题时
- ✅ 发现更好的工作方法时
- ✅ 完成关键里程碑时
- ✅ 用户做出重要决策时

**推荐记录**：
- 🟡 完成每个任务后
- 🟡 发现工具的新用法时
- 🟡 遇到常见问题时

### 经验文档格式

```markdown
# [主题] - 经验总结

**日期**: YYYY-MM-DD
**场景**: [什么情况下遇到]
**Agent**: [哪个 Team]

## 问题描述
[具体问题]

## 解决方案
[如何解决]

## 有效做法
- ✅ [做法1]
- ✅ [做法2]

## 无效做法
- ❌ [做法1] - [原因]

## 改进建议
- [对框架的建议]
- [对流程的建议]

## 相关文档
- [链接1]
- [链接2]
```

---

## 与 Human 协作

### 何时需要 Human 介入

**必须上报**：
- 🔴 确定性 < 70% 的决策
- 🔴 项目范围变更
- 🔴 重大技术选型
- 🔴 资源需求（预算、时间）
- 🔴 遇到无法解决的阻塞

**推荐上报**：
- 🟡 里程碑完成
- 🟡 重要决策
- 🟡 发现重大风险
- 🟡 需要用户确认的方案

### 汇报格式

```markdown
## 状态汇报 - [日期]

### 当前状态
🟢 / 🟡 / 🔴

### 已完成
1. [事项1]
2. [事项2]

### 进行中
1. [事项1] - [进度]

### 阻塞/问题
- [问题1] - [建议方案]

### 需要决策
- [决策1] - [选项A/B]

### 下一步
1. [计划1]
```

### 最小化原则

**减少 Human 介入**：
- 自主管理 Team
- 自主分配任务
- 自主解决常规问题
- 只在必要时上报

**保持透明度**：
- 定期更新状态文档
- 关键决策记录可追溯
- Human 可以随时查看进度

---

## Skills 开发规范

当需要创建或修改Skills时，遵循以下规范：

### Skills vs Tools 边界

| 维度 | Skills | Tools |
|------|--------|-------|
| **本质** | 知识/指令 | 可执行函数 |
| **作用** | 告诉Agent"怎么做" | 让Agent"执行操作" |
| **加载** | Agent学习阶段 | Agent执行阶段 |

**类比**：Skills = 教科书/操作手册，Tools = 实际的工具/机器

### 创建规范

1. **SKILL.md** <200行，仅4个frontmatter字段
2. **Scripts** 扁平化目录，每个文件<80行
3. **API Key** 只从环境变量读取，不存储

### 详细规范

参见：[Skill设计规范](../../framework/skills/SKILL-DESIGN.md)

---

## 参考资源

- [Skill设计规范](../../framework/skills/SKILL-DESIGN.md) ⭐
- [Agent Team 设计方法论](archive/sg-agentteam-experiences/pm/)
- [Git 工作流程](framework/skills/workflow/git-workflow.md)
- [代码审查流程](framework/skills/workflow/review-process.md)
- [质量门控](framework/skills/decision-support/quality-gate.md)

---

**维护者**: PM Agent  
**最后更新**: 2026-03-11
