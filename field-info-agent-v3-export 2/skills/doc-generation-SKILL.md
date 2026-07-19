---
skill_id: doc-generation
name: 文档自动生成
version: 3.0.0
type: openclaw-skill
category: output
priority: P1
---

# Doc Generation Skill - 文档生成（Markdown版）

> 📄 基于Markdown的轻量级文档生成（v3.0 极简版）

## 一、功能定位

**核心能力**:
- 基于模板生成Markdown文档
- 自动填充工作数据
- 引用照片和记录
- 支持多种文档类型

**与旧版区别**:
```yaml
旧版 (v2.x):
  - 生成Word (.docx) 文件
  - 需要python-docx库
  - 依赖MinIO存储
  - 复杂模板渲染

新版 (v3.0) - 极简版:
  - 生成Markdown (.md) 文件
  - 纯文本模板
  - 本地文件系统存储
  - 简洁易读，Git友好
  - 零外部依赖
```

## 二、文档类型

### 2.1 支持文档

| 文档类型 | 文件名 | 用途 | 优先级 |
|---------|--------|------|--------|
| 驻点工作记录 | work-record.md | 完整记录一次驻点工作 | P0 |
| 供电简报 | power-briefing.md | 小区供电情况汇总 | P1 |
| 设备台账 | equipment-list.md | 设备清单和状态 | P2 |
| 问题汇总 | issues-summary.md | 发现问题和整改进度 | P2 |

### 2.2 文档存储位置

```
field-data/
└── communities/
    └── {小区名}/
        └── {YYYY-MM}/
            ├── work-record.md           # 工作记录
            └── documents/
                ├── {YYYYMMDD}_work-record.md
                ├── {YYYYMMDD}_power-briefing.md
                └── {YYYYMMDD}_equipment-list.md
```

## 三、生成流程

### 3.1 文档生成步骤

```
触发条件（自动/手动）
    ↓
读取Session数据
    ↓
读取当前work-record.md
    ↓
选择文档模板
    ↓
填充数据字段
    ↓
生成Markdown内容
    ↓
保存到documents目录
    ↓
更新README.md引用
    ↓
返回文档链接
```

### 3.2 模板变量

```markdown
# {{community_name}}供电简报

**生成时间**: {{generation_time}}  
**工作人员**: {{worker_name}}

## 一、小区基本信息

- **小区名称**: {{community_name}}
- **地址**: {{address}}
- **总户数**: {{total_households}}
- **配电房**: {{power_room_count}}个
- **变压器**: {{transformer_count}}台

## 二、本次工作

**日期**: {{work_date}}  
**时长**: {{work_duration}}

### 完成事项

- ✅ 配电房检查: {{power_room_checked}}个
- ✅ 客户走访: {{customer_visit_count}}户
- 📸 照片采集: {{photo_count}}张
- ⚠️ 发现问题: {{issue_count}}个

{{work_summary}}

## 三、照片记录

{{photo_section}}

## 四、设备状态

{{equipment_table}}

## 五、工作总结

{{conclusion}}

---

**数据来源**: [工作记录](./work-record.md)  
**生成时间**: {{timestamp}}
```

## 四、实现逻辑

### 4.1 数据收集

```typescript
// 从Session和工作记录收集数据
async function collectData(session: Session): Promise<TemplateData> {
  const workRecord = await readFile(
    `./field-data/communities/${session.community}/${session.date.substring(0,7)}/work-record.md`
  );
  
  return {
    community_name: session.community,
    work_date: session.date,
    worker_name: session.worker,
    work_duration: calculateDuration(session),
    power_room_count: extractPowerRoomCount(workRecord),
    customer_visit_count: extractCustomerCount(workRecord),
    photo_count: extractPhotoCount(workRecord),
    issue_count: extractIssueCount(workRecord),
    work_summary: extractSummary(workRecord),
    photo_section: generatePhotoSection(workRecord),
    equipment_table: generateEquipmentTable(workRecord),
    conclusion: generateConclusion(workRecord),
    timestamp: new Date().toISOString()
  };
}
```

### 4.2 Markdown生成

