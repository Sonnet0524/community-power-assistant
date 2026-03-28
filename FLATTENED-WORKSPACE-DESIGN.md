# 扁平化Workspace架构设计（效率优先）

> ⚡ 基于OpenClaw，但优化文件结构以减少跳转，提升开发效率

**设计原则**:
1. **单文件优先**: 核心逻辑集中在AGENTS.md，减少跨文件跳转
2. **AGENTS即核心**: AGENTS.md成为"唯一真相源"，可接受较长篇幅
3. **Skills轻量可选**: Skills目录极简，甚至逻辑直接内联在AGENTS中
4. **基于-dev版本**: 在workspace-field-worker-dev基础上重构

---

## 一、效率问题分析

### 1.1 当前架构的跳转问题

**传统OpenClaw风格（多文件跳转）**:
```
AGENTS.md (简配) 
    → skills/photo-collection/SKILL.md (详细逻辑)
        → 路径构造章节
        → 错误处理章节
    → skills/doc-generation/SKILL.md
    → rules/storage-rules.md
    → 频繁跳转，效率低
```

**问题**:
- 修改一个功能需要打开3-4个文件
- 上下文分散，容易遗漏
- 开发时频繁切换文件

### 1.2 扁平化架构（减少跳转）

**新架构（AGENTS为核心长文件）**:
```
AGENTS.md (长文件，包含所有)
    ├── ## Agent Identity
    ├── ## Session Management (数据隔离逻辑)
    ├── ## Skill: Photo Collection (完整逻辑，修复01号Bug)
    ├── ## Skill: Doc Generation (完整逻辑，修复07号Bug)
    ├── ## Tools Configuration
    └── ## Data Rules (存储规范，修复09号)
    
内部跳转: 仅通过Markdown Header锚点跳转，不离开文件
```

**优势**:
- 一个文件看到全部逻辑
- 修改功能只需改一处
- 开发效率高

---

## 二、扁平化架构设计

### 2.1 整体结构

```
workspace-field-worker-dev/              # 基于-dev版本
│
├── 📄 AGENTS.md                         # ⭐ 核心长文件（500-800行，包含所有）
│   ├── YAML frontmatter (OpenClaw标准)
│   │   ├── name, emoji, description
│   │   ├── skills声明 (引用内部章节)
│   │   └── tools声明
│   │
│   └── Markdown正文 (长内容，分章节)
│       ├── # 身份与角色
│       ├── # Session管理 (解决03号数据隔离)
│       ├── # Skill: Grid Field Work (现场工作引导)
│       ├── # Skill: Photo Collection (照片采集，解决01号路径Bug)
│       ├── # Skill: Doc Generation (文档生成，解决07号引用Bug)
│       ├── # Skill: Info Retrieval (信息检索)
│       ├── # Tools配置
│       ├── # 数据存储规则 (解决09号权限)
│       └── # 红线与边界
│
├── 🧩 skills/                            # ⭐ 极简Skills目录（可选，甚至可删除）
│   ├── photo-collection/
│   │   └── SKILL.md                      # 仅trigger声明，逻辑在AGENTS
│   ├── doc-generation/
│   │   └── SKILL.md
│   └── ...                               # 其他skill同理
│
└── 🗂️ field-data/                        # 数据目录（保持不变）
    ├── communities-index.md
    └── communities/
```

### 2.2 AGENTS.md 长文件结构（核心）

**文件长度**: 500-800行（可接受）  
**组织方式**: 大章节（##）+ 小章节（###）

