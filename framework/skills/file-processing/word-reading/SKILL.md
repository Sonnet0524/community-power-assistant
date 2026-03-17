---
skill: word-reading
category: file-processing
version: 1.0.0
depends_on: [python-docx]
---

# Word文档读取Skill

> 📄 读取和解析Word文档，提取结构化内容

---

## 📋 能力定义

读取Word文档并转换为结构化数据，支持：
- **文档结构解析**: 标题、段落、列表、表格
- **结构化输出**: JSON格式数据结构
- **Markdown输出**: 转换为Markdown格式
- **元数据提取**: 文档属性信息

---

## 🎯 使用场景

- 文档处理和分析
- 制度文件解析
- 知识提取项目
- 内容管理系统

---

## 🔧 支持格式

| 格式 | 说明 | 工具函数 |
|------|------|----------|
| `.docx` | Word文档 | `read_docx` |

---

## 🛠️ 使用方法

### 安装依赖

```bash
pip install python-docx
```

### Python API调用

```python
import sys
sys.path.insert(0, r'framework/skills/file-processing/word-reading')

from read_docx import read_docx, read_docx_as_markdown

# 读取为结构化数据
data = read_docx('document.docx')
print(data['title'])
print(data['content'])

# 读取为Markdown
md = read_docx_as_markdown('document.docx')
print(md)
```

---

## 📤 返回数据结构

```python
{
    "file_info": {
        "file_path": "文件路径",
        "paragraphs_count": 段落数,
        "tables_count": 表格数
    },
    "title": "文档标题",
    "content": [
        {"type": "heading", "level": 1, "text": "标题文本"},
        {"type": "paragraph", "text": "段落文本"},
        {"type": "list", "text": "列表项"}
    ],
    "tables": [
        {
            "rows": 3,
            "columns": 2,
            "data": [["单元格1", "单元格2"], [...], [...]]
        }
    ]
}
```

---

## 📝 内容类型

| 类型 | 说明 | 字段 |
|------|------|------|
| `heading` | 标题 | level, text |
| `paragraph` | 段落 | text |
| `list` | 列表项 | text |

---

## 💡 最佳实践

### 提取标题

```python
# 提取所有标题
for item in data['content']:
    if item['type'] == 'heading':
        print(f"H{item['level']}: {item['text']}")
```

### 提取表格

```python
# 处理表格数据
for table in data['tables']:
    print(f"表格: {table['rows']}行 x {table['columns']}列")
    for row in table['data']:
        print(row)
```

### Markdown输出

```python
# 生成文档友好的Markdown
md = read_docx_as_markdown('document.docx')
with open('output.md', 'w', encoding='utf-8') as f:
    f.write(md)
```

---

## 📋 完整示例

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, r'framework/skills/file-processing/word-reading')

from read_docx import read_docx, read_docx_as_markdown

# 读取Word文档
data = read_docx('培训管理实务手册.docx')

# 打印文件信息
print(f"文档标题: {data['title']}")
print(f"段落数: {data['file_info']['paragraphs_count']}")
print(f"表格数: {data['file_info']['tables_count']}")

# 打印文档结构
print("\n=== 文档结构 ===")
for i, item in enumerate(data['content'][:10]):
    if item['type'] == 'heading':
        print(f"{item['level']}. {item['text']}")
    elif item['type'] == 'paragraph':
        print(f"   段落: {item['text'][:50]}...")

# 处理表格
if data['tables']:
    print("\n=== 第一个表格 ===")
    table = data['tables'][0]
    for row in table['data'][:3]:
        print(row)

# 转换为Markdown
md = read_docx_as_markdown('培训管理实务手册.docx')
print("\n=== Markdown输出 ===")
print(md[:500])
```

---

## ⚠️ 注意事项

1. **文件格式**: 仅支持.docx格式，不支持.doc
2. **复杂格式**: 部分复杂格式可能丢失
3. **编码问题**: 确保文件路径不含特殊字符
4. **大文件**: 大量内容可能占用较多内存

---

## 📚 相关资源

- [python-docx文档](https://python-docx.readthedocs.io/)
- [Word格式规范](https://docs.microsoft.com/en-us/office/open-xml/open-xml-sdk)

---

**版本**: 1.0.0  
**来源**: shared-tools  
**维护者**: Agent Team Template  
**最后更新**: 2026-03-10
