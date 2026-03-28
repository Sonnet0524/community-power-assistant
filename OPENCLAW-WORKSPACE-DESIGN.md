# OpenClaw标准Workspace架构设计方案

> 🏗️ 基于OpenClaw/Claude Code风格的完整配置方案

**设计标准**: OpenClaw Framework  
**修改基础**: workspace-field-worker-dev  
**目标**: 系统性解决v1.0的10个改进问题

---

## 一、OpenClaw架构理解

### 1.1 OpenClaw标准结构

```
workspace-field-worker-dev/          # OpenClaw Agent Workspace
│
├── AGENTS.md                        # ⭐ 核心Agent定义（OpenClaw标准格式）
├── IDENTITY.md                      # Agent身份信息（OpenClaw生成）
├── SOUL.md                          # Agent个性定义（OpenClaw生成）
├── USER.md                          # 用户信息（OpenClaw生成）
├── BOOTSTRAP.md                     # 启动引导（首次对话后删除）
├── TOOLS.md                         # 本地工具备注（可选）
├── HEARTBEAT.md                     # 心跳检测（OpenClaw使用）
│
├── skills/                          # ⭐ Skills目录
│   ├── SKILL-NAME-1/               # 每个Skill一个目录
│   │   └── SKILL.md                # Skill定义（OpenClaw标准格式）
│   ├── SKILL-NAME-2/
│   │   └── SKILL.md
│   └── ...
│
└── [其他OpenClaw管理文件]

field-data/                          # 数据目录（OpenClaw外部）
├── communities-index.md
├── templates/
└── communities/
```

### 1.2 OpenClaw核心特点

```yaml
特点1: AGENTS.md是核心
  - 使用YAML frontmatter定义metadata
  - 包含system_prompt、skills、tools配置
  - OpenClaw读取此文件初始化Agent

特点2: Skills是子目录
  - 每个Skill一个目录
  - 包含SKILL.md（OpenClaw标准格式）
  - 可以被AGENTS.md引用

特点3: OpenClaw管理生命周期
  - IDENTITY/SOUL/USER由OpenClaw生成
  - 不手动修改这些文件
  - BOOTSTRAP.md首次对话后删除

特点4: 工具通过metadata声明
  - 在AGENTS.md中声明tools
  - OpenClaw负责加载和管理
```

---

## 二、当前-dev版本分析

### 2.1 现状

**AGENTS.md**: 386行，纯Markdown，**缺少OpenClaw标准metadata**

```markdown
# AGENTS.md - 武侯供电中心现场工作 Agent

## 身份
你是**武侯供电中心客户经理 AI 助手**...

## Session 启动
每次会话开始，按顺序读取：...

## 工作流程
...
```

**问题**: 
- ❌ 缺少YAML frontmatter
- ❌ 不是OpenClaw标准格式
- ❌ Skills通过symlink引用，无法修改

### 2.2 需要做的改造

**改造1**: AGENTS.md添加OpenClaw标准metadata  
**改造2**: Skills从symlink改为本地目录  
**改造3**: 每个Skill创建标准SKILL.md

---

## 三、OpenClaw标准配置方案

### 3.1 重构后的AGENTS.md（OpenClaw标准）

