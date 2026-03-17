---
skill_id: git-workflow
name: Git工作流程
description: 标准化的Git协作流程，包括分支管理、提交规范、PR流程
version: 2.0.0
skill_type: workflow
category: collaboration
triggers:
  - "提交代码"
  - "创建分支"
  - "合并代码"
  - "Git操作"
  - "Pull Request"
trigger_patterns:
  - "(提交|commit)\\s*代码"
  - "创建\\s*(功能|bug|hotfix)\\s*分支"
  - "(合并|merge)\\s*代码"
  - "git\\s+(commit|push|pull|merge)"
  - "(创建|create)\\s*(PR|pull request)"
tags:
  - git
  - version-control
  - collaboration
  - workflow
  - code-review
---

# Git工作流程

## 概述

提供标准化的Git协作流程，包括分支管理策略、提交信息规范、Pull Request流程和代码审查标准，确保团队协作高效有序。

## 能力范围

### ✅ Can Do

- 指导创建标准化的分支结构
- 提供提交信息格式规范
- 指导Pull Request创建和审查流程
- 解决常见的Git操作问题
- 提供合并冲突解决方案
- 规范化团队协作流程

### ❌ Cannot Do

- 自动执行Git命令（需要人工确认）
- 强制修改用户的Git配置
- 解决所有类型的合并冲突（复杂冲突需要人工判断）
- 替代团队制定自己的Git规范
- 处理Git服务器端问题

## 使用场景

### Pattern 1: 功能开发提交

**User Intent**: 完成功能开发后，按照标准流程提交代码

**Trigger Phrases**:
- "提交功能代码"
- "如何创建功能分支"
- "完成开发，准备提交"
- "功能开发完成"

**Execution Flow**:
1. 确认当前分支状态
2. 创建标准命名的功能分支
3. 编写符合规范的提交信息
4. 推送到远程仓库
5. 创建Pull Request

**Example Interaction**:
```
User: "我刚完成CSV解析功能，如何提交代码？"

Agent:
我来帮你按照标准流程提交代码。

## 提交流程

### 1. 创建功能分支
```bash
# 确保在main分支
git checkout main
git pull origin main

# 创建功能分支（遵循命名规范）
git checkout -b feature/csv-parser-001
```

**命名规范**: `feature/{description}-{number}`
- ✅ `feature/csv-parser-001` - 好的命名
- ❌ `feature/parse` - 缺少编号
- ❌ `my-feature` - 缺少前缀

### 2. 提交代码
```bash
# 添加文件
git add .

# 提交（使用规范格式）
git commit -m "feat: 实现CSV解析器

- 支持UTF-8和GBK编码自动检测
- 添加错误处理和异常捕获
- 单元测试覆盖率85%

Closes #123"
```

**提交信息格式**:
```
<type>: <subject>

<body>

<footer>
```

**常用Type**:
- `feat` - 新功能
- `fix` - 修复bug
- `docs` - 文档更新
- `refactor` - 重构
- `test` - 测试相关

### 3. 推送到远程
```bash
git push origin feature/csv-parser-001
```

### 4. 创建Pull Request
```bash
gh pr create --title "feat: 实现CSV解析器" \
             --body "## 变更内容
- 支持UTF-8和GBK编码
- 添加错误处理
- 单元测试覆盖率85%

## 测试
- [x] 单元测试通过
- [x] 集成测试通过
- [x] 手动测试通过

Closes #123"
```

## 最佳实践

- ✅ **小步提交**: 每个commit只做一件事
- ✅ **清晰描述**: commit message清楚说明做了什么
- ✅ **自审查**: 创建PR前先自己审查一遍
- ✅ **及时同步**: 经常从main分支拉取最新代码

需要我帮你检查当前的分支状态吗？
```

---

### Pattern 2: 合并冲突解决

**User Intent**: 遇到合并冲突时，寻求解决方案

