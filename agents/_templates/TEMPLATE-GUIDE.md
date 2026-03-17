# Agent 模板使用指南

> 📖 如何使用和定制 Agent 模板

---

## 模板列表

本目录包含以下 Agent 模板：

| 模板 | 职责 | 适用场景 |
|------|------|----------|
| `core-team/` | 数据处理、工具开发 | 需要数据处理和基础工具的项目 |
| `ai-team/` | 向量嵌入、语义搜索、ML | AI/ML 相关项目 |
| `test-team/` | 测试、质量保证 | 需要测试的项目 |
| `integration-team/` | 系统集成、连接器 | 需要与外部系统集成的项目 |
| `research-team/` | 理论研究、框架设计 | 研究型项目 |

---

## 使用流程

### 步骤 1: 选择合适的模板

根据项目需求，选择合适的 Team 模板。

**决策指南**:
- 需要数据处理？→ Core Team
- 需要 AI/ML？→ AI Team
- 需要测试？→ Test Team
- 需要集成？→ Integration Team
- 需要研究？→ Research Team

### 步骤 2: 复制模板

```bash
# 从 _templates 复制到 agents/
cp -r agents/_templates/core-team agents/my-core-team

# 目录结构：
# agents/my-core-team/
# ├── AGENTS.md.template
# └── README.md
```

### 步骤 3: 定制 AGENTS.md

将 `AGENTS.md.template` 重命名为 `AGENTS.md`，然后定制：

#### 3.1 修改 Frontmatter

```yaml
---
description: [Team Name] - [角色描述]  # 修改
type: primary
skills:
  - git-workflow
  - review-process
  # 根据需要添加/删除 skills
memory_index: framework/memory-index.yaml
---
```

#### 3.2 修改角色定义

```markdown
# [Team Name] - [角色描述]

## 角色定位

[Team Name] 是项目的 [角色]，负责 [主要职责]。

### 核心职责
- [ ] [职责1]
- [ ] [职责2]
```

#### 3.3 修改模块边界

