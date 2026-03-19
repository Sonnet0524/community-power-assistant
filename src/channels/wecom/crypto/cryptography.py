"""
企业微信消息加解密模块
遵循企业微信官方加解密规范
https://developer.work.weixin.qq.com/document/path/96211
"""

import base64
import hashlib
import struct
import time
from Crypto.Cipher import AES
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class WeComDecryptResult:
    """解密结果"""
    msg: str
    receive_id: str


class WeComCryptoError(Exception):
    """加解密错误"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class WeComCryptography:
    """
    企业微信消息加解密类
    
    企业微信使用AES-CBC加密，关键参数：
    - AES密钥长度：256位（32字节）
    - 初始向量（IV）：使用AES密钥的前16字节
    - 填充方式：PKCS7
    """
    
    # 错误码定义
    ERROR_INVALID_SIGNATURE = -40001
    ERROR_INVALID_XML = -40002
    ERROR_INVALID_CORP_ID = -40003
    ERROR_INVALID_AES_KEY = -40004
    ERROR_INVALID_MSG = -40005
    ERROR_INVALID_BUFFER = -40006
    ERROR_INVALID_ENCODE = -40007
    ERROR_INVALID_DECODE = -40008
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        """
        初始化加解密工具
        
        Args:
            token: 企业微信配置的Token
            encoding_aes_key: 企业微信配置的EncodingAESKey（43字符Base64编码）
            corp_id: 企业微信CorpID
        """
        self.token = token
        self.corp_id = corp_id
        
        # 解码AES密钥（43字符Base64解码为32字节）
        try:
            self.aes_key = base64.b64decode(encoding_aes_key + '=')
            if len(self.aes_key) != 32:
                raise WeComCryptoError(
                    self.ERROR_INVALID_AES_KEY,
                    f"AES密钥长度错误: {len(self.aes_key)}，应为32字节"
                )
        except Exception as e:
            raise WeComCryptoError(
                self.ERROR_INVALID_AES_KEY,
                f"AES密钥解码失败: {str(e)}"
            )
    
    def _pkcs7_encode(self, data: bytes) -> bytes:
        """
        PKCS7填充
        
        填充规则：
        - 块大小固定为32字节
        - 需要填充的字节数 = 32 - (len(data) % 32)
        - 每个填充字节的值 = 需要填充的字节数
        """
        block_size = 32
        padding_len = block_size - (len(data) % block_size)
        padding = bytes([padding_len] * padding_len)
        return data + padding
    
    def _pkcs7_decode(self, data: bytes) -> bytes:
        """PKCS7去除填充"""
        if not data:
            return data
        padding_len = data[-1]
        if padding_len > 32 or padding_len == 0:
            return data
        return data[:-padding_len]
    
    def encrypt(self, msg: str, receive_id: str) -> str:
        """
        加密消息
        
        加密过程：
        1. 生成16字节随机字符串
        2. 计算msg长度（4字节网络字节序）
        3. 拼接：random(16) + msg_len(4) + msg + receive_id
        4. AES-CBC加密
        5. Base64编码
        
        Args:
            msg: 待加密的明文消息
            receive_id: 接收方ID（企业微信为CorpID）
            
        Returns:
            Base64编码的密文
        """
        try:
            # 生成16字节随机字符串
            random_bytes = bytes([ord(c) for c in "1234567890123456"])
            
            # 计算消息长度（4字节，网络字节序大端）
            msg_bytes = msg.encode('utf-8')
            msg_len = struct.pack('>I', len(msg_bytes))
            
            # 拼接数据
            receive_id_bytes = receive_id.encode('utf-8')
            data = random_bytes + msg_len + msg_bytes + receive_id_bytes
            
            # PKCS7填充
            padded_data = self._pkcs7_encode(data)
            
            # AES-CBC加密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            encrypted = cipher.encrypt(padded_data)
            
            # Base64编码
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            raise WeComCryptoError(
                self.ERROR_INVALID_ENCODE,
                f"加密失败: {str(e)}"
            )
    
    def decrypt(self, encrypted_msg: str) -> WeComDecryptResult:
        """
        解密消息
        
        解密过程：
        1. Base64解码
        2. AES-CBC解密
        3. PKCS7去除填充
        4. 解析：random(16) + msg_len(4) + msg + receive_id
        5. 验证receive_id
        
        Args:
            encrypted_msg: Base64编码的密文
            
        Returns:
            WeComDecryptResult包含解密后的消息和receive_id
        """
        try:
            # Base64解码
            encrypted_data = base64.b64decode(encrypted_msg)
            
            # AES-CBC解密
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            decrypted = cipher.decrypt(encrypted_data)
            
            # PKCS7去除填充
            unpadded = self._pkcs7_decode(decrypted)
            
            # 解析数据
            if len(unpadded) < 20:
                raise WeComCryptoError(
                    self.ERROR_INVALID_MSG,
                    "解密后数据长度不足"
                )
            
            # 读取消息长度（4字节，网络字节序）
            msg_len = struct.unpack('>I', unpadded[16:20])[0]
            
            # 提取消息和receive_id
            msg = unpadded[20:20 + msg_len].decode('utf-8')
            receive_id = unpadded[20 + msg_len:].decode('utf-8')
            
            # 验证receive_id
            if receive_id != self.corp_id:
                raise WeComCryptoError(
                    self.ERROR_INVALID_CORP_ID,
                    f"CorpID不匹配: {receive_id} != {self.corp_id}"
                )
            
            return WeComDecryptResult(msg=msg, receive_id=receive_id)
            
        except WeComCryptoError:
            raise
        except Exception as e:
            raise WeComCryptoError(
                self.ERROR_INVALID_DECODE,
                f"解密失败: {str(e)}"
            )
    
    def generate_signature(self, timestamp: str, nonce: str, encrypt: str) -> str:
        """
        生成消息签名
        
        签名算法：
        1. 将token、timestamp、nonce、encrypt按字典序排序
        2. 拼接成字符串
        3. SHA1哈希
        4. 转十六进制小写
        
        Args:
            timestamp: 时间戳
            nonce: 随机字符串
            encrypt: 密文
            
        Returns:
            SHA1签名（40字符十六进制）
        """
        try:
            # 按字典序排序并拼接
            data = [self.token, timestamp, nonce, encrypt]
            data.sort()
            content = ''.join(data)
            
            # SHA1哈希
            sha1_hash = hashlib.sha1(content.encode('utf-8')).hexdigest()
            return sha1_hash
            
        except Exception as e:
            raise WeComCryptoError(
                self.ERROR_INVALID_BUFFER,
                f"签名生成失败: {str(e)}"
            )
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, encrypt: str) -> bool:
        """
        验证消息签名
        
        Args:
            signature: 待验证的签名
            timestamp: 时间戳
            nonce: 随机字符串
            encrypt: 密文
            
        Returns:
            验证结果
        """
        try:
            expected = self.generate_signature(timestamp, nonce, encrypt)
            return signature == expected
        except Exception:
            return False
    
    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echo_str: str) -> str:
        """
        验证回调URL（企业微信服务器配置验证）
        
        回调验证流程：
        1. 验证消息签名
        2. 解密echo_str
        3. 返回明文echo_str
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机字符串
            echo_str: 加密的回显字符串
            
        Returns:
            解密后的明文
            
        Raises:
            WeComCryptoError: 验证失败
        """
        # 验证签名
        if not self.verify_signature(msg_signature, timestamp, nonce, echo_str):
            raise WeComCryptoError(
                self.ERROR_INVALID_SIGNATURE,
                "URL验证签名不匹配"
            )
        
        # 解密echo_str
        result = self.decrypt(echo_str)
        return result.msg


class MessageDeduplicator:
    """消息去重器"""
    
    def __init__(self, ttl: int = 300):
        """
        Args:
            ttl: 消息去重时间窗口（秒）
        """
        self.ttl = ttl
        self._processed_msgs: dict[str, float] = {}
    
    def is_duplicate(self, msg_id: str) -> bool:
        """
        检查消息是否重复
        
        Args:
            msg_id: 消息ID
            
        Returns:
            True表示重复，False表示新消息
        """
        now = time.time()
        
        # 清理过期的消息记录
        expired = [k for k, v in self._processed_msgs.items() if now - v > self.ttl]
        for k in expired:
            del self._processed_msgs[k]
        
        # 检查是否已处理
        if msg_id in self._processed_msgs:
            return True
        
        # 记录本次消息
        self._processed_msgs[msg_id] = now
        return False
    
    def mark_processed(self, msg_id: str):
        """标记消息已处理"""
        self._processed_msgs[msg_id] = time.time()
