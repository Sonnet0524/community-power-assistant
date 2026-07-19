---
skill_id: info-retrieval
name: 信息检索
version: 3.0.0
type: openclaw-skill
category: retrieval
priority: P1
---

# Info Retrieval Skill - 信息检索

> 🔍 基于纯文件系统的全文检索能力

## 一、功能定位

**核心能力**:
- 跨小区信息查询
- 历史记录检索
- 设备信息查询
- 客户信息查询
- 问题记录追踪

**检索范围**:
```
📁 field-data/
├── communities-index.md        ← 小区总览
├── search-index.md             ← 检索索引
└── 📁 {小区名}/
    ├── README.md               ← 小区档案
    └── 📁 {YYYY-MM}/
        └── work-record.md      ← 工作记录
```

## 二、触发方式

### 2.1 意图识别

```yaml
triggers:
  keywords:
    - "查询"
    - "搜索"
    - "查找"
    - "历史"
    - "记录"
    - "信息"
    
  patterns:
    - "{小区}.*信息"
    - "{设备}.*在哪里"
    - "{客户}.*住.*哪"
    - "{时间}.*问题"
    - "变压器.*{小区}"
    
  examples:
    - "查询阳光小区的信息"
    - "王大爷住在哪个小区"
    - "上个月发现了什么问题"
    - "锦绣花园的变压器型号"
    - "查找所有敏感客户"
```

### 2.2 查询类型分类

| 查询类型 | 示例 | 检索目标 |
|---------|------|----------|
| **小区查询** | "阳光小区地址" | 小区README.md |
| **设备查询** | "变压器信息" | 所有工作记录 |
| **客户查询** | "王大爷信息" | 敏感客户清单 |
| **问题查询** | "发现的问题" | 工作记录中的问题 |
| **历史查询** | "上次驻点" | communities-index.md |

## 三、检索实现

### 3.1 检索索引结构

**search-index.md**（自动生成）:

```markdown
# 检索索引

**生成时间**: 2024-03-17 15:30

## 小区索引

### 阳光小区
- **路径**: ./communities/阳光小区/
- **地址**: 武侯区xx路xx号
- **设备**: 变压器4台（SCB11-500/10 x2, SCB11-630/10 x2）
- **客户**: 王大爷(3-2-501), 张女士(4-1-302)
- **历史**: 2024-03-17, 2024-02-15

### 锦绣花园
- **路径**: ./communities/锦绣花园/
- **地址**: 武侯区yy路yy号
- **设备**: 变压器6台
- **客户**: 李奶奶(2-1-101)

## 问题索引

| 日期 | 小区 | 问题描述 | 严重程度 | 状态 |
|------|------|----------|----------|------|
| 2024-03-17 | 阳光小区 | 2#变压器油位偏低 | 一般 | 待复查 |
| 2024-03-15 | 锦绣花园 | 配电房照明损坏 | 轻微 | 已修复 |

## 客户索引

| 姓名 | 小区 | 房号 | 类型 | 电话 |
|------|------|------|------|------|
| 王大爷 | 阳光小区 | 3-2-501 | 独居老人 | 139****1234 |
| 张女士 | 阳光小区 | 4-1-302 | 孕妇 | 137****5678 |
| 李奶奶 | 锦绣花园 | 2-1-101 | 独居老人 | 138****9012 |
```

### 3.2 检索算法

```python
# 伪代码
class InfoRetrieval:
    def search(self, query: str) -> List[Result]:
        # 1. 解析查询意图
        intent = self.parse_intent(query)
        
        # 2. 加载索引
        index = self.load_index("search-index.md")
        
        # 3. 执行检索
        if intent.type == "小区查询":
            return self.search_community(intent.keywords)
        elif intent.type == "设备查询":
            return self.search_equipment(intent.keywords)
        elif intent.type == "客户查询":
            return self.search_customer(intent.keywords)
        elif intent.type == "问题查询":
            return self.search_issues(intent.keywords)
        
        # 4. 全文搜索
        return self.full_text_search(query)
    
    def search_community(self, name: str) -> dict:
        """查询小区信息"""
        readme_path = f"./communities/{name}/README.md"
        content = read_file(readme_path)
        return self.parse_community_info(content)
    
    def search_customer(self, name: str) -> List[dict]:
        """查询客户信息"""
        results = []
        for community in list_communities():
            readme = read_file(f"./communities/{community}/README.md")
            if name in readme:
                info = self.extract_customer_info(readme, name)
                results.append({
                    "小区": community,
                    **info
                })
        return results
    
    def search_issues(self, time_range: str = None) -> List[dict]:
        """查询问题记录"""
        issues = []
        for record_file in find_all("work-record.md"):
            content = read_file(record_file)
            issues.extend(self.extract_issues(content, record_file))
        return issues
    
    def full_text_search(self, query: str) -> List[dict]:
        """全文检索"""
        results = []
        for md_file in find_all("*.md"):
            content = read_file(md_file)
            if query in content:
                context = self.extract_context(content, query)
                results.append({
                    "文件": md_file,
                    "上下文": context
                })
        return results
```

