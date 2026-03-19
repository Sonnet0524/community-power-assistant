"""
Field Info Agent - Tools 模块

提供 PostgreSQL、MinIO、Redis 等基础设施工具的封装。

Usage:
    from src.tools import PostgreSQLTool, MinIOTool, RedisTool
    from src.tools.types import PostgreSQLConfig, MinIOConfig, RedisConfig
    
    # PostgreSQL
    pg_config = PostgreSQLConfig(...)
    async with PostgreSQLTool(pg_config) as pg:
        users = await pg.query("SELECT * FROM users")
    
    # MinIO
    minio_config = MinIOConfig(...)
    async with MinIOTool(minio_config) as minio:
        await minio.upload_file("/tmp/file.txt", "documents/file.txt")
    
    # Redis
    redis_config = RedisConfig(...)
    async with RedisTool(redis_config) as redis:
        await redis.set("key", "value", expire=3600)

Components:
    - PostgreSQLTool: 数据库操作封装
    - MinIOTool: 对象存储操作封装
    - RedisTool: 缓存操作封装
    - BaseTool: Tool 基类
    - Types: 数据模型和配置
    - Errors: 错误定义
"""

from src.tools.base import BaseTool, ToolLogEntry
from src.tools.postgresql_tool import PostgreSQLTool, TransactionContext
from src.tools.minio_tool import MinIOTool
from src.tools.redis_tool import RedisTool
from src.tools.types import (
    # PostgreSQL 模型
    User, Session, Task, TaskStatus, AnalysisResult, Document,
    # MinIO 模型
    FileMetadata, UploadResult,
    # Redis 模型
    LockInfo, RateLimitInfo,
    # 配置模型
    PostgreSQLConfig, MinIOConfig, RedisConfig
)
from src.tools.errors import (
    ToolError,
    PostgreSQLError,
    MinIOError,
    RedisError,
    ConnectionError,
    ValidationError,
    NotFoundError,
    TimeoutError
)

__version__ = "1.0.0"
__all__ = [
    # Tools
    "BaseTool",
    "PostgreSQLTool",
    "MinIOTool",
    "RedisTool",
    "TransactionContext",
    # Types
    "User",
    "Session",
    "Task",
    "TaskStatus",
    "AnalysisResult",
    "Document",
    "FileMetadata",
    "UploadResult",
    "LockInfo",
    "RateLimitInfo",
    "ToolLogEntry",
    # Configs
    "PostgreSQLConfig",
    "MinIOConfig",
    "RedisConfig",
    # Errors
    "ToolError",
    "PostgreSQLError",
    "MinIOError",
    "RedisError",
    "ConnectionError",
    "ValidationError",
    "NotFoundError",
    "TimeoutError"
]
