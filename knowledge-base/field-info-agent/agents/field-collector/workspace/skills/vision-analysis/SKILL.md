---
name: vision-analysis
description: |
  AI照片智能分析技能
  
  使用OpenClaw配置的多模态模型（KIMI 2.5）对现场照片进行智能分析。
  支持单图分析和批量分析，识别电力设备、检测缺陷、评估状态。
  
  核心能力：
  - 设备类型识别（变压器、高压柜、低压柜、电缆等）
  - 缺陷检测（漏油、锈蚀、松动、过热等）
  - 状态评估（正常、注意、异常、危险）
  - 安全隐患识别
  
  实现方式：直接调用OpenClaw LLM多模态能力，无需额外Tool封装

metadata:
  openclaw:
    emoji: 🔍
    category: ai
    requires:
      tools:
        - postgres-query    # 仅用于保存分析结果
        - minio-storage     # 仅用于照片存储
      channels:
        - wecom
    triggers:
      - type: message
        condition: image_received
      - type: command
        condition: analyze_photos
---

# Vision Analysis - AI照片智能分析技能（简化版）

## 概述

本技能利用OpenClaw的多模态能力，直接调用配置的KIMI 2.5模型对现场照片进行分析。无需开发额外的Tool，只需在Skill中定义好Prompt模板和分析逻辑。

## 核心设计

### 利用OpenClaw原生能力

```
用户发送图片 → OpenClaw Channel接收 → OpenClaw LLM多模态分析 → Skill解析结果 → 保存到DB
```

**关键点**：OpenClaw会自动将图片传给配置的多模态模型，Skill只需要：
1. 提供分析Prompt
2. 接收并解析JSON结果
3. 保存到PostgreSQL
4. 返回给用户

## 分析Prompt模板

### 单图分析Prompt（配置在openclaw.config.yaml）

```
你是电力设备检测专家。请分析用户上传的现场照片。

分析要求：
1. 识别设备类型（变压器/高压柜/低压柜/电缆/计量装置/其他）
2. 评估整体状态（正常/注意/异常/危险）
3. 检查以下缺陷：
   - 外观：锈蚀、变形、破损、油污
   - 连接：松动、脱落、接触不良
   - 绝缘：老化、裂纹、放电痕迹
   - 运行：漏油、过热、异响
   - 标识：缺失、模糊、错误
4. 识别安全隐患
5. 给出处理建议

必须按JSON格式输出：
{
  "device_type": "设备类型",
  "device_subtype": "子类型",
  "status": "normal|attention|abnormal|danger",
  "confidence": 0-1,
  "findings": [
    {
      "category": "缺陷类别",
      "description": "具体描述",
      "severity": "low|medium|high|critical"
    }
  ],
  "safety_issues": ["隐患1", "隐患2"],
  "recommendations": ["建议1", "建议2"],
  "summary": "一句话摘要"
}
```

### 批量分析Prompt

```
你正在分析同一配电房的多张照片。请批量分析并给出整体评估。

照片数量: {{photo_count}}
社区: {{community_name}}

要求：
1. 分别分析每张照片
2. 识别设备间的关联问题
3. 发现共性问题
4. 给出整体评估和优先处理建议

输出JSON格式：
{
  "overall_status": "normal|attention|abnormal|danger",
  "total_devices": 数量,
  "issues_found": 问题数,
  "critical_issues": 严重问题数,
  "per_image": [单图分析结果],
  "common_issues": ["共性问题"],
  "priority_actions": ["优先处理1", "优先处理2"],
  "summary": "整体评估摘要"
}
```

## 实现逻辑

### 1. 接收图片并分析（单图）

```typescript
// Skill处理函数
async function handleImage(message: ImageMessage, context: Context) {
  // OpenClaw已经自动将图片传给LLM分析
  // 我们只需要从context中获取分析结果
  const analysisResult = context.llmResponse
  
  // 解析JSON
  const result = JSON.parse(analysisResult.content)
  
  // 保存到数据库
  await saveAnalysisResult({
    sessionId: context.sessionId,
    imageUrl: message.picUrl,
    result: result,
    analyzedAt: new Date()
  })
  
  // 返回给用户
  return formatAnalysisReport(result)
}
```

### 2. 批量分析实现

