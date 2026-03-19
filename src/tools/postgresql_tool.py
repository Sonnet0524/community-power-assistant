"""
Field Info Agent - PostgreSQL Tool

封装 PostgreSQL 数据库操作，提供：
- 连接池管理
- CRUD 操作
- 事务支持
- SQL 注入防护

Usage:
    from src.tools.postgresql_tool import PostgreSQLTool
    from src.tools.types import PostgreSQLConfig
    
    config = PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="field_agent",
        user="field_user",
        password="field_pass"
    )
    
    async with PostgreSQLTool(config) as pg:
        # 查询
        users = await pg.query("SELECT * FROM users WHERE id = $1", {"id": "user_123"})
        
        # 事务
        async with pg.transaction() as txn:
            await txn.execute("INSERT INTO users (id, name) VALUES ($1, $2)", 
                            {"id": "new_user", "name": "张三"})
            
        # 表操作
        user = await pg.get_user("user_123")
        await pg.create_user(User(id="new_user", name="李四"))
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

try:
    import asyncpg
    from asyncpg import Connection, Pool
    ASYNC_PG_AVAILABLE = True
except ImportError:
    ASYNC_PG_AVAILABLE = False
    Connection = Any
    Pool = Any

from src.tools.base import BaseTool
from src.tools.types import (
    PostgreSQLConfig, User, Session, Task, 
    AnalysisResult, Document, TaskStatus
)
from src.tools.errors import PostgreSQLError, ConnectionError, ValidationError, NotFoundError


class TransactionContext:
    """事务上下文管理器
    
    提供事务的原子性操作支持
    
    Example:
        async with pg.transaction() as txn:
            await txn.execute("INSERT INTO ...")
            await txn.execute("UPDATE ...")
    """
    
    def __init__(self, connection: Connection):
        self._connection = connection
        self._transaction = None
    
    async def __aenter__(self) -> 'TransactionContext':
        """进入事务上下文"""
        self._transaction = self._connection.transaction()
        await self._transaction.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出事务上下文"""
        if exc_type is None:
            await self._transaction.commit()
        else:
            await self._transaction.rollback()
    
    async def execute(self, sql: str, params: Dict[str, Any] = None) -> int:
        """执行 SQL 语句
        
        Args:
            sql: SQL 语句（使用 $1, $2 作为参数占位符）
            params: 参数字典
        
        Returns:
            影响的行数
        """
        if params:
            # 将字典转换为元组
            param_list = [params.get(f"${i+1}", params.get(k)) 
                         for i, k in enumerate(params.keys())]
            result = await self._connection.execute(sql, *param_list)
        else:
            result = await self._connection.execute(sql)
        
        # 解析结果获取行数
        if result.startswith("INSERT"):
            return 1
        elif result.startswith("UPDATE") or result.startswith("DELETE"):
            parts = result.split()
            return int(parts[-1]) if len(parts) > 1 else 0
        return 0
    
    async def query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            sql: SQL 查询语句
            params: 参数字典
        
        Returns:
            查询结果列表
        """
        if params:
            param_list = [params.get(f"${i+1}", params.get(k)) 
                         for i, k in enumerate(params.keys())]
            records = await self._connection.fetch(sql, *param_list)
        else:
            records = await self._connection.fetch(sql)
        
        return [dict(record) for record in records]


class PostgreSQLTool(BaseTool):
    """PostgreSQL Tool
    
    封装 PostgreSQL 数据库操作，提供异步连接池和 CRUD 操作
    
    Example:
        config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="field_agent",
            user="field_user",
            password="field_pass"
        )
        
        pg = PostgreSQLTool(config)
        await pg.connect()
        
        # 查询
        users = await pg.query("SELECT * FROM users LIMIT 10")
        
        # 执行
        rows = await pg.execute(
            "UPDATE users SET name = $1 WHERE id = $2",
            {"name": "张三", "id": "user_123"}
        )
        
        # 事务
        async with pg.transaction() as txn:
            await txn.execute("INSERT INTO ...")
        
        await pg.close()
    """
    
    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        """初始化 PostgreSQL Tool
        
        Args:
            config: PostgreSQL 配置，如果为 None 则从环境变量加载
        """
        super().__init__("postgresql", config)
        self._config = config
        self._pool: Optional[Pool] = None
        self._connection: Optional[Connection] = None
        
        if not ASYNC_PG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQLTool. "
                "Install with: pip install asyncpg"
            )
    
    async def connect(self) -> None:
        """建立数据库连接
        
        创建连接池并建立连接
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        if self._connected:
            return
        
        try:
            start_time = time.time()
            
            self._pool = await asyncpg.create_pool(
                host=self._config.host,
                port=self._config.port,
                database=self._config.database,
                user=self._config.user,
                password=self._config.password,
                min_size=1,
                max_size=self._config.pool_size,
                max_inactive_time=self._config.pool_timeout,
                command_timeout=30
            )
            
            # 获取一个连接用于直接操作
            self._connection = await self._pool.acquire()
            
            self._connected = True
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("connect", duration_ms, metadata={
                "host": self._config.host,
                "database": self._config.database
            })
            
        except Exception as e:
            raise ConnectionError(
                message=f"Failed to connect to PostgreSQL: {str(e)}",
                details={
                    "host": self._config.host,
                    "port": self._config.port,
                    "database": self._config.database
                }
            )
    
    async def health_check(self) -> bool:
        """健康检查
        
        执行简单的查询检查数据库连接状态
        
        Returns:
            True 表示健康，False 表示不健康
        """
        if not self._connected or not self._connection:
            return False
        
        try:
            start_time = time.time()
            await self._connection.fetchval("SELECT 1")
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("health_check", duration_ms)
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self._connection and self._pool:
            await self._pool.release(self._connection)
            self._connection = None
        
        if self._pool:
            await self._pool.close()
            self._pool = None
        
        self._connected = False
        self._log_operation("close", 0)
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[TransactionContext, None]:
        """获取事务上下文
        
        Yields:
            TransactionContext: 事务上下文对象
        
        Example:
            async with pg.transaction() as txn:
                await txn.execute("INSERT INTO ...")
                await txn.execute("UPDATE ...")
        """
        if not self._connection:
            raise PostgreSQLError("Not connected to database")
        
        txn = TransactionContext(self._connection)
        async with txn:
            yield txn
    
    def _convert_params(self, params: Optional[Dict[str, Any]]) -> tuple:
        """转换参数字典为 asyncpg 格式
        
        Args:
            params: 参数字典
        
        Returns:
            (sql_with_placeholders, param_list)
        """
        if not params:
            return None, []
        
        # 转换为列表，保持顺序
        param_list = []
        for key in params.keys():
            value = params[key]
            # 处理 datetime 类型
            if isinstance(value, datetime):
                param_list.append(value)
            # 处理列表类型
            elif isinstance(value, list):
                param_list.append(value)
            else:
                param_list.append(value)
        
        return param_list
    
    async def query(
        self, 
        sql: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行查询
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果列表
        
        Raises:
            PostgreSQLError: 查询失败时抛出
        """
        start_time = time.time()
        
        try:
            param_list = self._convert_params(params)
            
            if param_list:
                records = await self._connection.fetch(sql, *param_list)
            else:
                records = await self._connection.fetch(sql)
            
            results = [dict(record) for record in records]
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("query", duration_ms, metadata={
                "sql": sql[:100],
                "rows": len(results)
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "query", {"sql": sql[:100]})
            self._log_operation("query", duration_ms, "error", error_info)
            raise PostgreSQLError(
                message=f"Query failed: {str(e)}",
                details={"sql": sql[:100]}
            )
    
    async def execute(
        self, 
        sql: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """执行 SQL 语句
        
        Args:
            sql: SQL 语句
            params: 执行参数
        
        Returns:
            影响的行数
        
        Raises:
            PostgreSQLError: 执行失败时抛出
        """
        start_time = time.time()
        
        try:
            param_list = self._convert_params(params)
            
            if param_list:
                result = await self._connection.execute(sql, *param_list)
            else:
                result = await self._connection.execute(sql)
            
            # 解析结果获取行数
            rows_affected = 0
            if result.startswith("INSERT"):
                rows_affected = 1
            elif result.startswith("UPDATE") or result.startswith("DELETE"):
                parts = result.split()
                rows_affected = int(parts[-1]) if len(parts) > 1 else 0
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("execute", duration_ms, metadata={
                "sql": sql[:100],
                "rows_affected": rows_affected
            })
            
            return rows_affected
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "execute", {"sql": sql[:100]})
            self._log_operation("execute", duration_ms, "error", error_info)
            raise PostgreSQLError(
                message=f"Execute failed: {str(e)}",
                details={"sql": sql[:100]}
            )
    
    async def fetchval(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """获取单个值
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
        
        Returns:
            单个值或 None
        """
        start_time = time.time()
        
        try:
            param_list = self._convert_params(params)
            
            if param_list:
                result = await self._connection.fetchval(sql, *param_list)
            else:
                result = await self._connection.fetchval(sql)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("fetchval", duration_ms)
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "fetchval", {"sql": sql[:100]})
            self._log_operation("fetchval", duration_ms, "error", error_info)
            raise PostgreSQLError(
                message=f"Fetchval failed: {str(e)}",
                details={"sql": sql[:100]}
            )
    
    # === 用户表操作 ===
    
    async def create_user(self, user: User) -> User:
        """创建用户
        
        Args:
            user: 用户对象
        
        Returns:
            创建的用户对象
        """
        sql = """
            INSERT INTO users (id, name, department, role, created_at, updated_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await self.execute(sql, {
            "id": user.id,
            "name": user.name,
            "department": user.department,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "metadata": user.metadata
        })
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户对象或 None
        
        Raises:
            NotFoundError: 用户不存在时抛出
        """
        sql = "SELECT * FROM users WHERE id = $1"
        result = await self.query(sql, {"id": user_id})
        
        if not result:
            return None
        
        return User(**result[0])
    
    async def update_user(self, user: User) -> User:
        """更新用户
        
        Args:
            user: 用户对象
        
        Returns:
            更新后的用户对象
        """
        user.updated_at = datetime.now()
        
        sql = """
            UPDATE users 
            SET name = $1, department = $2, role = $3, updated_at = $4, metadata = $5
            WHERE id = $6
        """
        rows = await self.execute(sql, {
            "name": user.name,
            "department": user.department,
            "role": user.role,
            "updated_at": user.updated_at,
            "metadata": user.metadata,
            "id": user.id
        })
        
        if rows == 0:
            raise NotFoundError(f"User {user.id} not found")
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否删除成功
        """
        sql = "DELETE FROM users WHERE id = $1"
        rows = await self.execute(sql, {"id": user_id})
        return rows > 0
    
    # === 会话表操作 ===
    
    async def create_session(self, session: Session) -> Session:
        """创建会话"""
        sql = """
            INSERT INTO sessions (id, user_id, data, created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5)
        """
        await self.execute(sql, {
            "id": session.id,
            "user_id": session.user_id,
            "data": session.data,
            "created_at": session.created_at,
            "expires_at": session.expires_at
        })
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        sql = "SELECT * FROM sessions WHERE id = $1"
        result = await self.query(sql, {"id": session_id})
        
        if not result:
            return None
        
        return Session(**result[0])
    
    async def update_session(self, session: Session) -> Session:
        """更新会话"""
        sql = """
            UPDATE sessions 
            SET data = $1, expires_at = $2
            WHERE id = $3
        """
        rows = await self.execute(sql, {
            "data": session.data,
            "expires_at": session.expires_at,
            "id": session.id
        })
        
        if rows == 0:
            raise NotFoundError(f"Session {session.id} not found")
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        sql = "DELETE FROM sessions WHERE id = $1"
        rows = await self.execute(sql, {"id": session_id})
        return rows > 0
    
    # === 任务表操作 ===
    
    async def create_task(self, task: Task) -> Task:
        """创建任务"""
        sql = """
            INSERT INTO tasks (id, user_id, type, status, input_data, output_data, 
                             created_at, updated_at, completed_at, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        await self.execute(sql, {
            "id": task.id,
            "user_id": task.user_id,
            "type": task.type,
            "status": task.status.value,
            "input_data": task.input_data,
            "output_data": task.output_data,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message
        })
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        sql = "SELECT * FROM tasks WHERE id = $1"
        result = await self.query(sql, {"id": task_id})
        
        if not result:
            return None
        
        return Task(**result[0])
    
    async def update_task(self, task: Task) -> Task:
        """更新任务"""
        task.updated_at = datetime.now()
        
        sql = """
            UPDATE tasks 
            SET status = $1, output_data = $2, updated_at = $3, 
                completed_at = $4, error_message = $5
            WHERE id = $6
        """
        rows = await self.execute(sql, {
            "status": task.status.value,
            "output_data": task.output_data,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message,
            "id": task.id
        })
        
        if rows == 0:
            raise NotFoundError(f"Task {task.id} not found")
        
        return task
    
    async def list_tasks(
        self, 
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """列出任务
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            任务列表
        """
        conditions = []
        params = {}
        
        if user_id:
            conditions.append("user_id = $1")
            params["user_id"] = user_id
        
        if status:
            param_key = f"${len(params) + 1}"
            conditions.append(f"status = {param_key}")
            params["status"] = status.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f"""
            SELECT * FROM tasks {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params["limit"] = limit
        params["offset"] = offset
        
        results = await self.query(sql, params)
        return [Task(**row) for row in results]
    
    # === 分析结果表操作 ===
    
    async def save_analysis(self, result: AnalysisResult) -> AnalysisResult:
        """保存分析结果"""
        sql = """
            INSERT INTO analysis_results 
            (id, task_id, type, input_files, result_data, confidence, created_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        await self.execute(sql, {
            "id": result.id,
            "task_id": result.task_id,
            "type": result.type,
            "input_files": result.input_files,
            "result_data": result.result_data,
            "confidence": result.confidence,
            "created_at": result.created_at,
            "metadata": result.metadata
        })
        return result
    
    async def get_analysis(self, result_id: str) -> Optional[AnalysisResult]:
        """获取分析结果"""
        sql = "SELECT * FROM analysis_results WHERE id = $1"
        result = await self.query(sql, {"id": result_id})
        
        if not result:
            return None
        
        return AnalysisResult(**result[0])
    
    async def list_analysis(
        self, 
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AnalysisResult]:
        """列出分析结果"""
        if task_id:
            sql = "SELECT * FROM analysis_results WHERE task_id = $1 ORDER BY created_at DESC LIMIT $2"
            results = await self.query(sql, {"task_id": task_id, "limit": limit})
        else:
            sql = "SELECT * FROM analysis_results ORDER BY created_at DESC LIMIT $1"
            results = await self.query(sql, {"limit": limit})
        
        return [AnalysisResult(**row) for row in results]
    
    # === 文档表操作 ===
    
    async def save_document(self, document: Document) -> Document:
        """保存文档"""
        sql = """
            INSERT INTO documents 
            (id, user_id, task_id, title, content, file_path, doc_type, created_at, updated_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        await self.execute(sql, {
            "id": document.id,
            "user_id": document.user_id,
            "task_id": document.task_id,
            "title": document.title,
            "content": document.content,
            "file_path": document.file_path,
            "doc_type": document.doc_type,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "metadata": document.metadata
        })
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        sql = "SELECT * FROM documents WHERE id = $1"
        result = await self.query(sql, {"id": document_id})
        
        if not result:
            return None
        
        return Document(**result[0])
    
    async def update_document(self, document: Document) -> Document:
        """更新文档"""
        document.updated_at = datetime.now()
        
        sql = """
            UPDATE documents 
            SET title = $1, content = $2, file_path = $3, doc_type = $4, 
                updated_at = $5, metadata = $6
            WHERE id = $7
        """
        rows = await self.execute(sql, {
            "title": document.title,
            "content": document.content,
            "file_path": document.file_path,
            "doc_type": document.doc_type,
            "updated_at": document.updated_at,
            "metadata": document.metadata,
            "id": document.id
        })
        
        if rows == 0:
            raise NotFoundError(f"Document {document.id} not found")
        
        return document


__all__ = [
    "PostgreSQLTool",
    "TransactionContext"
]
