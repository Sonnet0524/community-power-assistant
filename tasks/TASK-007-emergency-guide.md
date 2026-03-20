# Task-007: EmergencyGuide Skill 开发

## 任务概述

**任务ID**: TASK-007  
**任务名称**: EmergencyGuide Skill（应急处置）  
**优先级**: 🔴 最高  
**预计耗时**: 40-60分钟  
**依赖**: TASK-003 ✅, TASK-004 ✅  
**负责团队**: Field Core Team

## 任务目标

开发应急处置 Skill，提供：
1. 敏感客户识别与关怀
2. 应急方案智能推送
3. 现场处置指引
4. 应急联系人自动通知

## Skill设计

### Skill定义

```yaml
skill:
  name: emergency_guide
  description: 应急处置Skill，提供应急方案推送和现场处置指引
  version: 1.0.0
  
  input:
    - emergency_type: str      # 应急类型
    - location: str            # 地点
    - severity: str            # 严重程度
    - description: str         # 描述
    - photos: list             # 现场照片
    
  output:
    - response: str            # 回复消息
    - action_plan: dict        # 行动计划
    - contacts_to_notify: list # 需要通知的联系人
    - doc_url: str             # 应急文档URL
```

### 应急类型

```python
EMERGENCY_TYPES = {
    "power_outage": {
        "name": "停电故障",
        "severity_levels": ["一般", "较大", "重大"],
        "auto_response": True
    },
    "equipment_fault": {
        "name": "设备故障", 
        "severity_levels": ["一般", "严重", "危急"],
        "auto_response": True
    },
    "safety_incident": {
        "name": "安全事故",
        "severity_levels": ["轻微", "一般", "重大"],
        "auto_response": False  # 需要人工确认
    },
    "customer_complaint": {
        "name": "敏感客户投诉",
        "severity_levels": ["一般", "重要", "紧急"],
        "auto_response": True
    }
}
```

## 详细工作内容

### 1. Skill 主类

**文件**: `src/skills/emergency_guide/skill.py`

```python
class EmergencyGuideSkill(BaseSkill):
    """应急处置 Skill"""
    
    NAME = "emergency_guide"
    DESCRIPTION = "提供应急处置方案和现场指引"
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """处理应急事件"""
        emergency_type = context.params.get("emergency_type")
        location = context.params.get("location")
        severity = context.params.get("severity", "一般")
        description = context.params.get("description", "")
        photos = context.params.get("photos", [])
        
        # 分析应急情况
        analysis = await self._analyze_emergency(
            emergency_type, location, description, photos
        )
        
        # 生成应急方案
        action_plan = await self._generate_action_plan(
            emergency_type, severity, analysis
        )
        
        # 识别敏感客户
        sensitive_customers = await self._identify_sensitive_customers(location)
        
        # 生成应急文档
        doc_url = await self._generate_emergency_doc(
            emergency_type, location, action_plan, photos
        )
        
        # 构建回复
        response = self._build_response(
            emergency_type, severity, action_plan, sensitive_customers
        )
        
        return SkillResult(
            response=response,
            data={
                "action_plan": action_plan,
                "sensitive_customers": sensitive_customers,
                "doc_url": doc_url,
                "contacts_to_notify": action_plan.get("contacts", [])
            }
        )
```

### 2. 应急分析

```python
async def _analyze_emergency(
    self,
    emergency_type: str,
    location: str,
    description: str,
    photos: list
) -> dict:
    """使用KIMI分析应急情况"""
    
    # 如果有照片，先分析照片
    photo_analysis = []
    if photos:
        for photo in photos[:3]:  # 最多分析3张
            analysis = await self.kimi.analyze_image(
                photo,
                "分析这张照片中的电力设施状态，识别任何异常或故障迹象"
            )
            photo_analysis.append(analysis)
    
    # 综合分析
    prompt = f"""
    分析以下应急事件：
    
    类型：{EMERGENCY_TYPES[emergency_type]['name']}
    地点：{location}
    描述：{description}
    
    照片分析：
    {json.dumps(photo_analysis, ensure_ascii=False)}
    
    请提供：
    1. 影响范围评估
    2. 可能的故障原因
    3. 紧急程度判断
    4. 建议的处置措施
    
    以JSON格式返回分析结果。
    """
    
    response = await self.kimi.chat([
        {"role": "system", "content": "你是电力应急处理专家"},
        {"role": "user", "content": prompt}
    ])
    
    return self._parse_json_response(response)
```

### 3. 敏感客户关怀