```typescript
async function generateMarkdown(
  templateName: string,
  data: TemplateData
): Promise<string> {
  // 1. 加载模板
  const template = await readFile(
    `./field-data/templates/${templateName}-template.md`
  );
  
  // 2. 替换变量
  let content = template;
  content = content.replace(/\{\{community_name\}\}/g, data.community_name);
  content = content.replace(/\{\{work_date\}\}/g, data.work_date);
  // ... 更多替换
  
  // 3. 替换复杂内容
  content = content.replace(/\{\{photo_section\}\}/g, data.photo_section);
  content = content.replace(/\{\{equipment_table\}\}/g, data.equipment_table);
  
  return content;
}

// 生成照片章节
function generatePhotoSection(workRecord: string): string {
  const photos = extractPhotos(workRecord);
  
  let section = "### 现场照片\n\n";
  photos.forEach((photo, index) => {
    section += `${index + 1}. [${photo.filename}](${photo.path})\n`;
    section += `   - 时间: ${photo.time}\n`;
    section += `   - 描述: ${photo.description}\n\n`;
  });
  
  return section;
}

// 生成设备表格
function generateEquipmentTable(workRecord: string): string {
  const equipments = extractEquipments(workRecord);
  
  let table = "| 编号 | 型号 | 容量 | 位置 | 状态 |\n";
  table += "|------|------|------|------|------|\n";
  
  equipments.forEach(eq => {
    const statusEmoji = eq.status === '正常' ? '✅' : '⚠️';
    table += `| ${eq.id} | ${eq.model} | ${eq.capacity} | ${eq.location} | ${statusEmoji} ${eq.status} |\n`;
  });
  
  return table;
}
```

### 4.3 文档保存

```typescript
async function saveDocument(
  docType: string,
  content: string,
  context: Context
): Promise<string> {
  const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
  const filename = `${date}_${docType}.md`;
  const filepath = `./field-data/communities/${context.community}/${context.month}/documents/${filename}`;
  
  // 确保目录存在
  await ensureDir(`./field-data/communities/${context.community}/${context.month}/documents`);
  
  // 写入文件
  await writeFile(filepath, content);
  
  // 更新README.md文档索引
  await updateDocIndex(context.community, {
    date: context.date,
    type: docType,
    filename,
    path: filepath
  });
  
  return filepath;
}
```

## 五、交互示例

### 5.1 自动触发

```
用户: "完成采集"

Agent:
✅ 驻点工作完成，正在生成文档...

📄 生成文档:
1. 驻点工作记录
2. 供电简报

⏱️ 预计时间: 3秒

[2秒后]

✅ 文档生成完成

📁 保存位置:
./field-data/communities/阳光小区/2024-03/documents/

📄 生成文件:
• 20240317_work-record.md
• 20240317_power-briefing.md

[查看工作记录] [查看供电简报]
```

### 5.2 手动触发

```
用户: "生成供电简报"

Agent:
📄 正在生成阳光小区供电简报...

包含内容:
• 小区基本信息
• 本次工作概况
• 设备状态评估
• 客户服务情况
• 问题与建议

✅ 文档生成完成

📄 供电简报-20240317.md
位置: 阳光小区/2024-03/documents/

[查看文档] [返回列表]
```

### 5.3 历史对比

```
用户: "对比一下历史数据"

Agent:
📊 阳光小区历史对比（近3次驻点）

| 指标 | 本次(3月) | 上次(2月) | 上上次(1月) |
|------|-----------|-----------|-------------|
| 发现问题 | 1个 | 2个 | 0个 |
| 客户走访 | 2户 | 1户 | 3户 |
| 工作时长 | 2小时 | 1.5小时 | 2.5小时 |
| 照片采集 | 8张 | 5张 | 12张 |

趋势分析: 
• 工作质量稳定，客户满意度保持优秀
• 问题发现率适中，设备状态良好
• 建议保持每月1次的驻点频率
```

## 六、模板系统

### 6.1 模板文件

```
field-data/templates/
├── work-record-template.md      # 工作记录模板
├── power-briefing-template.md   # 供电简报模板
├── equipment-list-template.md   # 设备台账模板
└── issues-summary-template.md   # 问题汇总模板
```

### 6.2 模板示例（供电简报）

