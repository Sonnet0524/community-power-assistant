# Field Info Agent - OpenClaw 标准架构指南

> 🏗️ 基于OpenClaw框架的标准化架构设计

**版本**: 1.0.0  
**框架**: OpenClaw / 同类产品  
**架构层级**: L3 - 应用层Agent

---

## 一、OpenClaw 架构核心原则

### 1.1 架构边界定义

```
┌────────────────────────────────────────────────────────────────────┐
│                         OpenClaw Framework                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   Channel    │  │   Session    │  │        Skills Router     │ │
│  │   企业微信    │  │   Manager    │  │                          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│           │                │                        │              │
│           └────────────────┴────────────────────────┘              │
│                              │                                      │
│  ╔═══════════════════════════▼═══════════════════════════╗          │
│  ║  FIELD INFO AGENT - 应用层实现                         ║          │
│  ║  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  ║          │
│  ║  │  AGENTS    │ │  SKILLS    │ │   Scripts        │  ║          │
│  ║  │  角色定义  │ │  能力封装  │ │   自动化脚本     │  ║          │
│  ║  └────────────┘ └────────────┘ └──────────────────┘  ║          │
│  ╚═══════════════════════════════════════════════════════╝          │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────┐         │
│  │               Tools & External Services                │         │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │         │
│  │  │ MCP      │ │ API      │ │ Scripts  │ │ Native   │ │         │
│  │  │ Tools    │ │ Clients  │ │ Execution│ │ File I/O │ │         │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │         │
│  └───────────────────────────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────┘
```

**核心原则**:

```yaml
原则1: OpenClaw框架不可修改
  - Channel层: 由OpenClaw管理（企业微信、钉钉等）
  - Session层: 由OpenClaw管理（状态、上下文）
  - Router: 由OpenClaw管理（Skill分发）

原则2: 应用层可修改范围
  ✅ AGENTS: 角色定义、系统提示词、工作流
  ✅ SKILLS: 能力封装、业务逻辑
  ✅ Scripts: 自动化脚本、数据处理
  
原则3: 外部能力接入方式
  ✅ MCP Tools: 标准化的工具调用
  ✅ API Clients: HTTP/GRPC接口封装
  ✅ Scripts: 本地脚本执行
  ✅ Native Tools: OpenClaw内置工具（文件读写等）

原则4: 禁止直接修改
  ❌ OpenClaw核心代码
  ❌ Channel实现
  ❌ Session存储机制
  ❌ Skill路由逻辑
```

---

## 二、AGENTS 层设计

### 2.1 Agent角色定义

**文件**: `agents/field-collector/AGENTS.md`

```markdown
---
name: field-collector
description: |
  现场信息收集智能体 - 供电所驻点工作人员的AI助手
  
  基于OpenClaw框架，通过企业微信提供自然语言交互服务。
  
  核心职责：
  1. 驻点工作引导（配电房检查、客户走访、应急采集）
  2. 照片智能分析（设备识别、缺陷检测）
  3. 文档自动生成（工作记录、供电简报）
  4. 信息检索查询（历史记录、设备台账）

type: openclaw-agent
version: "3.0.0"

metadata:
  openclaw:
    channels:
      - wecom
    supported_message_types:
      - text
      - image
      - location
    
    # Agent级系统提示词
    system_prompt: |
      你是供电所现场工作人员的AI助手，专门协助完成驻点工作。
      
      ## 工作原则
      1. 使用简洁、专业的语言
      2. 主动引导工作流程
      3. 准确记录现场信息
      4. 及时提醒重要事项
      
      ## 可用工具
      {{skills}}
      
      ## 数据存储
      所有数据存储在本地文件系统中，路径: {{data_root}}
      
    # 工作流定义
    workflow:
      states:
        - idle
        - preparing
        - collecting
        - analyzing
        - completed
        
      transitions:
        - from: idle
          to: preparing
          trigger: start_intent
          
        - from: preparing
          to: collecting
          trigger: confirm_start
          
        - from: collecting
          to: analyzing
          trigger: complete_collection
          
        - from: analyzing
          to: completed
          trigger: generate_docs
```

### 2.2 Agent工作流（OpenClaw标准）

