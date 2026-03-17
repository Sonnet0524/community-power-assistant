# PM Agent 初始化指南

> 🚀 首次启动 PM Agent 时，请按以下步骤执行

---

## 📋 初始化清单

### Step 1: 理解项目目标（必须）

请向 Human 询问以下问题：

#### 1.1 项目基本信息
- [ ] **项目名称**是什么？
- [ ] **项目目标**是什么？（一句话概括）
- [ ] 项目的**核心功能**是什么？
- [ ] 期望的**交付物**是什么？（代码/文档/研究报告/其他）

#### 1.2 项目约束
- [ ] **技术栈**限制？（如：必须使用 Python、必须使用某框架）
- [ ] **时间**限制？（截止日期）
- [ ] **资源**限制？（预算、人员、算力）
- [ ] **质量要求**？（如：测试覆盖率、文档要求）

#### 1.3 协作方式
- [ ] Human 希望如何参与？（每日同步/里程碑检查/完全自主）
- [ ] 决策权限？（PM Agent 可以自主决策的范围）
- [ ] 汇报频率？（每日/每周/里程碑）

---

### Step 2: 设计 Agent Team（必须）

基于项目目标，决定需要哪些 Team。

#### 2.1 选择 Team 类型

查看 `agents/_templates/` 中的可用模板：

| Team | 职责 | 适用场景 | 模板路径 |
|------|------|----------|----------|
| Core Team | 数据处理、工具开发 | 需要数据处理的项目 | `core-team/` |
| AI Team | 向量嵌入、语义搜索、ML | AI/ML 相关项目 | `ai-team/` |
| Frontend Team | 前端界面开发 | Web 应用 | （待创建） |
| Backend Team | 后端服务开发 | Web 服务 | （待创建） |
| Test Team | 测试、质量保证 | 需要测试的项目 | `test-team/` |
| Integration Team | 系统集成、连接器 | 需要集成的项目 | `integration-team/` |
| Research Team | 理论研究、框架设计 | 研究型项目 | `research-team/` |

#### 2.2 创建 Team 的步骤

对于每个需要的 Team：

1. **复制模板**
   ```bash
   cp -r agents/_templates/{team} agents/{team}
   ```

2. **定制 AGENTS.md**
   - 修改 `description` 中的角色描述
   - 调整 `模块边界` 部分
   - 更新 `行为准则`
   - 根据项目需求增减 skills

3. **配置 memory-index.yaml**
   在 `framework/memory-index.yaml` 中添加该 Team 的配置

4. **注册到 opencode.json**
   在 `opencode.json` 中注册该 Team Agent

5. **创建启动脚本**
   创建 `start-{team}.sh` 和 `start-{team}.bat`

6. **更新 CATCH_UP.md**
   在 Team Structure 表格中添加新 Team

---

### Step 3: 初始化项目文档（必须）

#### 3.1 更新状态文档

**编辑 `status/agent-status.md`**：
```markdown
# Agent Status

## Project: [项目名称]

| Agent | Status | Last Update | Current Task | Blockers |
|-------|--------|-------------|--------------|----------|
| PM | 🟢 Active | [时间] | 初始化项目 | 无 |
| [Team] | 🟡 Pending | - | - | - |
```

**编辑 `status/human-admin.md`**：
```markdown
# Human Admin Dashboard

## Project Overview
- **Name**: [项目名称]
- **Goal**: [一句话目标]
- **Status**: [当前阶段]

## Team Members
| Role | Agent | Status |
|------|-------|--------|
| PM | PM Agent | 🟢 Active |
| [Role] | [Team] | [Status] |

## Quick Links
- Tasks: `tasks/`
- Reports: `reports/`
- Archive: `archive/`
```

#### 3.2 创建第一个任务

在 `tasks/` 目录下创建第一个任务文件：
```markdown
# Task 1: [任务名称]

## Background
[任务背景]

## Requirements
1. [要求1]
2. [要求2]

## Acceptance Criteria
- [ ] [验收标准1]
- [ ] [验收标准2]

## Output
完成后在 `reports/task-1-report.md` 写入报告

---
**Priority**: P0
**Assigned to**: [Team]
```

#### 3.3 更新 CATCH_UP.md

填写以下信息：
- Project Info（名称、目标、约束）
- Team Structure
- Current Focus
- Next Actions

---

### Step 4: 项目启动（可选）

#### 4.1 启动第一个 Team

如果需要立即开始工作：

1. **分配任务**
   ```bash
   # 创建任务文件
   cat > tasks/{team}-task-1.md << 'EOF'
   [任务内容]
   EOF
   ```

2. **启动 Team Agent**
   ```bash
   # 方法1: 直接启动
   opencode run --agent {team} "读取 tasks/{team}-task-1.md 并执行，结果写入 reports/{team}-report-1.md" > logs/{team}.log 2>&1 &
   
   # 方法2: 使用启动脚本
   ./start-{team}.sh
   ```

3. **等待报告**
   PM Agent 继续其他工作，不轮询状态

---

## 📚 参考资源

### 模板使用
- `agents/_templates/TEMPLATE-GUIDE.md` - Agent 模板使用指南
- `agents/_templates/{team}/` - 各 Team 模板

### 实践经验
- `archive/sg-agentteam-experiences/` - SG-AgentTeam 的实践经验
- 按 Team 分类的经验文档

### 技能文档
- `framework/skills/workflow/` - 工作流程技能
- `framework/skills/decision-support/` - 决策支持技能

---

## ⚠️ 重要提醒

1. **不要跳过 Step 1** - 充分理解项目目标是成功的基础
2. **Team 不是越多越好** - 根据项目复杂度选择，可以逐步增加
3. **文档要及时更新** - 特别是 `CATCH_UP.md` 和 `status/` 下的文件
4. **经验要及时沉淀** - 重要决策和问题解决后要写入 `experiences/`

---

## ✅ 初始化完成检查

- [ ] 已理解项目目标
- [ ] 已设计 Team 结构
- [ ] 已创建/配置所有 Team
- [ ] 已更新 `status/agent-status.md`
- [ ] 已更新 `status/human-admin.md`
- [ ] 已更新 `agents/pm/CATCH_UP.md`
- [ ] 已创建第一个任务（可选）

**初始化完成后，删除或归档此文件，后续使用 `CATCH_UP.md` 作为启动文档。**

---

**最后更新**: 2026-03-08  
**维护者**: PM Agent Template
