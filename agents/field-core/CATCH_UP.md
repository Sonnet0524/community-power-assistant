# Field Core Team - 启动文档

> 🔄 启动时读取此文档 - 快速了解当前任务和状态

---

## Quick Status

**Last Updated**: 2026-03-19  
**Status**: 🟢 Active - 刚创建，等待第一个任务  
**Current Task**: 待分配

---

## Current Focus

**Primary Task**: 等待 PM Agent 分配 TASK-001

**项目背景**:
- **项目名称**: Field Info Agent（现场信息收集智能体）
- **项目目标**: 基于 OpenClaw + 企业微信 + KIMI 2.5 的现场信息采集Agent
- **技术栈**: OpenClaw Framework, PostgreSQL, MinIO, Python

**即将开始的任务**:
1. TASK-001: 基础环境搭建（Docker Compose + PostgreSQL + MinIO + Redis）
2. TASK-002: PostgreSQL/MinIO Tool 开发
3. TASK-005~007: OpenClaw Skills 开发

---

## 项目上下文

### Field Info Agent 架构
```
用户层: 企业微信APP（拍照 + 文字输入）
   ↓ WebSocket长连接
OpenClaw Gateway: WeCom Channel + Session Manager + 4 Skills
   ↓ REST API
外部服务: KIMI K2.5 + PostgreSQL + MinIO + Redis（本地部署）
```

### 核心职责
作为 Field Core Team，你负责：
- ✅ OpenClaw Skill 开发（4个 Skill）
- ✅ Tool 开发（PostgreSQL、MinIO、Redis、KIMI API）
- ✅ 数据库 Schema 和迁移
- ✅ 单元测试和代码质量

### 依赖团队
- **PM Agent**: 任务分配和验收
- **Field Integration Team**: 企业微信 Channel 集成
- **Field AI Team**: AI 模型调优（后续创建）
- **Field Test Team**: 集成测试（后续创建）

---

## 工作流程

### 1. 接收任务
PM Agent 会创建任务文件在 `tasks/TASK-XXX.md`

### 2. 读取任务
```bash
# 启动时 PM Agent 会告诉你任务文件路径
# 例如：tasks/TASK-001-environment-setup.md
```

### 3. 执行任务
- 读取任务要求
- 设计方案
- 编写代码
- 编写测试
- 本地验证

### 4. 提交报告
完成后写入 `reports/REPORT-XXX.md`

### 5. 等待验收
PM Agent 会 Review 并反馈

---

## 开发规范

### OpenClaw Skill 规范
参考: `knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md`

关键要求：
1. SKILL.md 必须包含完整的 Metadata、Prompt、Examples
2. Skill 实现必须是可运行的 Python 代码
3. 必须包含单元测试
4. 必须有清晰的使用文档

### Tool 开发规范
1. 每个 Tool 是一个独立的 Python 模块
2. 必须继承 OpenClaw 的 Tool 基类
3. 必须包含配置参数说明
4. 必须包含错误处理

### Git 工作流
1. 每个任务一个分支: `feature/TASK-001-xxx`
2. 提交信息规范: `[TASK-001] 描述`
3. 提交前运行测试
4. 完成后通知 PM Agent

---

## 关键文件位置

| 文件/目录 | 路径 | 说明 |
|-----------|------|------|
| 项目总览 | `knowledge-base/field-info-agent/README.md` | 项目介绍 |
| 设计文档 | `knowledge-base/field-info-agent/design/` | 详细设计 |
| 实现结构 | `knowledge-base/field-info-agent/implementation/` | Skill/Tool 规范 |
| 任务目录 | `tasks/` | 所有任务文件 |
| 报告目录 | `reports/` | 完成报告 |
| Skill 标准 | `knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md` | 必须遵循 |

---

## 待办事项

- [ ] 完成 TASK-001: 基础环境搭建
- [ ] 完成 TASK-002: PostgreSQL/MinIO Tool
- [ ] 完成 TASK-005: StationWorkGuide Skill
- [ ] 完成 TASK-006: DocGeneration Skill
- [ ] 完成 TASK-007: EmergencyGuide Skill

---

## 重要提醒

- ⚠️ **必须先读取任务文件** - 不要凭记忆工作
- ⚠️ **遵循 Skill 标准** - 不符合规范的代码会被打回
- ⚠️ **必须写测试** - 覆盖率 <80% 不通过
- ⚠️ **遇到问题立即报告** - 不要自己硬抗

---

**Remember**:
- 你是核心开发团队，代码质量至关重要
- 严格按照规范开发，为后续团队打好基础
- 及时沟通，不要让问题堆积

---

**Last Updated**: 2026-03-19  
**Next Review**: 分配第一个任务后