```yaml
workflow:
  # 状态定义
  states:
    idle:
      description: "空闲状态，等待用户指令"
      on_enter: "show_welcome_message"
      
    preparing:
      description: "准备阶段，加载小区信息"
      on_enter: "load_community_info"
      
    collecting:
      description: "采集阶段，收集现场数据"
      sub_states:
        - power_room
        - customer_visit
        - emergency
      
    analyzing:
      description: "分析阶段，处理采集数据"
      actions:
        - "analyze_photos"
        - "generate_summary"
        
    completed:
      description: "完成阶段，生成文档"
      actions:
        - "generate_documents"
        - "update_index"

  # 状态转换
  transitions:
    - name: "start_work"
      from: idle
      to: preparing
      condition: "intent == 'start_station_work'"
      actions:
        - "validate_community"
        - "create_session"
        
    - name: "begin_collection"
      from: preparing
      to: collecting
      condition: "user_confirmed"
      actions:
        - "initialize_collection"
        - "send_work_list"
```

---

## 三、SKILLS 层设计

### 3.1 Skill标准结构

**文件**: `skills/{skill-name}/SKILL.md`

```markdown
---
skill_id: station-work-guide
name: 驻点工作引导
description: |
  引导现场人员完成驻点工作的全流程信息采集。
  包括：意图识别、工作清单生成、进度追踪。

type: openclaw-skill
category: workflow
version: "3.0.0"

# OpenClaw集成配置
openclaw:
  # 触发条件
  triggers:
    - type: intent
      patterns:
        - "驻点"
        - "去.*社区"
        - "开始.*工作"
      confidence_threshold: 0.7
      
    - type: command
      pattern: "/start"
      
    - type: message_type
      value: "text"
      
  # 依赖检查
  requires:
    - tool: file_system
      description: "读写本地文件"
    - tool: session_storage
      description: "访问会话数据"
      
  # 权限声明
  permissions:
    - read: "field-data/communities/*"
    - write: "field-data/communities/*"
    
  # 配置参数
  config:
    data_root: "./field-data"
    template_path: "./templates"
    max_photos_per_session: 50
    
  # 错误处理
  error_handling:
    retry_count: 3
    fallback_action: "notify_user"
---

# Skill实现说明

## 输入
- user_message: 用户输入文本
- session_data: 当前会话数据
- community_id: 小区ID（可选）

## 输出
- response: 回复消息
- actions: 执行的动作列表
- state_update: 状态更新

## 工具调用

### 1. 文件读取（Native Tool）
```javascript
const communityInfo = await tools.read_file({
  path: `field-data/communities/${communityId}/README.md`
});
```

### 2. 文件写入（Native Tool）
```javascript
await tools.write_file({
  path: `field-data/communities/${communityId}/2024-03/work-record.md`,
  content: workRecordContent
});
```

### 3. Session更新（Native Tool）
```javascript
await tools.update_session({
  session_id: sessionId,
  data: {
    phase: 'power_room',
    progress: 50
  }
});
```

### 4. 外部API调用（API Client）
```javascript
// 如果配置了外部AI服务
const analysis = await tools.call_api({
  endpoint: "${AI_SERVICE_URL}/analyze",
  method: "POST",
  body: {
    image: imageData,
    type: "power_room"
  }
});
```

### 5. MCP工具调用（MCP Server）
```javascript
// 如果有MCP服务器提供数据库能力
const result = await tools.mcp_call({
  server: "postgres-mcp",
  tool: "query",
  args: {
    sql: "SELECT * FROM communities WHERE id = $1",
    params: [communityId]
  }
});
```
```

### 3.2 Skill分类

```yaml
Skill分类:
  
  工作流类:
    - station-work-guide      # 驻点工作引导
    - photo-collection        # 照片采集
    
  生成类:
    - doc-generation          # 文档生成
    - report-generation       # 报告生成
    
  检索类:
    - info-retrieval          # 信息检索
    - knowledge-query         # 知识查询
    
  工具类:
    - file-manager            # 文件管理
    - image-processor         # 图片处理
```

---

## 四、Scripts 层设计

### 4.1 Scripts角色定位

```yaml
Scripts职责:
  1. 数据迁移和转换
  2. 批量处理任务
  3. 定时任务执行
  4. 数据备份和恢复
  5. 索引重建和优化

Scripts执行方式:
  - 被Skills调用（tools.run_script）
  - 定时任务（cron）
  - 手动执行（CLI）
```

### 4.2 Scripts示例

**文件**: `scripts/migrate-v3-to-v4.py`

