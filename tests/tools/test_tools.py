"""
Field Info Agent - Tool 单元测试

测试 PostgreSQL、MinIO、Redis Tool 的功能

运行测试:
    pytest tests/tools/ -v --cov=src.tools --cov-report=html
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any


# 模拟依赖
@pytest.fixture(autouse=True)
def mock_dependencies():
    """模拟所有外部依赖"""
    with patch.dict('sys.modules', {
        'asyncpg': Mock(),
        'minio': Mock(),
        'minio.error': Mock(),
        'redis': Mock(),
        'redis.asyncio': Mock()
    }):
        yield


# ================================
# Base Tool Tests
# ================================

class TestBaseTool:
    """测试 Tool 基类"""
    
    @pytest.fixture
    def base_tool(self):
        """创建测试用的 Tool 实例"""
        from src.tools.base import BaseTool
        
        class TestTool(BaseTool):
            async def connect(self):
                self._connected = True
            
            async def health_check(self):
                return self._connected
            
            async def close(self):
                self._connected = False
        
        return TestTool("test_tool")
    
    @pytest.mark.asyncio
    async def test_init(self, base_tool):
        """测试初始化"""
        assert base_tool.name == "test_tool"
        assert not base_tool.is_connected
        assert base_tool._operation_count == 0
        assert base_tool._error_count == 0
    
    @pytest.mark.asyncio
    async def test_connect(self, base_tool):
        """测试连接"""
        await base_tool.connect()
        assert base_tool.is_connected
    
    @pytest.mark.asyncio
    async def test_close(self, base_tool):
        """测试关闭"""
        await base_tool.connect()
        await base_tool.close()
        assert not base_tool.is_connected
    
    @pytest.mark.asyncio
    async def test_context_manager(self, base_tool):
        """测试异步上下文管理器"""
        async with base_tool as tool:
            assert tool.is_connected
        assert not tool.is_connected
    
    @pytest.mark.asyncio
    async def test_health_check(self, base_tool):
        """测试健康检查"""
        assert not await base_tool.health_check()
        await base_tool.connect()
        assert await base_tool.health_check()
    
    def test_log_operation(self, base_tool):
        """测试日志记录"""
        base_tool._log_operation("test_op", 50.0, metadata={"key": "value"})
        assert base_tool._operation_count == 1
    
    def test_log_operation_error(self, base_tool):
        """测试错误日志记录"""
        error_info = {"error_type": "TestError", "message": "test"}
        base_tool._log_operation("test_op", 50.0, "error", error_info)
        assert base_tool._operation_count == 1
        assert base_tool._error_count == 1
    
    def test_handle_error(self, base_tool):
        """测试错误处理"""
        error = Exception("test error")
        error_info = base_tool._handle_error(error, "test_op")
        
        assert error_info["error_type"] == "Exception"
        assert error_info["message"] == "test error"
        assert error_info["operation"] == "test_op"
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self, base_tool):
        """测试重试机制 - 成功"""
        mock_op = AsyncMock(return_value="success")
        result = await base_tool._retry_with_backoff(mock_op, max_retries=3)
        
        assert result == "success"
        assert mock_op.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure(self, base_tool):
        """测试重试机制 - 失败"""
        mock_op = AsyncMock(side_effect=Exception("always fails"))
        
        with pytest.raises(Exception, match="always fails"):
            await base_tool._retry_with_backoff(mock_op, max_retries=2, base_delay=0.01)
        
        assert mock_op.call_count == 3  # 初始 + 2次重试
    
    def test_get_stats(self, base_tool):
        """测试获取统计信息"""
        stats = base_tool.get_stats()
        
        assert stats["tool"] == "test_tool"
        assert stats["connected"] == False
        assert stats["operation_count"] == 0
        assert stats["error_count"] == 0
        assert stats["error_rate"] == 0.0


# ================================
# PostgreSQL Tool Tests
# ================================

class TestPostgreSQLTool:
    """测试 PostgreSQL Tool"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        from src.tools.types import PostgreSQLConfig
        return PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
    
    @pytest.fixture
    def mock_pool(self):
        """创建模拟连接池"""
        pool = AsyncMock()
        pool.acquire = AsyncMock()
        pool.close = AsyncMock()
        return pool
    
    @pytest.fixture
    def mock_connection(self):
        """创建模拟连接"""
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[
            {"id": "user_1", "name": "Test User"}
        ])
        conn.fetchval = AsyncMock(return_value=1)
        conn.execute = AsyncMock(return_value="INSERT 0 1")
        return conn
    
    @pytest.mark.asyncio
    async def test_init_without_config(self):
        """测试无配置初始化"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.errors import ConnectionError
        
        with pytest.raises(ConnectionError):
            tool = PostgreSQLTool()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_config, mock_pool, mock_connection):
        """测试连接成功"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            assert tool.is_connected
            assert tool._pool == mock_pool
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_config):
        """测试连接失败"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.errors import ConnectionError
        
        with patch("asyncpg.create_pool", side_effect=Exception("Connection refused")):
            tool = PostgreSQLTool(mock_config)
            
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await tool.connect()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_config, mock_pool, mock_connection):
        """测试健康检查成功"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            assert await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_config, mock_pool, mock_connection):
        """测试健康检查失败"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            mock_connection.fetchval = AsyncMock(side_effect=Exception("DB error"))
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            assert not await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_close(self, mock_config, mock_pool, mock_connection):
        """测试关闭连接"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            await tool.close()
            
            assert not tool.is_connected
    
    @pytest.mark.asyncio
    async def test_query(self, mock_config, mock_pool, mock_connection):
        """测试查询操作"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            result = await tool.query("SELECT * FROM users WHERE id = $1", {"id": "user_1"})
            
            assert len(result) == 1
            assert result[0]["id"] == "user_1"
    
    @pytest.mark.asyncio
    async def test_execute(self, mock_config, mock_pool, mock_connection):
        """测试执行操作"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            rows = await tool.execute(
                "UPDATE users SET name = $1 WHERE id = $2",
                {"name": "New Name", "id": "user_1"}
            )
            
            assert rows == 1
    
    @pytest.mark.asyncio
    async def test_transaction(self, mock_config, mock_pool, mock_connection):
        """测试事务操作"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            # 模拟事务
            mock_transaction = AsyncMock()
            mock_connection.transaction.return_value = mock_transaction
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            async with tool.transaction() as txn:
                await txn.execute("INSERT INTO test VALUES (1)")
    
    @pytest.mark.asyncio
    async def test_create_user(self, mock_config, mock_pool, mock_connection):
        """测试创建用户"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import User
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            user = User(id="user_1", name="Test User", department="IT")
            result = await tool.create_user(user)
            
            assert result.id == "user_1"
            assert result.name == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_user(self, mock_config, mock_pool, mock_connection):
        """测试获取用户"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            result = await tool.get_user("user_1")
            
            assert result is not None
            assert result.id == "user_1"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_config, mock_pool, mock_connection):
        """测试获取不存在的用户"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            mock_connection.fetch = AsyncMock(return_value=[])
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            result = await tool.get_user("non_existent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user(self, mock_config, mock_pool, mock_connection):
        """测试更新用户"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import User
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            mock_connection.execute = AsyncMock(return_value="UPDATE 1")
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            user = User(id="user_1", name="Updated Name")
            result = await tool.update_user(user)
            
            assert result.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, mock_config, mock_pool, mock_connection):
        """测试删除用户"""
        from src.tools.postgresql_tool import PostgreSQLTool
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            mock_connection.execute = AsyncMock(return_value="DELETE 1")
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            result = await tool.delete_user("user_1")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_create_task(self, mock_config, mock_pool, mock_connection):
        """测试创建任务"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import Task
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            task = Task(id="task_1", user_id="user_1", type="analysis")
            result = await tool.create_task(task)
            
            assert result.id == "task_1"
            assert result.type == "analysis"
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, mock_config, mock_pool, mock_connection):
        """测试列出任务"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import Task
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            mock_connection.fetch = AsyncMock(return_value=[
                {"id": "task_1", "user_id": "user_1", "type": "analysis", "status": "pending"},
                {"id": "task_2", "user_id": "user_1", "type": "generation", "status": "completed"}
            ])
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            results = await tool.list_tasks(user_id="user_1")
            
            assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_save_analysis(self, mock_config, mock_pool, mock_connection):
        """测试保存分析结果"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import AnalysisResult
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            result = AnalysisResult(
                id="analysis_1",
                task_id="task_1",
                type="vision",
                result_data={"objects": ["car", "person"]},
                confidence=0.95
            )
            saved = await tool.save_analysis(result)
            
            assert saved.id == "analysis_1"
    
    @pytest.mark.asyncio
    async def test_save_document(self, mock_config, mock_pool, mock_connection):
        """测试保存文档"""
        from src.tools.postgresql_tool import PostgreSQLTool
        from src.tools.types import Document
        
        with patch("asyncpg.create_pool", return_value=mock_pool):
            mock_pool.acquire.return_value = mock_connection
            
            tool = PostgreSQLTool(mock_config)
            await tool.connect()
            
            doc = Document(
                id="doc_1",
                user_id="user_1",
                title="Test Document",
                content="This is a test document"
            )
            result = await tool.save_document(doc)
            
            assert result.id == "doc_1"
            assert result.title == "Test Document"


