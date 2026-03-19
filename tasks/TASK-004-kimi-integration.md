# Task-004: KIMI 多模态集成

## 任务概述

**任务ID**: TASK-004  
**任务名称**: KIMI 多模态集成  
**优先级**: 🔴 最高  
**预计耗时**: 30-45分钟  
**依赖**: TASK-001 ✅ 已完成  
**负责团队**: Field AI Team（或 Field Core Team）

## 任务目标

集成 KIMI K2.5 多模态能力，实现：
1. KIMI API Tool 开发（文本生成 + 图片分析）
2. 照片智能分析功能（设备识别、隐患发现、规范检查）
3. 流式输出支持（提升用户体验）
4. 与 TASK-003 企业微信 Channel 集成

## 技术方案

基于当前 OpenCode 已配置的 KIMI API，开发调用封装。

### KIMI API 配置参考

```python
# 从环境变量或配置文件读取
KIMI_API_KEY="${KIMI_API_KEY}"  # 已由 OpenCode 平台配置
KIMI_BASE_URL="https://api.moonshot.cn/v1"
KIMI_MODEL="kimi-k2-5"  # 或其他指定模型
```

## 详细工作内容

### 1. KIMI API Tool

**接口设计**:
```python
class KIMITool:
    """KIMI K2.5 多模态 API 封装"""
    
    async def chat(
        self, 
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]
    
    async def analyze_image(
        self,
        image_url: str,  # 支持 MinIO URL
        prompt: str,
        analysis_type: str = "general"  # general/nameplate/safety/compliance
    ) -> Dict[str, Any]
    
    async def analyze_images_batch(
        self,
        image_urls: List[str],
        prompt: str,
        batch_size: int = 5
    ) -> List[Dict[str, Any]]
    
    async def generate_document(
        self,
        template_type: str,  # briefing/emergency/summary
        data: Dict[str, Any],
        photos: List[str] = None
    ) -> str  # Markdown/Word 内容
```

**图片分析 Prompt 设计**:

```python
ANALYSIS_PROMPTS = {
    "nameplate": """
    分析这张变压器铭牌照片，提取以下信息：
    - 型号
    - 容量 (kVA)
    - 电压等级 (kV)
    - 制造商
    - 生产日期
    
    以JSON格式返回：
    {"model": "...", "capacity": "...", "voltage": "...", "manufacturer": "...", "date": "..."}
    """,
    
    "safety": """
    分析这张配电房照片，识别安全隐患：
    - 是否有杂物堆积？
    - 是否有漏水迹象？
    - 设备状态是否正常？
    - 消防设施是否到位？
    
    返回：{"risks": [...], "severity": "high/medium/low", "suggestions": [...]}
    """,
    
    "compliance": """
    检查这张电力设施照片是否符合安全规范：
    - 安全标识是否清晰
    - 通道是否畅通
    - 设备间距是否合规
    - 接地是否规范
    
    返回：{"compliant": true/false, "violations": [...], "score": 0-100}
    """
}
```

### 2. 流式输出支持

**实现方案**:
```python
async def stream_chat(
    self,
    messages: List[Dict],
    callback: Callable[[str], None]  # 逐字回调
) -> None:
    """流式输出，实时推送到企业微信"""
    async for chunk in self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        stream=True
    ):
        if chunk.choices[0].delta.content:
            await callback(chunk.choices[0].delta.content)
```

**与企业微信集成**:
```python
# 在 WeCom Channel 中使用流式输出
async def send_streaming_response(
    self, 
    user_id: str, 
    generator: AsyncGenerator[str, None]
):
    """将 KIMI 流式输出推送到企业微信"""
    buffer = ""
    last_send = time.time()
    
    async for chunk in generator:
        buffer += chunk
        
        # 每2秒或缓冲区超过100字发送一次
        if time.time() - last_send > 2 or len(buffer) > 100:
            await self.send_text_message(user_id, buffer)
            buffer = ""
            last_send = time.time()
    
    # 发送剩余内容
    if buffer:
        await self.send_text_message(user_id, buffer)
```

### 3. 照片分析服务

