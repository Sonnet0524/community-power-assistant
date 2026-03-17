---
name: doc-generation
description: |
  工作文档自动生成技能
  
  根据现场采集的数据，自动生成标准化的驻点工作文档，
  支持Word(docx)格式导出，包含照片、分析结果、工作记录等。
  
  支持文档类型：
  - 驻点工作记录表（含配电房检查、客户走访）
  - 设备缺陷报告
  - 安全隐患整改通知单
  - 应急通道位置图
  
  核心能力：
  - 模板化文档生成
  - 自动数据填充
  - 照片自动排版
  - 版本控制与归档

metadata:
  openclaw:
    emoji: 📄
    category: output
    requires:
      tools:
        - docx-generator
        - minio-storage
        - postgres-query
      channels:
        - wecom
    triggers:
      - type: event
        condition: collection_completed
      - type: command
        condition: generate_report_requested
---

# Doc Generation - 工作文档自动生成技能

## 概述

本技能负责根据现场采集的数据，自动生成标准化的工作文档。支持多种文档类型，采用模板化设计，确保文档格式统一、内容完整。

## 文档类型

### 1. 驻点工作记录表 (station-work-record)
**用途**: 记录完整的驻点工作过程
**内容**: 
- 基本信息（时间、地点、人员）
- 配电房检查记录
- 客户走访记录
- 照片附件
- 工作总结

**模板**: `templates/station-work-record.docx`

### 2. 设备缺陷报告 (defect-report)
**用途**: 详细记录发现的设备缺陷
**内容**:
- 缺陷设备信息
- 缺陷描述与照片
- AI分析结果
- 处理建议
- 整改跟踪

**模板**: `templates/defect-report.docx`

### 3. 安全隐患整改通知单 (safety-notice)
**用途**: 正式的安全隐患整改通知
**内容**:
- 隐患描述
- 整改要求
- 整改期限
- 整改结果跟踪

**模板**: `templates/safety-notice.docx`

### 4. 应急通道位置图 (emergency-map)
**用途**: 记录应急通道位置信息
**内容**:
- 地图位置标注
- 通道照片
-  access说明
- 联系方式

**模板**: `templates/emergency-map.docx`

## 文档生成流程

```
1. 接收生成请求
   ↓
2. 获取Session数据
   ├─ 2.1 基本信息
   ├─ 2.2 采集数据
   ├─ 2.3 分析结果
   └─ 2.4 照片列表
   ↓
3. 选择文档模板
   ↓
4. 数据预处理
   ├─ 4.1 格式化数据
   ├─ 4.2 下载照片
   └─ 4.3 生成表格
   ↓
5. 渲染文档
   ├─ 5.1 填充文本字段
   ├─ 5.2 插入照片
   ├─ 5.3 生成表格
   └─ 5.4 应用样式
   ↓
6. 保存文档
   ├─ 6.1 保存到MinIO
   └─ 6.2 记录到数据库
   ↓
7. 返回下载链接
```

## 模板设计

### 模板变量

```yaml
# 基本信息变量
basic_info:
  - {{STATION_NAME}}          # 供电所名称
  - {{COMMUNITY_NAME}}        # 社区名称
  - {{WORK_DATE}}            # 工作日期
  - {{WORKER_NAME}}          # 工作人员
  - {{SESSION_ID}}           # 会话编号

# 配电房数据变量
power_room:
  - {{PR_CHECKLIST}}         # 配电房检查清单（表格）
  - {{PR_PHOTOS}}           # 配电房照片
  - {{PR_FINDINGS}}         # 配电房发现问题
  - {{PR_STATUS}}           # 配电房整体状态

# 客户走访数据变量
customer_visit:
  - {{CV_LIST}}             # 客户走访列表（表格）
  - {{CV_SUMMARY}}          # 走访总结

# 分析结果变量
analysis:
  - {{ANALYSIS_SUMMARY}}    # 分析摘要
  - {{ISSUES_LIST}}         # 问题清单
  - {{RECOMMENDATIONS}}     # 建议清单

# 照片变量
photos:
  - {{PHOTO_GRID}}          # 照片网格布局
  - {{PHOTO_COUNT}}         # 照片总数
```

### 模板示例（驻点工作记录表）

