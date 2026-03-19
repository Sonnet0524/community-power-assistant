"""
Field Info Agent - Tool 基类

提供所有 Tool 的基础功能，包括：
- 异步上下文管理器支持
- 健康检查接口
- 配置管理
- 日志记录

Usage:
    from src.tools.base import BaseTool
    
    class MyTool(BaseTool):
        async def connect(self):
            # 实现连接逻辑
            pass
            
        async def health_check(self) -> bool:
            # 实现健康检查
            return True
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime
from contextlib import asynccontextmanager
import functools

from pydantic import BaseModel, Field
from framework.tools.base import BaseParams, BaseOutput
from framework.tools.metrics import with_metrics

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

T = TypeVar('T')


class ToolLogEntry(BaseModel):
    """Tool 日志条目
    
    统一格式的日志条目，用于记录 Tool 操作
    
    Attributes:
        timestamp: 时间戳
        tool: Tool 名称
        operation: 操作名称
        duration_ms: 执行时长（毫秒）
        status: 状态（success/error）
        error: 错误信息
        metadata: 元数据
    """
    
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tool: str = Field(..., description="Tool 名称")
    operation: str = Field(..., description="操作名称")
    duration_ms: float = Field(default=0.0, ge=0, description="执行时长（毫秒）")
    status: str = Field(default="success", description="状态")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class BaseTool(ABC):
    """Tool 基类
    
    所有 Tool 必须继承此类，实现统一的接口和行为
    
    子类必须实现：
    - connect(): 建立连接
    - health_check(): 健康检查
    - close(): 关闭连接
    
    可选实现：
    - _log_operation(): 自定义日志记录
    
    Example:
        class PostgreSQLTool(BaseTool):
            def __init__(self, config: PostgreSQLConfig):
                super().__init__("postgresql", config)
                self.pool = None
            
            async def connect(self):
                # 实现连接逻辑
                pass
            
            async def health_check(self) -> bool:
                # 实现健康检查
                return True
            
            async def close(self):
                # 实现关闭逻辑
                pass
    
    Usage:
        # 方式1: 使用 async with
        async with PostgreSQLTool(config) as tool:
            result = await tool.query("SELECT * FROM users")
        
        # 方式2: 手动管理
        tool = PostgreSQLTool(config)
        await tool.connect()
        try:
            result = await tool.query("SELECT * FROM users")
        finally:
            await tool.close()
    """
    
    def __init__(self, name: str, config: Optional[Any] = None):
        """初始化 Tool
        
        Args:
            name: Tool 名称
            config: Tool 配置对象
        """
        self.name = name
        self.config = config
        self._connected = False
        self._logger = logging.getLogger(f"tool.{name}")
        self._operation_count = 0
        self._error_count = 0
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接
        
        子类必须实现此方法，建立到后端服务的连接
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        子类必须实现此方法，检查服务健康状态
        
        Returns:
            True 表示健康，False 表示不健康
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接
        
        子类必须实现此方法，关闭连接并释放资源
        """
        pass
    
    async def __aenter__(self) -> 'BaseTool':
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()
    
    def _log_operation(
        self,
        operation: str,
        duration_ms: float,
        status: str = "success",
        error: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            duration_ms: 执行时长（毫秒）
            status: 状态（success/error）
            error: 错误信息
            metadata: 元数据
        """
        log_entry = ToolLogEntry(
            tool=self.name,
            operation=operation,
            duration_ms=duration_ms,
            status=status,
            error=error,
            metadata=metadata
        )
        
        self._operation_count += 1
        
        if status == "error":
            self._error_count += 1
            self._logger.error(
                f"[{self.name}] {operation} failed: {error}",
                extra={"log_entry": log_entry.model_dump()}
            )
        else:
            self._logger.info(
                f"[{self.name}] {operation} completed in {duration_ms:.2f}ms",
                extra={"log_entry": log_entry.model_dump()}
            )
    
    def _handle_error(
        self,
        error: Exception,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理错误
        
        将异常转换为统一的错误格式
        
        Args:
            error: 异常对象
            operation: 操作名称
            details: 错误详情
        
        Returns:
            错误信息字典
        """
        error_info = {
            "error_type": type(error).__name__,
            "message": str(error),
            "operation": operation,
            "details": details or {}
        }
        
        self._logger.error(
            f"[{self.name}] {operation} error: {error}",
            exc_info=True,
            extra={"error_info": error_info}
        )
        
        return error_info
    
    async def _retry_with_backoff(
        self,
        operation: callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ) -> Any:
        """带退避的重试机制
        
        对操作进行重试，每次重试间隔逐渐增加
        
        Args:
            operation: 异步操作函数
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
        
        Returns:
            操作结果
        
        Raises:
            最后一次重试失败的异常
        """
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries:
                    raise
                
                # 计算延迟时间（指数退避）
                delay = min(base_delay * (2 ** attempt), max_delay)
                self._logger.warning(
                    f"[{self.name}] Operation failed (attempt {attempt + 1}), "
                    f"retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取 Tool 统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "tool": self.name,
            "connected": self._connected,
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "error_rate": (
                self._error_count / self._operation_count
                if self._operation_count > 0 else 0.0
            )
        }


__all__ = [
    "ToolLogEntry",
    "BaseTool"
]
