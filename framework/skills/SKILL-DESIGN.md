# Skill 设计规范

**版本**: 2.0  
**更新日期**: 2026-03-11  
**适用范围**: 所有Agent Team项目的skills建设

---

## 一、Skills vs Tools 边界

### 1.1 核心定义

| 维度 | Skills | Tools |
|------|--------|-------|
| **本质** | 知识/指令 | 可执行函数 |
| **形式** | Markdown + YAML | Python代码 |
| **作用** | 告诉Agent"怎么做" | 让Agent"执行操作" |
| **加载** | Agent学习阶段 | Agent执行阶段 |
| **调用** | Agent阅读理解 | Agent直接function call |

### 1.2 类比

```
Skills = 教科书/操作手册（告诉Agent如何使用工具）
Tools  = 实际的工具/机器（Agent运行时直接调用）
```

### 1.3 使用场景

| 场景 | 使用Skills | 使用Tools |
|------|-----------|-----------|
| 告诉Agent如何使用搜索 | ✅ | ❌ |
| 实际执行搜索操作 | ❌ | ✅ |
| 提供API调用示例 | ✅ (scripts) | ❌ |
| 执行确定性计算 | ✅ (scripts) | ✅ (也可以) |

---

## 二、目录结构

```
skill-name/
├── SKILL.md (必需, <200行)
│   ├── YAML frontmatter (仅4字段)
│   └── Markdown指令
└── Bundled Resources (可选)
    ├── scripts/     — 可执行代码（确定性任务、API调用）
    └── references/  — 详细文档（参数、错误处理、最佳实践）
```

---

## 三、SKILL.md 规范

### 3.1 Frontmatter（仅4字段）

```yaml
---
name: skill-name
description: 功能描述 + 触发条件（必须包含触发条件）
trigger: on_demand
tags: tag1, tag2
---
```

### 3.2 行数限制

- **SKILL.md**: <200行
- **scripts/*.py**: <80行/文件
- **references/*.md**: 无限制（按需加载）

---

## 四、Scripts 设计规范

### 4.1 目录结构（扁平化）

```
scripts/
├── __init__.py
├── config.py      # API Key配置（<50行）
├── api.py         # 外部API调用（<80行）
├── process.py     # 数据处理（<80行，可选）
└── format.py      # 输出格式化（<60行，可选）
```

**原则**：扁平化，不使用子目录。

### 4.2 API Key 安全

**只从环境变量读取**，不存储到文件：

```python
import os

def get_api_key(name: str) -> str:
    key = os.environ.get(name)
    if not key:
        raise ValueError(f"""
API Key未配置: {name}

配置方法：
  export {name}='your-api-key'
  # 或添加到 ~/.bashrc 或 ~/.zshrc
""")
    return key
```

### 4.3 设计原则

| 原则 | 说明 |
|------|------|
| **纯函数** | 避免复杂类设计 |
| **独立运行** | 只依赖Python标准库 |
| **简洁** | 每个文件<80行 |
| **安全** | API Key只从环境变量读取 |

---

## 五、渐进式披露

```
Level 1: Metadata (~100 words)     → 始终在上下文中
Level 2: SKILL.md Body (<200行)   → 触发时加载
Level 3: references/scripts/       → 按需加载
```

---

## 六、创建检查清单

### Frontmatter
- [ ] 只有4个必需字段
- [ ] description包含触发条件
- [ ] name使用kebab-case格式

### Body
- [ ] 总行数<200行
- [ ] 每个段落都值得其token成本
- [ ] 没有README/CHANGELOG等元文档

### Scripts
- [ ] 扁平化目录（无子目录）
- [ ] 每个文件<80行
- [ ] 只依赖Python标准库
- [ ] API Key从环境变量读取

---

## 七、参考来源

- Claude Code Skills: https://code.claude.com/docs/skills
- MCP Protocol: https://modelcontextprotocol.io
- Agno Tools: https://docs.agno.com/agents/tools

---

**维护者**: Research Agent  
**版本**: 2.0
