# 企业微信长连接技术规范

> 基于企业微信官方文档，适配OpenClaw框架的长连接接入规范

---

## 一、技术架构对比

### 长连接 vs 回调模式

| 特性 | WebSocket长连接 | Webhook回调模式 |
|------|----------------|----------------|
| **连接方式** | 客户端主动建立WebSocket | 服务端被动接收HTTP POST |
| **协议** | `wss://` | `https://` |
| **延迟** | 低（复用连接） | 较高（每次新建连接） |
| **服务端要求** | **无需公网IP**，内网可部署 | **必须公网IP+域名+SSL** |
| **消息解密** | **无需解密**（底层加密） | 需要AES解密 |
| **实时性** | 支持流式输出（打字机效果） | 不支持 |
| **适用场景** | 高实时性、内网部署 | 简单场景、快速接入 |

### 推荐使用长连接的场景

✅ **Field Info Agent完全符合长连接的推荐场景：**
- ✅ 部署在内网（安全考虑）
- ✅ 需要实时交互（AI分析结果即时返回）
- ✅ 需要流式输出（KIMI大模型的打字机效果）
- ✅ 不想维护公网服务器和SSL证书

---

## 二、连接建立流程

### 2.1 整体流程

```
┌─────────────────┐      ┌───────────────────────────────────┐
│  OpenClaw Agent │      │        企业微信服务器              │
│   (内网部署)     │      │                                   │
└────────┬────────┘      └───────────────────┬───────────────┘
         │                                    │
         │ 1. 建立WebSocket连接                │
         │    wss://openws.work.weixin.qq.com │
         ═════════════════════════════════════▶
         │                                    │
         │◄════════════════════════════════════
         │    2. WebSocket握手成功              │
         │                                    │
         │ 3. 发送订阅请求 (aibot_subscribe)   │
         │    {                               │
         │      "cmd": "aibot_subscribe",     │
         │      "body": {                     │
         │        "bot_id": "xxx",            │
         │        "secret": "xxx"             │
         │      }                             │
         │    }                               │
         ═════════════════════════════════════▶
         │                                    │
         │◄════════════════════════════════════
         │    4. 返回订阅结果                   │
         │    { "type": "subscribe_success" } │
         │                                    │
         ═════════════════════════════════════
         │    5. 保持连接，双向通信              │
         │    • 接收用户消息（企业微信→Agent）   │
         │    • 发送回复（Agent→企业微信）       │
         │    • 心跳保活（30秒间隔）            │
         ═════════════════════════════════════
```

### 2.2 详细步骤

#### Step 1: 建立WebSocket连接

```javascript
const ws = new WebSocket('wss://openws.work.weixin.qq.com');

ws.on('open', () => {
  console.log('WebSocket连接已建立');
  // 进入Step 2: 发送订阅请求
});
```

#### Step 2: 发送订阅请求（身份验证）

```json
{
  "cmd": "aibot_subscribe",
  "headers": {
    "req_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "body": {
    "bot_id": "YOUR_BOT_ID",
    "secret": "YOUR_SECRET"
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| cmd | string | 是 | 固定值 `aibot_subscribe` |
| headers.req_id | string | 是 | 请求唯一标识UUID |
| body.bot_id | string | 是 | 智能机器人BotID |
| body.secret | string | 是 | 长连接专用Secret |

#### Step 3: 接收订阅响应

```json
// 成功
{
  "type": "subscribe_success",
  "headers": {
    "req_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "body": {}
}

// 失败
{
  "type": "subscribe_fail",
  "headers": {
    "req_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "body": {
    "err_code": 40001,
    "err_msg": "invalid bot_id or secret"
  }
}
```

---

## 三、消息交互协议

### 3.1 接收用户消息

当用户向机器人发送消息时，企业微信通过WebSocket推送消息回调：

```json
{
  "type": "aibot_msg_callback",
  "headers": {
    "req_id": "msg_123456789"
  },
  "body": {
    "msg_id": "MSG_ID",
    "conversation_id": "CONV_ID",
    "chat_type": "single",
    "from_user": {
      "userid": "USER_ID",
      "name": "张三"
    },
    "msg_type": "text",
    "content": "我今天要去阳光社区驻点",
    "create_time": 1710828000
  }
}
```

**消息类型：**

| msg_type | 说明 | content格式 |
|----------|------|-------------|
| text | 文字消息 | 纯文本字符串 |
| image | 图片消息 | JSON对象，包含pic_url |
| location | 位置消息 | JSON对象，包含latitude/longitude |

### 3.2 回复消息（同步回复）

```json
{
  "cmd": "aibot_respond_msg",
  "headers": {
    "req_id": "resp_123456789"
  },
  "body": {
    "msg_id": "MSG_ID",              // 对应用户消息的msg_id
    "content": "📋 已为您准备阳光社区驻点工作...",
    "msg_type": "markdown",
    "finish": true                    // true表示完整消息，false表示流式片段
  }
}
```

### 3.3 流式消息回复（打字机效果）⭐

长连接模式支持流式输出，完美契合大模型的打字机效果：

```javascript
// 第1段
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msg_id": "MSG_ID",
    "content": "🔍 正在分析照片",
    "finish": false    // 还有更多内容
  }
}

