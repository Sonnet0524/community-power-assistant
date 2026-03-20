# EmergencyGuide Skill 使用文档

## 概述

EmergencyGuide Skill 是 Field Info Agent 的核心应急处置技能，提供电力系统应急事件的快速响应和处置能力。

## 功能特性

### 1. 支持的应急类型

| 类型 | 说明 | 严重程度 |
|------|------|----------|
| **停电故障** | 突发的停电事件 | 一般 / 较大 / 重大 |
| **设备故障** | 电力设备异常 | 一般 / 严重 / 危急 |
| **安全事故** | 涉及人身安全的突发事件 | 轻微 / 一般 / 重大 |
| **敏感客户投诉** | 重要客户的投诉事件 | 一般 / 重要 / 紧急 |

### 2. 智能功能

- **AI 分析**：使用 KIMI 分析现场照片和情况描述
- **敏感客户识别**：自动识别受影响区域的重要客户（医院、学校、企业等）
- **关怀消息**：自动向敏感客户发送关怀通知
- **应急方案**：根据事件类型自动生成处理方案
- **文档生成**：自动生成应急处理文档

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
import asyncio
from src.skills.emergency_guide import EmergencyGuideSkill, SkillContext

async def main():
    # 初始化 Skill
    skill = EmergencyGuideSkill()
    
    # 构建上下文
    context = SkillContext(
        params={
            "emergency_type": "power_outage",
            "location": "XX街道XX号配电房",
            "severity": "重大",
            "description": "变压器冒烟，有明火"
        }
    )
    
    # 调用 Skill
    result = await skill.invoke(context)
    
    # 输出结果
    print(result.response)
    print(f"应急方案: {result.data['action_plan']}")
    print(f"敏感客户: {result.data['sensitive_customers']}")

# 运行
asyncio.run(main())
```

## 完整配置

### 1. 配置工具依赖

```python
from src.tools.kimi_tool import KIMITool
from src.tools.postgresql_tool import PostgreSQLTool
from src.tools.minio_tool import MinIOTool

# KIMI Tool（用于AI分析）
kimi = KIMITool(config=KIMIConfig(
    api_key="your-api-key",
    model="kimi-for-coding"
))

# PostgreSQL Tool（用于敏感客户查询）
pg = PostgreSQLTool(config=PostgreSQLConfig(
    host="localhost",
    port=5432,
    database="field_info",
    user="postgres",
    password="password"
))

# MinIO Tool（用于文档存储）
minio = MinIOTool(config=MinIOConfig(
    endpoint="minio:9000",
    access_key="access-key",
    secret_key="secret-key"
))

# WeCom Tool（用于发送消息）
wecom = WeComTool(config=WeComConfig(
    corp_id="corp-id",
    corp_secret="corp-secret",
    agent_id="agent-id"
))

# 初始化 Skill
skill = EmergencyGuideSkill(
    kimi_tool=kimi,
    pg_tool=pg,
    wecom_tool=wecom,
    minio_tool=minio
)
```

### 2. 环境变量配置

```bash
# KIMI API
export KIMI_API_KEY="your-kimi-api-key"
export KIMI_MODEL="kimi-for-coding"

# PostgreSQL
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="field_info"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="password"

# MinIO
export MINIO_ENDPOINT="minio:9000"
export MINIO_ACCESS_KEY="access-key"
export MINIO_SECRET_KEY="secret-key"

# WeCom
export WECOM_CORP_ID="corp-id"
export WECOM_CORP_SECRET="corp-secret"
export WECOM_AGENT_ID="agent-id"
```

## 使用场景

### 场景1：停电故障处理

```python
context = SkillContext(
    params={
        "emergency_type": "power_outage",
        "location": "XX小区配电房",
        "severity": "较大",
        "description": "突降暴雨导致线路跳闸，影响XX小区500户居民",
        "photos": [
            "http://minio:9000/photos/fault_1.jpg",
            "http://minio:9000/photos/fault_2.jpg"
        ]
    }
)

