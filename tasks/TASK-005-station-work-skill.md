# Task-005: StationWorkGuide Skill开发

## 任务概述

**任务ID**: TASK-005  
**任务名称**: StationWorkGuide Skill开发  
**优先级**: 🔴 最高  
**预计工期**: 5-7天  
**依赖**: TASK-002, TASK-003, TASK-004

## 任务目标

开发驻点工作引导Skill，实现完整的驻点工作流程：
1. 工作启动和准备
2. 配电房信息采集
3. 客户走访记录
4. 应急信息采集
5. 智能审核和数据保存

## 详细工作内容

### 1. Skill框架搭建

**Skill定义**:
```typescript
// src/skills/station-work-guide/index.ts
export class StationWorkGuideSkill implements Skill {
  id = 'station_work_guide'
  name = '驻点工作引导'
  version = '1.0.0'
  
  triggers = [
    { type: 'command', pattern: '/start' },
    { type: 'command', pattern: '/start-station-work' },
    { type: 'intent', intent: 'start_station_work' }
  ]
  
  async handle(message: Message, session: Session): Promise<void>
  async onEnter(session: Session): Promise<void>
  async onExit(session: Session): Promise<void>
}
```

**状态机实现**:
```typescript
// src/skills/station-work-guide/states.ts
enum WorkPhase {
  PREPARATION = 'preparation',
  POWER_ROOM = 'power_room',
  CUSTOMER_VISIT = 'customer_visit',
  EMERGENCY_INFO = 'emergency_info',
  REVIEW = 'review',
  COMPLETED = 'completed'
}

enum PowerRoomSubState {
  LOCATION = 'location',
  ENTRANCE_PHOTO = 'entrance_photo',
  NAMEPLATE_PHOTO = 'nameplate_photo',
  EQUIPMENT_STATUS = 'equipment_status',
  DEFECT_CHECK = 'defect_check',
  COMPLETED = 'completed'
}

class StateMachine {
  async transition(session: Session, event: string): Promise<void>
  async getCurrentState(session: Session): Promise<State>
  async isValidTransition(from: State, to: State): Promise<boolean>
}
```

**工作内容**:
- [ ] 创建Skill基础框架
- [ ] 实现状态机
- [ ] 实现Session数据模型
- [ ] 集成消息处理器

### 2. 工作启动阶段

**流程设计**:
```
用户: /start 阳光小区
    ↓
Agent:
  1. 验证用户权限
  2. 查询小区信息（WPS）
  3. 查询历史驻点记录
  4. 生成任务清单
  5. 发送引导消息
    ↓
等待用户选择工作类型
```

**实现代码**:
```typescript
async function handleStartCommand(message: Message, session: Session) {
  const communityName = extractCommunityName(message.content)
  
  // 查询小区信息
  const community = await wpsApi.queryRecords('community_info', {
    community_name: communityName,
    station_id: session.stationId
  })
  
  if (!community) {
    await sendMessage(message.userId, `未找到小区"${communityName}"，请检查名称是否正确。`)
    return
  }
  
  // 查询历史记录
  const history = await wpsApi.queryRecords('station_work_records', {
    community_id: community.community_id,
    orderBy: 'work_date DESC',
    limit: 1
  })
  
  // 生成任务清单
  const tasks = generateTaskList(community, history)
  
  // 更新Session
  session.state = 'collecting'
  session.phase = 'preparation'
  session.communityId = community.community_id
  session.communityName = community.community_name
  session.tasks = tasks
  await sessionManager.save(session)
  
  // 发送引导消息
  await sendStartMessage(message.userId, community, history, tasks)
}

function generateTaskList(community: Community, history: WorkRecord[]): Task[] {
  const tasks: Task[] = []
  
  // 基础任务
  tasks.push({ id: 'power_room', name: '配电房检查', priority: 'high' })
  
  // 根据历史记录添加建议任务
  if (history?.issue_found_count > 0) {
    tasks.push({ 
      id: 'issue_follow_up', 
      name: `跟进${history.issue_found_count}个待处理问题`, 
      priority: 'high' 
    })
  }
  
  // 根据小区特点添加任务
  if (community.sensitive_customer_count > 0) {
    tasks.push({ 
      id: 'sensitive_visit', 
      name: `走访${community.sensitive_customer_count}户敏感客户`, 
      priority: 'medium' 
    })
  }
  
  return tasks
}
```

