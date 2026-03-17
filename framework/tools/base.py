"""
Tools层基础设施 v1.0

提供Pydantic基础类、统计装饰器、统一错误处理等基础设施

Usage:
    from framework.tools.base import BaseParams, BaseOutput
    from framework.tools.metrics import with_metrics
    from framework.tools.errors import ToolError, NetworkError
    
    class SearchParams(BaseParams):
        query: str = Field(..., min_length=1)
    
    @with_metrics
    def web_search(params: SearchParams) -> SearchOutput:
        # Implementation
        pass
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# === 基础模型 ===

class BaseParams(BaseModel):
    """
    所有Tool参数的基类
    
    所有Tool参数类应继承此基类，自动获得：
    - 参数验证
    - 类型转换
    - 序列化/反序列化
    
    Example:
        class SearchParams(BaseParams):
            query: str = Field(..., min_length=1, max_length=500)
            max_results: int = Field(default=10, ge=1, le=100)
    """
    
    class Config:
        # 自动去除字符串两端空白
        anystr_strip_whitespace = True
        # 验证赋值
        validate_assignment = True
        # 使用枚举值
        use_enum_values = True


class BaseOutput(BaseModel):
    """
    所有Tool输出的基类
    
    所有Tool输出类应继承此基类，自动获得：
    - 成功标识
    - 执行时间
    - 时间戳
    - 错误信息（可选）
    
    Example:
        class SearchOutput(BaseOutput):
            query: str
            total_results: int = Field(ge=0)
            results: List[SearchResult]
    """
    
    success: bool = Field(default=True, description="是否成功")
    execution_time_ms: float = Field(
        default=0.0,
        ge=0,
        description="执行时间（毫秒）"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="执行时间戳"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息（如果失败）"
    )
    
    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True


class SearchResult(BaseModel):
    """通用搜索结果项"""
    rank: int = Field(ge=1, description="排名")
    title: str = Field(..., description="标题")
    url: Optional[str] = Field(None, description="URL")
    snippet: str = Field(..., description="摘要")
    relevance_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="相关度分数"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="额外元数据"
    )


class ListOutput(BaseOutput):
    """通用列表输出"""
    total: int = Field(default=0, ge=0, description="总数")
    items: List[Any] = Field(default_factory=list, description="项目列表")
    
    @property
    def count(self) -> int:
        """返回项目数量"""
        return len(self.items)


# === 工具函数 ===

def create_error_output(
    error_type: str,
    message: str,
    suggestion: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    execution_time_ms: float = 0.0
) -> Dict[str, Any]:
    """
    创建错误输出字典
    
    Args:
        error_type: 错误类型
        message: 错误消息
        suggestion: 建议解决方案
        details: 错误详情
        execution_time_ms: 执行时间
    
    Returns:
        错误输出字典
    """
    return {
        "error": {
            "error_type": error_type,
            "message": message,
            "suggestion": suggestion,
            "details": details or {}
        },
        "execution_time_ms": execution_time_ms,
        "timestamp": datetime.now().isoformat()
    }


def validate_positive_int(value: int, field_name: str) -> int:
    """验证正整数"""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    return value


def validate_non_empty_string(value: str, field_name: str) -> str:
    """验证非空字符串"""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return value.strip()


__all__ = [
    'BaseParams',
    'BaseOutput',
    'SearchResult',
    'ListOutput',
    'create_error_output',
    'validate_positive_int',
    'validate_non_empty_string'
]