# ================================
# MinIO Tool Tests
# ================================

class TestMinIOTool:
    """测试 MinIO Tool"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        from src.tools.types import MinIOConfig
        return MinIOConfig(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin123",
            bucket="test-bucket"
        )
    
    @pytest.fixture
    def mock_minio_client(self):
        """创建模拟 MinIO 客户端"""
        client = Mock()
        client.list_buckets = Mock()
        client.bucket_exists = Mock(return_value=True)
        client.fput_object = Mock(return_value=Mock(etag="abc123"))
        client.fget_object = Mock()
        client.get_object = Mock(return_value=Mock(
            read=Mock(return_value=b"test content"),
            close=Mock(),
            release_conn=Mock()
        ))
        client.put_object = Mock(return_value=Mock(etag="def456"))
        client.remove_object = Mock()
        client.stat_object = Mock(return_value=Mock(
            object_name="test.txt",
            size=100,
            content_type="text/plain",
            last_modified=datetime.now(),
            etag="abc123",
            metadata={}
        ))
        client.presigned_get_object = Mock(return_value="http://presigned-url")
        client.presigned_put_object = Mock(return_value="http://presigned-put-url")
        client.list_objects = Mock(return_value=[])
        client.copy_object = Mock()
        return client
    
    @pytest.mark.asyncio
    async def test_init_without_config(self):
        """测试无配置初始化"""
        from src.tools.minio_tool import MinIOTool
        from src.tools.errors import ConnectionError
        
        with pytest.raises(ConnectionError):
            tool = MinIOTool()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_config, mock_minio_client):
        """测试连接成功"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            assert tool.is_connected
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_config):
        """测试连接失败"""
        from src.tools.minio_tool import MinIOTool
        from src.tools.errors import ConnectionError
        
        with patch("minio.Minio", side_effect=Exception("Connection refused")):
            tool = MinIOTool(mock_config)
            
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await tool.connect()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_config, mock_minio_client):
        """测试健康检查成功"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            assert await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_config, mock_minio_client):
        """测试健康检查失败"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            mock_minio_client.list_buckets = Mock(side_effect=Exception("Error"))
            assert not await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_upload_file(self, mock_config, mock_minio_client, tmp_path):
        """测试文件上传"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            # 创建临时文件
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            
            result = await tool.upload_file(
                str(test_file),
                "documents/test.txt",
                metadata={"key": "value"}
            )
            
            assert result.success
            assert result.object_name == "documents/test.txt"
            assert result.etag == "abc123"
    
    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, mock_config, mock_minio_client):
        """测试上传不存在的文件"""
        from src.tools.minio_tool import MinIOTool
        from src.tools.errors import MinIOError
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            with pytest.raises(MinIOError, match="File not found"):
                await tool.upload_file("/nonexistent/file.txt", "test.txt")
    
    @pytest.mark.asyncio
    async def test_download_file(self, mock_config, mock_minio_client, tmp_path):
        """测试文件下载"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            download_path = str(tmp_path / "downloaded.txt")
            result = await tool.download_file("documents/test.txt", download_path)
            
            assert result == download_path
    
    @pytest.mark.asyncio
    async def test_get_presigned_url(self, mock_config, mock_minio_client):
        """测试生成预签名 URL"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            url = await tool.get_presigned_url("documents/test.txt", expires=3600)
            
            assert url == "http://presigned-url"
    
    @pytest.mark.asyncio
    async def test_delete_file(self, mock_config, mock_minio_client):
        """测试删除文件"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            result = await tool.delete_file("documents/test.txt")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_list_files(self, mock_config, mock_minio_client):
        """测试列出文件"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            mock_minio_client.list_objects = Mock(return_value=[
                Mock(object_name="file1.txt", size=100, last_modified=datetime.now(), etag="etag1"),
                Mock(object_name="file2.txt", size=200, last_modified=datetime.now(), etag="etag2")
            ])
            
            results = await tool.list_files(prefix="documents/")
            
            assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_get_file_metadata(self, mock_config, mock_minio_client):
        """测试获取文件元数据"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            metadata = await tool.get_file_metadata("documents/test.txt")
            
            assert metadata.object_name == "test.txt"
            assert metadata.size == 100
    
    @pytest.mark.asyncio
    async def test_copy_file(self, mock_config, mock_minio_client):
        """测试复制文件"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            result = await tool.copy_file("source.txt", "dest.txt")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_move_file(self, mock_config, mock_minio_client):
        """测试移动文件"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            result = await tool.move_file("source.txt", "dest.txt")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_upload_bytes(self, mock_config, mock_minio_client):
        """测试上传字节数据"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            data = b"test data content"
            result = await tool.upload_bytes(data, "documents/data.bin")
            
            assert result.success
            assert result.size == len(data)
    
    @pytest.mark.asyncio
    async def test_download_bytes(self, mock_config, mock_minio_client):
        """测试下载字节数据"""
        from src.tools.minio_tool import MinIOTool
        
        with patch("minio.Minio", return_value=mock_minio_client):
            tool = MinIOTool(mock_config)
            await tool.connect()
            
            data = await tool.download_bytes("documents/test.txt")
            
            assert data == b"test content"


# ================================
# Redis Tool Tests
# ================================

class TestRedisTool:
    """测试 Redis Tool"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        from src.tools.types import RedisConfig
        return RedisConfig(
            host="localhost",
            port=6379,
            password="redispass",
            db=0
        )
    
    @pytest.fixture
    def mock_redis_client(self):
        """创建模拟 Redis 客户端"""
        client = AsyncMock()
        client.ping = AsyncMock()
        client.get = AsyncMock(return_value="test_value")
        client.set = AsyncMock(return_value=True)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=1)
        client.expire = AsyncMock(return_value=True)
        client.exists = AsyncMock(return_value=1)
        client.ttl = AsyncMock(return_value=3600)
        client.incrby = AsyncMock(return_value=1)
        client.sadd = AsyncMock(return_value=1)
        client.smembers = AsyncMock(return_value={"member1", "member2"})
        client.rpush = AsyncMock(return_value=2)
        client.lrange = AsyncMock(return_value=["item1", "item2"])
        client.eval = AsyncMock(return_value=1)
        client.pipeline = Mock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=AsyncMock(
                zremrangebyscore=AsyncMock(),
                zcard=AsyncMock(),
                zadd=AsyncMock(),
                expire=AsyncMock(),
                execute=AsyncMock(return_value=[0, 5, 1, True])
            )),
            __aexit__=AsyncMock()
        ))
        return client
    
    @pytest.mark.asyncio
    async def test_init_without_config(self):
        """测试无配置初始化"""
        from src.tools.redis_tool import RedisTool
        from src.tools.errors import ConnectionError
        
        with pytest.raises(ConnectionError):
            tool = RedisTool()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_config, mock_redis_client):
        """测试连接成功"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            assert tool.is_connected
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_config):
        """测试连接失败"""
        from src.tools.redis_tool import RedisTool
        from src.tools.errors import ConnectionError
        
        with patch("redis.asyncio.Redis", side_effect=Exception("Connection refused")):
            tool = RedisTool(mock_config)
            
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await tool.connect()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_config, mock_redis_client):
        """测试健康检查成功"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            assert await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_config, mock_redis_client):
        """测试健康检查失败"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            mock_redis_client.ping = AsyncMock(side_effect=Exception("Error"))
            assert not await tool.health_check()
    
    @pytest.mark.asyncio
    async def test_get(self, mock_config, mock_redis_client):
        """测试获取值"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            value = await tool.get("test_key")
            
            assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_set(self, mock_config, mock_redis_client):
        """测试设置值"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.set("test_key", "test_value", expire=3600)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete(self, mock_config, mock_redis_client):
        """测试删除键"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.delete("test_key")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_exists(self, mock_config, mock_redis_client):
        """测试检查键是否存在"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.exists("test_key")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_expire(self, mock_config, mock_redis_client):
        """测试设置过期时间"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.expire("test_key", 3600)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ttl(self, mock_config, mock_redis_client):
        """测试获取剩余时间"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.ttl("test_key")
            
            assert result == 3600
    
    @pytest.mark.asyncio
    async def test_set_session(self, mock_config, mock_redis_client):
        """测试存储 Session"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.set_session("session_1", {"user_id": "user_1"})
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_session(self, mock_config, mock_redis_client):
        """测试获取 Session"""
        from src.tools.redis_tool import RedisTool
        
        mock_redis_client.get = AsyncMock(return_value='{"user_id": "user_1"}')
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.get_session("session_1")
            
            assert result == {"user_id": "user_1"}
    
    @pytest.mark.asyncio
    async def test_delete_session(self, mock_config, mock_redis_client):
        """测试删除 Session"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.delete_session("session_1")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, mock_config, mock_redis_client):
        """测试获取锁成功"""
        from src.tools.redis_tool import RedisTool
        
        mock_redis_client.set = AsyncMock(return_value=True)
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            lock = await tool.acquire_lock("test_lock", timeout=10)
            
            assert lock.acquired is True
            assert lock.lock_name == "test_lock"
    
    @pytest.mark.asyncio
    async def test_acquire_lock_failure(self, mock_config, mock_redis_client):
        """测试获取锁失败"""
        from src.tools.redis_tool import RedisTool
        
        mock_redis_client.set = AsyncMock(return_value=False)
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            lock = await tool.acquire_lock("test_lock", timeout=10)
            
            assert lock.acquired is False
    
    @pytest.mark.asyncio
    async def test_release_lock(self, mock_config, mock_redis_client):
        """测试释放锁"""
        from src.tools.redis_tool import RedisTool
        
        mock_redis_client.eval = AsyncMock(return_value=1)
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.release_lock("test_lock", "identifier_123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self, mock_config, mock_redis_client):
        """测试限流检查"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.rate_limit_check("api_key_1", limit=100, window=60)
            
            assert result.key == "api_key_1"
            assert result.limit == 100
            assert result.window == 60
    
    @pytest.mark.asyncio
    async def test_increment(self, mock_config, mock_redis_client):
        """测试原子递增"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.increment("counter", amount=5)
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_set_add(self, mock_config, mock_redis_client):
        """测试向集合添加成员"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.set_add("my_set", "member1", "member2")
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_set_members(self, mock_config, mock_redis_client):
        """测试获取集合成员"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.set_members("my_set")
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_list_push(self, mock_config, mock_redis_client):
        """测试向列表添加元素"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.list_push("my_list", "item1", "item2")
            
            assert result == 2
    
    @pytest.mark.asyncio
    async def test_list_range(self, mock_config, mock_redis_client):
        """测试获取列表范围"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis", return_value=mock_redis_client):
            tool = RedisTool(mock_config)
            await tool.connect()
            
            result = await tool.list_range("my_list", 0, -1)
            
            assert len(result) == 2
    
    def test_serialize_value(self, mock_config):
        """测试值序列化"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis"):
            tool = RedisTool(mock_config)
            
            # 字符串
            assert tool._serialize_value("test") == "test"
            
            # 字典
            assert tool._serialize_value({"key": "value"}) == '{"key": "value"}'
            
            # 列表
            assert tool._serialize_value([1, 2, 3]) == "[1, 2, 3]"
    
    def test_deserialize_value(self, mock_config):
        """测试值反序列化"""
        from src.tools.redis_tool import RedisTool
        
        with patch("redis.asyncio.Redis"):
            tool = RedisTool(mock_config)
            
            # None
            assert tool._deserialize_value(None) is None
            
            # JSON 字符串
            assert tool._deserialize_value('{"key": "value"}') == {"key": "value"}
            
            # 普通字符串
            assert tool._deserialize_value("test") == "test"


