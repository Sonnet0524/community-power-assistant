"""
EmergencyGuide Skill - 应急模板

提供应急方案模板和消息模板
"""

from typing import Dict, List, Any


class EmergencyTemplates:
    """应急模板管理器"""
    
    # 应急类型定义
    EMERGENCY_TYPES = {
        "power_outage": {
            "name": "停电故障",
            "severity_levels": ["一般", "较大", "重大"],
            "auto_response": True,
            "icon": "⚡"
        },
        "equipment_fault": {
            "name": "设备故障", 
            "severity_levels": ["一般", "严重", "危急"],
            "auto_response": True,
            "icon": "🔧"
        },
        "safety_incident": {
            "name": "安全事故",
            "severity_levels": ["轻微", "一般", "重大"],
            "auto_response": False,  # 需要人工确认
            "icon": "⚠️"
        },
        "customer_complaint": {
            "name": "敏感客户投诉",
            "severity_levels": ["一般", "重要", "紧急"],
            "auto_response": True,
            "icon": "📞"
        }
    }
    
    # 应急方案模板
    ACTION_PLAN_TEMPLATES = {
        "power_outage": {
            "immediate_actions": [
                "确认故障范围和原因",
                "启动备用电源（如有）",
                "通知受影响用户",
                "派遣抢修队伍",
                "记录故障时间和现象"
            ],
            "contacts": ["抢修班", "调度中心", "客服中心"],
            "estimated_time": "2-4小时",
            "safety_precautions": [
                "穿戴绝缘防护用品",
                "设置安全警示标志",
                "确认设备已断电"
            ]
        },
        "equipment_fault": {
            "immediate_actions": [
                "现场安全检查",
                "隔离故障设备",
                "评估是否需要停电处理",
                "联系设备厂家",
                "准备备用设备"
            ],
            "contacts": ["设备厂家", "检修班", "安监部"],
            "estimated_time": "4-8小时",
            "safety_precautions": [
                "悬挂警示牌",
                "隔离带电部位",
                "准备应急照明"
            ]
        },
        "safety_incident": {
            "immediate_actions": [
                "确保人员安全",
                "封锁现场",
                "报告上级部门",
                "启动应急预案",
                "联系医疗机构（如有人员受伤）"
            ],
            "contacts": ["安监部", "应急办", "公司领导"],
            "estimated_time": "视情况而定",
            "safety_precautions": [
                "禁止无关人员进入",
                "保护现场证据",
                "配合事故调查"
            ]
        },
        "customer_complaint": {
            "immediate_actions": [
                "安抚客户情绪",
                "了解详细情况",
                "记录投诉内容",
                "联系相关部门",
                "制定解决方案"
            ],
            "contacts": ["客服中心", "营销部", "运维部"],
            "estimated_time": "24小时内响应",
            "safety_precautions": [
                "保持专业态度",
                "避免冲突升级",
                "及时上报领导"
            ]
        }
    }
    
    # 客户关怀消息模板
    CUSTOMER_CARE_TEMPLATES = {
        "hospital": """🏥 重要通知

{customer_name}您好：

因{location}发生{emergency_type}，
您所在的区域可能受到影响。

我们正在紧急处理，预计{eta}恢复。

医院作为重要用户，如有紧急用电需求，
请联系专属客户经理：{manager_contact}

深表歉意！""",
        
        "school": """🏫 重要通知

{customer_name}您好：

因电力设施故障，您所在的区域可能停电。

我们正在紧急抢修，预计{eta}恢复供电。

如影响教学活动，请提前做好准备。

客服热线：95598""",
        
        "enterprise": """🏢 重要通知

{customer_name}您好：

您所在的区域因{emergency_type}暂时停电，
我们正在全力抢修。

预计恢复时间：{eta}

作为重要企业用户，如有特殊用电需求，
请联系您的客户经理或拨打 95598

给您带来不便，敬请谅解！""",
        
        "default": """⚠️ 停电通知

尊敬的{customer_name}：

您所在的区域因故障暂时停电，
我们正在全力抢修。

预计恢复时间：{eta}

给您带来不便，敬请谅解！

最新进展请关注本群通知。"""
    }
    
    # 应急响应级别
    RESPONSE_LEVELS = {
        "重大": "一级响应",
        "较大": "二级响应",
        "一般": "三级响应",
        "严重": "二级响应",
        "危急": "一级响应",
        "重要": "二级响应",
        "紧急": "一级响应"
    }
    
    # 通知消息模板
    NOTIFICATION_TEMPLATES = {
        "emergency_start": """🚨 应急响应启动

**事件类型**：{emergency_name} {icon}
**严重程度**：{severity}
**响应级别**：{response_level}
**发生地点**：{location}
**报告时间**：{timestamp}

---

**即时行动**：
{actions}

---

**需要通知**：{contacts}

**预计处理时间**：{estimated_time}

---

{sensitive_customers_info}

应急文档已生成，详细方案请查看附件。

⚡ 请立即开始处置，并每30分钟汇报进展。""",
        
        "progress_update": """📢 应急进展更新

**事件**：{emergency_name}
**当前状态**：{status}
**更新时间**：{timestamp}

**处置进展**：
{progress}

**预计完成时间**：{eta}

如有变化将及时通知。""",
        
        "emergency_complete": """✅ 应急处理完成

**事件**：{emergency_name}
**处理结果**：{result}
**完成时间**：{timestamp}
**总耗时**：{duration}

**处置总结**：
{summary}

感谢大家的配合与支持！"""
    }
    
    # 应急分析提示词模板
    ANALYSIS_PROMPTS = {
        "emergency_analysis": """分析以下应急事件：

类型：{emergency_type}
地点：{location}
描述：{description}

照片分析：
{photo_analysis}

请提供：
1. 影响范围评估
2. 可能的故障原因
3. 紧急程度判断（高/中/低）
4. 建议的处置措施（3-5条）
5. 需要的资源和支持

以JSON格式返回分析结果，格式如下：
{{
    "impact_scope": "影响范围描述",
    "possible_causes": ["原因1", "原因2"],
    "urgency_level": "高/中/低",
    "suggested_actions": ["措施1", "措施2"],
    "required_resources": ["资源1", "资源2"]
}}""",
        
        "photo_analysis": "分析这张照片中的电力设施状态，识别任何异常或故障迹象。如果有异常，请说明类型和严重程度。"
    }
    
    @classmethod
    def get_emergency_type(cls, emergency_type: str) -> Dict[str, Any]:
        """获取应急类型定义"""
        return cls.EMERGENCY_TYPES.get(emergency_type, {})
    
    @classmethod
    def get_action_plan(cls, emergency_type: str) -> Dict[str, Any]:
        """获取应急方案模板"""
        return cls.ACTION_PLAN_TEMPLATES.get(emergency_type, {}).copy()
    
    @classmethod
    def get_customer_care_message(
        cls,
        customer_type: str,
        customer_name: str,
        location: str,
        emergency_type: str,
        eta: str,
        manager_contact: str = ""
    ) -> str:
        """获取客户关怀消息"""
        template = cls.CUSTOMER_CARE_TEMPLATES.get(
            customer_type, 
            cls.CUSTOMER_CARE_TEMPLATES["default"]
        )
        
        return template.format(
            customer_name=customer_name,
            location=location,
            emergency_type=emergency_type,
            eta=eta,
            manager_contact=manager_contact
        )
    
    @classmethod
    def get_response_level(cls, severity: str) -> str:
        """获取响应级别"""
        return cls.RESPONSE_LEVELS.get(severity, "三级响应")
    
    @classmethod
    def build_notification(
        cls,
        template_name: str,
        **kwargs
    ) -> str:
        """构建通知消息"""
        template = cls.NOTIFICATION_TEMPLATES.get(template_name, "")
        return template.format(**kwargs)
    
    @classmethod
    def get_analysis_prompt(cls, prompt_type: str, **kwargs) -> str:
        """获取分析提示词"""
        template = cls.ANALYSIS_PROMPTS.get(prompt_type, "")
        return template.format(**kwargs) if template else ""


# 导出所有模板
__all__ = ["EmergencyTemplates"]
