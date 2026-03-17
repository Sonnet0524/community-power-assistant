# PM Agent - 工作流程

> 📖 **核心文档** - Agent 管理和任务分配的标准流程

---

## 🎯 核心理念

```
主动启动 + 不轮询 + 被动接收
```

### 三大原则

1. ✅ **主动启动 Agent** - 分配任务后立即启动，不犹豫
2. ❌ **不轮询状态** - 不主动检查 Agent 进度，不浪费资源
3. ✅ **被动接收报告** - Agent 完成后自动写入报告，PM 按需读取

---

## 📋 标准工作流程

### 完整流程图

```
Human 询问/指示
        ↓
PM Agent 分析任务
        ↓
决定工作模式
        ↓
    ┌───────┴───────┐
    │               │
模式A: 独立执行    模式B: Team 执行
(简单任务)          (复杂任务)
    │               │
创建任务文件    创建任务文件
    │               │
启动临时 Agent  启动 Team Agent
    │               │
等待完成        后台执行
    │               │
验收结果        PM 继续其他工作
                    ↓
                Agent 完成
                    ↓
                写入报告
                    ↓
                PM 读取报告
                    ↓
                验收结果
```

---

## 🔄 模式 A: 独立执行（简单任务）

适用于：简单、一次性、不需要专门 Team 的任务

### 步骤

```bash
# 1. 创建任务文件
mkdir -p tasks reports logs

cat > tasks/simple-task.md << 'EOF'
# Task: [任务名称]

## Requirements
[具体要求]

## Output
完成后在 reports/simple-report.md 写入结果
EOF

# 2. 启动临时 Agent（使用 task 工具）
task "读取 tasks/simple-task.md 并完成，结果写入 reports/simple-report.md"

# 3. 等待完成（task 工具会等待）

# 4. 读取报告
cat reports/simple-report.md

# 5. 验收结果
```

### 适用场景

- 文档整理
- 简单查询
- 格式转换
- 数据分析（简单）

---

## 🔄 模式 B: Team 执行（复杂任务）

适用于：需要专业 Team 处理的复杂任务

### 步骤 1: 创建任务文件

```bash
# 创建目录
mkdir -p tasks reports logs

# 创建任务文件
cat > tasks/core-data-processing.md << 'EOF'
# Task: 数据处理模块开发

## Background
项目需要处理用户上传的 CSV 文件

## Requirements
1. 实现 CSV 解析器
2. 支持大文件分块处理
3. 错误行记录和报告

## Constraints
- 内存限制：单次处理不超过 100MB
- 支持中文编码（UTF-8, GBK）

## Acceptance Criteria
- [ ] 能正确解析标准 CSV 文件
- [ ] 能处理 1GB+ 的大文件
- [ ] 错误处理完善
- [ ] 单元测试覆盖率 >80%

## Output
完成后在 reports/core-data-processing-report.md 写入：
- 实现代码
- 测试用例
- 使用文档
- 遇到的问题

---
**Priority**: P0
**Assigned to**: Core Team
EOF
```

### 步骤 2: 启动 Team Agent

```bash
# 方法 1: 使用 opencode run（推荐）
opencode run --agent core "读取 tasks/core-data-processing.md 中的任务并完成，结果写入 reports/core-data-processing-report.md" > logs/core.log 2>&1 &

# 方法 2: 使用启动脚本（如果已创建）
./start-core.sh

# 注意：& 表示后台运行，PM Agent 不等待
```

### 步骤 3: PM Agent 继续其他工作

启动后，PM Agent：
- 不检查日志
- 不查询状态
- 继续处理其他任务或等待 Human 询问

### 步骤 4: Team Agent 完成并写入报告

Team Agent 执行完成后，自动写入 `reports/core-data-processing-report.md`

### 步骤 5: PM Agent 读取报告（被动触发）

报告生成后，PM Agent 在以下时机读取：
- Human 询问进度时
- PM Agent 需要继续下一步时
- 定期检查（如每日）

```bash
cat reports/core-data-processing-report.md
```

### 步骤 6: 验收结果

根据 Acceptance Criteria 检查：
- ✅ 全部完成 → 更新状态，继续下一步
- 🟡 部分完成 → 要求补充或调整
- ❌ 未完成 → 创建新任务继续

---

## 🏗️ 创建新 Team

### 场景

当现有 Team 无法满足需求时，需要创建新 Team。

### 流程

```bash
# 1. 选择合适的模板
ls agents/_templates/

# 2. 复制模板
cp -r agents/_templates/core-team agents/data-processing-team

# 3. 定制 AGENTS.md
vim agents/data-processing-team/AGENTS.md
# - 修改 description
# - 调整模块边界
# - 更新行为准则

# 4. 配置 memory-index.yaml
vim framework/memory-index.yaml
# 添加 data-processing-team 的配置

# 5. 注册到 opencode.json
vim opencode.json
# 在 agents 部分添加配置

# 6. 创建启动脚本
cp start-pm.sh start-data-processing.sh
vim start-data-processing.sh
# 修改 agent 名称

# 7. 更新 CATCH_UP.md
# 在 Team Structure 中添加新 Team

# 8. 更新 agent-status.md
# 添加新 Team 的状态行
```

