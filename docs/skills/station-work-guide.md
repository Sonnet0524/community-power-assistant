# StationWorkGuide Skill 使用文档

## 概述

StationWorkGuide 是 Field Info Agent 的核心 Skill 之一，为供电所现场工作人员提供智能化的工作引导。通过对话式交互，帮助用户标准化完成现场信息采集工作。

## 功能特性

- ✅ **三种工作类型**：配电房巡检、客户走访、应急信息采集
- ✅ **完整状态机**：IDLE → PREPARING → COLLECTING → ANALYZING → COMPLETED
- ✅ **AI 智能分析**：自动识别变压器铭牌、检测安全隐患
- ✅ **数据持久化**：自动保存到 PostgreSQL
- ✅ **照片管理**：集成 MinIO 存储
- ✅ **全局命令**：随时查看帮助、状态或取消工作

## 快速开始

### 1. 启动 Skill

用户发送任意消息触发：

```
用户: 开始工作
系统: 👋 您好！我是驻点工作助手。
      
      我可以帮助您完成以下工作：
      1️⃣ 配电房巡检
      2️⃣ 客户走访  
      3️⃣ 应急信息采集
      
      请发送数字（1/2/3）或关键词开始工作。
```

### 2. 选择工作类型

支持多种选择方式：

```
用户: 1
或
用户: 配电房
或
用户: 配电房巡检
```

### 3. 跟随引导完成工作

系统会按步骤引导您：
1. **准备阶段** - 显示检查清单
2. **采集阶段** - 逐步骤采集信息
3. **分析阶段** - AI 自动分析
4. **完成阶段** - 生成报告

## 工作类型详解

### 配电房巡检

**适用场景**：定期设备巡检、安全检查

**采集步骤**：
1. **基本信息** - 配电房名称、所属单位
2. **变压器铭牌** - 拍摄铭牌，AI 自动识别型号和容量
3. **设备状态** - 高压柜、低压柜、变压器外观
4. **安全环境** - 通道、消防设施、通风情况
5. **巡检结论** - 总结和建议

**AI 分析能力**：
- 🔍 变压器铭牌识别（型号、容量、制造商）
- ⚠️ 安全隐患检测（通道堵塞、消防问题）

### 客户走访

**适用场景**：定期客户拜访、满意度调查

**采集步骤**：
1. **客户信息** - 户名、地址、联系方式
2. **用电情况** - 稳定性、停电记录
3. **业务需求** - 增容、改类、新装需求
4. **意见建议** - 服务反馈
5. **走访小结** - 总结和跟进事项

**特点**：
- 支持语音输入（用于走访记录）
- 部分步骤可选

### 应急信息采集

**适用场景**：突发故障、应急抢修

**采集步骤**：
1. **基本情况** - 故障地点、现象、影响范围
2. **现场照片** - 多角度现场记录
3. **初步处理** - 已采取的应急措施
4. **后续安排** - 处理计划和人员安排

**特点**：
- 快速采集流程（仅4步）
- 所有步骤必填
- AI 安全分析优先

## 全局命令

在任何阶段都可以使用：

| 命令 | 别名 | 功能 |
|------|------|------|
| `帮助` | help, ? | 显示操作指南 |
| `状态` | status | 查看当前进度 |
| `取消` | cancel, 退出, quit | 取消当前工作 |

## 采集阶段操作

### 基本操作

```
发送照片/文字    - 完成当前步骤
下一步/next     - 确认并继续
上一步/prev     - 返回修改
跳过/skip       - 跳过当前步骤（仅限可选步骤）
```

### 照片上传

照片可以单独发送，也可以配合文字：

```
用户: [发送照片]
系统: ✓ 照片已接收

用户: 1号配电房外观，位于阳光小区
系统: ✓ 信息已记录，自动进入下一步
```

### AI 自动分析

当步骤标记为需要 AI 分析时，上传照片后会自动触发：

```
用户: [发送变压器铭牌照片]
系统: [后台自动分析...]
      
      ✓ AI分析完成
      识别结果：
      - 型号：S11-M-800/10
      - 容量：800kVA
      - 制造商：XX变压器厂
      
      (2/5) 设备状态
      请拍摄主要设备照片...
```

## 状态流转图

```
┌─────────┐
│  IDLE   │ ◀────────────────────────────┐
└────┬────┘                              │
     │ 选择工作类型                        │
     ▼                                    │
┌───────────┐                            │
│ PREPARING │                            │
└─────┬─────┘                            │
      │ 开始采集                          │
      ▼                                    │
┌───────────┐   完成所有步骤   ┌───────────┐   完成分析   ┌───────────┐
│ COLLECTING │ ──────────────▶ │ ANALYZING │ ──────────▶ │ COMPLETED │
└───────────┘                └───────────┘            └─────┬─────┘
      │                                                    │
      │ 取消/完成                                           │ 开始新工作
      └────────────────────────────────────────────────────┘
```

