"""
Field Info Agent - MinIO Tool

封装 MinIO 对象存储操作，提供：
- 文件上传/下载
- 预签名 URL 生成
- 文件元数据管理
- 分片上传支持

Usage:
    from src.tools.minio_tool import MinIOTool
    from src.tools.types import MinIOConfig
    
    config = MinIOConfig(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        bucket="field-documents"
    )
    
    async with MinIOTool(config) as minio:
        # 上传文件
        url = await minio.upload_file(
            file_path="/tmp/photo.jpg",
            object_name="raw-photos/user_123/photo.jpg",
            metadata={"user_id": "user_123"}
        )
        
        # 下载文件
        await minio.download_file(
            object_name="raw-photos/user_123/photo.jpg",
            file_path="/tmp/downloaded.jpg"
        )
        
        # 生成预签名 URL
        presigned_url = await minio.get_presigned_url(
            object_name="raw-photos/user_123/photo.jpg",
            expires=3600
        )
"""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    Minio = Any
    S3Error = Exception
    MINIO_AVAILABLE = False

from src.tools.base import BaseTool
from src.tools.types import MinIOConfig, FileMetadata, UploadResult
from src.tools.errors import MinIOError, ConnectionError, NotFoundError


class MinIOTool(BaseTool):
    """MinIO Tool
    
    封装 MinIO 对象存储操作
    
    Example:
        config = MinIOConfig(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin123",
            bucket="field-documents"
        )
        
        minio = MinIOTool(config)
        await minio.connect()
        
        # 上传
        result = await minio.upload_file("/tmp/file.txt", "documents/file.txt")
        
        # 下载
        await minio.download_file("documents/file.txt", "/tmp/downloaded.txt")
        
        await minio.close()
    """
    
    # Bucket 结构定义
    BUCKETS = {
        "raw-photos": "原始照片",
        "analysis-outputs": "分析结果",
        "generated-docs": "生成文档",
        "temp": "临时文件",
        "backups": "备份文件"
    }
    
    def __init__(self, config: Optional[MinIOConfig] = None):
        """初始化 MinIO Tool
        
        Args:
            config: MinIO 配置
        """
        super().__init__("minio", config)
        self._config = config
        self._client: Optional[Minio] = None
        
        if not MINIO_AVAILABLE:
            raise ImportError(
                "minio is required for MinIOTool. "
                "Install with: pip install minio"
            )
    
    async def connect(self) -> None:
        """建立 MinIO 连接
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        if self._connected:
            return
        
        try:
            start_time = time.time()
            
            self._client = Minio(
                endpoint=self._config.endpoint,
                access_key=self._config.access_key,
                secret_key=self._config.secret_key,
                secure=self._config.secure,
                region=self._config.region
            )
            
            # 检查连接
            self._client.list_buckets()
            
            # 确保默认 bucket 存在
            self._ensure_bucket_exists(self._config.bucket)
            
            self._connected = True
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("connect", duration_ms, metadata={
                "endpoint": self._config.endpoint,
                "bucket": self._config.bucket
            })
            
        except Exception as e:
            raise ConnectionError(
                message=f"Failed to connect to MinIO: {str(e)}",
                details={
                    "endpoint": self._config.endpoint,
                    "bucket": self._config.bucket
                }
            )
    
    async def health_check(self) -> bool:
        """健康检查"""
        if not self._connected or not self._client:
            return False
        
        try:
            start_time = time.time()
            self._client.list_buckets()
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("health_check", duration_ms)
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """关闭连接"""
        self._client = None
        self._connected = False
        self._log_operation("close", 0)
    
    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """确保 bucket 存在"""
        try:
            if not self._client.bucket_exists(bucket_name):
                self._client.make_bucket(bucket_name)
                self._logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            raise MinIOError(
                message=f"Failed to create bucket {bucket_name}: {str(e)}",
                details={"bucket": bucket_name}
            )
    
    async def upload_file(
        self,
        file_path: str,
        object_name: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: Optional[str] = None
    ) -> UploadResult:
        """上传文件
        
        Args:
            file_path: 本地文件路径
            object_name: 对象名称（存储路径）
            bucket: 存储桶名称，默认使用配置中的 bucket
            metadata: 自定义元数据
            content_type: 内容类型
        
        Returns:
            上传结果
        
        Raises:
            MinIOError: 上传失败时抛出
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 推断内容类型
            if content_type is None:
                content_type = self._infer_content_type(file_path)
            
            # 准备元数据
            meta = metadata or {}
            meta["upload_time"] = datetime.now().isoformat()
            meta["original_filename"] = os.path.basename(file_path)
            
            # 执行上传
            result = self._client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=meta
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("upload_file", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name,
                "size": file_size
            })
            
            return UploadResult(
                success=True,
                object_name=object_name,
                etag=result.etag,
                bucket=bucket,
                size=file_size,
                metadata=meta
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "upload_file", {
                "file_path": file_path,
                "object_name": object_name
            })
            self._log_operation("upload_file", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to upload file: {str(e)}",
                details={"file_path": file_path, "object_name": object_name}
            )
    
    async def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: Optional[str] = None
    ) -> UploadResult:
        """上传字节数据
        
        Args:
            data: 字节数据
            object_name: 对象名称
            bucket: 存储桶名称
            metadata: 自定义元数据
            content_type: 内容类型
        
        Returns:
            上传结果
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            from io import BytesIO
            
            # 准备元数据
            meta = metadata or {}
            meta["upload_time"] = datetime.now().isoformat()
            
            # 推断内容类型
            if content_type is None:
                content_type = "application/octet-stream"
            
            # 执行上传
            result = self._client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=meta
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("upload_bytes", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name,
                "size": len(data)
            })
            
            return UploadResult(
                success=True,
                object_name=object_name,
                etag=result.etag,
                bucket=bucket,
                size=len(data),
                metadata=meta
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "upload_bytes", {
                "object_name": object_name,
                "size": len(data)
            })
            self._log_operation("upload_bytes", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to upload bytes: {str(e)}",
                details={"object_name": object_name}
            )
    
    async def download_file(
        self,
        object_name: str,
        file_path: str,
        bucket: Optional[str] = None
    ) -> str:
        """下载文件
        
        Args:
            object_name: 对象名称
            file_path: 本地保存路径
            bucket: 存储桶名称
        
        Returns:
            下载的文件路径
        
        Raises:
            MinIOError: 下载失败时抛出
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 执行下载
            self._client.fget_object(bucket, object_name, file_path)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("download_file", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name,
                "file_path": file_path
            })
            
            return file_path
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise NotFoundError(
                    message=f"Object not found: {object_name}",
                    resource_type="object",
                    details={"bucket": bucket, "object_name": object_name}
                )
            
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "download_file", {
                "object_name": object_name,
                "bucket": bucket
            })
            self._log_operation("download_file", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to download file: {str(e)}",
                details={"object_name": object_name, "bucket": bucket}
            )
    
    async def download_bytes(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> bytes:
        """下载文件为字节数据
        
        Args:
            object_name: 对象名称
            bucket: 存储桶名称
        
        Returns:
            文件字节数据
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            response = self._client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("download_bytes", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name,
                "size": len(data)
            })
            
            return data
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise NotFoundError(
                    message=f"Object not found: {object_name}",
                    resource_type="object"
                )
            raise MinIOError(
                message=f"Failed to download bytes: {str(e)}",
                details={"object_name": object_name}
            )
    
    async def get_presigned_url(
        self,
        object_name: str,
        bucket: Optional[str] = None,
        expires: int = 3600,
        method: str = "GET"
    ) -> str:
        """生成预签名 URL
        
        Args:
            object_name: 对象名称
            bucket: 存储桶名称
            expires: 过期时间（秒）
            method: HTTP 方法（GET 或 PUT）
        
        Returns:
            预签名 URL
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            if method.upper() == "GET":
                url = self._client.presigned_get_object(bucket, object_name, expires)
            elif method.upper() == "PUT":
                url = self._client.presigned_put_object(bucket, object_name, expires)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("get_presigned_url", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name,
                "expires": expires,
                "method": method
            })
            
            return url
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "get_presigned_url", {
                "object_name": object_name,
                "method": method
            })
            self._log_operation("get_presigned_url", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to generate presigned URL: {str(e)}",
                details={"object_name": object_name}
            )
    
    async def delete_file(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> bool:
        """删除文件
        
        Args:
            object_name: 对象名称
            bucket: 存储桶名称
        
        Returns:
            是否删除成功
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            self._client.remove_object(bucket, object_name)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("delete_file", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name
            })
            
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "delete_file", {
                "object_name": object_name
            })
            self._log_operation("delete_file", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to delete file: {str(e)}",
                details={"object_name": object_name}
            )
    
    async def list_files(
        self,
        prefix: Optional[str] = None,
        bucket: Optional[str] = None,
        recursive: bool = True
    ) -> List[FileMetadata]:
        """列出文件
        
        Args:
            prefix: 前缀过滤
            bucket: 存储桶名称
            recursive: 是否递归列出
        
        Returns:
            文件元数据列表
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            objects = self._client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=recursive
            )
            
            results = []
            for obj in objects:
                # 跳过目录
                if obj.object_name.endswith("/"):
                    continue
                
                results.append(FileMetadata(
                    object_name=obj.object_name,
                    bucket=bucket,
                    size=obj.size,
                    last_modified=obj.last_modified,
                    etag=obj.etag
                ))
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("list_files", duration_ms, metadata={
                "bucket": bucket,
                "prefix": prefix,
                "count": len(results)
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "list_files", {
                "prefix": prefix,
                "bucket": bucket
            })
            self._log_operation("list_files", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to list files: {str(e)}",
                details={"prefix": prefix}
            )
    
    async def get_file_metadata(
        self,
        object_name: str,
        bucket: Optional[str] = None
    ) -> FileMetadata:
        """获取文件元数据
        
        Args:
            object_name: 对象名称
            bucket: 存储桶名称
        
        Returns:
            文件元数据
        """
        start_time = time.time()
        bucket = bucket or self._config.bucket
        
        try:
            stat = self._client.stat_object(bucket, object_name)
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("get_file_metadata", duration_ms, metadata={
                "bucket": bucket,
                "object_name": object_name
            })
            
            return FileMetadata(
                object_name=stat.object_name,
                bucket=bucket,
                size=stat.size,
                content_type=stat.content_type,
                last_modified=stat.last_modified,
                etag=stat.etag,
                metadata=stat.metadata or {}
            )
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise NotFoundError(
                    message=f"Object not found: {object_name}",
                    resource_type="object"
                )
            
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "get_file_metadata", {
                "object_name": object_name
            })
            self._log_operation("get_file_metadata", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to get file metadata: {str(e)}",
                details={"object_name": object_name}
            )
    
    async def copy_file(
        self,
        source_object: str,
        dest_object: str,
        source_bucket: Optional[str] = None,
        dest_bucket: Optional[str] = None
    ) -> bool:
        """复制文件
        
        Args:
            source_object: 源对象名称
            dest_object: 目标对象名称
            source_bucket: 源存储桶
            dest_bucket: 目标存储桶
        
        Returns:
            是否复制成功
        """
        start_time = time.time()
        source_bucket = source_bucket or self._config.bucket
        dest_bucket = dest_bucket or self._config.bucket
        
        try:
            # 复制对象
            copy_source = f"{source_bucket}/{source_object}"
            result = self._client.copy_object(
                dest_bucket,
                dest_object,
                copy_source
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation("copy_file", duration_ms, metadata={
                "source": f"{source_bucket}/{source_object}",
                "dest": f"{dest_bucket}/{dest_object}"
            })
            
            return True
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_info = self._handle_error(e, "copy_file", {
                "source": source_object,
                "dest": dest_object
            })
            self._log_operation("copy_file", duration_ms, "error", error_info)
            raise MinIOError(
                message=f"Failed to copy file: {str(e)}",
                details={"source": source_object, "dest": dest_object}
            )
    
    async def move_file(
        self,
        source_object: str,
        dest_object: str,
        bucket: Optional[str] = None
    ) -> bool:
        """移动文件
        
        Args:
            source_object: 源对象名称
            dest_object: 目标对象名称
            bucket: 存储桶名称
        
        Returns:
            是否移动成功
        """
        bucket = bucket or self._config.bucket
        
        # 复制文件
        await self.copy_file(source_object, dest_object, bucket, bucket)
        
        # 删除源文件
        await self.delete_file(source_object, bucket)
        
        return True
    
    def _infer_content_type(self, file_path: str) -> str:
        """推断文件内容类型
        
        Args:
            file_path: 文件路径
        
        Returns:
            内容类型 MIME
        """
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"


__all__ = [
    "MinIOTool"
]
