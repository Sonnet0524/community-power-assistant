# AGENTS + SKILLS 两层架构设计

> 🏗️ 清晰的职责分离：AGENTS定规范，SKILLS做执行

## 一、架构原则

```
AGENTS.md（规范层）
├── 任务描述：做什么
├── 规范要求：怎么做（标准）
├── 文档结构：数据怎么存
├── 红线边界：什么不能做
└── 协调调度：调用哪个SKILL

SKILLS/（执行层）
├── grid-field-work/：具体执行现场工作
├── photo-collection/：具体执行照片处理
├── doc-generation/：具体执行文档生成
└── info-retrieval/：具体执行信息检索
```

## 二、AGENTS.md 职责（规范层）

### 2.1 内容范围（300-400行）

```markdown
---
metadata配置...
---

# 身份与核心职责
# Session管理规范
# 文档结构规范（数据怎么存）
# 红线与边界
# Skills调用协调
```

### 2.2 具体内容

**包含**：
- ✅ Agent身份定义（武侯供电中心客户经理AI助手）
- ✅ Session变量规范（current_community等）
- ✅ 文件存储规范（路径、命名、格式）
- ✅ 数据隔离规则（Session校验逻辑）
- ✅ 红线边界（隐私保护、服务范围）
- ✅ Skill触发条件（什么时候调用哪个Skill）

**不包含**：
- ❌ 具体的Skill执行逻辑（移到SKILL.md）
- ❌ 详细的路径构造代码（移到SKILL.md）
- ❌ 具体的AI分析prompt（移到SKILL.md）

## 三、SKILLS 职责（执行层）

### 3.1 每个SKILL的内容（100-200行）

```markdown
SKILL.md
├── 触发条件（继承AGENTS声明）
├── 输入参数
├── 执行逻辑（具体怎么做）
├── 输出结果
└── 错误处理
```

### 3.2 四个SKILL的分工

| SKILL | 核心职责 | AGENTS协调 | 具体执行 |
|-------|---------|-----------|----------|
| **grid-field-work** | 驻点工作全流程引导 | AGENTS声明触发词 | SKILL实现5项清单流程 |
| **photo-collection** | 照片采集与AI分析 | AGENTS声明路径规范 | SKILL实现路径构造+保存+分析 |
| **doc-generation** | 文档自动生成 | AGENTS声明模板位置 | SKILL实现模板填充+生成 |
| **info-retrieval** | 信息检索查询 | AGENTS声明检索范围 | SKILL实现检索逻辑+格式化 |

## 四、两层协作流程

### 4.1 照片采集场景

```
用户发送照片
    ↓
OpenClaw接收消息
    ↓
AGENTS.md判断：
  - message_type == "image"
  - session.state == "collecting"
  → 应该调用 photo-collection SKILL
    ↓
AGENTS传递上下文给SKILL：
  - current_community: "蓝光雍锦世家"
  - current_month: "2026-03"
  - storage_rules: {path_template, naming_format}
    ↓
photo-collection SKILL执行：
  1. 读取AGENTS传递的规范
  2. 构造路径（使用AGENTS的path_template）
  3. 保存照片
  4. AI分析
  5. 更新work-record.md
  6. 返回结果给AGENTS
    ↓
AGENTS接收结果，生成用户回复
```

### 4.2 职责边界

| 步骤 | AGENTS职责 | SKILL职责 |
|------|-----------|-----------|
| 触发判断 | ✅ 判断应该调用哪个SKILL | ❌ 不处理 |
| 上下文准备 | ✅ 准备Session变量、规范 | ❌ 不处理 |
| 路径构造 | ❌ 只提供模板 | ✅ 具体构造路径 |
| 文件保存 | ❌ 只规范要求 | ✅ 执行保存 |
| AI分析 | ❌ 只声明模型 | ✅ 调用API分析 |
| 错误处理 | ❌ 只声明规则 | ✅ 具体处理错误 |
| 返回用户 | ✅ 生成回复话术 | ❌ 返回结构化结果 |

## 五、当前Skills评估

### 5.1 当前问题

当前的Skills都是**symlink到系统目录**：
```
skills/photo-collection -> /usr/lib/node_modules/openclaw/skills/photo-collection
```

**问题**：
- ❌ 无法修改（只读）
- ❌ 无法查看源码
- ❌ 无法修复01号路径Bug

### 5.2 需要的改造

**改造为本地SKILL**：
```
skills/
├── grid-field-work/
│   └── SKILL.md          # 本地实现，可修改
├── photo-collection/
│   └── SKILL.md          # 本地实现，修复01号Bug
├── doc-generation/
│   └── SKILL.md          # 本地实现，修复07号Bug
└── info-retrieval/
    └── SKILL.md          # 本地实现
```

## 六、模拟业务流程

### 场景1：完整的驻点工作流程

