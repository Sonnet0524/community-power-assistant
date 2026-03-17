# PM Agent - 启动文档

> 🔄 **启动时读取此文档** - 快速了解当前状态和工作

---

## Quick Status

**Last Updated**: 2026-03-18 10:30  
**Current Phase**: OpenClaw Agent结构创建完成 - 待分配开发团队  
**Status**: 🟢 Ready - 等待开发团队启动TASK-001

---

## Current Focus

**Primary Task**: Field Info Agent的OpenClaw实现结构已完成创建

**Completed Actions**:
- ✅ 完成技术可行性深度分析（OpenClaw + 企业微信 + KIMI 2.5）
- ✅ 完成详细设计方案 v2.1（语音→文字、OCR→KIMI多模态）
- ✅ 完成存储方案设计 v2.2（WPS云文档→本地MinIO+PostgreSQL）
- ✅ 完成OpenClaw框架可行性验证
- ✅ 设计并创建11个开发任务（TASK-001到TASK-007）
- ✅ 所有设计文档已提交到Git仓库
- ✅ **完成**: OpenClaw Agent完整实现结构创建
  - ✅ Agent角色定义（AGENTS.md）
  - ✅ OpenClaw配置（openclaw.config.yaml）
  - ✅ 4个Skill定义（station-work-guide, vision-analysis简化版, doc-generation, emergency-guide）
  - ✅ 数据库Schema（PostgreSQL）
  - ✅ Docker Compose配置（PostgreSQL + MinIO + Redis）
  - ✅ 环境变量模板（.env.example）

**Next Actions**:
1. ⏳ 分配开发团队，启动TASK-001（基础环境搭建）
2. ⏳ 申请相关API权限（企业微信、KIMI 2.5）
3. ⏳ 开发团队Review实现结构，开始编码

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
| Team | Status | Current Task | Owner |
|------|--------|--------------|-------|
| PM | 🟢 Active | 设计完成，协调开发 | PM Agent |
| Backend Dev | 🟡 Pending | 等待启动 | 待分配 |
| DevOps | 🟡 Pending | 等待启动 | 待分配 |
| QA | 🟡 Pending | 等待启动 | 待分配 |

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

**Last Updated**: 2026-03-17 20:00  
**Git Commit**: d76f526 - "feat: Add Field Info Agent project design documents"  
**Next Work**: 分配开发团队，启动TASK-001（基础环境搭建）
