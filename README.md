# 小区供电服务信息助理 (Community Power Assistant)

> **基于 PM Agent Template 的项目**
>
> 基于 OpenCode 框架开发的小区驻点服务助理系统。
> 该项目是 PM Agent 模板的实例化项目，L3 应用层。
>
> **模板来源**: `agent-team-template` (L2 层)

> 🤖 为小区供电服务提供智能化信息管理和服务支持

**版本**: 1.0.0 | **状态**: 初始化中 | **更新**: 2026-03-17

---

## 💡 什么是 PM Agent？

PM Agent 是一个**独立的项目管理工具**，能够：

- 🎯 **项目规划** - 理解项目目标，设计执行方案
- 👥 **团队组建** - 根据需要动态创建 Agent Team
- 📋 **任务管理** - 分配任务、跟踪进度、验收成果
- 📝 **文档管理** - 维护项目文档和知识库
- 🔍 **质量保证** - 代码审查、测试验收

### 核心理念

```
PM Agent (中心协调者)
    ↓ 创建和管理
Team A → Team B → Team C (执行者)
    ↓ 报告
PM Agent (汇总验收)
```

**关键原则**：
- ✅ **主动启动** - 分配任务后立即启动 Agent
- ❌ **不轮询** - 不主动检查 Agent 进度
- ✅ **被动接收** - 等待 Agent 报告完成
- 📄 **文档化交互** - 通过文档交换信息

---

## 📁 目录结构

```
pm-agent-template/
├── agents/
│   ├── pm/                           # PM Agent（核心）
│   │   ├── AGENTS.md                 # 身份定义
│   │   ├── CATCH_UP.md               # 状态记忆（通用化）
│   │   ├── INIT.md                   # 首次启动指南 ⭐
│   │   ├── WORKFLOW.md               # 工作流程
│   │   ├── ESSENTIALS.md             # 核心指南
│   │   ├── session-log.md            # 会话记录
│   │   ├── experiences/              # 经验积累
│   │   └── guides/                   # 详细指南
│   │
│   └── _templates/                   # Agent 模板库 ⭐
│       ├── core-team/                # 数据处理 Team 模板
│       ├── ai-team/                  # AI Team 模板
│       ├── test-team/                # 测试 Team 模板
│       ├── integration-team/         # 集成 Team 模板
│       ├── research-team/            # 研究 Team 模板
│       └── TEMPLATE-GUIDE.md         # 模板使用指南
│
├── framework/
│   ├── memory-index.yaml             # 记忆索引
│   └── skills/
│       ├── workflow/
│       │   ├── git-workflow.md       # Git 工作流
│       │   └── review-process.md     # 代码审查流程
│       └── decision-support/
│           └── quality-gate.md       # 质量门控
│
├── status/
│   ├── agent-status.md               # 团队状态跟踪
│   └── human-admin.md                # 用户总览
│
├── archive/                          # 实践经验库 ⭐
│   └── sg-agentteam-experiences/     # SG-AgentTeam 的实践经验
│
├── tasks/                            # 动态：任务文件
├── reports/                          # 动态：报告文件
├── logs/                             # 动态：日志文件
├── issues/                           # 问题管理
├── knowledge-base/                   # 项目知识库
├── start-pm.sh                       # 启动脚本（Unix）
├── start-pm.bat                      # 启动脚本（Windows）
├── opencode.json                     # OpenCode 配置
└── README.md                         # 本文件
```

---

## 🚀 快速开始

### 1. 安装 OpenCode CLI

```bash
pip install opencode
```

### 2. 配置 OpenCode

编辑 OpenCode 配置，添加本项目：

```bash
# 编辑配置文件
# Linux/Mac: ~/.config/opencode/config.yaml
# Windows: %APPDATA%\opencode\config.yaml

projects:
  pm-agent-template:
    path: /path/to/pm-agent-template
```

### 3. 首次启动 PM Agent

```bash
# 进入项目目录
cd pm-agent-template

# 启动 PM Agent
./start-pm.sh
# Windows: start-pm.bat
```

### 4. 初始化项目

PM Agent 首次启动后会读取 `INIT.md`，引导你完成：

1. **理解项目目标** - 询问 Human 项目基本信息
2. **设计 Agent Team** - 根据需求选择 Team 模板
3. **初始化项目文档** - 更新状态文档
4. **开始工作** - 创建第一个任务

---

## 📖 使用模式

### 模式 1: PM Agent 独立工作

适用于简单任务：

```bash
# 启动 PM Agent
./start-pm.sh

# PM Agent 通过 task 工具启动临时 agent 执行任务
```

### 模式 2: Agent Team 协作

适用于复杂项目：

```bash
# 1. PM Agent 设计 Team 结构
# 2. 从 _templates/ 创建 Team
# 3. 分配任务给 Team
# 4. Team 执行并报告
# 5. PM Agent 验收并继续
```

