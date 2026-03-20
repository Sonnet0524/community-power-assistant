# DocGeneration Skill 使用文档

## 概述

DocGeneration Skill 是一个文档自动生成工具，根据现场采集的数据自动生成专业的电力行业文档。支持三种文档类型：

1. **供电简报 (briefing)** - 日常巡检工作报告
2. **应急指引 (emergency)** - 突发事件处置方案  
3. **工作总结 (summary)** - 周期性工作汇总

## 特性

- 🤖 **AI 驱动**: 集成 KIMI AI 自动生成专业内容
- 📄 **Word 导出**: 自动生成格式规范的 Word 文档
- 📷 **照片嵌入**: 支持现场照片自动嵌入文档
- 👁️ **实时预览**: 生成 Markdown 格式预览
- 🔗 **分享链接**: 提供7天有效期的预签名分享链接
- 🎨 **专业模板**: 使用行业标准的文档模板

## 安装

### 依赖安装

```bash
pip install python-docx>=0.8.11
pip install aiohttp>=3.8.0
```

### 环境配置

设置以下环境变量：

```bash
# KIMI API 配置
export KIMI_API_KEY="your_api_key"
export KIMI_BASE_URL="https://api.moonshot.cn/v1"

# MinIO 配置
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="your_access_key"
export MINIO_SECRET_KEY="your_secret_key"
export MINIO_BUCKET="documents"
```

## 快速开始

### 基本使用

```python
from src.skills.doc_generation import DocGenerationSkill

# 创建 Skill 实例
skill = DocGenerationSkill()

# 生成供电简报
context = {
    "params": {
        "doc_type": "briefing",
        "task_id": "task_001",
        "data": {
            "station": "城北供电所",
            "date": "2026-03-20",
            "staff": "张三",
            "location": "配电室A"
        },
        "photos": [],
        "user_id": "user_001"
    }
}

result = await skill.invoke(context)
print(result.response)
print(f"文档URL: {result.data['document_url']}")
print(f"分享链接: {result.data['share_link']}")
```

## 文档类型详解

### 1. 供电简报 (briefing)

适用于日常巡检、设备检查等工作场景。

**所需数据字段：**

| 字段 | 类型 | 说明 |
|-----|------|------|
| station | string | 供电所名称 |
| date | string | 工作日期 |
| staff | string | 工作人员 |
| location | string | 工作地点 |
| collection_data | string | 采集数据描述 |

**生成的章节：**
- 工作概述
- 现场情况
- 设备状态
- 发现问题
- 整改建议
- 附件（照片）

**示例：**

```python
context = {
    "params": {
        "doc_type": "briefing",
        "task_id": "task_20260320_001",
        "data": {
            "station": "城北供电所",
            "date": "2026-03-20",
            "staff": "张三、李四",
            "location": "工业园区A区配电室",
            "collection_data": """
            1. 变压器温度65℃，运行正常
            2. 开关柜无异常声响
            3. 接地电阻测试：0.8Ω，合格
            4. 电缆头无发热现象
            """
        },
        "photos": [
            "http://minio/photos/transformer_01.jpg",
            "http://minio/photos/switchgear_01.jpg"
        ]
    }
}
```

### 2. 应急指引 (emergency)

适用于突发故障、紧急事件处置场景。

**所需数据字段：**

| 字段 | 类型 | 说明 |
|-----|------|------|
| event_type | string | 事件类型（如：停电、设备故障） |
| location | string | 事件发生地点 |
| time | string | 发生时间 |
| impact | string | 影响范围描述 |
| current_status | string | 当前处理状态 |
| scene_description | string | 现场情况描述 |

**生成的章节：**
- 事件概述
- 影响范围
- 应急措施
- 恢复方案
- 注意事项

**示例：**

```python
context = {
    "params": {
        "doc_type": "emergency",
        "task_id": "emergency_001",
        "data": {
            "event_type": "变压器故障跳闸",
            "location": "商业街配电室",
            "time": "2026-03-20 15:30",
            "impact": "影响商业街200户商户用电，涉及负荷500kW",
            "current_status": "已隔离故障设备，启动备用电源，恢复80%供电",
            "scene_description": "10kV变压器冒烟，绝缘油泄漏，已停电处理"
        },
        "photos": [
            "http://minio/photos/emergency/transformer_damage.jpg"
        ]
    }
}
```

### 3. 工作总结 (summary)

适用于月度、季度、年度工作总结场景。

**所需数据字段：**

| 字段 | 类型 | 说明 |
|-----|------|------|
| period | string | 总结周期 |
| department | string | 所属部门 |
| reporter | string | 汇报人 |
| completed_tasks | string | 完成工作内容 |
| issues | string | 发现问题描述 |
| task_count | int | 完成任务数 |
| issue_count | int | 发现问题数 |
| fix_rate | float | 整改完成率(%) |
| satisfaction | float | 满意度(%) |

**生成的章节：**
- 工作回顾
- 完成情况
- 问题分析
- 改进措施
- 下阶段计划

**示例：**

