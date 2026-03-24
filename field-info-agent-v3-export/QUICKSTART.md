# 快速启动指南

> 🚀 5分钟内启动Field Info Agent v3.0

---

## 步骤1: 准备环境

### 1.1 安装OpenClaw

```bash
# 如果尚未安装OpenClaw
pip install opencode
```

### 1.2 创建工作目录

```bash
mkdir field-info-project
cd field-info-project
```

---

## 步骤2: 初始化文件结构

### 2.1 复制导出包内容

```bash
# 复制模板
cp -r field-info-agent-v3-export/templates ./

# 创建数据目录
mkdir -p field-data/{communities,templates}
cp templates/* field-data/templates/

# 创建索引文件
touch field-data/communities-index.md
touch field-data/search-index.md
```

### 2.2 创建第一个小区

```bash
# 创建小区目录
mkdir -p "field-data/communities/阳光小区/2024-03/{photos,documents}"

# 创建小区档案
cp field-info-agent-v3-export/examples/community-README-example.md \
   "field-data/communities/阳光小区/README.md"
```

---

## 步骤3: 配置OpenClaw

创建 `openclaw.config.yaml`:

```yaml
name: FieldInfoCollector
version: 3.0.0
description: 现场信息收集Agent - 极简版

channels:
  wecom:
    enabled: true
    supported_message_types:
      - text
      - image
      - location

skills:
  station_work_guide:
    enabled: true
    priority: high
    triggers:
      - type: intent
        patterns:
          - "驻点"
          - "去.*社区"
          - "配电房"
          - "开始.*工作"
          
  photo_collection:
    enabled: true
    priority: high
    triggers:
      - type: message_type
        value: "image"
    config:
      base_path: "./field-data"
      photo_subdir: "photos"
      filename_format: "IMG_{timestamp}_{seq}"
      auto_analyze: true
    
  doc_generation:
    enabled: true
    priority: normal
    triggers:
      - type: command
        pattern: "生成.*报告|完成.*采集"
    config:
      data_root: "./field-data"
      template_path: "./field-data/templates"
      output_subdir: "documents"
      
  info_retrieval:
    enabled: true
    priority: normal
    triggers:
      - type: keyword
        patterns:
          - "查询"
          - "搜索"
          - "查找"
          - "历史"
    config:
      data_root: "./field-data"
      index_file: "search-index.md"
      auto_update: true

llm:
  vision_analysis:
    enabled: true
    model: "default"
    prompts:
      power_room: |
        你是电力设备识别专家。请分析这张配电房照片：
        1. 识别设备类型（变压器/高压柜/低压柜/其他）
        2. 描述整体环境（整洁度、照明、通道）
        3. 指出明显的安全隐患
        4. 用一句话总结
        请用中文回复，简洁明了。
        
      transformer: |
        请分析这张变压器照片：
        1. 识别设备型号（如能看到铭牌）
        2. 观察外观状态（清洁度、锈蚀、漏油）
        3. 检查油位（如有油位计）
        4. 一句话总结
        
      general: |
        请描述这张照片的内容，指出主要对象和整体状态。

session:
  storage: memory  # 使用内存存储，无需Redis
  timeout: 7200    # 2小时超时

logging:
  level: info
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 步骤4: 配置Agent角色

创建 `AGENTS.md`:

```markdown
---
description: Field Collector Agent - 极简本地版
type: primary
---

# Field Collector Agent

## 角色定义

**类型**: OpenClaw Agent  
**版本**: 3.0.0  
**架构**: 纯文件系统（零外部依赖）

## 核心能力

1. **驻点工作引导**: 工作流管理和进度追踪
2. **照片采集**: 接收照片、OpenClaw读图、自动标注
3. **文档生成**: Markdown文档自动生成
4. **信息检索**: 全文搜索和跨小区查询

## 数据目录

- 数据根目录: `./field-data`
- 小区目录: `./field-data/communities/{小区名}/`
- 模板目录: `./field-data/templates/`

## 使用示例

```
用户: "我要去阳光小区驻点"
Agent: 读取小区档案 → 创建工作记录 → 引导采集

用户: [发送照片]
Agent: 保存照片 → OpenClaw读图 → 更新记录

用户: "完成采集"
Agent: 生成供电简报 → 更新索引 → 返回文档链接

用户: "查询历史问题"
Agent: 检索索引 → 返回问题列表
```
```

---

## 步骤5: 启动测试

### 5.1 本地测试模式

```bash
# 启动Agent（本地测试）
opencode run --agent field-collector --config openclaw.config.yaml

# 或使用交互模式
opencode chat --agent field-collector
```

### 5.2 测试对话

```
# 测试1: 启动驻点工作
用户: 我要去阳光小区驻点
Agent: [读取README.md] 已准备阳光小区档案...

# 测试2: 照片采集（模拟）
用户: [发送测试图片]
Agent: [保存图片] [调用vision_analysis] 照片已分析...

# 测试3: 文档生成
用户: 完成采集
Agent: [生成Markdown] 文档已生成...

# 测试4: 信息检索
用户: 查询阳光小区的信息
Agent: [检索索引] 阳光小区：500户，2个配电房...
```

---

## 步骤6: 查看生成的文件

```bash
# 查看工作记录
cat field-data/communities/阳光小区/2024-03/work-record.md

# 查看生成的文档
ls -la field-data/communities/阳光小区/2024-03/documents/

# 查看小区索引
cat field-data/communities-index.md
```

---

## 常见问题

### Q1: 照片保存在哪里？

**A**: 照片保存在 `field-data/communities/{小区}/{年月}/photos/` 目录下，命名格式为 `IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg`。

### Q2: 如何查看生成的文档？

**A**: 生成的Markdown文档在 `field-data/communities/{小区}/{年月}/documents/` 目录下，可以使用任何Markdown编辑器打开。

### Q3: 如何添加新的小区？

**A**: 
```bash
mkdir -p "field-data/communities/新小区名/2024-03/{photos,documents}"
touch "field-data/communities/新小区名/README.md"
# 编辑README.md添加小区信息
```

### Q4: 检索功能如何工作？

**A**: 检索功能通过读取 `search-index.md` 文件实现。Agent会自动更新索引，也可以通过发送"更新索引"手动触发。

### Q5: 可以导出为Word吗？

**A**: Markdown可以直接转换为Word。使用pandoc工具：
```bash
pandoc input.md -o output.docx
```

---

## 下一步

1. 查看完整设计方案：`docs/DESIGN-v3-simplified.md`
2. 了解Skill实现：`skills/`
3. 参考示例文件：`examples/`
4. 自定义模板：`templates/`

---

**祝您使用愉快！** 🎉
