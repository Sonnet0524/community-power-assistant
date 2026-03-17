# Task-007: EmergencyGuide Skill开发

## 任务概述

**任务ID**: TASK-007  
**任务名称**: EmergencyGuide Skill开发  
**优先级**: 🟡 高  
**预计工期**: 3-4天  
**依赖**: TASK-002, TASK-003

## 任务目标

开发应急处置指引Skill，在应急情况下快速响应：
1. 应急事件启动和确认
2. 敏感客户自动查询和关怀
3. 应急方案推送
4. 处理过程记录和报告生成

## 详细工作内容

### 1. Skill框架搭建

**Skill定义**:
```typescript
// src/skills/emergency-guide/index.ts
export class EmergencyGuideSkill implements Skill {
  id = 'emergency_guide'
  name = '应急处置指引'
  version = '1.0.0'
  
  triggers = [
    { type: 'command', pattern: '/emergency' },
    { type: 'keyword', keywords: ['停电', '故障', '抢修', '应急'] },
    { type: 'intent', intent: 'emergency_response' }
  ]
  
  async handle(message: Message, session: Session): Promise<void>
}

// 应急类型定义
enum EmergencyType {
  POWER_OUTAGE = 'power_outage',       // 停电故障
  EQUIPMENT_FAILURE = 'equipment_failure', // 设备故障
  CUSTOMER_COMPLAINT = 'customer_complaint' // 紧急投诉
}

interface EmergencySession extends Session {
  emergencyType: EmergencyType
  communityId: string
  affectedScope: string
  startTime: Date
  progress: EmergencyProgress[]
}
```

### 2. 应急事件启动

**启动流程**:
```
用户: /emergency 停电 阳光小区
    ↓
Agent:
  1. 解析应急类型（停电）
  2. 解析地点（阳光小区）
  3. 查询小区信息
  4. 查询应急资料
  5. 创建应急Session
  6. 发送启动消息
    ↓
等待确认影响范围
```

**实现代码**:
```typescript
async function handleEmergencyCommand(message: Message, session: Session) {
  const parsed = parseEmergencyCommand(message.content)
  const { emergencyType, communityName } = parsed
  
  // 查询小区信息
  const community = await wpsApi.queryRecords('community_info', {
    community_name: communityName,
    station_id: session.stationId
  })
  
  if (!community) {
    await sendMessage(message.userId, 
      `⚠️ 未找到小区"${communityName}"，请检查名称。\n可用格式：/emergency 类型 小区名`
    )
    return
  }
  
  // 查询应急资料
  const [emergencyInfo, sensitiveCustomers] = await Promise.all([
    wpsApi.queryRecords('emergency_access_info', {
      community_id: community.community_id
    }),
    wpsApi.queryRecords('customer_info', {
      community_id: community.community_id,
      is_sensitive: true
    })
  ])
  
  // 创建应急Session
  const emergencySession: EmergencySession = {
    ...session,
    state: 'emergency',
    emergencyType,
    communityId: community.community_id,
    communityName: community.community_name,
    startTime: new Date(),
    progress: [],
    collectedData: {
      emergencyInfo: emergencyInfo[0],
      sensitiveCustomers,
      affectedCustomers: []
    }
  }
  
  await sessionManager.save(emergencySession)
  
  // 发送应急启动消息
  await sendEmergencyStartMessage(message.userId, emergencySession)
}

function parseEmergencyCommand(content: string): { 
  emergencyType: EmergencyType
  communityName: string 
} {
  const parts = content.split(' ')
  const typeMap: Record<string, EmergencyType> = {
    '停电': EmergencyType.POWER_OUTAGE,
    '故障': EmergencyType.EQUIPMENT_FAILURE,
    '投诉': EmergencyType.CUSTOMER_COMPLAINT,
    'outage': EmergencyType.POWER_OUTAGE,
    'failure': EmergencyType.EQUIPMENT_FAILURE
  }
  
  const emergencyType = typeMap[parts[1]] || EmergencyType.POWER_OUTAGE
  const communityName = parts.slice(2).join(' ')
  
  return { emergencyType, communityName }
}
```

