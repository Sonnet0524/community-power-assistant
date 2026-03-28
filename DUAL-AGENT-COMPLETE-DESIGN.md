# 双Agent协同工作空间架构设计

> 🏗️ 信息收集Agent + 信息输出Agent + 共享Workspace + 版本管理

**设计目标**: 
- 双Agent协同：采集Agent + 输出Agent
- 共享Workspace：跨Session数据持久化
- 版本管理：N小区 × N版本
- 可扩展：预留规划Agent接口

---

## 一、整体架构概览

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      共享工作空间层                               │
│  field-data/                                                    │
│  ├── communities-index.md          # 小区总索引（所有Agent共享）  │
│  ├── search-index.md               # 全文检索索引               │
│  ├── global-config.yaml            # 全局配置（两个Agent共享）   │
│  ├── templates/                    # 文档模板（共享）           │
│  └── communities/                  # 小区数据（核心共享区）      │
│      └── {小区名}/                 # 每个小区独立目录           │
│          ├── README.md             # 小区档案（最新版本）        │
│          ├── versions/             # ⭐ 历史版本管理            │
│          │   ├── v1.0.0-20240301/  # 版本化存储               │
│          │   ├── v1.1.0-20240315/  # 每次重大更新创建版本      │
│          │   └── ...                                             │
│          └── {YYYY-MM}/            # 月份工作目录（当前活跃）   │
│              ├── work-record.md    # 工作记录                  │
│              ├── photos/           # 照片                      │
│              └── documents/        # 生成文档                  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌─────────▼──────────┐    ┌────▼────┐
│  Agent A     │    │     Agent B        │    │ Future  │
│  采集Agent   │◄──►│    输出Agent       │    │ 规划Agent│
│              │    │                    │    │         │
│ - 信息收集   │    │ - 信息检索         │    │ - 计划  │
│ - 现场工作   │    │ - 报告生成         │    │ - 调度  │
│ - 照片采集   │    │ - 历史查询         │    │ - 预测  │
│ - 数据录入   │    │ - 数据分析         │    │         │
└──────────────┘    └────────────────────┘    └─────────┘
        │                     │
        └──────────┬──────────┘
                   │
┌──────────────────▼──────────────────┐
│         Agent工作空间层              │
│  workspace-{agent-name}/            │
│  ├── AGENTS.md                      │
│  ├── skills/                        │
│  └── session-data/                  │
│      └── {session-id}/              │
│          ├── context.json           │
│          ├── conversation.log       │
│          └── temp-files/            │
└─────────────────────────────────────┘
```

### 1.2 工作空间分层

```yaml
Layer 1: 共享工作空间 (field-data/)
  - 位置: 系统相对路径 ../field-data/ (跳出agent空间)
  - 访问: 两个Agent都有读写权限
  - 内容: 小区数据、版本历史、生成文档
  - 生命周期: 跨Session持久化

Layer 2: Agent工作空间 (workspace-{agent}/)
  - 位置: agent目录内
  - 访问: 仅当前Agent
  - 内容: AGENTS.md、skills、session临时数据
  - 生命周期: Agent级别

Layer 3: Session工作空间 (session-data/{session-id}/)
  - 位置: Agent工作空间内
  - 访问: 仅当前Session
  - 内容: 对话历史、上下文、临时文件
  - 生命周期: Session级别
```

---

## 二、双Agent设计

### 2.1 Agent A: 采集Agent (field-collector)

**定位**: 现场工作执行者
**用户**: 供电所客户经理
**核心能力**: 信息收集 + 基础检索

#### AGENTS.md 结构

```markdown
---
name: field-collector
description: |
  武侯供电中心现场采集Agent
  负责：小区驻点工作、现场数据采集、照片采集、数据录入
  
type: openclaw-agent
version: "2.0.0"
role: collector  # ⭐ 角色标识

