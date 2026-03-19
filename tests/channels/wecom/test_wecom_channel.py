"""
企业微信Channel测试套件
测试消息加解密、消息处理、API调用等功能
"""

import pytest
import asyncio
import base64
import hashlib
import xml.etree.ElementTree as ET
from Crypto.Cipher import AES
import struct

# 导入待测试模块
import sys
sys.path.insert(0, '/Users/sonnet/opencode/community-power-assistant/src')

from channels.wecom.crypto.cryptography import (
    WeComCryptography, WeComCryptoError, MessageDeduplicator
)
from channels.wecom.crypto.xml_parser import (
    WeComXMLParser, TextMessage, ImageMessage, VoiceMessage,
    LocationMessage, EventMessage
)
from channels.wecom.command_parser import CommandParser, CommandType


# ========== 测试配置 ==========

TEST_CONFIG = {
    'token': 'test_token_123456',
    'encoding_aes_key': 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG',
    'corp_id': 'ww1234567890abcdef'
}


# ========== 加解密测试 ==========

class TestWeComCryptography:
    """测试消息加解密功能"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.crypto = WeComCryptography(
            token=TEST_CONFIG['token'],
            encoding_aes_key=TEST_CONFIG['encoding_aes_key'],
            corp_id=TEST_CONFIG['corp_id']
        )
    
    def test_pkcs7_encode_decode(self):
        """测试PKCS7填充和去填充"""
        # 测试填充
        data = b'hello world'
        padded = self.crypto._pkcs7_encode(data)
        assert len(padded) % 32 == 0
        
        # 测试去填充
        unpadded = self.crypto._pkcs7_decode(padded)
        assert unpadded == data
    
    def test_encrypt_decrypt(self):
        """测试加密和解密"""
        original_msg = "这是一条测试消息"
        
        # 加密
        encrypted = self.crypto.encrypt(original_msg, TEST_CONFIG['corp_id'])
        assert encrypted is not None
        assert len(encrypted) > 0
        
        # 解密
        result = self.crypto.decrypt(encrypted)
        assert result.msg == original_msg
        assert result.receive_id == TEST_CONFIG['corp_id']
    
    def test_signature_generation(self):
        """测试签名生成"""
        timestamp = '1234567890'
        nonce = 'abc123'
        encrypt = 'encrypted_message'
        
        signature = self.crypto.generate_signature(timestamp, nonce, encrypt)
        assert len(signature) == 40  # SHA1哈希长度为40
        
        # 验证签名
        is_valid = self.crypto.verify_signature(signature, timestamp, nonce, encrypt)
        assert is_valid is True
        
        # 测试错误签名
        is_invalid = self.crypto.verify_signature('wrong_signature', timestamp, nonce, encrypt)
        assert is_invalid is False
    
    def test_decrypt_invalid_corp_id(self):
        """测试CorpID不匹配的情况"""
        original_msg = "测试消息"
        encrypted = self.crypto.encrypt(original_msg, TEST_CONFIG['corp_id'])
        
        # 创建错误的crypto对象
        wrong_crypto = WeComCryptography(
            token=TEST_CONFIG['token'],
            encoding_aes_key=TEST_CONFIG['encoding_aes_key'],
            corp_id='wrong_corp_id'
        )
        
        with pytest.raises(WeComCryptoError) as exc_info:
            wrong_crypto.decrypt(encrypted)
        
        assert exc_info.value.code == WeComCryptoError.ERROR_INVALID_CORP_ID


class TestMessageDeduplicator:
    """测试消息去重功能"""
    
    def test_duplicate_detection(self):
        """测试消息去重检测"""
        dedup = MessageDeduplicator(ttl=60)
        
        msg_id = '1234567890123456'
        
        # 第一次应该不是重复
        assert dedup.is_duplicate(msg_id) is False
        
        # 第二次应该是重复
        assert dedup.is_duplicate(msg_id) is True
        
        # 不同的消息ID不是重复
        assert dedup.is_duplicate('9999999999999999') is False


# ========== XML解析测试 ==========

class TestWeComXMLParser:
    """测试XML解析功能"""
    
    def test_parse_text_message(self):
        """测试文本消息解析"""
        xml = """<xml>
        <ToUserName><![CDATA[corp_id]]></ToUserName>
        <FromUserName><![CDATA[user123]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[/start 阳光小区]]></Content>
        <MsgId>1234567890123456</MsgId>
        <AgentID>1000002</AgentID>
        </xml>"""
        
        result = WeComXMLParser.parse(xml)
        assert result['ToUserName'] == 'corp_id'
        assert result['FromUserName'] == 'user123'
        assert result['MsgType'] == 'text'
        assert result['Content'] == '/start 阳光小区'
    
    def test_parse_image_message(self):
        """测试图片消息解析"""
        xml = """<xml>
        <ToUserName><![CDATA[corp_id]]></ToUserName>
        <FromUserName><![CDATA[user123]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[image]]></MsgType>
        <PicUrl><![CDATA[http://example.com/image.jpg]]></PicUrl>
        <MediaId><![CDATA[media_id_123]]></MediaId>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        
        result = WeComXMLParser.parse(xml)
        assert result['MsgType'] == 'image'
        assert result['PicUrl'] == 'http://example.com/image.jpg'
        assert result['MediaId'] == 'media_id_123'
    
    def test_parse_location_message(self):
        """测试位置消息解析"""
        xml = """<xml>
        <ToUserName><![CDATA[corp_id]]></ToUserName>
        <FromUserName><![CDATA[user123]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[location]]></MsgType>
        <Location_X>104.0668</Location_X>
        <Location_Y>30.5728</Location_Y>
        <Scale>15</Scale>
        <Label><![CDATA[成都市武侯区]]></Label>
        <MsgId>1234567890123456</MsgId>
        </xml>"""
        
        message = WeComXMLParser.parse_message(xml)
        assert isinstance(message, LocationMessage)
        assert message.location_x == 104.0668
        assert message.location_y == 30.5728
        assert message.label == '成都市武侯区'
    
    def test_parse_event_message(self):
        """测试事件消息解析"""
        xml = """<xml>
        <ToUserName><![CDATA[corp_id]]></ToUserName>
        <FromUserName><![CDATA[user123]]></FromUserName>
        <CreateTime>123456789</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[subscribe]]></Event>
        <AgentID>1000002</AgentID>
        </xml>"""
        
        message = WeComXMLParser.parse_message(xml)
        assert isinstance(message, EventMessage)
        assert message.event == 'subscribe'
    
    def test_build_text_response(self):
        """测试构建文本响应"""
        xml = WeComXMLParser.build_text_response(
            to_user='user123',
            from_user='corp_id',
            content='回复消息'
        )
        
        result = WeComXMLParser.parse(xml)
        assert result['ToUserName'] == 'user123'
        assert result['FromUserName'] == 'corp_id'
        assert result['MsgType'] == 'text'
        assert result['Content'] == '回复消息'


# ========== 命令解析测试 ==========

class TestCommandParser:
    """测试命令解析功能"""
    
    def setup_method(self):
        self.parser = CommandParser()
    
    def test_parse_start_command(self):
        """测试/start命令解析"""
        result = self.parser.parse('/start 阳光小区')
        
        assert result.command_type == CommandType.START
        assert result.name == 'start'
        assert result.args == ['阳光小区']
        assert result.confidence == 1.0
    
    def test_parse_status_command(self):
        """测试/status命令解析"""
        result = self.parser.parse('/status')
        
        assert result.command_type == CommandType.STATUS
        assert result.name == 'status'
        assert len(result.args) == 0
    
    def test_parse_help_command(self):
        """测试/help命令解析"""
        result = self.parser.parse('/help')
        
        assert result.command_type == CommandType.HELP
        assert result.name == 'help'
    
    def test_parse_emergency_command(self):
        """测试/emergency命令解析"""
        result = self.parser.parse('/emergency 停电 阳光小区')
        
        assert result.command_type == CommandType.EMERGENCY
        assert result.name == 'emergency'
        assert result.args == ['停电', '阳光小区']
    
    def test_parse_natural_language(self):
        """测试自然语言解析"""
        result = self.parser.parse('我要去阳光小区驻点')
        
        assert result.command_type == CommandType.START
        assert result.name == 'start'
        assert result.confidence < 1.0  # 自然语言解析置信度较低
    
    def test_parse_unknown(self):
        """测试未知输入"""
        result = self.parser.parse('随便说点什么')
        
        assert result.command_type == CommandType.UNKNOWN
        assert result.confidence < 0.5
    
    def test_is_command(self):
        """测试命令检测"""
        assert self.parser.is_command('/start 小区') is True
        assert self.parser.is_command('/help') is True
        assert self.parser.is_command('普通对话') is False
    
    def test_get_help_text(self):
        """测试帮助文本生成"""
        help_text = self.parser.get_help_text()
        
        assert '/start' in help_text
        assert '/help' in help_text
        assert '/status' in help_text


# ========== 集成测试 ==========

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """测试完整的消息处理流程"""
        crypto = WeComCryptography(
            token=TEST_CONFIG['token'],
            encoding_aes_key=TEST_CONFIG['encoding_aes_key'],
            corp_id=TEST_CONFIG['corp_id']
        )
        
        # 构建原始消息
        original_xml = WeComXMLParser.build_text_response(
            to_user=TEST_CONFIG['corp_id'],
            from_user='user123',
            content='测试消息'
        )
        
        # 加密
        encrypted = crypto.encrypt(original_xml, TEST_CONFIG['corp_id'])
        
        # 生成签名
        timestamp = '1234567890'
        nonce = 'abc123'
        signature = crypto.generate_signature(timestamp, nonce, encrypted)
        
        # 验证签名
        assert crypto.verify_signature(signature, timestamp, nonce, encrypted)
        
        # 解密
        result = crypto.decrypt(encrypted)
        assert TEST_CONFIG['corp_id'] in result.msg


# ========== 运行测试 ==========

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
