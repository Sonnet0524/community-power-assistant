# PM Agent - 启动文档

> 🔄 **启动时读取此文档** - 快速了解当前状态和工作

---

## Quick Status

**Last Updated**: 2026-03-19 11:30  
**Current Phase**: 设计完成，项目介绍已汇报，等待开发启动  
**Status**: 🟡 开发准备就绪，待Human决策开发团队组建方案

---

## Current Focus

**Primary Task**: 等待开发团队组建决策，启动 TASK-001（基础环境搭建）

**Completed Actions**:
- ✅ 完成技术可行性深度分析（OpenClaw + 企业微信 + KIMI 2.5）
- ✅ 完成详细设计方案 v2.1（语音→文字、OCR→KIMI多模态）
- ✅ 完成存储方案设计 v2.2（WPS云文档→本地MinIO+PostgreSQL）
- ✅ 完成OpenClaw框架可行性验证
- ✅ 设计并创建11个开发任务（TASK-001到TASK-011）
- ✅ 所有设计文档已提交到Git仓库
- ✅ **完成**: OpenClaw Agent完整实现结构创建
  - ✅ Agent角色定义（AGENTS.md）
  - ✅ OpenClaw配置（openclaw.config.yaml）
  - ✅ 4个Skill定义（station-work-guide, vision-analysis简化版, doc-generation, emergency-guide）
  - ✅ 数据库Schema（PostgreSQL）
  - ✅ Docker Compose配置（PostgreSQL + MinIO + Redis）
  - ✅ 环境变量模板（.env.example）
- ✅ **OpenClaw Skills 标准化** - 所有 SKILL.md 修正为官方标准格式
- ✅ **README 重构** - 明确区分开发工具和应用项目
- ✅ **Skills 开发标准文档** - 创建 `OPENCLAW-SKILLS-STANDARD.md`
- ✅ **架构图优化** - 简化核心层，提交到Git
- ✅ **项目介绍汇报** - 业务逻辑和技术架构详细介绍

**Next Actions**:
1. ⏳ **Human决策**: 开发团队组建方案
   - 方案A: 创建专用开发团队Agent（field-core, field-integration等）
   - 方案B: 使用task工具启动临时Agent执行任务
2. ⏳ 启动 TASK-001（基础环境搭建）
3. ⏳ 申请相关 API 权限（企业微信、KIMI 2.5）
4. ⏳ 开发团队 Review 实现结构，开始编码

---

## 📝 本次更新要点 (2026-03-19)

### 项目介绍汇报

**内容**: 向Human详细介绍项目的业务逻辑和技术架构

**业务逻辑总结**:
- 目标用户：供电所驻点人员（客户经理）
- 核心场景：出发前准备 → 现场采集 → 智能分析 → 文档生成
- 四大功能：驻点工作引导、照片智能分析、文档自动生成、应急处置
- 工作流程状态机：IDLE → PREPARING → COLLECTING → ANALYZING → COMPLETED

**技术架构总结**:
```
用户层: 企业微信APP（拍照 + 文字输入）
   ↓ WebSocket长连接
OpenClaw Gateway: WeCom Channel + Session Manager + 4 Skills
   ↓ REST API
外部服务: KIMI K2.5 + PostgreSQL + MinIO + Redis（本地部署）
```

**关键技术决策**:
- 语音识别：❌ 移除（用户使用语音输入法）
- OCR：❌ 移除（KIMI多模态能力更强）
- 照片分析：KIMI K2.5（国产合规、中文优化）
- 存储：本地MinIO+PostgreSQL（数据主权、约省¥300/月）
- 企业微信：长连接模式（支持流式输出）

**成本估算**: ¥500-900/月

**待Human决策**: 开发团队组建方案

---

## Project Context