# ================================
# Error Tests
# ================================

class TestErrors:
    """测试错误类"""
    
    def test_tool_error(self):
        """测试 ToolError"""
        from src.tools.errors import ToolError
        
        error = ToolError(
            error_type="TestError",
            message="Test message",
            suggestion="Try again",
            details={"key": "value"}
        )
        
        assert error.error_type == "TestError"
        assert error.message == "Test message"
        assert error.suggestion == "Try again"
        assert error.details == {"key": "value"}
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "TestError"
    
    def test_postgresql_error(self):
        """测试 PostgreSQLError"""
        from src.tools.errors import PostgreSQLError
        
        error = PostgreSQLError("Connection failed")
        
        assert error.error_type == "PostgreSQLError"
        assert "Connection failed" in error.message
    
    def test_minio_error(self):
        """测试 MinIOError"""
        from src.tools.errors import MinIOError
        
        error = MinIOError("Upload failed")
        
        assert error.error_type == "MinIOError"
        assert "Upload failed" in error.message
    
    def test_redis_error(self):
        """测试 RedisError"""
        from src.tools.errors import RedisError
        
        error = RedisError("Get failed")
        
        assert error.error_type == "RedisError"
        assert "Get failed" in error.message
    
    def test_connection_error(self):
        """测试 ConnectionError"""
        from src.tools.errors import ConnectionError
        
        error = ConnectionError("Cannot connect")
        
        assert error.error_type == "ConnectionError"
        assert "Cannot connect" in error.message
    
    def test_validation_error(self):
        """测试 ValidationError"""
        from src.tools.errors import ValidationError
        
        error = ValidationError("Invalid input", field="user_id")
        
        assert error.error_type == "ValidationError"
        assert error.details["field"] == "user_id"
    
    def test_not_found_error(self):
        """测试 NotFoundError"""
        from src.tools.errors import NotFoundError
        
        error = NotFoundError("User not found", resource_type="user")
        
        assert error.error_type == "NotFoundError"
        assert error.details["resource_type"] == "user"
    
    def test_timeout_error(self):
        """测试 TimeoutError"""
        from src.tools.errors import TimeoutError
        
        error = TimeoutError("Operation timed out")
        
        assert error.error_type == "TimeoutError"
        assert "Operation timed out" in error.message


