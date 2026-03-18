---
name: emergency-guide
description: 应急处理引导技能，快速记录应急信息、GPS位置标注、一键上报
metadata:
  {
    "openclaw":
      {
        "emoji": "🚨",
        "requires": { "env": ["KIMI_API_KEY"], "config": ["channels.wecom.enabled"] }
      }
  }
---

# Emergency Guide - 应急处理引导技能

## 概述

本技能负责应急情况下的快速信息记录和上报，提供快速通道和自动通知机制。

**核心能力**：
- 快速信息记录（一键启动）
- GPS 位置自动标注
- 应急照片拍摄引导
- 自动通知相关方
- 应急知识库查询

## 触发条件

### 关键词触发

**触发词**: 应急、紧急、抢修、故障、危险、停电、火灾、漏电

**示例**:
- "发现紧急情况"
- "这里有危险"
- "需要抢修"
- "发生停电事故"

## 工作流程

```
用户提及应急关键词
   ↓
[快速通道启动]
   ↓
询问应急类型
   ├── 设备故障
   ├── 停电事故
   ├── 安全隐患
   └── 其他紧急情况
   ↓
快速信息采集
   ├── 位置信息（自动获取/手动输入）
   ├── 现场照片
   ├── 简要描述
   └── 联系方式
   ↓
自动上报
   ├── 通知供电所值班人员
   ├── 生成应急记录
   └── 返回确认信息
```

## 实现逻辑

### 1. 应急检测与响应

```typescript
async function detectEmergency(message: string, context: Context): Promise<boolean> {
  const emergencyKeywords = [
    '应急', '紧急', '抢修', '故障', '危险', 
    '停电', '火灾', '漏电', '触电', '爆炸'
  ];
  
  const hasEmergency = emergencyKeywords.some(
    keyword => message.includes(keyword)
  );
  
  if (hasEmergency) {
    // 立即启动快速通道
    await activateFastTrack(context);
    return true;
  }
  
  return false;
}

async function activateFastTrack(context: Context): Promise<void> {
  // 设置会话状态为应急模式
  await context.setSessionState({
    mode: 'emergency',
    startTime: new Date(),
    data: {}
  });
  
  // 发送快速响应
  await context.send(`🚨 **应急通道已启动**

请选择应急类型：
1️⃣ 设备故障
2️⃣ 停电事故
3️⃣ 安全隐患
4️⃣ 其他紧急情况

直接回复数字或描述情况`);
}
```

### 2. 位置信息获取

```typescript
async function handleLocation(context: Context): Promise<LocationInfo> {
  // 尝试从企业微信位置消息获取
  if (context.message.type === 'location') {
    return {
      latitude: context.message.latitude,
      longitude: context.message.longitude,
      address: context.message.label,
      source: 'wechat'
    };
  }
  
  // 提示用户提供位置
  await context.send(`📍 请提供位置信息：
  
方式一：发送位置消息（推荐）
方式二：描述具体地址（如：阳光社区东门配电房）`);
  
  return null;
}

async function saveEmergencyPoint(
  sessionId: string,
  location: LocationInfo,
  context: Context
): Promise<void> {
  await context.tools['postgres-query'].execute({
    query: `
      INSERT INTO emergency_points (
        session_id, latitude, longitude, address, 
        reported_at, status
      ) VALUES ($1, $2, $3, $4, $5, $6)
    `,
    params: [
      sessionId,
      location.latitude,
      location.longitude,
      location.address,
      new Date(),
      'pending'
    ]
  });
}
```

### 3. 应急照片采集

```typescript
async function guideEmergencyPhotos(context: Context): Promise<void> {
  await context.send(`📸 **应急照片采集**

请拍摄以下内容（按优先级）：
1. 现场整体情况
2. 故障设备/隐患点特写
3. 周围环境

💡 提示：
• 确保安全前提下拍摄
• 可发送多张照片
• 回复"完成"结束采集`);
}

async function saveEmergencyPhotos(
  sessionId: string,
  photos: PhotoItem[],
  context: Context
): Promise<void> {
  for (const photo of photos) {
    // 上传到 MinIO
    const url = await context.tools['minio-storage'].upload({
      bucket: 'field-photos',
      path: `emergency/${sessionId}/${photo.filename}`,
      file: photo.content
    });
    
    // 记录到数据库
    await context.tools['postgres-query'].execute({
      query: `
        INSERT INTO photos (
          session_id, photo_type, photo_url, 
          latitude, longitude, taken_at
        ) VALUES ($1, $2, $3, $4, $5, $6)
      `,
      params: [
        sessionId,
        'emergency',
        url,
        photo.latitude,
        photo.longitude,
        new Date()
      ]
    });
  }
}
```

### 4. 自动通知

```typescript
async function notifyEmergency(
  sessionId: string,
  emergencyData: EmergencyData,
  context: Context
): Promise<void> {
  // 查询值班人员
  const dutyStaff = await context.tools['postgres-query'].execute({
    query: `
      SELECT user_id, phone, name 
      FROM users 
      WHERE station_id = $1 
        AND role = 'duty' 
        AND is_active = true
    `,
    params: [emergencyData.stationId]
  });
  
  // 构建通知消息
  const notification = `🚨 **应急情况上报**

📍 位置: ${emergencyData.address || '待确认'}
⏰ 时间: ${new Date().toLocaleString()}
📝 类型: ${emergencyData.type}
👤 上报人: ${emergencyData.reporterName}

📋 简要描述:
${emergencyData.description}

📷 照片: ${emergencyData.photos.length} 张