metadata:
  openclaw:
    channels:
      - wecom
    
    # 能力声明
    capabilities:
      - field_work           # 现场工作引导
      - photo_collection     # 照片采集
      - data_entry           # 数据录入
      - basic_retrieval      # 基础检索（只读自己录入的数据）
    
    # 共享工作空间配置
    shared_workspace:
      path: "../field-data"  # ⭐ 跳出agent空间，相对路径
      permissions:
        - read: "communities/**"
        - write: "communities/**"  # 可以写入
    
    # 本Agent工作空间
    agent_workspace:
      path: "./"
      session_data: "./session-data"
    
    skills:
      - name: grid-field-work
        section: "Skill_GridFieldWork"
      - name: photo-collection
        section: "Skill_PhotoCollection"
      - name: data-entry
        section: "Skill_DataEntry"
      - name: basic-retrieval
        section: "Skill_BasicRetrieval"
    
    # 版本管理配置
    version_control:
      enabled: true
      auto_commit: true
      commit_message_template: "[{agent}] {action} - {community} - {date}"

---

# Agent A: 采集Agent

## 角色定位

你是**现场采集Agent**，专为供电所客户经理提供现场驻点工作支持。

**你可以**：
- ✅ 引导完成小区驻点工作
- ✅ 采集现场照片和数据
- ✅ 录入工作记录
- ✅ 基础查询（自己录入的数据）

**你不能**（由Agent B处理）：
- ❌ 跨小区综合分析
- ❌ 生成正式报告
- ❌ 历史版本对比
- ❌ 数据挖掘分析

## 共享工作空间访问

**数据根目录**: `../field-data/`（相对路径，跳出本Agent空间）

**你可以读写**：
- `../field-data/communities/{小区}/{月份}/` - 当前工作数据
- `../field-data/communities/{小区}/README.md` - 小区档案

**你不要修改**：
- `../field-data/communities/{小区}/versions/` - 版本历史（只读）
- `../field-data/search-index.md` - 全局检索索引（由Agent B维护）

## Session与持久化

**Session级别**（当前对话）：
- Session ID: {session-id}
- 工作目录: `./session-data/{session-id}/`
- 存储: 对话历史、临时文件、当前上下文
- 生命周期: 对话结束可清理

**跨Session级别**（共享工作空间）：
- 路径: `../field-data/`
- 存储: 小区数据、照片、文档
- 生命周期: 永久保存
- 访问: 本Agent和Agent B都可以访问

## 版本管理规则

**什么时候创建版本**：
1. 完成一次完整的驻点工作 → 自动创建版本 v1.x
2. 重大数据更新（如新增变压器）→ 手动创建版本
3. 每天首次工作 → 检查是否需要版本

**版本命名**: v{主版本}.{次版本}.{修订}-{YYYYMMDD}
- v1.0.0-20240301: 首次完整驻点
- v1.1.0-20240315: 补充配电房信息
- v2.0.0-20240401: 重新勘察（重大变更）

**版本内容**: 
```
../field-data/communities/{小区}/versions/v1.0.0-20240301/
├── README.md              # 该版本的完整档案
├── work-record.md         # 工作记录
├── photos/                # 照片快照
└── documents/             # 生成文档快照
```

## 与Agent B的协作

**何时调用Agent B**：
- 用户需要："生成月度报告"、"分析历史趋势"
- 你说："这个功能由报告Agent处理，请稍候"
- 系统会自动转发给Agent B

**数据共享**：
- 你录入的数据，Agent B可以读取
- Agent B生成的报告，你可以查看
- 不要在Agent B工作时修改同一小区数据

## Skill: Grid Field Work

### 触发条件
- intent: "驻点" | "去.*小区" | "开始.*工作"

### 执行逻辑
1. 确认当前小区（文字确认，避免同音字）
2. 确认工作人员
3. 读取小区历史（如果有）
4. 创建/进入 `../field-data/communities/{小区}/{月份}/`
5. 按5项清单引导采集

