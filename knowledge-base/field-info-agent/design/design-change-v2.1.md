# Field Info Agent - 设计变更说明（v2.1）

**变更日期**: 2026-03-17  
**变更类型**: 需求调整  
**影响范围**: 技术架构、开发任务  

---

## 一、变更内容

### 1.1 语音输入 → 文字输入

**原设计**:
- 企业微信接收语音消息（AMR格式）
- 百度语音识别转文字
- 支持四川话识别

**变更为**:
- ✅ **仅接收文字消息**
- 用户可使用手机语音输入法自行转文字后发送
- Agent只处理文字内容

**原因**:
- 简化技术架构
- 降低开发复杂度
- 用户习惯：现场人员已习惯语音输入法
- 减少外部依赖（百度语音API）

**影响**:
- 移除TASK-004中的语音识别部分
- 移除百度语音API依赖
- 降低月成本约¥200

---

### 1.2 PaddleOCR → Agent多模态识图

**原设计**:
- 部署PaddleOCR本地服务
- 识别变压器铭牌、电表等信息
- 结构化提取字段

**变更为**:
- ✅ **使用Agent多模态模型识图**（如GPT-4V/Claude 3 Vision）
- Agent直接分析图片内容
- 理解图片中的文字、设备、场景

**优势**:
- 无需部署OCR服务
- 识别能力更强（不仅文字，还能理解场景）
- 可识别设备状态（如"变压器漏油"）
- 自然语言交互，无需固定模板

**示例交互**:
```
用户: [发送变压器铭牌照片]

Agent: "我看到这是一台变压器铭牌，让我识别一下关键信息：
- 型号：SCB11-500/10
- 容量：500kVA
- 制造商：某某电气有限公司
- 出厂日期：2015年6月

以上信息是否正确？"
```

---

### 1.3 新增：批量照片智能分析

**新需求**:
驻点工作会收集大量现场照片（配电房、设备、隐患等），需要在收集完毕后，**用模型对所有照片进行批量分析**。

**应用场景**:
1. **设备状态评估**: 分析所有设备照片，判断运行状态
2. **隐患自动发现**: 从照片中识别安全隐患
3. **完整性检查**: 检查是否遗漏关键设备
4. **生成分析报告**: 基于照片内容生成分析报告

**工作流程**:
```
驻点工作采集中
    ↓
用户持续发送照片（5-10张或更多）
    ↓
Agent: 保存所有照片到WPS
    ↓
用户: "完成采集"
    ↓
Agent触发批量分析
    ↓
模型分析所有照片
    ↓
生成分析报告
    ↓
用户确认或补充
```

---

## 二、更新后的技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                         用户层                                │
│              企业微信APP（拍照 + 文字输入）                    │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS回调
┌────────────────────────────▼─────────────────────────────────┐
│                   OpenClaw Gateway                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ WeCom Channel│ │Session Manager│ │     Skills          │  │
│  └──────────────┘ └──────────────┘ └──────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Tools: WPS API | LLM Vision | WeCom API                │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼─────────────────────────────────┐
│                      外部服务层                              │
│      LLM多模态模型      WPS开放平台       企业微信服务器      │
│   (GPT-4V/Claude 3)                                       │
└──────────────────────────────────────────────────────────────┘
```

**技术栈更新**:
- ✅ 移除：百度语音识别
- ✅ 移除：PaddleOCR
- ✅ 新增：多模态LLM（如GPT-4V、Claude 3 Opus、Gemini Pro Vision）

---

## 三、更新后的消息交互设计

### 3.1 支持的输入类型

| 输入类型 | 支持情况 | 处理方式 |
|---------|---------|---------|
| **文字消息** | ✅ 支持 | 直接处理 |
| **图片消息** | ✅ 支持 | 保存后分析 |
| **位置信息** | ✅ 支持 | 提取GPS坐标 |
| ~~语音消息~~ | ❌ 不支持 | 用户转文字后发送 |

### 3.2 交互示例（更新后）

**场景1：配电房位置描述**
```
原方案:
用户: [语音] "3号楼地下室"
Agent: 语音识别 → 提取位置

新方案:
用户: [文字] "3号楼地下室，进门左转"
Agent: 直接处理文字内容
```

**场景2：变压器铭牌识别**
```
用户: [发送照片]

Agent: 我看到这是一张变压器铭牌照片，识别信息如下：

🔍 识别结果：
• 型号：SCB11-500/10
• 容量：500kVA  
• 制造商：某某电气
• 出厂日期：2015-06

⚠️ 注意：铭牌显示出厂日期是2015年，已运行9年，建议关注设备老化情况。