```
                    供电所驻点工作记录表

一、基本信息
┌─────────────────────────────────────────────────────┐
│ 供电所：{{STATION_NAME}}                              │
│ 社区：{{COMMUNITY_NAME}}                              │
│ 日期：{{WORK_DATE}}                                   │
│ 工作人员：{{WORKER_NAME}}                             │
│ 记录编号：{{SESSION_ID}}                              │
└─────────────────────────────────────────────────────┘

二、配电房检查
{{PR_CHECKLIST}}

发现问题：
{{PR_FINDINGS}}

三、客户走访
{{CV_LIST}}

四、照片记录
{{PHOTO_GRID}}

五、工作总结
{{WORK_SUMMARY}}

六、后续跟进
{{FOLLOW_UP}}

                                    记录人：___________
                                    日期：_____________
```

## 数据预处理

### 检查清单格式化

```typescript
function formatChecklist(items: ChecklistItem[]): Table {
  const headers = ['序号', '检查项', '要求', '结果', '备注']
  const rows = items.map((item, index) => [
    index + 1,
    item.name,
    item.description,
    item.status === 'completed' ? '✓' : '○',
    item.notes || ''
  ])
  
  return createTable(headers, rows)
}
```

### 照片网格生成

```typescript
function createPhotoGrid(photos: PhotoItem[], cols: number = 3): DocumentElement {
  const rows = Math.ceil(photos.length / cols)
  const grid = []
  
  for (let i = 0; i < rows; i++) {
    const rowPhotos = photos.slice(i * cols, (i + 1) * cols)
    const row = rowPhotos.map(photo => ({
      type: 'image',
      src: photo.url,
      caption: photo.description || `照片${i * cols + rowPhotos.indexOf(photo) + 1}`
    }))
    grid.push(row)
  }
  
  return { type: 'grid', rows: grid }
}
```

### 问题清单格式化

```typescript
function formatIssuesList(findings: FindingItem[]): string {
  if (findings.length === 0) {
    return '本次检查未发现明显问题。'
  }
  
  const severityEmojis = {
    critical: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🟢'
  }
  
  return findings.map((finding, index) => {
    const emoji = severityEmojis[finding.severity]
    return `${index + 1}. ${emoji} 【${finding.category}】${finding.description}`
  }).join('\n')
}
```

## 文档生成实现

### DocxGenerator工具

```typescript
interface DocxGenerator {
  // 加载模板
  loadTemplate(templatePath: string): Promise<Template>
  
  // 设置数据
  setData(data: Record<string, any>): void
  
  // 插入图片
  insertImage(placeholder: string, imagePath: string): void
  
  // 插入表格
  insertTable(placeholder: string, table: Table): void
  
  // 生成文档
  generate(outputPath: string): Promise<void>
}

// 使用示例
async function generateStationWorkRecord(session: FieldWorkSession): Promise<string> {
  const generator = new DocxGenerator()
  
  // 1. 加载模板
  await generator.loadTemplate('templates/station-work-record.docx')
  
  // 2. 准备数据
  const data = {
    STATION_NAME: session.stationName,
    COMMUNITY_NAME: session.communityName,
    WORK_DATE: formatDate(session.createdAt),
    WORKER_NAME: session.workerName,
    SESSION_ID: session.sessionId,
    PR_CHECKLIST: formatChecklist(session.data.powerRoom?.checklist || []),
    PR_FINDINGS: formatIssuesList(session.data.photoAnalysis?.findings || []),
    CV_LIST: formatCustomerList(session.data.customers || []),
    PHOTO_GRID: createPhotoGrid(session.data.photos, 2),
    ANALYSIS_SUMMARY: session.data.photoAnalysis?.summary || ''
  }
  
  // 3. 设置数据
  generator.setData(data)
  
  // 4. 插入照片
  for (let i = 0; i < session.data.photos.length; i++) {
    const photo = session.data.photos[i]
    generator.insertImage(`PHOTO_${i}`, photo.localPath)
  }
  
  // 5. 生成临时文件
  const tempPath = `./temp/${session.sessionId}.docx`
  await generator.generate(tempPath)
  
  // 6. 上传到MinIO
  const docUrl = await minio.upload(
    'field-documents',
    `reports/${session.sessionId}.docx`,
    tempPath
  )
  
  // 7. 清理临时文件
  await fs.unlink(tempPath)
  
  return docUrl
}
```

