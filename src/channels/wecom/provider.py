"""
企业微信Channel Provider
实现OpenClaw规范的Channel接口
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .crypto.cryptography import WeComCryptography, WeComCryptoError, MessageDeduplicator
from .crypto.xml_parser import WeComXMLParser
from .api_client import WeComAPIClient
from .command_parser import CommandParser
from .handlers.message_handler import WeComMessageProcessor
from .errors import ErrorHandler, WeComAPIException

logger = logging.getLogger(__name__)


@dataclass
class WeComConfig:
    """企业微信配置"""
    # 企业信息
    corp_id: str
    agent_id: int
    secret: str
    
    # 回调配置
    token: str
    encoding_aes_key: str
    callback_url: Optional[str] = None
    
    # 功能开关
    enable_text_message: bool = True
    enable_image_message: bool = True
    enable_voice_message: bool = True
    enable_location_message: bool = True
    enable_file_message: bool = True
    
    # 加密配置
    encryption_enabled: bool = True
    encryption_mode: str = "aes"  # aes/safe
    
    # 存储配置
    storage_path: str = "./temp"
    
    # 高级配置
    dedup_ttl: int = 300  # 消息去重时间窗口（秒）
    max_image_size: int = 2097152  # 2MB
    download_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'WeComConfig':
        """从环境变量加载配置"""
        return cls(
            corp_id=os.environ.get('WECOM_CORP_ID', ''),
            agent_id=int(os.environ.get('WECOM_AGENT_ID', '0')),
            secret=os.environ.get('WECOM_SECRET', ''),
            token=os.environ.get('WECOM_TOKEN', ''),
            encoding_aes_key=os.environ.get('WECOM_ENCODING_AES_KEY', ''),
            callback_url=os.environ.get('WECOM_CALLBACK_URL'),
            storage_path=os.environ.get('WECOM_STORAGE_PATH', './temp')
        )
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        required_fields = [
            self.corp_id,
            self.secret,
            self.token,
            self.encoding_aes_key
        ]
        return all(required_fields) and self.agent_id > 0


class WeComChannelProvider:
    """
    企业微信Channel Provider
    
    实现OpenClaw规范的Channel接口，提供：
    - 消息接收和解析
    - 消息加解密
    - 消息发送
    - 媒体文件下载
    - 命令解析
    - 消息去重
    """
    
    def __init__(self, config: WeComConfig):
        """
        初始化Provider
        
        Args:
            config: 企业微信配置
        """
        self.config = config
        
        # 验证配置
        if not config.validate():
            raise ValueError("企业微信配置不完整，请检查必要参数")
        
        # 初始化加密工具
        self.crypto = WeComCryptography(
            token=config.token,
            encoding_aes_key=config.encoding_aes_key,
            corp_id=config.corp_id
        )
        
        # 初始化API客户端
        self.api_client = WeComAPIClient(
            corp_id=config.corp_id,
            secret=config.secret,
            agent_id=config.agent_id
        )
        
        # 初始化消息处理器
        self.message_processor = WeComMessageProcessor(
            api_client=self.api_client,
            storage_path=config.storage_path
        )
        
        # 初始化去重器
        self.deduplicator = MessageDeduplicator(ttl=config.dedup_ttl)
        
        logger.info(f"企业微信Channel Provider初始化完成，CorpID: {config.corp_id}")
    
    async def verify_url(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echo_str: str
    ) -> str:
        """
        验证回调URL（企业微信服务器配置验证）
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机字符串
            echo_str: 加密的回显字符串
            
        Returns:
            解密后的明文
        """
        return self.crypto.verify_url(msg_signature, timestamp, nonce, echo_str)
    
    async def receive_message(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        encrypted_xml: str
    ) -> Optional[str]:
        """
        接收并处理消息
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机字符串
            encrypted_xml: 加密的XML消息
            
        Returns:
            回复消息的XML字符串（可选）
        """
        try:
            # 验证签名
            if not self.crypto.verify_signature(msg_signature, timestamp, nonce, encrypted_xml):
                logger.error("消息签名验证失败")
                return None
            
            # 解密消息
            decrypt_result = self.crypto.decrypt(encrypted_xml)
            xml_content = decrypt_result.msg
            
            # 解析XML获取消息ID
            parsed = WeComXMLParser.parse(xml_content)
            msg_id = parsed.get('MsgId')
            
            # 消息去重
            if msg_id and self.deduplicator.is_duplicate(msg_id):
                logger.info(f"消息 {msg_id} 重复，忽略")
                return None
            
            logger.debug(f"收到消息: {xml_content[:200]}...")
            
            # 处理消息
            reply = await self.message_processor.process_xml(xml_content)
            
            if reply:
                # 加密回复
                encrypted_reply = self.crypto.encrypt(reply, self.config.corp_id)
                reply_signature = self.crypto.generate_signature(timestamp, nonce, encrypted_reply)
                
                # 构建响应XML
                return WeComXMLParser.build_encrypt_response(
                    encrypt=encrypted_reply,
                    signature=reply_signature,
                    timestamp=timestamp,
                    nonce=nonce
                )
            
            return None
            
        except WeComCryptoError as e:
            logger.error(f"消息解密失败: {e}")
            return None
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            return None
    
    async def send_text_message(self, user_id: str, content: str) -> bool:
        """
        发送文本消息
        
        Args:
            user_id: 用户ID
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        try:
            await self.api_client.send_text_message(user_id, content)
            return True
        except WeComAPIException as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def send_markdown_message(self, user_id: str, markdown: str) -> bool:
        """
        发送Markdown消息
        
        Args:
            user_id: 用户ID
            markdown: Markdown内容
            
        Returns:
            是否发送成功
        """
        try:
            await self.api_client.send_markdown_message(user_id, markdown)
            return True
        except WeComAPIException as e:
            logger.error(f"发送Markdown消息失败: {e}")
            return False
    
    async def send_text_card(
        self,
        user_id: str,
        title: str,
        description: str,
        url: str,
        buttons: Optional[list] = None
    ) -> bool:
        """
        发送图文卡片
        
        Args:
            user_id: 用户ID
            title: 标题
            description: 描述
            url: 跳转链接
            buttons: 按钮列表
            
        Returns:
            是否发送成功
        """
        try:
            await self.api_client.send_text_card_message(user_id, title, description, url, buttons)
            return True
        except WeComAPIException as e:
            logger.error(f"发送卡片消息失败: {e}")
            return False
    
    async def send_image_message(self, user_id: str, media_id: str) -> bool:
        """
        发送图片消息
        
        Args:
            user_id: 用户ID
            media_id: 媒体文件ID
            
        Returns:
            是否发送成功
        """
        try:
            await self.api_client.send_image_message(user_id, media_id)
            return True
        except WeComAPIException as e:
            logger.error(f"发送图片消息失败: {e}")
            return False
    
    async def download_media(self, media_id: str, save_path: str) -> Optional[Dict[str, Any]]:
        """
        下载媒体文件
        
        Args:
            media_id: 媒体文件ID
            save_path: 保存路径
            
        Returns:
            文件信息字典
        """
        try:
            return await self.api_client.download_media(media_id, save_path)
        except WeComAPIException as e:
            logger.error(f"下载媒体文件失败: {e}")
            return None
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典
        """
        try:
            user_info = await self.api_client.get_user_info(user_id)
            return {
                'user_id': user_info.user_id,
                'name': user_info.name,
                'department': user_info.department,
                'position': user_info.position,
                'mobile': user_info.mobile,
                'email': user_info.email,
                'avatar': user_info.avatar,
                'status': user_info.status
            }
        except WeComAPIException as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    async def close(self):
        """关闭Provider，释放资源"""
        await self.api_client.close()
        logger.info("企业微信Channel Provider已关闭")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