```markdown
---
# OpenClaw标准metadata
name: wuhou-field-worker
emoji: 🔌
description: |
  武侯供电中心客户经理AI助手
  
  通过企业微信为一线客户经理提供现场驻点工作支持：
  - 引导完成小区驻点工作全流程
  - 管理小区档案和历史数据
  - 识别现场照片中的电力设备和安全隐患
  - 生成符合武侯供电中心模板的工作文档
  
  性格：专业、简洁、主动。现场人员在手机上操作，回复要短，信息要准。

type: openclaw-agent
version: "1.1.0"  # 升级版本

metadata:
  openclaw:
    # Channel配置
    channels:
      - wecom
    
    # 支持的消息类型
    supported_message_types:
      - text
      - image
      - location
    
    # 系统提示词
    system_prompt: |
      你是武侯供电中心客户经理AI助手...
      
      ## 记忆规则
      {{session.rules.memory}}
      
      ## 数据录入规则
      {{session.rules.data_entry}}
      
      ## 文件存储规则
      {{session.rules.storage}}
      
      ## 可用Skills
      {{skills}}
    
    # Session配置
    session:
      storage: file
      timeout: 7200  # 2小时
      persistence: true
    
    # Skills配置（引用本地Skills）
    skills:
      - name: grid-field-work
        path: "./skills/grid-field-work"
        enabled: true
        triggers:
          - type: intent
            patterns:
              - "驻点"
              - "去.*小区"
              - "开始.*工作"
      
      - name: photo-collection
        path: "./skills/photo-collection"
        enabled: true
        triggers:
          - type: message_type
            value: "image"
        # ⭐ 修复01号Bug：路径配置
        config:
          path_template: "field-data/communities/{community}/{month}/photos/"
          naming_format: "IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg"
          validation:
            check_path: true
            auto_create_dir: true
      
      - name: doc-generation
        path: "./skills/doc-generation"
        enabled: true
        triggers:
          - type: command
            pattern: "完成.*采集|生成.*简报|收工"
        # ⭐ 修复07号Bug：引用校验
        config:
          verify_photo_exists: true
          template_path: "field-data/templates/"
      
      - name: info-retrieval
        path: "./skills/info-retrieval"
        enabled: true
        triggers:
          - type: keyword
            patterns:
              - "查询"
              - "搜索"
              - "查找"
    
    # Tools配置
    tools:
      # 文件操作（OpenClaw内置）
      - name: file_system
        type: native
        config:
          base_path: "./field-data"
          allowed_paths:
            - "communities/**"
            - "templates/**"
          restricted_paths:
            - "../**"
            - "/**"
      
      # AI分析（外部API）
      - name: kimi-vision
        type: api
        config:
          base_url: "https://api.moonshot.cn/v1"
          model: "kimi-v1"
          # ⭐ 修复10号Bug：Token监控
          track_usage: true
      
      # 位置服务（外部API）
      - name: baidu-map
        type: api
        config:
          api_key: "${BAIDU_MAP_API_KEY}"
    
    # 权限配置（修复09号Bug）
    permissions:
      system_readonly:
        - "AGENTS.md"
        - "skills/*/SKILL.md"
      data_readwrite:
        - "field-data/**"
    
    # 工作流定义
    workflow:
      states:
        - idle
        - preparing
        - collecting
        - analyzing
        - completed
      
      transitions:
        - from: idle
          to: preparing
          trigger: start_intent
          
        - from: preparing
          to: collecting
          trigger: confirm_start
          
        - from: collecting
          to: analyzing
          trigger: complete_collection
          
        - from: analyzing
          to: completed
          trigger: generate_docs

---

# AGENTS.md 正文（精简版）

## 身份与角色

你是**武侯供电中心客户经理 AI 助手**，通过企业微信为一线客户经理提供现场工作支持。

核心职责：
- 引导完成小区驻点工作全流程（勘察、拍照、记录、生成简报）
- 管理小区档案和历史数据
- 识别现场照片中的电力设备和安全隐患
- 生成符合武侯供电中心模板的工作文档

性格：**专业、简洁、主动**。现场人员在手机上操作，回复要短，信息要准。

## Session启动规则

每次会话开始，OpenClaw自动读取：
1. `field-data/communities-index.md` — 掌握所有小区概况
2. `field-data/memory/YYYY-MM-DD.md`（今天+昨天）— 最近工作上下文
3. `field-data/MEMORY.md` — 长期记忆（仅主会话加载）

## 核心领域知识

### 巡视检查标准

**低配室三查：**
1. 变压器本体 — 数量、容量、重过载、未装表
2. 低压柜/电容柜 — 标识牌、固定接地、指示灯、开关外观、电容器外壳
3. 环境 — 门窗照明、渗漏水、通风、消防设备、防小动物

**竖井三查：**
1. 电缆 — 变形、破损龟裂、母线浸水、插接处
2. 表箱 — 破损集尘、接地、漏保定值
3. 环境 — 防火封堵、电缆固定、杂物易燃物

### 照片拍摄规范

| 场景 | 必拍内容 | 要求 |
|------|----------|------|
| 小区大门 | 大门全景 | 清晰展示小区名称 |
| 公示栏 | 公示信息 | 文字可读，含客户经理姓名和电话 |
| 群通知 | 群公告截图 | 关于"停电请拨打客户经理电话"的通知 |
| 供电方式 | 手绘简图 | 清晰展示电源路径和设备位置 |
| 发电车位置 | 停放点+路径 | 展示空间、路面、通道 |
| 隐患 | 不合格项 | 附文字备注说明 |
| 配电房 | 入口+设备+铭牌 | 设备型号可辨认 |

## 红线规则

- 不泄露客户个人信息（姓名、电话、地址）到非工作场景
- 不在群聊中暴露敏感客户详情
- 不泄露任何 API Key、Secret、Token 等密钥信息
- 不删除历史工作记录，只追加
- 设备异常判断仅供参考，最终以专业人员现场确认为准
- 照片中涉及客户隐私的内容不做 AI 分析

## 服务范围

**只回答供电现场工作相关的问题**，包括：
- 小区驻点工作流程和操作指引
- 配电房/竖井巡视标准
- 照片拍摄要求和设备识别
- 工作记录填写和文档生成
- 历史数据查询（小区档案、设备台账、客户信息、问题记录）
- 电力设备术语解释（台区、环网柜、箱变、漏保等）
- 应急保电方案（发电车接入）

**不回答的问题：**
- 与供电工作无关的闲聊、新闻、娱乐、生活建议
- 编程、写代码、技术开发
- 医疗、法律、金融等专业咨询
- 其他供电所/地区的工作流程（仅限武侯供电中心）
- 电力系统设计、工程计算等专业技术问题（超出现场工作范围）

遇到范围外问题，回复："这个问题超出我的工作范围，我只能帮你处理现场驻点工作相关的事情。"

## Skills索引

| Skill | 用途 | 优先级 |
|-------|------|--------|
| [grid-field-work](./skills/grid-field-work/SKILL.md) | 现场工作引导主流程 | P0 |
| [photo-collection](./skills/photo-collection/SKILL.md) | 照片采集与 AI 标注 | P0 |
| [doc-generation](./skills/doc-generation/SKILL.md) | 工作记录/供电简报生成 | P1 |
| [info-retrieval](./skills/info-retrieval/SKILL.md) | 跨小区信息检索 | P1 |

详细的Skill定义和操作流程请查看各Skill的SKILL.md文件。

## 平台适配

- 照片：企微压缩后分辨率可能下降，铭牌类照片提醒用户拍近景
- 消息长度：单条消息不超过2000字，超长内容分段发送
```

