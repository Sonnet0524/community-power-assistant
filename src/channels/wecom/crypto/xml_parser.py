"""
企业微信消息XML解析模块
处理企业微信推送消息的XML格式
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    LOCATION = "location"
    FILE = "file"
    EVENT = "event"
    LINK = "link"


class EventType(Enum):
    """事件类型枚举"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ENTER_AGENT = "enter_agent"
    LOCATION = "LOCATION"
    BATCH_JOB_RESULT = "batch_job_result"


@dataclass
class BaseMessage:
    """基础消息结构"""
    to_user_name: str
    from_user_name: str
    create_time: int
    msg_type: str
    msg_id: Optional[int] = None
    agent_id: Optional[int] = None
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'BaseMessage':
        """从XML字典创建基础消息"""
        return cls(
            to_user_name=data.get('ToUserName', ''),
            from_user_name=data.get('FromUserName', ''),
            create_time=int(data.get('CreateTime', 0)),
            msg_type=data.get('MsgType', ''),
            msg_id=data.get('MsgId'),
            agent_id=data.get('AgentID')
        )


@dataclass
class TextMessage(BaseMessage):
    """文本消息"""
    content: str = ""
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'TextMessage':
        """从XML字典创建文本消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            content=data.get('Content', '')
        )


@dataclass
class ImageMessage(BaseMessage):
    """图片消息"""
    pic_url: str = ""
    media_id: str = ""
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'ImageMessage':
        """从XML字典创建图片消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            pic_url=data.get('PicUrl', ''),
            media_id=data.get('MediaId', '')
        )


@dataclass
class VoiceMessage(BaseMessage):
    """语音消息"""
    media_id: str = ""
    format: str = ""
    recognition: Optional[str] = None  # 语音识别结果（需开通语音识别功能）
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'VoiceMessage':
        """从XML字典创建语音消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            media_id=data.get('MediaId', ''),
            format=data.get('Format', 'amr'),
            recognition=data.get('Recognition')
        )


@dataclass
class VideoMessage(BaseMessage):
    """视频消息"""
    media_id: str = ""
    thumb_media_id: str = ""
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'VideoMessage':
        """从XML字典创建视频消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            media_id=data.get('MediaId', ''),
            thumb_media_id=data.get('ThumbMediaId', '')
        )


@dataclass
class LocationMessage(BaseMessage):
    """位置消息"""
    location_x: float = 0.0
    location_y: float = 0.0
    scale: int = 0
    label: str = ""
    app_type: Optional[str] = None
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'LocationMessage':
        """从XML字典创建位置消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            location_x=float(data.get('Location_X', 0)),
            location_y=float(data.get('Location_Y', 0)),
            scale=int(data.get('Scale', 0)),
            label=data.get('Label', ''),
            app_type=data.get('AppType')
        )


@dataclass
class FileMessage(BaseMessage):
    """文件消息"""
    media_id: str = ""
    file_name: str = ""
    file_md5: str = ""
    file_size: int = 0
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'FileMessage':
        """从XML字典创建文件消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            media_id=data.get('MediaId', ''),
            file_name=data.get('FileName', ''),
            file_md5=data.get('FileMd5', ''),
            file_size=int(data.get('FileSize', 0))
        )


@dataclass
class EventMessage(BaseMessage):
    """事件消息"""
    event: str = ""
    event_key: Optional[str] = None
    # 地理位置事件
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    precision: Optional[float] = None
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'EventMessage':
        """从XML字典创建事件消息"""
        base = BaseMessage.from_xml_dict(data)
        return cls(
            to_user_name=base.to_user_name,
            from_user_name=base.from_user_name,
            create_time=base.create_time,
            msg_type=base.msg_type,
            msg_id=base.msg_id,
            agent_id=base.agent_id,
            event=data.get('Event', ''),
            event_key=data.get('EventKey'),
            latitude=float(lat) if (lat := data.get('Latitude')) else None,
            longitude=float(lng) if (lng := data.get('Longitude')) else None,
            precision=float(prec) if (prec := data.get('Precision')) else None
        )


class WeComXMLParser:
    """企业微信XML消息解析器"""
    
    @staticmethod
    def parse(xml_string: str) -> Dict[str, Any]:
        """
        解析XML字符串为字典
        
        Args:
            xml_string: XML字符串
            
        Returns:
            解析后的字典
        """
        try:
            root = ET.fromstring(xml_string)
            result = {}
            
            for child in root:
                if child.text:
                    result[child.tag] = child.text.strip()
                else:
                    result[child.tag] = ""
            
            return result
        except ET.ParseError as e:
            raise ValueError(f"XML解析失败: {str(e)}")
    
    @staticmethod
    def parse_message(xml_string: str) -> BaseMessage:
        """
        解析消息XML
        
        Args:
            xml_string: XML字符串
            
        Returns:
            对应类型的消息对象
        """
        data = WeComXMLParser.parse(xml_string)
        msg_type = data.get('MsgType', '').lower()
        
        # 根据消息类型返回对应的消息对象
        if msg_type == 'text':
            return TextMessage.from_xml_dict(data)
        elif msg_type == 'image':
            return ImageMessage.from_xml_dict(data)
        elif msg_type == 'voice':
            return VoiceMessage.from_xml_dict(data)
        elif msg_type == 'video':
            return VideoMessage.from_xml_dict(data)
        elif msg_type == 'location':
            return LocationMessage.from_xml_dict(data)
        elif msg_type == 'file':
            return FileMessage.from_xml_dict(data)
        elif msg_type == 'event':
            return EventMessage.from_xml_dict(data)
        else:
            # 未知类型，返回基础消息
            return BaseMessage.from_xml_dict(data)
    
    @staticmethod
    def build_text_response(to_user: str, from_user: str, content: str) -> str:
        """
        构建文本消息响应XML
        
        Args:
            to_user: 接收方UserID
            from_user: 发送方UserID
            content: 消息内容
            
        Returns:
            XML字符串
        """
        import time
        create_time = int(time.time())
        
        xml = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
        return xml
    
    @staticmethod
    def build_encrypt_response(
        encrypt: str,
        signature: str,
        timestamp: str,
        nonce: str
    ) -> str:
        """
        构建加密消息响应XML
        
        Args:
            encrypt: 加密后的消息
            signature: 消息签名
            timestamp: 时间戳
            nonce: 随机字符串
            
        Returns:
            XML字符串
        """
        xml = f"""<xml>
<Encrypt><![CDATA[{encrypt}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
        return xml
