"""
企业微信消息处理器
处理各种类型的消息（文本、图片、语音、位置等）
"""

import os
import logging
from typing import Optional, Dict, Any, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import inspect

from ..crypto.xml_parser import (
    BaseMessage, TextMessage, ImageMessage, VoiceMessage,
    LocationMessage, FileMessage, EventMessage, WeComXMLParser
)
from ..command_parser import CommandParser, CommandType, ParsedCommand
from ..api_client import WeComAPIClient

logger = logging.getLogger(__name__)

# Handler类型别名
TextHandlerType = Callable[[str, "MessageContext"], Any]
ImageHandlerType = Callable[[str, "MessageContext"], Any]
VoiceHandlerType = Callable[[str, "MessageContext"], Any]
LocationHandlerType = Callable[[float, float, str, "MessageContext"], Any]
EventHandlerType = Callable[["MessageContext"], Any]


@dataclass
class MessageContext:
    """消息上下文"""
    user_id: str
    session_id: str
    message: BaseMessage
    raw_xml: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageHandler(ABC):
    """消息处理器基类"""
    
    @abstractmethod
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """
        处理消息
        
        Args:
            message: 消息对象
            context: 消息上下文
            
        Returns:
            回复消息内容（可选）
        """
        pass
    
    @abstractmethod
    def can_handle(self, message: BaseMessage) -> bool:
        """是否可以处理该消息"""
        pass


async def _call_handler(handler: Callable, *args) -> Optional[str]:
    """调用处理器（支持同步和异步）"""
    if handler is None:
        return None
    result = handler(*args)
    if inspect.isawaitable(result):
        return await result
    return result


class TextMessageHandler(MessageHandler):
    """文本消息处理器"""
    
    def __init__(
        self,
        command_parser: Optional[CommandParser] = None,
        text_handler: Optional[TextHandlerType] = None
    ):
        self.command_parser = command_parser or CommandParser()
        self.text_handler = text_handler
    
    def can_handle(self, message: BaseMessage) -> bool:
        return isinstance(message, TextMessage)
    
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """处理文本消息"""
        if not isinstance(message, TextMessage):
            return None
        
        content = message.content.strip()
        logger.info(f"收到文本消息 from {context.user_id}: {content[:50]}...")
        
        # 解析命令
        command = self.command_parser.parse(content)
        
        # 如果有自定义处理器，交给它处理
        if self.text_handler:
            return await _call_handler(self.text_handler, content, context)
        
        # 默认处理：返回命令解析结果
        if command.command_type != CommandType.UNKNOWN:
            return self._handle_command(command, context)
        
        # 一般对话
        return f"收到您的消息：{content}\n\n如需帮助，请发送 /help"
    
    def _handle_command(self, command: ParsedCommand, context: MessageContext) -> str:
        """处理命令"""
        if command.command_type == CommandType.HELP:
            return self.command_parser.get_help_text()
        
        if command.command_type == CommandType.START:
            community = command.args[0] if command.args else "未指定"
            return f"🏠 开始驻点工作：{community}\n\n请选择要开展的工作：\n[配电房检查] [客户走访] [应急信息采集]"
        
        if command.command_type == CommandType.STATUS:
            return "📊 当前状态：待机中\n\n暂无进行中的任务"
        
        if command.command_type == CommandType.CANCEL:
            return "✅ 已取消当前任务"
        
        return f"收到命令：{command.name}\n参数：{command.args}"