// 第2段（1秒后）
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msg_id": "MSG_ID",
    "content": "🔍 正在分析照片...\n\n📷 设备识别：箱式变压器",
    "finish": false
  }
}

// 第3段（再1秒后）
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msg_id": "MSG_ID",
    "content": "🔍 正在分析照片...\n\n📷 设备识别：箱式变压器\n📊 状态评估：正常",
    "finish": false
  }
}

// 最后一段
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msg_id": "MSG_ID",
    "content": "🔍 分析完成\n\n📷 设备：箱式变压器（SCB11-500kVA）\n📊 状态：🟢 正常\n✅ 置信度：95%\n\n💡 建议：继续检查低压侧接线",
    "finish": true     // 流式结束
  }
}
```

### 3.4 主动推送消息

开发者可在没有用户消息触发的情况下，主动向用户推送消息：

```json
{
  "cmd": "aibot_send_msg",
  "headers": {
    "req_id": "push_123456789"
  },
  "body": {
    "conversation_id": "CONV_ID",
    "content": "⏰ 您的驻点工作已进行2小时，请及时保存进度",
    "msg_type": "text"
  }
}
```

**适用场景：**
- 定时提醒（如驻点超时提醒）
- 异步任务完成通知（如文档生成完成）
- 系统告警推送

---

## 四、心跳保活机制

### 4.1 心跳协议

```json
// 客户端发送（每30秒）
{
  "cmd": "ping"
}

// 服务端响应
{
  "type": "pong"
}
```

### 4.2 心跳配置

```yaml
# openclaw.config.yaml
channels:
  wecom:
    heartbeat:
      enabled: true
      interval: 30          # 心跳间隔(秒)
      timeout: 10           # 心跳响应超时(秒)
      max_retries: 3        # 最大重试次数
```

### 4.3 心跳失败处理

1. **第1次失败**：立即重试
2. **第2次失败**：延迟1秒后重试
3. **第3次失败**：触发重连机制

---

## 五、连接管理

### 5.1 连接数量限制

⚠️ **重要**：每个智能机器人**同一时间只能保持1个有效的长连接**

```
场景1：新连接踢掉旧连接
┌─────────┐         ┌─────────┐         ┌─────────┐
│ 连接A   │ ──────▶ │ 连接B   │ ──────▶ │ 连接A   │
│ (活跃)  │  新连接  │ (新)    │  断开   │ (被踢)  │
└─────────┘         └─────────┘         └─────────┘

场景2：高可用主备切换
┌─────────┐                    ┌─────────┐
│ 主连接A │  ──────故障──────▶ │ 备连接B │
│ (活跃)  │     自动切换        │ (接管)  │
└─────────┘                    └─────────┘
```

### 5.2 重连机制

```yaml
# openclaw.config.yaml
channels:
  wecom:
    reconnection:
      enabled: true
      max_attempts: 10              # 最大重连次数
      base_delay: 1000              # 初始重连延迟(ms)
      max_delay: 30000              # 最大重连延迟(ms)
      exponential_backoff: true     # 指数退避
```

**重连延迟计算：**
- 第1次：1秒
- 第2次：2秒
- 第3次：4秒
- 第4次：8秒
- ...
- 最大：30秒

---

## 六、事件处理

### 6.1 连接断开事件

```json
{
  "type": "aibot_event_callback",
  "body": {
    "event_type": "connection_closed",
    "reason": "new_connection_established"
  }
}
```

### 6.2 用户进入会话事件

```json
{
  "type": "aibot_event_callback",
  "body": {
    "event_type": "enter_chat",
    "conversation_id": "CONV_ID",
    "from_user": {
      "userid": "USER_ID",
      "name": "张三"
    }
  }
}
```

**响应：欢迎语**

```json
{
  "cmd": "aibot_respond_welcome_msg",
  "body": {
    "conversation_id": "CONV_ID",
    "content": "👋 欢迎使用现场信息收集助手！\n\n发送小区名称开始驻点工作，如：\"我要去阳光社区\""
  }
}
```

---

## 七、完整代码示例

### 7.1 基础连接示例（Node.js）

```javascript
const WebSocket = require('ws');

class WeComWebSocketClient {
  constructor(botId, secret) {
    this.botId = botId;
    this.secret = secret;
    this.ws = null;
    this.heartbeatInterval = null;
    this.reconnectAttempts = 0;
  }