### 3.3 索引更新机制

```yaml
更新时机:
  - 每次工作记录完成后
  - 每日凌晨定时更新
  - 手动触发更新

更新内容:
  - 小区列表
  - 设备信息汇总
  - 问题记录汇总
  - 客户信息汇总
```

## 四、响应格式

### 4.1 小区查询响应

```
用户: "查询阳光小区的信息"

Agent:
📋 阳光小区信息

**基本信息**
• 地址: 武侯区xx路xx号
• 总户数: 500户
• 配电房: 2个
• 变压器: 4台

**设备信息**
• 1号配电房（3号楼地下室）: 2台变压器
  - 1#变: SCB11-500/10，运行正常
  - 2#变: SCB11-630/10，⚠️ 油位偏低
• 2号配电房（5号楼一楼）: 2台变压器
  - 3#变: SCB11-500/10，运行正常
  - 4#变: SCB11-500/10，运行正常

**驻点历史**
• 2024-03-17: 配电房检查，发现问题1个
• 2024-02-15: 客户走访，走访2户
• 累计驻点: 3次

**敏感客户**
• 王大爷 3-2-501（独居老人）
• 张女士 4-1-302（孕妇）

[查看详细档案] [查看历史记录]
```

### 4.2 客户查询响应

```
用户: "王大爷住在哪个小区？"

Agent:
🔍 查询结果

王大爷住在 **阳光小区**
• 房号: 3-2-501
• 类型: 独居老人（70岁）
• 电话: 139****1234
• 上次走访: 2024-03-17
• 反馈: 近期电压稳定，无停电

**关联信息**
• 所属配电房: 1号配电房（3号楼地下室）
• 最近驻点: 2024-03-17，工作人员张三

[查看走访记录] [导航到地址]
```

### 4.3 问题查询响应

```
用户: "最近发现了什么问题？"

Agent:
⚠️ 近期问题记录（最近30天）

| 日期 | 小区 | 问题描述 | 严重程度 | 状态 |
|------|------|----------|----------|------|
| 03-17 | 阳光小区 | 2#变压器油位偏低 | 一般 | 待复查 |
| 03-15 | 锦绣花园 | 配电房照明损坏 | 轻微 | 已修复 |
| 03-10 | 金色家园 | 客户投诉停电频繁 | 重要 | 处理中 |

**问题统计**
• 总计: 3个问题
• 待处理: 2个
• 已解决: 1个

[查看详细记录]
```

## 五、与其他Skill协作

```
StationWorkGuide (驻点工作引导)
    ↓ 需要查询历史信息
InfoRetrieval (信息检索)
    ↓ 提供历史数据
StationWorkGuide
    ↓ 生成工作建议
用户
```

**协作示例**:
```
用户: "我要去阳光小区驻点"

Agent调用InfoRetrieval:
→ 查询阳光小区README.md
→ 获取设备信息、历史问题、敏感客户

Agent响应:
"🏠 阳光小区 - 驻点准备

📍 基本信息: 武侯区xx路xx号，500户

⚠️ 建议关注:
• 2#变压器油位偏低（上次发现，需复查）
• 王大爷（3-2-501）建议回访

📋 工作清单:
1. 检查2号配电房变压器油位
2. 走访王大爷、张女士
3. 拍摄配电房环境照片

是否开始记录？[开始]"
```

## 六、配置参数

```yaml
# openclaw.config.yaml
skills:
  info_retrieval:
    enabled: true
    priority: normal
    
    config:
      data_root: "./field-data"
      index_file: "search-index.md"
      auto_update: true
      update_interval: "0 2 * * *"  # 每天凌晨2点
      
    search:
      max_results: 10
      context_lines: 3
      fuzzy_match: true
      
    cache:
      enabled: true
      ttl: 300  # 5分钟
```

## 七、文件操作规范

### 7.1 读取文件

```typescript
// 使用OpenClaw文件工具
const content = await tools.read_file({
  file_path: "./field-data/communities/阳光小区/README.md"
});
```

### 7.2 更新索引

```typescript
// 更新search-index.md
async function updateSearchIndex() {
  const communities = await listCommunities();
  const index = {
    generated_at: new Date().toISOString(),
    communities: [],
    issues: [],
    customers: []
  };
  
  for (const community of communities) {
    const info = await parseCommunityInfo(community);
    index.communities.push(info);
  }
  
  await tools.write_file({
    file_path: "./field-data/search-index.md",
    content: generateIndexMarkdown(index)
  });
}
```

## 八、性能优化

### 8.1 索引策略

| 策略 | 说明 |
|------|------|
| **预生成索引** | 定期扫描生成search-index.md |
| **增量更新** | 仅更新变更的部分 |
| **分层索引** | 小区级、问题级、客户级 |

### 8.2 缓存策略

```yaml
缓存层级:
  - 内存缓存: 最近查询结果（5分钟）
  - 文件缓存: 索引文件（实时）
  - 原始数据: Markdown文件（源头）
```

---

**技能版本**: 3.0.0  
**适用Agent**: field-collector  
**依赖**: 无（纯文件操作）
