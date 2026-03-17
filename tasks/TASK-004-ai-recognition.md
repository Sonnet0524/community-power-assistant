# Task-004: 语音识别与OCR集成

## 任务概述

**任务ID**: TASK-004  
**任务名称**: 语音识别与OCR集成  
**优先级**: 🟡 高  
**预计工期**: 3-4天  
**依赖**: TASK-001, TASK-003

## 任务目标

集成语音识别和OCR能力，实现：
1. 语音消息转文字（百度语音识别）
2. 图片OCR识别（PaddleOCR）
3. 变压器铭牌结构化识别
4. 置信度评估和人工确认机制

## 详细工作内容

### 1. 百度语音识别集成

**接口设计**:
```typescript
interface BaiduSTTTool {
  recognize(params: {
    audioData: Buffer | string  // 音频数据或URL
    format: 'pcm' | 'wav' | 'amr' | 'm4a'
    sampleRate: 16000 | 8000
    devPid: number  // 语言模型ID
  }): Promise<{
    text: string
    confidence: number
    errCode: number
    errMsg: string
  }>
}

// 语言模型常量
const LANGUAGE_MODELS = {
  MANDARIN: 1537,        // 普通话
  MANDARIN_FAR: 1536,    // 普通话远场
  SICHUAN: 1837,         // 四川话（推荐）
  CANTONESE: 1637,       // 粤语
  ENGLISH: 1737,         // 英语
}
```

**工作内容**:
- [ ] 注册百度AI开放平台账号
- [ ] 创建语音识别应用，获取API Key和Secret Key
- [ ] 实现Token获取和刷新（百度Token有效期30天）
- [ ] 实现语音识别API调用
- [ ] 实现AMR转WAV格式转换（如需要）
- [ ] 实现置信度评估
- [ ] 实现错误处理和重试

**音频格式处理**:
```typescript
// AMR转WAV（如企业微信语音需要转换）
async function convertAmrToWav(amrBuffer: Buffer): Promise<Buffer> {
  // 使用ffmpeg或专用库转换
}

// 音频预处理
async function preprocessAudio(audioBuffer: Buffer): Promise<Buffer> {
  // 降噪、音量归一化等
}
```

**置信度评估**:
```typescript
function evaluateConfidence(result: STTResult): 'high' | 'medium' | 'low' {
  if (result.confidence >= 0.9) return 'high'
  if (result.confidence >= 0.7) return 'medium'
  return 'low'
}
```

### 2. PaddleOCR集成

**部署方案选择**:

**方案A：本地部署（推荐）**
```yaml
部署方式: Docker容器
镜像: paddleocr/paddleocr:latest
端口: 8000
资源配置:
  CPU: 2核+
  内存: 4GB+
  磁盘: 10GB
```

**方案B：云服务API**
- 百度OCR API
- 腾讯OCR API
- 阿里OCR API

**接口设计**:
```typescript
interface PaddleOCRTool {
  // 通用文字识别
  recognizeText(params: {
    imageUrl: string
    language?: 'ch' | 'en' | 'ch_en'
  }): Promise<{
    texts: Array<{
      content: string
      confidence: number
      position: [number, number, number, number]  // 四角坐标
    }>
  }>
  
  // 结构化识别（变压器铭牌）
  recognizeNameplate(params: {
    imageUrl: string
  }): Promise<{
    fields: {
      model?: string        // 型号
      capacity?: string    // 容量
      voltage?: string     // 电压
      manufacturer?: string // 制造商
      serialNumber?: string // 序列号
      manufactureDate?: string // 生产日期
    }
    confidence: number
  }>
}
```

**工作内容**:
- [ ] 部署PaddleOCR服务（Docker）
- [ ] 实现通用文字识别
- [ ] 实现变压器铭牌专用识别模型（可选优化）
- [ ] 实现图片预处理（旋转、裁剪、增强）
- [ ] 实现结果后处理（字段提取、格式化）

**铭牌识别优化**:
```typescript
// 铭牌字段提取规则
const NAMEPLATE_PATTERNS = {
  model: [/型号[：:]?\s*([A-Z0-9\-]+)/i, /Model[：:]?\s*([A-Z0-9\-]+)/i],
  capacity: [/容量[：:]?\s*(\d+)\s*[Kk]?[Vv]?[Aa]?/, /Capacity[：:]?\s*(\d+)/],
  voltage: [/电压[：:]?\s*([\d/]+)[Kk]?[Vv]?/, /Voltage[：:]?\s*([\d/]+)/],
  manufacturer: [/制造商[：:]?\s*([^\n]+)/, /Manufacturer[：:]?\s*([^\n]+)/],
}

// 提取字段
function extractFields(texts: string[]): NameplateData {
  const data: NameplateData = {}
  const fullText = texts.join(' ')
  
  for (const [field, patterns] of Object.entries(NAMEPLATE_PATTERNS)) {
    for (const pattern of patterns) {
      const match = fullText.match(pattern)
      if (match) {
        data[field] = match[1].trim()
        break
      }
    }
  }
  
  return data
}
```

### 3. 智能识别服务

**服务设计**:
```typescript
class SmartRecognitionService {
  constructor(
    private sttTool: BaiduSTTTool,
    private ocrTool: PaddleOCRTool
  ) {}
  
  // 语音转文字并提取信息
  async processVoice(audioData: Buffer, context: string): Promise<{
    text: string
    extractedInfo: Record<string, any>
    confidence: number
  }>
  
  // 图片识别并提取信息
  async processImage(imageUrl: string, type: 'nameplate' | 'general'): Promise<{
    texts: string[]
    structuredData: Record<string, any>
    confidence: number
  }>
}
```

