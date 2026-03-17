---
skill_id: quality-gate
name: 质量门控
description: Agent输出的质量评估和决策支持，包括确定性评估、可接受性判断、混淆检测
version: 2.0.0
skill_type: workflow
category: decision-support
triggers:
  - "质量评估"
  - "检查输出质量"
  - "确定性评估"
  - "质量门控"
  - "任务完成评估"
trigger_patterns:
  - "(评估|检查)\\s*(输出|任务)\\s*(质量|完成度)"
  - "质量\\s*(门控|检查|评估)"
  - "确定性\\s*评估"
  - "(任务|输出)\\s*完成\\s*(情况|质量)"
tags:
  - quality-assurance
  - decision-support
  - meta-cognition
  - self-assessment
  - confidence-evaluation
---

# 质量门控

## 概述

质量门控是一种元认知能力，帮助Agent评估自己输出的质量，识别不确定性和风险，在必要时请求人类帮助，确保输出质量可预期、可信赖。

## 能力范围

### ✅ Can Do

- 评估输出的确定性等级
- 评估输出的可接受性
- 检测混淆和不确定性
- 识别需要人类介入的情况
- 提供质量评估报告
- 指导何时请求帮助

### ❌ Cannot Do

- 替代人类的最终决策
- 强制要求人类介入
- 自动修复输出质量问题
- 解决知识或信息缺失问题
- 预测所有可能的错误

## 使用场景

### Pattern 1: 任务完成质量评估

**User Intent**: 完成任务后，评估输出质量是否达标

**Trigger Phrases**:
- "任务完成了，检查质量"
- "评估输出质量"
- "质量门控检查"
- "检查完成度"

**Execution Flow**:
1. 评估确定性等级
2. 评估可接受性
3. 检测混淆情况
4. 检查Kill Criteria
5. 做出决策

**Example Interaction**:
```
User: "我刚完成了用户认证功能的实现，帮我检查质量"

Agent:
我来帮你进行质量门控评估。

## 质量门控评估

### 第一步：确定性评估

**评估维度**:

**知识领域**:
- ✅ 在专业领域内（认证安全）
- ✅ 有相关经验（实现过类似功能）
- ✅ 理解上下文（用户需求明确）

**信息完整性**:
- ✅ 信息完整（需求文档详细）
- ✅ 无缺失的关键信息
- ✅ 不需要澄清

**约束理解**:
- ✅ 理解所有约束
- ✅ 约束之间无冲突
- ✅ 无隐含约束

**方案可行性**:
- ✅ 方案可行（采用JWT标准）
- ✅ 无明显风险
- ✅ 无更好方案

**确定性等级**: 🟢 HIGH (85%)

**评估依据**:
- 专业领域内，有经验
- 需求明确，信息完整
- 技术方案成熟可靠

---

### 第二步：可接受性评估

**评估维度**:

**功能正确性**:
- ✅ 满足需求（登录、注册、Token刷新）
- ✅ 处理了边界情况（Token过期、密码错误）
- ✅ 无明显bug（已自测）

**质量**:
- ✅ 符合编码规范
- ✅ 有适当的注释和文档
- ✅ 易于理解（代码结构清晰）

**完整性**:
- ✅ 完整实现（包含所有需求功能）
- ✅ 无遗漏（对照需求检查）
- 🟡 有待办事项（后续可优化错误提示）

**测试**:
- ✅ 有单元测试（覆盖率78%）
- ✅ 测试通过
- 🟡 缺少集成测试

**可接受性等级**: 🟢 ACCEPTABLE (75%)

**评估依据**:
- 功能完整，满足需求
- 代码质量良好
- 测试覆盖充分
- 文档完善

**需要改进**:
- 补充集成测试
- 优化错误提示文案

---

### 第三步：混淆检测

**是否混淆**: ❌ 否

**检查项**:
- ✅ 不存在知识缺口
- ✅ 不存在信息缺口
- ✅ 约束无冲突
- ✅ 需求无歧义
- ✅ 复杂度可控

---

### 第四步：Kill Criteria检查

**是否需要停止**: ❌ 否

**检查项**:
- ✅ 确定性>70%
- ✅ 无边界冲突
- ✅ 资源充足
- ✅ 目标一致
- ✅ 无技术障碍

---

### 第五步：质量门控决策

**决策**: ✅ **通过质量门控，可以交付**

**理由**:
1. 确定性85% - 高度确定
2. 可接受性75% - 可接受水平
3. 无混淆和冲突
4. 满足Kill Criteria

**输出建议**:
```
## ✅ 任务完成报告