**启动消息模板**:
```
🚨 应急事件启动 - {community_name}
类型：{emergency_type}
时间：{start_time}
───────────────────
正在查询应急资料...
✅ 已获取应急发电指引
✅ 已获取敏感客户清单（{sensitive_count}户）
✅ 已获取物业联系信息

请确认停电影响范围：
[整小区] [部分楼栋] [单栋楼] [不确定]
```

### 3. 影响范围确认和敏感客户关怀

**处理流程**:
```
用户选择影响范围
    ↓
Agent:
  1. 计算影响户数
  2. 查询受影响敏感客户
  3. 生成关怀清单
  4. 发送敏感客户提醒
    ↓
提供一键拨打功能
```

**实现代码**:
```typescript
async function handleScopeConfirmation(
  message: Message, 
  session: EmergencySession
) {
  const scope = parseScopeOption(message.content)
  session.collectedData.affectedScope = scope
  
  // 计算影响户数（简化逻辑，实际需要查询楼栋户数）
  const affectedCount = await calculateAffectedHouseholds(
    session.communityId, 
    scope
  )
  
  // 查询受影响敏感客户
  const affectedSensitiveCustomers = await findAffectedSensitiveCustomers(
    session.collectedData.sensitiveCustomers,
    scope
  )
  
  session.collectedData.affectedCustomers = affectedSensitiveCustomers
  
  // 发送影响分析
  await sendImpactAnalysis(message.userId, {
    scope,
    affectedCount,
    sensitiveCustomers: affectedSensitiveCustomers
  })
  
  // 如果存在敏感客户，发送紧急提醒
  if (affectedSensitiveCustomers.length > 0) {
    await sendSensitiveCustomerAlert(
      message.userId, 
      affectedSensitiveCustomers
    )
  }
  
  await sessionManager.save(session)
}

async function sendSensitiveCustomerAlert(
  userId: string,
  customers: Customer[]
): Promise<void> {
  let message = '🔴 敏感客户关怀提醒\n\n'
  message += `发现 ${customers.length} 户敏感客户受影响，请立即联系！\n\n`
  
  customers.forEach((customer, index) => {
    message += `${index + 1}. ${customer.address}\n`
    message += `   类型：${customer.sensitive_type}\n`
    message += `   电话：${maskPhone(customer.contact_phone)}\n`
    message += `   [一键拨打]\n\n`
  })
  
  message += '⚠️ 建议优先关怀，确认是否需要紧急协助'
  
  await wecomApi.sendMarkdownMessage(userId, message)
}

// 手机号脱敏
function maskPhone(phone: string): string {
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}
```

### 4. 应急方案推送

**方案推送流程**:
```
Agent发送应急处理步骤
    ↓
提供文档链接
    ↓
提供导航链接
    ↓
询问是否需要记录处理过程
```

**实现代码**:
```typescript
async function sendEmergencyGuide(
  userId: string,
  session: EmergencySession
): Promise<void> {
  const { emergencyInfo, community } = session.collectedData
  
  let message = '📋 应急处理指引\n\n'
  
  // 步骤1：联系物业
  message += '第1步：联系物业确认情况\n'
  message += `• 联系人：${community.property_contact}\n`
  message += `• 电话：${community.property_phone}\n`
  message += `• [一键拨打]\n\n`
  
  // 步骤2：安抚敏感客户（如果存在）
  if (session.collectedData.affectedCustomers?.length > 0) {
    message += '第2步：安抚敏感客户\n'
    session.collectedData.affectedCustomers.forEach(c => {
      message += `• ${c.address} ${c.sensitive_type} [拨打]\n`
    })
    message += '\n'
  }
  
  // 步骤3：准备应急发电车
  if (emergencyInfo) {
    message += '第3步：准备应急发电车\n'
    message += `• 进入点：${emergencyInfo.entry_point_description}\n`
    message += `• 停放点：${emergencyInfo.parking_point_description}\n`
    message += `• 接入点：${emergencyInfo.access_point_description}\n`
    message += `• 电缆：${emergencyInfo.cable_model} ${emergencyInfo.cable_length}米\n`
    message += `• [查看详细指引] [导航到接入点]\n\n`
  }
  
  // 步骤4：记录处理过程
  message += '第4步：记录处理过程\n'
  message += '请每30分钟更新一次进展\n\n'
  
  message += '[开始记录] [设置提醒]'
  
  await wecomApi.sendMarkdownMessage(userId, message)
}
```

