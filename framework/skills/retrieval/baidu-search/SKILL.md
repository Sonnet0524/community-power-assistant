---
skill: baidu-search
category: retrieval
version: 2.0.0
depends_on: [requests]
api_endpoint: https://qianfan.baidubce.com/v2/ai_search/web_search
standard_version: sgcc-quality-service-research
---

# 百度搜索Skill

> 🌐 通过百度千帆平台调用百度搜索API，获取实时全网信息

---

## 📋 能力定义

使用百度搜索API进行实时信息检索，支持：
- **网页搜索**：全网实时信息检索
- **多模态搜索**：网页、视频、图片、阿拉丁内容
- **高级过滤**：站点过滤、时效过滤、屏蔽站点
- **自动日志**：搜索记录、用量跟踪、质量监控

---

## ⚠️ 重要说明

**✅ 标准版本**: 本目录下的Python API实现

**❌ 不使用**: MCP协议版本（功能不完整，不推荐）

---

## 🎯 使用场景

- 需要获取最新的实时信息
- 需要搜索新闻、技术文档、教程等
- 需要在特定站点内搜索
- 需要按时间范围筛选结果
- 需要多模态搜索（网页、视频、图片）

---

## 🔧 API配置

### 安装依赖

```bash
pip install requests
```

### 配置API Key

**方式1: 环境变量**
```bash
export BAIDU_AISEARCH_TOKEN="your_api_key"
```

**方式2: 配置文件**

创建 `.env.local` 文件：
```
BAIDU_AISEARCH_TOKEN=your_api_key
```

---

## 🛠️ 使用方法

### Python API调用

```python
import sys
sys.path.insert(0, r'framework/skills/retrieval/baidu-search')

from baidu_web_search_api import BaiduWebSearch

# 创建客户端
client = BaiduWebSearch()

# 基础搜索
result = client.search(query="关键词")

# 多模态搜索
result = client.search(
    query="Python教程",
    resource_types=["web", "video", "image"],
    top_k=10
)

# 站点过滤
result = client.search(
    query="技术文档",
    site_filter=["docs.python.org"]
)

# 时效过滤
result = client.search(
    query="最新技术",
    recency_filter="month"
)
```

### 命令行调用

```bash
# 基础搜索
python framework/skills/retrieval/baidu-search/baidu_web_search_api.py --query "关键词"

# 指定结果数量
python framework/skills/retrieval/baidu-search/baidu_web_search_api.py --query "关键词" --top_k 10

# 多模态搜索
python framework/skills/retrieval/baidu-search/baidu_web_search_api.py \
  --query "Python教程" \
  --resource_types web video image

# 站点过滤
python framework/skills/retrieval/baidu-search/baidu_web_search_api.py \
  --query "天气预报" \
  --site www.weather.com.cn

# 时效过滤
python framework/skills/retrieval/baidu-search/baidu_web_search_api.py \
  --query "最新技术" \
  --recency month
```

---

## 📝 参数说明

### 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必需 | 搜索关键词 |
| `top_k` | int | 20 | 返回结果数量 |
| `resource_types` | List[str] | ["web"] | 资源类型：web/video/image/aladdin |
| `site_filter` | List[str] | None | 指定站点列表 |
| `recency_filter` | str | None | 时效：week/month/semiyear/year |
| `block_websites` | List[str] | None | 屏蔽站点列表 |
| `edition` | str | "standard" | 搜索版本：standard/lite |

---

## 📤 返回数据

### 成功响应

```python
{
    "success": True,
    "request_id": "xxx-xxx-xxx",
    "references": [
        {
            "id": 1,
            "title": "网页标题",
            "url": "https://example.com",
            "content": "网页内容片段...",
            "date": "2026-03-10 08:30:00",
            "type": "web",
            "rerank_score": 0.95
        }
    ],
    "response_time_ms": 1234,
    "result_count": 5
}
```

### 失败响应

```python
{
    "success": False,
    "error": "错误信息",
    "error_code": 401,
    "response_time_ms": 234
}
```

---

## 📊 监控与日志

### 自动日志记录

每次搜索自动记录到：
- `search-logs/YYYY-MM-DD.jsonl` - 每日搜索记录
- `search-logs/usage-stats.json` - 用量统计

### 日志内容

```json
{
  "timestamp": "2026-03-10T10:30:00.000Z",
  "call_id": "call-20260310-001",
  "query": "搜索关键词",
  "result_count": 5,
  "response_time_ms": 1234,
  "daily_total": 15,
  "remaining": 985
}
```

### 用量监控

- **免费额度**: 1000次/天
- **速率限制**: 3 QPS
- **超出计费**: 0.036元/次

---

## 💡 最佳实践

### 参数选择

| 场景 | 推荐配置 |
|------|---------|
| 新闻资讯 | resource_types=[web], recency=week |
| 技术文档 | resource_types=[web], edition=standard |
| 视频教程 | resource_types=[web, video] |
| 特定站点 | site_filter=["目标站点"] |
| 快速搜索 | edition=lite, top_k=5-10 |

### 查询构建

- ✅ 使用简洁明确的关键词
- ✅ 复杂查询拆分为多个简单查询
- ❌ 避免过于宽泛或模糊的词语

---

## 📚 相关资源

- [百度千帆控制台](https://console.bce.baidu.com/qianfan/)
- [百度搜索API文档](https://cloud.baidu.com/doc/AppBuilder/s/klv6eyrj9)
- [API Key获取](https://console.bce.baidu.com/qianfan/ais/console/onlineTest)

---

## 📋 完整示例

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, r'framework/skills/retrieval/baidu-search')

from baidu_web_search_api import BaiduWebSearch

# 创建客户端
client = BaiduWebSearch()

# 执行搜索
result = client.search(
    query="国家电网 优质服务举措",
    resource_types=["web"],
    top_k=10,
    recency_filter="month"
)

# 处理结果
if result["success"]:
    print(f"✅ 找到 {result['result_count']} 条结果")
    print(f"⏱️  响应时间: {result['response_time_ms']}ms")
    print()
    
    for ref in result["references"]:
        print(f"{ref['id']}. {ref['title']}")
        print(f"   URL: {ref['url']}")
        print(f"   日期: {ref['date']}")
        print(f"   内容: {ref['content'][:100]}...")
        print()
else:
    print(f"❌ 搜索失败: {result['error']}")
```

---

**版本**: 2.0.0  
**标准版本来源**: sgcc-quality-service-research  
**维护者**: Agent Team Template  
**最后更新**: 2026-03-10
