---
name: station-work-guide
description: 驻点工作引导Skill，支持配电房巡检、客户走访、应急信息采集三种工作类型
homepage: https://github.com/openclaw/field-info-agent
metadata:
  {"openclaw": {"emoji": "🛠️", "requires": {"env": ["KIMI_API_KEY"], "config": ["skills.station_work_guide"]}, "install": []}}
---

# StationWorkGuide - 驻点工作引导

## 概述

StationWorkGuide 是一个面向供电所现场工作人员的智能引导 Skill。它通过对话式交互，帮助用户完成三种类型的现场工作：

1. **配电房巡检** - 标准化设备巡检流程
2. **客户走访** - 客户需求收集和满意度调查
3. **应急信息采集** - 应急情况快速信息采集

## 状态机设计

```
┌─────────┐    选择类型     ┌───────────┐
│  IDLE   │ ─────────────▶ │ PREPARING │
└─────────┘                └───────────┘
                                │
                                │ 开始
                                ▼
┌──────────┐   完成采集   ┌───────────┐
│ ANALYZING │ ◀────────── │ COLLECTING │
└──────────┘              └───────────┘
      │                          │
      │ 生成报告                 │ 跳过/完成
      ▼                          ▼
┌───────────┐              ┌───────────┐
│ COMPLETED │ ◀─────────── │  (loop)   │
└───────────┘              └───────────┘
```

## 使用方法

### 1. 启动工作

用户发送任意消息或特定关键词启动：

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

```
用户: 1
系统: 您选择了：配电房巡检
      
      配电房设备巡检和安全检查
      
      请确认是否开始？发送"开始"继续
```

### 3. 准备阶段

```
系统: 📋 配电房巡检 - 准备清单
      
      请确认已准备以下物品：
      □ 安全帽、绝缘手套
      □ 巡检记录表
      □ 测温仪
      □ 相机/手机
      
      ✅ 准备好后发送"开始"进入采集阶段
```

### 4. 信息采集

```
系统: (1/5) 基本信息
      
      请拍摄配电房外观照片，并告诉我：
      1. 配电房名称/编号
      2. 所属小区/单位
      
      💡 提示：发送照片和文字信息，完成后发送"下一步"
      
用户: [发送照片]
系统: (2/5) 变压器铭牌
      
      请拍摄变压器铭牌照片，系统将自动识别型号、容量等信息。
      
      💡 提示：请确保铭牌清晰可见，光线充足
```

### 5. AI 自动分析

当用户上传需要 AI 分析的照片时，系统自动调用 KIMI 进行分析：

```python
# 变压器铭牌识别
analysis = await kimi_tool.analyze_image(
    photo_url,
    analysis_type="nameplate"
)
# 返回: {"model": "S11-M-800/10", "capacity": "800", ...}

# 安全隐患识别  
analysis = await kimi_tool.analyze_image(
    photo_url,
    analysis_type="safety"
)
# 返回: {"risks": ["通道堵塞"], "severity": "medium", ...}
```

### 6. 完成工作

```
系统: ✅ 配电房巡检完成！数据已保存，分析报告已生成。
      
      📋 采集数据摘要：
      ✓ 基本信息: 2张照片
      ✓ 变压器铭牌: AI分析完成
      ✓ 设备状态: 3张照片
      ✓ 安全环境: AI分析完成
      ✓ 巡检结论: 设备运行正常...
      
      💾 数据已保存到数据库
      📄 报告已生成：/reports/work-xxx.pdf
      
      发送"1"开始新的工作
```

## 数据存储

### PostgreSQL Schema