**应急指引卡片**:
```typescript
async function sendEmergencyCard(
  userId: string,
  session: EmergencySession
): Promise<void> {
  await wecomApi.sendCardMessage(userId, {
    title: '应急事件：阳光小区停电',
    description: `影响范围：${session.collectedData.affectedScope}\n` +
                 `敏感客户：${session.collectedData.affectedCustomers?.length || 0}户`,
    url: session.collectedData.emergencyDocUrl || '',
    buttons: [
      {
        text: '查看应急指引',
        url: session.collectedData.emergencyDocUrl
      },
      {
        text: '导航到接入点',
        type: 'navigation',
        url: generateNavigationUrl(session.collectedData.emergencyInfo)
      },
      {
        text: '确认收到',
        type: 'callback',
        callback: 'acknowledge_emergency'
      }
    ]
  })
}
```

### 5. 处理过程记录

**记录流程**:
```
Agent: "请更新处理进展"
    ↓
用户: "已联系物业，确认变压器故障"
    ↓
Agent:
  1. 记录时间戳
  2. 记录内容
  3. 询问是否需要拍照
    ↓
用户: [照片]
    ↓
Agent: "已保存照片，预计恢复时间？"
    ↓
用户: "预计2小时内恢复"
    ↓
Agent: "已记录，将在30分钟后提醒更新"
```

**实现代码**:
```typescript
class EmergencyProgressTracker {
  async recordProgress(
    session: EmergencySession,
    content: string,
    photos?: string[]
  ): Promise<void> {
    const progress: EmergencyProgress = {
      timestamp: new Date(),
      content,
      photos: photos || [],
      recordedBy: session.userId
    }
    
    session.progress.push(progress)
    await sessionManager.save(session)
    
    // 发送确认
    await sendProgressConfirmation(session.userId, progress)
    
    // 设置下次提醒
    await scheduleNextReminder(session)
  }
  
  async scheduleNextReminder(session: EmergencySession): Promise<void> {
    // 30分钟后发送提醒
    const reminderTime = new Date(Date.now() + 30 * 60 * 1000)
    
    await scheduler.schedule(reminderTime, async () => {
      await wecomApi.sendTextMessage(
        session.userId,
        '⏰ 应急处理进展更新提醒\n\n请更新当前处理进展。\n[更新进展] [事件已解决]'
      )
    })
  }
}
```

### 6. 应急报告生成

**报告生成流程**:
```
用户: "/emergency-complete" 或点击"事件已解决"
    ↓
Agent:
  1. 计算处理时长
  2. 汇总所有记录
  3. 生成应急处理报告
  4. 发送给相关人员
```

**报告内容**:
```typescript
async function generateEmergencyReport(
  session: EmergencySession
): Promise<void> {
  const duration = Date.now() - session.startTime.getTime()
  const durationText = formatDuration(duration)
  
  const report = {
    title: `${session.communityName} 应急处理报告`,
    event_type: session.emergencyType,
    start_time: session.startTime,
    end_time: new Date(),
    duration: durationText,
    affected_scope: session.collectedData.affectedScope,
    affected_customers: session.collectedData.affectedCustomers?.length || 0,
    progress_timeline: session.progress,
    photos: session.progress.flatMap(p => p.photos)
  }
  
  // 生成文档
  const docUrl = await docGenerationSkill.generateEmergencyReport(report)
  
  // 发送通知
  await sendEmergencyCompleteNotification(session, docUrl)
}

async function sendEmergencyCompleteNotification(
  session: EmergencySession,
  docUrl: string
): Promise<void> {
  const message = `✅ 应急事件处理完成