**示例流程**：

```
Human: "开发一个 CSV 数据处理工具"
    ↓
PM Agent: 理解需求，决定需要 Core Team
    ↓
PM Agent: 从 _templates/core-team 创建 agents/csv-core/
    ↓
PM Agent: 创建任务 tasks/csv-core-task-001.md
    ↓
PM Agent: 启动 Core Team
    opencode run --agent csv-core "任务..."
    ↓
Core Team: 执行任务，写入 reports/csv-core-report-001.md
    ↓
PM Agent: 读取报告，验收成果
    ↓
PM Agent: 继续下一步或报告给 Human
```

---

## 🎯 PM Agent 核心能力

### 三级文档体系

```
Level 0 - 必需层 (CATCH_UP.md) <50行
  └─ 启动时读取，了解当前状态

Level 1 - 按需层 (ESSENTIALS.md, WORKFLOW.md) <100行
  └─ 工作时按需读取

Level 2 - 参考层 (guides/, experiences/, archive/)
  └─ 遇到问题时参考
```

**效果**：
- Context 使用降低 93%
- 启动时间减少 80%
- 信息利用率提升 325%

### 质量门控

PM Agent 具备**元认知能力**：
- 评估自己的确定性
- 低确定性时主动请求帮助
- 明确说明不确定性
- 必要时请求 Human 介入

### 模板化团队

提供 5 种 Team 模板：

| 模板 | 职责 | 适用场景 |
|------|------|----------|
| Core Team | 数据处理、工具开发 | 数据处理项目 |
| AI Team | 向量嵌入、语义搜索 | AI/ML 项目 |
| Test Team | 测试、质量保证 | 需要测试的项目 |
| Integration Team | 系统集成 | 需要集成的项目 |
| Research Team | 理论研究 | 研究型项目 |

---

## 📚 文档导航

### 核心文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 初始化指南 | `agents/pm/INIT.md` | 首次启动必读 ⭐ |
| 启动文档 | `agents/pm/CATCH_UP.md` | 当前状态 |
| 核心指南 | `agents/pm/ESSENTIALS.md` | 详细工作规范 |
| 工作流程 | `agents/pm/WORKFLOW.md` | Agent 管理流程 |

### 模板文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 模板指南 | `agents/_templates/TEMPLATE-GUIDE.md` | 如何使用模板 ⭐ |
| Core Team | `agents/_templates/core-team/` | 数据处理模板 |
| AI Team | `agents/_templates/ai-team/` | AI 模板 |
| Test Team | `agents/_templates/test-team/` | 测试模板 |
| Integration Team | `agents/_templates/integration-team/` | 集成模板 |
| Research Team | `agents/_templates/research-team/` | 研究模板 |

### 技能文档

| 文档 | 路径 | 说明 |
|------|------|------|
| Git 工作流 | `framework/skills/workflow/git-workflow.md` | 标准 Git 流程 |
| 代码审查 | `framework/skills/workflow/review-process.md` | Review 标准 |
| 质量门控 | `framework/skills/decision-support/quality-gate.md` | 质量评估 |

### 实践经验

| 文档 | 路径 | 说明 |
|------|------|------|
| 经验库索引 | `archive/README.md` | 实践经验说明 |
| SG-AgentTeam 经验 | `archive/sg-agentteam-experiences/` | 历史经验参考 |
| Knowledge-Assistant 经验 | `archive/knowledge-assistant-experiences/` | v1.1实战经验 ⭐ |

---

## 🆕 v1.1.0 新特性

### 验证的工作模式

v1.1.0 版本通过 **knowledge-assistant-dev** 项目验证了以下核心工作模式：

#### 1. 并行启动多个Agent

**场景**: 多个独立任务需要并行执行

**方法**:
```bash
# 并行启动多个Agent
opencode run --agent core "任务A..." > logs/core.log 2>&1 &
opencode run --agent ai "任务B..." > logs/ai.log 2>&1 &
opencode run --agent integration "任务C..." > logs/integration.log 2>&1 &
```

**效果**:
- ✅ 开发周期从6周缩短到3天
- ✅ PM Team工作量降低80%
- ✅ 充分利用并行能力

详见: [并行启动Agent经验](agents/pm/experiences/parallel-agent-launch-20260308.md)

#### 2. 任务文件 + 报告文件机制

**场景**: PM Agent与Team Agent的信息交换

**方法**:
```
tasks/
  ├── core-task.md      # PM Agent创建
  ├── ai-task.md
  └── integration-task.md

reports/
  ├── core-report.md    # Team Agent生成
  ├── ai-report.md
  └── integration-report.md
```

**优势**:
- 任务描述完整，避免理解偏差
- 报告格式统一，便于汇总
- 历史记录可追溯

#### 3. 被动接收报告模式

**原则**:
- ❌ 不主动轮询Agent进度
- ✅ 等待Agent生成报告文件
- ✅ 用户询问时检查reports/目录