以上信息是否正确？
[正确] [需要修改]
```

**场景3：批量照片分析**
```
用户完成配电房采集，发送了8张照片

Agent: 
📊 照片智能分析报告
───────────────────

已分析8张照片，识别内容如下：

📷 照片1-2：配电房入口
✓ 通道畅通，无明显障碍
✓ 门牌标识清晰

📷 照片3-4：变压器铭牌  
✓ 识别到2台变压器
• 1号：SCB11-500kVA，2015年投运
• 2号：SCB11-800kVA，2018年投运

📷 照片5-6：设备运行状态
✓ 外观正常，无漏油
⚠️ 发现：2号变压器温度指示贴显示偏黄（需关注）

📷 照片7-8：配电房环境
✓ 照明正常
✓ 通风良好
⚠️ 发现：墙角有轻微渗水痕迹

🔴 建议关注：
1. 2号变压器运行温度偏高
2. 配电房墙角渗水，需检查防水

是否生成详细报告？
[生成报告] [补充说明] [忽略]
```

---

## 四、多模态识图能力设计

### 4.1 Vision Analysis Tool

```typescript
interface VisionAnalysisTool {
  name: 'vision_analysis'
  version: '1.0.0'
  
  // 单图分析
  analyzeSingleImage(params: {
    imageUrl: string
    context?: string  // 分析上下文（如"变压器铭牌"、"设备状态"）
    questions?: string[]  // 特定问题
  }): Promise<{
    description: string  // 图片描述
    textContent?: string  // 识别到的文字
    objects: Array<{
      name: string
      confidence: number
      bbox?: [number, number, number, number]
    }>
    insights: string[]  // 关键发现
    concerns?: string[]  // 潜在问题
  }>
  
  // 批量分析（多张照片）
  analyzeBatchImages(params: {
    imageUrls: string[]
    analysisType: 'equipment_status' | 'safety_check' | 'completeness' | 'comprehensive'
    context?: string
  }): Promise<{
    summary: string  // 总体摘要
    perImageAnalysis: Array<{
      imageUrl: string
      findings: string[]
    }>
    overallFindings: string[]  // 整体发现
    recommendations: string[]  // 建议
    missingItems?: string[]  // 可能遗漏的项目
  }>
  
  // 对比分析（新旧照片对比）
  compareImages(params: {
    oldImageUrl: string
    newImageUrl: string
    focus?: string[]  // 对比关注点
  }): Promise<{
    changes: Array<{
      type: 'added' | 'removed' | 'modified'
      description: string
      severity: 'low' | 'medium' | 'high'
    }>
    summary: string
  }>
}
```

### 4.2 分析类型

```yaml
analysis_types:
  equipment_status:
    name: 设备状态评估
    description: 分析设备运行状态、外观完整性
    output:
      - 设备类型识别
      - 运行状态判断
      - 异常发现（漏油、锈蚀、损坏等）
      - 建议措施
      
  safety_check:
    name: 安全检查
    description: 识别安全隐患
    output:
      - 安全隐患列表
      - 风险等级
      - 整改建议
      - 法规符合性评估
      
  completeness:
    name: 完整性检查
    description: 检查是否遗漏关键设备或信息
    output:
      - 已采集设备清单
      - 缺失设备提醒
      - 建议补充采集项
      
  comprehensive:
    name: 综合分析
    description: 全面分析所有照片，生成综合报告
    output:
      - 总体评估
      - 分类发现
      - 优先级排序
      - 行动建议
```

### 4.3 Prompt设计示例

**单图分析Prompt**:
```
你是一位电力设备专家，正在分析现场拍摄的照片。

请分析这张图片，重点关注：
1. 设备类型和型号（如有铭牌请识别）
2. 设备运行状态（正常/异常）
3. 可见的缺陷或隐患
4. 环境状况

请以结构化方式输出：
- 设备识别结果
- 状态评估
- 发现的问题（如有）
- 建议措施

图片URL: {image_url}
上下文: {context}
```

**批量分析Prompt**:
```
你是一位供电所现场工作专家，需要分析一次驻点工作收集的所有照片。

共有{count}张照片，请进行综合分析：

1. 识别所有设备及其状态
2. 发现安全隐患
3. 检查是否有遗漏的关键设备
4. 评估整体工作质量

请输出：
- 总体摘要
- 每张照片的关键发现
- 整体问题清单（按优先级排序）
- 建议补充的采集项（如有）
- 后续工作建议

照片列表: {image_urls}
```

---

## 五、更新后的开发任务

### TASK-004 变更：AI能力集成

**原任务**: 语音识别与OCR集成  
**新任务**: **多模态识图能力集成**

**工作内容更新**:
```yaml
移除:
  - 百度语音识别集成
  - PaddleOCR部署和集成
  
