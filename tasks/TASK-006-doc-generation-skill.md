# Task-006: AutoDocGeneration Skill开发

## 任务概述

**任务ID**: TASK-006  
**任务名称**: AutoDocGeneration Skill开发  
**优先级**: 🟡 高  
**预计工期**: 3-4天  
**依赖**: TASK-002, TASK-005

## 任务目标

开发文档自动生成Skill，实现基于采集数据自动生成标准化业务文档：
1. 小区供电简报
2. 应急发电指引
3. 驻点工作总结
4. 优质服务简报

## 详细工作内容

### 1. Skill框架搭建

**Skill定义**:
```typescript
// src/skills/auto-doc-generation/index.ts
export class AutoDocGenerationSkill implements Skill {
  id = 'auto_doc_generation'
  name = '文档自动生成'
  version = '1.0.0'
  
  triggers = [
    { type: 'command', pattern: '/generate' },
    { type: 'command', pattern: '/doc' },
    { type: 'event', event: 'collection_completed' }
  ]
  
  async handle(message: Message, session: Session): Promise<void>
}
```

**文档类型定义**:
```typescript
enum DocumentType {
  POWER_BRIEFING = 'power_briefing',       // 小区供电简报
  EMERGENCY_GUIDE = 'emergency_guide',     // 应急发电指引
  WORK_SUMMARY = 'work_summary',           // 驻点工作总结
  SERVICE_REPORT = 'service_report'        // 优质服务简报
}

interface DocumentTemplate {
  type: DocumentType
  name: string
  templateFile: string
  dataSource: DataSource[]
  outputFormat: ('docx' | 'pdf')[]
}
```

### 2. 数据查询和组装

**数据查询服务**:
```typescript
class DocumentDataService {
  constructor(private wpsApi: WPSAPITool) {}
  
  // 查询小区供电简报所需数据
  async queryPowerBriefingData(communityId: string): Promise<PowerBriefingData> {
    const [community, powerRooms, visits, transformers] = await Promise.all([
      this.wpsApi.queryRecords('community_info', { community_id: communityId }),
      this.wpsApi.queryRecords('power_room_info', { community_id: communityId }),
      this.wpsApi.queryRecords('customer_visit_records', { 
        community_id: communityId,
        visit_date: { $gte: getLastMonth() }
      }),
      this.wpsApi.queryRecords('transformer_info', { 
        community_id: communityId 
      })
    ])
    
    return {
      community: community[0],
      powerRooms,
      visits,
      transformers,
      statistics: {
        totalVisits: visits.length,
        avgSatisfaction: calculateAverageSatisfaction(visits),
        issueCount: countIssues(visits)
      }
    }
  }
  
  // 查询应急指引所需数据
  async queryEmergencyGuideData(communityId: string): Promise<EmergencyGuideData> {
    const [community, emergencyInfo, powerRooms] = await Promise.all([
      this.wpsApi.queryRecords('community_info', { community_id: communityId }),
      this.wpsApi.queryRecords('emergency_access_info', { community_id: communityId }),
      this.wpsApi.queryRecords('power_room_info', { community_id: communityId })
    ])
    
    return {
      community: community[0],
      emergencyInfo: emergencyInfo[0],
      powerRooms,
      // 提取照片URL
      photos: {
        entry: emergencyInfo[0]?.entry_point_photos || [],
        parking: emergencyInfo[0]?.parking_point_photos || [],
        access: emergencyInfo[0]?.access_point_photos || []
      }
    }
  }
  
  // 查询驻点工作总结数据
  async queryWorkSummaryData(recordId: string): Promise<WorkSummaryData> {
    const record = await this.wpsApi.queryRecords('station_work_records', {
      record_id: recordId
    })
    
    const [community, powerRooms, visits] = await Promise.all([
      this.wpsApi.queryRecords('community_info', { 
        community_id: record[0].community_id 
      }),
      this.wpsApi.queryRecords('power_room_info', {
        community_id: record[0].community_id
      }),
      this.wpsApi.queryRecords('customer_visit_records', {
        record_id: recordId
      })
    ])
    
    return {
      record: record[0],
      community: community[0],
      powerRooms,
      visits
    }
  }
}
```

### 3. 文档生成引擎

