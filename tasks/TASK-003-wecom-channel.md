# Task-003: 企业微信Channel配置

## 任务概述

**任务ID**: TASK-003  
**任务名称**: 企业微信Channel配置  
**优先级**: 🔴 最高  
**预计工期**: 2-3天  
**依赖**: TASK-001

## 任务目标

配置企业微信Channel，实现与OpenClaw框架的集成，包括：
1. 企业微信Provider配置
2. 消息接收和解析
3. 媒体文件下载
4. 消息发送
5. Session管理集成

## 详细工作内容

### 1. 企业微信Provider配置

**配置内容**:
```yaml
# config/channels/wecom.yaml
channel:
  name: wecom
  type: official
  
  # 企业微信应用配置
  corp_id: "${WECOM_CORP_ID}"
  agent_id: "${WECOM_AGENT_ID}"
  secret: "${WECOM_SECRET}"
  
  # 回调配置
  callback:
    url: "https://your-domain.com/webhook/wecom"
    token: "${WECOM_TOKEN}"
    encoding_aes_key: "${WECOM_AES_KEY}"
  
  # 功能开关
  features:
    text_message: true
    voice_message: true
    image_message: true
    file_message: true
    location_message: true
  
  # 消息加解密
  encryption:
    enabled: true
    mode: "aes"  # aes/safe
```

**工作内容**:
- [ ] 配置企业微信应用参数
- [ ] 配置回调URL和加解密
- [ ] 配置消息类型支持
- [ ] 验证配置正确性

### 2. 消息接收处理

**消息类型处理**:

```typescript
// 消息处理器
class WeComMessageHandler {
  async handleText(message: TextMessage): Promise<void>
  async handleVoice(message: VoiceMessage): Promise<void>
  async handleImage(message: ImageMessage): Promise<void>
  async handleLocation(message: LocationMessage): Promise<void>
  async handleEvent(message: EventMessage): Promise<void>
}
```

**工作内容**:
- [ ] 实现文本消息接收和解析
- [ ] 实现语音消息接收
- [ ] 实现图片消息接收
- [ ] 实现位置信息接收
- [ ] 实现事件消息处理（订阅、取消订阅等）
- [ ] 实现消息加解密
- [ ] 实现消息去重（防止重复处理）

**消息解析示例**:
```xml
<!-- 接收到的XML消息 -->
<xml>
  <ToUserName><![CDATA[corp_id]]></ToUserName>
  <FromUserName><![CDATA[user_id]]></FromUserName>
  <CreateTime>123456789</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[/start 阳光小区]]></Content>
  <MsgId>1234567890123456</MsgId>
</xml>

<!-- 解析后 -->
{
  type: 'text',
  userId: 'user_id',
  content: '/start 阳光小区',
  timestamp: 123456789,
  msgId: '1234567890123456'
}
```

### 3. 媒体文件下载

**接口设计**:
```typescript
interface MediaDownloader {
  downloadVoice(mediaId: string): Promise<Buffer>
  downloadImage(mediaId: string): Promise<Buffer>
  downloadFile(mediaId: string): Promise<Buffer>
}
```

**工作内容**:
- [ ] 实现媒体文件下载
- [ ] 实现临时文件存储
- [ ] 实现文件格式转换（AMR转WAV）
- [ ] 实现文件上传WPS
- [ ] 实现定期清理临时文件

**注意事项**:
- 媒体文件临时链接有效期3天
- 需及时下载保存
- AMR格式语音需要转换才能识别

### 4. 消息发送

**接口设计**:
```typescript
interface WeComMessageSender {
  sendText(userId: string, content: string): Promise<void>
  sendMarkdown(userId: string, markdown: string): Promise<void>
  sendCard(userId: string, card: CardMessage): Promise<void>
  sendImage(userId: string, imageUrl: string): Promise<void>
}
```

**消息类型实现**:
- [ ] 文本消息
- [ ] Markdown消息
- [ ] 图文卡片（用于重要通知）
- [ ] 图片消息

**卡片消息示例**:
```json
{
  "msgtype": "template_card",
  "template_card": {
    "card_type": "text_notice",
    "source": {
      "desc": "企业微信"
    },
    "main_title": {
      "title": "应急事件通知",
      "desc": "阳光小区停电故障"
    },
    "jump_list": [
      {
        "type": 1,
        "url": "https://wps.cn/doc/xxx",
        "title": "查看应急指引"
      }
    ]
  }
}
```

