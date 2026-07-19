# Field Info Agent - 极简版设计方案（v3.0）

> 🎯 基于纯文件系统的现场信息收集方案（零外部依赖）

**版本**: 3.0.0  
**日期**: 2024-03-24  
**架构**: 纯本地文件系统（Markdown + 文件夹）

---

## 一、方案概述

### 1.1 设计目标

**极简原则**:
- ✅ 零外部依赖（无数据库、无云存储、无外部API）
- ✅ 纯Markdown文件管理
- ✅ 一个小区 = 一个文件夹
- ✅ 使用OpenClaw原生读图能力
- ✅ 内置信息检索能力

### 1.2 与之前版本对比

| 维度 | v2.x（完整版） | v3.0（极简版） |
|------|---------------|---------------|
| **存储** | PostgreSQL + MinIO | 纯文件系统 |
| **文档** | Word (.docx) | Markdown (.md) |
| **AI分析** | KIMI多模态API | OpenClaw读图 |
| **检索** | SQL查询 | 文件索引 |
| **依赖** | 多（数据库、对象存储、AI服务） | 零 |
| **成本** | ¥800/月 | 仅需存储空间 |
| **复杂度** | 高 | 极低 |
| **适用** | 生产环境 | 原型/MVP/个人使用 |

---

## 二、存储架构

### 2.1 目录结构

```
field-data/                                    # 数据根目录
├── 📄 communities-index.md                    # 小区总索引
├── 📄 search-index.md                         # 检索索引
├── 📁 templates/                              # 文档模板
│   ├── 📄 work-record-template.md
│   ├── 📄 power-briefing-template.md
│   └── 📄 equipment-list-template.md
│
└── 📁 communities/                            # 小区数据
    ├── 📁 阳光小区/
    │   ├── 📄 README.md                       # 小区档案
    │   ├── 📁 2024-03/                        # 按月组织
    │   │   ├── 📄 work-record.md              # 工作记录
    │   │   ├── 📁 photos/                     # 照片目录
    │   │   │   ├── 📸 IMG_20240317_093015.jpg
    │   │   │   ├── 📸 IMG_20240317_093052.jpg
    │   │   │   └── 📸 IMG_20240317_093118.jpg
    │   │   └── 📁 documents/                  # 生成文档
    │   │       ├── 📄 20240317_work-record.md
    │   │       └── 📄 20240317_power-briefing.md
    │   └── 📁 2024-02/
    │       └── ...
    │
    ├── 📁 锦绣花园/
    │   └── ...
    │
    └── 📁 金色家园/
        └── ...
```

### 2.2 索引文件设计

#### communities-index.md（小区总索引）

```markdown
# 小区信息索引

**最后更新**: 2024-03-17 14:30

## 小区列表

| 小区名称 | 地址 | 总户数 | 配电房数 | 变压器数 | 最后驻点 | 驻点次数 |
|---------|------|--------|----------|----------|----------|----------|
| 阳光小区 | 武侯区xx路xx号 | 500 | 2 | 4 | 2024-03-17 | 3 |
| 锦绣花园 | 武侯区yy路yy号 | 800 | 3 | 6 | 2024-03-15 | 5 |
| 金色家园 | 武侯区zz路zz号 | 300 | 1 | 2 | 2024-03-10 | 2 |

## 敏感客户清单

### 阳光小区
- 3-2-501 王大爷（70岁，独居）139****1234
- 4-1-302 张女士（孕妇）137****5678

## 设备问题跟踪

| 日期 | 小区 | 问题描述 | 状态 |
|------|------|----------|------|
| 2024-03-17 | 阳光小区 | 2#变压器油位偏低 | 待复查 |
```

#### 小区README.md（单个小区档案）

