---
name: emergency-guide
description: 应急处置Skill，提供应急方案推送和现场处置指引
homepage: https://github.com/community-power-assistant/emergency-guide
metadata:
  {"openclaw":{"emoji":"🚨","requires":{"bins":[],"env":["KIMI_API_KEY"],"config":["emergency_guide"]},"install":[]}}
---

# EmergencyGuide Skill - 应急处置

## 概述

EmergencyGuide Skill 是 Field Info Agent 的核心技能之一，专门用于电力系统应急事件的快速响应和处置。该 Skill 能够：

- **智能识别** 4 种应急类型
- **自动识别** 敏感客户并发送关怀消息
- **自动生成** 应急方案和处理指引
- **自动通知** 相关责任人和部门
- **自动生成** 应急处理文档

## 支持的应急类型

| 类型 | 名称 | 严重程度级别 | 自动响应 |
|------|------|-------------|----------|
| `power_outage` | 停电故障 | 一般、较大、重大 | ✅ |
| `equipment_fault` | 设备故障 | 一般、严重、危急 | ✅ |
| `safety_incident` | 安全事故 | 轻微、一般、重大 | ❌（需人工确认）|
| `customer_complaint` | 敏感客户投诉 | 一般、重要、紧急 | ✅ |

## 使用方法

### 1. 基础调用

```python
from src.skills.emergency_guide import EmergencyGuideSkill, SkillContext

# 初始化 Skill
skill = EmergencyGuideSkill(
    kimi_tool=kimi_tool,      # KIMI Tool 实例
    pg_tool=pg_tool,          # PostgreSQL Tool 实例
    wecom_tool=wecom_tool,    # 企业微信 Tool 实例
    minio_tool=minio_tool     # MinIO Tool 实例
)

# 构建上下文
context = SkillContext(
    params={
        "emergency_type": "power_outage",
        "location": "XX街道XX号配电房",
        "severity": "重大",
        "description": "变压器冒烟，有明火",
        "photos": ["http://minio:9000/photos/1.jpg"]
    },
    user_id="user_001",
    session_id="session_001"
)

# 调用 Skill
result = await skill.invoke(context)

print(result.response)  # 打印响应消息
print(result.data)      # 打印完整数据
```

### 2. 应急类型详解

#### 停电故障 (power_outage)

```python
context = SkillContext(
    params={
        "emergency_type": "power_outage",
        "location": "XX小区配电房",
        "severity": "较大",
        "description": "突降暴雨导致线路跳闸"
    }
)
```

**自动生成的行动方案**：
1. 确认故障范围和原因
2. 启动备用电源（如有）
3. 通知受影响用户
4. 派遣抢修队伍
5. 记录故障时间和现象

#### 设备故障 (equipment_fault)

```python
context = SkillContext(
    params={
        "emergency_type": "equipment_fault",
        "location": "XX变电站",
        "severity": "严重",
        "description": "主变油温异常升高"
    }
)
```

**自动生成的行动方案**：
1. 现场安全检查
2. 隔离故障设备
3. 评估是否需要停电处理
4. 联系设备厂家
5. 准备备用设备

#### 安全事故 (safety_incident)

```python
context = SkillContext(
    params={
        "emergency_type": "safety_incident",
        "location": "XX施工现场",
        "severity": "重大",
        "description": "触电事故，有人员受伤"
    }
)
```

**⚠️ 注意**：安全事故需要**人工确认**后才会启动自动响应。

**自动生成的行动方案**：
1. 确保人员安全
2. 封锁现场
3. 报告上级部门
4. 启动应急预案
5. 联系医疗机构（如有人员受伤）

#### 敏感客户投诉 (customer_complaint)

```python
context = SkillContext(
    params={
        "emergency_type": "customer_complaint",
        "location": "XX医院",
        "severity": "紧急",
        "description": "多次停电导致医疗设备受损"
    }
)
```

**自动生成的行动方案**：
1. 安抚客户情绪
2. 了解详细情况
3. 记录投诉内容
4. 联系相关部门
5. 制定解决方案

### 3. 敏感客户关怀

当应急事件发生时，系统会自动识别该区域的敏感客户并发送关怀消息：

```python
# 敏感客户类型包括：
# - hospital（医院）
# - school（学校）
# - enterprise（重要企业）
# - default（一般重要用户）

# 关怀消息示例（医院）：
"""
🏥 重要通知

XX医院您好：

因XX街道发生停电故障，
您所在的区域可能受到影响。

我们正在紧急处理，预计2-4小时恢复。

医院作为重要用户，如有紧急用电需求，
请联系专属客户经理：138-xxxx-xxxx

深表歉意！
"""
```

