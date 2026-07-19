# Field Info Agent v3.0 - 极简版导出包

> 🎯 基于纯文件系统的现场信息收集方案（零外部依赖）

**版本**: 3.0.0  
**日期**: 2024-03-24  
**架构**: 纯本地文件系统（Markdown + 文件夹）

---

## 📦 包内容说明

```
field-info-agent-v3-export/
├── README.md                          # 本说明文件
├── agent/
│   └── AGENTS-v3-simplified.md        # Agent角色定义
├── skills/
│   ├── photo-collection-SKILL.md      # 照片采集Skill（OpenClaw读图）
│   ├── doc-generation-SKILL.md        # 文档生成Skill（Markdown）
│   └── info-retrieval-SKILL.md        # 信息检索Skill（全文搜索）
├── templates/
│   ├── work-record-template.md        # 工作记录模板
│   └── power-briefing-template.md     # 供电简报模板
├── examples/
│   ├── community-README-example.md    # 小区档案示例
│   ├── work-record-example.md         # 工作记录示例
│   └── communities-index-example.md   # 小区索引示例
└── docs/
    └── DESIGN-v3-simplified.md        # 完整设计方案
```

---

## 🎯 核心特点

### 极简架构
- ✅ **零外部依赖**：无需数据库、云存储、外部API
- ✅ **纯文件存储**：一个小区 = 一个文件夹
- ✅ **Markdown管理**：所有数据都是可读的Markdown文件
- ✅ **OpenClaw原生**：使用内置读图能力，无需KIMI

### 新增能力
- ⭐ **信息检索**：全文搜索、跨小区查询
- ⭐ **Markdown文档**：自动生成工作记录和供电简报
- ⭐ **Git友好**：天然支持版本控制

---

## 🚀 快速开始

### 1. 目录结构初始化

```bash
# 创建数据根目录
mkdir -p field-data/{communities,templates}
touch field-data/communities-index.md
touch field-data/search-index.md

# 复制模板
cp templates/*.md field-data/templates/
```

### 2. 添加小区

```bash
# 创建小区目录
mkdir -p "field-data/communities/阳光小区/2024-03/{photos,documents}"
touch "field-data/communities/阳光小区/README.md"
```

### 3. 配置OpenClaw

```yaml
# openclaw.config.yaml
name: FieldInfoCollector
version: 3.0.0

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
    
  photo_collection:
    enabled: true
    priority: high
    
  doc_generation:
    enabled: true
    priority: normal
    
  info_retrieval:
    enabled: true
    priority: normal

config:
  data_root: "./field-data"
  template_path: "./field-data/templates"
```

### 4. 启动使用

```bash
# 启动OpenClaw Agent
opencode run --agent field-collector
```

---

## 📁 文件存储规范

### 目录结构

```
field-data/
├── 📄 communities-index.md           # 小区总索引
├── 📄 search-index.md                # 检索索引
├── 📁 templates/                     # 文档模板
│   ├── work-record-template.md
│   └── power-briefing-template.md
│
└── 📁 communities/
    └── 📁 {小区名}/
        ├── 📄 README.md              # 小区档案
        ├── 📁 {YYYY-MM}/             # 按月组织
        │   ├── 📄 work-record.md     # 工作记录
        │   ├── 📁 photos/            # 照片目录
        │   │   └── 📸 IMG_{timestamp}.jpg
        │   └── 📁 documents/         # 生成文档
        │       └── 📄 {date}_power-briefing.md
        └── 📁 equipment-list.md      # 设备台账
```

### 命名规范

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| **照片** | `IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg` | `IMG_20240317_093015_01.jpg` |
| **工作记录** | `work-record.md` | `work-record.md` |
| **供电简报** | `{YYYYMMDD}_power-briefing.md` | `20240317_power-briefing.md` |
| **小区目录** | `{小区名}/` | `阳光小区/` |
| **月度目录** | `{YYYY-MM}/` | `2024-03/` |

---

## 🔧 核心功能

### 1. 驻点工作引导

**触发**: 用户发送"我要去阳光小区驻点"

**流程**:
1. 读取 `communities-index.md` 获取小区信息
2. 创建月度目录结构
3. 初始化 `work-record.md`
4. 引导用户完成采集

### 2. 照片采集

**触发**: 用户发送照片

**流程**:
1. 保存到 `./photos/IMG_{timestamp}.jpg`
2. 使用OpenClaw读图分析
3. 更新 `work-record.md`（添加照片引用和描述）