# ================================
# Type Tests
# ================================

class TestTypes:
    """测试数据模型"""
    
    def test_user_model(self):
        """测试 User 模型"""
        from src.tools.types import User
        
        user = User(id="user_1", name="Test User", department="IT")
        
        assert user.id == "user_1"
        assert user.name == "Test User"
        assert user.department == "IT"
        assert user.role == "user"
    
    def test_user_validation(self):
        """测试 User 验证"""
        from src.tools.types import User
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            User(id="", name="Test")
    
    def test_session_model(self):
        """测试 Session 模型"""
        from src.tools.types import Session
        from datetime import datetime, timedelta
        
        expires = datetime.now() + timedelta(hours=1)
        session = Session(
            id="session_1",
            user_id="user_1",
            data={"key": "value"},
            expires_at=expires
        )
        
        assert session.id == "session_1"
        assert session.user_id == "user_1"
        assert session.data == {"key": "value"}
    
    def test_task_model(self):
        """测试 Task 模型"""
        from src.tools.types import Task, TaskStatus
        
        task = Task(
            id="task_1",
            user_id="user_1",
            type="analysis",
            status=TaskStatus.PENDING
        )
        
        assert task.id == "task_1"
        assert task.type == "analysis"
        assert task.status == TaskStatus.PENDING
    
    def test_analysis_result_model(self):
        """测试 AnalysisResult 模型"""
        from src.tools.types import AnalysisResult
        
        result = AnalysisResult(
            id="analysis_1",
            task_id="task_1",
            type="vision",
            result_data={"objects": ["car"]},
            confidence=0.95
        )
        
        assert result.id == "analysis_1"
        assert result.confidence == 0.95
    
    def test_document_model(self):
        """测试 Document 模型"""
        from src.tools.types import Document
        
        doc = Document(
            id="doc_1",
            user_id="user_1",
            title="Test Doc",
            content="Content"
        )
        
        assert doc.id == "doc_1"
        assert doc.title == "Test Doc"
    
    def test_file_metadata_model(self):
        """测试 FileMetadata 模型"""
        from src.tools.types import FileMetadata
        
        meta = FileMetadata(
            object_name="test.txt",
            bucket="test-bucket",
            size=100,
            content_type="text/plain"
        )
        
        assert meta.object_name == "test.txt"
        assert meta.size == 100
    
    def test_upload_result_model(self):
        """测试 UploadResult 模型"""
        from src.tools.types import UploadResult
        
        result = UploadResult(
            object_name="test.txt",
            bucket="test-bucket",
            size=100
        )
        
        assert result.success is True
        assert result.size == 100
    
    def test_lock_info_model(self):
        """测试 LockInfo 模型"""
        from src.tools.types import LockInfo
        
        lock = LockInfo(
            lock_name="test_lock",
            identifier="uuid-123",
            acquired=True,
            ttl=10
        )
        
        assert lock.acquired is True
        assert lock.ttl == 10
    
    def test_rate_limit_info_model(self):
        """测试 RateLimitInfo 模型"""
        from src.tools.types import RateLimitInfo
        from datetime import datetime
        
        info = RateLimitInfo(
            key="api_key",
            allowed=True,
            remaining=50,
            reset_time=datetime.now(),
            limit=100,
            window=60
        )
        
        assert info.allowed is True
        assert info.remaining == 50
    
    def test_postgresql_config(self):
        """测试 PostgreSQLConfig 模型"""
        from src.tools.types import PostgreSQLConfig
        
        config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="test",
            user="test",
            password="test"
        )
        
        assert config.host == "localhost"
        assert config.pool_size == 10
    
    def test_minio_config(self):
        """测试 MinIOConfig 模型"""
        from src.tools.types import MinIOConfig
        
        config = MinIOConfig(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="secret",
            bucket="test-bucket"
        )
        
        assert config.endpoint == "localhost:9000"
        assert config.secure is False
    
    def test_redis_config(self):
        """测试 RedisConfig 模型"""
        from src.tools.types import RedisConfig
        
        config = RedisConfig(
            host="localhost",
            port=6379,
            password="secret"
        )
        
        assert config.host == "localhost"
        assert config.db == 0


# ================================
# Integration Tests
# ================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_tool_lifecycle(self):
        """测试 Tool 生命周期"""
        from src.tools.base import BaseTool
        
        class TestTool(BaseTool):
            async def connect(self):
                self._connected = True
            
            async def health_check(self):
                return self._connected
            
            async def close(self):
                self._connected = False
        
        tool = TestTool("integration_test")
        
        # 连接
        await tool.connect()
        assert tool.is_connected
        assert await tool.health_check()
        
        # 操作
        tool._log_operation("test", 10.0)
        assert tool._operation_count == 1
        
        # 关闭
        await tool.close()
        assert not tool.is_connected
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        from src.tools.base import BaseTool
        
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__("concurrent_test")
                self.counter = 0
            
            async def connect(self):
                self._connected = True
            
            async def health_check(self):
                return True
            
            async def close(self):
                self._connected = False
            
            async def increment(self):
                self.counter += 1
                return self.counter
        
        tool = TestTool()
        await tool.connect()
        
        # 并发执行
        tasks = [tool.increment() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert tool.counter == 10
        
        await tool.close()
