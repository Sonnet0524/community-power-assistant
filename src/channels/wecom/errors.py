"""
企业微信API错误处理模块
定义错误类型和处理策略
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
import time
from functools import wraps


logger = logging.getLogger(__name__)


class WeComErrorCode(Enum):
    """企业微信错误码"""
    # 系统错误
    SYSTEM_ERROR = -1
    SYSTEM_BUSY = -2
    
    # 加解密错误
    INVALID_SIGNATURE = -40001
    INVALID_XML = -40002
    INVALID_CORP_ID = -40003
    INVALID_AES_KEY = -40004
    INVALID_MSG = -40005
    INVALID_BUFFER = -40006
    INVALID_ENCODE = -40007
    INVALID_DECODE = -40008
    INVALID_MEDIA_ID = -40009
    
    # Token相关
    ACCESS_TOKEN_EXPIRED = 42001
    ACCESS_TOKEN_INVALID = 40014
    
    # 消息发送
    INVALID_USERID = 40031
    INVALID_PARTY_ID = 40032
    MESSAGE_SIZE_EXCEED = 40033
    MESSAGE_CONTENT_INVALID = 40036
    
    # 媒体文件
    MEDIA_FILE_NOT_FOUND = 40006
    MEDIA_FILE_SIZE_EXCEED = 40007
    MEDIA_FILE_TYPE_INVALID = 40008
    
    # 频率限制
    API_RATE_LIMIT = 45009
    
    # 网络错误
    NETWORK_ERROR = 6001
    TIMEOUT_ERROR = 6002


@dataclass
class WeComError:
    """企业微信错误"""
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class WeComAPIException(Exception):
    """企业微信API异常基类"""
    
    def __init__(self, error: WeComError, original_error: Optional[Exception] = None):
        self.error = error
        self.original_error = original_error
        super().__init__(str(error))
    
    @property
    def code(self) -> int:
        return self.error.code
    
    @property
    def message(self) -> str:
        return self.error.message
    
    @property
    def is_retryable(self) -> bool:
        """是否可重试的错误"""
        retryable_codes = [
            WeComErrorCode.SYSTEM_ERROR.value,
            WeComErrorCode.SYSTEM_BUSY.value,
            WeComErrorCode.ACCESS_TOKEN_EXPIRED.value,
            WeComErrorCode.NETWORK_ERROR.value,
            WeComErrorCode.TIMEOUT_ERROR.value,
            WeComErrorCode.API_RATE_LIMIT.value
        ]
        return self.code in retryable_codes


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[tuple] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or (
            WeComAPIException,
            ConnectionError,
            TimeoutError
        )
    
    def get_delay(self, attempt: int) -> float:
        """获取第attempt次的延迟时间（指数退避）"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


def with_retry(config: Optional[RetryConfig] = None):
    """
    重试装饰器
    
    Args:
        config: 重试配置
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否应该重试
                    should_retry = (
                        attempt < config.max_retries and
                        isinstance(e, config.retryable_exceptions)
                    )
                    
                    if isinstance(e, WeComAPIException) and not e.is_retryable:
                        should_retry = False
                    
                    if not should_retry:
                        raise
                    
                    # 计算延迟并等待
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"函数 {func.__name__} 第{attempt + 1}次调用失败: {e}, "
                        f"{delay}秒后重试..."
                    )
                    await asyncio.sleep(delay)
            
            # 所有重试都失败
            if last_exception:
                raise last_exception
            raise RuntimeError("重试失败但无异常记录")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import asyncio
            # 对于同步函数，使用同步重试
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    should_retry = (
                        attempt < config.max_retries and
                        isinstance(e, config.retryable_exceptions)
                    )
                    
                    if isinstance(e, WeComAPIException) and not e.is_retryable:
                        should_retry = False
                    
                    if not should_retry:
                        raise
                    
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"函数 {func.__name__} 第{attempt + 1}次调用失败: {e}, "
                        f"{delay}秒后重试..."
                    )
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            raise RuntimeError("重试失败但无异常记录")
        
        # 根据函数类型返回对应的wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """熔断器"""
    
    STATE_CLOSED = 'closed'      # 正常状态
    STATE_OPEN = 'open'          # 熔断状态
    STATE_HALF_OPEN = 'half_open'  # 半开状态
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
    
    def record_success(self):
        """记录成功"""
        if self.state == self.STATE_HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self._close_circuit()
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == self.STATE_HALF_OPEN:
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == self.STATE_CLOSED:
            return True
        
        if self.state == self.STATE_OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._half_open_circuit()
                return True
            return False
        
        if self.state == self.STATE_HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return True
    
    def _open_circuit(self):
        """打开熔断器"""
        self.state = self.STATE_OPEN
        logger.error("熔断器打开，暂停服务调用")
    
    def _close_circuit(self):
        """关闭熔断器"""
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        logger.info("熔断器关闭，恢复正常服务")
    
    def _half_open_circuit(self):
        """半开熔断器"""
        self.state = self.STATE_HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        logger.info("熔断器半开，尝试恢复服务")


def with_circuit_breaker(breaker: CircuitBreaker):
    """熔断器装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise WeComAPIException(
                    WeComError(
                        code=WeComErrorCode.SYSTEM_BUSY.value,
                        message="服务暂时不可用，请稍后重试"
                    )
                )
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise WeComAPIException(
                    WeComError(
                        code=WeComErrorCode.SYSTEM_BUSY.value,
                        message="服务暂时不可用，请稍后重试"
                    )
                )
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class ErrorHandler:
    """错误处理器"""
    
    # 错误码到友好消息的映射
    ERROR_MESSAGES = {
        WeComErrorCode.INVALID_SIGNATURE.value: "消息签名验证失败，请检查配置",
        WeComErrorCode.INVALID_AES_KEY.value: "加密密钥错误，请检查EncodingAESKey配置",
        WeComErrorCode.ACCESS_TOKEN_EXPIRED.value: "访问令牌已过期，正在重新获取...",
        WeComErrorCode.ACCESS_TOKEN_INVALID.value: "访问令牌无效，请检查CorpID和Secret",
        WeComErrorCode.INVALID_USERID.value: "用户ID不存在，请检查用户是否已关注应用",
        WeComErrorCode.MESSAGE_SIZE_EXCEED.value: "消息内容过长，请缩短后重试",
        WeComErrorCode.MEDIA_FILE_NOT_FOUND.value: "媒体文件不存在或已过期",
        WeComErrorCode.API_RATE_LIMIT.value: "请求过于频繁，请稍后再试",
        WeComErrorCode.NETWORK_ERROR.value: "网络连接异常，请检查网络设置",
        WeComErrorCode.TIMEOUT_ERROR.value: "请求超时，请稍后重试"
    }
    
    @staticmethod
    def get_friendly_message(error_code: int, default_message: Optional[str] = None) -> str:
        """获取友好的错误消息"""
        return ErrorHandler.ERROR_MESSAGES.get(
            error_code,
            default_message or f"操作失败，错误码：{error_code}"
        )
    
    @staticmethod
    def handle_error(error: Exception) -> str:
        """处理错误并返回用户友好的消息"""
        if isinstance(error, WeComAPIException):
            return ErrorHandler.get_friendly_message(error.code, error.message)
        
        if isinstance(error, ConnectionError):
            return "网络连接失败，请检查网络后重试"
        
        if isinstance(error, TimeoutError):
            return "请求超时，请稍后重试"
        
        logger.error(f"未处理的错误: {error}")
        return "系统繁忙，请稍后重试"


# 导入asyncio用于重试装饰器
import asyncio