**Trigger Phrases**:
- "合并冲突了怎么办"
- "解决Git冲突"
- "代码合并失败"
- "有冲突"

**Execution Flow**:
1. 识别冲突类型和范围
2. 获取最新代码
3. 尝试自动合并
4. 指导手动解决冲突
5. 验证解决结果

**Example Interaction**:
```
User: "合并代码时遇到冲突了，怎么办？"

Agent:
我来帮你解决合并冲突。

## 解决冲突流程

### 1. 查看冲突文件
```bash
# 查看冲突状态
git status

# 查看冲突详情
git diff
```

### 2. 获取最新代码
```bash
# 切换到main分支
git checkout main
git pull origin main

# 回到功能分支
git checkout feature/csv-parser-001

# 合并main分支
git merge main
```

### 3. 手动解决冲突

冲突标记格式：
```
<<<<<<< HEAD
你的代码
=======
main分支的代码
>>>>>>> main
```

**解决策略**:
- **保留你的修改**: 删除`=======`和`>>>>>>> main`之间的内容
- **使用main分支**: 删除`<<<<<<< HEAD`和`=======`之间的内容
- **合并两者**: 手动整合两边的代码

### 4. 提交解决
```bash
# 标记冲突已解决
git add <conflicted-file>

# 提交
git commit -m "merge: 解决合并冲突

- 合并main分支的最新更改
- 保留CSV解析器的实现
- 更新相关测试"
```

### 5. 推送
```bash
git push origin feature/csv-parser-001
```

## 常见冲突类型

1. **同一行修改** - 需要手动决定使用哪个版本
2. **文件删除vs修改** - 决定保留还是删除
3. **重命名冲突** - 需要统一命名

## 预防冲突

- ✅ 频繁从main分支合并更新
- ✅ 小范围修改，减少冲突范围
- ✅ 团队沟通，避免同时修改同一文件
- ✅ 使用feature分支隔离开发

你的冲突是什么类型的？我可以提供更具体的解决方案。
```

---

### Pattern 3: 紧急修复流程

**User Intent**: 需要快速修复生产环境的紧急问题

**Trigger Phrases**:
- "紧急修复"
- "hotfix流程"
- "生产环境bug"
- "紧急上线"

**Execution Flow**:
1. 从main创建hotfix分支
2. 快速修复问题
3. 测试验证
4. 合并到main和develop
5. 打标签发布

**Example Interaction**:
```
User: "生产环境发现严重bug，需要紧急修复"

Agent:
我来指导你进行紧急修复。

## Hotfix流程

### 1. 创建hotfix分支
```bash
# 从main创建hotfix分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-encoding-bug
```

**命名规范**: `hotfix/{description}`
- 快速识别紧急修复
- 区别于普通bugfix

### 2. 快速修复
```bash
# 修改代码...

# 提交（明确标记为fix）
git add .
git commit -m "fix: 修复生产环境编码问题

- 修复UTF-8编码解析错误
- 添加边界条件检查
- 紧急修复，影响范围：文件上传模块

Fixes #456"
```

### 3. 快速测试
```bash
# 运行关键测试
npm run test:critical

# 手动验证修复效果
npm run verify:fix
```

### 4. 合并到main和develop
```bash
# 合并到main
git checkout main
git merge hotfix/critical-encoding-bug
git push origin main

# 合并到develop（如果存在）
git checkout develop
git merge hotfix/critical-encoding-bug
git push origin develop
```

### 5. 打标签发布
```bash
# 创建版本标签
git tag -a v1.2.1 -m "Hotfix: 修复编码问题"
git push origin v1.2.1
```

## Hotfix检查清单

- [ ] 问题确认：确认问题确实严重且紧急
- [ ] 最小修改：只修复问题，不做其他改动
- [ ] 测试验证：至少验证问题已修复
- [ ] 团队通知：通知相关人员hotfix内容
- [ ] 文档更新：更新CHANGELOG
- [ ] 监控部署：关注部署后的监控数据

## Hotfix vs 普通修复

| 特性 | Hotfix | 普通修复 |
|------|--------|----------|
| 紧急度 | 高 | 中/低 |
| 分支 | hotfix/* | bugfix/* |
| 合并目标 | main + develop | develop |
| 测试要求 | 关键路径测试 | 完整测试 |
| 发布方式 | 立即发布 | 随版本发布 |

需要我帮你创建hotfix分支吗？
```