class ImageMessageHandler(MessageHandler):
    """图片消息处理器"""
    
    def __init__(
        self,
        api_client: WeComAPIClient,
        image_handler: Optional[ImageHandlerType] = None,
        storage_path: str = "./temp/images"
    ):
        self.api_client = api_client
        self.image_handler = image_handler
        self.storage_path = storage_path
    
    def can_handle(self, message: BaseMessage) -> bool:
        return isinstance(message, ImageMessage)
    
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """处理图片消息"""
        if not isinstance(message, ImageMessage):
            return None
        
        logger.info(f"收到图片消息 from {context.user_id}, media_id: {message.media_id}")
        
        try:
            # 下载图片
            save_path = os.path.join(self.storage_path, f"{message.media_id}.jpg")
            result = await self.api_client.download_media(
                media_id=message.media_id,
                save_path=save_path
            )
            
            logger.info(f"图片下载成功: {result['size']} bytes")
            
            # 如果有自定义处理器，交给它处理
            if self.image_handler:
                return await _call_handler(self.image_handler, save_path, context)
            
            # 默认返回成功消息
            return f"✅ 照片已接收并保存\n\n文件名: {os.path.basename(save_path)}\n大小: {result['size'] / 1024:.1f} KB\n\n🔍 正在分析照片内容..."
            
        except Exception as e:
            logger.error(f"处理图片消息失败: {e}")
            return f"❌ 照片处理失败: {str(e)}"


class VoiceMessageHandler(MessageHandler):
    """语音消息处理器"""
    
    def __init__(
        self,
        api_client: WeComAPIClient,
        voice_handler: Optional[VoiceHandlerType] = None,
        storage_path: str = "./temp/voice",
        enable_stt: bool = True
    ):
        self.api_client = api_client
        self.voice_handler = voice_handler
        self.storage_path = storage_path
        self.enable_stt = enable_stt
    
    def can_handle(self, message: BaseMessage) -> bool:
        return isinstance(message, VoiceMessage)
    
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """处理语音消息"""
        if not isinstance(message, VoiceMessage):
            return None
        
        logger.info(f"收到语音消息 from {context.user_id}, media_id: {message.media_id}")
        
        try:
            # 下载语音
            save_path = os.path.join(self.storage_path, f"{message.media_id}.amr")
            result = await self.api_client.download_media(
                media_id=message.media_id,
                save_path=save_path
            )
            
            logger.info(f"语音下载成功: {result['size']} bytes")
            
            # 如果企业微信已提供语音识别结果
            if message.recognition:
                logger.info(f"语音识别结果: {message.recognition}")
                
                # 如果有自定义处理器，交给它处理
                if self.voice_handler:
                    return await _call_handler(self.voice_handler, message.recognition, context)
                
                return f"🎤 语音消息已识别:\n\n{message.recognition}\n\n正在处理..."
            
            # 如果没有语音识别结果，需要调用STT服务
            if self.enable_stt:
                return "🎤 语音消息已接收\n\n正在进行语音识别，请稍候..."
            
            return "✅ 语音消息已接收\n\n（语音识别功能未启用）"
            
        except Exception as e:
            logger.error(f"处理语音消息失败: {e}")
            return f"❌ 语音处理失败: {str(e)}"


class LocationMessageHandler(MessageHandler):
    """位置消息处理器"""
    
    def __init__(
        self,
        location_handler: Optional[LocationHandlerType] = None
    ):
        self.location_handler = location_handler
    
    def can_handle(self, message: BaseMessage) -> bool:
        return isinstance(message, LocationMessage)
    
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """处理位置消息"""
        if not isinstance(message, LocationMessage):
            return None
        
        logger.info(
            f"收到位置消息 from {context.user_id}: "
            f"({message.location_x}, {message.location_y}) - {message.label}"
        )
        
        # 如果有自定义处理器，交给它处理
        if self.location_handler:
            return await _call_handler(
                self.location_handler,
                message.location_x,
                message.location_y,
                message.label,
                context
            )
        
        # 默认返回位置信息
        return (
            f"📍 位置已接收\n\n"
            f"坐标: {message.location_x}, {message.location_y}\n"
            f"地址: {message.label}\n"
            f"精度: {message.scale}米"
        )


