---
name: vision-analysis
description: AI照片智能分析技能，使用OpenClaw多模态能力对电力设备照片进行智能分析
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "requires": { "env": ["KIMI_API_KEY"], "config": ["llm.kimi.vision_analysis.enabled"] }
      }
  }
---

# Vision Analysis - AI照片智能分析技能

## 概述

本技能利用 OpenClaw 的多模态能力，直接调用配置的 KIMI 2.5 模型对现场照片进行分析。

**核心能力**：
- 设备类型识别（变压器、高压柜、低压柜、电缆等）
- 缺陷检测（漏油、锈蚀、松动、过热等）
- 状态评估（正常、注意、异常、危险）
- 安全隐患识别

## 使用场景

### 触发条件（在 openclaw.config.yaml 中配置）

1. **接收到图片消息** - 自动触发分析
2. **用户命令** - "分析照片"、"批量分析"

### 工作流程

```
用户发送图片 
  → OpenClaw Channel 接收 
  → LLM 多模态自动分析（使用配置的 Prompt）
  → Skill 解析 JSON 结果
  → 保存到 PostgreSQL
  → 返回分析摘要给用户
```

## Prompt 模板

### 单图分析 Prompt

配置位置：`openclaw.config.yaml` → `llm.kimi.vision_analysis.prompts.single_image`

```
请仔细分析这张电力设备照片，按以下 JSON 格式返回分析结果：

{
  "device_type": "设备类型（变压器/高压柜/低压柜/电缆/计量装置/其他）",
  "device_subtype": "设备子类型（如：箱式变压器、干式变压器等）",
  "status": "normal|attention|abnormal|danger",
  "confidence": 0-1,
  "findings": [
    {
      "category": "appearance|connection|insulation|operation|label|environment",
      "description": "缺陷描述",
      "severity": "low|medium|high|critical",
      "location": "位置描述"
    }
  ],
  "safety_issues": ["安全隐患1", "安全隐患2"],
  "recommendations": ["建议1", "建议2"],
  "summary": "一句话分析摘要"
}
```

### 批量分析 Prompt

配置位置：`openclaw.config.yaml` → `llm.kimi.vision_analysis.prompts.batch_images`

```
你正在分析同一配电房的 {{photo_count}} 张照片。请进行批量分析：

分析要求：
1. 分别识别每张照片中的设备
2. 评估每台设备的状态
3. 发现设备间的关联问题
4. 识别共性问题（环境、标识等）
5. 给出整体评估和优先处理建议

按 JSON 格式返回：
{
  "overall_assessment": {
    "facility_type": "配电房类型",
    "overall_status": "normal|attention|abnormal|danger",
    "total_devices": 数量,
    "issues_found": 问题数量,
    "critical_issues": 严重问题数量,
    "score": 0-100
  },
  "per_image_analysis": [
    {
      "image_index": 0,
      "device_type": "设备类型",
      "status": "状态",
      "findings": [],
      "recommendations": []
    }
  ],
  "common_issues": ["共性问题1"],
  "priority_actions": ["优先处理1"],
  "summary": "整体评估摘要"
}
```

## 实现逻辑

### 1. 单图分析处理