### 新 Team 配置模板

```yaml
# memory-index.yaml 中的配置示例
data-processing:
  identity:
    path: "agents/data-processing-team/AGENTS.md"
    priority: P0
    estimated_tokens: 5000
  state:
    path: "agents/data-processing-team/CATCH_UP.md"
    priority: P1
    estimated_tokens: 2000
  experiences:
    path: "agents/data-processing-team/experiences/"
    priority: P3
    load_mode: "on-demand"
```

```json
// opencode.json 中的配置示例
{
  "agents": {
    "data-processing": {
      "path": "agents/data-processing-team/AGENTS.md",
      "skills": [
        "framework/skills/workflow/git-workflow.md"
      ]
    }
  }
}
```

---

## 📊 多 Agent 并行管理

### 并行启动多个 Team

```bash
# 启动 Core Team
opencode run --agent core "任务1..." > logs/core.log 2>&1 &

# 启动 AI Team
opencode run --agent ai "任务2..." > logs/ai.log 2>&1 &

# 启动 Test Team
opencode run --agent test "任务3..." > logs/test.log 2>&1 &
```

### 依赖管理

如果 Agent B 依赖 Agent A 的结果：

```bash
# 1. 先启动 Agent A
opencode run --agent core "任务A..." > logs/core.log 2>&1 &

# 2. 等待 Agent A 完成（读取报告）
# PM Agent 不需要主动等待，只需在需要时检查

# 3. 确认 Agent A 完成后，启动 Agent B
if [ -f reports/core-task-a-report.md ]; then
    opencode run --agent test "任务B..." > logs/test.log 2>&1 &
fi
```

---

## 📝 任务文件命名规范

### 文件名格式

```
tasks/{team}-{brief-description}-{number}.md

示例：
- tasks/core-csv-parser-001.md
- tasks/ai-semantic-search-001.md
- tasks/test-integration-001.md
```

### 报告文件名

```
reports/{team}-{brief-description}-{number}-report.md

示例：
- reports/core-csv-parser-001-report.md
```

---

## ⚠️ 重要注意事项

### ✅ 必须做

1. ✅ **启动前创建任务文件** - 明确任务要求
2. ✅ **使用后台运行（`&`）** - 不阻塞 PM Agent
3. ✅ **重定向日志** - `> logs/{team}.log 2>&1`
4. ✅ **在 message 中明确指出报告文件位置**
5. ✅ **等待 Agent 报告** - 不主动检查进度

### ❌ 禁止做

1. ❌ **使用 task 工具启动 Team Agent** - task 只用于临时 agent
2. ❌ **轮询 Agent 状态** - 不要 `tail -f` 持续查看日志
3. ❌ **使用交互式启动** - 不要用 `opencode --agent <name>`
4. ❌ **忘记创建报告目录** - 确保 `reports/` 存在
5. ❌ **直接修改 Team 的代码** - 只 review，不修改

---

## 🎓 完整示例

### 场景：数据处理项目

#### 第 1 天：项目初始化

```bash
# Human 启动 PM Agent
./start-pm.sh

# PM Agent 读取 INIT.md
# 询问 Human 项目目标
# Human: "开发一个 CSV 数据处理工具"

# PM Agent 决定需要：Core Team
# 创建 Core Team
cp -r agents/_templates/core-team agents/core
# 配置 memory-index.yaml 和 opencode.json
# 更新 CATCH_UP.md
```

#### 第 2 天：分配第一个任务

```bash
# PM Agent 创建任务
cat > tasks/core-csv-parser-001.md << 'EOF'
# Task: CSV 解析器实现

## Requirements
1. 实现 CSV 文件读取
2. 支持 UTF-8 和 GBK 编码
3. 错误处理

## Acceptance Criteria
- [ ] 单元测试 >80%
- [ ] 能处理 100MB+ 文件

## Output
reports/core-csv-parser-001-report.md
EOF

# 启动 Core Team
opencode run --agent core "读取 tasks/core-csv-parser-001.md 并完成，结果写入 reports/core-csv-parser-001-report.md" > logs/core.log 2>&1 &

# PM Agent 继续其他工作...
```

#### 第 3 天：验收结果

```bash
# PM Agent 读取报告
cat reports/core-csv-parser-001-report.md

# 检查 Acceptance Criteria
# ✅ 全部通过

# 更新状态
vim status/agent-status.md
# 标记 Core Team 任务完成

# 更新 CATCH_UP.md
# 记录已完成任务

# 创建下一个任务...
```

---

## 📚 参考资源

- [PM Agent 身份定义](AGENTS.md)
- [核心指南](ESSENTIALS.md)
- [Agent 模板指南](../_templates/TEMPLATE-GUIDE.md)
- [Git 工作流程](../../framework/skills/workflow/git-workflow.md)
- [代码审查流程](../../framework/skills/workflow/review-process.md)

---

**维护者**: PM Agent  
**最后更新**: 2026-03-08