```markdown
---
# YAML frontmatter (OpenClaw标准)
name: wuhou-field-worker
emoji: 🔌
description: |
  武侯供电中心客户经理AI助手...

type: openclaw-agent
version: "1.1.0"

metadata:
  openclaw:
    channels:
      - wecom
    
    # ⭐ Skills声明：引用AGENTS.md内部章节，不是外部文件
    skills:
      - name: grid-field-work
        section: "Skill: Grid Field Work"    # 指向AGENTS.md内章节
        enabled: true
        
      - name: photo-collection
        section: "Skill: Photo Collection"   # 指向AGENTS.md内章节
        enabled: true
        
      - name: doc-generation
        section: "Skill: Doc Generation"
        enabled: true
        
      - name: info-retrieval
        section: "Skill: Info Retrieval"
        enabled: true
    
    # Tools声明
    tools:
      - name: file_system
        type: native
      - name: kimi-vision
        type: api
      - name: baidu-map
        type: api

---

# AGENTS.md 正文（长文件开始）

## 身份与角色

你是**武侯供电中心客户经理AI助手**...

## Session管理（解决03号数据隔离）

### Session变量定义
- `current_community`: 当前工作的小区名称
- `current_month_dir`: 当前工作的月份目录路径
- `work_start_time`: 本次工作开始时间

### 小区切换流程
用户说"我要去XX小区"时：
1. 保存当前工作（如有）
2. 设置 `current_community = "XX小区"`
3. 设置 `current_month_dir = "field-data/communities/XX小区/YYYY-MM/"`
4. 读取新小区README.md

### 数据隔离规则
**所有文件写入前必须检查**：
- 路径是否包含 `current_community`？
- 路径是否以 `current_month_dir` 开头？
- 如果不符合，拒绝写入并提示错误

## Skill: Photo Collection（解决01号路径Bug）

### 触发条件
- message_type: image
- session.state: collecting

### 路径构造逻辑（⭐ 核心修复）

**构造函数**（必须在AGENTS中明确写出）：
```javascript
function constructPhotoPath(community, date) {
  // 1. 提取月份（不是日期！）
  const month = date.toISOString().slice(0, 7); // "2026-03"
  
  // 2. 构造标准路径
  const path = `field-data/communities/${community}/${month}/photos/`;
  
  // 3. 自动创建目录
  ensureDir(path);
  
  return path;
}
```

**路径规范**：
- ✅ 正确: `field-data/communities/{小区}/2026-03/photos/`
- ❌ 错误: `field-data/communities/{小区}/photos/` （缺少月份）
- ❌ 错误: `field-data/communities/{小区}/2026-03-26/photos/` （日期目录）

### 执行流程

1. **接收照片**
2. **获取上下文**：从session读取 `current_community`
3. **构造路径**：调用 `constructPhotoPath()`
4. **生成文件名**：`IMG_${YYYYMMDD}_${HHMMSS}_${SEQ}.jpg`
5. **保存文件**：写入photos目录
6. **验证存在性**：检查文件是否成功保存
7. **AI分析**：调用Kimi分析照片
8. **更新记录**：写入work-record.md
9. **返回确认**

### 错误处理

| 错误 | 处理 | 用户提示 |
|------|------|----------|
| 路径错误 | 自动修正 | "照片已保存，路径已规范为：{正确路径}" |
| 保存失败 | 重试3次 | "保存失败，请重试" |
| AI失败 | 保存照片，人工标注 | "照片已保存，请手动添加描述" |

## Skill: Doc Generation（解决07号文件名引用Bug）

### 触发条件
- command: "完成采集" / "生成简报" / "收工"

### 照片引用规则（⭐ 核心修复）

**生成文档前必须执行**：
1. **列出实际照片**：`ls field-data/communities/{小区}/{月份}/photos/`
2. **只引用存在的文件**：禁止使用猜测/编造的文件名
3. **完整文件名匹配**：必须使用`ls`返回的完整文件名

**禁止行为**：
- ❌ 禁止：`![photo](IMG_001.jpg)` （序号猜测）
- ❌ 禁止：`![photo]({timestamp}.jpg)` （时间戳编造）
- ✅ 正确：`![photo](IMG_20260328_143022_01.jpg)` （实际文件名）

### 生成流程

1. **收集数据**：读取work-record.md
2. **列出照片**：执行`ls`获取实际文件名列表
3. **验证引用**：检查文档中所有`![](...)`是否存在于列表
4. **修正错误**：删除不存在的引用，或替换为正确文件名
5. **生成文档**：基于模板填充
6. **二次校验**：生成的文档中所有图片链接都可访问

## Skill: Grid Field Work

### 驻点工作主流程

用户说"我要去XX小区驻点"：
1. 读取小区档案
2. **文字确认小区名**（避免同音字）
3. **文字确认工作人员姓名**
4. 发送5项检查清单
5. 逐项引导完成

### 5项采集清单

1. 小区基本情况 + 大门照片
2. 进网入格（公示栏照片）
3. 供配电方案（手绘供电图）
4. 应急保电方案（发电车接入）
5. 用电检查隐患台账（低配室/竖井）

## Skill: Info Retrieval

### 查询类型

- "阳光小区的变压器信息" → 检索小区README.md
- "王大爷住哪" → 检索敏感客户清单
- "上个月发现的问题" → 检索近期work-record.md

## Tools配置

### File System

**允许的路径**：
- `field-data/communities/**`
- `field-data/templates/**`

**禁止的路径**：
- `../**` （上级目录）
- `/**` （系统根目录）

### Kimi Vision

**用途**：照片AI分析
**模型**：kimi-v1
**Prompt**：根据场景切换（配电房/变压器/通用）

### Baidu Map

**用途**：位置服务、导航
**API Key**：${BAIDU_MAP_API_KEY}

## 数据存储规则（解决09号权限问题）

### 目录结构

```
field-data/
├── communities-index.md              # 小区总索引
├── search-index.md                   # 检索索引
├── templates/                        # 文档模板
└── communities/
    └── {小区名}/
        ├── README.md                 # 小区档案
        └── {YYYY-MM}/                # 月份目录（强制）
            ├── work-record.md        # 工作记录
            ├── photos/               # 照片
            └── documents/            # 生成文档
```

### 强制规范

1. **必须使用月份目录**：`{YYYY-MM}/`，禁止`{YYYY-MM-DD}/`
2. **照片必须放photos子目录**：禁止放根目录
3. **命名规范**：
   - 照片：`IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg`
   - 文档：`{YYYYMMDD}_power-briefing.md`

### 权限规则（系统级保护）

**只读文件**（OpenClaw权限控制）：
- `AGENTS.md` - 核心配置，不可修改
- `skills/**/SKILL.md` - Skill定义，不可修改

**可写文件**：
- `field-data/**` - 数据文件，可读写

**红线**：
- 禁止修改AGENTS.md中的路径规范
- 禁止在非数据目录创建文件

## 红线与边界

### 隐私保护

- 不主动暴露用户身份信息
- 工作档案概览匿名化
- 待办事项不关联具体人员

### 服务范围

**只回答**：供电现场工作相关问题
**不回答**：编程、医疗、法律、闲聊

### 字段分级（解决02号改进）

**P0级（必填，阻断流程）**：
- 小区名称、工作人员姓名、地址、户数、配电房数量

**P1级（重要，提醒但不阻断）**：
- 物业信息、敏感客户、竖井记录

**P2级（选填）**：
- 商业户数、充电桩
```

### 2.3 Skills目录（极简可选）

**方案A: 完全扁平化（推荐）**
```
skills/                              # 可选，甚至可删除
# 空目录或不存在
# 所有逻辑在AGENTS.md中
```

**方案B: 保留极简Skills**
```
skills/
├── photo-collection/
│   └── SKILL.md                      # 仅声明，内容："见AGENTS.md ## Skill: Photo Collection"
└── ...                               # 其他skill同理
```

**推荐方案A**：完全依赖AGENTS.md，最扁平。

---

## 三、10个改进的扁平化解决方案

| 问题 | 传统方案 | 扁平化方案 | 位置 |
|------|---------|-----------|------|
| **01 照片路径** | skills/photo-collection/SKILL.md 详细逻辑 | AGENTS.md `## Skill: Photo Collection` 章节，内含constructPhotoPath函数 | AGENTS.md 内 |
| **03 数据隔离** | rules/data-isolation.md | AGENTS.md `## Session管理` 章节 | AGENTS.md 内 |
| **07 文件名引用** | skills/doc-generation/SKILL.md | AGENTS.md `## Skill: Doc Generation` 章节，内含验证逻辑 | AGENTS.md 内 |
| **08 Skill重构** | 拆分多个Skill文件 | 合并到AGENTS.md各章节，或保留极简Skills目录 | AGENTS.md 内 |
| **09 权限控制** | rules/permission-rules.md + 系统权限 | AGENTS.md `## 数据存储规则` 章节 + OpenClaw permissions | AGENTS.md 内 |
| **其他** | 分散在多个文件 | 全部集中到AGENTS.md对应章节 | AGENTS.md 内 |

**结论**：所有改进都可以在AGENTS.md内解决，无需外部文件跳转！

---

## 四、开发效率对比

### 场景：修改照片保存路径逻辑

**传统多文件方案**：
1. 打开 `skills/photo-collection/SKILL.md` - 30秒
2. 找到路径构造章节 - 10秒
3. 修改后，发现需要同步修改AGENTS.md中的引用 - 20秒
4. 打开 `AGENTS.md` - 10秒
5. 修改 - 20秒
6. 保存两个文件 - 10秒
**总计**: 100秒

**扁平化单文件方案**：
1. 打开 `AGENTS.md` - 10秒
2. 跳转到 `## Skill: Photo Collection` 章节（Markdown锚点）- 5秒
3. 修改路径构造函数 - 20秒
4. 保存 - 5秒
**总计**: 40秒

**效率提升**: 60%

---

## 五、实施步骤（基于-dev版本）

### Step 1: 备份
```bash
cp -r workspace-field-worker-dev workspace-field-worker-dev-backup
```

### Step 2: 重写AGENTS.md为扁平化长文件

1. 保留YAML frontmatter（OpenClaw标准）
2. 将386行内容重组为大章节结构
3. 将分散的逻辑内联到各章节
4. 目标长度：500-800行

### Step 3: 处理Skills目录

**选择A（推荐）**：删除skills/目录，完全扁平化  
**选择B**：保留skills/，但SKILL.md仅包含指向AGENTS.md的链接

### Step 4: 测试

1. OpenClaw加载新的AGENTS.md
2. 测试照片路径（验证01号修复）
3. 测试数据隔离（验证03号修复）
4. 测试文档生成（验证07号修复）

---

## 六、与OpenClaw的兼容性

### 完全兼容

- ✅ YAML frontmatter（OpenClaw标准）
- ✅ skills声明（只是section指向AGENTS内部）
- ✅ tools声明
- ✅ permissions声明

### 优化点

- 不强制要求skills/目录存在
- Skill逻辑可以全部在AGENTS.md内
- 更少的文件I/O，更高的加载效率

---

**下一步**：是否开始编写具体的扁平化AGENTS.md长文件？