result = await skill.invoke(context)

# 输出示例：
# 🚨 应急响应启动
# **事件类型**：停电故障 ⚡
# **严重程度**：较大
# **响应级别**：二级响应
# ...
```

**自动生成的行动方案**：
1. 确认故障范围和原因
2. 启动备用电源（如有）
3. 通知受影响用户
4. 派遣抢修队伍
5. 记录故障时间和现象

### 场景2：设备故障处理

```python
context = SkillContext(
    params={
        "emergency_type": "equipment_fault",
        "location": "XX变电站2号主变",
        "severity": "严重",
        "description": "主变油温异常升高至95℃，超过警戒线"
    }
)

result = await skill.invoke(context)
```

**自动生成的行动方案**：
1. 现场安全检查
2. 隔离故障设备
3. 评估是否需要停电处理
4. 联系设备厂家
5. 准备备用设备

### 场景3：安全事故处理

```python
context = SkillContext(
    params={
        "emergency_type": "safety_incident",
        "location": "XX施工现场",
        "severity": "重大",
        "description": "作业人员触电，已昏迷，已拨打120"
    }
)

result = await skill.invoke(context)
```

**⚠️ 注意**：安全事故需要人工确认后才会启动自动响应。

### 场景4：敏感客户投诉处理

```python
context = SkillContext(
    params={
        "emergency_type": "customer_complaint",
        "location": "XX医院",
        "severity": "紧急",
        "description": "本月第3次停电，导致手术中断，院方强烈投诉"
    }
)

result = await skill.invoke(context)
```

## 响应消息格式

### 标准响应

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

### 关怀消息示例

**医院**：
```
🏥 重要通知

中心医院您好：

因XX街道发生停电故障，
您所在的区域可能受到影响。

我们正在紧急处理，预计2-4小时恢复。

医院作为重要用户，如有紧急用电需求，
请联系专属客户经理：138-xxxx-xxxx

深表歉意！
```

## 数据库 Schema

### users 表

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50), -- hospital/school/enterprise/default
    location VARCHAR(200),
    is_important BOOLEAN DEFAULT false,
    complaint_count INTEGER DEFAULT 0,
    contact_phone VARCHAR(20),
    wecom_id VARCHAR(100),
    manager_contact VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_location ON users(location);
CREATE INDEX idx_users_important ON users(is_important);
CREATE INDEX idx_users_complaints ON users(complaint_count);
```

### 插入示例数据

```sql
-- 医院
INSERT INTO users (name, type, location, is_important, contact_phone, wecom_id, manager_contact)
VALUES ('中心医院', 'hospital', 'XX街道1号', true, '1234567890', 'user_hospital_001', '138-xxxx-xxxx');

-- 学校
INSERT INTO users (name, type, location, is_important, contact_phone, wecom_id, manager_contact)
VALUES ('第一中学', 'school', 'XX街道2号', true, '0987654321', 'user_school_001', '');

-- 投诉客户
INSERT INTO users (name, type, location, is_important, complaint_count, contact_phone, wecom_id)
VALUES ('张先生', 'default', 'XX街道3号', false, 3, '1122334455', 'user_001');
```

## 运行测试

```bash
# 运行所有测试
pytest tests/skills/test_emergency_guide.py -v

# 运行特定测试类
pytest tests/skills/test_emergency_guide.py::TestEmergencyTemplates -v
pytest tests/skills/test_emergency_guide.py::TestEmergencyGuideSkill -v

# 生成覆盖率报告
pytest tests/skills/test_emergency_guide.py --cov=src.skills.emergency_guide --cov-report=html

# 打开覆盖率报告
open htmlcov/index.html
```

## 最佳实践

### 1. 及时报告

发现应急事件后应立即调用 Skill，越早报告，处置效果越好。

```python
# 好的做法：立即报告
context = SkillContext(
    params={
        "emergency_type": "power_outage",
        "location": "XX街道",
        "severity": "重大"
    }
)

# 不好的做法：等待详细信息
# 应该立即报告，后续补充详细信息
```