### 4. 应急文档生成

系统自动生成应急处理文档，包含：

- 基本信息（事件类型、地点、时间）
- 影响范围评估
- 可能原因分析
- 即时行动清单
- 安全注意事项
- 联系人列表
- 预计处理时间
- 所需资源

## 配置示例

### openclaw.config.yaml

```yaml
skills:
  emergency_guide:
    enabled: true
    priority: high
    
    triggers:
      - type: intent
        patterns:
          - "应急.*处理"
          - ".*故障.*"
          - ".*停电.*"
          - ".*事故.*"
          - ".*投诉.*"
      
      - type: command
        pattern: "启动应急响应"
    
    config:
      auto_notify: true              # 自动通知联系人
      auto_care_message: true        # 自动发送关怀消息
      doc_generation: true           # 生成应急文档
      care_message_delay: 0          # 关怀消息延迟（秒）
      progress_update_interval: 1800 # 进展更新间隔（秒，默认30分钟）

tools:
  kimi:
    enabled: true
    config:
      api_key: "${KIMI_API_KEY}"
      model: "kimi-for-coding"
  
  postgresql:
    enabled: true
    config:
      host: "${POSTGRES_HOST}"
      port: 5432
      database: "field_info"
      user: "${POSTGRES_USER}"
      password: "${POSTGRES_PASSWORD}"
  
  wecom:
    enabled: true
    config:
      corp_id: "${WECOM_CORP_ID}"
      corp_secret: "${WECOM_CORP_SECRET}"
      agent_id: "${WECOM_AGENT_ID}"
  
  minio:
    enabled: true
    config:
      endpoint: "${MINIO_ENDPOINT}"
      access_key: "${MINIO_ACCESS_KEY}"
      secret_key: "${MINIO_SECRET_KEY}"
      bucket: "emergency-docs"
```

## API 参考

### SkillContext

```python
@dataclass
class SkillContext:
    params: Dict[str, Any]        # 输入参数
    user_id: Optional[str]        # 用户ID
    session_id: Optional[str]     # 会话ID
    timestamp: datetime           # 时间戳
```

**params 字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| emergency_type | str | ✅ | 应急类型 |
| location | str | ✅ | 地点 |
| severity | str | ❌ | 严重程度（默认：一般）|
| description | str | ❌ | 描述 |
| photos | List[str] | ❌ | 照片URL列表 |

### SkillResult

```python
@dataclass
class SkillResult:
    response: str                  # 响应消息
    data: Dict[str, Any]          # 完整数据
    success: bool                 # 是否成功
    error: Optional[str]          # 错误信息
```

**data 字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| action_plan | dict | 应急方案 |
| sensitive_customers | list | 敏感客户列表 |
| doc_url | str | 应急文档URL |
| contacts_to_notify | list | 需要通知的联系人 |
| analysis | dict | 应急分析结果 |

## 响应消息示例

```
🚨 应急响应启动

**事件类型**：停电故障 ⚡
**严重程度**：重大
**响应级别**：一级响应
**发生地点**：XX街道XX号配电房
**报告时间**：2026-03-20 14:30:00

---

**即时行动**：
1. 确认故障范围和原因
2. 启动备用电源（如有）
3. 通知受影响用户
4. 派遣抢修队伍
5. 记录故障时间和现象

---

**需要通知**：抢修班, 调度中心, 客服中心, 公司领导, 应急办

**预计处理时间**：2-4小时

---

**敏感客户**：已识别 3 位敏感客户，已自动发送关怀消息。

应急文档已生成，详细方案请查看附件。

⚡ 请立即开始处置，并每30分钟汇报进展。
```

## 错误处理

```python
result = await skill.invoke(context)

if not result.success:
    print(f"错误: {result.error}")
    # 处理错误
else:
    print(result.response)
    # 处理成功结果
```

## 最佳实践

1. **及时报告**：发现应急事件后应尽快调用 Skill
2. **提供照片**：有现场照片时务必提供，AI 会进行分析
3. **准确描述**：提供尽可能详细的描述信息
4. **定期更新**：每30分钟汇报进展，直到事件处理完成
5. **安全第一**：所有行动必须以人员安全为首要考虑

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-03-20 | 初始版本，支持4种应急类型 |

---

**维护者**: Field Core Team  
**文档版本**: 1.0.0  
**最后更新**: 2026-03-20