## 参数说明

### 必需参数

无（本skill基于用户意图触发，不需要必需参数）

### 可选参数

#### branch_type
- **Type**: string
- **Default**: `"feature"`
- **Description**: 分支类型
- **Example**: `"feature"`, `"bugfix"`, `"hotfix"`

#### branch_name
- **Type**: string
- **Default**: `null`
- **Description**: 分支名称
- **Example**: `"csv-parser-001"`

#### commit_type
- **Type**: string
- **Default**: `"feat"`
- **Description**: 提交类型
- **Example**: `"feat"`, `"fix"`, `"docs"`, `"refactor"`

## 输出格式

### 成功输出

```json
{
  "success": true,
  "action": "branch_created",
  "branch": {
    "name": "feature/csv-parser-001",
    "type": "feature",
    "base": "main",
    "created_at": "2026-03-10T15:30:00Z"
  },
  "next_steps": [
    "进行代码开发",
    "提交代码",
    "创建Pull Request"
  ],
  "execution_time_ms": 123.45
}
```

### 错误输出

```json
{
  "success": false,
  "error": {
    "error_type": "ValidationError",
    "message": "分支名称不符合规范",
    "suggestion": "使用格式: feature/{description}-{number}"
  }
}
```

## 工具函数

### create_branch

**Purpose**: 创建符合规范的Git分支

**Input**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class CreateBranchParams(BaseModel):
    """创建分支参数"""
    branch_type: str = Field(
        default="feature",
        description="分支类型: feature, bugfix, hotfix"
    )
    branch_name: str = Field(
        ...,
        description="分支名称（不含前缀）"
    )
    base_branch: str = Field(
        default="main",
        description="基础分支"
    )
    issue_number: Optional[int] = Field(
        default=None,
        description="关联的Issue编号"
    )
```

**Output**:
```python
from datetime import datetime

class BranchOutput(BaseModel):
    """分支创建输出"""
    success: bool
    branch: dict
    next_steps: list[str]
    execution_time_ms: float
```

**Calling Convention**:
```python
from framework.skills.workflow.git_workflow import create_branch, CreateBranchParams

# 创建参数
params = CreateBranchParams(
    branch_type="feature",
    branch_name="csv-parser-001",
    issue_number=123
)

# 调用函数
result = create_branch(params)

# 处理结果
if result.success:
    print(f"分支已创建: {result.branch['name']}")
    print(f"下一步: {result.next_steps}")
```

---

### commit_changes

**Purpose**: 生成符合规范的提交信息

**Input**:
```python
class CommitParams(BaseModel):
    """提交参数"""
    commit_type: str = Field(
        ...,
        description="提交类型: feat, fix, docs, etc."
    )
    subject: str = Field(
        ...,
        max_length=50,
        description="提交主题（不超过50字符）"
    )
    body: Optional[str] = Field(
        default=None,
        description="提交详细描述"
    )
    issue_number: Optional[int] = Field(
        default=None,
        description="关联的Issue编号"
    )
    breaking_change: bool = Field(
        default=False,
        description="是否包含破坏性变更"
    )
```

**Output**:
```python
class CommitOutput(BaseModel):
    """提交输出"""
    success: bool
    commit_message: str
    commit_hash: Optional[str]
    execution_time_ms: float
```

**Calling Convention**:
```python
from framework.skills.workflow.git_workflow import commit_changes, CommitParams

