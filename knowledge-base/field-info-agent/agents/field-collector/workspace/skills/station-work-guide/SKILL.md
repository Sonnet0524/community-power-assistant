---
name: station-work-guide
description: 驻点工作全流程引导技能，通过自然语言理解用户意图，动态生成工作清单，引导现场信息采集
metadata:
  {
    "openclaw":
      {
        "emoji": "🔌",
        "requires": { "env": ["KIMI_API_KEY"], "config": ["channels.wecom.enabled"] }
      }
  }
---

# Station Work Guide - 驻点工作引导技能

## 概述

本技能负责整个驻点工作流程的引导和协调，是 Field Info Collector 的核心工作流技能。

**核心能力**：
- 零命令自然语言交互
- 上下文感知状态管理
- 动态工作清单生成
- 多轮对话引导

**支持的工作类型**：
- 配电房检查（变压器、高压柜、低压柜等）
- 客户走访（重点客户、安全隐患排查）
- 应急通道采集（位置标记、照片记录）

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

## 实现逻辑

### 1. 意图识别

```typescript
async function recognizeIntent(message: string, context: Context): Promise<Intent> {
  // 使用 OpenClaw LLM 进行意图识别
  const prompt = `分析用户消息，识别工作意图：
  
用户消息：${message}
可能的意图：start_station_work | collect_power_room | collect_customer | collect_emergency | complete_collection | query_info | general_chat

只输出 JSON：{"intent": "类型", "confidence": 0-1, "entities": {...}}`;

  const result = await context.llm.chat({
    messages: [{ role: 'user', content: prompt }]
  });
  
  return JSON.parse(result.content);
}
```

### 2. 工作清单生成

```typescript
async function generateWorkList(
  communityId: string, 
  workType: string,
  context: Context
): Promise<WorkList> {
  // 查询社区历史信息
  const history = await context.tools['postgres-query'].execute({
    query: `
      SELECT 
        COUNT(*) as visit_count,
        MAX(created_at) as last_visit,
        json_agg(DISTINCT priority_customers) as priority_customers
      FROM field_collections
      WHERE community_id = $1
    `,
    params: [communityId]
  });
  
  // 根据工作类型生成清单
  const checklist = getChecklistTemplate(workType);
  
  return {
    communityId,
    workType,
    history,
    checklist,
    createdAt: new Date()
  };
}
```

### 3. 会话状态管理

```typescript
interface StationWorkSession {
  // 基础信息
  sessionId: string;
  userId: string;
  stationId: string;
  
  // 工作信息
  communityId: string;
  communityName: string;
  workType: 'routine' | 'emergency' | 'special';
  
  // 状态
  state: 'preparing' | 'collecting' | 'analyzing' | 'completed';
  currentPhase: 'power_room' | 'customer_visit' | 'emergency' | null;
  
  // 进度
  progress: {
    totalItems: number;
    completedItems: number;
    currentItem: string;
  };
  
  // 采集数据
  data: {
    powerRoom?: PowerRoomData;
    customers?: CustomerVisitData[];
    emergencyPoints?: EmergencyPointData[];
    photos: PhotoItem[];
    notes: string[];
  };
  
  // 时间戳
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}
```

## 引导话术模板

### 开始引导

```
📋 已为您准备 {communityName} 驻点工作

🏠 社区: {communityName}
📊 历史记录: {historyCount} 次驻点，上次 {lastVisitDate}
⚡ 重点客户: {priorityCustomerCount} 户（{priorityCustomerNames}）

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
✅ {phaseName} 已完成

📊 本次采集统计：
• 照片: {photoCount} 张
• 文字记录: {noteCount} 条
• 发现异常: {anomalyCount} 处

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

```typescript
async function handleIrrelevantContent(
  message: string, 
  session: StationWorkSession
): Promise<string> {
  return `抱歉，我没有理解您的意思。

当前正在进行：${session.currentPhase}

您可以：
• 发送相关照片继续记录
• 回复"下一步"继续下一项
• 回复"帮助"查看当前工作说明`;
}
```

### 用户长时间无响应

```typescript
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 分钟

async function handleSessionTimeout(sessionId: string): Promise<string> {
  // 保存当前进度
  await saveSessionProgress(sessionId);
  
  return `⏰ 您已超过 30 分钟没有操作

当前工作进度已自动保存。

如需继续，请回复：
• "继续" - 恢复当前工作
• "保存退出" - 保存并结束本次工作
• "放弃" - 放弃本次工作（数据将保留）`;
}
```

### 重复采集处理

```typescript
async function handleDuplicateContent(
  contentType: string,
  existingTime: Date
): Promise<string> {
  return `⚠️ 检测到 ${contentType} 已存在

已记录时间: ${existingTime.toLocaleString()}
是否覆盖？
• 回复"覆盖" - 用新内容替换
• 回复"保留" - 保留原有内容
• 回复"都保留" - 保留新旧两个版本`;
}
```

## 数据存储

### 保存工作进度

```typescript
async function saveProgress(
  sessionId: string,
  progress: WorkProgress,
  context: Context
): Promise<void> {
  await context.tools['postgres-query'].execute({
    query: `
      UPDATE field_sessions
      SET 
        progress = $2,
        data = $3,
        updated_at = NOW()
      WHERE session_id = $1
    `,
    params: [sessionId, JSON.stringify(progress), JSON.stringify(session.data)]
  });
}
```

## 配置说明

### 在 openclaw.config.yaml 中配置

```yaml
skills:
  station_work_guide:
    enabled: true
    priority: high
    triggers:
      - type: intent
        patterns:
          - "驻点"
          - "去.*社区"
          - "配电房"
          - "客户走访"
          - "应急通道"
          - "开始.*工作"
    config:
      max_session_duration: 7200  # 2 小时
      auto_save_interval: 300     # 5 分钟自动保存
```

## 使用示例

### 完整驻点流程

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

**版本**: 2.0.0  
**作者**: PM Agent  
**更新日期**: 2026-03-18  
**变更**: 修正为 OpenClaw 标准 SKILL.md 格式
