# Workspace完整架构设计方案

> 🏗️ 从v1.0问题出发，重构整体workspace结构

**设计原则**: 分层清晰、职责分离、配置驱动、易于维护

---

## 一、当前Workspace问题分析

### 1.1 现状结构

```
workspace-field-worker/
├── AGENTS.md          # 386行，过于臃肿
├── IDENTITY.md        # 23行，身份信息模板
├── BOOTSTRAP.md       # 55行，启动引导（应删除）
├── TOOLS.md           # 40行，工具说明
├── HEARTBEAT.md       # 心跳（未使用）
├── SOUL.md            # 个性定义
├── USER.md            # 用户信息
└── skills/            # Symlink到系统目录
    ├── doc-generation -> /usr/lib/...
    ├── grid-field-work -> /usr/lib/...
    ├── info-retrieval -> /usr/lib/...
    └── photo-collection -> /usr/lib/...
```

**field-data/**（在workspace之外）
```
field-data/                    # 数据根目录
├── communities-index.md
├── search-index.md
├── templates/
└── communities/
    └── {小区名}/
        └── {YYYY-MM}/
```

### 1.2 核心问题

| 问题 | 表现 | 影响 |
|------|------|------|
| **AGENTS.md臃肿** | 386行，包含身份、知识、流程、规则 | 难以维护，边界不清 |
| **Skills是Symlink** | 链接到系统目录，无法自定义 | 无法修复路径Bug |
| **缺少配置中心** | 分散在多个文件 | 难以统一管理 |
| **数据目录分离** | field-data/在workspace外 | 路径容易出错 |
| **职责不清晰** | IDENTITY/SOUL/USER分离 | 信息分散 |

### 1.3 与10个改进的关联

| 改进 | 根本原因 | 架构问题 |
|------|----------|----------|
| **01 照片路径Bug** | Skill实现与规范不一致 | Skills是symlink，无法修改 |
| **03 数据隔离** | Session管理不完善 | AGENTS.md缺少Session规范章节 |
| **07 文件名引用** | 文档生成逻辑错误 | doc-generation是symlink |
| **08 Skill重构** | AGENTS.md臃肿 | 缺少分层架构 |
| **09 权限控制** | 系统文件保护不足 | 缺少权限配置文件 |
| **其他** | ... | 都可通过架构优化解决 |

---

## 二、重构后的Workspace架构

### 2.1 目标架构

```
workspace-field-worker/              # Agent工作区
│
├── 📄 核心配置
│   ├── config.yaml                  # ⭐ 统一配置中心
│   └── AGENTS.md                    # 精简版Agent定义（150行）
│
├── 🧩 Skills（本地实现）
│   └── skills/
│       ├── grid-field-work/
│       │   ├── SKILL.md            # Skill定义+实现
│       │   └── config.yaml         # Skill配置
│       ├── photo-collection/
│       │   ├── SKILL.md            # ⭐ 修复路径Bug
│       │   └── config.yaml
│       ├── doc-generation/
│       │   ├── SKILL.md            # ⭐ 修复文件名引用
│       │   └── config.yaml
│       └── info-retrieval/
│           ├── SKILL.md
│           └── config.yaml
│
├── 📋 规则定义
│   └── rules/
│       ├── storage-rules.md        # 存储规范（从AGENTS提取）
│       ├── privacy-rules.md        # 隐私保护（从AGENTS提取）
│       └── field-grading.yaml      # 字段分级（P0/P1/P2）
│
├── 🗂️ 数据目录（纳入workspace）
│   └── field-data/                 # ⭐ 移入workspace
│       ├── communities-index.md
│       ├── search-index.md
│       ├── templates/
│       └── communities/
│           └── {小区名}/
│               └── {YYYY-MM}/
│                   ├── work-record.md
│                   ├── photos/
│                   └── documents/
│
├── 🔧 工具配置
│   └── tools/
│       ├── wecom-config.yaml       # 企业微信配置
│       ├── kimi-config.yaml        # Kimi API配置
│       └── baidu-map-config.yaml   # 百度地图配置
│
├── 📝 文档
│   └── docs/
│       ├── README.md               # 使用说明
│       ├── DEPLOYMENT.md           # 部署指南
│       └── CHANGELOG.md            # 变更日志
│
└── 🧪 测试
    └── tests/
        ├── test-photo-path.js      # 路径测试
        ├── test-data-isolation.js  # 数据隔离测试
        └── test-doc-generation.js  # 文档生成测试
```

### 2.2 核心文件对比

#### AGENTS.md 重构对比

**重构前（386行）**:
```markdown
# AGENTS.md
- 身份定义（14行）
- Session启动（56行）
- 隐私保护（24行）
- 记忆策略（25行）
- 领域知识（35行）
- 照片规范（11行）
- 工作流程（153行）← 臃肿
- 交互原则（10行）
- 数据录入（30行）
- 文件存储（40行）
- 服务范围（18行）
- Skills列表（8行）
- 物品清单（44行）
```

**重构后（150行）**:
```markdown
# AGENTS.md
- 身份定义（10行）✅ 保留
- Session启动（20行）✅ 精简
- 隐私规则（15行）✅ 引用rules/privacy-rules.md
- 领域知识（30行）✅ 保留核心
- Skills列表（10行）✅ 保留
- 工作流程（50行）✅ 引用skills/grid-field-work/SKILL.md
- 服务范围（15行）✅ 保留
```

**提取到新文件**:
- `rules/storage-rules.md`（40行）← 文件存储规范
- `rules/field-grading.yaml`（30行）← 字段分级
- `rules/privacy-rules.md`（15行）← 详细隐私规则
- `skills/*/SKILL.md` ← 各Skill的操作流程

---

### 2.3 Skills本地实现

**重构前（Symlink方式）**:
```bash
skills/
├── doc-generation -> /usr/lib/node_modules/openclaw/skills/doc-generation
├── grid-field-work -> /usr/lib/node_modules/openclaw/skills/grid-field-work
├── info-retrieval -> /usr/lib/node_modules/openclaw/skills/info-retrieval
└── photo-collection -> /usr/lib/node_modules/openclaw/skills/photo-collection
```

**问题**: 无法修改，无法修复Bug

**重构后（本地实现）**:
```bash
skills/
├── grid-field-work/
│   ├── SKILL.md              # Skill定义（包含触发条件、输入输出、流程）
│   └── config.yaml           # Skill配置（字段分级、提醒话术）
├── photo-collection/
│   ├── SKILL.md              # ⭐ 明确路径构造逻辑
│   └── config.yaml           # 照片命名规范、存储路径
├── doc-generation/
│   ├── SKILL.md              # ⭐ 明确文件名引用逻辑
│   └── config.yaml           # 文档模板配置
└── info-retrieval/
    ├── SKILL.md
    └── config.yaml
