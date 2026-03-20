"""
StationWorkGuide Skill - 驻点工作引导

支持配电房巡检、客户走访、应急信息采集三种工作类型
"""

from .skill import StationWorkGuideSkill
from .workflows import (
    WorkPhase, WorkType, CollectionStep, WorkflowConfig,
    PHASE_TRANSITIONS, WORK_TYPE_CONFIGS
)
from .templates import MessageGenerator, MessageTemplates

__all__ = [
    "StationWorkGuideSkill",
    "WorkPhase",
    "WorkType",
    "CollectionStep",
    "WorkflowConfig",
    "PHASE_TRANSITIONS",
    "WORK_TYPE_CONFIGS",
    "MessageGenerator",
    "MessageTemplates"
]

__version__ = "1.0.0"