### 5项采集清单
1. 小区基本情况 + 大门照片
2. 进网入格（公示栏照片）
3. 供配电方案（手绘供电图）
4. 应急保电方案（发电车接入）
5. 用电检查隐患台账（低配室/竖井）

## Skill: Photo Collection

### 触发条件
- message_type: "image"

### 路径构造（关键）
```javascript
// 必须使用共享工作空间的相对路径
const basePath = "../field-data/communities/";
const community = session.current_community;
const month = getCurrentMonth(); // "2026-03"
const photoPath = `${basePath}${community}/${month}/photos/`;

// 确保目录存在
ensureDir(photoPath);

// 保存照片
const filename = `IMG_${timestamp}_${seq}.jpg`;
savePhoto(photoPath + filename, imageData);

// 验证并更新索引
verifyExists(photoPath + filename);
updateCommunityIndex(community, photoPath + filename);
```

## Skill: Data Entry

### 数据录入规则
1. **实时录入**: 采集完成后立即写入work-record.md
2. **更新README**: 工作结束后更新小区档案
3. **创建版本**: 重要节点自动创建版本快照

### 版本创建流程
```
完成驻点工作
    ↓
检查是否需要新版本（是否有重大更新）
    ↓
是 → 创建版本目录: ../field-data/communities/{小区}/versions/v{x.y.z}-{date}/
    → 复制当前所有数据到版本目录
    → 更新README.md版本历史
    ↓
否 → 直接更新当前数据
```

## Skill: Basic Retrieval

### 查询范围
- 当前小区的历史记录
- 自己录入的数据
- 基础设备信息

### 查询限制
- 不跨小区综合分析
- 不进行数据挖掘
- 复杂查询交给Agent B
```

### Agent A 的 Skills 目录

```
workspace-field-collector/
├── AGENTS.md
└── skills/
    ├── grid-field-work/
    │   └── SKILL.md          # 现场工作引导
    ├── photo-collection/
    │   └── SKILL.md          # 照片采集（含路径构造）
    ├── data-entry/
    │   └── SKILL.md          # 数据录入（含版本管理）
    └── basic-retrieval/
        └── SKILL.md          # 基础检索
```

---

### 2.2 Agent B: 输出Agent (field-reporter)

**定位**: 数据分析与报告生成者
**用户**: 供电所主管、客户经理（查看报告）
**核心能力**: 信息检索 + 报告生成 + 数据分析

#### AGENTS.md 结构

```markdown
---
name: field-reporter
description: |
  武侯供电中心报告生成Agent
  负责：信息检索、报告生成、数据分析、历史查询
  
type: openclaw-agent
version: "2.0.0"
role: reporter  # ⭐ 角色标识

metadata:
  openclaw:
    channels:
      - wecom
      - web        # ⭐ 额外支持Web界面
    
    capabilities:
      - advanced_retrieval   # 高级检索（跨小区、跨时间）
      - report_generation    # 报告生成
      - data_analysis        # 数据分析
      - version_management   # 版本管理
      - trend_analysis       # 趋势分析
    
    shared_workspace:
      path: "../field-data"
      permissions:
        - read: "**/*"        # 读取所有数据
        - write: "templates/**" # 可更新模板
        - write: "search-index.md"  # 维护检索索引
        - write: "communities/*/versions/**"  # 可创建版本快照
    
    skills:
      - name: advanced-retrieval
        section: "Skill_AdvancedRetrieval"
      - name: report-generator
        section: "Skill_ReportGenerator"
      - name: data-analyzer
        section: "Skill_DataAnalyzer"
      - name: version-manager
        section: "Skill_VersionManager"

---

# Agent B: 报告Agent

## 角色定位

你是**报告生成Agent**，专为供电所提供数据分析和报告生成服务。

**你可以**：
- ✅ 跨小区综合检索
- ✅ 生成各类报告（月度/季度/年度）
- ✅ 历史数据对比分析
- ✅ 版本管理和回溯
- ✅ 数据可视化（趋势图、统计表）

