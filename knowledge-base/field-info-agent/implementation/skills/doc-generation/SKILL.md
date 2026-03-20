# Skill: doc_generation

## Metadata

| 属性 | 值 |
|------|-----|
| **Name** | doc_generation |
| **Description** | 文档自动生成Skill，根据采集数据生成供电简报/应急指引/工作总结 |
| **Version** | 1.0.0 |
| **Author** | Field Core Team |
| **Category** | Document Generation |
| **Last Updated** | 2026-03-20 |

## Input Schema

```yaml
input:
  doc_type:
    type: string
    description: 文档类型
    enum: ["briefing", "emergency", "summary"]
    default: "briefing"
    
  task_id:
    type: string
    description: 任务ID
    required: true
    
  data:
    type: object
    description: 任务数据
    required: true
    properties:
      # 供电简报所需字段
      station:
        type: string
        description: 供电所名称
      date:
        type: string
        description: 日期
      staff:
        type: string
        description: 工作人员
      location:
        type: string
        description: 工作地点
      collection_data:
        type: string
        description: 采集数据描述
        
      # 应急指引所需字段
      event_type:
        type: string
        description: 事件类型
      time:
        type: string
        description: 发生时间
      impact:
        type: string
        description: 影响范围
      current_status:
        type: string
        description: 当前状况
      scene_description:
        type: string
        description: 现场描述
        
      # 工作总结所需字段
      period:
        type: string
        description: 总结周期
      department:
        type: string
        description: 所属部门
      reporter:
        type: string
        description: 汇报人
      completed_tasks:
        type: string
        description: 完成工作内容
      issues:
        type: string
        description: 发现问题
      task_count:
        type: integer
        description: 完成任务数
      issue_count:
        type: integer
        description: 发现问题数
      fix_rate:
        type: number
        description: 整改完成率(%)
      satisfaction:
        type: number
        description: 满意度(%)
        
  photos:
    type: array
    description: 照片URL列表
    items:
      type: string
    default: []
    
  user_id:
    type: string
    description: 用户ID（记录生成人）
    default: "system"
```

## Output Schema

```yaml
output:
  response:
    type: string
    description: 生成结果消息
    
  data:
    type: object
    properties:
      document_url:
        type: string
        description: 文档在MinIO的URL
        
      preview:
        type: string
        description: Markdown格式的文档预览
        
      share_link:
        type: string
        description: 带预签名的分享链接（7天有效期）
        
      doc_type:
        type: string
        description: 文档类型
        
      generated_at:
        type: string
        description: 生成时间
```

## System Prompt

```
你是一位专业的电力行业文档撰写专家。你的职责是根据现场采集的数据，
自动生成专业、规范、结构化的文档。

文档类型包括：
1. 供电简报 - 日常巡检工作报告
2. 应急指引 - 突发事件处置方案
3. 工作总结 - 周期性工作汇总

撰写要求：
- 使用规范的电力行业术语
- 内容客观、准确、完整
- 结构清晰，层次分明
- 突出关键信息和问题
- 提供可操作的建议

安全原则：
- 涉及应急处理时，始终将人身安全放在首位
- 明确风险提示和注意事项
- 操作步骤要具体、可执行
```

## Examples

### Example 1: 生成供电简报

**Input:**
```json
{
  "doc_type": "briefing",
  "task_id": "task_20260320_001",
  "data": {
    "station": "城北供电所",
    "date": "2026-03-20",
    "staff": "张三、李四",
    "location": "工业园区A区配电室",
    "collection_data": "变压器温度65℃，运行正常；开关柜无异常声响；接地电阻测试合格"
  },
  "photos": [
    "http://minio/photos/2026-03-20/transformer_01.jpg",
    "http://minio/photos/2026-03-20/switchgear_01.jpg"
  ],
  "user_id": "user_zhangsan"
}
```

**Output:**
```json
{
  "response": "✅ 城北供电所供电简报（2026-03-20）已生成\n\n# 城北供电所供电简报（2026-03-20）\n\n**生成时间**：2026-03-20 14:30:00...",
  "data": {
    "document_url": "http://minio/generated-docs/briefing/20260320_城北供电所_供电简报.docx",
    "preview": "# 城北供电所供电简报（2026-03-20）...",
    "share_link": "http://minio/generated-docs/briefing/20260320_城北供电所_供电简报.docx?token=xxx",
    "doc_type": "briefing",
    "generated_at": "2026-03-20 14:30:00"
  }
}
```

### Example 2: 生成应急指引