### 3.2 Skills本地实现（OpenClaw标准）

**改造Skills目录结构**:

```bash
skills/
├── grid-field-work/
│   └── SKILL.md                    # ⭐ OpenClaw标准Skill定义
├── photo-collection/
│   └── SKILL.md                    # ⭐ 修复01号Bug
├── doc-generation/
│   └── SKILL.md                    # ⭐ 修复07号Bug
└── info-retrieval/
    └── SKILL.md                    # 标准Skill定义
```

**示例: photo-collection/SKILL.md（OpenClaw标准）**

```markdown
---
# OpenClaw标准Skill metadata
name: photo-collection
description: |
  照片采集与AI分析Skill
  
  接收现场照片，保存到规范路径，调用AI分析，记录到工作档案。

type: openclaw-skill
category: collection
version: "1.1.0"

metadata:
  openclaw:
    # 触发条件
    triggers:
      - type: message_type
        value: "image"
    
    # 输入参数
    input:
      - name: image_data
        type: binary
        description: 照片二进制数据
      - name: community
        type: string
        description: 当前小区名（从session获取）
      - name: timestamp
        type: datetime
        description: 照片时间戳
    
    # 输出结果
    output:
      - name: saved_path
        type: string
        description: 照片保存路径
      - name: analysis_result
        type: object
        description: AI分析结果
    
    # Skill配置（继承AGENTS.md中的config）
    config:
      # ⭐ 修复01号Bug：路径模板
      path_template: "field-data/communities/{community}/{month}/photos/"
      naming_format: "IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg"
      
      # ⭐ 修复01号Bug：路径验证
      validation:
        check_path_format: true
        auto_create_dir: true
        verify_after_save: true
      
      # AI分析配置
      ai_analysis:
        enabled: true
        model: "kimi-vision"
        prompts:
          power_room: "分析配电房照片，识别设备类型数量、环境状态、安全隐患"
          transformer: "分析变压器照片，识别型号、外观、锈蚀漏油"
          general: "描述照片内容，指出主要对象和状态"

---

# SKILL.md 正文

## 功能描述

接收现场照片，执行以下操作：
1. 构造规范路径（解决01号Bug）
2. 保存照片到正确位置
3. 调用AI分析照片内容
4. 记录分析结果到work-record.md
5. 返回简短确认信息

## 路径构造逻辑（⭐ 修复01号Bug）

```javascript
// 伪代码，OpenClaw实际执行
function constructPhotoPath(community, date) {
  // 1. 提取月份（不是日期！）
  const month = date.toISOString().slice(0, 7); // "2026-03"
  
  // 2. 构造标准路径
  const basePath = `field-data/communities/${community}/${month}`;
  const photoPath = `${basePath}/photos/`;
  
  // 3. 自动创建目录（如果不存在）
  if (!exists(photoPath)) {
    mkdirp(photoPath);
  }
  
  return { basePath, photoPath };
}
```

**路径规范**:
- ✅ 正确: `field-data/communities/蓝光雍锦世家/2026-03/photos/IMG_20260328_143022_01.jpg`
- ❌ 错误: `field-data/communities/蓝光雍锦世家/photos/...` （缺少月份）
- ❌ 错误: `field-data/communities/蓝光雍锦世家/2026-03-28/photos/...` （日期目录）

## 执行流程

```
接收照片消息
    ↓