新增:
  - 多模态LLM选型（GPT-4V / Claude 3 / Gemini）
  - Vision Analysis Tool开发
  - 单图分析能力
  - 批量照片分析能力
  - 对比分析能力
  - Prompt工程优化
```

**技术方案**:
```typescript
// VisionAnalysisTool实现
class VisionAnalysisTool {
  private llmClient: LLMClient
  
  async analyzeSingleImage(params: AnalyzeParams): Promise<AnalysisResult> {
    const prompt = buildSingleImagePrompt(params)
    const response = await this.llmClient.chat.completions.create({
      model: 'gpt-4-vision-preview',
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: params.imageUrl } }
        ]
      }]
    })
    return parseAnalysisResponse(response)
  }
  
  async analyzeBatchImages(params: BatchAnalyzeParams): Promise<BatchResult> {
    // 分批处理（模型可能有限制）
    const batches = chunk(params.imageUrls, 5)
    const results = []
    
    for (const batch of batches) {
      const prompt = buildBatchPrompt(batch, params.analysisType)
      const response = await this.llmClient.chat.completions.create({
        model: 'gpt-4-vision-preview',
        messages: [{
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            ...batch.map(url => ({
              type: 'image_url',
              image_url: { url }
            }))
          ]
        }]
      })
      results.push(parseBatchResponse(response))
    }
    
    return mergeBatchResults(results)
  }
}
```

### TASK-005 变更：StationWorkGuide Skill

**更新内容**:
- 移除语音识别相关逻辑
- 仅处理文字消息
- 集成Vision Analysis Tool
- 新增批量照片分析触发点

**关键更新点**:
```typescript
// 照片处理更新
async function handlePhoto(message: Message, session: Session) {
  // 1. 下载并保存照片
  const photoUrl = await savePhoto(message.mediaId)
  session.collectedData.photos.push(photoUrl)
  
  // 2. 实时简单分析（可选）
  if (session.settings.realtimeAnalysis) {
    const quickAnalysis = await visionTool.analyzeSingleImage({
      imageUrl: photoUrl,
      context: session.currentPhase
    })
    await sendQuickFeedback(message.userId, quickAnalysis)
  }
  
  // 3. 继续采集或等待批量分析
  await sessionManager.save(session)
}

// 完成采集后批量分析
async function performBatchAnalysis(session: Session) {
  if (session.collectedData.photos.length === 0) return
  
  await sendMessage(session.userId, '🔍 正在分析所有照片，请稍候...')
  
  const analysis = await visionTool.analyzeBatchImages({
    imageUrls: session.collectedData.photos,
    analysisType: 'comprehensive',
    context: `小区：${session.communityName}，驻点工作采集`
  })
  
  // 保存分析结果
  session.collectedData.photoAnalysis = analysis
  
  // 发送分析报告
  await sendAnalysisReport(session.userId, analysis)
}
```

---

## 六、成本变化

### 原方案月成本

| 项目 | 成本 |
|------|------|
| 云服务器 | ¥400 |
| Redis | ¥150 |
| WPS API | ¥300 |
| 百度语音 | ¥150 |
| PaddleOCR部署 | ¥0（自有服务器） |
| **总计** | **¥1000** |

### 新方案月成本（使用KIMI K2.5）

| 项目 | 成本 | 说明 |
|------|------|------|
| 云服务器 | ¥400 | |
| Redis | ¥150 | |
| WPS API | ¥300 | |
| **KIMI K2.5 API** | **¥200-400** | 图像分析约¥0.003-0.006/张 |
| **总计** | **¥1050-1250** | |

**变化**:
- 移除百度语音：-¥150
- 新增KIMI K2.5：+¥200-400
- 净增加：+¥50-250/月

**KIMI K2.5 价格参考**:
- 图像输入：约¥0.003-0.006/张（按token计费）
- 文字输出：约¥0.012/千token
- 一次照片分析（含文字说明）约¥0.05-0.1

---

## 七、Prompt模板库

### 7.1 变压器铭牌识别

```yaml
name: transformer_nameplate
prompt: |
  分析这张变压器铭牌照片，提取以下信息：
  1. 型号（Model）
  2. 容量（Capacity，单位kVA）
  3. 额定电压（Voltage）
  4. 制造商（Manufacturer）
  5. 出厂日期或序列号
  6. 其他技术参数
  
  请以JSON格式输出：
  {
    "model": "型号",
    "capacity": "容量",
    "voltage": "电压",
    "manufacturer": "制造商",
    "serialNumber": "序列号",
    "manufactureDate": "出厂日期",
    "otherParams": "其他参数"
  }
  
  如果某些信息无法识别，请标注为"未识别"。
