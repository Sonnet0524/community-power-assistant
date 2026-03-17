---
skill_id: review-process
name: 代码审查流程
description: 标准化的代码审查流程，包括审查维度、问题分类、意见模板和最佳实践
version: 2.0.0
skill_type: workflow
category: collaboration
triggers:
  - "代码审查"
  - "Code Review"
  - "审查代码"
  - "检查代码"
  - "Review"
trigger_patterns:
  - "(代码|code)\\s*(审查|review)"
  - "review\\s*(代码|code)"
  - "检查\\s*(代码|实现)"
tags:
  - code-review
  - quality-assurance
  - collaboration
  - best-practices
  - team-workflow
---

# 代码审查流程

## 概述

提供标准化的代码审查（Code Review）流程，包括审查维度、问题分类、意见模板和最佳实践，帮助团队提高代码质量和协作效率。

## 能力范围

### ✅ Can Do

- 提供系统化的代码审查流程
- 指导审查者如何发现问题
- 提供标准的审查意见模板
- 帮助评估代码质量和风险
- 指导处理审查反馈
- 提供审查检查清单

### ❌ Cannot Do

- 自动执行代码审查（需要人工判断）
- 强制修改代码
- 替代团队的审查标准
- 解决团队间的审查分歧
- 执行代码测试

## 使用场景

### Pattern 1: 标准审查流程

**User Intent**: 收到代码审查请求，需要按照标准流程进行审查

**Trigger Phrases**:
- "审查这个PR"
- "代码审查流程"
- "如何做Code Review"
- "审查代码"

**Execution Flow**:
1. 快速浏览获取整体印象
2. 详细审查各维度
3. 记录和分类问题
4. 撰写审查意见
5. 确认审查结论

**Example Interaction**:
```
User: "我收到了一个PR审查请求，如何进行代码审查？"

Agent:
我来指导你进行标准的代码审查。

## 审查流程

### 第一步：快速浏览（5-10分钟）

**目标**: 获得整体印象

**检查项**:
- [ ] PR描述是否清晰？
- [ ] 变更范围是否合理？（建议<400行）
- [ ] 是否有明显的架构问题？
- [ ] 测试是否充分？

**决策**:
- PR太大 → 建议拆分
- 描述不清 → 要求补充
- 架构问题 → 先讨论架构

### 第二步：详细审查（15-30分钟）

**维度1: 正确性**
```markdown
- [ ] 逻辑是否正确？
- [ ] 边界条件是否处理？
- [ ] 错误处理是否完善？
- [ ] 并发安全（如适用）？
```

**维度2: 可读性**
```markdown
- [ ] 命名是否清晰？
- [ ] 函数是否简短（<50行）？
- [ ] 注释是否必要且准确？
- [ ] 代码组织是否合理？
```

**维度3: 可维护性**
```markdown
- [ ] 是否遵循DRY原则？
- [ ] 耦合度是否合适？
- [ ] 是否易于测试？
- [ ] 是否易于扩展？
```

**维度4: 性能**
```markdown
- [ ] 算法复杂度是否合理？
- [ ] 是否有明显的性能问题？
- [ ] 资源使用是否合理？
```

**维度5: 安全性**
```markdown
- [ ] 是否有注入风险？
- [ ] 是否有越权风险？
- [ ] 敏感信息是否泄露？
```

### 第三步：记录问题

**问题分类**:

| 标记 | 级别 | 含义 | 处理方式 |
|------|------|------|----------|
| 🔴 | Blocker | 必须修复 | 不修复不能合并 |
| 🟡 | Major | 建议修复 | 最好修复，可讨论 |
| 🟢 | Minor | 小问题 | 可选修复 |
| 💡 | Nitpick | 吹毛求疵 | 仅供参考 |

### 第四步：撰写审查意见

```markdown
## 总体评价
整体实现良好，逻辑清晰，测试覆盖充分。

## 🔴 Blockers（必须修复）
- [ ] 第45行可能导致空指针异常
  - 建议：添加null检查

## 🟡 Major（建议修复）
- [ ] 第120行使用了魔法数字
  - 建议：提取为常量

## 🟢 Minor（可选修复）
- 变量名`data`可以更具体一些

## 👍 Highlights（亮点）
- 错误处理做得很好
- 测试覆盖率很高