```markdown
# 阳光小区 - 信息档案

**基本信息**
- 地址: 武侯区xx路xx号
- 总户数: 500户
- 配电房: 2个
- 变压器: 4台
- 物业: xx物业，李经理 138****8888

## 配电房信息

### 1号配电房（3号楼地下室）
- 位置: 进门左转，靠近电梯间
- 变压器: 2台
  - 1#变: SCB11-500/10，运行正常
  - 2#变: SCB11-630/10，⚠️ 油位偏低（2024-03-17发现）
- 照片: [查看](./2024-03/photos/)

### 2号配电房（5号楼一楼）
- 位置: 5号楼东侧
- 变压器: 2台，一切正常

## 历史驻点记录

| 日期 | 工作人员 | 工作类型 | 发现问题 | 文档 |
|------|----------|----------|----------|------|
| 2024-03-17 | 张三 | 配电房检查 | 油位低 | [记录](./2024-03/work-record.md) |
| 2024-02-15 | 李四 | 客户走访 | 无 | [记录](./2024-02/work-record.md) |

## 敏感客户
- 王大爷 3-2-501（独居老人，每月回访）
- 张女士 4-1-302（孕妇，已生产）

## 应急信息
- 进入点: 小区东门（宽4米）
- 停放点: 3号楼前广场
- 接入点: 1号配电房
- 电缆: YJV22-3×95，需50米
```

---

## 三、核心Skills

### 3.1 Skill清单

| Skill ID | 名称 | 功能 | 优先级 |
|----------|------|------|--------|
| station-work-guide | 驻点工作引导 | 工作流引导、进度管理 | P0 |
| photo-collection | 照片采集 | 接收照片、OpenClaw读图、标注 | P0 |
| doc-generation | 文档生成 | Markdown文档自动生成 | P1 |
| **info-retrieval** | **信息检索** | **全文检索、跨小区查询** | **P1** |

### 3.2 照片采集（OpenClaw读图）

**处理流程**:
```
用户发送照片
    ↓
保存到 ./photos/IMG_{timestamp}.jpg
    ↓
使用OpenClaw读图分析（无需外部API）
    ↓
生成描述文本
    ↓
更新work-record.md（添加照片引用和AI描述）
```

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

### 3.3 信息检索（新增核心能力）⭐

**检索范围**:
- 小区基本信息
- 历史工作记录
- 设备台账
- 问题记录
- 客户信息

**检索示例**:
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

**检索索引**（search-index.md）:
```markdown
# 检索索引

## 设备索引
| 小区 | 设备类型 | 型号 | 位置 | 状态 |
|------|----------|------|------|------|
| 阳光小区 | 变压器 | SCB11-500/10 | 1号配电房 | 正常 |
| 阳光小区 | 变压器 | SCB11-630/10 | 1号配电房 | 油位低 |

## 问题索引
| 日期 | 小区 | 问题 | 严重程度 | 状态 |
|------|------|------|----------|------|
| 2024-03-17 | 阳光小区 | 变压器油位低 | 一般 | 待复查 |
```

---

## 四、工作流程

### 4.1 完整驻点流程

```
用户: "我要去阳光小区驻点"
    ↓
Agent读取communities-index.md
"阳光小区：武侯区xx路xx号，500户，上次驻点2024-02-15"
    ↓
创建文件夹 阳光小区/2024-03-17/
初始化work-record.md
    ↓
Agent: "已准备阳光小区档案
       建议关注：2#变压器油位、王大爷回访
       工作清单已生成，请发送'开始'"
    ↓
用户: "开始配电房检查"
    ↓
Agent引导采集，每张照片：
  - 保存到photos/
  - OpenClaw读图分析
  - 更新work-record.md
    ↓
用户: "完成采集"
    ↓
Agent: 生成供电简报、更新索引
"✅ 工作完成！文档已生成"
```

### 4.2 状态流转

```
IDLE → PREPARING → COLLECTING → COMPLETED
         ↑___________________________|
         
COLLECTING子状态:
  ├── POWER_ROOM（配电房检查）
  ├── CUSTOMER_VISIT（客户走访）
  └── EMERGENCY（应急采集）
```

---

## 五、技术实现

### 5.1 文件操作API（OpenClaw）

```typescript
// 读取文件
const content = await tools.read_file({
  file_path: "./field-data/communities/阳光小区/README.md"
});

// 写入文件
await tools.write_file({
  file_path: "./field-data/communities/阳光小区/2024-03/work-record.md",
  content: markdownContent
});

// 读图分析
const analysis = await tools.vision_analyze({
  image_path: "./field-data/communities/阳光小区/2024-03/photos/IMG_001.jpg",
  prompt: "分析配电房照片"
});
```

### 5.2 索引更新机制