```markdown
## 📁 模块边界

### ✅ 负责维护
```
[模块1]/**
[模块2]/**
```

### ⚠️ Review Only
```
[其他模块]/**
```

### ❌ 不负责
```
[不负责的模块]/**
```
```

#### 3.4 修改行为准则

```markdown
## 🎯 行为准则

### 必须执行
- ✅ [必须做的事1]
- ✅ [必须做的事2]

### 严格禁止
- ❌ [禁止做的事1]
- ❌ [禁止做的事2]
```

### 步骤 4: 创建 CATCH_UP.md

创建 `agents/{team}/CATCH_UP.md`：

```markdown
# [Team Name] - 启动文档

> 🔄 启动时读取此文档

---

## Quick Status

**Last Updated**: [待填充]  
**Status**: 🟡 Initializing

---

## Current Focus

**Primary Task**: [待填充]

**Completed**: [待填充]

**Next Actions**:
1. [待填充]

---

## Project Context

- **Project**: [项目名称]
- **Goal**: [项目目标]

---

**Remember**: [关键提醒]
```

### 步骤 5: 配置 memory-index.yaml

在 `framework/memory-index.yaml` 中添加该 Team 的配置：

```yaml
agents:
  # 已有 PM Agent 配置...
  
  [team-name]:  # 新增
    identity:
      path: "agents/[team-name]/AGENTS.md"
      priority: P0
      estimated_tokens: 5000
      description: "[Team Name] 身份定义"
    
    state:
      path: "agents/[team-name]/CATCH_UP.md"
      priority: P1
      estimated_tokens: 2000
      description: "[Team Name] 当前状态"
```

### 步骤 6: 注册到 opencode.json

在 `opencode.json` 中注册该 Team：

```json
{
  "agents": {
    "pm": {
      "path": "agents/pm/AGENTS.md",
      "skills": [...]
    },
    "[team-name]": {  // 新增
      "path": "agents/[team-name]/AGENTS.md",
      "skills": [
        "framework/skills/workflow/git-workflow.md"
        // 根据需要添加 skills
      ]
    }
  }
}
```

### 步骤 7: 创建启动脚本

创建 `start-[team].sh` 和 `start-[team].bat`：

**start-[team].sh**:
```bash
#!/bin/bash
echo "Starting [Team Name]..."
opencode --agent [team-name]
```

**start-[team].bat**:
```batch
@echo off
echo Starting [Team Name]...
opencode --agent [team-name]
```

### 步骤 8: 更新项目文档

更新以下文档：

1. **CATCH_UP.md** - 在 Team Structure 中添加新 Team
2. **agent-status.md** - 添加新 Team 的状态行
3. **human-admin.md** - 添加新 Team 的信息

---

## 模板定制指南

### 添加自定义 Skills

如果 Team 需要特定技能，可以：

1. **创建 Skill 文件**:
   ```bash
   # 在 framework/skills/ 下创建
   mkdir -p framework/skills/[category]
   touch framework/skills/[category]/[skill-name].md
   ```

2. **在 AGENTS.md 中引用**:
   ```yaml
   skills:
     - git-workflow
     - [category]/[skill-name]
   ```

3. **在 opencode.json 中添加**:
   ```json
   "skills": [
     "framework/skills/workflow/git-workflow.md",
     "framework/skills/[category]/[skill-name].md"
   ]
   ```

### 调整模块边界

根据项目需求调整：

```markdown
## 📁 模块边界

### ✅ 负责维护
```
src/data-processing/**
tools/csv-parser/**
```

### ⚠️ Review Only
```
src/api/**          # API 层只 review
```

### ❌ 不负责
```
src/frontend/**     # 前端不负责
src/backend/**      # 后端不负责
```
```

### 定制行为准则

根据 Team 特点定制：

```markdown
## 🎯 行为准则

### 必须执行
- ✅ 每次启动读取 CATCH_UP.md
- ✅ 提交前运行测试
- ✅ 代码审查通过后才能合并
- ✅ 遇到性能问题立即上报

### 严格禁止
- ❌ 提交未测试的代码
- ❌ 直接修改其他 Team 的模块
- ❌ 忽略内存/性能问题
- ❌ 跳过代码审查
```

---

## 最佳实践

### DO ✅

- ✅ 根据项目需求选择合适的模板
- ✅ 充分定制 AGENTS.md
- ✅ 明确模块边界
- ✅ 添加项目特定的行为准则
- ✅ 及时更新 CATCH_UP.md
- ✅ 记录经验到 experiences/

### DON'T ❌

- ❌ 不做任何定制直接使用模板
- ❌ 模块边界模糊不清
- ❌ 职责与其他 Team 重叠
- ❌ 忽略质量门控

---

## 示例：定制 Core Team

### 场景：CSV 数据处理项目

**步骤**:

```bash
# 1. 复制模板
cp -r agents/_templates/core-team agents/csv-core

# 2. 编辑 AGENTS.md
vim agents/csv-core/AGENTS.md
# - description: "CSV Core Team - CSV 数据处理专家"
# - 核心职责: CSV 解析、数据清洗、格式转换
# - 模块边界: src/csv-processing/**, tools/csv-*/**

# 3. 创建 CATCH_UP.md
vim agents/csv-core/CATCH_UP.md

# 4. 配置 memory-index.yaml
vim framework/memory-index.yaml
# 添加 csv-core 配置

# 5. 注册到 opencode.json
vim opencode.json
# 添加 csv-core agent

# 6. 创建启动脚本
cp start-pm.sh start-csv-core.sh
vim start-csv-core.sh
# 修改 agent 名称为 csv-core

# 7. 更新项目文档
vim agents/pm/CATCH_UP.md
# 在 Team Structure 中添加 csv-core
```

---

## 参考资源

- [PM Agent 核心指南](../../pm/ESSENTIALS.md)
- [Agent Team 设计方法论](../../../docs/methodology/agent-team-design.md)
- [质量门控](../../../framework/skills/decision-support/quality-gate.md)

---

**维护者**: PM Agent Framework  
**最后更新**: 2026-03-08