**消息模板**:
```
🏠 {community_name} - 驻点工作启动
───────────────────
📍 小区信息：
• 地址：{address}
• 户数：{total_households}户
• 配电房：{power_room_count}个
• 上次驻点：{last_station_date}

📋 建议关注：
{issues}

请选择要开展的工作：
[配电房检查] [客户走访] [应急信息采集]

───────────────────
提示：输入数字或点击按钮选择
```

### 3. 配电房信息采集

**流程设计**:
```
用户选择"配电房检查"
    ↓
Agent: "请前往1号配电房，到达后回复'到达'"
    ↓
用户: "到达"
    ↓
Agent: "请拍摄配电房入口照片"
    ↓
用户: [照片]
    ↓
Agent: 
  1. 下载照片
  2. 保存到WPS
  3. "照片已保存，请描述配电房位置"
    ↓
用户: [语音] "3号楼地下室..."
    ↓
Agent:
  1. 语音识别
  2. 提取位置信息
  3. "已记录，请拍摄变压器铭牌"
    ↓
用户: [照片]
    ↓
Agent:
  1. 下载照片
  2. OCR识别
  3. 展示结果，要求确认
    ↓
用户: "正确"
    ↓
Agent: "请检查设备运行状态"
    ↓
[继续...]
```

**实现代码**:
```typescript
// 处理配电房采集
class PowerRoomCollector {
  async handleLocationInput(message: Message, session: Session) {
    // 语音识别
    const voiceResult = await sttTool.recognize({
      audioData: message.mediaData,
      devPid: LANGUAGE_MODELS.SICHUAN
    })
    
    // 提取位置信息
    const locationInfo = extractLocationInfo(voiceResult.text)
    
    // 保存到Session
    session.collectedData.powerRoom = {
      ...session.collectedData.powerRoom,
      location: voiceResult.text,
      locationExtracted: locationInfo
    }
    
    // 更新状态
    session.subState = 'entrance_photo'
    await sessionManager.save(session)
    
    // 发送下一步引导
    await sendMessage(message.userId, '✅ 已记录位置信息\n\n请拍摄配电房入口照片')
  }
  
  async handleNameplatePhoto(message: Message, session: Session) {
    // 下载照片
    const photoBuffer = await wecomApi.downloadMedia(message.mediaId)
    
    // 上传WPS
    const photoUrl = await wpsApi.uploadFile(photoBuffer, {
      folderId: session.communityFolderId + '/配电房/照片/'
    })
    
    // OCR识别
    const ocrResult = await ocrTool.recognizeNameplate({ imageUrl: photoUrl })
    
    // 置信度评估
    const assessment = assessOCRConfidence(ocrResult)
    
    // 保存识别结果
    session.collectedData.powerRoom.photos.push(photoUrl)
    session.collectedData.powerRoom.transformerInfo = ocrResult.fields
    
    // 根据置信度决定是否需要确认
    if (assessment.needsConfirmation) {
      await sendConfirmationMessage(message.userId, ocrResult, assessment)
      session.subState = 'confirming_nameplate'
    } else {
      session.subState = 'equipment_status'
      await sendMessage(message.userId, '✅ 铭牌信息已识别并保存\n\n请描述设备运行状态')
    }
    
    await sessionManager.save(session)
  }
  
  async handleConfirmation(message: Message, session: Session) {
    const action = parseConfirmationAction(message.content)
    
    switch (action) {
      case 'correct':
        session.subState = 'equipment_status'
        await sendMessage(message.userId, '✅ 已确认\n\n请描述设备运行状态')
        break
      case 'edit':
        await sendMessage(message.userId, '请发送修正后的信息，格式：\n型号：XXX\n容量：XXX')
        session.subState = 'editing_nameplate'
        break
      case 'retake':
        await sendMessage(message.userId, '请重新拍摄变压器铭牌照片')
        session.subState = 'nameplate_photo'
        break
    }
    
    await sessionManager.save(session)
  }
}
```