## 数据存储

### PostgreSQL 表结构

```sql
-- 工作记录
CREATE TABLE station_work_records (
    id UUID PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    work_type VARCHAR(32) NOT NULL,
    phase VARCHAR(32) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    summary JSONB,
    report_url VARCHAR(512)
);

-- 采集数据明细
CREATE TABLE collection_data (
    id UUID PRIMARY KEY,
    work_id UUID REFERENCES station_work_records(id),
    step INTEGER NOT NULL,
    step_name VARCHAR(128),
    data_type VARCHAR(32),
    content TEXT,
    photos JSONB,
    ai_result JSONB
);
```

### MinIO 存储路径

```
station-work/
├── {work_id}/
│   ├── photos/
│   │   ├── step_1_photo_1.jpg
│   │   └── step_2_photo_1.jpg
│   └── reports/
│       └── report.pdf
```

## API 使用示例

### Python 调用

```python
from src.skills.station_work_guide import StationWorkGuideSkill
from src.skills.base import SkillContext

# 初始化
skill = StationWorkGuideSkill(pg_tool, kimi_tool, minio_tool)

# 创建上下文
context = SkillContext(
    session_id="sess_123",
    user_id="user_456",
    message="1",  # 选择配电房巡检
    session={"phase": "idle"}
)

# 调用
result = await skill.invoke(context)
print(result.response)
```

### 完整工作流程

```python
async def demo_workflow():
    skill = StationWorkGuideSkill()
    session = {"phase": "idle"}
    
    # 1. 启动
    result = await skill.invoke(SkillContext(
        session_id="demo", user_id="u1",
        message="开始", session=session
    ))
    print(result.response)
    
    # 2. 选择配电房巡检
    result = await skill.invoke(SkillContext(
        session_id="demo", user_id="u1",
        message="1", session=session
    ))
    
    # 3. 确认开始
    result = await skill.invoke(SkillContext(
        session_id="demo", user_id="u1",
        message="开始", session=session
    ))
    
    # 4-8. 完成所有采集步骤...
    
    # 9. 完成工作
    result = await skill.invoke(SkillContext(
        session_id="demo", user_id="u1",
        message="完成", session=session
    ))
    print("工作完成！")
```

## 配置选项

### Skill 配置

```yaml
skills:
  station_work_guide:
    enabled: true
    priority: high
    
    config:
      # AI 分析
      auto_analyze: true
      analysis_timeout: 30
      
      # 采集设置
      allow_skip_optional: true
      max_photos_per_step: 5
      
      # 存储
      save_intermediate: true
      report_format: "pdf"
```

### 环境变量

```bash
# KIMI API
KIMI_API_KEY=your-api-key

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_DATABASE=field_agent

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=field-agent
```

## 常见问题

### Q: 可以跳过必填步骤吗？
A: 不可以。系统会提示"【XX】是必填项，不能跳过"。

### Q: 工作中断后如何恢复？
A: 发送任意消息会自动恢复之前的进度。

### Q: AI 分析失败怎么办？
A: 系统会保存原始照片，您可以稍后手动补充信息。

### Q: 支持哪些图片格式？
A: 支持 JPG、PNG 格式，单张不超过 10MB。

### Q: 如何查看历史记录？
A: 发送"状态"可以查看当前进度，完整历史请查看后台系统。

## 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| AI 分析超时 | 网络问题或图片过大 | 检查网络，压缩图片后重试 |
| 数据保存失败 | 数据库连接问题 | 稍后重试，数据会本地缓存 |
| 状态未更新 | 会话过期 | 发送"取消"后重新开始 |
| 照片上传失败 | MinIO 服务异常 | 检查 MinIO 状态 |

## 更新日志

### v1.0.0 (2026-03-20)
- ✅ 初始版本发布
- ✅ 支持三种工作类型
- ✅ 完整状态机实现
- ✅ KIMI AI 分析集成
- ✅ PostgreSQL/MinIO 存储

## 相关文档

- [SKILL.md](../../knowledge-base/field-info-agent/implementation/skills/station-work-guide/SKILL.md) - Skill 定义规范
- [test_station_work_guide.py](../../tests/skills/test_station_work_guide.py) - 单元测试
- [API 文档](../api/README.md) - API 详细文档

---

**维护者**: Field Core Team  
**最后更新**: 2026-03-20