```python
async def _identify_sensitive_customers(self, location: str) -> list:
    """识别敏感客户"""
    # 从数据库查询该区域的敏感客户
    # 标准：医院、学校、重要企业、历史投诉客户
    
    customers = await self.pg_tool.query(
        """
        SELECT * FROM users 
        WHERE location LIKE $1 
        AND (is_important = true OR complaint_count > 0)
        """,
        {"location": f"%{location}%"}
    )
    
    return customers

async def _send_customer_care_message(
    self,
    customer: dict,
    emergency_info: dict
):
    """发送关怀消息"""
    messages = {
        "hospital": f"""🏥 重要通知

{customer['name']}您好：

因{emergency_info['location']}发生{emergency_info['type']}，
您所在的区域可能受到影响。

我们正在紧急处理，预计{emergency_info['eta']}恢复。

医院作为重要用户，如有紧急用电需求，
请联系专属客户经理：{emergency_info['manager_contact']}

深表歉意！""",

        "school": f"""🏫 重要通知

{customer['name']}您好：

因电力设施故障，您所在的区域可能停电。

我们正在紧急抢修，预计{emergency_info['eta']}恢复供电。

如影响教学活动，请提前做好准备。

客服热线：95598""",

        "default": f"""⚠️ 停电通知

尊敬的{customer['name']}：

您所在的区域因故障暂时停电，
我们正在全力抢修。

预计恢复时间：{emergency_info['eta']}

给您带来不便，敬请谅解！

最新进展请关注本群通知。"""
    }
    
    message = messages.get(
        customer.get('type', 'default'),
        messages['default']
    )
    
    await self.wecom.send_text(customer['wecom_id'], message)
```

### 4. 应急方案生成

```python
async def _generate_action_plan(
    self,
    emergency_type: str,
    severity: str,
    analysis: dict
) -> dict:
    """生成应急方案"""
    
    action_plans = {
        "power_outage": {
            "immediate_actions": [
                "确认故障范围和原因",
                "启动备用电源（如有）",
                "通知受影响用户",
                "派遣抢修队伍"
            ],
            "contacts": ["抢修班", "调度中心", "客服中心"],
            "estimated_time": "2-4小时"
        },
        "equipment_fault": {
            "immediate_actions": [
                "现场安全检查",
                "隔离故障设备",
                "评估是否需要停电处理",
                "联系设备厂家"
            ],
            "contacts": ["设备厂家", "检修班", "安监部"],
            "estimated_time": "4-8小时"
        },
        "safety_incident": {
            "immediate_actions": [
                "确保人员安全",
                "封锁现场",
                "报告上级部门",
                "启动应急预案"
            ],
            "contacts": ["安监部", "应急办", "公司领导"],
            "estimated_time": "视情况而定"
        }
    }
    
    base_plan = action_plans.get(emergency_type, {})
    
    # 根据严重程度调整
    if severity == "重大":
        base_plan["contacts"].append("公司领导")
        base_plan["escalation_required"] = True
    
    return base_plan
```

### 5. 现场处置指引

```python
def _build_response(
    self,
    emergency_type: str,
    severity: str,
    action_plan: dict,
    sensitive_customers: list
) -> str:
    """构建回复消息"""
    
    response = f"""🚨 应急响应启动

**事件类型**：{EMERGENCY_TYPES[emergency_type]['name']}
**严重程度**：{severity}
**响应级别**：{"一级" if severity == "重大" else "二级" if severity == "较大" else "三级"}

---

**即时行动**：
"""
    
    for i, action in enumerate(action_plan.get("immediate_actions", []), 1):
        response += f"{i}. {action}\n"
    
    response += f"""
---

**需要通知**：{', '.join(action_plan.get("contacts", []))}

**预计处理时间**：{action_plan.get("estimated_time", "待定")}

---

"""
    
    if sensitive_customers:
        response += f"**敏感客户**：已识别 {len(sensitive_customers)} 位敏感客户，已自动发送关怀消息。\n\n"
    
    response += """应急文档已生成，详细方案请查看附件。

⚡ 请立即开始处置，并每30分钟汇报进展。"""
    
    return response
```

## 交付物

1. **Skill 主类**: `src/skills/emergency_guide/skill.py`
2. **Skill 定义**: `knowledge-base/field-info-agent/implementation/skills/emergency-guide/SKILL.md`
3. **应急模板**: `src/skills/emergency_guide/templates.py`
4. **单元测试**: `tests/skills/test_emergency_guide.py`
5. **使用文档**: `docs/skills/emergency-guide.md`

## 验收标准

- [ ] 支持4种应急类型
- [ ] 敏感客户自动识别
- [ ] 应急方案自动生成
- [ ] 关怀消息自动发送
- [ ] 应急文档正确生成
- [ ] 单元测试覆盖率 >90%

## 报告要求

完成后请提交报告到: `reports/REPORT-007-emergency-guide.md`

---

**创建时间**: 2026-03-20  
**负责团队**: Field Core Team  
**状态**: 待开始  
**依赖**: Phase 1 全部完成 ✅