### 4. 客户走访记录

**流程设计**:
```
Agent: "建议走访以下客户：\n1. 张三（2-3-501）- 频繁停电投诉\n2. 李四（3-1-202）- 新装用户满意度调查"
    ↓
用户: "1"
    ↓
Agent: "客户：张三\n地址：2栋3单元501\n历史：投诉3次停电\n\n请前往走访，到达后回复'到达'"
    ↓
用户: "到达"
    ↓
Agent: "请记录客户反馈"
    ↓
用户: [语音] "客户反映近期未停电，表示满意"
    ↓
Agent:
  1. 语音识别
  2. "问题类型？"
    ↓
用户: "无"
    ↓
Agent: "客户满意度？"
    ↓
用户: "满意"
    ↓
Agent: "是否需要回访？"
    ↓
用户: "否"
    ↓
Agent: "记录完成，是否走访其他客户？"
```

**实现代码**:
```typescript
class CustomerVisitCollector {
  async recommendCustomers(session: Session): Promise<Customer[]> {
    // 查询敏感客户
    const sensitiveCustomers = await wpsApi.queryRecords('customer_info', {
      community_id: session.communityId,
      is_sensitive: true
    })
    
    // 查询近期未走访客户
    const threeMonthsAgo = new Date()
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3)
    
    const notVisitedRecently = await wpsApi.queryRecords('customer_info', {
      community_id: session.communityId,
      last_visit_date: { $lt: threeMonthsAgo }
    })
    
    // 查询有投诉历史的客户
    const complaintCustomers = await wpsApi.queryRecords('customer_info', {
      community_id: session.communityId,
      complaint_count: { $gt: 0 }
    })
    
    // 合并去重，按优先级排序
    return mergeAndSortCustomers([
      ...sensitiveCustomers,
      ...complaintCustomers,
      ...notVisitedRecently
    ])
  }
  
  async handleVisitRecord(message: Message, session: Session) {
    const voiceResult = await sttTool.recognize({
      audioData: message.mediaData
    })
    
    const visitRecord: CustomerVisitData = {
      customerId: session.currentCustomerId,
      visitContent: voiceResult.text,
      visitDate: new Date(),
      workerUserId: session.userId
    }
    
    session.collectedData.customerVisits.push(visitRecord)
    session.subState = 'issue_type'
    
    await sendMessage(message.userId, 
      '✅ 已记录\n\n问题类型？\n[无] [停电] [电费] [服务] [其他]'
    )
    await sessionManager.save(session)
  }
}
```

### 5. 智能审核

**审核规则**:
```typescript
interface ValidationRule {
  field: string
  required: boolean
  validator: (value: any) => ValidationResult
}

const AUDIT_RULES: ValidationRule[] = [
  {
    field: 'powerRoom.location',
    required: true,
    validator: (value) => ({
      valid: value && value.length >= 5,
      message: '位置描述过于简单'
    })
  },
  {
    field: 'powerRoom.photos',
    required: true,
    validator: (value) => ({
      valid: value && value.length >= 2,
      message: '照片数量不足（至少2张）'
    })
  },
  {
    field: 'powerRoom.transformerInfo.model',
    required: true,
    validator: (value) => ({
      valid: value && value.length > 0,
      message: '变压器型号未记录'
    })
  }
]

async function auditCollectedData(session: Session): Promise<AuditResult> {
  const issues: AuditIssue[] = []
  
  for (const rule of AUDIT_RULES) {
    const value = getFieldValue(session.collectedData, rule.field)
    const result = rule.validator(value)
    
    if (rule.required && !result.valid) {
      issues.push({
        field: rule.field,
        severity: 'error',
        message: result.message
      })
    } else if (!result.valid) {
      issues.push({
        field: rule.field,
        severity: 'warning',
        message: result.message
      })
    }
  }
  
  return {
    passed: issues.filter(i => i.severity === 'error').length === 0,
    issues,
    completeness: calculateCompleteness(session.collectedData)
  }
}
```