**服务类设计**:
```python
class PhotoAnalysisService:
    """照片智能分析服务"""
    
    def __init__(self, kimi_tool: KIMITool):
        self.kimi = kimi_tool
    
    async def analyze_power_room(
        self, 
        photo_urls: List[str]
    ) -> Dict[str, Any]:
        """配电房照片分析"""
        results = []
        for url in photo_urls:
            result = await self.kimi.analyze_image(
                url, 
                ANALYSIS_PROMPTS["safety"]
            )
            results.append(result)
        
        # 汇总分析结果
        return self._aggregate_results(results)
    
    async def analyze_nameplate(
        self, 
        photo_url: str
    ) -> Dict[str, str]:
        """铭牌识别"""
        return await self.kimi.analyze_image(
            photo_url,
            ANALYSIS_PROMPTS["nameplate"]
        )
    
    async def check_compliance(
        self, 
        photo_urls: List[str]
    ) -> ComplianceReport:
        """规范检查"""
        violations = []
        for url in photo_urls:
            result = await self.kimi.analyze_image(
                url,
                ANALYSIS_PROMPTS["compliance"]
            )
            if not result.get("compliant"):
                violations.extend(result.get("violations", []))
        
        return ComplianceReport(violations=violations)
```

### 4. 与 Channel 集成

**在 Message Handler 中调用**:
```python
class MessageHandler:
    def __init__(self):
        self.kimi = KIMITool()
        self.photo_service = PhotoAnalysisService(self.kimi)
    
    async def handle_image(self, context: MessageContext):
        """处理用户发送的图片"""
        # 下载图片到 MinIO
        photo_url = await self.download_and_store(context.media_id)
        
        # 根据当前任务类型选择分析方式
        if context.session.current_task == "nameplate":
            result = await self.photo_service.analyze_nameplate(photo_url)
            reply = self.format_nameplate_result(result)
        elif context.session.current_task == "safety_check":
            result = await self.photo_service.analyze_power_room([photo_url])
            reply = self.format_safety_report(result)
        else:
            # 通用分析
            result = await self.kimi.analyze_image(photo_url, "描述这张图片")
            reply = result.get("description", "无法识别")
        
        await self.send_text_message(context.user_id, reply)
```

## 配置文件

```yaml
# config/kimi.yaml
kimi:
  api_key: "${KIMI_API_KEY}"
  base_url: "https://api.moonshot.cn/v1"
  model: "kimi-k2-5"
  
  # 请求配置
  timeout: 60
  max_retries: 3
  retry_interval: 1
  
  # 生成配置
  defaults:
    temperature: 0.7
    max_tokens: 2000
    top_p: 0.9
  
  # 流式输出
  streaming:
    enabled: true
    buffer_size: 100
    flush_interval: 2  # 秒
```

## 交付物

1. **KIMI Tool**: `src/tools/kimi_tool.py`
2. **照片分析服务**: `src/services/photo_analysis.py`
3. **配置文件**: `config/kimi.yaml`
4. **单元测试**: `tests/tools/test_kimi_tool.py`
5. **集成测试**: `tests/integration/test_photo_analysis.py`
6. **使用文档**: `docs/tools/kimi.md`

## 验收标准

- [ ] KIMI API Tool 可正常调用
- [ ] 图片分析功能可用（准确率 > 85%）
- [ ] 流式输出正常工作
- [ ] 与企业微信 Channel 集成成功
- [ ] 单元测试覆盖率 > 90%
- [ ] 文档完整

## 使用示例

```python
# 基本调用
from src.tools.kimi_tool import KIMITool

kimi = KIMITool()

# 文本生成
response = await kimi.chat([
    {"role": "system", "content": "你是电力专家"},
    {"role": "user", "content": "分析变压器过载的原因"}
])

# 图片分析
result = await kimi.analyze_image(
    "http://minio:9000/field-documents/photos/transformer.jpg",
    "识别铭牌信息"
)

# 流式输出
async for chunk in kimi.stream_chat(messages):
    print(chunk, end="")
```

## 相关文档

- [项目总览](../knowledge-base/field-info-agent/README.md)
- [详细设计](../knowledge-base/field-info-agent/design/detailed-design-v2.md)
- KIMI API 文档: https://platform.moonshot.cn/docs
- TASK-003 企业微信 Channel: [REPORT-003](../reports/REPORT-003-wecom-channel.md)

## 报告要求

完成后请提交报告到: `reports/REPORT-004-kimi-integration.md`

---

**创建时间**: 2026-03-17  
**更新**: 2026-03-19（更新为 KIMI 多模态方案）  
**负责团队**: Field AI Team（建议）或 Field Core Team  
**状态**: 待开始  
**依赖**: TASK-001 ✅ 完成，TASK-003 ✅ 完成