```

### 7.2 设备状态评估

```yaml
name: equipment_status
prompt: |
  作为电力设备专家，分析这张设备照片：
  
  1. 设备类型识别
  2. 外观状态评估（正常/异常）
  3. 可见缺陷检查：
     - 是否有漏油？
     - 是否有锈蚀？
     - 是否有破损？
     - 是否有异物？
  4. 环境状态
  5. 安全风险等级（低/中/高）
  
  输出要求：
  - 设备类型
  - 状态评估
  - 发现的问题清单
  - 建议措施
  - 风险等级
```

### 7.3 配电房环境检查

```yaml
name: power_room_environment
prompt: |
  分析配电房环境照片，检查以下项目：
  
  安全检查项：
  □ 通道是否畅通
  □ 照明是否正常
  □ 通风是否良好
  □ 消防设施是否完备
  □ 有无漏水/渗水
  □ 有无杂物堆积
  □ 门窗是否完好
  
  请以清单形式输出检查结果，标注发现的问题。
```

---

## 八、实施建议

### 8.1 多模态LLM选型

**确定选型**: **KIMI K2.5** (Moonshot AI)

**KIMI K2.5 能力**:
- ✅ 支持图像理解（多模态）
- ✅ 长文本处理（200万字上下文）
- ✅ 中文优化，理解能力强
- ✅ 支持视觉问答
- ✅ 支持文档理解

**优势**:
- 国产模型，合规性好
- 中文场景优化
- 成本相对较低
- API稳定可靠

**使用方式**:
```typescript
const kimiClient = new OpenAI({
  baseURL: 'https://api.moonshot.cn/v1',
  apiKey: process.env.KIMI_API_KEY
})

// 图像分析
const response = await kimiClient.chat.completions.create({
  model: 'kimi-k2.5',
  messages: [{
    role: 'user',
    content: [
      { type: 'text', text: '分析这张变压器照片' },
      { type: 'image_url', image_url: { url: imageUrl } }
    ]
  }]
})
```

### 8.2 成本控制策略

```yaml
成本控制措施:
  1. 缓存机制:
     - 相同图片不重复分析
     - 缓存有效期：24小时
     
  2. 分级分析:
     - 实时采集：简单确认（低成本）
     - 完成采集：详细分析（高成本）
     
  3. 批量处理:
     - 多张照片一次性分析
     - 减少API调用次数
     
  4. 降级方案:
     - API限流时切换备选模型
     - 或提示用户稍后重试
```

### 8.3 准确度保障

```yaml
准确度提升措施:
  1. Prompt优化:
     - 提供明确的分析框架
     - 给出示例输出格式
     
  2. 上下文增强:
     - 提供小区信息、设备类型等背景
     - 说明分析目的
     
  3. 人工确认:
     - 关键信息（如铭牌数据）要求用户确认
     - 异常发现必须人工确认
     
  4. 多模型交叉验证:
     - 重要照片用多个模型分析
     - 对比结果，选择置信度高的
```

---

## 九、文档更新清单

### 已更新文档
- [x] 本变更说明文档（design-change-v2.1.md）

### 需要更新的文档
- [ ] detailed-design-v2.md
  - 移除语音识别章节
  - 更新Tools设计（移除OCR，新增Vision Analysis）
  - 更新交互流程（文字输入）
  - 新增批量照片分析章节
  
- [ ] technical-feasibility-analysis.md
  - 更新技术架构图
  - 更新成本估算
  - 更新风险评估
  
- [ ] TASK-004-ai-recognition.md
  - 重命名为：多模态识图能力集成
  - 完全重写内容
  
- [ ] TASK-005-station-work-skill.md
  - 移除语音识别逻辑
  - 新增Vision Analysis集成
  - 新增批量分析触发点

---

## 十、下一步行动

1. **确认多模态LLM选型**（本周）
   - 测试GPT-4V、Claude 3识别准确率
   - 确认成本预算
   - 申请API密钥

2. **更新设计文档**（本周）
   - 按照变更说明更新所有相关文档
   - 更新开发任务文档

3. **开发Vision Analysis Tool**（下周开始）
   - 实现基础识图能力
   - 测试各种电力设备照片
   - 优化Prompt

4. **测试批量分析能力**
   - 准备测试照片集
   - 测试分析准确率和速度
   - 调优参数

---

**变更记录**:
- 2026-03-17: 创建变更说明文档
- 调整：语音→文字、OCR→多模态LLM、新增批量分析

**审批状态**: 待确认  
**影响评估**: 中等（架构简化但新增AI能力）  
**建议**: 同意变更，新方案技术更先进，用户体验更好