请尽快处理！`;
  
  // 发送通知（通过企业微信）
  for (const staff of dutyStaff) {
    await context.tools['wecom'].sendMessage({
      userId: staff.user_id,
      message: notification
    });
  }
  
  // 记录通知日志
  await context.tools['postgres-query'].execute({
    query: `
      INSERT INTO emergency_notifications (
        session_id, notified_users, notified_at, status
      ) VALUES ($1, $2, $3, $4)
    `,
    params: [
      sessionId,
      JSON.stringify(dutyStaff.map(s => s.user_id)),
      new Date(),
      'sent'
    ]
  });
}
```

## 应急知识库

### 常见应急处理指南

```typescript
const emergencyGuides = {
  power_outage: {
    title: '停电事故处理',
    steps: [
      '确认停电范围（单户/多户/整个区域）',
      '检查配电房设备状态',
      '联系调度中心确认供电情况',
      '安抚受影响用户',
      '记录事故信息'
    ],
    contacts: ['调度中心', '供电所值班室']
  },
  
  equipment_fault: {
    title: '设备故障处理',
    steps: [
      '确认故障设备类型和位置',
      '判断故障严重程度',
      '设置安全警示',
      '联系抢修班组',
      '记录故障信息'
    ],
    contacts: ['抢修班组', '设备运维']
  },
  
  safety_hazard: {
    title: '安全隐患处理',
    steps: [
      '评估隐患风险等级',
      '设置警示标志',
      '隔离危险区域',
      '通知相关部门',
      '跟踪整改进度'
    ],
    contacts: ['安全员', '供电所所长']
  }
};

async function getEmergencyGuide(
  type: string,
  context: Context
): Promise<string> {
  const guide = emergencyGuides[type];
  if (!guide) return null;
  
  return `📋 **${guide.title}**

处理步骤：
${guide.steps.map((step, i) => `${i + 1}. ${step}`).join('\n')}

联系人：
${guide.contacts.map(c => `• ${c}`).join('\n')}`;
}
```

## 用户交互示例

### 示例1：快速上报流程

```
[10:30] User: 阳光社区配电房有异响，可能是紧急情况
[10:30] Agent: 🚨 应急通道已启动

请选择应急类型：
1️⃣ 设备故障
2️⃣ 停电事故
3️⃣ 安全隐患
4️⃣ 其他紧急情况

[10:31] User: 1
[10:31] Agent: 📍 请提供位置信息：
         方式一：发送位置消息（推荐）
         方式二：描述具体地址

[10:32] User: [发送位置]
[10:32] Agent: 📍 位置已记录：阳光社区配电房
         
         📸 请拍摄现场照片
         回复"完成"结束采集

[10:35] User: [发送照片1]
[10:35] User: [发送照片2]
[10:36] User: 完成
[10:36] Agent: ✅ 应急信息已记录

         📋 应急记录编号：EM-20260318001
         📍 位置：阳光社区配电房
         ⏰ 上报时间：10:30
         📷 照片：2张
         
         📢 已自动通知：
         • 供电所值班室（张三）
         • 抢修班组（李四）
         
         请保持电话畅通，等待进一步指示。
```

### 示例2：查询应急知识

```
[14:00] User: 停电事故怎么处理？
[14:00] Agent: 📋 停电事故处理指南

         处理步骤：
         1. 确认停电范围（单户/多户/整个区域）
         2. 检查配电房设备状态
         3. 联系调度中心确认供电情况
         4. 安抚受影响用户
         5. 记录事故信息
         
         联系人：
         • 调度中心
         • 供电所值班室
         
         如需上报，请回复"应急上报"
```

## 数据存储

### 应急记录表

```sql
CREATE TABLE emergency_records (
  record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  
  -- 应急信息
  emergency_type VARCHAR(50) NOT NULL,  -- power_outage | equipment_fault | safety_hazard | other
  severity VARCHAR(20),                  -- critical | high | medium | low
  
  -- 位置信息
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  address VARCHAR(255),
  
  -- 描述
  description TEXT,
  
  -- 状态
  status VARCHAR(20) DEFAULT 'pending',  -- pending | processing | resolved
  
  -- 时间
  reported_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP,
  
  -- 关联
  station_id UUID,
  reporter_id VARCHAR(100),
  
  FOREIGN KEY (session_id) REFERENCES field_sessions(session_id)
);
```

### 应急通知表

```sql
CREATE TABLE emergency_notifications (
  notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  record_id UUID NOT NULL,
  
  -- 通知信息
  notified_users JSONB,        -- 被通知的用户列表
  notification_method VARCHAR(50),  -- wecom | sms | phone
  
  -- 状态
  status VARCHAR(20) DEFAULT 'pending',
  
  -- 时间
  notified_at TIMESTAMP DEFAULT NOW(),
  acknowledged_at TIMESTAMP,
  
  FOREIGN KEY (record_id) REFERENCES emergency_records(record_id)
);
```

## 配置说明

### 在 openclaw.config.yaml 中配置

```yaml
skills:
  emergency_guide:
    enabled: true
    priority: high  # 最高优先级
    triggers:
      - type: intent
        patterns:
          - "应急"
          - "紧急"
          - "抢修"
          - "故障"
          - "危险"
    config:
      fast_track: true       # 快速通道
      auto_notify: true      # 自动通知
      notify_delay: 0        # 通知延迟（秒）
```

## 安全注意事项

1. **优先确保人员安全**
   - 提醒用户在安全前提下操作
   - 危险情况优先撤离

2. **信息完整性**
   - 位置信息必须准确
   - 照片要清晰反映情况
   - 联系方式要确认

3. **通知及时性**
   - 应急信息立即上报
   - 超时未响应自动升级

---

**版本**: 2.0.0  
**作者**: PM Agent  
**更新日期**: 2026-03-18  
**变更**: 修正为 OpenClaw 标准 SKILL.md 格式
