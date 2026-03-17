"""
统一错误处理

提供标准化的错误类型和错误处理机制

Usage:
    from framework.tools.errors import (
        ToolError, NetworkError, ValidationError, 
        QuotaExceededError, TimeoutError
    )
    
    try:
        result = web_search(params)
    except NetworkError as e:
        print(f"网络错误: {e.message}")
        print(f"建议: {e.suggestion}")
    except ValidationError as e:
        print(f"参数错误: {e.message}")
"""

from typing import Optional, Dict, Any


class ToolError(Exception):
    """
    Tool错误基类
    
    所有Tool相关错误的基类，提供统一的错误格式
    
    Attributes:
        error_type: 错误类型
        message: 错误消息
        suggestion: 建议解决方案
        details: 错误详情
    
    Example:
        raise ToolError(
            error_type="GenericError",
            message="Something went wrong",
            suggestion="Try again later"
        )
    """
    
    def __init__(
        self,
        error_type: str,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'suggestion': self.suggestion,
            'details': self.details
        }
    
    def __str__(self) -> str:
        if self.suggestion:
            return f"[{self.error_type}] {self.message} (Suggestion: {self.suggestion})"
        return f"[{self.error_type}] {self.message}"


class NetworkError(ToolError):
    """
    网络错误
    
    当网络连接失败或网络请求超时时抛出
    
    Example:
        raise NetworkError(
            message="Failed to connect to API server",
            details={"url": "https://api.example.com"}
        )
    """
    
    def __init__(
        self, 
        message: str = "Network connection failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type='NetworkError',
            message=message,
            suggestion='Check your network connection and try again',
            details=details
        )


class QuotaExceededError(ToolError):
    """
    配额超限错误
    
    当API配额用尽时抛出
    
    Example:
        raise QuotaExceededError(
            message="Daily API quota exceeded",
            details={"quota": 1000, "used": 1000}
        )
    """
    
    def __init__(
        self,
        message: str = "API quota exceeded",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type='QuotaExceededError',
            message=message,
            suggestion='Wait for quota reset or upgrade your plan',
            details=details
        )


class ValidationError(ToolError):
    """
    参数验证错误
    
    当参数验证失败时抛出
    
    Example:
        raise ValidationError(
            message="Invalid query parameter",
            field="query",
            details={"value": "", "constraint": "min_length=1"}
        )
    """
    
    def __init__(
        self,
        message: str = "Parameter validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details['field'] = field
        
        super().__init__(
            error_type='ValidationError',
            message=message,
            suggestion=f'Please check the parameter format and value',
            details=details
        )


class TimeoutError(ToolError):
    """
    超时错误
    
    当操作超时时抛出
    
    Example:
        raise TimeoutError(
            message="Search operation timed out",
            details={"timeout_seconds": 30}
        )
    """
    
    def __init__(
        self,
        message: str = "Operation timed out",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type='TimeoutError',
            message=message,
            suggestion='Try with a simpler query or increase timeout',
            details=details
        )


class ResourceExhaustedError(ToolError):
    """
    资源耗尽错误
    
    当系统资源不足时抛出
    
    Example:
        raise ResourceExhaustedError(
            message="Memory limit exceeded",
            details={"used_mb": 1024, "limit_mb": 512}
        )
    """
    
    def __init__(
        self,
        message: str = "System resource exhausted",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type='ResourceExhaustedError',
            message=message,
            suggestion='Reduce data size or try again later',
            details=details
        )


class NotFoundError(ToolError):
    """
    未找到错误
    
    当请求的资源不存在时抛出
    
    Example:
        raise NotFoundError(
            message="Document not found",
            details={"document_id": "12345"}
        )
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if resource_type:
            details['resource_type'] = resource_type
        
        super().__init__(
            error_type='NotFoundError',
            message=message,
            suggestion='Check if the resource exists or has been deleted',
            details=details
        )


class PermissionDeniedError(ToolError):
    """
    权限拒绝错误
    
    当用户没有足够权限时抛出
    
    Example:
        raise PermissionDeniedError(
            message="Access denied to private document",
            details={"required_permission": "read"}
        )
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type='PermissionDeniedError',
            message=message,
            suggestion='Check your permissions or contact administrator',
            details=details
        )


__all__ = [
    'ToolError',
    'NetworkError',
    'QuotaExceededError',
    'ValidationError',
    'TimeoutError',
    'ResourceExhaustedError',
    'NotFoundError',
    'PermissionDeniedError'
]
