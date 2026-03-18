# OpenClaw Skills 开发标准

> 本文档定义了 Field Info Agent 项目中 OpenClaw Skills 的开发规范，所有开发人员必须严格遵守。

**版本**: 1.0.0  
**生效日期**: 2026-03-18  
**适用范围**: Field Info Agent 所有 Skill 开发

---

## 📋 核心原则

### Skills vs Tools 的区别

| 组件 | 格式 | 职责 | 位置 |
|------|------|------|------|
| **Skills** | Markdown (`SKILL.md`) | 定义 Agent 的"能力"和"行为指南" | `workspace/skills/<name>/SKILL.md` |
| **Tools** | TypeScript/JavaScript | 定义具体的"可执行功能" | OpenClaw 内置或自定义插件 |
| **Config** | YAML (`openclaw.config.yaml`) | 定义触发器、运行时配置 | 项目根目录 |

### 文件职责划分

```
┌─────────────────────────────────────────────────────────────┐
│                        SKILL.md                              │
│  • 技能名称和描述                                             │
│  • 依赖声明（bins、env、config）                              │
│  • 使用指南和 Prompt 模板                                     │
│  • 工作流程说明                                               │
│  • 示例代码（伪代码/TypeScript）                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    openclaw.config.yaml                      │
│  • Skill 启用/禁用                                            │
│  • 触发器定义（triggers）                                     │
│  • 运行时配置（config）                                       │
│  • LLM Prompt 配置                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Tools (TypeScript)                         │
│  • 具体可执行功能                                             │
│  • 数据库操作                                                 │
│  • API 调用                                                   │
│  • 文件处理                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 SKILL.md 格式规范

### 必须遵循的格式

```markdown
---
name: skill-name
description: 简洁的技能描述（一行）
homepage: https://example.com
metadata:
  {
    "openclaw":
      {
        "emoji": "✨",
        "requires": { "bins": ["required-cli"], "env": ["REQUIRED_API_KEY"], "config": ["path.to.config"] },
        "install": [
          {
            "id": "install-id",
            "kind": "brew|node|go|uv|download",
            ...
          }
        ]
      }
  }
---

# Skill Name

## 概述
[技能的详细说明]

## 使用方法
[具体使用指南]

## 示例
[代码示例和交互示例]
```

### Frontmatter 字段说明

#### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | Skill 名称，使用 kebab-case（如 `vision-analysis`） |
| `description` | string | 简洁描述，建议一行 |

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `homepage` | string | 技能主页 URL |
| `user-invocable` | boolean | 是否暴露为用户斜杠命令，默认 true |
| `disable-model-invocation` | boolean | 是否从模型提示中排除，默认 false |

#### metadata.openclaw 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `emoji` | string | macOS Skills UI 显示的 emoji |
| `homepage` | string | Skills UI 中"网站"链接 |
| `os` | string[] | 支持的平台：`darwin`, `linux`, `win32` |
| `always` | boolean | 始终包含该 Skill（跳过其他条件检查） |
| `requires.bins` | string[] | 必须存在的可执行文件（在 PATH 中） |
| `requires.anyBins` | string[] | 至少一个必须存在的可执行文件 |
| `requires.env` | string[] | 必须存在的环境变量 |
| `requires.config` | string[] | 必须为 truthy 的配置路径 |
| `primaryEnv` | string | 与 `apiKey` 关联的主环境变量名 |
| `install` | object[] | 安装器规格数组 |

### ⚠️ 重要限制

1. **metadata 必须是单行 JSON 对象**
   ```markdown
   # ✅ 正确
   metadata:
     {
       "openclaw":
         {
           "emoji": "✨",
           "requires": { "bins": ["gemini"] }
         }
     }
   
   # ❌ 错误（多行 YAML 格式）
   metadata:
     openclaw:
       emoji: "✨"
       requires:
         bins:
           - gemini
   ```

2. **requires 不支持以下字段**
   - ❌ `tools` - 工具依赖应在 SKILL.md 内容中说明
   - ❌ `channels` - 渠道依赖应在 openclaw.config.yaml 中配置
   - ❌ `triggers` - 触发器应在 openclaw.config.yaml 中配置

3. **category 不是官方字段**
   - 如果需要分类，使用自定义字段或文件夹组织

---

## 🔧 openclaw.config.yaml 配置规范

### Skills 配置部分

```yaml
skills:
  # Skill 名称（对应 SKILL.md 中的 name）
  skill_name:
    enabled: true                    # 启用/禁用
    priority: high                   # 优先级：high | medium | low
    
    # 触发器定义
    triggers:
      - type: message_type           # 消息类型触发
        value: "image"
      - type: intent                 # 意图触发
        patterns:
          - "关键词1"
          - "关键词2"
      - type: command                # 命令触发
        pattern: "分析.*照片"
      - type: event                  # 事件触发
        value: "collection_completed"
    
    # 运行时配置
    config:
      auto_analyze: true
      batch_size: 10
      timeout: 300
