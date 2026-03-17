# PM Agent - 启动文档

> 🔄 **启动时读取此文档** - 快速了解当前状态和工作

---

## Quick Status

**Last Updated**: 2026-03-17  
**Current Phase**: 初始化  
**Status**: 🟢 Initializing

---

## Current Focus

**Primary Task**: 项目初始化完成，等待细化需求

**Completed Actions**:
- ✅ 从模板实例化项目仓库
- ✅ 初始化项目配置

**Next Actions**:
1. Human 确认项目需求和范围
2. 设计 Agent Team 结构
3. 创建第一个开发任务

---

## Project Context

### Project Info
- **Name**: 小区供电服务信息助理
- **Goal**: 基于 OpenCode 开发的小区驻点服务助理，提供供电服务信息管理和智能支持
- **Constraints**: 
  - 基于 OpenCode 框架
  - 面向小区供电服务场景

### Team Structure
| Team | Status | Current Task | Owner |
|------|--------|--------------|-------|
| PM | 🟢 Active | 项目初始化 | PM Agent |
| [待设计] | - | - | - |

---

## Working Directory

**启动位置**: [当前目录路径]

**Key Paths**:
- PM Config: `agents/pm/`
- Team Templates: `agents/_templates/`
- Tasks: `tasks/`
- Reports: `reports/`
- Status: `status/`
- Archive: `archive/`

---

## Quick Reference

| 文档 | 路径 | 用途 |
|------|------|------|
| 初始化指南 | `agents/pm/INIT.md` | 首次启动必读 |
| 本文件 | `agents/pm/CATCH_UP.md` | 当前状态 |
| 核心指南 | `agents/pm/ESSENTIALS.md` | 工作规范 |
| 工作流程 | `agents/pm/WORKFLOW.md` | Agent 管理 |
| Agent 模板 | `agents/_templates/` | 创建 Team |
| 实践经验 | `archive/` | 参考经验 |

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

**Last Updated**: 2026-03-17  
**Next Work**: 等待 Human 细化项目需求和范围