```typescript
// Skill 处理函数
async function handleImage(message: ImageMessage, context: Context) {
  // OpenClaw 已经自动将图片传给 LLM 分析
  // 从 context 中获取分析结果
  const analysisResult = context.llmResponse;
  
  // 解析 JSON
  const result = JSON.parse(analysisResult.content);
  
  // 保存到数据库（使用 postgres-query 工具）
  await context.tools['postgres-query'].execute({
    query: `
      INSERT INTO photo_analysis (
        session_id, photo_url, result,
        device_type, status, confidence, has_issues, issue_count
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `,
    params: [
      context.sessionId,
      message.picUrl,
      JSON.stringify(result),
      result.device_type,
      result.status,
      result.confidence,
      result.findings?.length > 0,
      result.findings?.length || 0
    ]
  });
  
  // 返回给用户
  return formatAnalysisReport(result);
}
```

### 2. 批量分析处理

```typescript
async function handleBatchAnalysis(sessionId: string, context: Context) {
  const session = await getSession(sessionId);
  const photos = session.collectedData.photos;
  
  if (photos.length === 0) {
    return "没有待分析的照片";
  }
  
  // 发送进度通知
  await context.send(`🔍 正在分析 ${photos.length} 张照片...`);
  
  // 分批处理（每批 10 张）
  const batchSize = 10;
  
  for (let i = 0; i < photos.length; i += batchSize) {
    const batch = photos.slice(i, i + batchSize);
    
    // 调用 LLM 批量分析（OpenClaw 自动处理多图输入）
    const result = await context.llm.chat({
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: BATCH_PROMPT },
          ...batch.map(p => ({ 
            type: 'image_url', 
            image_url: { url: p.url } 
          }))
        ]
      }]
    });
    
    // 解析并保存
    const analysis = JSON.parse(result.content);
    await saveBatchResult(sessionId, analysis);
    
    // 发送进度
    if (photos.length > batchSize) {
      await context.send(`✓ 已完成 ${Math.min(i + batchSize, photos.length)}/${photos.length}`);
    }
  }
  
  // 生成最终报告
  return generateAnalysisReport(sessionId);
}
```

## 用户交互示例

### 单图分析回复

```
🔍 分析结果：

📷 照片：变压器整体
🔧 设备类型：箱式变压器（SCB11-800kVA）
📊 状态：🟡 注意
✅ 置信度：92%

⚠️ 发现 1 处问题：
• 【注意】变压器油位偏低
  建议：补充变压器油，检查是否有渗漏点

💡 下一步建议：
拍摄变压器低压侧接线情况
```

### 批量分析完成

```
✅ 照片分析完成（共 8 张）

📊 整体评估：
• 配电房：阳光社区#1 配电房
• 设备数量：6 台
• 整体状态：🟡 注意
• 发现问题：2 处

📋 设备清单：
1. 🟡 变压器 - 注意（油位偏低）
2. 🟢 高压柜 - 正常
3. 🟡 低压柜 - 注意（门锁损坏）
4. 🟢 计量柜 - 正常
5. 🟢 电缆沟 - 正常

⚡ 优先处理：
1. 补充变压器油
2. 更换低压柜门锁

📄 详细报告已生成
```

## 配置说明

### 在 openclaw.config.yaml 中配置

```yaml
# LLM 配置（定义 Prompt 模板）
llm:
  kimi:
    vision_analysis:
      enabled: true
      system_prompt: |
        你是电力设备检测专家...
      prompts:
        single_image: |
          请分析这张电力设备照片...
        batch_images: |
          请批量分析这组照片...

# Skill 配置（定义触发器和运行时参数）
skills:
  vision_analysis:
    enabled: true
    triggers:
      - type: message_type
        value: image
      - type: command
        pattern: "分析.*照片|批量分析"
    config:
      auto_analyze: true
      batch_size: 10
      async_mode: true
      timeout: 300
      save_results: true
      confidence_threshold: 0.7

# Tool 配置（数据库连接）
tools:
  postgres_query:
    enabled: true
    config:
      host: "${POSTGRES_HOST}"
      # ...
```

## 错误处理

### 分析失败

```typescript
async function handleAnalysisError(error: Error, context: Context) {
  // 记录错误
  await logError(error);
  
  // 降级处理
  return `⚠️ 照片分析遇到问题：${error.message}
  
您可以：
• 重新发送照片
• 手动描述设备情况
• 联系技术支持`;
}
```

### 超时处理

```typescript
const ANALYSIS_TIMEOUT = 300000; // 5 分钟

async function analyzeWithTimeout(photos: Photo[]) {
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('分析超时')), ANALYSIS_TIMEOUT);
  });
  
  try {
    return await Promise.race([
      analyzePhotos(photos),
      timeoutPromise
    ]);
  } catch (error) {
    if (error.message === '分析超时') {
      // 分批重试
      return analyzeInBatches(photos, 5); // 更小的批次
    }
    throw error;
  }
}
```

## 数据存储

### 数据库表结构

详见 `workspace/database/schema.sql` 中的 `photo_analysis` 和 `batch_analysis` 表。

### 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `analysis_id` | UUID | 分析记录 ID |
| `session_id` | UUID | 关联的工作会话 |
| `photo_url` | VARCHAR | 照片存储地址 |
| `result` | JSONB | 完整分析结果 |
| `device_type` | VARCHAR | 设备类型 |
| `status` | VARCHAR | 状态评估 |
| `confidence` | DECIMAL | 置信度 |

---

**版本**: 2.0.0  
**作者**: PM Agent  
**更新日期**: 2026-03-18  
**变更**: 修正为 OpenClaw 标准 SKILL.md 格式
