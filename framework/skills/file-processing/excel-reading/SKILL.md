---
skill: excel-reading
category: file-processing
version: 1.0.0
depends_on: [openpyxl, xlrd]
---

# Excel文件读取Skill

> 📊 读取和解析Excel文件，支持多种格式

---

## 📋 能力定义

读取Excel文件并转换为结构化数据，支持：
- **多格式支持**: xlsx, xlsm, xls, et (WPS表格)
- **结构化输出**: JSON格式数据结构
- **Markdown输出**: 转换为Markdown表格
- **灵活配置**: 指定工作表、行数限制

---

## 🎯 使用场景

- 数据导入和迁移
- 报表处理和分析
- 知识库建设
- 数据验证和清洗

---

## 🔧 支持格式

| 格式 | 说明 | 工具函数 |
|------|------|----------|
| `.xlsx` | Excel 2007+ | `read_xlsx` |
| `.xlsm` | Excel 2007+ (带宏) | `read_xlsx` |
| `.xls` | Excel 97-2003 | `read_xls` |
| `.et` | WPS 表格 | `read_et` |

---

## 🛠️ 使用方法

### 安装依赖

```bash
pip install openpyxl xlrd
```

### Python API调用

```python
import sys
sys.path.insert(0, r'framework/skills/file-processing/excel-reading')

from read_excel import read_excel, read_excel_as_markdown

# 读取为结构化数据
data = read_excel('data.xlsx')
print(data['file_info'])
print(data['sheets'][0]['data'])

# 读取为Markdown
md = read_excel_as_markdown('data.xlsx')
print(md)

# 指定工作表和最大行数
data = read_excel('data.xlsx', sheet_names=['Sheet1'], max_rows=100)
```

---

## 📤 返回数据结构

```python
{
    "file_info": {
        "file_path": "文件路径",
        "total_sheets": 工作表总数,
        "read_sheets": 实际读取数量,
        "format": ".xlsx"
    },
    "sheets": [
        {
            "name": "工作表名称",
            "rows": 行数,
            "columns": 列数,
            "data": [[单元格数据...], ...]
        }
    ]
}
```

---

## 📝 参数说明

### read_excel()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file_path` | str | 必需 | Excel文件路径 |
| `sheet_names` | List[str] | None | 指定工作表名称，None表示读取所有 |
| `max_rows` | int | None | 最大读取行数，None表示不限制 |

### read_excel_as_markdown()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `file_path` | str | 必需 | Excel文件路径 |
| `sheet_names` | List[str] | None | 指定工作表名称 |
| `max_rows` | int | None | 最大读取行数 |

---

## 💡 最佳实践

### 处理大文件

```python
# 限制行数，避免内存溢出
data = read_excel('large_file.xlsx', max_rows=1000)
```

### 读取特定工作表

```python
# 只读取需要的工作表
data = read_excel('data.xlsx', sheet_names=['Sheet1', 'Sheet2'])
```

### Markdown输出

```python
# 生成文档友好的Markdown表格
md = read_excel_as_markdown('data.xlsx')
with open('output.md', 'w', encoding='utf-8') as f:
    f.write(md)
```

---

## 📋 完整示例

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, r'framework/skills/file-processing/excel-reading')

from read_excel import read_excel, read_excel_as_markdown

# 读取Excel文件
data = read_excel('courses.xlsx')

# 打印文件信息
print(f"文件格式: {data['file_info']['format']}")
print(f"工作表数量: {data['file_info']['total_sheets']}")

# 打印每个工作表的数据
for sheet in data['sheets']:
    print(f"\n工作表: {sheet['name']}")
    print(f"行数: {sheet['rows']}, 列数: {sheet['columns']}")
    
    # 打印前5行数据
    for i, row in enumerate(sheet['data'][:5]):
        print(f"Row {i+1}: {row}")

# 转换为Markdown
md = read_excel_as_markdown('courses.xlsx')
print("\n=== Markdown输出 ===")
print(md[:500])
```

---

## ⚠️ 注意事项

1. **文件大小**: 大文件建议使用 `max_rows` 参数限制
2. **格式兼容**: xlrd库已停止维护xls格式，建议转换为xlsx
3. **编码问题**: 确保文件路径不含特殊字符
4. **内存占用**: 大量数据可能占用较多内存

---

## 📚 相关资源

- [openpyxl文档](https://openpyxl.readthedocs.io/)
- [xlrd文档](https://xlrd.readthedocs.io/)
- [Excel格式规范](https://docs.microsoft.com/en-us/office/open-xml/open-xml-sdk)

---

**版本**: 1.0.0  
**来源**: shared-tools  
**维护者**: Agent Team Template  
**最后更新**: 2026-03-10