## 结论
- [ ] 需要修改（有未解决的blocker）
```

### 第五步：提交审查

```bash
# 使用GitHub CLI
gh pr review <pr-number> \
  --request-changes \
  --body "[审查意见]"
```

## 审查时间建议

- **简单PR** (<100行): 10-15分钟
- **中等PR** (100-400行): 20-30分钟
- **复杂PR** (>400行): 建议拆分

需要我帮你生成审查意见模板吗？
```

---

### Pattern 2: 处理审查反馈

**User Intent**: 作为代码作者，收到审查意见后如何处理

**Trigger Phrases**:
- "审查意见怎么处理"
- "回应代码审查"
- "修改代码后的审查"
- "审查反馈"

**Execution Flow**:
1. 认真阅读所有意见
2. 分类处理意见
3. 修改代码
4. 回复审查者
5. 请求重新审查

**Example Interaction**:
```
User: "收到审查意见，有几个blocker需要修复"

Agent:
我来指导你处理审查反馈。

## 处理流程

### 1. 分类处理意见

**优先级排序**:
1. 🔴 Blocker - 立即处理
2. 🟡 Major - 尽快处理
3. 🟢 Minor - 视情况处理
4. 💡 Nitpick - 可选处理

### 2. 修复Blocker问题

**示例问题**: 第45行可能导致空指针异常

```typescript
// 问题代码
function processUser(user) {
  return user.name.toUpperCase();
}

// 修复方案1: 添加null检查
function processUser(user) {
  if (!user) {
    throw new Error('User is required');
  }
  return user.name.toUpperCase();
}

// 修复方案2: 提供默认值
function processUser(user) {
  return user?.name?.toUpperCase() ?? 'Unknown';
}
```

### 3. 回复审查者

**回复模板**:
```markdown
感谢审查！我已经修复了所有blocker：

## 已修复
- ✅ 第45行：添加了null检查
- ✅ 第120行：提取了魔法数字

## 讨论点
- 关于第80行的实现方式，我有不同的想法...

## 未处理
- 🟢 变量命名：暂时保持，因为符合项目现有风格
```

### 4. 提交修改

```bash
# 修复代码
git add .
git commit -m "fix: 根据审查意见修复问题

- 添加null检查防止NPE
- 提取魔法数字为常量
- 优化错误处理"

git push origin feature/xxx
```

### 5. 请求重新审查

```bash
# GitHub网页：点击"Re-request review"
# 或使用CLI
gh pr review <pr-number> --comment --body "已修复所有blocker，请重新审查"
```

## 处理审查的心态

### ✅ DO
- 认真对待每条意见
- 不理解时主动询问
- 解释设计决策
- 及时修复问题
- 感谢审查者的时间

### ❌ DON'T
- 防御性回应
- 无视意见
- 延迟修复
- 情绪化反应

需要我帮你审查具体的代码吗？
```

---

### Pattern 3: 审查复杂PR

**User Intent**: 需要审查一个复杂的PR（大改动或架构变更）

**Trigger Phrases**:
- "审查复杂的PR"
- "大改动的代码审查"
- "架构变更审查"
- "大型PR审查"

**Execution Flow**:
1. 评估PR复杂度
2. 制定审查策略
3. 分阶段审查
4. 协作审查
5. 综合评估

**Example Interaction**:
```
User: "这个PR有800行变更，如何高效审查？"

Agent:
大型PR需要系统化的审查策略。

## 复杂PR审查策略

### 1. 评估复杂度

**复杂度指标**:
- 变更行数: 800行 → 高复杂度
- 涉及文件: ?个文件
- 是否重构: 是否改变架构
- 测试覆盖: 是否有充分测试

**建议**: 如果>400行，考虑建议拆分

### 2. 分阶段审查

**阶段1: 架构审查（15分钟）**
```markdown
- [ ] 整体设计是否合理？
- [ ] 是否与现有架构冲突？
- [ ] 是否影响其他模块？
- [ ] 是否需要迁移计划？
```

**阶段2: 核心逻辑审查（30分钟）**
```markdown
- [ ] 核心算法是否正确？
- [ ] 数据流是否清晰？
- [ ] 错误处理是否完善？
- [ ] 性能是否有影响？
```

**阶段3: 边缘情况审查（20分钟）**
```markdown
- [ ] 边界条件处理
- [ ] 异常情况处理
- [ ] 向后兼容性
```

**阶段4: 测试审查（15分钟）**
```markdown
- [ ] 测试覆盖是否充分？
- [ ] 测试用例是否有效？
- [ ] 是否需要补充测试？
```

### 3. 使用工具辅助

```bash
# 查看文件差异统计
git diff --stat main...feature-branch

