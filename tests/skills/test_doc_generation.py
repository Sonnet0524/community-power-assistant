"""
DocGeneration Skill 单元测试
测试覆盖率目标: >90%
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Mock openclaw 框架
import sys
from unittest.mock import MagicMock

# 创建一个可以接受 config 参数的 BaseSkill 类
class MockBaseSkill:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = MagicMock()

# 创建一个带有 params 属性的 SkillContext 类
class MockSkillContext:
    def __init__(self, params):
        self.params = params

mock_openclaw = MagicMock()
mock_openclaw.BaseSkill = MockBaseSkill
mock_openclaw.SkillContext = MockSkillContext
mock_openclaw.SkillResult = lambda response, data: type('SkillResult', (), {'response': response, 'data': data})()

sys.modules['openclaw'] = mock_openclaw
sys.modules['openclaw.tools'] = MagicMock()

# 现在可以导入被测模块
from src.skills.doc_generation.skill import (
    DocGenerationSkill,
    GeneratedDocument,
    DocumentSection,
    DOC_TEMPLATES
)


@pytest.fixture
def skill_config():
    """Skill 配置 Fixture"""
    return {
        "kimi_config": {"api_key": "test_key", "base_url": "https://test.com"},
        "minio_config": {"endpoint": "localhost:9000", "access_key": "test"},
        "output_dir": "/tmp/test_docs"
    }


@pytest.fixture
def mock_kimi():
    """Mock KIMI Tool"""
    mock = AsyncMock()
    mock.chat = AsyncMock(return_value=json.dumps({
        "工作概述": "本次巡检工作正常完成",
        "现场情况": "现场环境良好",
        "设备状态": "设备运行正常",
        "发现问题": "无明显问题",
        "整改建议": "继续保持"
    }))
    return mock


@pytest.fixture
def mock_minio():
    """Mock MinIO Tool"""
    mock = AsyncMock()
    mock.upload_file = AsyncMock(return_value="http://minio/test/doc.docx")
    mock.get_presigned_url = AsyncMock(return_value="http://minio/test/doc.docx?token=abc")
    return mock


@pytest.fixture
def doc_skill(skill_config, mock_kimi, mock_minio):
    """创建测试用的 Skill 实例"""
    with patch('src.skills.doc_generation.skill.KIMITool', return_value=mock_kimi), \
         patch('src.skills.doc_generation.skill.MinIOTool', return_value=mock_minio):
        skill = DocGenerationSkill(skill_config)
        return skill


class TestDocGenerationSkillInitialization:
    """测试 Skill 初始化"""
    
    def test_init_with_default_config(self):
        """测试默认配置初始化"""
        with patch('src.skills.doc_generation.skill.KIMITool'), \
             patch('src.skills.doc_generation.skill.MinIOTool'):
            skill = DocGenerationSkill()
            assert skill.NAME == "doc_generation"
            assert skill.DESCRIPTION == "根据采集数据自动生成供电简报/应急指引/工作总结文档"
            assert skill.VERSION == "1.0.0"
            assert skill.output_dir.exists()
    
    def test_init_with_custom_config(self, skill_config):
        """测试自定义配置初始化"""
        with patch('src.skills.doc_generation.skill.KIMITool'), \
             patch('src.skills.doc_generation.skill.MinIOTool'):
            skill = DocGenerationSkill(skill_config)
            assert skill.config == skill_config
            assert str(skill.output_dir) == skill_config["output_dir"]


class TestDocGenerationSkillInvoke:
    """测试 invoke 方法"""
    
    @pytest.mark.asyncio
    async def test_invoke_briefing_success(self, doc_skill):
        """测试生成供电简报成功"""
        context = MockSkillContext({
            "doc_type": "briefing",
            "task_id": "task_001",
            "data": {
                "station": "测试供电所",
                "date": "2026-03-20",
                "staff": "张三",
                "location": "测试地点",
                "collection_data": "测试数据"
            },
            "photos": ["http://example.com/photo1.jpg"],
            "user_id": "user_001"
        })
        
        result = await doc_skill.invoke(context)
        
        assert "✅" in result.response
        assert result.data["doc_type"] == "briefing"
        assert "document_url" in result.data
        assert "share_link" in result.data
        assert "preview" in result.data
    
    @pytest.mark.asyncio
    async def test_invoke_emergency_success(self, doc_skill):
        """测试生成应急指引成功"""
        context = MockSkillContext({
            "doc_type": "emergency",
            "task_id": "task_002",
            "data": {
                "event_type": "停电事故",
                "location": "测试区域",
                "time": "2026-03-20 10:00",
                "impact": "影响100户用户",
                "current_status": "正在抢修"
            },
            "photos": [],
            "user_id": "user_002"
        })
        
        result = await doc_skill.invoke(context)
        
        assert "✅" in result.response
        assert result.data["doc_type"] == "emergency"
    
    @pytest.mark.asyncio
    async def test_invoke_summary_success(self, doc_skill):
        """测试生成工作总结成功"""
        context = MockSkillContext({
                "doc_type": "summary",
                "task_id": "task_003",
                "data": {
                    "period": "2026年3月",
                    "department": "运维部",
                    "reporter": "李四",
                    "completed_tasks": "完成巡检20次",
                    "issues": "发现3处隐患",
                    "task_count": 20,
                    "issue_count": 3,
                    "fix_rate": 90,
                    "satisfaction": 95
                },
                "photos": [],
                "user_id": "user_003"
        }
        
        result = await doc_skill.invoke(context)
        
        assert "✅" in result.response
        assert result.data["doc_type"] == "summary"
    
    @pytest.mark.asyncio
    async def test_invoke_invalid_doc_type(self, doc_skill):
        """测试不支持的文档类型"""
        context = MockSkillContext({
                "doc_type": "invalid_type",
                "task_id": "task_004",
                "data": {},
                "photos": []
        }
        
        result = await doc_skill.invoke(context)
        
        assert "❌" in result.response
        assert "参数错误" in result.response
        assert "error" in result.data
    
    @pytest.mark.asyncio
    async def test_invoke_default_doc_type(self, doc_skill):
        """测试默认文档类型"""
        context = MockSkillContext({
                "task_id": "task_005",
                "data": {
                    "station": "测试供电所",
                    "date": "2026-03-20",
                    "staff": "测试人员",
                    "location": "测试地点"
                },
                "photos": [],
                "user_id": "user_005"
        }
        
        result = await doc_skill.invoke(context)
        
        assert result.data["doc_type"] == "briefing"  # 默认类型


class TestContentGeneration:
    """测试内容生成"""
    
    @pytest.mark.asyncio
    async def test_generate_content_briefing(self, doc_skill):
        """测试生成供电简报内容"""
        task_data = {
            "station": "测试供电所",
            "date": "2026-03-20",
            "staff": "张三",
            "location": "测试地点",
            "collection_data": "测试数据",
            "photos": [],
            "photo_count": 0,
            "user_id": "user_001"
        }
        
        content = await doc_skill._generate_content("briefing", task_data)
        
        assert content.doc_type == "briefing"
        assert "测试供电所" in content.title
        assert "2026-03-20" in content.generated_at
        assert "user_001" in content.generated_by
        assert "工作概述" in content.sections
        assert "现场情况" in content.sections
    
    @pytest.mark.asyncio
    async def test_generate_content_emergency(self, doc_skill):
        """测试生成应急指引内容"""
        task_data = {
            "event_type": "停电事故",
            "location": "测试区域",
            "time": "2026-03-20 10:00",
            "impact": "影响用户",
            "current_status": "处理中",
            "scene_description": "现场描述",
            "photos": [],
            "photo_count": 0,
            "user_id": "user_002"
        }
        
        content = await doc_skill._generate_content("emergency", task_data)
        
        assert content.doc_type == "emergency"
        assert "停电事故" in content.title
        assert "事件概述" in content.sections
        assert "应急措施" in content.sections
    
    @pytest.mark.asyncio
    async def test_generate_content_summary(self, doc_skill):
        """测试生成工作总结内容"""
        task_data = {
            "period": "2026年3月",
            "department": "运维部",
            "reporter": "李四",
            "completed_tasks": "任务列表",
            "issues": "问题列表",
            "task_count": 10,
            "issue_count": 2,
            "fix_rate": 80,
            "satisfaction": 90,
            "photos": [],
            "photo_count": 0,
            "user_id": "user_003"
        }
        
        content = await doc_skill._generate_content("summary", task_data)
        
        assert content.doc_type == "summary"
        assert "工作总结" in content.title
        assert "工作回顾" in content.sections
        assert "完成情况" in content.sections
    
    @pytest.mark.asyncio
    async def test_generate_content_kimi_error(self, doc_skill, mock_kimi):
        """测试 KIMI 调用失败时的处理"""
        mock_kimi.chat.side_effect = Exception("KIMI API Error")
        
        task_data = {
            "station": "测试",
            "date": "2026-03-20",
            "photos": [],
            "photo_count": 0,
            "user_id": "user"
        }
        
        with pytest.raises(Exception):
            await doc_skill._generate_content("briefing", task_data)


class TestContentParsing:
    """测试内容解析"""
    
    def test_parse_generated_content_json(self, doc_skill):
        """测试 JSON 格式解析"""
        response = json.dumps({
            "工作概述": "概述内容",
            "现场情况": "现场描述",
            "设备状态": "状态良好"
        })
        
        sections = doc_skill._parse_generated_content(
            response, 
            ["工作概述", "现场情况", "设备状态", "发现问题"]
        )
        
        assert sections["工作概述"] == "概述内容"
        assert sections["现场情况"] == "现场描述"
        assert sections["设备状态"] == "状态良好"
        assert "发现问题" in sections  # 缺失的字段会被补充
    
    def test_parse_generated_content_text(self, doc_skill):
        """测试文本格式解析"""
        response = """
        工作概述：本次工作顺利完成
        现场情况：现场条件良好
        设备状态：运行正常
        发现问题：无
        """
        
        sections = doc_skill._parse_generated_content(
            response,
            ["工作概述", "现场情况", "设备状态", "发现问题"]
        )
        
        assert "本次工作顺利完成" in sections["工作概述"]
        assert "现场条件良好" in sections["现场情况"]
    
    def test_parse_generated_content_missing_sections(self, doc_skill):
        """测试缺失章节的处理"""
        response = json.dumps({
            "工作概述": "概述内容"
        })
        
        sections = doc_skill._parse_generated_content(
            response,
            ["工作概述", "现场情况", "设备状态"]
        )
        
        assert sections["工作概述"] == "概述内容"
        assert sections["现场情况"] == "（待补充）"
        assert sections["设备状态"] == "（待补充）"


class TestWordDocumentCreation:
    """测试 Word 文档创建"""
    
    @pytest.mark.asyncio
    async def test_create_word_document_briefing(self, doc_skill, mock_minio):
        """测试创建供电简报 Word 文档"""
        content = GeneratedDocument(
            title="测试供电简报",
            doc_type="briefing",
            generated_at="2026-03-20 10:00:00",
            generated_by="测试用户",
            sections={
                "工作概述": "工作顺利完成",
                "现场情况": "现场良好",
                "设备状态": "正常",
                "发现问题": "无",
                "整改建议": "继续保持",
                "附件（照片）": ""
            },
            photos=[],
            metadata={}
        )
        
        task_data = {"station": "测试供电所"}
        
        doc_url = await doc_skill._create_word_document(content, "briefing", task_data)
        
        assert doc_url == "http://minio/test/doc.docx"
        mock_minio.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_word_document_with_photos(self, doc_skill, mock_minio):
        """测试带照片的 Word 文档创建"""
        content = GeneratedDocument(
            title="测试文档",
            doc_type="briefing",
            generated_at="2026-03-20 10:00:00",
            generated_by="测试用户",
            sections={
                "工作概述": "概述",
                "现场情况": "情况",
                "设备状态": "状态",
                "发现问题": "问题",
                "整改建议": "建议",
                "附件（照片）": ""
            },
            photos=["http://example.com/photo1.jpg"],
            metadata={}
        )
        
        task_data = {"station": "测试"}
        
        # Mock 照片下载
        with patch.object(doc_skill, '_download_photo', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = None  # 模拟下载失败，但不影响主流程
            
            doc_url = await doc_skill._create_word_document(content, "briefing", task_data)
            
            assert doc_url is not None


class TestPreviewGeneration:
    """测试预览生成"""
    
    def test_generate_preview_briefing(self, doc_skill):
        """测试供电简报预览"""
        content = GeneratedDocument(
            title="测试简报",
            doc_type="briefing",
            generated_at="2026-03-20 10:00:00",
            generated_by="测试用户",
            sections={
                "工作概述": "这是工作概述内容",
                "现场情况": "现场情况描述",
                "设备状态": "设备状态信息"
            },
            photos=["photo1.jpg"],
            metadata={}
        )
        
        preview = doc_skill._generate_preview(content)
        
        assert "# 测试简报" in preview
        assert "测试用户" in preview
        assert "工作概述" in preview
        assert "现场情况" in preview
        assert "此文档由 AI 自动生成" in preview
    
    def test_generate_preview_long_content(self, doc_skill):
        """测试长内容预览（会被截断）"""
        content = GeneratedDocument(
            title="测试",
            doc_type="briefing",
            generated_at="2026-03-20 10:00:00",
            generated_by="用户",
            sections={
                "工作概述": "A" * 500  # 长内容
            },
            photos=[],
            metadata={}
        )
        
        preview = doc_skill._generate_preview(content)
        
        assert "..." in preview  # 内容被截断


class TestShareLink:
    """测试分享链接"""
    
    @pytest.mark.asyncio
    async def test_create_share_link_success(self, doc_skill, mock_minio):
        """测试创建分享链接成功"""
        doc_url = "http://minio/test/doc.docx"
        
        share_link = await doc_skill._create_share_link(doc_url)
        
        assert "token=abc" in share_link
        mock_minio.get_presigned_url.assert_called_once_with(doc_url, expires=604800)
    
    @pytest.mark.asyncio
    async def test_create_share_link_failure(self, doc_skill, mock_minio):
        """测试创建分享链接失败"""
        doc_url = "http://minio/test/doc.docx"
        mock_minio.get_presigned_url.side_effect = Exception("MinIO Error")
        
        share_link = await doc_skill._create_share_link(doc_url)
        
        assert share_link == doc_url  # fallback 到原始 URL


class TestUtilityMethods:
    """测试工具方法"""
    
    @pytest.mark.asyncio
    async def test_get_supported_types(self, doc_skill):
        """测试获取支持的文档类型"""
        types = await doc_skill.get_supported_types()
        
        assert len(types) == 3
        
        type_names = [t["type"] for t in types]
        assert "briefing" in type_names
        assert "emergency" in type_names
        assert "summary" in type_names
        
        # 验证每个类型都有 name 和 sections
        for t in types:
            assert "name" in t
            assert "sections" in t
            assert isinstance(t["sections"], list)
    
    @pytest.mark.asyncio
    async def test_validate_params_valid(self, doc_skill):
        """测试参数验证 - 合法参数"""
        params = {"doc_type": "briefing"}
        
        is_valid, error_msg = await doc_skill.validate_params(params)
        
        assert is_valid is True
        assert error_msg == ""
    
    @pytest.mark.asyncio
    async def test_validate_params_missing_field(self, doc_skill):
        """测试参数验证 - 缺少必需字段"""
        params = {}  # 缺少 doc_type
        
        is_valid, error_msg = await doc_skill.validate_params(params)
        
        assert is_valid is False
        assert "缺少必需参数" in error_msg
    
    @pytest.mark.asyncio
    async def test_validate_params_invalid_type(self, doc_skill):
        """测试参数验证 - 无效文档类型"""
        params = {"doc_type": "invalid_type"}
        
        is_valid, error_msg = await doc_skill.validate_params(params)
        
        assert is_valid is False
        assert "不支持的文档类型" in error_msg


class TestDocumentTemplates:
    """测试文档模板"""
    
    def test_doc_templates_structure(self):
        """测试文档模板结构"""
        assert "briefing" in DOC_TEMPLATES
        assert "emergency" in DOC_TEMPLATES
        assert "summary" in DOC_TEMPLATES
        
        for doc_type, template in DOC_TEMPLATES.items():
            assert "name" in template
            assert "file_name" in template
            assert "sections" in template
            assert "title_template" in template
            assert "prompt_template" in template
            assert isinstance(template["sections"], list)
            assert len(template["sections"]) > 0
    
    def test_briefing_template(self):
        """测试供电简报模板"""
        template = DOC_TEMPLATES["briefing"]
        assert template["name"] == "供电简报"
        assert "{date}" in template["file_name"]
        assert "{station}" in template["file_name"]
        assert "工作概述" in template["sections"]
        assert "附件（照片）" in template["sections"]
    
    def test_emergency_template(self):
        """测试应急指引模板"""
        template = DOC_TEMPLATES["emergency"]
        assert template["name"] == "应急指引"
        assert "事件概述" in template["sections"]
        assert "应急措施" in template["sections"]
    
    def test_summary_template(self):
        """测试工作总结模板"""
        template = DOC_TEMPLATES["summary"]
        assert template["name"] == "工作总结"
        assert "工作回顾" in template["sections"]
        assert "下阶段计划" in template["sections"]


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_invoke_with_exception(self, doc_skill, mock_kimi):
        """测试 invoke 异常处理"""
        mock_kimi.chat.side_effect = Exception("Unexpected Error")
        
        context = MockSkillContext({
                "doc_type": "briefing",
                "task_id": "task_001",
                "data": {"station": "测试"},
                "photos": [],
                "user_id": "user_001"
        }
        
        result = await doc_skill.invoke(context)
        
        assert "❌" in result.response
        assert "error" in result.data
    
    @pytest.mark.asyncio
    async def test_download_photo_failure(self, doc_skill):
        """测试照片下载失败"""
        result = await doc_skill._download_photo("http://invalid-url", 1)
        assert result is None


class TestGeneratedDocumentDataclass:
    """测试 GeneratedDocument 数据类"""
    
    def test_generated_document_creation(self):
        """测试 GeneratedDocument 创建"""
        doc = GeneratedDocument(
            title="测试标题",
            doc_type="briefing",
            generated_at="2026-03-20",
            generated_by="用户",
            sections={"概述": "内容"},
            photos=["photo.jpg"],
            metadata={"key": "value"}
        )
        
        assert doc.title == "测试标题"
        assert doc.doc_type == "briefing"
        assert len(doc.photos) == 1
        assert doc.metadata["key"] == "value"
    
    def test_generated_document_defaults(self):
        """测试 GeneratedDocument 默认值"""
        doc = GeneratedDocument(
            title="测试",
            doc_type="briefing",
            generated_at="2026-03-20",
            generated_by="用户"
        )
        
        assert doc.sections == {}
        assert doc.photos == []
        assert doc.metadata == {}


class TestDocumentSectionDataclass:
    """测试 DocumentSection 数据类"""
    
    def test_document_section_creation(self):
        """测试 DocumentSection 创建"""
        section = DocumentSection(
            name="测试章节",
            content="章节内容",
            level=2
        )
        
        assert section.name == "测试章节"
        assert section.content == "章节内容"
        assert section.level == 2
    
    def test_document_section_default_level(self):
        """测试默认 level"""
        section = DocumentSection(
            name="测试",
            content="内容"
        )
        
        assert section.level == 1  # 默认值


# 运行测试覆盖率检查
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=src.skills.doc_generation",
        "--cov-report=term-missing",
        "--cov-fail-under=90"
    ])