```sql
-- 工作记录表
CREATE TABLE station_work_records (
    id UUID PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    work_type VARCHAR(32) NOT NULL,
    phase VARCHAR(32) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    summary JSONB,
    report_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 采集数据明细表
CREATE TABLE collection_data (
    id UUID PRIMARY KEY,
    work_id UUID REFERENCES station_work_records(id),
    step INTEGER NOT NULL,
    step_name VARCHAR(128),
    data_type VARCHAR(32),
    content TEXT,
    photos JSONB,
    ai_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### MinIO 存储

- 照片存储路径: `station-work/{work_id}/photos/`
- 报告存储路径: `station-work/{work_id}/reports/`

## 配置选项

```yaml
skills:
  station_work_guide:
    enabled: true
    priority: high
    
    config:
      # AI 分析配置
      auto_analyze: true
      analysis_timeout: 30
      
      # 采集配置
      allow_skip_optional: true
      max_photos_per_step: 5
      
      # 存储配置
      save_intermediate: true
      report_format: "pdf"
```

## 全局命令

在任何阶段都可以使用以下命令：

| 命令 | 功能 |
|------|------|
| `帮助` / `help` | 显示帮助信息 |
| `状态` / `status` | 查看当前进度 |
| `取消` / `cancel` | 取消当前工作 |

## 集成说明

### 依赖 Tools

- **PostgreSQL Tool**: 保存工作记录和采集数据
- **KIMI Tool**: AI 照片分析
- **MinIO Tool**: 照片和报告存储

### 依赖配置

```yaml
# 必需的环境变量
env:
  KIMI_API_KEY: "your-kimi-api-key"

# Tools 配置
tools:
  postgresql:
    enabled: true
    config:
      host: "${POSTGRES_HOST}"
      database: "field_agent"
      
  kimi:
    enabled: true
    config:
      api_key: "${KIMI_API_KEY}"
      model: "kimi-k2.5"
      
  minio:
    enabled: true
    config:
      endpoint: "${MINIO_ENDPOINT}"
      bucket: "field-agent"
```

## 示例代码

### Python 调用

```python
from src.skills.station_work_guide import StationWorkGuideSkill
from src.skills.base import SkillContext

# 初始化 Skill
skill = StationWorkGuideSkill(
    pg_tool=postgresql_tool,
    kimi_tool=kimi_tool,
    minio_tool=minio_tool
)

# 创建上下文
context = SkillContext(
    session_id="sess_123",
    user_id="user_456",
    message="1",  # 选择配电房巡检
    session={"phase": "idle"}
)

# 调用 Skill
result = await skill.invoke(context)
print(result.response)
```

### 模拟用户交互

```python
# 完整工作流程示例
session = {"phase": "idle"}

# 1. 启动
result = await skill.invoke(SkillContext(
    session_id="test", user_id="u1",
    message="开始", session=session
))

# 2. 选择工作类型
result = await skill.invoke(SkillContext(
    session_id="test", user_id="u1",
    message="1", session=session
))

# 3. 确认开始
result = await skill.invoke(SkillContext(
    session_id="test", user_id="u1",
    message="开始", session=session
))

# 4. 采集数据
result = await skill.invoke(SkillContext(
    session_id="test", user_id="u1",
    message="1号配电房，阳光小区",
    session=session,
    metadata={"photos": ["http://minio/photo1.jpg"]}
))

# 5. 完成所有步骤后
result = await skill.invoke(SkillContext(
    session_id="test", user_id="u1",
    message="完成", session=session
))
```

## 错误处理

### 常见错误

| 错误 | 说明 | 处理建议 |
|------|------|----------|
| work_type_not_set | 工作类型未设置 | 返回 IDLE 阶段重新选择 |
| invalid_work_type | 无效的工作类型 | 提示用户重新选择 |
| ai_analysis_failed | AI 分析失败 | 保存原始数据，继续流程 |
| database_error | 数据库错误 | 记录日志，不中断用户体验 |

### 错误响应示例

```python
SkillResult(
    response="⚠️ 工作类型未设置，请重新开始",
    status=SkillResultStatus.ERROR,
    next_phase=WorkPhase.IDLE.value,
    error="work_type_not_set"
)
```

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-03-20 | 初始版本，支持三种工作类型 |

## 维护信息

- **作者**: Field Core Team
- **维护者**: PM Agent
- **测试覆盖率**: >90%
- **状态**: ✅ 已验收