**上下文感知识别**:
```typescript
// 根据当前采集阶段，优化识别结果
async function recognizeWithContext(
  audioData: Buffer,
  context: CollectionContext
): Promise<RecognitionResult> {
  const result = await sttTool.recognize({
    audioData,
    format: 'amr',
    devPid: LANGUAGE_MODELS.SICHUAN  // 根据地区选择方言
  })
  
  // 根据上下文提取特定信息
  switch (context.phase) {
    case 'power_room_location':
      return extractLocationInfo(result.text)
    case 'equipment_status':
      return extractStatusInfo(result.text)
    case 'customer_feedback':
      return extractFeedbackInfo(result.text)
    default:
      return { text: result.text, extractedInfo: {} }
  }
}
```

### 4. 置信度评估与人工确认

**置信度评估策略**:
```typescript
interface ConfidenceAssessment {
  level: 'high' | 'medium' | 'low'
  score: number
  needsConfirmation: boolean
  suggestions: string[]
}

function assessConfidence(
  recognitionResult: RecognitionResult,
  context: CollectionContext
): ConfidenceAssessment {
  let score = recognitionResult.confidence
  
  // 根据上下文调整置信度
  if (context.phase === 'nameplate' && !recognitionResult.structuredData.model) {
    score -= 0.2  // 关键字段缺失，降低置信度
  }
  
  // 规则检查
  const validations = validateResult(recognitionResult, context)
  if (validations.length > 0) {
    score -= validations.length * 0.1
  }
  
  return {
    level: score >= 0.9 ? 'high' : score >= 0.7 ? 'medium' : 'low',
    score,
    needsConfirmation: score < 0.9,
    suggestions: validations
  }
}
```

**人工确认流程**:
```
识别结果 → 置信度评估 → 是否需确认？
    ↓
    是 → 发送确认消息给用户
         ↓
         用户确认/修正
         ↓
         保存最终结果
    ↓
    否 → 直接保存结果
```

**确认消息模板**:
```
🔍 识别结果（置信度：85%）

型号：SCB11-500/10
容量：500kVA
厂家：某某电气

⚠️ 请确认以上信息是否正确：
[正确] [修改] [重新拍摄]

如修改，请直接发送正确信息。
```

### 5. 缓存与优化

**识别结果缓存**:
```typescript
// 缓存相同图片的识别结果
async function recognizeWithCache(imageUrl: string): Promise<OCRResult> {
  const cacheKey = `ocr:${hash(imageUrl)}`
  const cached = await redis.get(cacheKey)
  
  if (cached) {
    return JSON.parse(cached)
  }
  
  const result = await ocrTool.recognizeText({ imageUrl })
  await redis.setex(cacheKey, 86400, JSON.stringify(result))  // 缓存1天
  return result
}
```

**图片预处理优化**:
```typescript
async function preprocessImage(imageBuffer: Buffer): Promise<Buffer> {
  // 1. 自动旋转（根据EXIF信息）
  // 2. 图像增强（对比度、亮度）
  // 3. 裁剪（去除边缘空白）
  // 4. 尺寸调整（控制在2MB以内）
  // 5. 格式转换（统一为JPG）
}
```

## 测试要求

### 语音识别测试
- [ ] 普通话识别准确率 > 95%
- [ ] 四川话识别准确率 > 90%
- [ ] 带背景噪音识别准确率 > 85%
- [ ] 响应时间 < 3秒

### OCR识别测试
- [ ] 通用文字识别准确率 > 90%
- [ ] 变压器铭牌关键字段识别准确率 > 85%
- [ ] 不同光线条件下识别准确率 > 80%
- [ ] 响应时间 < 5秒

### 集成测试
- [ ] 端到端语音采集-识别-存储流程
- [ ] 端到端图片采集-OCR-存储流程
- [ ] 置信度评估准确性
- [ ] 人工确认流程

### 测试数据准备
- [ ] 准备100+条语音测试样本
- [ ] 准备50+张变压器铭牌照片
- [ ] 覆盖不同光线、角度、清晰度

## 交付物

1. **百度语音Tool**: `src/tools/baidu-stt/`
2. **PaddleOCR Tool**: `src/tools/paddle-ocr/`
3. **智能识别服务**: `src/services/recognition/`
4. **部署文档**: `docs/deployment/ocr-setup.md`
5. **测试报告**: `tests/recognition/`

## 验收标准

- [ ] 语音识别准确率达标
- [ ] OCR识别准确率达标
- [ ] 置信度评估准确
- [ ] 人工确认流程可用
- [ ] 性能指标达标
- [ ] 错误处理完善

## 注意事项

1. **百度Token有效期30天**，需定期刷新
2. **PaddleOCR首次启动较慢**，需预热
3. **图片大小控制在2MB以内**，超过需压缩
4. **识别失败后必须有备选方案**（人工输入）
5. **敏感图片需本地处理**，避免上传到第三方

## 成本估算

**百度语音识别**:
- 免费额度：50000次/天
- 超出部分：约¥0.002/次
- 预计月费用：¥0-200

**PaddleOCR本地部署**:
- 服务器成本：已包含在基础设施中
- 无额外API费用

## 相关文档

- [详细设计方案 - AI能力](../design/detailed-design-v2.md#tools详细设计)
- 百度语音识别文档：https://ai.baidu.com/tech/speech
- PaddleOCR文档：https://github.com/PaddlePaddle/PaddleOCR

---

**创建时间**: 2026-03-17  
**负责人**: 待分配  
**状态**: 待开始  
**依赖**: TASK-001完成，TASK-003完成
