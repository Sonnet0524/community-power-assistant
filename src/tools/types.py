"""
Field Info Agent - Tool 类型定义

定义 PostgreSQL、MinIO、Redis Tool 的数据模型和类型

Usage:
    from src.tools.types import User, Task, AnalysisResult, Document
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# === PostgreSQL 数据模型 ===

class User(BaseModel):
    """用户数据模型
    
    Attributes:
        id: 用户唯一标识
        name: 用户姓名
        department: 部门
        role: 角色
        created_at: 创建时间
        updated_at: 更新时间
        metadata: 附加元数据
    """
    
    id: str = Field(..., description="用户唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    department: str = Field(default="", max_length=100, description="部门")
    role: str = Field(default="user", description="用户角色")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="附加元数据"
    )
    
    @validator("id")
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


class Session(BaseModel):
    """会话数据模型
    
    Attributes:
        id: 会话唯一标识
        user_id: 关联用户ID
        data: 会话数据
        created_at: 创建时间
        expires_at: 过期时间
    """
    
    id: str = Field(..., description="会话唯一标识")
    user_id: str = Field(..., description="关联用户ID")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="会话数据"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="过期时间"
    )
    
    @validator("expires_at")
    def validate_expires(cls, v, values):
        if v and "created_at" in values and v < values["created_at"]:
            raise ValueError("expires_at must be after created_at")
        return v


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """任务数据模型
    
    Attributes:
        id: 任务唯一标识
        user_id: 关联用户ID
        type: 任务类型
        status: 任务状态
        input_data: 输入数据
        output_data: 输出数据
        created_at: 创建时间
        updated_at: 更新时间
        completed_at: 完成时间
        error_message: 错误信息
    """
    
    id: str = Field(..., description="任务唯一标识")
    user_id: str = Field(..., description="关联用户ID")
    type: str = Field(..., min_length=1, description="任务类型")
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="任务状态"
    )
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="输入数据"
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="输出数据"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="完成时间"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )


class AnalysisResult(BaseModel):
    """分析结果数据模型
    
    Attributes:
        id: 结果唯一标识
        task_id: 关联任务ID
        type: 分析类型
        input_files: 输入文件列表
        result_data: 分析结果数据
        confidence: 置信度
        created_at: 创建时间
        metadata: 元数据
    """
    
    id: str = Field(..., description="结果唯一标识")
    task_id: str = Field(..., description="关联任务ID")
    type: str = Field(..., min_length=1, description="分析类型")
    input_files: List[str] = Field(
        default_factory=list,
        description="输入文件列表"
    )
    result_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="分析结果数据"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="置信度"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据"
    )


class Document(BaseModel):
    """文档数据模型
    
    Attributes:
        id: 文档唯一标识
        user_id: 关联用户ID
        task_id: 关联任务ID
        title: 文档标题
        content: 文档内容
        file_path: 文件路径
        doc_type: 文档类型
        created_at: 创建时间
        updated_at: 更新时间
        metadata: 元数据
    """
    
    id: str = Field(..., description="文档唯一标识")
    user_id: str = Field(..., description="关联用户ID")
    task_id: Optional[str] = Field(
        default=None,
        description="关联任务ID"
    )
    title: str = Field(default="", max_length=500, description="文档标题")
    content: Optional[str] = Field(default=None, description="文档内容")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    doc_type: str = Field(default="unknown", description="文档类型")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据"
    )


# === MinIO 数据模型 ===

class FileMetadata(BaseModel):
    """文件元数据模型
    
    Attributes:
        object_name: 对象名称
        bucket: 存储桶
        size: 文件大小
        content_type: 内容类型
        last_modified: 最后修改时间
        etag: ETag
        metadata: 自定义元数据
    """
    
    object_name: str = Field(..., description="对象名称")
    bucket: str = Field(..., description="存储桶")
    size: int = Field(default=0, ge=0, description="文件大小（字节）")
    content_type: str = Field(default="application/octet-stream", description="内容类型")
    last_modified: Optional[datetime] = Field(default=None, description="最后修改时间")
    etag: Optional[str] = Field(default=None, description="ETag")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="自定义元数据"
    )


class UploadResult(BaseModel):
    """上传结果模型
    
    Attributes:
        success: 是否成功
        object_name: 对象名称
        etag: ETag
        version_id: 版本ID
        bucket: 存储桶
        size: 文件大小
        metadata: 元数据
    """
    
    success: bool = Field(default=True, description="是否成功")
    object_name: str = Field(..., description="对象名称")
    etag: Optional[str] = Field(default=None, description="ETag")
    version_id: Optional[str] = Field(default=None, description="版本ID")
    bucket: str = Field(..., description="存储桶")
    size: int = Field(default=0, ge=0, description="文件大小（字节）")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据"
    )


# === Redis 数据模型 ===

class LockInfo(BaseModel):
    """锁信息模型
    
    Attributes:
        lock_name: 锁名称
        identifier: 锁标识符
        acquired: 是否获取成功
        ttl: 锁过期时间（秒）
    """
    
    lock_name: str = Field(..., description="锁名称")
    identifier: str = Field(..., description="锁标识符")
    acquired: bool = Field(default=False, description="是否获取成功")
    ttl: int = Field(default=10, ge=1, description="锁过期时间（秒）")


class RateLimitInfo(BaseModel):
    """限流信息模型
    
    Attributes:
        key: 限流键
        allowed: 是否允许
        remaining: 剩余次数
        reset_time: 重置时间
        limit: 限制次数
        window: 窗口大小（秒）
    """
    
    key: str = Field(..., description="限流键")
    allowed: bool = Field(..., description="是否允许")
    remaining: int = Field(default=0, ge=0, description="剩余次数")
    reset_time: datetime = Field(..., description="重置时间")
    limit: int = Field(..., ge=1, description="限制次数")
    window: int = Field(..., ge=1, description="窗口大小（秒）")


# === 配置数据模型 ===

class PostgreSQLConfig(BaseModel):
    """PostgreSQL 配置模型"""
    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口")
    database: str = Field(..., description="数据库名")
    user: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    pool_size: int = Field(default=10, ge=1, description="连接池大小")
    max_overflow: int = Field(default=20, ge=0, description="最大溢出连接")
    pool_timeout: int = Field(default=30, ge=1, description="连接池超时（秒）")


class MinIOConfig(BaseModel):
    """MinIO 配置模型"""
    endpoint: str = Field(..., description="服务端点")
    access_key: str = Field(..., description="访问密钥")
    secret_key: str = Field(..., description="秘密密钥")
    bucket: str = Field(..., description="默认存储桶")
    secure: bool = Field(default=False, description="是否使用HTTPS")
    region: str = Field(default="us-east-1", description="区域")


class RedisConfig(BaseModel):
    """Redis 配置模型"""
    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="端口")
    password: Optional[str] = Field(default=None, description="密码")
    db: int = Field(default=0, ge=0, le=15, description="数据库编号")
    decode_responses: bool = Field(default=True, description="是否解码响应")


__all__ = [
    # PostgreSQL 模型
    "User",
    "Session", 
    "Task",
    "TaskStatus",
    "AnalysisResult",
    "Document",
    # MinIO 模型
    "FileMetadata",
    "UploadResult",
    # Redis 模型
    "LockInfo",
    "RateLimitInfo",
    # 配置模型
    "PostgreSQLConfig",
    "MinIOConfig",
    "RedisConfig"
]
