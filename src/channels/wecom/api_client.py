"""
企业微信API客户端
封装企业微信所有API调用
"""

import os
import json
import time
import aiohttp
from typing import Optional, Dict, Any, List, BinaryIO
from dataclasses import dataclass
import logging

from .errors import WeComAPIException, WeComError, WeComErrorCode, with_retry, RetryConfig, CircuitBreaker, with_circuit_breaker

logger = logging.getLogger(__name__)


@dataclass
class AccessToken:
    """访问令牌"""
    token: str
    expires_at: int
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期（提前5分钟认为过期）"""
        return time.time() > (self.expires_at - 300)


@dataclass
class WeComUserInfo:
    """用户信息"""
    user_id: str
    name: str
    department: List[int]
    position: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[int] = None


class WeComAPIClient:
    """
    企业微信API客户端
    
    支持的功能：
    - AccessToken管理（自动刷新）
    - 消息发送（文本、Markdown、卡片、图片）
    - 媒体文件下载
    - 用户信息查询
    """
    
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(
        self,
        corp_id: str,
        secret: str,
        agent_id: Optional[int] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Args:
            corp_id: 企业微信CorpID
            secret: 应用Secret
            agent_id: 应用AgentID
            retry_config: 重试配置
        """
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self.retry_config = retry_config or RetryConfig()
        
        self._access_token: Optional[AccessToken] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # 创建熔断器
        self._circuit_breaker = CircuitBreaker()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Content-Type': 'application/json; charset=utf-8'
                }
            )
        return self._session
    
    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def get_access_token(self) -> str:
        """
        获取AccessToken（自动刷新）
        
        Returns:
            AccessToken字符串
        """
        # 检查现有token是否有效
        if self._access_token and not self._access_token.is_expired:
            return self._access_token.token
        
        # 获取新token
        url = f"{self.BASE_URL}/gettoken"
        params = {
            'corpid': self.corp_id,
            'corpsecret': self.secret
        }
        
        session = await self._get_session()
        async with session.get(url, params=params) as response:
            data = await response.json()
            
            if data.get('errcode') != 0:
                error = WeComError(
                    code=data.get('errcode', -1),
                    message=data.get('errmsg', '获取AccessToken失败')
                )
                raise WeComAPIException(error)
            
            token = data['access_token']
            expires_in = data.get('expires_in', 7200)
            
            self._access_token = AccessToken(
                token=token,
                expires_at=int(time.time()) + expires_in
            )
            
            logger.info(f"获取新的AccessToken，有效期{expires_in}秒")
            return token
    
    @with_circuit_breaker(CircuitBreaker())
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            
        Returns:
            响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        
        # 自动添加access_token
        if 'access_token' not in params:
            params['access_token'] = await self.get_access_token()
        
        session = await self._get_session()
        
        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                **kwargs
            ) as response:
                result = await response.json()
                
                # 检查错误码
                errcode = result.get('errcode', 0)
                if errcode != 0:
                    error = WeComError(
                        code=errcode,
                        message=result.get('errmsg', '未知错误'),
                        details=result
                    )
                    raise WeComAPIException(error)
                
                return result
                
        except aiohttp.ClientError as e:
            error = WeComError(
                code=WeComErrorCode.NETWORK_ERROR.value,
                message=f"网络错误: {str(e)}"
            )
            raise WeComAPIException(error, e)
        except asyncio.TimeoutError as e:
            error = WeComError(
                code=WeComErrorCode.TIMEOUT_ERROR.value,
                message="请求超时"
            )
            raise WeComAPIException(error, e)
    
    # ========== 消息发送API ==========
    
    async def send_text_message(
        self,
        user_id: str,
        content: str,
        enable_duplicate_check: bool = True,
        duplicate_check_interval: int = 1800
    ) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            user_id: 接收用户ID
            content: 消息内容（最长2048字节）
            enable_duplicate_check: 是否开启重复消息检查
            duplicate_check_interval: 重复消息检查间隔（秒）
            
        Returns:
            发送结果
        """
        if len(content.encode('utf-8')) > 2048:
            raise ValueError("消息内容过长，最大2048字节")
        
        data = {
            'touser': user_id,
            'msgtype': 'text',
            'agentid': self.agent_id,
            'text': {'content': content},
            'enable_duplicate_check': 1 if enable_duplicate_check else 0,
            'duplicate_check_interval': duplicate_check_interval
        }
        
        return await self._request('POST', '/message/send', data=data)
    
    async def send_markdown_message(
        self,
        user_id: str,
        markdown: str
    ) -> Dict[str, Any]:
        """
        发送Markdown消息
        
        Args:
            user_id: 接收用户ID
            markdown: Markdown格式的消息内容
            
        Returns:
            发送结果
        """
        data = {
            'touser': user_id,
            'msgtype': 'markdown',
            'agentid': self.agent_id,
            'markdown': {'content': markdown}
        }
        
        return await self._request('POST', '/message/send', data=data)
    
    async def send_text_card_message(
        self,
        user_id: str,
        title: str,
        description: str,
        url: str,
        buttons: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        发送图文卡片消息
        
        Args:
            user_id: 接收用户ID
            title: 卡片标题（最长128字节）
            description: 卡片描述（最长512字节）
            url: 点击跳转链接
            buttons: 按钮列表 [{'title': '标题', 'url': '链接'}]
            
        Returns:
            发送结果
        """
        textcard = {
            'title': title,
            'description': description,
            'url': url
        }
        
        # 添加按钮
        if buttons and len(buttons) > 0:
            textcard['btntxt'] = buttons[0].get('title', '查看详情')
        
        data = {
            'touser': user_id,
            'msgtype': 'textcard',
            'agentid': self.agent_id,
            'textcard': textcard
        }
        
        return await self._request('POST', '/message/send', data=data)
    
    async def send_template_card_message(
        self,
        user_id: str,
        card_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送模板卡片消息
        
        Args:
            user_id: 接收用户ID
            card_data: 模板卡片数据
            
        Returns:
            发送结果
        """
        data = {
            'touser': user_id,
            'msgtype': 'template_card',
            'agentid': self.agent_id,
            'template_card': card_data
        }
        
        return await self._request('POST', '/message/send', data=data)
    
    async def send_image_message(
        self,
        user_id: str,
        media_id: str
    ) -> Dict[str, Any]:
        """
        发送图片消息
        
        Args:
            user_id: 接收用户ID
            media_id: 媒体文件ID
            
        Returns:
            发送结果
        """
        data = {
            'touser': user_id,
            'msgtype': 'image',
            'agentid': self.agent_id,
            'image': {'media_id': media_id}
        }
        
        return await self._request('POST', '/message/send', data=data)
    
    # ========== 媒体文件API ==========
    
    async def download_media(
        self,
        media_id: str,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        下载媒体文件
        
        Args:
            media_id: 媒体文件ID
            save_path: 保存路径（可选）
            
        Returns:
            包含文件信息的字典
        """
        url = f"{self.BASE_URL}/media/get"
        params = {
            'access_token': await self.get_access_token(),
            'media_id': media_id
        }
        
        session = await self._get_session()
        
        async with session.get(url, params=params) as response:
            content_type = response.headers.get('Content-Type', '')
            
            # 如果是JSON，说明有错误
            if 'application/json' in content_type:
                data = await response.json()
                error = WeComError(
                    code=data.get('errcode', -1),
                    message=data.get('errmsg', '下载媒体文件失败')
                )
                raise WeComAPIException(error)
            
            # 获取文件名
            content_disposition = response.headers.get('Content-Disposition', '')
            filename = None
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            
            # 读取内容
            content = await response.read()
            
            result = {
                'content': content,
                'content_type': content_type,
                'filename': filename,
                'size': len(content)
            }
            
            # 保存到文件
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(content)
                result['save_path'] = save_path
            
            return result
    
    async def upload_media(
        self,
        media_type: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        上传临时素材
        
        Args:
            media_type: 媒体类型（image/voice/video/file）
            file_path: 文件路径
            
        Returns:
            包含media_id的字典
        """
        url = f"{self.BASE_URL}/media/upload"
        params = {
            'access_token': await self.get_access_token(),
            'type': media_type
        }
        
        # 读取文件
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        filename = os.path.basename(file_path)
        
        session = await self._get_session()
        
        data = aiohttp.FormData()
        data.add_field('media', file_data, filename=filename)
        
        async with session.post(url, params=params, data=data) as response:
            result = await response.json()
            
            errcode = result.get('errcode', 0)
            if errcode != 0:
                error = WeComError(
                    code=errcode,
                    message=result.get('errmsg', '上传媒体文件失败')
                )
                raise WeComAPIException(error)
            
            return {
                'media_id': result['media_id'],
                'type': result.get('type'),
                'created_at': result.get('created_at')
            }
    
    # ========== 用户管理API ==========
    
    async def get_user_info(self, user_id: str) -> WeComUserInfo:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
        """
        params = {'userid': user_id}
        result = await self._request('GET', '/user/get', params=params)
        
        return WeComUserInfo(
            user_id=result.get('userid', ''),
            name=result.get('name', ''),
            department=result.get('department', []),
            position=result.get('position'),
            mobile=result.get('mobile'),
            email=result.get('email'),
            avatar=result.get('avatar'),
            status=result.get('status')
        )
    
    async def get_user_id_by_code(self, code: str) -> Optional[str]:
        """
        通过OAuth2 code获取用户ID
        
        Args:
            code: OAuth2授权code
            
        Returns:
            用户ID或None
        """
        params = {'code': code}
        result = await self._request('GET', '/user/getuserinfo', params=params)
        
        return result.get('UserId') or result.get('userId')


# 导入asyncio
import asyncio