### 5. 命令解析

**命令体系**:
```typescript
interface Command {
  name: string
  args: string[]
  raw: string
}

// 命令解析器
class CommandParser {
  parse(input: string): Command | null
}

// 支持的命令
const COMMANDS = {
  START: '/start',
  COLLECT: '/collect',
  GENERATE: '/generate',
  EMERGENCY: '/emergency',
  QUERY: '/query',
  HELP: '/help',
  STATUS: '/status',
  CANCEL: '/cancel'
}
```

**工作内容**:
- [ ] 实现命令解析器
- [ ] 实现自然语言意图识别（可选）
- [ ] 实现命令帮助信息

### 6. Session管理集成

**集成方案**:
```typescript
// Session初始化
async function initializeSession(userId: string): Promise<Session> {
  const session = await sessionManager.get(userId)
  if (!session || isExpired(session)) {
    return await createNewSession(userId)
  }
  return session
}

// 消息处理流程
async function handleMessage(message: Message) {
  const session = await initializeSession(message.userId)
  await sessionManager.updateActivity(message.userId)
  
  // 根据Session状态处理消息
  const skill = getSkillBySessionState(session.state)
  await skill.handle(message, session)
}
```

**工作内容**:
- [ ] 集成OpenClaw Session管理
- [ ] 实现用户身份识别
- [ ] 实现供电所自动关联
- [ ] 实现Session过期提醒

### 7. 错误处理

**错误类型**:
```typescript
enum WeComErrorCode {
  INVALID_SIGNATURE = -40001,  // 签名验证错误
  INVALID_XML = -40002,        // XML解析错误
  INVALID_CORP_ID = -40003,    // CorpID验证错误
  INVALID_AES_KEY = -40004,    // AES密钥解密错误
  INVALID_MSG = -40005,        // 消息解密错误
  INVALID_BUFFER = -40006,     // Buffer错误
  INVALID_ENCODE = -40007,     // 加密错误
  INVALID_DECODE = -40008,     // 解密错误
  INVALID_MEDIA_ID = -40009,   // 媒体文件ID错误
}
```

**工作内容**:
- [ ] 实现错误分类处理
- [ ] 实现错误日志记录
- [ ] 实现友好错误提示

## 测试要求

### 单元测试
- [ ] 消息解析测试
- [ ] 加解密测试
- [ ] 命令解析测试
- [ ] 媒体下载测试

### 集成测试
- [ ] 完整消息收发测试
- [ ] 多轮对话测试
- [ ] Session管理测试
- [ ] 并发消息测试

### 联调测试
- [ ] 与企业微信服务器联调
- [ ] 回调URL可达性测试
- [ ] 消息加解密联调

## 交付物

1. **配置文件**: `config/channels/wecom.yaml`
2. **Provider实现**: `src/channels/wecom/`
3. **消息处理器**: `src/channels/wecom/handlers/`
4. **类型定义**: `src/channels/wecom/types.ts`
5. **测试用例**: `tests/channels/wecom/`
6. **部署文档**: `docs/deployment/wecom-setup.md`

## 验收标准

- [ ] 可正常接收和解析所有类型消息
- [ ] 可正常发送各类消息
- [ ] 媒体文件下载和存储正常
- [ ] 命令解析准确
- [ ] Session管理集成正常
- [ ] 错误处理完善
- [ ] 与OpenClaw框架集成通过

## 注意事项

1. **回调URL必须公网可访问**，开发期可用ngrok
2. **消息加解密必须正确实现**，否则无法接收消息
3. **媒体文件需及时下载**，链接3天后失效
4. **需处理消息去重**，企业微信可能重复推送
5. **需设置合理的超时时间**，避免长时间等待

## 相关文档

- [详细设计方案 - 企业微信集成](../design/detailed-design-v2.md#企业微信集成方案)
- [技术可行性分析 - 企业微信能力边界](../analysis/technical-feasibility-analysis.md#企业微信能力边界深度分析)
- 企业微信开发者文档：https://developer.work.weixin.qq.com/document

---

**创建时间**: 2026-03-17  
**负责团队**: Field Integration Team  
**依赖**: TASK-001 ✅ 已完成