### 完成情况
已实现用户认证功能，包括：
- ✅ 用户注册和登录
- ✅ JWT Token生成和验证
- ✅ Token刷新机制
- ✅ 密码加密存储

### 📊 质量评估

**确定性**: 🟢 HIGH (85%)
- 专业领域内实现
- 需求明确完整
- 技术方案成熟

**可接受性**: 🟢 ACCEPTABLE (75%)
- 功能完整
- 代码质量良好
- 测试覆盖78%

### 📤 交付内容
- 源代码: `src/auth/`
- 单元测试: `tests/auth.test.ts`
- API文档: `docs/auth-api.md`
- 使用示例: `examples/auth-usage.md`

### ⚠️ 已知问题
- 缺少集成测试（建议补充）
- 错误提示文案待优化（低优先级）

### 💡 改进建议
1. 补充端到端的集成测试
2. 添加更多的错误场景覆盖
3. 考虑添加登录失败次数限制

---
**质量门控**: ✅ 已通过
**Agent**: Backend Team
**时间**: 2026-03-10 15:30
```

需要我生成详细的测试计划吗？
```

---

### Pattern 2: 低确定性情况处理

**User Intent**: 任务完成但确定性较低，需要指导如何处理

**Trigger Phrases**:
- "不确定实现是否正确"
- "确定性评估较低"
- "需要帮助验证"
- "不确定的地方"

**Execution Flow**:
1. 识别不确定性来源
2. 评估风险影响
3. 提出澄清方案
4. 决定是否请求帮助

**Example Interaction**:
```
User: "我实现了支付功能，但不确定是否考虑了所有边界情况"

Agent:
我来帮你进行质量门控评估。

## 质量门控评估

### 第一步：确定性评估

**知识领域**:
- ✅ 在专业领域内（支付系统）
- 🟡 有部分经验（首次处理跨境支付）
- ✅ 理解基本上下文

**信息完整性**:
- ✅ 基本需求明确
- ❌ 缺少汇率处理规则
- ❌ 缺少退款流程说明

**约束理解**:
- ✅ 理解主要约束
- 🟡 部分约束不明确（不同国家的法规要求）
- ❌ 可能存在隐含约束

**方案可行性**:
- 🟡 方案基本可行
- 🟡 存在潜在风险（并发处理）
- 🟡 可能有更好方案

**确定性等级**: 🟡 MEDIUM (65%)

**不确定性来源**:
1. 跨境支付的汇率处理规则不明确
2. 不同国家的支付法规要求不确定
3. 高并发场景下的订单处理未验证
4. 退款流程的详细规则缺失

---

### 第二步：可接受性评估

**功能正确性**:
- ✅ 基本流程正确（支付成功、失败）
- 🟡 边界情况处理部分缺失
- 🟡 可能存在未知bug

**质量**:
- ✅ 符合编码规范
- ✅ 有注释和文档
- ✅ 代码结构清晰

**完整性**:
- 🟡 核心功能完成
- ❌ 缺少退款功能
- ❌ 缺少汇率处理

**测试**:
- ✅ 有单元测试（覆盖率65%）
- 🟡 缺少并发场景测试
- ❌ 缺少边界情况测试

**可接受性等级**: 🟡 QUESTIONABLE (55%)

---

### 第三步：混淆检测

**是否混淆**: ✅ 是

**混淆类型**: 
- `information_gap` - 信息缺失
- `knowledge_gap` - 知识缺口（跨境支付规则）

**需要澄清**:
- 汇率处理规则是什么？
- 不同国家的法规要求？
- 退款流程如何处理？
- 并发场景如何保证一致性？

---

### 第四步：质量门控决策

**决策**: 🟡 **建议请求帮助**

**理由**:
1. 确定性65% - 低于推荐阈值70%
2. 存在信息缺失和知识缺口
3. 可接受性较低（55%）
4. 支付功能风险较高

**建议行动**:

```markdown
## 需要帮助

**问题类型**: information_gap, knowledge_gap

**问题描述**:
支付功能实现中存在不确定的地方，需要澄清规则和补充知识

**我已尝试**:
- ✅ 实现基本支付流程
- ✅ 参考了主流支付平台文档
- ✅ 添加了基本错误处理