# 查看特定文件的详细差异
git diff main...feature-branch -- path/to/file

# 只看新增的代码
git diff main...feature-branch --diff-filter=A
```

### 4. 协作审查

**如果PR太大**:
1. **建议拆分**:
   ```markdown
   这个PR较大，建议拆分为多个小PR：
   1. 数据模型变更
   2. API实现
   3. 前端集成
   4. 测试和文档
   ```

2. **分配审查责任**:
   - 审查者A: 后端逻辑
   - 审查者B: 前端UI
   - 审查者C: 测试覆盖

### 5. 综合评估

**审查报告模板**:
```markdown
## 架构评估
[整体架构评价]

## 🔴 Blockers
[必须修复的问题]

## 🟡 Major Issues
[重要问题]

## 📊 测试评估
- 测试覆盖率: ?
- 关键路径测试: ?
- 回归测试: ?

## ⚠️ 风险评估
- 性能影响: ?
- 兼容性风险: ?
- 安全风险: ?

## 💡 建议
[改进建议]

## 结论
- [ ] 批准
- [ ] 需要修改
- [ ] 建议拆分
```

## 大型PR审查技巧

1. **先理解意图** - 阅读PR描述和设计文档
2. **关注架构** - 先看整体，再看细节
3. **使用工具** - 利用差异工具和统计工具
4. **记录进展** - 分多次审查，记录已完成部分
5. **沟通优先** - 复杂问题面对面讨论

需要我帮你制定具体的审查计划吗？
```

## 参数说明

### 必需参数

无（本skill基于用户意图触发）

### 可选参数

#### pr_number
- **Type**: int
- **Default**: `null`
- **Description**: Pull Request编号
- **Example**: `123`

#### review_type
- **Type**: string
- **Default**: `"standard"`
- **Description**: 审查类型
- **Example**: `"quick"`, `"standard"`, `"thorough"`

#### focus_areas
- **Type**: list
- **Default**: `["correctness", "quality", "security"]`
- **Description**: 重点关注领域
- **Example**: `["performance", "security"]`

## 输出格式

### 成功输出

```json
{
  "success": true,
  "review": {
    "pr_number": 123,
    "overall_assessment": "良好，有少量问题需要修复",
    "blockers": [
      {
        "line": 45,
        "file": "src/parser.ts",
        "issue": "可能导致空指针异常",
        "suggestion": "添加null检查"
      }
    ],
    "major_issues": [
      {
        "line": 120,
        "file": "src/utils.ts",
        "issue": "使用魔法数字",
        "suggestion": "提取为常量"
      }
    ],
    "minor_issues": [],
    "highlights": [
      "错误处理做得很好",
      "测试覆盖充分"
    ]
  },
  "decision": "request_changes",
  "execution_time_ms": 1234.56
}
```

### 错误输出

```json
{
  "success": false,
  "error": {
    "error_type": "NotFoundError",
    "message": "PR不存在或无访问权限",
    "suggestion": "确认PR编号和访问权限"
  }
}
```

## 工具函数

### conduct_review

**Purpose**: 执行系统化的代码审查

**Input**:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ReviewParams(BaseModel):
    """审查参数"""
    pr_number: int = Field(
        ...,
        description="PR编号"
    )
    review_type: str = Field(
        default="standard",
        description="审查类型: quick, standard, thorough"
    )
    focus_areas: List[str] = Field(
        default=["correctness", "quality", "security"],
        description="关注领域"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="排除的文件模式"
    )
```

**Output**:
```python
class Issue(BaseModel):
    """问题"""
    line: int
    file: str
    severity: str  # blocker, major, minor, nitpick
    issue: str
    suggestion: str

class ReviewOutput(BaseModel):
    """审查输出"""
    success: bool
    review: dict
    decision: str  # approve, request_changes, comment
    execution_time_ms: float
```

**Calling Convention**:
```python
from framework.skills.workflow.review_process import conduct_review, ReviewParams

# 创建参数
params = ReviewParams(
    pr_number=123,
    review_type="thorough",
    focus_areas=["security", "performance"]
)

# 调用函数
result = conduct_review(params)

# 处理结果
if result.success:
    print(f"决策: {result.decision}")
    for blocker in result.review['blockers']:
        print(f"Blocker: {blocker['issue']}")
