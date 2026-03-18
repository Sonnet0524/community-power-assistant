# Community Power Assistant

> 🏠 小区供电服务智能化解决方案
> 
> 包含 **开发工具框架** 和 **Field Info Agent 应用项目**

**版本**: 1.0.0 | **状态**: 开发中 | **更新**: 2026-03-18

---

## 📋 仓库结构

本仓库包含两个核心部分：

```
community-power-assistant/
│
├── 📁 agents/                    # 开发工具 - Agent 框架
│   ├── pm/                       # PM Agent（项目管理）
│   └── _templates/               # Team Agent 模板库
│
├── 📁 framework/                 # 开发工具 - 框架支持
│   ├── skills/                   # 通用技能
│   └── memory-index.yaml         # 记忆索引
│
├── 📁 knowledge-base/            # 🎯 应用项目 - Field Info Agent
│   └── field-info-agent/         # 现场信息收集智能体
│
├── 📁 tasks/                     # 任务文件
├── 📁 reports/                   # 报告文件
└── 📁 status/                    # 状态跟踪
```

| 部分 | 类型 | 说明 |
|------|------|------|
| `agents/`, `framework/` | 开发工具 | 通用的 Agent 开发框架，可复用于其他项目 |
| `knowledge-base/` | 应用项目 | Field Info Agent 具体业务实现 |

---

## 🎯 应用项目：Field Info Agent

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

## 🛠️ 开发工具：Agent 框架

### 什么是 PM Agent？

PM Agent 是本仓库内置的**项目管理智能体**，作为开发工具协调项目开发：

```
PM Agent (中心协调者)
    ↓ 创建和管理
Team Agent → Team Agent → Team Agent (执行者)
    ↓ 报告
PM Agent (汇总验收)
```

**核心能力**：
- 🎯 项目规划 - 理解项目目标，设计执行方案
- 👥 团队组建 - 根据需要动态创建 Agent Team
- 📋 任务管理 - 分配任务、跟踪进度、验收成果
- 📝 文档管理 - 维护项目文档和知识库

### 如何使用开发工具

#### 1. 启动 PM Agent

```bash
# 进入项目目录
cd community-power-assistant

# 启动 PM Agent
./start-pm.sh
# Windows: start-pm.bat
```

#### 2. PM Agent 工作流程

```
1. 读取 CATCH_UP.md（了解当前状态）
   ↓
2. 继续未完成的任务或开始新任务
   ↓
3. 通过 task 工具或启动 Team Agent 执行
   ↓
4. 验收报告，更新文档
```

#### 3. Team Agent 模板

`agents/_templates/` 提供可复用的 Agent 模板：

| 模板 | 职责 | 适用场景 |
|------|------|----------|
| Core Team | 数据处理、工具开发 | 数据处理项目 |
| AI Team | 向量嵌入、语义搜索 | AI/ML 项目 |
| Test Team | 测试、质量保证 | 需要测试的项目 |
| Integration Team | 系统集成 | 需要集成的项目 |
| Research Team | 理论研究 | 研究型项目 |

### 开发工具文档

| 文档 | 路径 | 说明 |
|------|------|------|
| PM Agent 初始化 | [agents/pm/INIT.md](agents/pm/INIT.md) | 首次启动必读 |
| PM Agent 状态 | [agents/pm/CATCH_UP.md](agents/pm/CATCH_UP.md) | 当前工作状态 |
| PM Agent 指南 | [agents/pm/ESSENTIALS.md](agents/pm/ESSENTIALS.md) | 详细工作规范 |
| 模板使用指南 | [agents/_templates/TEMPLATE-GUIDE.md](agents/_templates/TEMPLATE-GUIDE.md) | Team 模板使用 |

---

## 📁 完整目录结构

```
community-power-assistant/
│
├── agents/                           # 开发工具 - Agent 框架
│   ├── pm/                           # PM Agent
│   │   ├── AGENTS.md                 # 身份定义
│   │   ├── CATCH_UP.md               # 状态记忆
│   │   ├── INIT.md                   # 首次启动指南
│   │   ├── WORKFLOW.md               # 工作流程
│   │   ├── ESSENTIALS.md             # 核心指南
│   │   └── experiences/              # 经验积累
│   │
│   └── _templates/                   # Team Agent 模板库
│       ├── core-team/
│       ├── ai-team/
│       ├── test-team/
│       ├── integration-team/
│       └── research-team/
│
├── framework/                        # 开发工具 - 框架支持
│   ├── memory-index.yaml             # 记忆索引
│   └── skills/                       # 通用技能
│       ├── workflow/
│       └── decision-support/
│
├── knowledge-base/                   # 🎯 应用项目
│   └── field-info-agent/             # Field Info Agent
│       ├── README.md                 # 项目总览 ⭐
│       ├── OPENCLAW-SKILLS-STANDARD.md  # Skills 开发标准 ⭐
│       ├── IMPLEMENTATION-SUMMARY.md    # 实现总结 ⭐
│       │
│       ├── agents/field-collector/   # Agent 实现
│       │   ├── AGENTS.md             # Agent 角色定义
│       │   ├── openclaw.config.yaml  # OpenClaw 配置
│       │   └── workspace/
│       │       ├── skills/           # Skills 定义
│       │       ├── database/         # 数据库 Schema
│       │       └── docker-compose.yml
│       │
│       ├── design/                   # 设计文档
│       │   ├── detailed-design-v2.md
│       │   ├── storage-change-v2.2.md
│       │   └── openclaw-feasibility-verification.md
│       │
│       └── analysis/                 # 分析文档
│           └── technical-feasibility-analysis.md
│
├── tasks/                            # 任务文件
├── reports/                          # 报告文件
├── status/                           # 状态跟踪
├── archive/                          # 实践经验库
├── logs/                             # 日志文件
│
├── start-pm.sh                       # PM Agent 启动脚本
├── start-pm.bat
├── opencode.json                     # OpenCode 配置
└── README.md                         # 本文件
```

---

## 🚀 快速开始

### 作为应用项目使用

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

### 作为开发工具使用

1. **启动 PM Agent**
   ```bash
   ./start-pm.sh
   ```

2. **PM Agent 自动引导后续工作**

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

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw Skills 规范](https://docs.openclaw.ai/tools/skills)
- [AgentSkills 规范](https://agentskills.io)
- [OpenCode](https://opencode.ai) - Agent 执行框架

---

**维护者**: Sonnet.G  
**创建日期**: 2026-03-08  
**最后更新**: 2026-03-18