**我的不确定性**:
- 确定性等级: 🟡 MEDIUM (65%)
- 不确定的地方:
  1. 跨境支付的汇率处理规则
  2. 不同国家的法规要求
  3. 高并发场景处理
  4. 退款流程详细规则

**建议方案**:
1. 明确汇率处理的业务规则
2. 咨询法务关于不同国家的要求
3. 设计并发处理方案
4. 确定退款流程

**需要支持**:
- [x] 确认方向
- [x] 提供信息（汇率规则、法规要求）
- [ ] 调整约束（时间、资源）
- [ ] 其他：技术架构评审

---
**Agent**: Payment Team
**时间**: 2026-03-10 15:45
```

---

### 补充信息后如何继续

**一旦获得澄清**:

1. 更新确定性评估
2. 补充实现缺失部分
3. 再次进行质量门控
4. 决定是否可以交付

**预期提升**:
- 确定性: 65% → 80%+
- 可接受性: 55% → 70%+

需要我帮你准备一个详细的问题清单，用于向Product Owner澄清？
```

---

### Pattern 3: 资源耗尽或阻塞处理

**User Intent**: 遇到资源耗尽或技术障碍，无法继续

**Trigger Phrases**:
- "遇到障碍了"
- "资源不够了"
- "无法继续"
- "被阻塞了"

**Execution Flow**:
1. 识别Kill Criteria触发条件
2. 评估影响范围
3. 准备升级报告
4. 提出解决方案

**Example Interaction**:
```
User: "Token快用完了，任务还没完成怎么办"

Agent:
我来帮你评估和处理这种情况。

## Kill Criteria检查

**是否需要停止**: ✅ 是

**触发条件**: 
- `resource_exhausted` - 资源耗尽（Token预算即将用尽）

**当前状态**:
- Token已使用: 95,000 / 100,000
- 剩余Token: 5,000
- 任务完成度: 70%
- 未完成部分: 测试和文档

**影响评估**:
- 影响等级: 🔴 SEVERE
- 影响范围: 任务交付延迟
- 风险: 无法完成测试和文档

---

## 升级报告

**需要升级**: ✅ 是

**升级目标**: PM Agent / Human

**升级原因**:
Token资源即将耗尽，无法完成剩余工作（测试和文档）

**当前进展**:
- ✅ 核心功能实现完成（100%）
- ✅ 单元测试编写完成（100%）
- ❌ 集成测试未完成（0%）
- ❌ 文档未完成（30%）

**已完成的工作**:
```markdown
## 已完成
1. 核心功能实现
   - 用户认证模块
   - API接口
   - 错误处理
   
2. 单元测试
   - 覆盖率: 85%
   - 测试用例: 42个
   - 全部通过
```

**未完成的工作**:
```markdown
## 未完成
1. 集成测试
   - 预计工作量: 3-5小时
   - Token消耗: 约10,000
   
2. API文档
   - 预计工作量: 1-2小时
   - Token消耗: 约3,000
```

**建议方案**:

**方案1: 申请更多资源**（推荐）
- 需要额外Token: 15,000
- 优点: 完整交付
- 缺点: 需要等待资源

**方案2: 调整交付范围**
- 先交付核心功能
- 测试和文档作为后续迭代
- 优点: 可立即交付
- 缺点: 交付不完整

**方案3: 简化剩余工作**
- 只做关键测试
- 生成简化版文档
- 优点: 平衡质量和时间
- 缺点: 质量有所妥协

---

## 决策请求

**需要决策**:
- [ ] 申请更多Token资源
- [ ] 调整交付范围
- [ ] 简化剩余工作
- [ ] 其他方案

**期望响应时间**: 立即（资源即将耗尽）

---
**紧急程度**: 🔴 HIGH
**Agent**: Backend Team
**时间**: 2026-03-10 16:00

---

**下一步**:
等待PM Agent或Human的决策后，继续执行相应方案。

需要我帮你准备更详细的资源申请报告吗？
```

## 参数说明

### 必需参数

无（本skill基于用户意图触发）

### 可选参数

#### confidence_threshold
- **Type**: float
- **Default**: `0.70`
- **Description**: 确定性阈值，低于此值建议请求帮助
- **Example**: `0.70`

#### acceptability_threshold
- **Type**: float
- **Default**: `0.60`
- **Description**: 可接受性阈值，低于此值需要改进
- **Example**: `0.60`

#### task_type
- **Type**: string
- **Default**: `"general"`
- **Description**: 任务类型
- **Example**: `"implementation"`, `"analysis"`, `"design"`