### 2. 提供照片

有现场照片时务必提供，AI 会分析照片内容，提高分析准确性。

```python
context = SkillContext(
    params={
        "emergency_type": "equipment_fault",
        "location": "XX变电站",
        "description": "设备异常",
        "photos": [
            "http://minio:9000/photos/fault_1.jpg",
            "http://minio:9000/photos/fault_2.jpg"
        ]
    }
)
```

### 3. 准确描述

提供尽可能详细的描述信息，帮助 AI 更准确分析。

```python
# 好的描述
"主变油温异常升高至95℃，超过警戒线，伴有异响"

# 不好的描述
"设备坏了"
```

### 4. 定期更新

每30分钟汇报进展，直到事件处理完成。

```python
# 使用进展更新模板
progress_msg = EmergencyTemplates.build_notification(
    "progress_update",
    emergency_name="停电故障",
    status="处理中",
    timestamp="2026-03-20 15:00:00",
    progress="已完成故障定位，正在抢修",
    eta="1小时"
)
```

### 5. 安全第一

所有行动必须以人员安全为首要考虑。

## 常见问题

### Q1: 安全事故为什么不自动响应？

安全事故涉及人身安全，需要人工确认后才能启动自动响应，以确保决策的准确性和安全性。

### Q2: 照片分析有数量限制吗？

是的，最多分析3张照片。如果提供更多照片，系统会自动选择前3张进行分析。

### Q3: 如何提高敏感客户识别准确率？

- 确保用户地址信息完整准确
- 及时更新 `is_important` 标记
- 记录投诉历史到 `complaint_count`
- 定期审核敏感客户列表

### Q4: 可以自定义应急方案吗？

可以，通过修改 `templates.py` 中的 `ACTION_PLAN_TEMPLATES` 来自定义方案。

```python
# 自定义方案
EmergencyTemplates.ACTION_PLAN_TEMPLATES["custom_type"] = {
    "immediate_actions": ["自定义行动1", "自定义行动2"],
    "contacts": ["联系人1", "联系人2"],
    "estimated_time": "自定义时间",
    "safety_precautions": ["自定义注意事项"]
}
```

### Q5: 如何测试 Skill？

使用单元测试进行测试：

```python
# 使用 Mock 工具测试
from unittest.mock import AsyncMock

skill = EmergencyGuideSkill(
    kimi_tool=AsyncMock(),
    pg_tool=AsyncMock(),
    wecom_tool=AsyncMock(),
    minio_tool=AsyncMock()
)

# 测试调用
result = await skill.invoke(context)
assert result.success is True
```

## API 参考

### EmergencyGuideSkill

```python
class EmergencyGuideSkill:
    """应急处置 Skill"""
    
    NAME = "emergency_guide"
    DESCRIPTION = "提供应急处置方案和现场指引"
    VERSION = "1.0.0"
    
    def __init__(
        self,
        kimi_tool=None,      # KIMI Tool 实例
        pg_tool=None,        # PostgreSQL Tool 实例
        wecom_tool=None,     # 企业微信 Tool 实例
        minio_tool=None      # MinIO Tool 实例
    )
    
    async def invoke(self, context: SkillContext) -> SkillResult
        """处理应急事件"""
```

### SkillContext

```python
@dataclass
class SkillContext:
    params: Dict[str, Any]        # 输入参数
    user_id: Optional[str]        # 用户ID
    session_id: Optional[str]     # 会话ID
    timestamp: datetime           # 时间戳
```

### SkillResult

```python
@dataclass
class SkillResult:
    response: str                  # 响应消息
    data: Dict[str, Any]          # 完整数据
    success: bool                 # 是否成功
    error: Optional[str]          # 错误信息
```

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-03-20 | 初始版本，支持4种应急类型 |

## 技术支持

如有问题，请联系：

- **Field Core Team**: field-core@example.com
- **PM Agent**: pm-agent@example.com

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-20  
**维护者**: Field Core Team