class EventMessageHandler(MessageHandler):
    """事件消息处理器"""
    
    def __init__(
        self,
        subscribe_handler: Optional[EventHandlerType] = None,
        unsubscribe_handler: Optional[EventHandlerType] = None
    ):
        self.subscribe_handler = subscribe_handler
        self.unsubscribe_handler = unsubscribe_handler
    
    def can_handle(self, message: BaseMessage) -> bool:
        return isinstance(message, EventMessage)
    
    async def handle(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """处理事件消息"""
        if not isinstance(message, EventMessage):
            return None
        
        event = message.event.lower()
        logger.info(f"收到事件消息 from {context.user_id}: {event}")
        
        if event == 'subscribe':
            if self.subscribe_handler:
                return await _call_handler(self.subscribe_handler, context)
            
            return (
                "🎉 欢迎使用现场信息采集助手！\n\n"
                "我可以帮助您：\n"
                "• 📋 驻点工作引导\n"
                "• 📸 照片智能分析\n"
                "• 📝 文档自动生成\n"
                "• 🚨 应急处置支持\n\n"
                "发送 /help 查看详细使用说明"
            )
        
        if event == 'unsubscribe':
            if self.unsubscribe_handler:
                return await _call_handler(self.unsubscribe_handler, context)
            
            logger.info(f"用户 {context.user_id} 取消关注")
            return None
        
        if event == 'enter_agent':
            return "👋 欢迎回来！有什么可以帮助您的吗？"
        
        if event == 'location':
            return (
                f"📍 位置上报事件\n\n"
                f"坐标: {message.latitude}, {message.longitude}\n"
                f"精度: {message.precision}米"
            )
        
        return None


class MessageDispatcher:
    """消息分发器"""
    
    def __init__(self):
        self.handlers: list[MessageHandler] = []
    
    def register_handler(self, handler: MessageHandler):
        """注册处理器"""
        self.handlers.append(handler)
        logger.info(f"注册消息处理器: {handler.__class__.__name__}")
    
    async def dispatch(self, message: BaseMessage, context: MessageContext) -> Optional[str]:
        """
        分发消息到对应的处理器
        
        Args:
            message: 消息对象
            context: 消息上下文
            
        Returns:
            回复消息内容
        """
        for handler in self.handlers:
            if handler.can_handle(message):
                try:
                    return await handler.handle(message, context)
                except Exception as e:
                    logger.error(f"消息处理失败: {e}", exc_info=True)
                    return f"❌ 处理消息时出错: {str(e)}"
        
        logger.warning(f"未找到消息处理器: {message.msg_type}")
        return "暂不支持该类型消息"


class WeComMessageProcessor:
    """企业微信消息处理器（整合类）"""
    
    def __init__(
        self,
        api_client: WeComAPIClient,
        command_parser: Optional[CommandParser] = None,
        storage_path: str = "./temp"
    ):
        self.api_client = api_client
        self.command_parser = command_parser or CommandParser()
        self.storage_path = storage_path
        
        # 创建分发器
        self.dispatcher = MessageDispatcher()
        
        # 注册处理器
        self._register_handlers()
    
    def _register_handlers(self):
        """注册默认的消息处理器"""
        # 文本消息处理器
        self.dispatcher.register_handler(
            TextMessageHandler(self.command_parser)
        )
        
        # 图片消息处理器
        self.dispatcher.register_handler(
            ImageMessageHandler(
                api_client=self.api_client,
                storage_path=os.path.join(self.storage_path, "images")
            )
        )
        
        # 语音消息处理器
        self.dispatcher.register_handler(
            VoiceMessageHandler(
                api_client=self.api_client,
                storage_path=os.path.join(self.storage_path, "voice")
            )
        )
        
        # 位置消息处理器
        self.dispatcher.register_handler(LocationMessageHandler())
        
        # 事件消息处理器
        self.dispatcher.register_handler(EventMessageHandler())
    
    async def process_xml(self, xml_string: str) -> Optional[str]:
        """
        处理XML格式的消息
        
        Args:
            xml_string: XML消息字符串
            
        Returns:
            回复消息内容
        """
        try:
            # 解析消息
            message = WeComXMLParser.parse_message(xml_string)
            
            # 创建上下文
            context = MessageContext(
                user_id=message.from_user_name,
                session_id=message.from_user_name,  # 使用user_id作为session_id
                message=message,
                raw_xml=xml_string
            )
            
            # 分发处理
            return await self.dispatcher.dispatch(message, context)
            
        except Exception as e:
            logger.error(f"处理XML消息失败: {e}", exc_info=True)
            return "消息处理失败，请重试"
    
    def register_custom_handler(self, handler: MessageHandler):
        """注册自定义处理器"""
        self.dispatcher.register_handler(handler)
