"""
Field Info Agent - Redis Tool

封装 Redis 缓存操作，提供：
- KV 操作封装
- Session 存储
- 分布式锁
- 限流支持

Usage:
    from src.tools.redis_tool import RedisTool
    from src.tools.types import RedisConfig
    
    config = RedisConfig(
        host="localhost",
        port=6379,
        password="redispass"
    )
    
    async with RedisTool(config) as redis:
        # KV 操作
        await redis.set("key", "value", expire=3600)
        value = await redis.get("key")
        
        # Session 存储
        await redis.set("session:user_123", session_data, expire=3600)
        
        # 分布式锁
        acquired = await redis.acquire_lock("task_lock", timeout=10)
        if acquired:
            try:
                # 执行临界区代码
                pass
            finally:
                await redis.release_lock("task_lock")
        
        # 限流检查
        allowed = await redis.rate_limit_check("api_key", limit=100, window=60)
"""

import time
import json
import uuid
from typing import Any, Optional, Dict, List
from datetime import datetime

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = Any
    REDIS_AVAILABLE = False

from src.tools.base import BaseTool
from src.tools.types import RedisConfig, LockInfo, RateLimitInfo
from src.tools.errors import RedisError, ConnectionError, ValidationError


class RedisTool(BaseTool):
    """Redis Tool
    
    封装 Redis 缓存操作
    
    Example:
        config = RedisConfig(
            host="localhost",
            port=6379,
            password="redispass"
        )
        
        redis = RedisTool(config)
        await redis.connect()
        
        # KV 操作
        await redis.set("key", "value", expire=3600)
        value = await redis.get("key")
        
        # 锁
        acquired = await redis.acquire_lock("lock_name")
        if acquired:
            await redis.release_lock("lock_name")
        
        await redis.close()
    """
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """初始化 Redis Tool
        
        Args:
            config: Redis 配置
        """
        super().__init__("redis", config)
        self._config = config
        self._client: Optional[Redis] = None
        
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis is required for RedisTool. "
                "Install with: pip install redis"
            )
    
    async def connect(self) -> None:
        """建立 Redis 连接
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        if self._connected:
            return
        
        try:
            start_time = time.time()
            
            self._client = redis.Redis(
                host=self._config.host,
                port=self._config.port,
                password=self._config.password,
                db=self._config.db,
                decode_responses=self._config.decode_responses
            )
            
            # 测试连接
            await self._client.ping()
            
            self._connected = True
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("connect", duration_ms, metadata={
                "host": self._config.host,
                "port": self._config.port
            })
            
        except Exception as e:
            raise ConnectionError(
                message=f"Failed to connect to Redis: {str(e)}",
                details={
                    "host": self._config.host,
                    "port": self._config.port
                }
            )
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self._connected or not self._client:
            return False
        
        try:
            start_time = time.time()
            await self._client.ping()
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("health_check", duration_ms)
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None
        
        self._connected = False
        self._log_operation("close", 0)
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值
        
        Args:
            value: 任意值
        
        Returns:
            序列化后的字符串
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化值
        
        Args:
            value: 字符串值
        
        Returns:
            反序列化后的值
        """
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    # === KV 操作 ===
    
    async def get(self, key: str) -> Any:
        """获取值
        
        Args:
            key: 键名
        
        Returns:
            值或 None
        
        Raises:
            RedisError: 操作失败时抛出
        """
        start_time = time.time()
        
        try:
            value = await self._client.get(key)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("get", duration_ms, metadata={"key": key})
            
            return self._deserialize_value(value)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "get", {"key": key})
            self._log_operation("get", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to get key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """设置值
        
        Args:
            key: 键名
            value: 值
            expire: 过期时间（秒）
        
        Returns:
            是否设置成功
        """
        start_time = time.time()
        
        try:
            serialized = self._serialize_value(value)
            
            if expire:
                result = await self._client.setex(key, expire, serialized)
            else:
                result = await self._client.set(key, serialized)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("set", duration_ms, metadata={
                "key": key,
                "expire": expire
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "set", {"key": key})
            self._log_operation("set", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to set key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def delete(self, key: str) -> int:
        """删除键
        
        Args:
            key: 键名
        
        Returns:
            删除的键数量
        """
        start_time = time.time()
        
        try:
            result = await self._client.delete(key)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("delete", duration_ms, metadata={"key": key})
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "delete", {"key": key})
            self._log_operation("delete", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to delete key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间
        
        Args:
            key: 键名
            seconds: 过期秒数
        
        Returns:
            是否设置成功
        """
        start_time = time.time()
        
        try:
            result = await self._client.expire(key, seconds)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("expire", duration_ms, metadata={
                "key": key,
                "seconds": seconds
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "expire", {"key": key})
            self._log_operation("expire", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to set expire for key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 键名
        
        Returns:
            是否存在
        """
        start_time = time.time()
        
        try:
            result = await self._client.exists(key)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("exists", duration_ms, metadata={"key": key})
            
            return bool(result)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "exists", {"key": key})
            self._log_operation("exists", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to check existence of key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间
        
        Args:
            key: 键名
        
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示不存在
        """
        start_time = time.time()
        
        try:
            result = await self._client.ttl(key)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("ttl", duration_ms, metadata={"key": key})
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "ttl", {"key": key})
            self._log_operation("ttl", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to get TTL for key {key}: {str(e)}",
                details={"key": key}
            )
    
    # === Session 存储 ===
    
    async def set_session(
        self, 
        session_id: str, 
        data: Dict[str, Any], 
        expire: int = 3600
    ) -> bool:
        """存储 Session
        
        Args:
            session_id: 会话ID
            data: 会话数据
            expire: 过期时间（秒）
        
        Returns:
            是否存储成功
        """
        key = f"session:{session_id}"
        return await self.set(key, data, expire)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取 Session
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话数据或 None
        """
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str) -> int:
        """删除 Session
        
        Args:
            session_id: 会话ID
        
        Returns:
            删除的键数量
        """
        key = f"session:{session_id}"
        return await self.delete(key)
    
    async def extend_session(self, session_id: str, expire: int = 3600) -> bool:
        """延长 Session 过期时间
        
        Args:
            session_id: 会话ID
            expire: 新的过期时间（秒）
        
        Returns:
            是否设置成功
        """
        key = f"session:{session_id}"
        return await self.expire(key, expire)
    
    # === 分布式锁 ===
    
    async def acquire_lock(
        self, 
        lock_name: str, 
        timeout: int = 10,
        blocking: bool = False,
        blocking_timeout: Optional[int] = None
    ) -> LockInfo:
        """获取分布式锁
        
        使用 Redis SETNX 实现分布式锁
        
        Args:
            lock_name: 锁名称
            timeout: 锁过期时间（秒）
            blocking: 是否阻塞等待
            blocking_timeout: 阻塞等待超时时间（秒）
        
        Returns:
            锁信息对象
        
        Example:
            lock = await redis.acquire_lock("task_lock", timeout=10)
            if lock.acquired:
                try:
                    # 执行临界区代码
                    pass
                finally:
                    await redis.release_lock("task_lock", lock.identifier)
        """
        start_time = time.time()
        identifier = str(uuid.uuid4())
        key = f"lock:{lock_name}"
        
        try:
            if blocking:
                # 阻塞等待模式
                end_time = time.time() + (blocking_timeout or timeout)
                while time.time() < end_time:
                    acquired = await self._client.set(
                        key, identifier, nx=True, ex=timeout
                    )
                    if acquired:
                        break
                    await asyncio.sleep(0.1)
                else:
                    # 超时
                    duration_ms = (time.time() - start_time) * 1000
                    self._log_operation("acquire_lock", duration_ms, metadata={
                        "lock_name": lock_name,
                        "acquired": False
                    })
                    return LockInfo(
                        lock_name=lock_name,
                        identifier=identifier,
                        acquired=False,
                        ttl=timeout
                    )
            else:
                # 非阻塞模式
                acquired = await self._client.set(
                    key, identifier, nx=True, ex=timeout
                )
                if not acquired:
                    duration_ms = (time.time() - start_time) * 1000
                    self._log_operation("acquire_lock", duration_ms, metadata={
                        "lock_name": lock_name,
                        "acquired": False
                    })
                    return LockInfo(
                        lock_name=lock_name,
                        identifier=identifier,
                        acquired=False,
                        ttl=timeout
                    )
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("acquire_lock", duration_ms, metadata={
                "lock_name": lock_name,
                "acquired": True
            })
            
            return LockInfo(
                lock_name=lock_name,
                identifier=identifier,
                acquired=True,
                ttl=timeout
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "acquire_lock", {"lock_name": lock_name})
            self._log_operation("acquire_lock", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to acquire lock {lock_name}: {str(e)}",
                details={"lock_name": lock_name}
            )
    
    async def release_lock(self, lock_name: str, identifier: str) -> bool:
        """释放分布式锁
        
        Args:
            lock_name: 锁名称
            identifier: 锁标识符（从 acquire_lock 获取）
        
        Returns:
            是否释放成功
        
        Example:
            lock = await redis.acquire_lock("task_lock")
            if lock.acquired:
                try:
                    pass
                finally:
                    await redis.release_lock("task_lock", lock.identifier)
        """
        start_time = time.time()
        key = f"lock:{lock_name}"
        
        try:
            # 使用 Lua 脚本确保原子性
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await self._client.eval(lua_script, 1, key, identifier)
            released = result == 1
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("release_lock", duration_ms, metadata={
                "lock_name": lock_name,
                "released": released
            })
            
            return released
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "release_lock", {"lock_name": lock_name})
            self._log_operation("release_lock", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to release lock {lock_name}: {str(e)}",
                details={"lock_name": lock_name}
            )
    
    # === 限流支持 ===
    
    async def rate_limit_check(
        self,
        key: str,
        limit: int = 100,
        window: int = 60
    ) -> RateLimitInfo:
        """限流检查
        
        使用滑动窗口算法实现限流
        
        Args:
            key: 限流键（如用户ID、IP地址）
            limit: 窗口内允许的最大请求数
            window: 窗口大小（秒）
        
        Returns:
            限流信息对象
        
        Example:
            info = await redis.rate_limit_check("api_user_123", limit=100, window=60)
            if info.allowed:
                # 处理请求
                pass
            else:
                # 返回 429 Too Many Requests
                pass
        """
        start_time = time.time()
        now = time.time()
        window_start = now - window
        
        try:
            redis_key = f"rate_limit:{key}"
            
            # 使用 Redis 事务
            pipe = self._client.pipeline()
            
            # 移除窗口外的记录
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # 获取当前窗口内的请求数
            pipe.zcard(redis_key)
            
            # 添加当前请求
            pipe.zadd(redis_key, {str(now): now})
            
            # 设置过期时间
            pipe.expire(redis_key, window + 1)
            
            results = await pipe.execute()
            current_count = results[1]
            
            allowed = current_count <= limit
            reset_time = datetime.fromtimestamp(now + window)
            remaining = max(0, limit - current_count)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("rate_limit_check", duration_ms, metadata={
                "key": key,
                "allowed": allowed,
                "current_count": current_count
            })
            
            return RateLimitInfo(
                key=key,
                allowed=allowed,
                remaining=remaining,
                reset_time=reset_time,
                limit=limit,
                window=window
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "rate_limit_check", {"key": key})
            self._log_operation("rate_limit_check", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to check rate limit for {key}: {str(e)}",
                details={"key": key}
            )
    
    # === 辅助功能 ===
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """原子递增
        
        Args:
            key: 键名
            amount: 递增量
        
        Returns:
            递增后的值
        """
        start_time = time.time()
        
        try:
            result = await self._client.incrby(key, amount)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("increment", duration_ms, metadata={
                "key": key,
                "amount": amount
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "increment", {"key": key})
            self._log_operation("increment", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to increment key {key}: {str(e)}",
                details={"key": key}
            )
    
    async def set_add(self, key: str, *members) -> int:
        """向集合添加成员
        
        Args:
            key: 集合键名
            members: 成员值
        
        Returns:
            添加成功的成员数
        """
        start_time = time.time()
        
        try:
            result = await self._client.sadd(key, *members)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("set_add", duration_ms, metadata={
                "key": key,
                "members_count": len(members)
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "set_add", {"key": key})
            self._log_operation("set_add", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to add to set {key}: {str(e)}",
                details={"key": key}
            )
    
    async def set_members(self, key: str) -> set:
        """获取集合所有成员
        
        Args:
            key: 集合键名
        
        Returns:
            成员集合
        """
        start_time = time.time()
        
        try:
            result = await self._client.smembers(key)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("set_members", duration_ms, metadata={"key": key})
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "set_members", {"key": key})
            self._log_operation("set_members", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to get set members {key}: {str(e)}",
                details={"key": key}
            )
    
    async def list_push(self, key: str, *values) -> int:
        """向列表右侧添加元素
        
        Args:
            key: 列表键名
            values: 值列表
        
        Returns:
            列表长度
        """
        start_time = time.time()
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            result = await self._client.rpush(key, *serialized_values)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("list_push", duration_ms, metadata={
                "key": key,
                "values_count": len(values)
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "list_push", {"key": key})
            self._log_operation("list_push", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to push to list {key}: {str(e)}",
                details={"key": key}
            )
    
    async def list_range(
        self, 
        key: str, 
        start: int = 0, 
        end: int = -1
    ) -> List[Any]:
        """获取列表范围元素
        
        Args:
            key: 列表键名
            start: 起始索引
            end: 结束索引（-1 表示到最后）
        
        Returns:
            元素列表
        """
        start_time = time.time()
        
        try:
            result = await self._client.lrange(key, start, end)
            deserialized = [self._deserialize_value(v) for v in result]
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("list_range", duration_ms, metadata={
                "key": key,
                "start": start,
                "end": end
            })
            
            return deserialized
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "list_range", {"key": key})
            self._log_operation("list_range", duration_ms, "error", error_info)
            raise RedisError(
                message=f"Failed to get list range {key}: {str(e)}",
                details={"key": key}
            )


# 导入 asyncio
import asyncio

__all__ = [
    "RedisTool"
]