# 创建参数
params = CommitParams(
    commit_type="feat",
    subject="实现CSV解析器",
    body="- 支持UTF-8和GBK编码\n- 添加错误处理\n- 单元测试覆盖率85%",
    issue_number=123
)

# 调用函数
result = commit_changes(params)

# 处理结果
if result.success:
    print(f"提交信息: {result.commit_message}")
```

## 最佳实践

### 分支管理

#### ✅ Do
- 使用清晰的分支命名规范
- 频繁从main分支同步更新
- 及时删除已合并的分支
- 保持分支短小精悍

#### ❌ Don't
- 在main分支直接开发
- 创建长期存在的feature分支
- 提交大文件到仓库
- 提交敏感信息（密码、密钥）

### 提交信息

#### ✅ Do
- 使用规范的提交格式
- 清晰描述变更内容
- 关联相关Issue
- 小步提交，每个commit只做一件事

#### ❌ Don't
- 提交未测试的代码
- 使用模糊的提交信息（如"update", "fix"）
- 一个commit包含多个不相关的变更
- 提交大量无关文件

### Pull Request

#### ✅ Do
- PR保持小而专注
- 提供清晰的PR描述
- 自己先审查一遍
- 及时响应审查意见

#### ❌ Don't
- PR包含多个无关功能
- 提交巨大的PR（>1000行）
- 忽视审查意见
- 强制合并未批准的PR

## 常见问题

### Q1: 分支命名不规范怎么办？

**A**: 遵循以下命名规范：

```
功能分支: feature/{description}-{number}
修复分支: bugfix/{description}-{number}
紧急修复: hotfix/{description}
发布分支: release/{version}
```

**示例**:
- ✅ `feature/csv-parser-001`
- ✅ `bugfix/encoding-issue-042`
- ✅ `hotfix/critical-security-fix`
- ❌ `my-feature` - 缺少类型前缀
- ❌ `feature/csv parser` - 包含空格

---

### Q2: 提交信息格式错误怎么办？

**A**: 使用标准格式：

```
<type>: <subject>

<body>

<footer>
```

**常用type**:
- `feat` - 新功能
- `fix` - Bug修复
- `docs` - 文档更新
- `style` - 代码格式
- `refactor` - 重构
- `test` - 测试
- `chore` - 构建/工具

**示例**:
```
feat: 实现CSV解析器

- 支持UTF-8和GBK编码
- 添加错误处理
- 单元测试覆盖率85%

Closes #123
```

---

### Q3: 如何撤销错误的提交？

**A**: 根据情况选择：

**未推送**:
```bash
# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD~1
```

**已推送**:
```bash
# 创建反向提交
git revert HEAD
git push origin main
```

**注意**: 不要对已推送的提交使用`reset --hard`，这会破坏团队协作。

---

### Q4: 合并冲突太复杂怎么办？

**A**: 使用工具辅助：

```bash
# 使用VSCode
git config --global merge.tool vscode

# 使用图形化工具
git mergetool
```

**策略**:
1. 先理解冲突的本质
2. 与团队成员沟通
3. 手动整合代码
4. 充分测试解决后的代码

## 相关技能

- **review-process**: 代码审查流程
- **quality-gate**: 质量门控决策
- **code-exploration**: 代码分析和重构建议

## 注意事项

- 所有Git操作都需要人工确认，不会自动执行破坏性操作
- 分支命名和提交信息规范可根据团队实际情况调整
- 合并冲突需要人工判断，工具只提供指导
- 敏感信息（密码、密钥）不应提交到版本控制
- Force push操作应在明确了解后果的情况下使用

---

**维护者**: PM Agent Framework  
**最后更新**: 2026-03-10  
**版本历史**:
- 2.0.0 (2026-03-10): 标准化改造，符合Claude Skill Format
- 1.0.0 (2026-03-08): 初始版本
