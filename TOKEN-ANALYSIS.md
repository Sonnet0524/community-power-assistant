# 扁平化设计的Token消耗分析

> 💰 成本与性能评估

## 一、当前Token消耗估算

### 1.1 当前AGENTS.md（386行）

```bash
文件大小: 14,789 字节
行数: 386 行
字符数: ~15,000
```

**Token估算**（混合中英文）：
- 平均 1 token ≈ 3.5 字符（中文密集）
- **当前AGENTS.md ≈ 4,200 tokens**

### 1.2 扁平化后的AGENTS.md（预计）

```yaml
预计行数: 600 行（取中间值）
预计字符: ~25,000

内容增加:
  - Skill: Photo Collection: +3,000 字符（路径构造逻辑）
  - Skill: Doc Generation: +2,500 字符（引用验证逻辑）
  - Session管理: +1,500 字符（数据隔离逻辑）
  - 数据存储规则: +2,000 字符（权限控制）
  - 其他优化: +1,500 字符
  
总计增加: ~10,500 字符
```

**Token估算**:
- **扁平化AGENTS.md ≈ 7,000-8,000 tokens**

### 1.3 Token增长对比

| 版本 | 大小 | Tokens | 增长 |
|------|------|--------|------|
| **当前** | 15KB | ~4,200 | baseline |
| **扁平化** | 25KB | ~7,000 | +67% |

---

## 二、成本影响分析

### 2.1 每次对话的Token消耗

**OpenClaw/Claude Code的工作方式**:
```
每次用户消息:
1. 加载 AGENTS.md (system prompt)
2. 加载 conversation history
3. 接收 user message
4. 生成 assistant response
```

**Token构成**:
```
Input tokens:
  - AGENTS.md: 7,000 (扁平化后)
  - History (最近5轮): ~2,000
  - User message: ~100
  = Total input: ~9,100 tokens

Output tokens:
  - Assistant response: ~500
  = Total output: ~500 tokens

Total per conversation: ~9,600 tokens
```

### 2.2 成本计算

**以Kimi K2.5价格为例**（参考）：
```
输入: ¥0.01 / 1K tokens
输出: ¥0.02 / 1K tokens
```

**单次对话成本**:
```
Input: 9,100 tokens × ¥0.01/1K = ¥0.091
Output: 500 tokens × ¥0.02/1K = ¥0.01
Total: ~¥0.10 per conversation
```

**对比传统多文件方案**:
```
传统方案 AGENTS.md: 4,200 tokens
Input: 6,300 tokens × ¥0.01/1K = ¥0.063
Output: 500 tokens × ¥0.02/1K = ¥0.01
Total: ~¥0.073 per conversation

扁平化增加成本: ¥0.10 - ¥0.073 = ¥0.027 per conversation (+37%)
```

### 2.3 月度成本估算

**假设使用频率**:
```
每日使用: 50次对话（5个客户经理 × 10次）
每月使用: 1,500次对话

扁平化月度成本: 1,500 × ¥0.10 = ¥150/月
传统方案月度成本: 1,500 × ¥0.073 = ¥110/月

月度增加: ¥40/月
```

---

## 三、性能影响

### 3.1 延迟增加

**Token处理延迟**（估算）：
```
处理 1K tokens ≈ 100-200ms

AGENTS.md加载时间:
  - 当前 (4.2K tokens): ~600ms
  - 扁平化 (7K tokens): ~1,000ms
  
增加延迟: ~400ms per conversation
```

**用户体验影响**:
- 首次回复延迟增加 0.4秒
- 对用户体验影响不大（可接受）

### 3.2 Context Window占用

**Kimi K2.5 Context Window**: 200K tokens

**占用比例**:
```
扁平化AGENTS.md: 7K / 200K = 3.5%
剩余可用: 193K tokens (足够长对话)

结论: Context Window 不是瓶颈
```

---

## 四、优化方案

### 4.1 方案A: 智能分段加载（推荐）

**核心思想**: 不一次性加载完整AGENTS.md，按需加载

**实现方式**:
```yaml
# AGENTS.md 结构优化

---
metadata:
  # 核心配置（必须加载）
  core_config:
    name: wuhou-field-worker
    identity: ...
    
  # Skills声明，但内容按需加载
  skills:
    - name: photo-collection
      lazy_load: true           # ⭐ 延迟加载
      trigger_keywords: ["照片", "拍照", "图片"]
      content_section: "Skill_Photo_Collection"
    
    - name: doc-generation
      lazy_load: true
      trigger_keywords: ["简报", "文档", "生成"]
      content_section: "Skill_Doc_Generation"
    
    - name: grid-field-work
      lazy_load: false          # 核心Skill，立即加载
      content_section: "Skill_Grid_Field_Work"
```

**工作方式**:
```
用户: "我要拍照"
  ↓
OpenClaw检测trigger_keywords: ["拍照"]
  ↓
动态加载 Skill_Photo_Collection 章节
  ↓
本次对话token: 4,000 (core) + 2,000 (photo skill) = 6,000 tokens
```

**效果**:
- 平均每次对话加载: 5,000-6,000 tokens
- 成本降低至: ¥0.08 per conversation
- 比扁平化节省: 20%