```python
#!/usr/bin/env python3
"""
数据迁移脚本：v3.0文件格式 → v4.0数据库格式

使用方式：
1. Skill调用：await tools.run_script("migrate-v3-to-v4", args)
2. 手动执行：python scripts/migrate-v3-to-v4.py --source ./field-data
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime

# 被Skill调用时的入口
def main(args):
    """Script入口函数"""
    source_path = args.get('source_path', './field-data')
    target_config = args.get('target_config', {})
    
    migrator = V3ToV4Migrator(source_path, target_config)
    result = migrator.migrate()
    
    return {
        "success": True,
        "migrated_count": result['count'],
        "errors": result['errors']
    }

class V3ToV4Migrator:
    def __init__(self, source_path, target_config):
        self.source = Path(source_path)
        self.target_config = target_config
        
    def migrate(self):
        """执行迁移"""
        results = {
            'count': 0,
            'errors': []
        }
        
        # 1. 读取所有小区
        communities = self._load_communities()
        
        for community in communities:
            try:
                # 2. 迁移小区数据
                self._migrate_community(community)
                results['count'] += 1
            except Exception as e:
                results['errors'].append({
                    'community': community['name'],
                    'error': str(e)
                })
                
        return results
        
    def _load_communities(self):
        """从索引文件加载小区列表"""
        index_file = self.source / "communities-index.md"
        # 解析Markdown表格...
        return communities
        
    def _migrate_community(self, community):
        """迁移单个小区"""
        # 读取README.md
        # 解析工作记录
        # 写入数据库或新格式
        pass

# 手动执行入口
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="./field-data")
    parser.add_argument("--target", default="./field-data-v4")
    args = parser.parse_args()
    
    result = main({
        'source_path': args.source,
        'target_path': args.target
    })
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 4.3 Scripts工具封装

```javascript
// Skill中调用Script
async function migrateData(session, tools) {
  const result = await tools.run_script({
    script: "migrate-v3-to-v4",
    args: {
      source_path: "./field-data",
      target_config: {
        db_host: "localhost",
        db_port: 5432
      }
    },
    timeout: 300  // 5分钟超时
  });
  
  if (result.success) {
    return `迁移完成，共迁移 ${result.migrated_count} 个小区`;
  } else {
    return `迁移失败：${result.errors[0].error}`;
  }
}
```

---

## 五、Tools 接入规范

### 5.1 工具类型矩阵

| 工具类型 | 适用场景 | 示例 | 调用方式 |
|---------|---------|------|---------|
| **Native** | OpenClaw内置能力 | read_file, write_file, session_update | `tools.{name}()` |
| **MCP** | 标准化外部工具 | PostgreSQL, MinIO, Elasticsearch | `tools.mcp_call()` |
| **API** | HTTP接口 | KIMI API, 百度API, 企业微信API | `tools.http_request()` |
| **Script** | 复杂本地逻辑 | 数据迁移、批量处理 | `tools.run_script()` |

### 5.2 MCP工具接入

**MCP Server定义**: `mcp-servers/postgres-mcp.yaml`

```yaml
name: postgres-mcp
description: PostgreSQL数据库MCP服务器
version: "1.0.0"

tools:
  - name: query
    description: 执行SQL查询
    parameters:
      - name: sql
        type: string
        required: true
      - name: params
        type: array
        required: false
        
  - name: insert
    description: 插入数据
    parameters:
      - name: table
        type: string
        required: true
      - name: data
        type: object
        required: true
        
  - name: update
    description: 更新数据
    parameters:
      - name: table
        type: string
        required: true
      - name: data
        type: object
        required: true
      - name: where
        type: string
        required: true

config:
  connection:
    host: "${DB_HOST}"
    port: 5432
    database: "field_agent"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

**Skill中调用**:

```javascript
// 方式1: 直接SQL查询（通过MCP）
const result = await tools.mcp_call({
  server: "postgres-mcp",
  tool: "query",
  args: {
    sql: "SELECT * FROM communities WHERE id = $1",
    params: [communityId]
  }
});

// 方式2: 封装为Skill内部函数
async function getCommunityInfo(communityId) {
  return await tools.mcp_call({
    server: "postgres-mcp",
    tool: "query",
    args: {
      sql: "SELECT * FROM communities WHERE id = $1",
      params: [communityId]
    }
  });
}
```

### 5.3 API Client接入

**API定义**: `api-clients/kimi-client.yaml`

```yaml
name: kimi-client
description: KIMI AI API客户端
version: "1.0.0"

base_url: "https://api.moonshot.cn/v1"
auth:
  type: bearer
  token: "${KIMI_API_KEY}"

endpoints:
  - name: chat
    path: "/chat/completions"
    method: POST
    description: 文本生成
    
  - name: vision
    path: "/chat/completions"
    method: POST
    description: 图片分析
    headers:
      Content-Type: "application/json"
```

