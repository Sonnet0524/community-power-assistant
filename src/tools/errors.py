"""
Field Info Agent - Tool 错误定义

定义 PostgreSQL、MinIO、Redis Tool 的专用错误类型

Usage:
    from src.tools.errors import PostgreSQLError, MinIOError, RedisError
    
    raise PostgreSQLError("Connection failed", details={"host": "localhost"})
"""

from typing import Optional, Dict, Any


class ToolError(Exception):
    """Tool 基础错误类
    
    所有 Tool 错误的基类，提供统一的错误格式
    
    Attributes:
        error_type: 错误类型标识
        message: 错误消息
        suggestion: 建议解决方案
        details: 错误详情字典
    
    Example:
        raise ToolError(
            error_type="GenericError",
            message="Operation failed",
            suggestion="Try again later",
            details={"operation": "upload"}
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
            "error_type": self.error_type,
            "message": self.message,
            "suggestion": self.suggestion,
            "details": self.details
        }
    
    def __str__(self) -> str:
        if self.suggestion:
            return f"[{self.error_type}] {self.message} (Suggestion: {self.suggestion})"
        return f"[{self.error_type}] {self.message}"


class PostgreSQLError(ToolError):
    """PostgreSQL 数据库错误
    
    当 PostgreSQL 操作失败时抛出，包括：
    - 连接失败
    - 查询错误
    - 事务错误
    - 数据验证错误
    
    Example:
        raise PostgreSQLError(
            message="Failed to execute query",
            details={"sql": "SELECT * FROM users", "params": {"id": 1}}
        )
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type="PostgreSQLError",
            message=message,
            suggestion=suggestion or "Check database connection and SQL syntax",
            details=details
        )


class MinIOError(ToolError):
    """MinIO 对象存储错误
    
    当 MinIO 操作失败时抛出，包括：
    - 上传失败
    - 下载失败
    - 文件不存在
    - 权限错误
    
    Example:
        raise MinIOError(
            message="Failed to upload file",
            details={"bucket": "field-documents", "object": "photo.jpg"}
        )
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type="MinIOError",
            message=message,
            suggestion=suggestion or "Check MinIO connection and bucket permissions",
            details=details
        )


class RedisError(ToolError):
    """Redis 缓存错误
    
    当 Redis 操作失败时抛出，包括：
    - 连接失败
    - 键操作错误
    - 锁操作错误
    - 限流错误
    
    Example:
        raise RedisError(
            message="Failed to acquire lock",
            details={"lock_name": "task_lock", "timeout": 10}
        )
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type="RedisError",
            message=message,
            suggestion=suggestion or "Check Redis connection and key existence",
            details=details
        )


class ConnectionError(ToolError):
    """连接错误
    
    当无法连接到服务时抛出
    
    Example:
        raise ConnectionError(
            message="Failed to connect to PostgreSQL",
            details={"host": "localhost", "port": 5432, "attempts": 3}
        )
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type="ConnectionError",
            message=message,
            suggestion=suggestion or "Check service status and network connectivity",
            details=details
        )


class ValidationError(ToolError):
    """参数验证错误
    
    当参数验证失败时抛出
    
    Example:
        raise ValidationError(
            message="Invalid user ID format",
            field="user_id",
            details={"value": "", "constraint": "min_length=1"}
        )
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        
        super().__init__(
            error_type="ValidationError",
            message=message,
            suggestion=suggestion or "Check parameter format and value",
            details=details
        )


class NotFoundError(ToolError):
    """资源未找到错误
    
    当请求的资源不存在时抛出
    
    Example:
        raise NotFoundError(
            message="User not found",
            resource_type="user",
            details={"user_id": "user_123"}
        )
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        
        super().__init__(
            error_type="NotFoundError",
            message=message,
            suggestion="Verify resource ID and existence",
            details=details
        )


class TimeoutError(ToolError):
    """超时错误
    
    当操作超时时抛出
    
    Example:
        raise TimeoutError(
            message="Database query timed out",
            details={"timeout_seconds": 30, "query": "SELECT * FROM large_table"}
        )
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_type="TimeoutError",
            message=message,
            suggestion=suggestion or "Try with a simpler operation or increase timeout",
            details=details
        )


__all__ = [
    "ToolError",
    "PostgreSQLError",
    "MinIOError",
    "RedisError",
    "ConnectionError",
    "ValidationError",
    "NotFoundError",
    "TimeoutError"
]
