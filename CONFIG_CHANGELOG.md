# OpenCode 配置修改日志

## 2026-03-09: 修复配置验证失败问题

### 问题

**错误信息**:
```
Configuration is invalid at D:\opencode\github\agent-team-template\opencode.json
↳ Unrecognized key: "_comment"
```

**根本原因**: OpenCode 不支持 `_comment` 字段，导致配置验证失败。

---

### 修复内容

#### 1. 删除 `_comment` 字段

**修改文件**: `opencode.json`

**修改前**:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "pm": { ... }
  },
  "_comment": {
    "permission_guide": {
      "interactive_mode": "edit: 'ask' - PM Agent交互式启动时可以询问用户",
      "non_interactive_mode": "edit: 'allow' - Team Agent后台启动时必须为allow",
      "example": {
        "core": {
          "permission": {
            "edit": "allow",
            "bash": {
              "pytest *": "allow",
              "git push": "ask"
            }
          }
        }
      }
    }
  }
}
```

**修改后**:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "pm": { ... }
  }
}
```

---

### 设计理念说明

#### 为什么保留自定义目录结构？

**核心理念**: **兼容性优先** - 自定义结构 + 显性指定 = 最大兼容性

**当前配置模式**:
```
agent-team-template/
├── opencode.json
│   └── agent.pm.prompt: "{file:./agents/pm/AGENTS.md}"
│   └── agent.pm.skills: [...]  (自定义字段)
│   └── agent.pm.memory_index: "framework/memory-index.yaml"  (自定义字段)
├── agents/pm/                    (自定义目录)
│   ├── AGENTS.md
│   ├── CATCH_UP.md
│   └── INIT.md
└── framework/skills/             (自定义目录)
    └── workflow/git-workflow.md
```

#### 优势分析

| 维度 | 自定义结构 + 显性指定 | 标准 `.opencode/` 目录 |
|------|---------------------|----------------------|
| **兼容性** | ⭐⭐⭐⭐⭐ 支持多工具 | ⭐⭐⭐ OpenCode 专用 |
| **可读性** | ⭐⭐⭐⭐⭐ 路径显式声明 | ⭐⭐⭐⭐ 依赖约定 |
| **维护性** | ⭐⭐⭐⭐ 集中配置 | ⭐⭐⭐ 分散配置 |
| **标准性** | ⭐⭐⭐ 部分非标准 | ⭐⭐⭐⭐⭐ 完全标准 |
| **工具支持** | ⭐⭐⭐⭐ 通用性强 | ⭐⭐⭐⭐⭐ OpenCode 原生 |

#### 关键优势

1. **框架独立性**
   - 不绑定特定工具（OpenCode、Claude、Cursor等）
   - 配置文件可以被多种工具复用
   - 便于迁移到其他 Agent 平台

2. **显性优于隐性**
   - 路径在配置中明确声明
   - 不依赖隐式的目录约定
   - 更容易理解和维护

3. **历史兼容性**
   - 保持现有项目结构
   - 降低迁移成本
   - 平滑演进

4. **团队协作友好**
   - 配置集中在一个文件
   - 目录结构清晰可见
   - 新成员易于理解

---

### 自定义字段说明

#### `skills` 字段

**定义**:
```json
"skills": [
  "framework/skills/workflow/git-workflow.md",
  "framework/skills/workflow/review-process.md",
  "framework/skills/decision-support/quality-gate.md"
]
```

**说明**:
- ⚠️ **非 OpenCode 标准字段**（OpenCode 标准通过 `.opencode/skills/<name>/SKILL.md` 定义）
- ✅ OpenCode 允许自定义字段（`additionalProperties: {}`）
- 📝 用于项目内部的技能管理和文档引用
- 🔧 可能被自定义扩展处理（如 PM Agent 的工作流）

#### `memory_index` 字段

**定义**:
```json
"memory_index": "framework/memory-index.yaml"
```

**说明**:
- ⚠️ **非 OpenCode 标准字段**
- 📝 用于定义 Agent 的记忆索引配置
- 🔧 被 Agent Team Framework 的记忆系统使用

---

### 注释信息迁移

**原有 `_comment` 字段的内容已迁移至**:

1. **权限配置说明** → `agents/pm/ESSENTIALS.md`
   - 交互式启动说明
   - 后台启动说明
   - 权限配置示例

---

### 验证结果

**修复前**:
```
Configuration is invalid
↳ Unrecognized key: "_comment"
```

**修复后**:
```
✅ 配置验证通过
```

---

### 参考资料

- [OpenCode 配置标准研究报告](../agent-team-research/knowledge-base/research/opencode-config-standard-20260309.md)
- [OpenCode 官方文档](https://opencode.ai/docs/config/)
- [OpenCode JSON Schema](https://opencode.ai/config.json)

---

**修改人**: Research Agent (L1)  
**修改日期**: 2026-03-09  
**影响项目**: course-assistant, agent-team-template