**模板填充引擎**:
```typescript
class DocumentGenerationEngine {
  constructor(private wpsApi: WPSAPITool) {}
  
  async generateDocument(
    templateType: DocumentType,
    data: any,
    outputName: string
  ): Promise<{ fileId: string; url: string }> {
    // 1. 加载模板
    const templateId = this.getTemplateId(templateType)
    
    // 2. 数据格式化
    const formattedData = this.formatDataForTemplate(templateType, data)
    
    // 3. 生成文档
    const result = await this.wpsApi.generateDocument({
      template_id: templateId,
      data: formattedData,
      output_name: outputName,
      output_format: 'docx'
    })
    
    return result
  }
  
  private formatDataForTemplate(type: DocumentType, data: any): any {
    switch (type) {
      case DocumentType.POWER_BRIEFING:
        return this.formatPowerBriefingData(data)
      case DocumentType.EMERGENCY_GUIDE:
        return this.formatEmergencyGuideData(data)
      case DocumentType.WORK_SUMMARY:
        return this.formatWorkSummaryData(data)
      case DocumentType.SERVICE_REPORT:
        return this.formatServiceReportData(data)
    }
  }
  
  private formatPowerBriefingData(data: PowerBriefingData): any {
    return {
      community_name: data.community.community_name,
      address: data.community.address,
      total_households: data.community.total_households,
      power_room_count: data.powerRooms.length,
      transformer_count: data.transformers.length,
      
      // 格式化日期
      date: formatDate(new Date()),
      
      // 统计数据
      month_visits: data.statistics.totalVisits,
      avg_satisfaction: data.statistics.avgSatisfaction,
      
      // 表格数据
      power_room_table: data.powerRooms.map(room => ({
        name: room.room_name,
        location: room.location_description,
        transformer_count: room.transformer_count,
        status: room.equipment_status
      })),
      
      // 照片
      photos: data.powerRooms.flatMap(r => r.photo_urls)
    }
  }
}
```

### 4. 文档模板设计

#### 4.1 小区供电简报模板

**模板结构**:
```
封面
├── 标题：{{community_name}} 供电简报
├── 生成日期：{{date}}
├── 生成单位：{{station_name}}
└── 生成人：{{worker_name}}

第一章 小区基本信息
├── 小区名称：{{community_name}}
├── 详细地址：{{address}}
├── 总户数：{{total_households}}户
├── 配电房数量：{{power_room_count}}个
├── 变压器数量：{{transformer_count}}台
└── 物业信息：{{property_company}} {{property_contact}}

第二章 供电设施概况
{{#power_room_table}}
| 配电房名称 | 位置 | 变压器数量 | 设备状态 |
{{/power_room_table}}

第三章 客户服务情况
├── 本月走访：{{month_visits}}户
├── 平均满意度：{{avg_satisfaction}}
└── 问题处理：{{issue_count}}项

第四章 存在问题及建议
{{#issues}}
• {{description}}
{{/issues}}

附件：现场照片
{{#photos}}
[图片：{{.}}]
{{/photos}}
```

**Word模板占位符**:
```docx
{{community_name}} - 供电服务简报
─────────────────────────────────

一、小区概况
小区名称：{{community_name}}
地址：{{address}}
总户数：{{total_households}}户

二、供电设施
{{#power_rooms}}
配电房：{{name}}
位置：{{location}}
变压器：{{transformer_count}}台
状态：{{status}}
{{/power_rooms}}

三、客户服务
本月走访{{month_visits}}户，平均满意度{{avg_satisfaction}}。

四、建议
{{suggestions}}

生成时间：{{date}}
```

#### 4.2 应急发电指引模板

**模板结构**:
```
标题：{{community_name}} 应急发电车接入指引

一、小区位置
地址：{{address}}

二、发电车进入点
{{entry_point_description}}
[图片：{{entry_point_photos}}]

三、停放点
{{parking_point_description}}
[图片：{{parking_point_photos}}]

四、接入点
{{access_point_description}}
[图片：{{access_point_photos}}]

五、电缆信息
型号：{{cable_model}}
长度：{{cable_length}}米

六、物业联系
联系人：{{property_contact}}
电话：{{property_phone}}

七、注意事项
1. 进入小区前联系物业
2. 停放时注意地面承重
3. 接入时确保断电操作
```

### 5. 文档管理和分享

