# Community Power Assistant

> 🏠 小区供电服务智能化解决方案

**版本**: 1.0.0 | **状态**: 开发中 | **更新**: 2026-03-18

---

## 📋 关于本仓库

本仓库是基于 **[sonnet0524/agent-team-template](https://github.com/sonnet0524/agent-team-template)** 框架开发的项目，包含 **Field Info Agent（现场信息收集智能体）** 的完整实现。

---

## 🎯 Field Info Agent

### 项目简介

**Field Info Agent（现场信息收集智能体）** 是一个基于 OpenClaw 框架的驻点工作辅助系统，为供电所驻点人员提供智能化信息收集和分析服务。

### 核心功能

| 功能 | 说明 |
|------|------|
| 🔌 **驻点工作引导** | 自然语言交互，动态生成工作清单，引导现场采集流程 |
| 🔍 **AI 照片分析** | KIMI 2.5 多模态分析，识别电力设备、检测缺陷、评估状态 |
| 📄 **文档自动生成** | 自动生成驻点工作记录表、设备缺陷报告等 Word 文档 |
| 🚨 **应急处理引导** | 快速记录应急信息，GPS 位置标注，一键上报 |

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     企业微信（交互渠道）                       │
└─────────────────────────────┬───────────────────────────────┘
                              │ WebSocket 长连接
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   OpenClaw Gateway                           │
│              (Agent 运行时 + 多模态 LLM)                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │    MinIO      │    │    Redis      │
│  (业务数据)    │    │  (照片/文档)   │    │   (会话缓存)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

**技术栈**：
- **Agent 框架**: OpenClaw
- **AI 模型**: KIMI 2.5（多模态）
- **渠道**: 企业微信 WebSocket 长连接
- **存储**: PostgreSQL + MinIO + Redis
- **文档**: Word (.docx)

### 关键设计

#### 1. Skills 架构（遵循 OpenClaw 标准）

Skills 采用 `SKILL.md` (Markdown) 定义能力指南，在 `openclaw.config.yaml` 中配置触发器：

| Skill | 文件 | 职责 |
|-------|------|------|
| station-work-guide | `skills/station-work-guide/SKILL.md` | 驻点工作流程引导 |
| vision-analysis | `skills/vision-analysis/SKILL.md` | AI 照片智能分析 |
| doc-generation | `skills/doc-generation/SKILL.md` | 文档自动生成 |
| emergency-guide | `skills/emergency-guide/SKILL.md` | 应急处理引导 |

详见：[OpenClaw Skills 开发标准](knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md)

#### 2. 零命令自然语言交互

```
用户: 我今天要去阳光社区驻点
Agent: 📋 已为您准备阳光社区驻点工作...

用户: [发送变压器照片]
Agent: 🔍 分析结果：箱式变压器，状态正常...

用户: 采集完成
Agent: ✅ 已生成工作报告，点击下载...
```

#### 3. 本地化数据存储

所有数据存储在本地服务器，符合电力行业安全规范：
- PostgreSQL: 业务数据 + 版本化知识库
- MinIO: 照片 + 生成的文档
- Redis: 会话状态缓存

### 📚 项目文档导航

#### 快速了解

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目总览** | [knowledge-base/field-info-agent/README.md](knowledge-base/field-info-agent/README.md) | 项目介绍和最新状态 ⭐ |
| **实现总结** | [knowledge-base/field-info-agent/IMPLEMENTATION-SUMMARY.md](knowledge-base/field-info-agent/IMPLEMENTATION-SUMMARY.md) | 已完成组件清单 ⭐ |
| **Skills 标准** | [knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md](knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md) | 开发规范 ⭐ |

#### 设计文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 详细设计 v2.1 | [design/detailed-design-v2.md](knowledge-base/field-info-agent/design/detailed-design-v2.md) | 完整技术方案 |
| 存储设计 v2.2 | [design/storage-change-v2.2.md](knowledge-base/field-info-agent/design/storage-change-v2.2.md) | 本地存储方案 |
| 可行性验证 | [design/openclaw-feasibility-verification.md](knowledge-base/field-info-agent/design/openclaw-feasibility-verification.md) | OpenClaw 框架验证 |

#### 开发任务

| 文档 | 路径 | 说明 |
|------|------|------|
| 任务清单 | [tasks/TASK-LIST-field-info-agent.md](tasks/TASK-LIST-field-info-agent.md) | 所有开发任务 |
| TASK-001 | [tasks/TASK-001-environment-setup.md](tasks/TASK-001-environment-setup.md) | 基础环境搭建 |
| TASK-002 | [tasks/TASK-002-wps-api-tool.md](tasks/TASK-002-wps-api-tool.md) | WPS API 工具开发 |
| TASK-003 | [tasks/TASK-003-wecom-channel.md](tasks/TASK-003-wecom-channel.md) | 企业微信渠道配置 |

#### 实现文件

| 文件 | 路径 | 说明 |
|------|------|------|
| Agent 定义 | [agents/field-collector/AGENTS.md](knowledge-base/field-info-agent/agents/field-collector/AGENTS.md) | OpenClaw Agent 角色 |
| 主配置 | [agents/field-collector/openclaw.config.yaml](knowledge-base/field-info-agent/agents/field-collector/openclaw.config.yaml) | OpenClaw 配置 |
| 数据库 Schema | [workspace/database/schema.sql](knowledge-base/field-info-agent/agents/field-collector/workspace/database/schema.sql) | PostgreSQL 结构 |
| Docker 编排 | [workspace/docker-compose.yml](knowledge-base/field-info-agent/agents/field-collector/workspace/docker-compose.yml) | 基础设施 |

---

## 📁 目录结构

```
community-power-assistant/
├── knowledge-base/field-info-agent/  # 🎯 Field Info Agent 项目
│   ├── README.md                     # 项目总览 ⭐
│   ├── OPENCLAW-SKILLS-STANDARD.md   # Skills 开发标准 ⭐
│   ├── IMPLEMENTATION-SUMMARY.md     # 实现总结 ⭐
│   │
│   ├── agents/field-collector/       # Agent 实现
│   │   ├── AGENTS.md                 # Agent 角色定义
│   │   ├── openclaw.config.yaml      # OpenClaw 配置
│   │   └── workspace/
│   │       ├── skills/               # Skills 定义
│   │       ├── database/             # 数据库 Schema
│   │       └── docker-compose.yml    # 基础设施编排
│   │
│   ├── design/                       # 设计文档
│   └── analysis/                     # 分析文档
│
├── tasks/                            # 开发任务
├── agents/                           # 开发工具框架
└── README.md                         # 本文件
```

---

## 🚀 快速开始

1. **阅读项目文档**
   ```bash
   # 了解 Field Info Agent 项目
   cat knowledge-base/field-info-agent/README.md
   ```

2. **查看设计文档**
   ```bash
   # 技术方案
   cat knowledge-base/field-info-agent/design/detailed-design-v2.md
   
   # 开发规范
   cat knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md
   ```

3. **开始开发**
   ```bash
   # 查看任务清单
   cat tasks/TASK-LIST-field-info-agent.md
   ```

---

## 📊 项目状态

| 项目 | 状态 | 说明 |
|------|------|------|
| Field Info Agent 设计 | ✅ 完成 | 详细设计 v2.1, v2.2 |
| OpenClaw 实现结构 | ✅ 完成 | Agent + Skills + 配置 |
| Skills 格式标准化 | ✅ 完成 | 符合 OpenClaw 官方规范 |
| 开发任务规划 | ✅ 完成 | TASK-001 ~ TASK-007 |
| 基础环境搭建 | ⏳ 待开始 | TASK-001 |
| 企业微信集成 | ⏳ 待开始 | TASK-003 |
| AI 照片分析 | ⏳ 待开始 | TASK-004 |

---

## 🤝 贡献

欢迎贡献：
- OpenClaw Skills 最佳实践
- Agent Team 模板
- 设计文档改进
- Bug 修复

---

## 📄 许可证

AGPL v3 License

---

## 🔗 相关资源

- [agent-team-template](https://github.com/sonnet0524/agent-team-template) - 本项目的开发框架
- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw Skills 规范](https://docs.openclaw.ai/tools/skills)
- [AgentSkills 规范](https://agentskills.io)

---

**维护者**: Sonnet.G  
**创建日期**: 2026-03-08  
**最后更新**: 2026-03-18