**你不要**（由Agent A处理）：
- ❌ 现场数据采集
- ❌ 实时照片录入
- ❌ 直接修改当前工作数据

## 高级检索能力

### 跨小区检索
用户: "查询所有小区的变压器状态"
```
检索范围: ../field-data/communities/*/
检索内容: 
  - 每个小区的README.md
  - 设备台账信息
  - 历史问题记录
输出: 综合对比表
```

### 跨时间检索
用户: "蓝光雍锦世家过去半年的变化"
```
检索范围: 
  - ../field-data/communities/蓝光雍锦世家/versions/*/
  - ../field-data/communities/蓝光雍锦世家/2026-*/
分析内容:
  - 版本对比
  - 设备变更
  - 问题趋势
输出: 变化趋势报告
```

### 全文检索
维护全局索引: ../field-data/search-index.md
```
倒排索引结构:
  关键词 -> [小区A/文档1, 小区B/文档2, ...]
```

## 报告生成

### 报告类型

1. **供电简报**（单次驻点）
   - 输入: 某次work-record.md
   - 输出: {date}_power-briefing.md

2. **月度汇总报告**
   - 输入: 某小区当月所有记录
   - 输出: monthly-report-{month}.md

3. **季度分析报告**
   - 输入: 多小区季度数据
   - 输出: quarterly-analysis.md

4. **设备状态报告**
   - 输入: 设备台账历史
   - 输出: equipment-status.md

### 报告模板

位置: `../field-data/templates/`
```
templates/
├── power-briefing-template.md      # 供电简报
├── monthly-report-template.md      # 月度报告
├── quarterly-analysis-template.md  # 季度分析
└── equipment-status-template.md    # 设备状态
```

## 版本管理

### 版本浏览
用户: "查看蓝光雍锦世家的历史版本"
```
列出: ../field-data/communities/蓝光雍锦世家/versions/*/
显示: 版本号、日期、变更摘要
操作: 对比任意两个版本
```

### 版本对比
```
版本A (v1.0.0-20240301) vs 版本B (v1.1.0-20240315)

变更:
+ 新增: 2号配电房信息
~ 修改: 变压器数量 2→3
- 删除: 无
```

### 版本恢复
用户: "恢复到3月1日的版本"
```
注意: 仅主管权限可执行
操作: 将versions/v1.0.0-20240301/复制到当前
记录: 在README.md中注明恢复操作
```

## 数据分析

### 趋势分析
- 隐患发现趋势（月度对比）
- 设备老化趋势（年度对比）
- 客户投诉趋势（小区对比）

### 统计分析
- 各小区驻点频次
- 设备类型分布
- 问题类型统计

## 与Agent A的协作

**何时接管**：
- 用户从Agent A转发过来
- 用户直接询问报告相关问题

**数据依赖**：
- 依赖Agent A采集的数据
- 不工作时可以读取所有数据
- Agent A工作时（Session活跃），只读不修改

**协作流程**：
```
Agent A完成驻点工作
    ↓
创建版本快照
    ↓
用户: "生成报告"（转发给Agent B）
    ↓
Agent B读取最新数据
    ↓
生成报告
    ↓
用户查看报告
```
```

### Agent B 的 Skills 目录

```
workspace-field-reporter/
├── AGENTS.md
└── skills/
    ├── advanced-retrieval/
    │   └── SKILL.md          # 高级检索（跨小区/时间）
    ├── report-generator/
    │   └── SKILL.md          # 报告生成
    ├── data-analyzer/
    │   └── SKILL.md          # 数据分析
    └── version-manager/
        └── SKILL.md          # 版本管理