```

**photo-collection/SKILL.md 示例**:
```markdown
# photo-collection Skill

## 触发条件
- message_type: image
- session.state: collecting

## 路径构造逻辑（解决01号Bug）
```javascript
function getPhotoPath(community, date) {
  // 提取月份（不是日期）
  const month = date.toISOString().slice(0, 7); // "2026-03"
  
  // 构造标准路径
  const path = `field-data/communities/${community}/${month}/photos/`;
  
  // 自动创建目录
  ensureDir(path);
  
  return path;
}
```

## 文件名生成
格式: IMG_${YYYYMMDD}_${HHMMSS}_${SEQ}.jpg
示例: IMG_20260328_143022_01.jpg

## 保存流程
1. 接收照片
2. 构造路径（getPhotoPath）
3. 生成文件名
4. 保存文件
5. 验证存在性
6. AI分析
7. 更新work-record.md
8. 返回确认

## 错误处理
- 路径错误 → 自动修正并提示
- 保存失败 → 重试3次后报错
- 分析失败 → 保存照片，人工标注
```

---

### 2.4 配置中心（config.yaml）

**统一配置，替代分散配置**:

```yaml
# workspace-field-worker/config.yaml

agent:
  name: "武侯供电中心客户经理AI助手"
  version: "1.0.0"
  personality: "专业、简洁、主动"
  
session:
  timeout: 7200  # 2小时
  storage: "memory"
  
storage:
  root: "./field-data"  # ⭐ 相对路径，纳入workspace
  communities_dir: "communities"
  templates_dir: "templates"
  index_file: "communities-index.md"
  
  # 路径规范（解决01号Bug）
  path_rules:
    month_format: "YYYY-MM"  # 强制月份格式
    photo_subdir: "photos"
    doc_subdir: "documents"
    naming:
      photo: "IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg"
      doc: "{YYYYMMDD}_power-briefing.md"
      
  # 校验规则（解决01号Bug）
  validation:
    check_path_format: true
    auto_create_dir: true
    verify_after_save: true

# 字段分级（解决02号改进）
field_grading:
  P0:  # 必填
    - community_name
    - worker_name
    - address
    - households
    - power_rooms
    - transformers
    - publicity_photo
  P1:  # 重要
    - property_company
    - property_contact
    - sensitive_customers
    - shaft_inspection
  P2:  # 选填
    - commercial_households
    - charging_piles

# Skills配置
skills:
  grid-field-work:
    enabled: true
    config_file: "skills/grid-field-work/config.yaml"
  
  photo-collection:
    enabled: true
    config_file: "skills/photo-collection/config.yaml"
    # ⭐ 修复01号Bug的路径配置
    path_template: "{storage.root}/communities/{community}/{month}/photos/"
    
  doc-generation:
    enabled: true
    config_file: "skills/doc-generation/config.yaml"
    # ⭐ 修复07号Bug的引用配置
    verify_photo_exists: true
    
  info-retrieval:
    enabled: true
    config_file: "skills/info-retrieval/config.yaml"