```

---

### generate_review_report

**Purpose**: 生成标准化的审查报告

**Input**:
```python
class ReportParams(BaseModel):
    """报告参数"""
    pr_number: int
    overall_assessment: str
    blockers: List[Issue]
    major_issues: List[Issue]
    minor_issues: List[Issue]
    highlights: List[str]
    decision: str
```

**Output**:
```python
class ReportOutput(BaseModel):
    """报告输出"""
    success: bool
    report_markdown: str
    execution_time_ms: float
```

## 最佳实践

### 审查者

#### ✅ Do
- 及时响应审查请求（24小时内）
- 就事论事，针对代码不针对人
- 提供具体的建议，不只是指出问题
- 认可做得好的地方
- 设置时间限制，避免疲劳审查

#### ❌ Don't
- 使用攻击性语言
- 只指出问题不给建议
- 坚持个人偏好
- 延迟审查请求
- 审查时间过长（>1小时）

### 代码作者

#### ✅ Do
- 认真对待每条意见
- 不理解时主动询问
- 解释设计决策
- 及时修复问题
- 感谢审查者的时间

#### ❌ Don't
- 防御性回应
- 无视意见
- 延迟修复
- 提交未测试的代码

## 常见问题

### Q1: 审查意见太尖锐怎么办？

**A**: 记住审查原则：

1. **就事论事** - 针对代码，不针对人
2. **提供方案** - 指出问题的同时给出建议
3. **保持尊重** - 用建设性的语气
4. **可以讨论** - 不确定时可以讨论

**正确示例**:
- ✅ "这里可以考虑使用更高效的数据结构"
- ✅ "建议参考xxx的最佳实践"
- ✅ "第45行可能在边界情况下出错，建议添加检查"

**错误示例**:
- ❌ "这代码写得太烂"
- ❌ "你怎么能这么写"
- ❌ "明显有bug"

---

### Q2: 审查者和作者意见不一致怎么办？

**A**: 按以下步骤处理：

1. **理解对方观点** - 为什么审查者认为有问题？
2. **解释设计决策** - 作者为什么这样实现？
3. **寻找中间方案** - 是否有双方都能接受的方案？
4. **寻求第三方意见** - 邀请其他团队成员参与讨论
5. **记录决策** - 将最终决策记录到文档

**讨论模板**:
```markdown
## 不同意见

**审查者观点**: [问题描述]

**作者观点**: [设计理由]

**讨论结果**: 
- 方案选择: [最终方案]
- 理由: [决策理由]
- 影响: [影响范围]
```

---

### Q3: 如何避免审查疲劳？

**A**: 使用以下策略：

1. **设置时间限制**
   - 单次审查不超过30分钟
   - 超时后休息或分多次审查

2. **建议拆分大PR**
   - 超过400行变更的PR建议拆分
   - 每个PR专注一个功能点

3. **使用工具辅助**
   - 自动化检查：lint、format、type check
   - 静态分析：SonarQube、CodeClimate
   - 自动化测试：CI/CD

4. **轮流审查**
   - 避免同一人连续审查多个PR
   - 团队成员轮流承担审查任务

---

### Q4: 审查发现严重问题怎么办？

**A**: 按严重程度处理：

**Blocker（阻塞问题）**:
- 必须修复才能合并
- 示例：安全漏洞、数据丢失风险、严重性能问题
- 标记为🔴，明确说明必须修复

**Major（重要问题）**:
- 强烈建议修复
- 示例：设计缺陷、潜在bug、代码质量问题
- 标记为🟡，说明影响和建议

**Minor（小问题）**:
- 可选修复
- 示例：命名、注释、格式
- 标记为🟢，仅供参考

## 相关技能

- **git-workflow**: Git协作流程
- **quality-gate**: 质量门控决策
- **code-exploration**: 代码分析和重构建议

## 注意事项

- 代码审查是协作过程，不是批评过程
- 保持建设性和尊重的态度
- 关注代码质量，不是个人风格
- 及时响应审查请求和反馈
- 记录重要决策和讨论结果
- 定期回顾和改进审查流程

---

**维护者**: PM Agent Framework  
**最后更新**: 2026-03-10  
**版本历史**:
- 2.0.0 (2026-03-10): 标准化改造，符合Claude Skill Format
- 1.0.0 (2026-03-08): 初始版本