### 4.2 方案B: 分层AGENTS（折中）

**核心思想**: 拆分为2个文件，平衡效率和token

```
AGENTS.md (核心，短文件)
├── Identity & Session (2,000 tokens)
├── Core Workflow (1,500 tokens)
└── Skill加载器声明

AGENTS-SKILLS.md (Skills，按需引用)
├── Skill: Photo Collection
├── Skill: Doc Generation
└── ...
```

**工作方式**:
```yaml
metadata:
  skills:
    - name: photo-collection
      external: true
      file: "AGENTS-SKILLS.md"
      section: "Skill_Photo_Collection"
```

**效果**:
- 基础对话: 3,500 tokens
- Skill对话: +2,000 tokens
- 平均: 5,500 tokens
- 成本: ¥0.085 per conversation

### 4.3 方案C: 内存缓存（技术优化）

**核心思想**: AGENTS.md只在首次加载，后续复用

**OpenClaw可能已实现的优化**:
```
首次对话:
  1. 读取AGENTS.md (7,000 tokens)
  2. 缓存到内存
  3. 后续对话复用缓存

后续对话:
  1. 从内存读取AGENTS (0 I/O, 快)
  2. 只计算input tokens (不重新加载)
```

**效果**:
- I/O减少，速度提升
- Token计算成本不变（按API收费）

### 4.4 方案D: 精简关键逻辑（内容优化）

**核心思想**: 压缩AGENTS.md内容，保留关键逻辑

**精简策略**:
```markdown
## Skill: Photo Collection (精简版)

### 核心逻辑
```javascript
// 路径构造（伪代码）
path = `field-data/communities/${community}/${month}/photos/`;
filename = `IMG_${timestamp}_${seq}.jpg`;
save(image, path + filename);
verify_exists(path + filename);
```

### 错误处理
- 路径错误: 自动修正
- 保存失败: 重试3次
- AI失败: 人工标注
```

**精简效果**:
- 从 3,000 字符 → 1,500 字符
- 保持核心逻辑完整
- Token节省: 50%

---

## 五、推荐方案

### 5.1 综合评估

| 方案 | Token/次 | 成本/次 | 开发效率 | 维护难度 | 推荐度 |
|------|---------|---------|----------|----------|--------|
| **纯扁平化** | 7,000 | ¥0.10 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 可选 |
| **智能分段** | 5,500 | ¥0.08 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐推荐 |
| **分层AGENTS** | 5,500 | ¥0.085 | ⭐⭐⭐ | ⭐⭐⭐ | 可选 |
| **内存缓存** | 7,000 | ¥0.10 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 依赖OpenClaw |
| **精简内容** | 5,000 | ¥0.075 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐推荐 |

### 5.2 最终推荐: 方案A + 方案D 组合

**智能分段 + 内容精简**:

```yaml
# AGENTS.md 结构

---
metadata:
  # 核心（始终加载）: ~3,000 tokens
  identity: ...
  session_rules: ...
  core_workflow: ...
  
  # Skills（延迟加载）
  skills:
    - name: photo-collection
      lazy_load: true
      trigger: ["照片", "拍照"]
      # 精简内容: ~1,500 tokens
      
    - name: doc-generation
      lazy_load: true
      trigger: ["简报", "文档"]
      # 精简内容: ~1,200 tokens

---

# 正文: 核心内容（3,000 tokens）
## Identity
...

## Session管理
...

## Core Workflow
...

# Skill详细内容（按需加载）
## Skill_Photo_Collection
精简版路径构造逻辑...

## Skill_Doc_Generation
精简版引用验证逻辑...
```

**预期效果**:
- 平均token: 5,000 per conversation
- 成本: ¥0.075 per conversation
- 开发效率: 保持扁平化优势
- 比纯扁平化节省: 25%

---

## 六、实施建议

### Phase 1: 先实施纯扁平化（验证）

1. 创建完整扁平化AGENTS.md（7,000 tokens）
2. 测试1周，监控token使用量
3. 评估实际成本

### Phase 2: 优化（根据实际数据）

如果成本过高:
1. 实施智能分段加载
2. 精简Skill内容
3. 目标降至5,000 tokens/次

---

## 七、总结

### Token消耗结论

| 指标 | 数值 | 评估 |
|------|------|------|
| 扁平化AGENTS.md | 7,000 tokens | 可接受 |
| 单次对话成本 | ¥0.10 | 比传统+37% |
| 月度成本增加 | ¥40 | 可接受 |
| Context占用 | 3.5% | 无压力 |

### 建议

**可以接受纯扁平化**，因为:
1. ¥40/月成本增加在可接受范围
2. 60%开发效率提升值得这个成本
3. Context Window充足（3.5%占用）

**或者采用优化方案**:
- 智能分段 + 内容精简
- Token降至5,000，成本¥0.075
- 兼顾效率和成本

---

**您的选择**?
1. **纯扁平化**（¥0.10/次，最高效率）
2. **智能分段**（¥0.08/次，平衡方案）
3. **先实施再优化**（实施扁平化，根据数据调整）
