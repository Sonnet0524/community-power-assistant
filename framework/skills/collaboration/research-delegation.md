# Research Delegation Skill

## Skill定义

**名称**: research-delegation  
**类型**: 协作技能  
**版本**: 1.0.0  
**所属层级**: L2

---

## 功能描述

使PM Agent能够将研究任务委托给L1 research agent，并跟踪研究进度。

---

## 使用方法

### 基本调用

```bash
/opencode skill research-delegation "研究任务描述"
```

### 高级选项

```bash
/opencode skill research-delegation "评估微服务架构" \
  --priority high \
  --scope "架构设计,团队规模,可扩展性" \
  --depth "Level 0-2" \
  --deadline "2026-03-10"
```

---

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| description | string | 是 | - | 研究任务描述 |
| priority | string | 否 | medium | 优先级(critical/high/medium/low) |
| scope | string | 否 | null | 研究范围 |
| depth | string | 否 | "Level 0-2" | 研究深度 |
| deadline | string | 否 | null | 截止日期 |

---

## 执行流程

### 1. 创建研究请求

```yaml
步骤:
  1. 生成请求ID
     格式: research-{YYYYMMDD}-{序号}
  
  2. 创建请求文件
     路径: collaboration/research-requests/{request-id}.json
  
  3. 填写请求信息
     - 研究目标和描述
     - 研究范围和深度
     - 交付物要求
     - 优先级和截止日期
```

### 2. 通知L1 Research Agent

```yaml
方式:
  - 通过文件系统：创建请求文件
  - 通过opencode：调用L1 agent
  
消息格式:
  "New research request available: {request-id}"
  "Location: collaboration/research-requests/{request-id}.json"
```

### 3. 跟踪进度

```yaml
监控:
  - 定期检查请求文件status字段
  - 读取progress updates
  - 等待状态变为"completed"
  
更新频率:
  - critical: 每2小时检查
  - high: 每4小时检查
  - medium: 每天检查
  - low: 每周检查
```

### 4. 接收结果

```yaml
完成标志:
  - status.current = "completed"
  - deliverables已生成
  
结果处理:
  1. 读取交付物（报告、矩阵等）
  2. 评估研究质量
  3. 应用到项目中
  4. 归档请求文件
```

---

## 请求模板

### 完整请求模板

```json
{
  "request_id": "research-20260308-001",
  "created_at": "{{timestamp}}",
  "created_by": "pm-agent",
  "project_name": "{{project-name}}",
  
  "research": {
    "title": "{{research-title}}",
    "description": "{{detailed-description}}",
    "goals": [
      "{{goal-1}}",
      "{{goal-2}}"
    ],
    "scope": {
      "depth": "Level 0-2",
      "areas": ["{{area-1}}", "{{area-2}}"],
      "constraints": ["{{constraint-1}}"]
    },
    "methodology": "SEARCH-R"
  },
  
  "deliverables": {
    "format": ["report", "presentation"],
    "output_path": "reports/research/{{request-id}}/",
    "deadline": "{{deadline}}"
  },
  
  "status": {
    "current": "pending",
    "assigned_to": null,
    "l1_instance_id": null,
    "progress": 0,
    "updates": []
  },
  
  "priority": "{{priority}}",
  "tags": ["{{tag-1}}", "{{tag-2}}"]
}
```

---

## 示例用例

### 示例1: 技术选型研究

```
PM Agent: "我需要评估状态管理库的选型"

执行:
skill research-delegation "评估Redux、MobX和Zustand三个状态管理库" \
  --priority high \
  --scope "功能特性,性能,学习曲线,社区支持" \
  --depth "Level 0-2" \
  --deadline "2026-03-10"

创建请求:
{
  "request_id": "research-20260308-001",
  "research": {
    "title": "State Management Library Evaluation",
    "goals": [
      "Compare features and performance",
      "Assess learning curve",
      "Recommend best option"
    ]
  }
}

等待结果:
- L1执行研究
- 生成对比报告
- 提供选型建议
```

### 示例2: 架构决策研究

```
PM Agent: "需要研究微服务架构的适用性"

执行:
skill research-delegation "研究微服务架构对本项目的适用性" \
  --priority critical \
  --scope "架构设计,团队规模,运维成本,可扩展性" \
  --depth "Level 0-1"

结果:
- 理论分析报告
- 适用性评估矩阵
- 实施建议
```

---

## 与L1的协作

### L1 Research Agent职责

1. **接收请求**
   - 监控research-requests目录
   - 读取待处理请求

2. **执行研究**
   - 使用SEARCH-R方法论
   - 创建L0研究实例
   - 执行研究循环

3. **更新进度**
   - 定期更新status字段
   - 记录progress updates

4. **交付结果**
   - 生成deliverables
   - 通知PM Agent完成

### PM Agent职责

1. **发起请求**
   - 明确研究目标
   - 设定合理范围
   - 提供充足背景

2. **跟踪进度**
   - 定期检查状态
   - 响应L1的问题
   - 提供额外信息

3. **应用结果**
   - 评估研究成果
   - 做出决策
   - 反馈效果

---

## 质量保证

### 请求质量检查

创建请求前验证：
- [ ] 目标明确具体
- [ ] 范围合理可行
- [ ] 优先级正确
- [ ] 截止日期合理

### 结果质量评估

接收结果时评估：
- [ ] 是否达到研究目标
- [ ] 深度是否符合要求
- [ ] 交付物是否完整
- [ ] 建议是否可操作

---

## 错误处理

### 常见问题

1. **L1未响应**
   - 检查L1 agent状态
   - 验证请求格式
   - 尝试重新发送

2. **研究延期**
   - 评估影响
   - 调整项目计划
   - 考虑替代方案

3. **结果不符合预期**
   - 与L1沟通
   - 补充背景信息
   - 要求重新研究

---

## 日志记录

所有委托操作记录在：
```
logs/research-delegation-{date}.log
```

---

## 相关Skills

- `quality-gate`: 评估研究结果质量
- `review-process`: 审查研究交付物

---

## 相关文档

- [Research Requests目录](../../../collaboration/research-requests/README.md)
- [Dependencies文档](../../../collaboration/dependencies/README.md)
- [L1 Research Agent](../agent-team-research/agents/research-agent/AGENTS.md)

---

**维护者**: Migration Agent  
**创建时间**: 2026-03-08  
**版本**: 1.0.0