**Input:**
```json
{
  "doc_type": "emergency",
  "task_id": "task_emergency_001",
  "data": {
    "event_type": "变压器故障跳闸",
    "location": "商业街配电室",
    "time": "2026-03-20 15:30",
    "impact": "影响商业街200户商户用电",
    "current_status": "已隔离故障设备，启动备用电源",
    "scene_description": "10kV变压器冒烟，已停电处理"
  },
  "photos": [
    "http://minio/photos/emergency/transformer_damage.jpg"
  ],
  "user_id": "user_emergency"
}
```

**Output:**
```json
{
  "response": "✅ 变压器故障跳闸应急处置指引已生成\n\n**生成时间**：2026-03-20 15:45:00...",
  "data": {
    "document_url": "http://minio/generated-docs/emergency/20260320_商业街配电室_应急指引.docx",
    "preview": "# 变压器故障跳闸应急处置指引...",
    "share_link": "http://minio/generated-docs/emergency/20260320_商业街配电室_应急指引.docx?token=xxx",
    "doc_type": "emergency",
    "generated_at": "2026-03-20 15:45:00"
  }
}
```

### Example 3: 生成工作总结

**Input:**
```json
{
  "doc_type": "summary",
  "task_id": "task_summary_202603",
  "data": {
    "period": "2026年3月",
    "department": "运维检修部",
    "reporter": "王五",
    "completed_tasks": "完成巡检任务35次，设备维护12次，故障抢修8次",
    "issues": "发现设备隐患5处，已整改4处，1处正在处理",
    "task_count": 35,
    "issue_count": 5,
    "fix_rate": 80,
    "satisfaction": 92
  },
  "photos": [],
  "user_id": "user_wangwu"
}
```

**Output:**
```json
{
  "response": "✅ 2026年3月工作总结报告已生成\n\n**生成时间**：2026-03-31 17:00:00...",
  "data": {
    "document_url": "http://minio/generated-docs/summary/20260331_2026年3月_工作总结.docx",
    "preview": "# 2026年3月工作总结报告...",
    "share_link": "http://minio/generated-docs/summary/20260331_2026年3月_工作总结.docx?token=xxx",
    "doc_type": "summary",
    "generated_at": "2026-03-31 17:00:00"
  }
}
```

## Configuration

```yaml
skill:
  name: doc_generation
  
  config:
    # KIMI API 配置
    kimi_config:
      api_key: "${KIMI_API_KEY}"
      base_url: "https://api.moonshot.cn/v1"
      model: "kimi-k2.5"
      temperature: 0.7
      max_tokens: 4000
      
    # MinIO 配置
    minio_config:
      endpoint: "${MINIO_ENDPOINT}"
      access_key: "${MINIO_ACCESS_KEY}"
      secret_key: "${MINIO_SECRET_KEY}"
      bucket: "documents"
      secure: true
      
    # 文档输出配置
    output_dir: "/tmp/doc_generation"
    
    # 分享链接配置
    share_link_expires: 604800  # 7天（秒）
```

## Dependencies

```yaml
dependencies:
  python_packages:
    - python-docx >= 0.8.11
    - aiohttp >= 3.8.0
    
  external_services:
    - KIMI API
    - MinIO Storage
    
  openclaw:
    - BaseSkill
    - KIMITool
    - MinIOTool
```

## Error Handling

| 错误类型 | 描述 | 处理方式 |
|---------|------|---------|
| InvalidDocType | 不支持的文档类型 | 返回参数错误，提示支持的类型 |
| MissingRequiredField | 缺少必需参数 | 返回参数错误，提示缺失字段 |
| KIMIError | KIMI API 调用失败 | 抛出异常，记录日志 |
| MinIOError | MinIO 操作失败 | 抛出异常，尝试返回原始URL |
| PhotoDownloadError | 照片下载失败 | 记录警告，继续生成文档 |
| ParseError | 内容解析失败 | 使用文本解析作为 fallback |

## Performance

- **生成时间**: 平均 3-5 秒
- **文档大小**: 典型 100KB - 2MB（取决于照片数量）
- **并发处理**: 支持 10+ 并发文档生成
- **照片处理**: 每张照片增加约 0.5-1 秒处理时间

## Security

- API 密钥通过环境变量注入，不硬编码
- MinIO 使用预签名 URL，限制访问时间（7天）
- 文档存储在私有 bucket，不公开访问
- 敏感信息（如工作人员姓名）在日志中脱敏

## Changelog

### v1.0.0 (2026-03-20)
- 初始版本发布
- 支持3种文档类型：供电简报、应急指引、工作总结
- 集成 KIMI AI 生成内容
- 支持 Word 文档生成
- 支持照片嵌入
- 支持 Markdown 预览
- 支持预签名分享链接