```

---

## 三、共享Workspace详细设计

### 3.1 目录结构（核心）

```
field-data/                                    # ⭐ 共享根目录
│
├── 📄 全局索引与配置
│   ├── communities-index.md                   # 小区总索引
│   ├── search-index.md                        # 全文检索索引（Agent B维护）
│   ├── global-config.yaml                     # 全局配置
│   └── version-history.md                     # 系统版本历史
│
├── 🎨 模板库（共享）
│   └── templates/
│       ├── power-briefing-template.md
│       ├── monthly-report-template.md
│       ├── work-record-template.md
│       └── emergency-guide-template.md
│
└── 🏘️ 小区数据（N小区 × N版本）
    └── {小区名}/                              # 示例: 蓝光雍锦世家/
        │
        ├── 📋 当前活跃数据
        │   ├── README.md                      # 小区档案（最新版）
        │   └── {YYYY-MM}/                     # 月份工作目录
        │       ├── work-record.md             # 工作记录
        │       ├── photos/                    # 照片
        │       │   └── IMG_*.jpg
        │       └── documents/                 # 生成文档
        │           └── *_power-briefing.md
        │
        └── 📁 版本历史（版本管理核心）
            └── versions/
                ├── v1.0.0-20240301/           # 版本快照
                │   ├── version-info.yaml      # 版本元数据
                │   ├── README.md              # 该版本的完整档案
                │   ├── work-record.md         # 工作记录快照
                │   ├── photos/                # 照片快照（符号链接或复制）
                │   └── documents/             # 文档快照
                │
                ├── v1.1.0-20240315/           # 下一个版本
                │   └── ...
                │
                └── latest -> v1.1.0-20240315/ # 最新版本软链接
```

### 3.2 版本管理设计

#### 版本元数据（version-info.yaml）

```yaml
version: "1.1.0"
version_code: "v1.1.0-20240315"
created_at: "2024-03-15T14:30:00+08:00"
created_by: "field-collector"  # 创建者Agent

change_type: "minor"  # major|minor|patch
change_summary: "补充2号配电房信息，新增变压器1台"

parent_version: "v1.0.0-20240301"  # 父版本
commit_message: "[field-collector] 完成驻点 - 蓝光雍锦世家 - 2024-03-15"

stats:
  photos_added: 12
  photos_modified: 0
  photos_removed: 0
  documents_generated: 2
  fields_updated: 5

# 变更详情
changes:
  - type: "add"
    field: "power_rooms"
    old_value: "1"
    new_value: "2"
    description: "新增2号配电房"
    
  - type: "modify"
    field: "transformers"
    old_value: "2"
    new_value: "3"
    description: "新增变压器SCB11-500/10"
```

#### 版本创建策略

**自动创建**（Agent A执行）：
```
触发条件:
  1. 完成一次完整的驻点工作
  2. 检测到重大数据变更（P0字段变化）
  
创建流程:
  1. Agent A完成工作，准备保存
  2. 检查是否需要新版本（对比上次版本）
  3. 如需要:
     - 创建版本目录: versions/v{x.y.z}-{date}/
     - 复制当前数据到版本目录
     - 生成version-info.yaml
     - 更新latest软链接
  4. 继续保存当前数据
```

**手动创建**（Agent B执行）：
```
触发: 主管通过Agent B主动创建
场景: 备份当前状态、标记里程碑
流程:
  1. Agent B接收创建版本指令
  2. 验证权限
  3. 创建版本快照
  4. 添加自定义commit message
