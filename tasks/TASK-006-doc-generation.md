# Task-006: DocGeneration Skill 开发

## 任务概述

**任务ID**: TASK-006  
**任务名称**: DocGeneration Skill（文档自动生成）  
**优先级**: 🔴 最高  
**预计耗时**: 40-60分钟  
**依赖**: TASK-002 ✅, TASK-004 ✅  
**负责团队**: Field Core Team

## 任务目标

开发文档自动生成 Skill，根据采集的数据自动生成：
1. 供电简报（Word格式）
2. 应急指引文档
3. 工作总结报告

## Skill设计

### Skill定义

```yaml
skill:
  name: doc_generation
  description: 文档自动生成Skill，根据数据生成供电简报/应急指引/工作总结
  version: 1.0.0
  
  input:
    - task_id: str              # 任务ID
    - doc_type: str             # 文档类型
    - data: dict                # 采集的数据
    - photos: list              # 照片URL列表
    
  output:
    - document_url: str         # 文档下载URL
    - preview: str              # 文档预览（Markdown）
    - share_link: str           # 分享链接
```

### 文档模板

```python
DOC_TEMPLATES = {
    "briefing": {
        "name": "供电简报",
        "file_name": "{date}_{station}_供电简报.docx",
        "sections": [
            "工作概述",
            "现场情况",
            "设备状态",
            "发现问题",
            "整改建议",
            "附件（照片）"
        ]
    },
    "emergency": {
        "name": "应急指引", 
        "file_name": "{date}_{location}_应急指引.docx",
        "sections": [
            "事件概述",
            "影响范围",
            "应急措施",
            "恢复方案",
            "注意事项"
        ]
    },
    "summary": {
        "name": "工作总结",
        "file_name": "{date}_{period}_工作总结.docx",
        "sections": [
            "工作回顾",
            "完成情况",
            "问题分析",
            "改进措施",
            "下阶段计划"
        ]
    }
}
```

## 详细工作内容

### 1. Skill 主类

**文件**: `src/skills/doc_generation/skill.py`

```python
class DocGenerationSkill(BaseSkill):
    """文档自动生成 Skill"""
    
    NAME = "doc_generation"
    DESCRIPTION = "根据采集数据自动生成文档"
    
    def __init__(self):
        super().__init__()
        self.kimi = KIMITool()
        self.minio = MinIOTool()
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """生成文档"""
        doc_type = context.params.get("doc_type", "briefing")
        task_id = context.params.get("task_id")
        
        # 从数据库获取任务数据
        task_data = await self._get_task_data(task_id)
        
        # 生成文档内容
        doc_content = await self._generate_document(doc_type, task_data)
        
        # 保存为Word文件
        doc_url = await self._save_as_word(doc_content, doc_type, task_data)
        
        return SkillResult(
            response=f"✅ 文档已生成\n{doc_content['preview']}",
            data={
                "document_url": doc_url,
                "share_link": await self._create_share_link(doc_url)
            }
        )
```

### 2. 内容生成

```python
async def _generate_content(
    self,
    doc_type: str,
    task_data: dict
) -> dict:
    """使用KIMI生成文档内容"""
    
    template_prompts = {
        "briefing": """
        根据以下数据生成供电简报：
        
        基本信息：
        - 供电所：{station}
        - 日期：{date}
        - 工作人员：{staff}
        - 工作地点：{location}
        
        采集数据：
        {collection_data}
        
        生成结构化的简报内容，包括：
        1. 工作概述（2-3句话）
        2. 现场情况描述
        3. 设备状态汇总
        4. 发现的问题列表
        5. 整改建议
        
        以JSON格式返回各个章节的内容。
        """,
        
        "emergency": """
        根据以下应急信息生成应急指引：
        
        事件：{event_type}
        地点：{location}
        时间：{time}
        影响：{impact}
        现状：{current_status}
        
        生成应急指引，包括：
        1. 事件概述
        2. 影响范围评估
        3. 即时应急措施
        4. 恢复供电方案
        5. 安全注意事项
        """,
        
        "summary": """
        根据以下数据生成工作总结：
        
        周期：{period}
        完成工作：{completed_tasks}
        发现问题：{issues}
        客户反馈：{feedback}
        
        生成工作总结，包括：
        1. 工作回顾
        2. 完成情况统计
        3. 问题分析
        4. 改进措施
        5. 下阶段计划
        """
    }
    
    prompt = template_prompts[doc_type].format(**task_data)
    
    # 调用KIMI生成
    response = await self.kimi.chat([
        {"role": "system", "content": "你是专业的电力行业文档撰写专家"},
        {"role": "user", "content": prompt}
    ])
    
    return self._parse_generated_content(response)
```

### 3. Word文档生成

```python
async def _create_word_document(
    self,
    content: dict,
    template_type: str,
    output_path: str
):
    """创建Word文档"""
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    
    # 标题
    title = doc.add_heading(content["title"], 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 元信息
    doc.add_paragraph(f"生成时间：{content['generated_at']}")
    doc.add_paragraph(f"生成人：{content['generated_by']}")
    
    # 各个章节
    for section in DOC_TEMPLATES[template_type]["sections"]:
        doc.add_heading(section, level=1)
        
        section_content = content.get("sections", {}).get(section, "")
        doc.add_paragraph(section_content)
        
        # 添加相关照片
        if section == "附件（照片）":
            for photo in content.get("photos", []):
                doc.add_picture(photo, width=Inches(5.0))
    
    # 保存
    doc.save(output_path)
    
    # 上传到MinIO
    minio_url = await self.minio.upload_file(
        output_path,
        f"generated-docs/{template_type}/{os.path.basename(output_path)}"
    )
    
    return minio_url
```

### 4. 文档预览

```python
def _generate_preview(self, content: dict) -> str:
    """生成Markdown格式的预览"""
    preview = f"""# {content['title']}

**生成时间**：{content['generated_at']}  
**生成人**：{content['generated_by']}

---

"""
    
    for section_name, section_content in content.get("sections", {}).items():
        preview += f"## {section_name}\n\n{section_content}\n\n"
    
    preview += "---\n\n*此文档由AI自动生成，请核对后使用*"
    
    return preview
```

### 5. 分享链接生成

```python
async def _create_share_link(self, doc_url: str) -> str:
    """生成分享链接"""
    # 生成预签名URL（7天有效期）
    presigned_url = await self.minio.get_presigned_url(
        doc_url,
        expires=604800  # 7天
    )
    
    return presigned_url
```

## 交付物

1. **Skill 主类**: `src/skills/doc_generation/skill.py`
2. **Skill 定义**: `knowledge-base/field-info-agent/implementation/skills/doc-generation/SKILL.md`
3. **Word模板**: `src/skills/doc_generation/templates/*.docx`
4. **单元测试**: `tests/skills/test_doc_generation.py`
5. **使用文档**: `docs/skills/doc-generation.md`

## 验收标准

- [ ] 支持3种文档类型生成
- [ ] Word文档格式正确
- [ ] 照片正确嵌入文档
- [ ] 预签名分享链接可用
- [ ] Markdown预览正确
- [ ] 单元测试覆盖率 >90%

## 报告要求

完成后请提交报告到: `reports/REPORT-006-doc-generation.md`

---

**创建时间**: 2026-03-20  
**负责团队**: Field Core Team  
**状态**: 待开始  
**依赖**: Phase 1 全部完成 ✅