**效果**: 减少PM Team干预，Agent自主完成

#### 4. 权限配置最佳实践

**问题**: 非交互模式下权限被自动拒绝

**解决**:
```json
{
  "agent": {
    "core": {
      "permission": {
        "edit": "allow"  // 必须为allow
      }
    }
  }
}
```

### 实战数据

| 指标 | 目标 | 实际 | 提升 |
|------|------|------|------|
| 开发周期 | 6周 | 3天 | 93% ⬇️ |
| 测试覆盖率 | >80% | 91.7% | 15% ⬆️ |
| PM工作量 | 高 | 低 | 80% ⬇️ |
| 并行任务数 | 1 | 3-5 | 300% ⬆️ |

### 完整案例

**项目**: [Knowledge Assistant](https://github.com/Sonnet0524/knowledge-assistant)  
**版本**: v1.1.0 → v1.2.0  
**详情**: [archive/knowledge-assistant-experiences/](archive/knowledge-assistant-experiences/)

---

## 🛠️ 创建新 Team

### 快速流程

```bash
# 1. 选择合适的模板
cp -r agents/_templates/core-team agents/my-team

# 2. 定制 AGENTS.md
vim agents/my-team/AGENTS.md
# - 修改 description
# - 调整模块边界
# - 更新行为准则

# 3. 创建 CATCH_UP.md
touch agents/my-team/CATCH_UP.md

# 4. 配置 memory-index.yaml
vim framework/memory-index.yaml
# 添加 my-team 配置

# 5. 注册到 opencode.json
vim opencode.json
# 添加 my-team agent

# 6. 创建启动脚本
cp start-pm.sh start-my-team.sh
vim start-my-team.sh
# 修改 agent 名称

# 7. 更新项目文档
vim agents/pm/CATCH_UP.md
# 在 Team Structure 中添加 my-team
```

详细指南：[TEMPLATE-GUIDE.md](agents/_templates/TEMPLATE-GUIDE.md)

---

## 🎓 最佳实践

### DO ✅

- ✅ 首次启动阅读 `INIT.md`
- ✅ 每次启动阅读 `CATCH_UP.md`
- ✅ 主动启动 Agent，不等待
- ✅ 不轮询 Agent 状态
- ✅ 及时更新文档
- ✅ 沉淀经验到 `experiences/`
- ✅ 关键决策前请求 Human 确认

### DON'T ❌

- ❌ 跳过初始化流程
- ❌ 主动检查 Agent 进度
- ❌ 直接修改业务代码
- ❌ 忽略质量门控
- ❌ 不做经验总结

---

## 🔄 工作流程示例

### 场景：新项目启动

```
Day 1: 初始化
├── Human 启动 PM Agent
├── PM Agent 读取 INIT.md
├── PM Agent 询问项目目标
├── Human: "开发知识管理系统"
└── PM Agent 设计 Team 结构

Day 2: 团队组建
├── PM Agent 创建 Core Team（数据处理）
├── PM Agent 创建 AI Team（语义搜索）
├── PM Agent 创建 Test Team（质量保证）
└── 更新所有配置和文档

Day 3: 开始开发
├── PM Agent 分配任务给 Core Team
├── Core Team 开发数据模块
├── PM Agent 分配任务给 AI Team
└── AI Team 开发搜索模块

Day 4: 验收和继续
├── PM Agent 验收 Core Team 成果
├── PM Agent 验收 AI Team 成果
├── PM Agent 分配集成任务
└── 继续迭代...
```

---

## 📊 对比：传统 vs PM Agent

| 维度 | 传统开发 | PM Agent |
|------|---------|----------|
| 项目管理 | 需要专职 PM | Agent 自动管理 |
| 任务分配 | 人工分配 | 自动分配和跟踪 |
| 进度跟踪 | 会议/邮件 | 文档化自动跟踪 |
| 知识沉淀 | 靠个人记录 | 系统化经验库 |
| 团队协作 | 人工协调 | Agent 自动协调 |
| 可扩展性 | 受限于人力 | 动态创建 Team |

---

## 🤝 贡献

欢迎贡献：
- 新的 Team 模板
- 最佳实践文档
- 经验总结
- Bug 修复

---

## 📄 许可证

AGPL v3 License - 详见 LICENSE 文件

---

## 🔗 相关资源

- [SG-AgentTeam](https://github.com/Sonnet0524/SG-AgentTeam) - 原始项目
- [OpenCode](https://opencode.ai) - Agent 执行框架
- [Agent Team 设计方法论](agents/_templates/TEMPLATE-GUIDE.md)

---

**维护者**: Sonnet.G  
**创建日期**: 2026-03-08  
**版本**: 1.0.0

---

## 🚀 开始使用

准备好开始了吗？

```bash
./start-pm.sh
```

PM Agent 会引导你完成初始化！