**Skill中调用**:

```javascript
// 调用KIMI API
const response = await tools.http_request({
  client: "kimi-client",
  endpoint: "vision",
  body: {
    model: "kimi-v1",
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: "分析这张配电房照片" },
          { type: "image_url", image_url: { url: imageUrl } }
        ]
      }
    ]
  }
});
```

---

## 六、数据流向

### 6.1 标准数据流

```
用户输入（企业微信）
    ↓
OpenClaw Channel
    ↓
OpenClaw Session Manager（更新会话状态）
    ↓
OpenClaw Skills Router（路由到对应Skill）
    ↓
╔═══════════════════════════════════════════╗
║  SKILL 执行                               ║
║  1. 读取输入参数（from Session）          ║
║  2. 执行业务逻辑                          ║
║  3. 调用Tools（Native/MCP/API/Script）    ║
║  4. 生成响应                              ║
╚═══════════════════════════════════════════╝
    ↓
返回给用户（通过OpenClaw Channel）
```

### 6.2 照片采集数据流

```
用户发送照片
    ↓
Channel接收 → Session Manager更新
    ↓
Skills Router → photo-collection Skill
    ↓
Skill执行:
  ├─ 1. 获取图片数据（from Session）
  ├─ 2. tools.save_file() → 保存到本地
  ├─ 3. tools.mcp_call() → 可选：MCP分析
  ├─ 4. tools.http_request() → 可选：API分析
  ├─ 5. tools.read_file() → 读取工作记录模板
  ├─ 6. tools.write_file() → 更新工作记录
  └─ 7. tools.update_session() → 更新会话进度
    ↓
生成响应："照片已保存并分析：[结果摘要]"
```

---

## 七、目录结构规范

### 7.1 标准目录结构

```
field-info-agent/                      # 项目根目录
│
├── agents/                            # AGENTS层
│   └── field-collector/
│       ├── AGENTS.md                  # Agent角色定义 ⭐
│       └── config.yaml                # Agent配置
│
├── skills/                            # SKILLS层
│   ├── station-work-guide/
│   │   └── SKILL.md                   # Skill定义 ⭐
│   ├── photo-collection/
│   │   └── SKILL.md                   # Skill定义 ⭐
│   ├── doc-generation/
│   │   └── SKILL.md                   # Skill定义 ⭐
│   └── info-retrieval/
│       └── SKILL.md                   # Skill定义 ⭐
│
├── scripts/                           # SCRIPTS层
│   ├── migrate-v3-to-v4.py            # 数据迁移
│   ├── build-search-index.py          # 索引构建
│   └── backup-data.sh                 # 数据备份
│
├── tools/                             # TOOLS配置
│   ├── mcp-servers/                   # MCP服务器配置
│   │   ├── postgres-mcp.yaml
│   │   └── minio-mcp.yaml
│   └── api-clients/                   # API客户端配置
│       ├── kimi-client.yaml
│       └── wecom-client.yaml
│
├── templates/                         # 文档模板
│   ├── markdown/
│   │   ├── work-record-template.md
│   │   └── power-briefing-template.md
│   └── word/
│       └── work-record-template.docx
│
├── data/                              # 数据目录（可选）
│   └── communities/                   # 小区数据
│
└── docs/                              # 文档
    ├── ARCHITECTURE.md                # 架构说明
    └── DEPLOYMENT.md                  # 部署指南
```

### 7.2 OpenClaw配置目录

```
.opencode/                             # OpenClaw配置（标准位置）
├── config.yaml                        # 主配置
├── agents/
│   └── field-collector.yaml           # Agent注册
├── skills/
│   ├── station-work-guide.yaml        # Skill注册
│   ├── photo-collection.yaml
│   └── ...
└── tools/
    ├── mcp-servers.yaml               # MCP服务器注册
    └── api-clients.yaml               # API客户端注册
```

---

## 八、配置示例

### 8.1 OpenClaw主配置