```

### 3.3 Agent权限设计

```yaml
Agent A (field-collector) 权限:
  read:
    - communities/*/README.md
    - communities/*/{月份}/
    - communities/*/versions/*/
  write:
    - communities/*/{月份}/**        # 当前工作数据
    - communities/*/README.md        # 更新小区档案
    - communities/*/versions/*/      # 创建新版本（只创建，不修改旧版本）
  not_allowed:
    - search-index.md                # 由Agent B维护
    - templates/*                    # 只读

Agent B (field-reporter) 权限:
  read:
    - **/*                           # 读取所有数据
  write:
    - templates/*                    # 更新模板
    - search-index.md                # 维护检索索引
    - communities/*/versions/*/      # 创建版本快照（用于备份）
  not_allowed:
    - communities/*/{月份}/work-record.md  # 不修改当前工作记录
    - communities/*/{月份}/photos/        # 不修改当前照片
```

---

## 四、Session与持久化设计

### 4.1 三层数据持久化

```
Layer 1: Session数据（临时，可清理）
  位置: workspace-{agent}/session-data/{session-id}/
  内容: 
    - context.json: 当前对话上下文
    - conversation.log: 对话历史
    - temp/: 临时文件
  生命周期: Session结束可清理
  访问: 仅当前Agent当前Session

Layer 2: Agent数据（Agent级别，持久）
  位置: workspace-{agent}/
  内容:
    - AGENTS.md: Agent配置
    - skills/: Skill实现
    - memory/: Agent记忆（跨Session）
  生命周期: 永久
  访问: 仅当前Agent

Layer 3: 共享数据（系统级别，核心）
  位置: ../field-data/（相对路径，跳出Agent空间）
  内容:
    - 小区数据、版本历史、生成文档
  生命周期: 永久
  访问: Agent A + Agent B + Future Agents
```

### 4.2 跨Session协作示例

```
Session 1 (Agent A):
  用户: "去蓝光雍锦世家驻点"
  Agent A采集数据，保存到 ../field-data/communities/蓝光雍锦世家/2026-03/
  Session结束

Session 2 (Agent B):
  用户: "查看蓝光雍锦世家的报告"
  Agent B读取 ../field-data/communities/蓝光雍锦世家/
  生成报告
  Session结束

Session 3 (Agent A):
  用户: "继续上次的工作"
  Agent A读取 ../field-data/communities/蓝光雍锦世家/2026-03/work-record.md
  继续采集
```

---

## 五、可扩展性设计（预留规划Agent）

### 5.1 未来Agent：现场工作计划规划Agent (field-planner)

**预留接口**:
```yaml
# 在global-config.yaml中预留
future_agents:
  field-planner:
    role: planner
    capabilities:
      - schedule_planning      # 排程规划
      - route_optimization     # 路线优化
      - resource_allocation    # 资源分配
      - workload_prediction    # 工作量预测
    
    shared_workspace:
      path: "../field-data"
      permissions:
        - read: "communities/**"
        - write: "planning/**"    # 预留规划目录
    
    integration:
      - read_from: [field-collector]    # 读取采集数据
      - write_to: [field-collector]     # 输出计划给采集Agent
```

### 5.2 预留目录结构

```
field-data/
├── ...
└── planning/                          # ⭐ 预留规划目录
    ├── schedules/                     # 排程计划
    ├── routes/                        # 路线规划
    └── predictions/                   # 预测数据
```

### 5.3 Agent协作扩展

```
未来工作流:

field-planner (规划Agent)
    ↓ 生成周计划
"本周需要走访3个小区，最优路线：A→B→C"
    ↓
field-collector (采集Agent)
    ↓ 按计划执行
完成3个小区采集
    ↓
field-reporter (报告Agent)
    ↓ 生成周报告
"本周完成情况：3/3，发现问题5个"
    ↓
field-planner (规划Agent)
    ↓ 优化下周计划
基于本周数据，优化下周路线
```

---

## 六、实施路线图

### Phase 1: 共享工作空间搭建（1-2周）

1. 创建 `../field-data/` 目录结构
2. 实现版本管理基础（versions/目录）
3. 创建全局配置文件

### Phase 2: Agent A实现（2-3周）

1. 创建 `workspace-field-collector/`
2. 编写AGENTS.md（采集Agent）
3. 实现4个Skills
4. 测试版本管理功能

### Phase 3: Agent B实现（2-3周）

1. 创建 `workspace-field-reporter/`
2. 编写AGENTS.md（报告Agent）
3. 实现4个Skills
4. 测试跨Agent协作

### Phase 4: 集成测试（1-2周）

1. 双Agent协作测试
2. 版本管理测试
3. 权限控制测试
4. 预留接口验证

---

**下一步**：开始Phase 1的具体实现？