📍 地点：${session.communityName}
⏱️ 处理时长：${formatDuration(Date.now() - session.startTime.getTime())}
👥 影响客户：${session.collectedData.affectedCustomers?.length || 0}户

📄 应急处理报告已生成：
${docUrl}

相关人员已收到通知。`

  // 发送给现场人员
  await wecomApi.sendMarkdownMessage(session.userId, message)
  
  // 发送给所长
  await notifySupervisor(session, docUrl)
  
  // 发送到工作群
  await notifyWorkGroup(session, docUrl)
}
```

## 通知机制

### 实时通知

| 触发条件 | 接收人 | 通知内容 | 优先级 |
|---------|--------|---------|--------|
| 应急事件启动 | 现场人员、所长 | 事件类型、地点、影响范围 | 🔴 紧急 |
| 敏感客户发现 | 现场人员、所长 | 敏感客户清单、联系方式 | 🔴 紧急 |
| 进展更新 | 所长 | 处理进展、预计恢复时间 | 🟡 高 |
| 事件解决 | 现场人员、所长、客服 | 处理报告、耗时统计 | 🟢 普通 |

### 通知实现

```typescript
class EmergencyNotificationService {
  async notifyEmergencyStart(session: EmergencySession): Promise<void> {
    // 通知现场人员（已在处理）
    // 通知所长
    await this.notifySupervisor(session, 'emergency_start')
  }
  
  async notifyProgressUpdate(session: EmergencySession): Promise<void> {
    await this.notifySupervisor(session, 'progress_update')
  }
  
  async notifyEmergencyComplete(session: EmergencySession): Promise<void> {
    await this.notifySupervisor(session, 'emergency_complete')
    await this.notifyCustomerService(session)
    await this.notifyWorkGroup(session)
  }
  
  private async notifySupervisor(
    session: EmergencySession, 
    type: string
  ): Promise<void> {
    const supervisorId = await this.getSupervisorId(session.stationId)
    
    const messages = {
      emergency_start: `🚨 应急事件：${session.communityName}发生${session.emergencyType}`,
      progress_update: `📊 ${session.communityName}应急处理进展更新`,
      emergency_complete: `✅ ${session.communityName}应急事件已处理完成`
    }
    
    await wecomApi.sendTextMessage(supervisorId, messages[type])
  }
}
```

## 测试要求

### 单元测试
- [ ] 应急命令解析测试
- [ ] 影响范围计算测试
- [ ] 敏感客户查询测试
- [ ] 进展记录测试

### 集成测试
- [ ] 完整应急流程测试
- [ ] 敏感客户通知测试
- [ ] 报告生成测试
- [ ] 多人员协同测试

### 压力测试
- [ ] 并发应急事件处理
- [ ] 大量敏感客户查询性能

## 交付物

1. **Skill主代码**: `src/skills/emergency-guide/index.ts`
2. **应急处理器**: `src/skills/emergency-guide/handlers.ts`
3. **进展追踪器**: `src/skills/emergency-guide/progress-tracker.ts`
4. **通知服务**: `src/skills/emergency-guide/notification-service.ts`
5. **测试用例**: `tests/skills/emergency-guide/`

## 验收标准

- [ ] 应急事件可正常启动
- [ ] 敏感客户自动查询准确
- [ ] 应急方案推送完整
- [ ] 进展记录功能正常
- [ ] 报告生成正确
- [ ] 通知机制可靠

## 注意事项

1. **应急事件响应时间必须快**（< 3秒）
2. **敏感客户信息要脱敏展示**
3. **所有操作要有时间戳记录**
4. **支持多人同时处理同一事件**
5. **要有强制结束机制**（防止Session一直挂着）

## 相关文档

- [详细设计方案 - EmergencyGuide](../design/detailed-design-v2.md#skill-3-应急处置emergencyguide)
- PRD应急功能需求

---

**创建时间**: 2026-03-17  
**负责人**: 待分配  
**状态**: 待开始  
**依赖**: TASK-002完成，TASK-003完成