```yaml
# .opencode/config.yaml
version: "1.0.0"
name: "Field Info Agent"

# Agent注册
agents:
  field-collector:
    path: "./agents/field-collector/AGENTS.md"
    enabled: true
    default: true

# Skills注册
skills:
  station-work-guide:
    path: "./skills/station-work-guide/SKILL.md"
    enabled: true
    
  photo-collection:
    path: "./skills/photo-collection/SKILL.md"
    enabled: true
    
  doc-generation:
    path: "./skills/doc-generation/SKILL.md"
    enabled: true
    
  info-retrieval:
    path: "./skills/info-retrieval/SKILL.md"
    enabled: true

# Channel配置
channels:
  wecom:
    enabled: true
    corp_id: "${WECOM_CORP_ID}"
    agent_id: "${WECOM_AGENT_ID}"
    secret: "${WECOM_SECRET}"

# Session配置
session:
  storage: "memory"  # memory | redis | file
  timeout: 7200

# Tools配置
tools:
  # Native工具（内置）
  native:
    enabled: true
    
  # MCP服务器
  mcp:
    enabled: false  # v3.0不启用，v4.0启用
    servers:
      - path: "./tools/mcp-servers/postgres-mcp.yaml"
        enabled: false
        
  # API客户端
  api:
    enabled: false  # v3.0不启用，v4.0启用
    clients:
      - path: "./tools/api-clients/kimi-client.yaml"
        enabled: false
```

### 8.2 v3.0配置（极简版）

```yaml
# v3.0使用纯Native工具
skills:
  station-work-guide:
    enabled: true
    config:
      data_root: "./field-data"
      storage_type: "file"  # 仅文件存储
      
  photo-collection:
    enabled: true
    config:
      use_openclaw_vision: true  # 使用OpenClaw内置读图
      save_to_local: true
      
tools:
  native:
    enabled: true  # 只使用Native工具
  mcp:
    enabled: false  # 不启用MCP
  api:
    enabled: false  # 不启用外部API
```

### 8.3 v4.0配置（企业版）

```yaml
# v4.0启用全部能力
skills:
  station-work-guide:
    enabled: true
    config:
      storage_type: "postgresql"  # 数据库存储
      
  photo-collection:
    enabled: true
    config:
      use_openclaw_vision: false  # 使用外部AI
      ai_service: "kimi"  # 使用KIMI
      
tools:
  native:
    enabled: true
  mcp:
    enabled: true  # 启用MCP
    servers:
      postgres-mcp:
        enabled: true
        config:
          host: "${DB_HOST}"
      minio-mcp:
        enabled: true
        config:
          endpoint: "${MINIO_ENDPOINT}"
  api:
    enabled: true  # 启用API
    clients:
      kimi-client:
        enabled: true
        api_key: "${KIMI_API_KEY}"
```

---

## 九、最佳实践

### 9.1 Skill设计原则

```yaml
1. 单一职责:
   ❌ 一个Skill做太多事
   ✅ 一个Skill = 一个明确的能力
   
2. 工具无关:
   ❌ Skill直接调用特定数据库
   ✅ Skill通过Tools抽象层调用
   
3. 配置驱动:
   ❌ Skill内部硬编码路径
   ✅ 从config读取配置
   
4. 错误处理:
   ❌ 忽略错误
   ✅ 明确错误处理和降级策略
   
5. 幂等性:
   ❌ 重复执行产生不同结果
   ✅ 重复执行结果一致
```

### 9.2 工具选择决策树

```
需要操作本地文件？
├─ 是 → 使用 Native Tool（read_file/write_file）
└─ 否 →

需要调用外部HTTP服务？
├─ 是 → 使用 API Client
└─ 否 →

需要标准化工具接口？
├─ 是 → 使用 MCP Tool
└─ 否 →

需要复杂本地逻辑？
├─ 是 → 使用 Script
└─ 否 → 重新评估需求
```

---

## 十、总结

### 10.1 架构核心

```
OpenClaw框架（不可修改）
    ↓
AGENTS（角色定义）
    ↓
SKILLS（能力封装）
    ↓
TOOLS（外部能力接入）
    ├─ Native（OpenClaw内置）
    ├─ MCP（标准化工具）
    ├─ API（HTTP接口）
    └─ Scripts（本地脚本）
```

### 10.2 版本演进

```
v3.0: 仅使用Native Tools
  ├── 文件读写
  ├── Session管理
  └── OpenClaw内置AI

v4.0: 启用MCP + API
  ├── Native Tools
  ├── MCP Tools（PostgreSQL, MinIO）
  └── API Clients（KIMI, 百度）
```

### 10.3 关键要点

1. **OpenClaw是框架**：提供Channel、Session、Router能力
2. **AGENTS定义角色**：系统提示词、工作流
3. **SKILLS封装业务**：通过TOOLS完成具体任务
4. **TOOLS提供能力**：Native/MCP/API/Scripts四种方式
5. **配置驱动一切**：零代码切换工具实现

---

**文档版本**: 1.0.0  
**最后更新**: 2024-03-25  
**维护者**: PM Agent