```python
def update_search_index():
    """定期更新检索索引"""
    index = {
        "communities": [],
        "equipment": [],
        "issues": [],
        "customers": []
    }
    
    for community in list_communities():
        readme = read_file(f"{community}/README.md")
        index["communities"].append(parse_community(readme))
        index["equipment"].extend(parse_equipment(readme))
        index["issues"].extend(parse_issues(readme))
        index["customers"].extend(parse_customers(readme))
    
    write_file("./field-data/search-index.md", generate_index_md(index))
```

---

## 六、优势与限制

### 6.1 核心优势

| 优势 | 说明 |
|------|------|
| **零依赖** | 无需数据库、云存储、外部API |
| **透明** | 所有数据可读Markdown，无黑盒 |
| **可迁移** | 复制文件夹即可迁移全部数据 |
| **版本控制** | Git直接管理，变更可追溯 |
| **成本低** | 仅需文件存储空间 |
| **快速启动** | 无需部署基础设施 |
| **离线可用** | 不依赖网络（除企业微信） |

### 6.2 已知限制

| 限制 | 缓解措施 |
|------|----------|
| **检索性能** | 定期生成索引文件，缓存常用查询 |
| **并发写入** | 按日期分文件夹，减少冲突 |
| **数据分析** | 定期导出到Excel做复杂分析 |
| **图片分析** | 使用OpenClaw基础能力，人工确认关键信息 |
| **数据量** | 适合中小型项目（<1000条记录） |

---

## 七、快速开始

### 7.1 初始化

```bash
# 创建目录结构
mkdir -p field-data/{communities,templates}
touch field-data/communities-index.md
touch field-data/search-index.md

# 创建模板
cp templates/*.md field-data/templates/
```

### 7.2 添加小区

```bash
mkdir -p "field-data/communities/阳光小区/2024-03/{photos,documents}"
touch "field-data/communities/阳光小区/README.md"
```

### 7.3 启动Agent

```yaml
# openclaw.config.yaml
name: FieldInfoCollector
version: 3.0.0

channels:
  wecom:
    enabled: true

skills:
  station_work_guide:
    enabled: true
  photo_collection:
    enabled: true
  doc_generation:
    enabled: true
  info_retrieval:
    enabled: true

config:
  data_root: "./field-data"
```

---

## 八、迁移路径

### 从v2.x迁移到v3.0

```python
# 数据迁移脚本
def migrate_v2_to_v3():
    """从PostgreSQL+MinIO迁移到文件系统"""
    
    # 1. 导出PostgreSQL数据
    records = query_postgres("SELECT * FROM station_work_records")
    
    # 2. 创建文件结构
    for record in records:
        community_dir = f"./field-data/communities/{record.community}"
        ensure_dir(community_dir)
        
        # 3. 生成work-record.md
        work_record_md = convert_to_markdown(record)
        write_file(f"{community_dir}/{record.date[:7]}/work-record.md", work_record_md)
        
        # 4. 复制照片
        for photo in record.photos:
            copy_from_minio(photo.minio_path, f"{community_dir}/{record.date[:7]}/photos/")
    
    # 5. 生成索引
    generate_all_indices()
```

---

## 九、文档清单

| 文档 | 路径 | 说明 |
|------|------|------|
| Agent定义 | `AGENTS-v3-simplified.md` | 极简版Agent角色定义 |
| 照片采集Skill | `skills/photo-collection/SKILL.md` | OpenClaw读图 |
| 文档生成Skill | `skills/doc-generation/SKILL.md` | Markdown生成 |
| 信息检索Skill | `skills/info-retrieval/SKILL.md` | 全文检索 |
| 本方案 | `DESIGN-v3-simplified.md` | 整体设计说明 |

---

## 十、总结

**极简版v3.0适合场景**:
- ✅ 快速原型验证（MVP）
- ✅ 个人/小团队使用
- ✅ 成本敏感项目
- ✅ 离线环境
- ✅ 学习/演示用途

**何时升级到v2.x**:
- 数据量超过1000条
- 需要多用户并发
- 复杂数据分析需求
- 正式生产环境
- 需要Word正式文档

---

**版本**: 3.0.0 - 极简版  
**最后更新**: 2024-03-24  
**状态**: 设计完成，可开发