  // 建立连接
  connect() {
    this.ws = new WebSocket('wss://openws.work.weixin.qq.com');
    
    this.ws.on('open', () => {
      console.log('WebSocket连接已建立');
      this.subscribe();
    });
    
    this.ws.on('message', (data) => {
      this.handleMessage(JSON.parse(data));
    });
    
    this.ws.on('close', () => {
      console.log('连接断开，准备重连...');
      this.reconnect();
    });
    
    this.ws.on('error', (error) => {
      console.error('WebSocket错误:', error);
    });
  }

  // 订阅身份验证
  subscribe() {
    const subscribeMsg = {
      cmd: 'aibot_subscribe',
      headers: {
        req_id: this.generateUUID()
      },
      body: {
        bot_id: this.botId,
        secret: this.secret
      }
    };
    
    this.ws.send(JSON.stringify(subscribeMsg));
  }

  // 处理消息
  handleMessage(message) {
    switch (message.type) {
      case 'subscribe_success':
        console.log('订阅成功，开始心跳保活');
        this.startHeartbeat();
        this.reconnectAttempts = 0;
        break;
        
      case 'aibot_msg_callback':
        // 处理用户消息
        this.handleUserMessage(message.body);
        break;
        
      case 'pong':
        // 心跳响应
        break;
        
      case 'aibot_event_callback':
        // 处理事件
        this.handleEvent(message.body);
        break;
    }
  }

  // 处理用户消息
  async handleUserMessage(msgBody) {
    const { msg_id, content, msg_type, from_user } = msgBody;
    
    // 调用OpenClaw处理逻辑
    const response = await openClaw.processMessage({
      userId: from_user.userid,
      content: content,
      msgType: msg_type
    });
    
    // 发送回复
    this.sendMessage(msg_id, response);
  }

  // 发送消息
  sendMessage(replyToMsgId, content, finish = true) {
    const msg = {
      cmd: 'aibot_respond_msg',
      headers: {
        req_id: this.generateUUID()
      },
      body: {
        msg_id: replyToMsgId,
        content: content,
        finish: finish
      }
    };
    
    this.ws.send(JSON.stringify(msg));
  }

  // 启动心跳
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.ws.send(JSON.stringify({ cmd: 'ping' }));
    }, 30000); // 30秒
  }

  // 重连
  reconnect() {
    if (this.reconnectAttempts >= 10) {
      console.error('重连次数超限，请检查网络或凭证');
      return;
    }
    
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    console.log(`${delay}ms后第${this.reconnectAttempts}次重连...`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
}

// 使用
const client = new WeComWebSocketClient('YOUR_BOT_ID', 'YOUR_SECRET');
client.connect();
```

---

## 八、OpenClaw集成要点

### 8.1 环境变量配置

```bash
# .env 文件
# 企业微信长连接配置
WECOM_CONNECTION_MODE=websocket
WECOM_BOT_ID=your_bot_id_here
WECOM_SECRET=your_secret_here

# 心跳配置（可选，使用默认值）
WECOM_HEARTBEAT_INTERVAL=30
WECOM_HEARTBEAT_TIMEOUT=10
WECOM_HEARTBEAT_MAX_RETRIES=3

# 重连配置（可选，使用默认值）
WECOM_RECONNECT_ENABLED=true
WECOM_RECONNECT_MAX_ATTEMPTS=10
WECOM_RECONNECT_BASE_DELAY=1000
```

### 8.2 关键配置检查清单

- [ ] 在企微管理后台开启「API模式」并选择「长连接」
- [ ] 获取BotID和Secret（与Webhook模式的Token不同）
- [ ] 确保服务器能访问 `wss://openws.work.weixin.qq.com`
- [ ] 配置防火墙允许WebSocket出站连接（端口443）
- [ ] 设置心跳间隔为30秒
- [ ] 配置重连机制（建议指数退避）

---

## 九、故障排查

### 9.1 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 40001 | BotID或Secret错误 | 检查凭证是否正确 |
| 40002 | 连接数超限 | 确保只有一个连接实例 |
| 40003 | 订阅请求格式错误 | 检查JSON格式 |
| 40004 | 心跳超时 | 检查网络连接，缩短心跳间隔 |

### 9.2 排查命令

```bash
# 测试WebSocket连接
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: openws.work.weixin.qq.com" \
  -H "Origin: https://your-domain.com" \
  https://openws.work.weixin.qq.com

# 检查网络连通性
ping openws.work.weixin.qq.com

# 检查端口
nc -zv openws.work.weixin.qq.com 443
```

---

**文档版本**: 1.0.0  
**基于**: 企业微信官方文档 2026-03-13  
**适配**: OpenClaw Framework  
**作者**: PM Agent
