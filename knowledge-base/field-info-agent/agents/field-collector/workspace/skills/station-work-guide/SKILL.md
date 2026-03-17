---
name: station-work-guide
description: |
  驻点工作全流程引导技能
  
  通过自然语言理解用户意图，自动识别驻点工作阶段，
  动态生成工作清单，引导现场信息采集流程。
  
  支持的工作类型：
  - 配电房检查（变压器、高压柜、低压柜等）
  - 客户走访（重点客户、安全隐患排查）
  - 应急通道采集（位置标记、照片记录）
  
  核心能力：
  - 零命令自然语言交互
  - 上下文感知状态管理
  - 动态工作清单生成
  - 多轮对话引导

metadata:
  openclaw:
    emoji: 🔌
    category: workflow
    requires:
      tools:
        - postgres-query
        - kimi-vision
      channels:
        - wecom
    triggers:
      - type: message
        condition: intent_recognition
      - type: event
        condition: session_state_change
---

# Station Work Guide - 驻点工作引导技能

## 概述

本技能负责整个驻点工作流程的引导和协调，是Field Info Collector的核心工作流技能。

## 工作流定义

### 阶段流转

```
[开始] 
  ↓ 用户说"我要去XX社区"
[准备阶段] 
  ↓ 确认开始工作
[采集阶段] 
  ├── 配电房子阶段
  ├── 客户走访子阶段
  └── 应急通道子阶段
  ↓ 完成采集
[分析阶段]
  ↓ 分析完成
[完成阶段]
  ↓ 生成报告
[结束]
```

## 意图识别规则

### 开始驻点工作
**触发词**: 驻点、去、前往、到、今天去、准备去
**示例**:
- "我今天要去阳光社区驻点"
- "准备去幸福小区"
- "到配电房检查一下"

### 配电房采集
**触发词**: 配电房、变压器、高压、低压、开关柜
**示例**:
- "我在配电房了"
- "这是变压器的照片"
- "检查一下高压侧"

### 客户走访
**触发词**: 客户、走访、拜访、用户、住户
**示例**:
- "去走访一下重点客户"
- "这户有安全隐患"
- "客户不在家"

### 应急通道
**触发词**: 应急、通道、入口、抢修、紧急
**示例**:
- "标记一下应急通道"
- "这是应急入口的位置"
- "记录一下抢修通道"

### 完成采集
**触发词**: 完成、结束、好了、搞定、生成报告
**示例**:
- "采集完成了"
- "配电房检查好了"
- "生成今天的报告"

## 上下文管理

### Session数据结构

```typescript
interface StationWorkSession {
  // 基础信息
  sessionId: string
  userId: string
  stationId: string
  
  // 工作信息
  communityId: string
  communityName: string
  workType: 'routine' | 'emergency' | 'special'
  
  // 状态
  state: 'preparing' | 'collecting' | 'analyzing' | 'completed'
  currentPhase: 'power_room' | 'customer_visit' | 'emergency' | null
  
  // 进度
  progress: {
    totalItems: number
    completedItems: number
    currentItem: string
  }
  
  // 采集数据
  data: {
    powerRoom?: PowerRoomData
    customers?: CustomerVisitData[]
    emergencyPoints?: EmergencyPointData[]
    photos: PhotoItem[]
    notes: string[]
  }
  
  // 时间戳
  createdAt: timestamp
  updatedAt: timestamp
  completedAt?: timestamp
}
```

## 引导话术模板

### 开始引导
```
📋 已为您准备{communityName}驻点工作

🏠 社区: {communityName}
📊 历史记录: {historyCount}次驻点，上次{lastVisitDate}
⚡ 重点客户: {priorityCustomerCount}户（{priorityCustomerNames}）

工作清单已生成，您可以：
• 回复"开始配电房检查"启动配电房采集
• 回复"开始客户走访"启动客户走访
• 回复"标记应急通道"记录应急入口
• 发送位置或照片直接开始对应工作
```

### 配电房引导
```
🔌 配电房检查引导

当前进度: {completed}/{total}

{currentItem}

操作提示：
• 发送照片记录当前设备
• 发送文字补充说明
• 回复"下一步"继续下一项
• 回复"跳过"暂时跳过此项
```

### 完成确认
```
✅ {phaseName}已完成

📊 本次采集统计：
• 照片: {photoCount}张
• 文字记录: {noteCount}条
• 发现异常: {anomalyCount}处

下一步您可以选择：
• 回复"继续"进入下一阶段
• 回复"分析"立即分析已采集数据
• 回复"生成报告"生成工作文档
• 发送更多照片补充信息
```