## 文档存储

### 存储结构

```
minio://field-documents/
├── reports/
│   ├── {session_id}.docx              # 原始报告
│   ├── {session_id}_v{version}.docx   # 版本化报告
│   └── archive/
│       └── {year}/{month}/
├── templates/
│   ├── station-work-record.docx
│   ├── defect-report.docx
│   ├── safety-notice.docx
│   └── emergency-map.docx
└── temp/
    └── {session_id}.docx              # 临时文件（自动清理）
```

### 数据库记录

```sql
-- 文档记录表
CREATE TABLE generated_documents (
  doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  doc_type VARCHAR(50) NOT NULL,
  doc_name VARCHAR(255) NOT NULL,
  storage_path VARCHAR(500) NOT NULL,
  download_url VARCHAR(500) NOT NULL,
  file_size BIGINT,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(100),
  metadata JSONB,
  
  FOREIGN KEY (session_id) REFERENCES field_sessions(session_id)
);

-- 文档版本表
CREATE TABLE document_versions (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id UUID NOT NULL,
  version INTEGER NOT NULL,
  storage_path VARCHAR(500) NOT NULL,
  changes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(100),
  
  FOREIGN KEY (doc_id) REFERENCES generated_documents(doc_id)
);
```

## 文档生成消息

### 生成中通知

```
📄 正在生成工作报告...

文档类型: 驻点工作记录表
包含内容:
• 配电房检查记录 (5项)
• 客户走访记录 (3户)
• 照片 (8张)
• AI分析结果

预计生成时间: 10秒
```

### 生成完成通知

```
✅ 工作报告生成完成

📋 文档信息：
• 名称: 阳光社区驻点工作记录表_20260318.docx
• 大小: 3.2 MB
• 页数: 12页
• 照片: 8张

📥 下载链接：
[点击下载文档]

💾 文档已自动归档，可随时查看历史版本
```

### 生成失败通知

```
❌ 文档生成失败

错误信息: 模板文件缺失

建议操作：
• 请稍后重试
• 联系管理员检查模板配置

您的数据已保存，不会丢失
```

## 版本控制

### 版本创建

```typescript
async function createDocumentVersion(
  docId: string,
  changes: string
): Promise<DocumentVersion> {
  // 1. 获取当前版本
  const currentDoc = await getDocument(docId)
  const newVersion = currentDoc.version + 1
  
  // 2. 复制文件到新版本路径
  const newPath = currentDoc.storage_path.replace(
    `.docx`,
    `_v${newVersion}.docx`
  )
  await minio.copy(currentDoc.storage_path, newPath)
  
  // 3. 记录版本
  const version = await db.insert('document_versions', {
    doc_id: docId,
    version: newVersion,
    storage_path: newPath,
    changes: changes,
    created_by: getCurrentUser()
  })
  
  // 4. 更新文档版本号
  await db.update('generated_documents', docId, {
    version: newVersion
  })
  
  return version
}
```

## 使用示例

### 示例1: 生成驻点工作记录

```typescript
// 用户完成采集后自动触发
async function onCollectionComplete(sessionId: string) {
  const session = await getSession(sessionId)
  
  // 生成文档
  const docUrl = await generateStationWorkRecord(session)
  
  // 发送通知
  await sendMessage({
    userId: session.userId,
    text: `✅ 工作报告已生成\n\n📥 下载：${docUrl}`
  })
}
```

### 示例2: 生成设备缺陷报告

```typescript
// 当发现严重缺陷时
async function generateDefectReport(
  sessionId: string,
  findings: FindingItem[]
) {
  const criticalFindings = findings.filter(
    f => f.severity === 'critical' || f.severity === 'high'
  )
  
  if (criticalFindings.length > 0) {
    const docUrl = await generateDocument({
      type: 'defect-report',
      sessionId,
      data: { findings: criticalFindings }
    })
    
    // 发送紧急通知
    await sendUrgentNotification({
      title: '发现严重设备缺陷',
      docUrl,
      findings: criticalFindings
    })
  }
}
```

---

**版本**: 1.0.0  
**作者**: PM Agent  
**最后更新**: 2026-03-18
