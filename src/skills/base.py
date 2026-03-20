"""
Field Info Agent - Skill 类型定义

定义Skill相关的类型和数据结构
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SkillResultStatus(Enum):
    """Skill 执行结果状态"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    NEED_INPUT = "need_input"
    COMPLETED = "completed"


@dataclass
class SkillResult:
    """Skill 执行结果
    
    Attributes:
        response: 回复消息
        status: 执行状态
        next_phase: 下一阶段
        actions: 建议操作列表
        data: 附加数据
        error: 错误信息
    """
    response: str
    status: SkillResultStatus = SkillResultStatus.SUCCESS
    next_phase: Optional[str] = None
    actions: List[Dict[str, Any]] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SkillContext:
    """Skill 上下文
    
    Attributes:
        session_id: 会话ID
        user_id: 用户ID
        message: 用户输入消息
        session: 会话数据
        metadata: 元数据
    """
    session_id: str
    user_id: str
    message: str
    session: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """获取会话数据"""
        return self.session.get(key, default)
    
    def set_session_data(self, key: str, value: Any) -> None:
        """设置会话数据"""
        self.session[key] = value


class BaseSkill:
    """Skill 基类
    
    所有 Skill 必须继承此类
    
    Example:
        class MySkill(BaseSkill):
            NAME = "my_skill"
            DESCRIPTION = "My skill description"
            
            async def invoke(self, context: SkillContext) -> SkillResult:
                # 实现 Skill 逻辑
                return SkillResult(response="Hello")
    """
    
    NAME: str = ""
    DESCRIPTION: str = ""
    VERSION: str = "1.0.0"
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """初始化 Skill"""
        self._initialized = True
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """执行 Skill
        
        Args:
            context: Skill 上下文
            
        Returns:
            Skill 执行结果
        """
        raise NotImplementedError("Subclasses must implement invoke()")
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Skill 信息"""
        return {
            "name": self.NAME,
            "description": self.DESCRIPTION,
            "version": self.VERSION
        }


__all__ = [
    "SkillResultStatus",
    "SkillResult",
    "SkillContext",
    "BaseSkill"
]