```
【开始】
用户: "我要去蓝光雍锦世家驻点"

【AGENTS处理 - 协调层】
AGENTS.md:
  1. 触发词匹配："去.*小区驻点" → 调用 grid-field-work
  2. Session准备：
     - current_community = "蓝光雍锦世家"
     - current_month = "2026-03"
  3. 读取规范：
     - storage.path_template
     - field_grading.P0_fields
  4. 调用 grid-field-work SKILL

【grid-field-work SKILL - 执行层】
SKILL执行：
  1. 获取AGENTS传递的context
  2. 文字确认小区名："请文字输入确认：蓝光雍锦世家"
  3. 文字确认工作人员："请文字输入工作人员姓名："
  4. 生成5项检查清单
  5. 返回给AGENTS：清单内容 + 当前状态

【AGENTS返回用户】
"已准备蓝光雍锦世家驻点工作...
检查清单：
1. 小区基本情况
2. 进网入格
3. 供配电方案
4. 应急保电方案
5. 用电检查隐患台账"

【用户开始采集】
用户: [发送小区大门照片]

【AGENTS处理】
AGENTS.md:
  1. 消息类型：image
  2. Session状态：collecting
  3. 当前小区：蓝光雍锦世家
  4. 调用 photo-collection SKILL

【photo-collection SKILL - 执行层】
SKILL执行（修复01号Bug）：
  1. 读取AGENTS传递的规范：
     - path_template: "field-data/communities/{community}/{month}/photos/"
  2. 构造路径：
     - community = "蓝光雍锦世家" (from AGENTS context)
     - month = "2026-03" (from AGENTS context)
     - path = "field-data/communities/蓝光雍锦世家/2026-03/photos/"
  3. 创建目录（如果不存在）
  4. 生成文件名：IMG_20260328_143022_01.jpg
  5. 保存照片到正确路径
  6. 验证文件存在
  7. 调用Kimi AI分析
  8. 更新work-record.md
  9. 返回结果给AGENTS

【AGENTS返回用户】
"📸 照片已保存：IMG_20260328_143022_01.jpg
AI分析：小区大门，名称清晰可见。
请继续拍摄公示栏照片。"

【继续采集...】
...

【完成采集】
用户: "完成采集"

【AGENTS处理】
AGENTS.md:
  1. 触发词："完成采集"
  2. 调用 doc-generation SKILL

【doc-generation SKILL - 执行层】
SKILL执行（修复07号Bug）：
  1. 读取AGENTS传递的规范：
     - template_path: "field-data/templates/"
     - verify_photo_exists: true
  2. 列出实际照片目录：
     ls field-data/communities/蓝光雍锦世家/2026-03/photos/
     → 返回实际文件名列表
  3. 读取work-record.md数据
  4. 填充模板
  5. 验证所有照片引用存在于列表中（不编造）
  6. 生成供电简报.md
  7. 返回给AGENTS

【AGENTS返回用户】
"✅ 驻点工作完成！
📄 供电简报已生成：[下载链接]
📊 本次采集：8张照片，5项检查"

【结束】
```

## 七、两层架构的Token优化

### 7.1 分层加载策略

```yaml
AGENTS.md（始终加载）：3,000 tokens
  - 身份与核心职责
  - Session管理规范
  - 文档结构规范
  - 红线与边界
  - Skills触发条件

SKILL.md（按需加载）：2,000 tokens/次
  - 只加载被触发的Skill
  - 不加载其他Skill
```

### 7.2 Token节省效果

**传统扁平化**：
- 一次性加载：7,000 tokens

**两层架构**：
- 基础：3,000 tokens (AGENTS)
- Skill：2,000 tokens (按需)
- **平均：5,000 tokens**
- **节省：30%**

## 八、实施建议

### 8.1 AGENTS.md 内容（350行）

```markdown
---
metadata配置（标准OpenClaw格式）
---

## 身份与核心职责（30行）
## Session管理规范（40行）
## 文档结构规范（50行）
## 红线与边界（40行）
## Skills调用协调（150行）
  - grid-field-work: 触发条件、传递参数
  - photo-collection: 触发条件、路径规范、命名规范
  - doc-generation: 触发条件、模板位置、验证规则
  - info-retrieval: 触发条件、检索范围
```

### 8.2 四个SKILL.md 内容（各150行）

每个SKILL：
```markdown
---
SKILL metadata
---

## 触发条件
## 输入参数
## 执行逻辑（100行，具体实现）
  - 读取AGENTS规范
  - 具体执行步骤
  - 错误处理
## 输出结果
```

## 九、总结

### 9.1 架构优势

1. **职责清晰**：AGENTS定规范，SKILLS做执行
2. **Token优化**：按需加载Skill，节省30%
3. **易于维护**：修改Skill不影响AGENTS规范
4. **问题修复**：本地Skill可修改，修复01/07号Bug

### 9.2 当前Skills评估结论

| 评估项 | 当前状态 | 是否需要改造 |
|--------|---------|-------------|
| 数量 | 4个，合适 | 不需要增减 |
| 分工 | 合理 | 不需要调整 |
| 实现方式 | Symlink（问题）| ✅ 需要改为本地 |
| 内容质量 | 未知（看不到源码）| 需要重写 |

**结论**：
- ✅ 保留4个Skills的分工
- ❌ 必须改为本地实现（不是symlink）
- ✅ 按照两层架构重写内容

---

**下一步**：
1. 开始编写AGENTS.md（规范层）
2. 创建本地Skills目录
3. 编写4个SKILL.md（执行层）