# 权限控制（解决09号改进）
permissions:
  system_files:
    - "AGENTS.md"
    - "config.yaml"
    - "skills/*/SKILL.md"
    mode: "read-only"  # 系统文件只读
  
  data_files:
    - "field-data/**"
    mode: "read-write"  # 数据文件可读写

# 外部服务
services:
  kimi:
    model: "kimi-v1"
    base_url: "https://api.moonshot.cn/v1"
    # ⭐ 解决10号改进的Token监控
    enable_token_tracking: true
    
  baidu_map:
    api_key: "${BAIDU_MAP_API_KEY}"
    
  wecom:
    corp_id: "${WECOM_CORP_ID}"
    agent_id: "${WECOM_AGENT_ID}"
```

---

### 2.5 数据目录纳入Workspace

**重构前（分离）**:
```
workspace-field-worker/    # Agent代码
field-data/                # 数据（分离在外）
```

**问题**: 路径容易出错，部署时容易遗漏

**重构后（统一）**:
```
workspace-field-worker/    # Agent + 数据统一
├── ...                    # 代码
└── field-data/            # ⭐ 纳入workspace
    ├── communities-index.md
    ├── search-index.md
    ├── templates/
    └── communities/
```

**好处**:
- ✅ 路径统一用相对路径
- ✅ 部署时一起打包
- ✅ 版本控制可以管理
- ✅ 备份时一起备份

---

## 三、架构改进与10个问题的对应

| 问题 | 架构改进方案 | 文件变更 |
|------|-------------|---------|
| **01 照片路径Bug** | Skill本地实现 + 路径模板配置 | `skills/photo-collection/SKILL.md` + `config.yaml` |
| **02 字段分级** | 统一配置中心 | `config.yaml` field_grading |
| **03 数据隔离** | Session规范 + 校验机制 | `AGENTS.md` + `skills/*/SKILL.md` |
| **04+09 权限控制** | 权限配置 + 系统文件保护 | `rules/permission-rules.md` + `config.yaml` |
| **05 Word自动生成** | Skill触发配置 | `skills/doc-generation/config.yaml` |
| **06 Word内容不全** | 模板配置 + 校验 | `field-data/templates/` + `SKILL.md` |
| **07 文件名引用** | 引用验证逻辑 | `skills/doc-generation/SKILL.md` |
| **08 Skill重构** | 本地Skill + 标准化 | `skills/*/` 目录 |
| **10 Token监控** | 服务配置 + 监控 | `config.yaml` services.kimi |

**结论**: 通过整体架构重构，可以系统性解决所有10个问题！

---

## 四、实施计划

### Phase 1: 基础架构搭建（1-2周）

1. **创建config.yaml** - 统一配置中心
2. **重构AGENTS.md** - 精简到150行
3. **创建rules/** - 提取规则文件
4. **移动field-data/** - 纳入workspace

**产出**: 新架构基础框架

### Phase 2: Skills本地实现（2-3周）

1. **复制Skills到本地** - 从symlink改为本地
2. **修复photo-collection** - 解决01号Bug
3. **修复doc-generation** - 解决07号Bug
4. **标准化所有Skills** - 解决08号重构

**产出**: 可自定义的本地Skills

### Phase 3: 配置完善（1-2周）

1. **字段分级配置** - 解决02号
2. **权限配置** - 解决04+09号
3. **自动触发配置** - 解决05号
4. **Token监控配置** - 解决10号

**产出**: 完整的配置驱动架构

### Phase 4: 测试验证（1周）

1. **路径测试** - 验证01号修复
2. **隔离测试** - 验证03号修复
3. **文档测试** - 验证06+07号修复
4. **集成测试** - 全链路验证

**产出**: 稳定的v1.0架构

**总计**: 5-8周完成架构重构

---

## 五、与我们的v3.0对比

| 维度 | 目标仓库v1.0（重构后） | 我们的v3.0 | 对比 |
|------|----------------------|-----------|------|
| **架构** | 分层清晰 | 分层清晰 | ✅ 一致 |
| **配置** | config.yaml | config.yaml | ✅ 一致 |
| **Skills** | 本地实现 | 本地实现 | ✅ 一致 |
| **数据** | 纳入workspace | 可配置路径 | 🟡 相似 |
| **规范** | rules/目录 | SKILL.md内 | 🟡 相似 |

**结论**: 重构后，目标仓库架构与我们的v3.0高度一致！

---

**下一步**: 
1. 提交整体架构重构Proposal
2. 或者先提交Phase 1的详细设计
3. 或者针对某个具体问题（如01号）提交详细修复方案

**需要我详细展开哪个部分？**