"""
Field Info Agent - KIMI K2.5 Tool

KIMI 多模态 API 封装，支持：
- 文本生成和对话
- 图片分析和理解
- 流式输出
- 文档生成

Usage:
    from src.tools.kimi_tool import KIMITool
    
    kimi = KIMITool()
    
    # 文本生成
    response = await kimi.chat([
        {"role": "user", "content": "你好"}
    ])
    
    # 图片分析
    result = await kimi.analyze_image(
        "http://minio:9000/photos/image.jpg",
        "描述这张图片"
    )
    
    # 流式输出
    async for chunk in kimi.stream_chat(messages):
        print(chunk, end="")
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from datetime import datetime
import aiohttp
from dataclasses import dataclass, field

from .base import BaseTool
from .errors import ToolError, ValidationError, ConnectionError
from .types import ToolStats


@dataclass
class KIMIConfig:
    """KIMI 配置"""
    api_key: str
    base_url: str = "https://api.kimi.com/coding/"
    model: str = "kimi-for-coding"
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2000


class KIMITool(BaseTool):
    """KIMI K2.5 多模态 Tool"""
    
    ANALYSIS_PROMPTS = {
        "nameplate": """
        分析这张变压器铭牌照片，提取以下信息并以JSON格式返回：
        {
            "model": "型号",
            "capacity": "容量(kVA)",
            "voltage": "电压等级(kV)",
            "manufacturer": "制造商",
            "date": "生产日期"
        }
        如果某项信息无法识别，值为null。
        """,
        
        "safety": """
        分析这张配电房照片，识别安全隐患。以JSON格式返回：
        {
            "risks": ["风险1", "风险2"],
            "severity": "high/medium/low",
            "suggestions": ["建议1", "建议2"]
        }
        """,
        
        "compliance": """
        检查这张电力设施照片是否符合安全规范。以JSON格式返回：
        {
            "compliant": true/false,
            "violations": ["违规项1"],
            "score": 0-100
        }
        """,
        
        "general": "请详细描述这张图片的内容，包括主要物体、场景和任何值得注意的细节。"
    }
    
    def __init__(self, config: Optional[KIMIConfig] = None):
        super().__init__()
        
        if config is None:
            # 从环境变量读取配置
            config = KIMIConfig(
                api_key=os.getenv("KIMI_API_KEY", ""),
                base_url=os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/"),
                model=os.getenv("KIMI_MODEL", "kimi-for-coding")
            )
        
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.config.api_key:
            raise ValidationError("KIMI_API_KEY not configured")
    
    async def connect(self) -> None:
        """初始化 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
            )
        self._connected = True
    
    async def close(self) -> None:
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._connected = False
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.connect()
            # 发送一个简单的请求检查连通性
            async with self._session.get(f"{self.config.base_url}/models") as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0-1)
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            完整响应字符串，或流式生成器
        """
        await self.connect()
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if stream:
                return self._stream_chat(payload)
            else:
                async with self._session.post(
                    f"{self.config.base_url}/chat/completions",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise ToolError(f"KIMI API error: {resp.status} - {error_text}")
                    
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # 记录操作
                    duration = (asyncio.get_event_loop().time() - start_time) * 1000
                    self._log_operation(
                        "chat",
                        {"messages_count": len(messages)},
                        True,
                        duration
                    )
                    
                    return content
        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            self._log_operation(
                "chat",
                {"messages_count": len(messages)},
                False,
                duration,
                str(e)
            )
            raise ConnectionError(f"KIMI chat failed: {e}")
    
    async def _stream_chat(
        self,
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        try:
            async with self._session.post(
                f"{self.config.base_url}/chat/completions",
                json=payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ToolError(f"KIMI API error: {resp.status} - {error_text}")
                
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise ConnectionError(f"KIMI stream failed: {e}")
    
    async def analyze_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        分析图片
        
        Args:
            image_url: 图片URL（支持MinIO等外部存储）
            prompt: 自定义提示词
            analysis_type: 分析类型 (general/nameplate/safety/compliance)
            
        Returns:
            分析结果字典
        """
        if prompt is None:
            prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS["general"])
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        try:
            response = await self.chat(messages)
            
            # 尝试解析JSON响应
            try:
                # 查找JSON块
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                else:
                    json_str = response
                
                result = json.loads(json_str.strip())
                result["raw_response"] = response
                return result
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始文本
                return {
                    "description": response,
                    "raw_response": response
                }
        except Exception as e:
            raise ToolError(f"Image analysis failed: {e}")
    
    async def analyze_images_batch(
        self,
        image_urls: List[str],
        prompt: str,
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量分析图片
        
        Args:
            image_urls: 图片URL列表
            prompt: 分析提示词
            batch_size: 批次大小
            
        Returns:
            分析结果列表
        """
        results = []
        
        for i in range(0, len(image_urls), batch_size):
            batch = image_urls[i:i+batch_size]
            
            # 并发处理
            tasks = [
                self.analyze_image(url, prompt)
                for url in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "url": url,
                        "error": str(result),
                        "success": False
                    })
                else:
                    result["url"] = url
                    result["success"] = True
                    results.append(result)
        
        return results
    
    async def generate_document(
        self,
        template_type: str,
        data: Dict[str, Any],
        photos: Optional[List[str]] = None
    ) -> str:
        """
        生成文档
        
        Args:
            template_type: 模板类型 (briefing/emergency/summary)
            data: 文档数据
            photos: 图片URL列表
            
        Returns:
            生成的文档内容（Markdown格式）
        """
        templates = {
            "briefing": "生成供电简报",
            "emergency": "生成应急指引",
            "summary": "生成工作总结"
        }
        
        template = templates.get(template_type, "生成文档")
        
        # 构建提示词
        prompt = f"""
        {template}
        
        数据：
        {json.dumps(data, ensure_ascii=False, indent=2)}
        
        要求：
        1. 使用正式、专业的语言
        2. 包含所有关键信息
        3. 结构清晰，使用Markdown格式
        4. 如有图片，请分析并整合到文档中
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        # 如果有图片，添加到消息中
        if photos:
            content = [{"type": "text", "text": prompt}]
            for photo_url in photos[:5]:  # 最多5张图片
                content.append({"type": "image_url", "image_url": {"url": photo_url}})
            messages[0]["content"] = content
        
        return await self.chat(messages)


# 便捷的流式输出函数
async def stream_to_string(generator: AsyncGenerator[str, None]) -> str:
    """将流式生成器转换为字符串"""
    result = []
    async for chunk in generator:
        result.append(chunk)
    return "".join(result)