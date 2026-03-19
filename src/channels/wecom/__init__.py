"""
企业微信Channel模块

基于OpenClaw规范的企业微信集成实现
支持消息加解密、接收处理、媒体下载、消息发送等功能
"""

from .crypto.cryptography import WeComCryptography, WeComCryptoError, MessageDeduplicator
from .crypto.xml_parser import (
    WeComXMLParser, BaseMessage, TextMessage, ImageMessage,
    VoiceMessage, LocationMessage, FileMessage, EventMessage,
    MessageType, EventType
)
from .api_client import WeComAPIClient, AccessToken, WeComUserInfo
from .command_parser import CommandParser, CommandType, ParsedCommand, IntentRecognizer
from .errors import (
    WeComError, WeComErrorCode, WeComAPIException,
    RetryConfig, CircuitBreaker, ErrorHandler,
    with_retry, with_circuit_breaker
)
from .handlers.message_handler import (
    MessageHandler, MessageContext,
    TextMessageHandler, ImageMessageHandler,
    VoiceMessageHandler, LocationMessageHandler,
    EventMessageHandler, MessageDispatcher,
    WeComMessageProcessor
)
from .provider import WeComChannelProvider

__version__ = "1.0.0"

__all__ = [
    # 加解密
    'WeComCryptography',
    'WeComCryptoError',
    'MessageDeduplicator',
    
    # XML解析
    'WeComXMLParser',
    'BaseMessage',
    'TextMessage',
    'ImageMessage',
    'VoiceMessage',
    'LocationMessage',
    'FileMessage',
    'EventMessage',
    'MessageType',
    'EventType',
    
    # API客户端
    'WeComAPIClient',
    'AccessToken',
    'WeComUserInfo',
    
    # 命令解析
    'CommandParser',
    'CommandType',
    'ParsedCommand',
    'IntentRecognizer',
    
    # 错误处理
    'WeComError',
    'WeComErrorCode',
    'WeComAPIException',
    'RetryConfig',
    'CircuitBreaker',
    'ErrorHandler',
    'with_retry',
    'with_circuit_breaker',
    
    # 消息处理
    'MessageHandler',
    'MessageContext',
    'TextMessageHandler',
    'ImageMessageHandler',
    'VoiceMessageHandler',
    'LocationMessageHandler',
    'EventMessageHandler',
    'MessageDispatcher',
    'WeComMessageProcessor',
    
    # Provider
    'WeComChannelProvider',
]