**保存和归档**:
```typescript
class DocumentArchiveService {
  constructor(private wpsApi: WPSAPITool) {}
  
  async archiveDocument(
    fileId: string,
    communityId: string,
    docType: DocumentType
  ): Promise<{ shareUrl: string }> {
    // 1. 获取小区文件夹ID
    const community = await this.wpsApi.queryRecords('community_info', {
      community_id: communityId
    })
    const folderId = community[0].wps_folder_id
    
    // 2. 根据文档类型确定子文件夹
    const subFolder = this.getSubFolderByType(docType)
    const targetFolderId = await this.wpsApi.getOrCreatePath(
      `${folderId}/${subFolder}/`
    )
    
    // 3. 移动文档到目标文件夹
    await this.wpsApi.moveFile(fileId, targetFolderId)
    
    // 4. 生成分享链接
    const shareUrl = await this.wpsApi.getShareLink(fileId, 'read')
    
    // 5. 记录到数据库
    await this.wpsApi.insertRecord('document_records', {
      document_id: generateId(),
      community_id: communityId,
      document_type: docType,
      file_id: fileId,
      share_url: shareUrl,
      created_at: new Date()
    })
    
    return { shareUrl }
  }
  
  private getSubFolderByType(type: DocumentType): string {
    const folderMap = {
      [DocumentType.POWER_BRIEFING]: '供电简报',
      [DocumentType.EMERGENCY_GUIDE]: '',  // 根目录
      [DocumentType.WORK_SUMMARY]: '驻点工作',
      [DocumentType.SERVICE_REPORT]: '服务简报'
    }
    return folderMap[type] || ''
  }
}
```

### 6. 消息通知

**生成完成通知**:
```typescript
async function sendGenerationCompleteMessage(
  userId: string,
  docType: DocumentType,
  shareUrl: string
): Promise<void> {
  const docNames = {
    [DocumentType.POWER_BRIEFING]: '小区供电简报',
    [DocumentType.EMERGENCY_GUIDE]: '应急发电指引',
    [DocumentType.WORK_SUMMARY]: '驻点工作总结',
    [DocumentType.SERVICE_REPORT]: '优质服务简报'
  }
  
  const message = `✅ ${docNames[docType]}已生成

📄 文档链接：${shareUrl}

💡 提示：
• 点击链接可在线查看
• 文档已保存到知识库
• 供电所同事均可访问

[查看文档] [分享给同事]`
  
  await wecomApi.sendMarkdownMessage(userId, message)
}
```

## 文档模板文件

**模板文件清单**:
1. `templates/power-briefing.docx` - 小区供电简报模板
2. `templates/emergency-guide.docx` - 应急发电指引模板
3. `templates/work-summary.docx` - 驻点工作总结模板
4. `templates/service-report.docx` - 优质服务简报模板

**模板设计要求**:
- 使用标准Word格式（.docx）
- 占位符格式：`{{field_name}}`
- 表格使用简单结构
- 预留照片插入位置
- 统一字体和样式

## 测试要求

### 单元测试
- [ ] 数据查询测试
- [ ] 数据格式化测试
- [ ] 文档生成测试
- [ ] 归档流程测试

### 集成测试
- [ ] 端到端文档生成流程
- [ ] 所有4种文档类型测试
- [ ] 大文件生成测试
- [ ] 并发生成测试

### 性能测试
- [ ] 文档生成时间 < 10秒
- [ ] 数据查询时间 < 2秒
- [ ] 大文件（50+照片）生成时间 < 30秒

## 交付物

1. **Skill主代码**: `src/skills/auto-doc-generation/index.ts`
2. **数据服务**: `src/skills/auto-doc-generation/data-service.ts`
3. **生成引擎**: `src/skills/auto-doc-generation/generation-engine.ts`
4. **归档服务**: `src/skills/auto-doc-generation/archive-service.ts`
5. **Word模板**: `templates/*.docx`
6. **测试用例**: `tests/skills/auto-doc-generation/`

## 验收标准

- [ ] 4种文档模板可用
- [ ] 文档生成正确完整
- [ ] 照片正确插入
- [ ] 分享链接可访问
- [ ] 文档正确归档
- [ ] 通知消息发送成功

## 注意事项

1. **模板文件需提前准备并上传到WPS**
2. **照片URL需可访问，否则无法插入**
3. **大量照片时考虑分批处理**
4. **文档生成失败时要有降级方案**
5. **保留生成日志，便于问题排查**

## 相关文档

- [详细设计方案 - AutoDocGeneration](../design/detailed-design-v2.md#skill-2-文档自动生成autodocgeneration)
- WPS文档生成API文档

---

**创建时间**: 2026-03-17  
**负责人**: 待分配  
**状态**: 待开始  
**依赖**: TASK-002完成，TASK-005完成