**审核报告**:
```
📋 采集数据审核报告
───────────────────
完整度：85%

✅ 已通过检查：
• 配电房位置信息 ✓
• 入口照片 2张 ✓
• 铭牌信息 ✓

⚠️ 建议补充：
• 设备运行状态（已记录但较简单）

❌ 必须补充：
• 缺陷检查（尚未完成）

[补充缺陷检查] [忽略并继续] [查看详情]
```

### 6. 数据保存

**保存流程**:
```typescript
async function saveCollectedData(session: Session): Promise<void> {
  const now = new Date()
  
  // 1. 创建驻点工作记录
  const workRecord = {
    record_id: generateId(),
    station_id: session.stationId,
    community_id: session.communityId,
    work_date: now,
    worker_user_id: session.userId,
    worker_name: session.userName,
    work_summary: generateSummary(session.collectedData),
    power_room_checked: !!session.collectedData.powerRoom,
    customer_visit_count: session.collectedData.customerVisits?.length || 0,
    issue_found_count: countIssues(session.collectedData),
    photo_count: countPhotos(session.collectedData),
    status: '已完成',
    created_at: now
  }
  
  await wpsApi.insertRecord('station_work_records', workRecord)
  
  // 2. 保存配电房信息
  if (session.collectedData.powerRoom) {
    await savePowerRoomInfo(session.communityId, session.collectedData.powerRoom)
  }
  
  // 3. 保存客户走访记录
  if (session.collectedData.customerVisits?.length > 0) {
    for (const visit of session.collectedData.customerVisits) {
      await wpsApi.insertRecord('customer_visit_records', {
        ...visit,
        record_id: generateId(),
        station_id: session.stationId,
        community_id: session.communityId
      })
    }
  }
  
  // 4. 更新小区信息
  await wpsApi.updateRecord('community_info', session.communityId, {
    last_station_date: now,
    station_count: { $inc: 1 }
  })
}
```

## 测试要求

### 单元测试
- [ ] 状态机转换测试
- [ ] 命令解析测试
- [ ] 数据验证测试
- [ ] 消息生成测试

### 集成测试
- [ ] 完整驻点工作流测试
- [ ] 多轮对话测试
- [ ] 异常处理测试
- [ ] 并发Session测试

### 场景测试
- [ ] 首次驻点场景
- [ ] 有历史记录驻点场景
- [ ] 多配电房小区场景
- [ ] 多客户走访场景

## 交付物

1. **Skill主代码**: `src/skills/station-work-guide/index.ts`
2. **状态机**: `src/skills/station-work-guide/states.ts`
3. **采集器**: `src/skills/station-work-guide/collectors/`
4. **消息模板**: `src/skills/station-work-guide/templates/`
5. **测试用例**: `tests/skills/station-work-guide/`

## 验收标准

- [ ] 完整驻点工作流可用
- [ ] 配电房采集功能正常
- [ ] 客户走访功能正常
- [ ] 智能审核准确
- [ ] 数据保存正确
- [ ] 异常处理完善
- [ ] 用户体验良好

## 注意事项

1. **每个步骤都要有超时处理**
2. **用户可随时取消或暂停**
3. **数据要实时保存，防止丢失**
4. **异常情况下要有明确的错误提示**
5. **多轮对话要保持上下文**

## 相关文档

- [详细设计方案 - StationWorkGuide](../design/detailed-design-v2.md#skill-1-驻点工作引导stationworkguide)
- PRD文档：`power-service-research/research/topics/field-info-agent/PRD-for-pm.md`

---

**创建时间**: 2026-03-17  
**负责人**: 待分配  
**状态**: 待开始  
**依赖**: TASK-002, TASK-003, TASK-004完成