## 输出格式

### 成功输出

```json
{
  "success": true,
  "quality_assessment": {
    "confidence_level": "HIGH",
    "confidence_score": 0.85,
    "acceptability_level": "ACCEPTABLE",
    "acceptability_score": 0.75,
    "is_confused": false,
    "kill_criteria_triggered": false
  },
  "decision": "proceed",
  "recommendation": "输出质量良好，可以交付",
  "execution_time_ms": 234.56
}
```

### 低确定性输出

```json
{
  "success": true,
  "quality_assessment": {
    "confidence_level": "MEDIUM",
    "confidence_score": 0.65,
    "acceptability_level": "QUESTIONABLE",
    "acceptability_score": 0.55,
    "is_confused": true,
    "confusion_type": ["information_gap", "knowledge_gap"],
    "kill_criteria_triggered": false
  },
  "decision": "request_help",
  "recommendation": "建议请求帮助，澄清不确定的地方",
  "clarification_needs": [
    "汇率处理规则",
    "跨境支付法规要求"
  ],
  "execution_time_ms": 456.78
}
```

### 错误输出

```json
{
  "success": false,
  "error": {
    "error_type": "QualityGateError",
    "message": "质量门控评估失败",
    "suggestion": "检查评估参数和输入信息"
  }
}
```

## 工具函数

### evaluate_confidence

**Purpose**: 评估输出的确定性等级

**Input**:
```python
from pydantic import BaseModel, Field
from typing import List

class ConfidenceParams(BaseModel):
    """确定性评估参数"""
    task_type: str = Field(
        default="general",
        description="任务类型"
    )
    knowledge_domain: dict = Field(
        default_factory=lambda: {
            "in_scope": True,
            "has_experience": True,
            "understands_context": True
        },
        description="知识领域评估"
    )
    information_completeness: dict = Field(
        default_factory=lambda: {
            "sufficient": True,
            "missing_critical": False,
            "needs_clarification": False
        },
        description="信息完整性评估"
    )
    constraints: dict = Field(
        default_factory=lambda: {
            "all_understood": True,
            "conflicts": False,
            "implicit_constraints": False
        },
        description="约束理解评估"
    )
    feasibility: dict = Field(
        default_factory=lambda: {
            "viable": True,
            "risks": "NONE",
            "better_alternatives": False
        },
        description="可行性评估"
    )
```

**Output**:
```python
class ConfidenceOutput(BaseModel):
    """确定性评估输出"""
    success: bool
    confidence_level: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    confidence_score: float  # 0.0 - 1.0
    assessment: dict
    uncertainties: List[str]
    execution_time_ms: float
```

**Calling Convention**:
```python
from framework.skills.decision_support.quality_gate import evaluate_confidence, ConfidenceParams

# 创建参数
params = ConfidenceParams(
    task_type="implementation",
    knowledge_domain={
        "in_scope": True,
        "has_experience": True,
        "understands_context": True
    }
)

# 调用函数
result = evaluate_confidence(params)

# 处理结果
if result.success:
    print(f"确定性: {result.confidence_level} ({result.confidence_score:.0%})")
    if result.uncertainties:
        print("不确定性来源:")
        for uncertainty in result.uncertainties:
            print(f"  - {uncertainty}")
```

---

### check_kill_criteria

**Purpose**: 检查是否触发终止标准

**Input**:
```python
class KillCriteriaParams(BaseModel):
    """Kill Criteria检查参数"""
    confidence_score: float = Field(..., ge=0, le=1)
    boundary_conflict: bool = Field(default=False)
    resource_usage: dict = Field(
        default_factory=lambda: {
            "token_used": 0,
            "token_limit": 100000,
            "time_used": 0,
            "time_limit": 3600
        }
    )
    goal_conflict: bool = Field(default=False)
    technical_blocker: bool = Field(default=False)
```

**Output**:
```python
class KillCriteriaOutput(BaseModel):
    """Kill Criteria检查输出"""
    success: bool
    should_stop: bool
    reasons: List[str]
    impact: str  # MINOR, MODERATE, SEVERE, CRITICAL
    escalation_required: bool
    escalation_target: str  # PM, HUMAN, TECH_LEAD
    next_steps: List[str]
    execution_time_ms: float
```