```python
context = {
    "params": {
        "doc_type": "summary",
        "task_id": "summary_202603",
        "data": {
            "period": "2026年3月",
            "department": "运维检修部",
            "reporter": "王五",
            "completed_tasks": """
            1. 完成巡检任务35次，覆盖率100%
            2. 设备维护保养12次
            3. 故障抢修8次，平均修复时间2小时
            4. 完成春季安全大检查
            """,
            "issues": "发现设备隐患5处，已整改4处，1处正在处理",
            "task_count": 35,
            "issue_count": 5,
            "fix_rate": 80,
            "satisfaction": 92
        }
    }
}
```

## API 参考

### DocGenerationSkill

#### 初始化

```python
skill = DocGenerationSkill(config: Optional[Dict] = None)
```

**参数：**
- `config`: 配置字典
  - `kimi_config`: KIMI API 配置
  - `minio_config`: MinIO 配置
  - `output_dir`: 临时文件输出目录

#### invoke

```python
async def invoke(self, context: SkillContext) -> SkillResult
```

执行文档生成。

**参数：**
- `context.params.doc_type`: 文档类型
- `context.params.task_id`: 任务ID
- `context.params.data`: 任务数据
- `context.params.photos`: 照片URL列表
- `context.params.user_id`: 用户ID

**返回：**
- `response`: 结果消息
- `data.document_url`: 文档URL
- `data.preview`: Markdown预览
- `data.share_link`: 分享链接

#### validate_params

```python
async def validate_params(self, params: dict) -> tuple[bool, str]
```

验证参数是否合法。

#### get_supported_types

```python
async def get_supported_types(self) -> List[Dict]
```

获取支持的文档类型列表。

## 配置文件

### 完整配置示例

```yaml
# config/doc_generation.yaml
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
      timeout: 30
      
    # MinIO 配置
    minio_config:
      endpoint: "${MINIO_ENDPOINT}"
      access_key: "${MINIO_ACCESS_KEY}"
      secret_key: "${MINIO_SECRET_KEY}"
      bucket: "documents"
      secure: true
      region: "us-east-1"
      
    # 输出配置
    output_dir: "/tmp/doc_generation"
    
    # 文档模板配置
    templates:
      briefing:
        file_name_pattern: "{date}_{station}_供电简报.docx"
        max_photos: 20
      emergency:
        file_name_pattern: "{date}_{location}_应急指引.docx"
        max_photos: 10
      summary:
        file_name_pattern: "{date}_{period}_工作总结.docx"
        max_photos: 0
```

## 常见问题

### Q: 如何处理 KIMI API 调用失败？

A: 系统会自动重试3次，如果仍然失败会抛出异常。建议：
1. 检查 API 密钥是否正确
2. 检查网络连接
3. 查看日志获取详细错误信息

### Q: 照片无法下载怎么办？

A: 照片下载失败会记录警告，但不会影响文档生成。文档中对应位置会显示"[照片加载失败]"。

### Q: 分享链接过期了怎么办？

A: 默认分享链接有效期为7天。过期后需要重新生成文档或联系管理员延长有效期。

### Q: 如何自定义文档模板？

A: 目前模板是硬编码的。如需自定义，可以：
1. 修改 `DOC_TEMPLATES` 配置
2. 继承 `DocGenerationSkill` 并重写相关方法

## 故障排除

### 问题：文档生成超时

**原因：**
- KIMI API 响应慢
- 照片数量过多

**解决方案：**
1. 减少照片数量（建议每份文档不超过20张）
2. 检查 KIMI API 状态
3. 增加超时时间配置

### 问题：Word 文档格式错乱

**原因：**
- python-docx 版本不兼容
- 特殊字符未转义

**解决方案：**
1. 升级 python-docx 到最新版本
2. 检查输入数据中是否包含特殊字符

### 问题：分享链接无法访问

**原因：**
- MinIO 配置错误
- Bucket 权限问题

**解决方案：**
1. 检查 MinIO 连接配置
2. 确认 bucket 存在且有写入权限
3. 检查预签名 URL 生成逻辑

## 性能优化建议

1. **照片压缩**: 上传前压缩照片，减少网络传输时间
2. **并发控制**: 单实例并发生成建议不超过10个文档
3. **缓存策略**: 相同数据可考虑缓存生成结果
4. **异步处理**: 大文档建议使用异步队列处理

## 安全建议

1. **API 密钥**: 使用环境变量或密钥管理服务，不要硬编码
2. **文件权限**: 确保临时文件目录权限正确（建议 700）
3. **数据脱敏**: 日志中脱敏处理敏感信息
4. **访问控制**: MinIO bucket 设置为私有，使用预签名 URL

## 更新日志

### v1.0.0 (2026-03-20)
- 初始版本发布
- 支持3种文档类型
- 集成 KIMI AI
- 支持 Word 导出

## 支持与反馈

如有问题或建议，请联系：
- **维护团队**: Field Core Team
- **邮箱**: field-core@example.com
- **文档**: [项目 Wiki](https://wiki.example.com/doc-generation)