```

### Tools 配置部分

```yaml
tools:
  tool_name:
    enabled: true
    config:
      host: "${ENV_VAR}"
      port: 5432
      # 具体配置...
```

### LLM 配置部分

```yaml
llm:
  default_provider: kimi
  
  kimi:
    api_key: "${KIMI_API_KEY}"
    model: "kimi-k2.5"
    
    # 多模态能力配置
    vision_analysis:
      enabled: true
      system_prompt: |
        你是电力设备检测专家...
      prompts:
        single_image: |
          请分析这张照片...
```

---

## 📁 项目目录结构

```
field-info-agent/
├── AGENTS.md                    # Agent 角色定义
├── openclaw.config.yaml         # OpenClaw 主配置
├── workspace/
│   ├── skills/
│   │   ├── station-work-guide/
│   │   │   └── SKILL.md         # 驻点工作引导技能
│   │   ├── vision-analysis/
│   │   │   └── SKILL.md         # 照片分析技能
│   │   ├── doc-generation/
│   │   │   └── SKILL.md         # 文档生成技能
│   │   └── emergency-guide/
│   │       └── SKILL.md         # 应急处理技能
│   ├── database/
│   │   └── schema.sql           # 数据库 Schema
│   ├── docker-compose.yml       # 基础设施编排
│   └── .env.example             # 环境变量模板
└── tools/                       # 自定义工具（如需要）
    └── custom-tool/
        ├── index.ts
        └── package.json
```

---

## ✅ 开发检查清单

### 创建新 Skill 时

- [ ] SKILL.md 使用正确的 frontmatter 格式
- [ ] metadata 是单行 JSON 对象
- [ ] requires 只包含 `bins`、`env`、`config`、`anyBins`
- [ ] 在 openclaw.config.yaml 中配置 triggers
- [ ] 在 openclaw.config.yaml 中配置运行时 config
- [ ] 提供清晰的 Prompt 模板和使用说明
- [ ] 包含示例代码（伪代码或 TypeScript）

### 代码审查标准

- [ ] SKILL.md 格式符合本文档规范
- [ ] 没有在 SKILL.md 中定义 triggers
- [ ] 没有在 requires 中使用 tools 或 channels
- [ ] 配置文件路径和名称正确
- [ ] 环境变量已在 .env.example 中声明

---

## 📚 参考资源

- [OpenClaw 官方文档 - Skills](https://docs.openclaw.ai/tools/skills)
- [AgentSkills 规范](https://agentskills.io)
- [OpenClaw GitHub - skills 目录](https://github.com/openclaw/openclaw/tree/main/skills)

---

## 🔄 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-03-18 | 初始版本，定义 OpenClaw Skills 开发标准 |

---

**维护者**: PM Agent  
**审核状态**: ✅ 已确认  
**强制执行**: 所有 Skill 开发必须遵守此标准