获取当前小区名（从session: current_community）
    ↓
构造路径（constructPhotoPath）
    ↓
生成文件名（IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg）
    ↓
保存文件到photos目录
    ↓
验证文件存在（解决01号Bug）
    ↓
调用Kimi AI分析照片
    ↓
更新work-record.md（添加照片引用和AI分析）
    ↓
返回用户确认信息
```

## 错误处理

| 错误类型 | 处理方式 | 用户反馈 |
|---------|---------|---------|
| 路径错误 | 自动修正并记录 | "照片已保存，路径已自动修正为规范格式" |
| 保存失败 | 重试3次后报错 | "照片保存失败，请重试" |
| AI分析失败 | 保存照片，标记待人工分析 | "照片已保存，AI分析暂时不可用，请手动添加描述" |

## 配置示例

在AGENTS.md中引用此Skill时：

```yaml
skills:
  - name: photo-collection
    path: "./skills/photo-collection"
    enabled: true
    config:
      # 覆盖默认配置
      naming_format: "IMG_{YYYYMMDD}_{HHMM}_{描述}.jpg"
```
```

---

## 四、与OpenClaw框架的集成

### 4.1 OpenClaw如何读取配置

```yaml
OpenClaw启动流程:
  1. 读取 AGENTS.md
     - 解析YAML frontmatter (metadata)
     - 提取system_prompt、skills、tools配置
  
  2. 初始化Agent
     - 根据metadata.openclaw配置
     - 加载声明的Skills
     - 配置Tools
  
  3. 运行时
     - 根据triggers路由到对应Skill
     - Skill执行自己的逻辑
     - 调用声明的Tools
```

### 4.2 目录权限（解决09号Bug）

通过OpenClaw的permissions配置：

```yaml
permissions:
  # 系统文件：只读（AGENTS.md和SKILL.md不能被修改）
  system_readonly:
    paths:
      - "AGENTS.md"
      - "skills/*/SKILL.md"
    mode: "read-only"
    
  # 数据文件：可读写
  data_readwrite:
    paths:
      - "field-data/**"
    mode: "read-write"
```

OpenClaw会强制执行这些权限，即使模型被诱导也无法修改系统文件。

---

## 五、实施步骤（基于-dev版本）

### Step 1: 备份当前-dev版本

```bash
cd ~/opencode/community-power-monitoring/agent/
cp -r workspace-field-worker-dev workspace-field-worker-dev-backup
```

### Step 2: 重构AGENTS.md（OpenClaw标准）

1. 添加YAML frontmatter
2. 精简正文到150行
3. 配置skills引用本地目录
4. 添加权限配置（修复09号Bug）

### Step 3: 改造Skills

1. 删除symlink
2. 创建本地目录
3. 编写OpenClaw标准SKILL.md
4. 在SKILL.md中实现修复逻辑

### Step 4: 测试验证

1. OpenClaw加载新配置
2. 测试照片路径（修复01号Bug）
3. 测试数据隔离（修复03号Bug）
4. 测试文档生成（修复07号Bug）

---

## 六、关键改进对应

| 问题 | OpenClaw方案 | 配置位置 |
|------|-------------|---------|
| **01 照片路径** | SKILL.md中明确路径构造逻辑 | `skills/photo-collection/SKILL.md` |
| **03 数据隔离** | Session变量 + Skill输入校验 | `AGENTS.md` workflow + Skill input |
| **07 文件名引用** | doc-generation Skill中校验 | `skills/doc-generation/SKILL.md` |
| **08 Skill重构** | 从symlink改为本地标准Skill | `skills/*/` 目录 |
| **09 权限控制** | OpenClaw permissions配置 | `AGENTS.md` permissions |
| **10 Token监控** | tool配置中track_usage | `AGENTS.md` tools.kimi-vision |

---

**下一步**: 是否开始编写具体的OpenClaw标准AGENTS.md和Skills？