## 工作清单模板

### 配电房检查清单

```yaml
power_room_checklist:
  - id: pr_001
    name: "变压器整体"
    description: "拍摄变压器整体外观"
    required: true
    
  - id: pr_002
    name: "变压器高压侧"
    description: "拍摄高压侧接线、开关状态"
    required: true
    
  - id: pr_003
    name: "变压器低压侧"
    description: "拍摄低压侧接线、开关状态"
    required: true
    
  - id: pr_004
    name: "高压柜"
    description: "拍摄高压柜仪表、指示灯"
    required: true
    
  - id: pr_005
    name: "低压柜"
    description: "拍摄低压柜仪表、开关状态"
    required: true
    
  - id: pr_006
    name: "环境照片"
    description: "拍摄配电房整体环境"
    required: true
    
  - id: pr_007
    name: "安全隐患"
    description: "拍摄发现的安全隐患"
    required: false
    
  - id: pr_008
    name: "其他设备"
    description: "其他需要记录的设备"
    required: false
```

### 客户走访清单

```yaml
customer_visit_checklist:
  - id: cv_001
    name: "客户信息确认"
    description: "确认客户名称、地址、联系方式"
    required: true
    
  - id: cv_002
    name: "用电情况"
    description: "了解客户用电负荷、用电性质"
    required: true
    
  - id: cv_003
    name: "安全隐患排查"
    description: "检查客户侧用电安全隐患"
    required: true
    
  - id: cv_004
    name: "需求收集"
    description: "收集客户用电需求和意见建议"
    required: false
    
  - id: cv_005
    name: "现场照片"
    description: "拍摄客户配电设施照片"
    required: false
```

## 异常处理

### 用户发送不相关内容
**处理**: 友好提示，引导回到当前工作
```
抱歉，我没有理解您的意思。

当前正在进行：{currentPhase}

您可以：
• 发送相关照片继续记录
• 回复"下一步"继续下一项
• 回复"帮助"查看当前工作说明
```

### 用户长时间无响应
**处理**: 发送提醒，保存当前进度
```
⏰ 您已{timeoutMinutes}分钟没有操作

当前工作进度已自动保存。

如需继续，请回复：
• "继续" - 恢复当前工作
• "保存退出" - 保存并结束本次工作
• "放弃" - 放弃本次工作（数据将保留）
```

### 重复采集
**处理**: 检测重复，询问是否覆盖
```
⚠️ 检测到{contentType}已存在

已记录时间: {existingTime}
是否覆盖？
• 回复"覆盖" - 用新内容替换
• 回复"保留" - 保留原有内容
• 回复"都保留" - 保留新旧两个版本
```

## API接口

### 获取社区历史信息

```typescript
async function getCommunityHistory(
  communityId: string
): Promise<CommunityHistory> {
  const query = `
    SELECT 
      COUNT(*) as visit_count,
      MAX(created_at) as last_visit,
      json_agg(DISTINCT priority_customers) as priority_customers
    FROM field_collections
    WHERE community_id = $1
    GROUP BY community_id
  `
  return await postgres.query(query, [communityId])
}
```

### 保存工作进度

```typescript
async function saveProgress(
  sessionId: string,
  progress: WorkProgress
): Promise<void> {
  const query = `
    UPDATE field_sessions
    SET 
      progress = $2,
      data = $3,
      updated_at = NOW()
    WHERE session_id = $1
  `
  await postgres.query(query, [sessionId, progress, session.data])
}
```

## 使用示例

### 示例1: 完整驻点流程

```
[14:30] User: 我今天要去阳光社区驻点
[14:30] Agent: 📋 已为您准备阳光社区驻点工作...

[14:32] User: 开始配电房检查
[14:32] Agent: 🔌 配电房检查引导...
         第1项：变压器整体（必须）
         请拍摄变压器整体外观照片

[14:35] User: [发送照片]
[14:35] Agent: 📸 照片已接收
         第2项：变压器高压侧（必须）
         ...

[15:00] User: 配电房检查好了
[15:00] Agent: ✅ 配电房检查已完成
         下一步您可以选择：...

[15:05] User: 去走访一下阳光大厦
[15:05] Agent: 🏢 开始客户走访：阳光大厦
         ...

[16:30] User: 采集完成
[16:30] Agent: ✅ 采集完成，正在分析照片...
         [分析完成后]
         📄 报告已生成...
```

---

**版本**: 1.0.0  
**作者**: PM Agent  
**最后更新**: 2026-03-18