```typescript
async function handleBatchAnalysis(sessionId: string) {
  const session = await getSession(sessionId)
  const photos = session.collectedData.photos
  
  if (photos.length === 0) return
  
  // 发送进度通知
  await sendMessage(`🔍 正在分析${photos.length}张照片...`)
  
  // OpenClaw支持多图输入，直接批量分析
  // 如果照片太多，分批处理
  const batchSize = 10  // KIMI支持一次10张
  
  for (let i = 0; i < photos.length; i += batchSize) {
    const batch = photos.slice(i, i + batchSize)
    
    // 调用LLM批量分析
    const result = await context.llm.chat({
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: BATCH_PROMPT },
          ...batch.map(p => ({ type: 'image_url', image_url: { url: p.url } }))
        ]
      }]
    })
    
    // 解析并保存
    const analysis = JSON.parse(result.content)
    await saveBatchResult(sessionId, analysis)
    
    // 发送进度
    if (photos.length > batchSize) {
      await sendMessage(`✓ 已完成 ${Math.min(i + batchSize, photos.length)}/${photos.length}`)
    }
  }
  
  // 生成最终报告
  const finalReport = await generateAnalysisReport(sessionId)
  await sendMessage(finalReport)
}
```

## 数据存储

### 分析结果表（PostgreSQL）

```sql
-- 照片分析结果表
CREATE TABLE photo_analysis (
  analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  photo_url VARCHAR(500) NOT NULL,
  photo_hash VARCHAR(64),           -- 图片哈希，用于去重
  
  -- 分析结果（JSON存储）
  result JSONB NOT NULL,
  
  -- 关键字段（冗余存储便于查询）
  device_type VARCHAR(50),
  status VARCHAR(20),               -- normal/attention/abnormal/danger
  confidence DECIMAL(3,2),
  has_issues BOOLEAN DEFAULT false,
  issue_count INTEGER DEFAULT 0,
  
  -- 元数据
  analyzed_at TIMESTAMP DEFAULT NOW(),
  model_version VARCHAR(20),        -- AI模型版本
  
  FOREIGN KEY (session_id) REFERENCES field_sessions(session_id)
);

-- 索引
CREATE INDEX idx_analysis_session ON photo_analysis(session_id);
CREATE INDEX idx_analysis_status ON photo_analysis(status);
CREATE INDEX idx_analysis_device ON photo_analysis(device_type);
```

### 保存分析结果

```typescript
async function saveAnalysisResult(data: AnalysisData) {
  const query = `
    INSERT INTO photo_analysis (
      session_id, photo_url, photo_hash, result,
      device_type, status, confidence, has_issues, issue_count
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    RETURNING analysis_id
  `
  
  const result = data.result
  const hasIssues = result.findings && result.findings.length > 0
  
  await postgres.query(query, [
    data.sessionId,
    data.photoUrl,
    data.photoHash,
    JSON.stringify(result),
    result.device_type,
    result.status,
    result.confidence,
    hasIssues,
    result.findings?.length || 0
  ])
}
```

## 用户交互

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
✅ 照片分析完成（共8张）

📊 整体评估：
• 配电房：阳光社区#1配电房
• 设备数量：6台
• 整体状态：🟡 注意
• 发现问题：2处

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

## 与OpenClaw集成配置

### 在openclaw.config.yaml中配置

```yaml
llm:
  default_provider: kimi
  
  kimi:
    api_key: "${KIMI_API_KEY}"
    base_url: "https://api.moonshot.cn/v1"
    model: "kimi-k2.5"
    temperature: 0.3
    max_tokens: 4096
    
    # 多模态分析专用配置
    vision_analysis:
      system_prompt: |
        你是电力设备检测专家。用户会发送电力设备照片，请进行专业分析。
        必须按JSON格式返回分析结果。
      
      # 分析提示词模板
      prompts:
        single_image: |
          请分析这张电力设备照片，按JSON格式返回：
          {
            "device_type": "设备类型",
            "status": "normal|attention|abnormal|danger",
            "findings": [...],
            "recommendations": [...],
            "summary": "摘要"
          }
        
        batch_images: |
          请批量分析这组{{count}}张配电房照片，给出整体评估...

skills:
  vision_analysis:
    enabled: true
    triggers:
      - message_type: image
    config:
      auto_analyze: true
      save_results: true
      confidence_threshold: 0.7
```

## 优势总结

✅ **简化实现**：无需开发TypeScript Tool，直接利用OpenClaw能力  
✅ **维护简单**：模型升级自动受益  
✅ **配置灵活**：Prompt可在配置文件中调整  
✅ **性能保障**：利用OpenClaw的异步处理能力  
✅ **成本优化**：减少一层封装，降低复杂度  

---

**版本**: 1.0.0（简化版）  
**作者**: PM Agent  
**更新**: 2026-03-18  
**变更**: 移除独立Tool封装，直接使用OpenClaw多模态能力