**Calling Convention**:
```python
from framework.skills.decision_support.quality_gate import check_kill_criteria, KillCriteriaParams

# 创建参数
params = KillCriteriaParams(
    confidence_score=0.35,
    resource_usage={
        "token_used": 95000,
        "token_limit": 100000
    }
)

# 调用函数
result = check_kill_criteria(params)

# 处理结果
if result.should_stop:
    print(f"需要停止，原因: {result.reasons}")
    if result.escalation_required:
        print(f"需要升级到: {result.escalation_target}")
```

## 最佳实践

### 确定性评估

#### ✅ Do
- 客观评估自己的知识和经验
- 识别信息缺口和知识缺口
- 考虑所有可能的约束
- 评估风险和影响

#### ❌ Don't
- 高估自己的确定性
- 忽视潜在风险
- 假装确定（当实际上不确定）
- 隐瞒不确定性

### 请求帮助

#### ✅ Do
- 明确说明不确定的地方
- 提供已尝试的方案
- 提出具体的澄清需求
- 及时请求帮助

#### ❌ Don't
- 等到问题无法解决才请求帮助
- 模糊地说明问题
- 不提供背景信息
- 延迟请求帮助

### 质量报告

#### ✅ Do
- 包含确定性评估
- 包含可接受性评估
- 列出已知问题和风险
- 提供改进建议

#### ❌ Don't
- 省略质量评估
- 隐藏问题和风险
- 只报告好消息
- 夸大输出质量

## 常见问题

### Q1: 确定性低于阈值但时间紧迫怎么办？

**A**: 评估权衡：

**决策矩阵**:

| 确定性 | 紧急度 | 建议 |
|--------|--------|------|
| <50% | 高 | 立即请求帮助 |
| 50-70% | 高 | 请求快速澄清或降低范围 |
| 50-70% | 中 | 建议请求帮助 |
| 50-70% | 低 | 先请求帮助，再继续 |
| >70% | 高 | 可以继续，标注不确定性 |

**快速澄清模板**:
```markdown
**问题**: [简要描述]
**影响**: [不澄清的后果]
**需要**: [具体需求]
**时间**: [期望响应时间]
```

---

### Q2: 如何提高确定性？

**A**: 使用以下策略：

1. **补充信息**
   - 向Product Owner澄清需求
   - 收集更多上下文信息
   - 查阅相关文档和资料

2. **补充知识**
   - 研究相关技术文档
   - 参考类似实现案例
   - 咨询领域专家

3. **验证方案**
   - 做技术验证（POC）
   - 编写测试用例
   - 进行设计评审

4. **降低复杂度**
   - 拆分复杂任务
   - 简化技术方案
   - 减少功能范围

---

### Q3: Kill Criteria触发后还能继续吗？

**A**: 取决于触发原因：

**可以继续的情况**:
- 获得更多资源
- 调整了约束条件
- 解决了技术障碍
- 获得了必要的帮助

**不能继续的情况**:
- 确定性严重不足（<30%）
- 存在不可调和的冲突
- 资源彻底耗尽
- 技术障碍无法解决

**重新评估流程**:
1. 解决触发Kill Criteria的问题
2. 重新评估确定性
3. 检查是否还触发Kill Criteria
4. 决定是否继续

---

### Q4: 质量门控会不会影响效率？

**A**: 短期可能降低速度，长期提高效率：

**短期影响**:
- 需要时间进行评估
- 可能延迟交付（请求帮助）
- 需要编写质量报告

**长期收益**:
- 减少返工（及早发现问题）
- 提高信任度（输出质量稳定）
- 降低风险（避免严重错误）
- 改进流程（持续优化）

**效率优化**:
- 建立快速评估流程
- 重用评估模板
- 自动化部分评估
- 定期回顾和优化

## 相关技能

- **git-workflow**: Git协作流程
- **review-process**: 代码审查流程
- **code-exploration**: 代码分析和质量评估

## 注意事项

- 质量门控是元认知能力，不是质量保证的替代品
- 确定性评估是主观的，需要客观依据
- 请求帮助不是失败，是负责任的表现
- Kill Criteria不是推卸责任，是风险管理
- 质量门控结果应记录和追溯
- 定期回顾质量门控的准确性和有效性

---

**维护者**: PM Agent Framework  
**适用范围**: 所有Agent  
**最后更新**: 2026-03-10  
**版本历史**:
- 2.0.0 (2026-03-10): 标准化改造，符合Claude Skill Format
- 1.0.0 (2026-03-08): 初始版本