```markdown
# {{community_name}}供电简报

**生成时间**: {{generation_time}}  
**工作人员**: {{worker_name}}  
**所属供电所**: {{station_name}}

---

## 一、小区基本信息

- **小区名称**: {{community_name}}
- **详细地址**: {{address}}
- **总户数**: {{total_households}}户
- **配电房数量**: {{power_room_count}}个
- **变压器数量**: {{transformer_count}}台
- **物业公司**: {{property_company}}

---

## 二、本次驻点工作概况

**工作日期**: {{work_date}}  
**工作时间**: {{work_duration}}

### 完成事项

{{completed_items}}

### 发现问题

{{issues_table}}

### 现场照片

本次采集 **{{photo_count}}张照片**，详见：
- [工作记录照片](./work-record.md#照片采集记录)

---

## 三、设备状态评估

### 变压器清单

{{equipment_table}}

### 设备状态统计

- **正常**: {{normal_count}}台 ({{normal_percent}}%)
- **注意**: {{attention_count}}台 ({{attention_percent}}%)
- **异常**: {{abnormal_count}}台 ({{abnormal_percent}}%)

---

## 四、客户服务情况

### 走访客户清单

{{customer_table}}

### 客户满意度统计

{{satisfaction_summary}}

---

## 五、问题与建议

### 待处理问题

{{pending_issues}}

### 工作建议

{{recommendations}}

---

## 六、历史对比

{{history_comparison}}

---

**文档生成时间**: {{timestamp}}  
**数据来源**: [驻点工作记录](./work-record.md)
```

## 七、文档管理

### 7.1 版本控制

```yaml
versioning:
  strategy: "日期版本"
  format: "{YYYYMMDD}_{type}.md"
  
examples:
  - 20240317_work-record.md
  - 20240317_power-briefing.md
  - 20240215_work-record.md
  
# 不覆盖历史文档，每次生成新文件
```

### 7.2 文档索引

在小区README.md中维护:

```markdown
## 文档档案

### 供电简报
- [2024-03-17 供电简报](./2024-03/documents/20240317_power-briefing.md)
- [2024-02-15 供电简报](./2024-02/documents/20240215_power-briefing.md)

### 工作记录
- [2024-03-17 驻点工作](./2024-03/work-record.md)
- [2024-02-15 驻点工作](./2024-02/work-record.md)

### 设备台账
- [设备清单](../equipment-list.md)（最新）
```

## 八、配置参数

```yaml
# openclaw.config.yaml
skills:
  doc_generation:
    enabled: true
    priority: normal
    
    config:
      # 路径配置
      data_root: "./field-data"
      template_path: "./field-data/templates"
      output_subdir: "documents"
      
      # 文档类型
      doc_types:
        work_record:
          template: "work-record-template.md"
          auto_generate: true
          filename_format: "{date}_work-record.md"
          
        power_briefing:
          template: "power-briefing-template.md"
          auto_generate: true
          filename_format: "{date}_power-briefing.md"
          
        equipment_list:
          template: "equipment-list-template.md"
          auto_generate: false
          filename_format: "equipment-list.md"
      
      # 历史对比
      history_comparison:
        enabled: true
        compare_count: 3  # 对比最近3次
        
      # 输出格式
      include_timestamps: true
      include_photo_links: true
```

## 九、优势对比

### 9.1 Markdown vs Word

| 维度 | Markdown (v3.0) | Word (v2.x) |
|------|-----------------|-------------|
| **存储** | 本地文件系统 | MinIO对象存储 |
| **依赖** | 零外部依赖 | python-docx + MinIO |
| **版本控制** | Git原生支持 | 需自定义版本管理 |
| **可读性** | 纯文本，直接阅读 | 需Word软件打开 |
| **转换** | 可转PDF/HTML/Word | 仅Word格式 |
| **编辑** | 任何文本编辑器 | 需Word |
| **打印** | 需转换为PDF | 直接打印 |
| **复杂度** | 低 | 高 |

### 9.2 适用场景

**Markdown版适合**:
- 快速原型和MVP
- 技术团队内部使用
- Git版本控制需求
- 成本敏感场景

**Word版适合**:
- 正式报告输出
- 非技术人员使用
- 复杂排版需求
- 对外正式文档

## 十、扩展建议

### 10.1 Markdown转Word

如需Word格式，可使用工具转换:

```python
# 使用pandoc转换
# pandoc input.md -o output.docx

# 或使用python库
import pypandoc
output = pypandoc.convert_file('input.md', 'docx', outputfile='output.docx')
```

### 10.2 在线预览

建议使用支持Markdown的编辑器:
- Typora（桌面端）
- VS Code + Markdown插件
- 在线Markdown编辑器

---

**技能版本**: 3.0.0  
**适用Agent**: field-collector  
**依赖**: 纯文件操作，零外部依赖