**OpenClaw配置**:
```yaml
llm:
  vision_analysis:
    enabled: true
    prompts:
      power_room: |
        分析这张配电房照片：
        1. 识别设备类型和数量
        2. 描述整体环境
        3. 指出安全隐患
        4. 一句话总结
```

### 3. 文档生成

**触发**: 用户发送"完成采集"或"生成简报"

**流程**:
1. 读取工作记录数据
2. 填充模板变量
3. 生成Markdown文档
4. 保存到 `documents/` 目录
5. 更新小区README索引

### 4. 信息检索

**示例查询**:
```
用户: "查询阳光小区的变压器"
→ 检索README.md和work-record.md
→ 返回: 4台变压器详细信息

用户: "王大爷住在哪？"
→ 检索所有README.md中的客户信息
→ 返回: 阳光小区 3-2-501

用户: "上个月发现的问题"
→ 检索最近30天的work-record.md
→ 返回: 问题列表
```

---

## 📖 文档说明

### Agent定义
**文件**: `agent/AGENTS-v3-simplified.md`

定义了Field Collector Agent的角色、职责、工作流程和模块边界。

### Skill文档

#### 照片采集
**文件**: `skills/photo-collection-SKILL.md`

- 照片接收与保存
- OpenClaw读图配置
- 照片命名与标注规范

#### 文档生成
**文件**: `skills/doc-generation-SKILL.md`

- Markdown文档生成
- 模板系统
- 历史对比功能

#### 信息检索
**文件**: `skills/info-retrieval-SKILL.md`

- 全文检索实现
- 检索索引管理
- 多类型查询支持

### 设计方案
**文件**: `docs/DESIGN-v3-simplified.md`

完整的架构设计、数据模型、流程图和配置说明。

---

## 📝 示例文件

### 小区档案示例
**文件**: `examples/community-README-example.md`

展示了一个完整的小区README.md应该包含的内容：
- 基本信息
- 配电房信息
- 历史驻点记录
- 敏感客户清单
- 设备台账
- 问题跟踪
- 应急信息
- 文档索引

### 工作记录示例
**文件**: `examples/work-record-example.md`

展示了一次完整的驻点工作记录：
- 基本信息
- 配电房检查详情
- 客户走访记录
- 照片采集记录
- 工作总结

### 小区索引示例
**文件**: `examples/communities-index-example.md`

展示了小区总索引的格式：
- 小区列表
- 敏感客户总览
- 设备问题跟踪
- 近期工作计划
- 统计信息

---

## 🔍 与v2.x版本对比

| 维度 | v2.x（完整版） | v3.0（极简版） |
|------|---------------|---------------|
| **存储** | PostgreSQL + MinIO | 纯文件系统 |
| **文档** | Word (.docx) | Markdown (.md) |
| **AI分析** | KIMI多模态API | OpenClaw读图 |
| **检索** | SQL查询 | 文件索引 |
| **依赖** | 多 | **零** |
| **成本** | ¥800/月 | **仅需磁盘** |
| **复杂度** | 高 | **极低** |
| **适用** | 生产环境 | 原型/MVP/个人使用 |

---

## ⚠️ 限制说明

| 限制 | 说明 | 缓解措施 |
|------|------|----------|
| **检索性能** | 大量数据时搜索慢 | 定期生成索引文件 |
| **并发写入** | 文件锁机制简单 | 按日期分文件夹减少冲突 |
| **数据分析** | 无法进行复杂统计 | 定期导出到Excel分析 |
| **图片分析** | 依赖OpenClaw基础能力 | 人工确认关键信息 |
| **数据量** | 适合中小型项目（<1000条记录） | 数据量大时升级到v2.x |

---

## 🔄 升级路径

### v3.0 → v2.x

当项目需要以下能力时，可平滑升级到完整版：
- 数据量超过1000条
- 多用户并发写入
- 复杂数据分析需求
- 正式生产环境
- 需要Word正式文档

**迁移脚本**:
```python
# 导出v3.0数据到v2.x
def migrate_v3_to_v2():
    # 1. 读取所有Markdown文件
    # 2. 解析数据
    # 3. 导入PostgreSQL
    # 4. 复制照片到MinIO
    # 5. 生成Word文档
    pass
```

---

## 🤝 贡献与反馈

如有问题或建议，请：
1. 查看完整设计方案：`docs/DESIGN-v3-simplified.md`
2. 参考示例文件：`examples/`
3. 提交Issue或PR

---

## 📄 许可证

MIT License

---

**版本**: 3.0.0 - 极简版  
**最后更新**: 2024-03-24  
**维护者**: PM Agent
