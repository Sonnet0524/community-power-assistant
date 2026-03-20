"""
EmergencyGuide Skill - 应急处置 Skill

提供应急方案推送和现场处置指引，支持：
- 4种应急类型（停电故障、设备故障、安全事故、敏感客户投诉）
- 敏感客户自动识别
- 应急方案自动生成
- 关怀消息自动发送
- 应急文档生成
"""

from .skill import EmergencyGuideSkill, SkillContext, SkillResult
from .templates import EmergencyTemplates

__all__ = [
    "EmergencyGuideSkill",
    "SkillContext",
    "SkillResult",
    "EmergencyTemplates"
]

__version__ = "1.0.0"
