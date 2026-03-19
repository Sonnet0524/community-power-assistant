"""
企业微信API对接测试
测试与企业微信API的集成（需要网络连接和有效凭证）

注意：运行这些测试需要有效的企业微信凭证
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, '/Users/sonnet/opencode/community-power-assistant/src')

from channels.wecom.api_client import WeComAPIClient, AccessToken
from channels.wecom.errors import WeComAPIException, WeComErrorCode


# 标记需要真实API调用的测试
requires_credentials = pytest.mark.skipif(
    not os.environ.get('WECOM_CORP_ID'),
    reason="需要企业微信凭证（设置WECOM_CORP_ID环境变量）"
)


class TestWeComAPIClientMock:
    """使用Mock测试API客户端"""
    
    @pytest.fixture
    def client(self):
        """创建API客户端实例"""
        return WeComAPIClient(
            corp_id='test_corp_id',
            secret='test_secret',
            agent_id=1000002
        )
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, client):
        """测试获取AccessToken成功"""
        mock_response = {
            'access_token': 'test_token_123',
            'expires_in': 7200
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            token = await client.get_access_token()
            assert token == 'test_token_123'
    
    @pytest.mark.asyncio
    async def test_send_text_message_success(self, client):
        """测试发送文本消息成功"""
        mock_response = {
            'errcode': 0,
            'errmsg': 'ok',
            'invaliduser': []
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.send_text_message(
                user_id='test_user',
                content='测试消息'
            )
            
            assert result['errcode'] == 0
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_text_message_too_long(self, client):
        """测试发送过长的文本消息"""
        long_content = 'x' * 3000  # 超过2048字节限制
        
        with pytest.raises(ValueError) as exc_info:
            await client.send_text_message(
                user_id='test_user',
                content=long_content
            )
        
        assert '过长' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_markdown_message_success(self, client):
        """测试发送Markdown消息成功"""
        mock_response = {'errcode': 0, 'errmsg': 'ok'}
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.send_markdown_message(
                user_id='test_user',
                markdown='# 标题\n正文内容'
            )
            
            assert result['errcode'] == 0
    
    @pytest.mark.asyncio
    async def test_send_card_message_success(self, client):
        """测试发送卡片消息成功"""
        mock_response = {'errcode': 0, 'errmsg': 'ok'}
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.send_text_card_message(
                user_id='test_user',
                title='卡片标题',
                description='卡片描述',
                url='https://example.com'
            )
            
            assert result['errcode'] == 0
    
    @pytest.mark.asyncio
    async def test_download_media_success(self, client, tmp_path):
        """测试下载媒体文件成功"""
        # Mock下载响应
        mock_content = b'test image data'
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.headers = {
                'Content-Type': 'image/jpeg',
                'Content-Disposition': 'attachment; filename="test.jpg"'
            }
            mock_response.read = AsyncMock(return_value=mock_content)
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=False)
            
            save_path = str(tmp_path / 'test.jpg')
            result = await client.download_media(
                media_id='test_media_id',
                save_path=save_path
            )
            
            assert result is not None
            assert result['size'] == len(mock_content)
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, client):
        """测试获取用户信息成功"""
        mock_response = {
            'errcode': 0,
            'userid': 'test_user',
            'name': '测试用户',
            'department': [1, 2],
            'position': '经理',
            'mobile': '13800138000',
            'email': 'test@example.com',
            'avatar': 'https://example.com/avatar.jpg',
            'status': 1
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            user_info = await client.get_user_info('test_user')
            
            assert user_info.user_id == 'test_user'
            assert user_info.name == '测试用户'
            assert len(user_info.department) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """测试错误处理"""
        from channels.wecom.errors import WeComError
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = WeComAPIException(
                WeComError(
                    code=WeComErrorCode.ACCESS_TOKEN_INVALID.value,
                    message='access_token is invalid'
                )
            )
            
            with pytest.raises(WeComAPIException) as exc_info:
                await client.send_text_message('user', 'test')
            
            assert exc_info.value.code == WeComErrorCode.ACCESS_TOKEN_INVALID.value


@requires_credentials
class TestWeComAPIClientReal:
    """使用真实API调用的测试（需要凭证）"""
    
    @pytest.fixture
    async def client(self):
        """创建真实的API客户端"""
        corp_id = os.environ.get('WECOM_CORP_ID')
        secret = os.environ.get('WECOM_SECRET')
        agent_id = int(os.environ.get('WECOM_AGENT_ID', '0'))
        
        client = WeComAPIClient(corp_id, secret, agent_id)
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_real_get_access_token(self, client):
        """测试真实获取AccessToken"""
        token = await client.get_access_token()
        assert token is not None
        assert len(token) > 0
        print(f"获取到AccessToken: {token[:10]}...")


# ========== 测试说明 ==========

"""
运行测试：

1. 运行Mock测试（不需要真实凭证）：
   pytest tests/channels/wecom/test_wecom_api.py::TestWeComAPIClientMock -v

2. 运行真实API测试（需要凭证）：
   export WECOM_CORP_ID=your_corp_id
   export WECOM_SECRET=your_secret
   export WECOM_AGENT_ID=your_agent_id
   pytest tests/channels/wecom/test_wecom_api.py::TestWeComAPIClientReal -v

3. 运行所有测试：
   pytest tests/channels/wecom/test_wecom_api.py -v

注意：
- Mock测试使用unittest.mock模拟API响应，用于验证逻辑
- 真实API测试需要有效的企业微信凭证，用于验证API连通性
- 建议在CI/CD环境中只运行Mock测试
"""

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