### Project Info
- **Name**: Field Info Agent（现场信息收集智能体）
- **Goal**: 基于 OpenClaw + 企业微信 + KIMI 2.5 的现场信息采集Agent，提供驻点工作引导、照片智能分析、文档自动生成
- **Tech Stack**: 
  - OpenClaw Framework
  - 企业微信（文字+图片）
  - KIMI 2.5（多模态识图）
  - MinIO + PostgreSQL（本地存储）
- **Duration**: 12周（3个月）

### Team Structure
| Team | Status | Current Task | Owner | Template |
|------|--------|--------------|-------|----------|
| PM | 🟢 Active | 设计完成，协调开发 | PM Agent | - |
| **Core Team** | 🔴 待创建 | TASK-001, TASK-002 | 待分配 | `core-team` |
| **Integration Team** | 🔴 待创建 | TASK-003 | 待分配 | `integration-team` |
| **AI Team** | 🟡 计划中 | TASK-004 | 待分配 | `ai-team` |
| **Test Team** | 🟡 计划中 | TASK-009 | 待分配 | `test-team` |

**团队创建计划**:
1. 创建 `agents/field-core/` - 负责 OpenClaw Skills 和 Tool 开发
2. 创建 `agents/field-integration/` - 负责企业微信 Channel 集成
3. 后续按需创建 AI Team 和 Test Team

**开发任务依赖**:
```
TASK-001 (环境搭建)
    ├── TASK-002 (PostgreSQL/MinIO Tool)
    ├── TASK-003 (企业微信Channel)
    │       └── TASK-004 (KIMI多模态集成)
    │               ├── TASK-005 (StationWorkGuide)
    │               ├── TASK-006 (DocGeneration)
    │               └── TASK-007 (EmergencyGuide)
```

---

## Working Directory

**启动位置**: `/Users/sonnet/opencode/community-power-assistant`

**Key Paths**:
- PM Config: `agents/pm/`
- Project Design: `knowledge-base/field-info-agent/` ⭐
- Tasks: `tasks/` ⭐
- Project Status: `status/field-info-agent-status.md` ⭐
- Reports: `reports/`
- Archive: `archive/`

---

## Quick Reference

| 文档 | 路径 | 用途 |
|------|------|------|
| 项目总览 | `knowledge-base/field-info-agent/README.md` | 项目介绍和最新状态 |
| 任务总览 | `tasks/TASK-LIST-field-info-agent.md` | 所有开发任务列表 |
| 设计文档 | `knowledge-base/field-info-agent/design/` | 详细设计方案 |
| 技术可行性 | `knowledge-base/field-info-agent/analysis/` | 可行性分析 |
| 项目状态 | `status/field-info-agent-status.md` | 实时状态跟踪 |
| 本文件 | `agents/pm/CATCH_UP.md` | PM工作当前状态 |
| 核心指南 | `agents/pm/ESSENTIALS.md` | 工作规范 |
| 工作流程 | `agents/pm/WORKFLOW.md` | Agent 管理 |

---

## Status Update Rules

**何时更新本文件**：
- ✅ 任务完成后
- ✅ 每日至少检查一次
- ✅ 遇到阻塞或重大变更
- ✅ 新增或修改 Team 结构

**更新内容**：
- Last Updated 时间
- Current Phase 和 Status
- Completed Actions
- Next Actions
- Team Structure 变化

---

## 🎯 核心原则提醒

- ✅ **主动启动 Agent** - 分配任务后立即启动
- ❌ **不轮询状态** - 不主动检查 Agent 进度
- ✅ **被动接收报告** - 等待 Agent 报告完成
- 📄 **文档化交互** - 通过 tasks/ 和 reports/ 交换信息

---

**Remember**: 
- 在根目录启动
- 你是项目的中心协调者
- 关键决策需要 Human 确认
- 经验需要及时沉淀到 `experiences/`

---

**Last Updated**: 2026-03-19 11:30  
**Key Changes**: 项目介绍汇报、业务逻辑和技术架构详细介绍  
**Next Work**: 等待Human决策开发团队组建方案
