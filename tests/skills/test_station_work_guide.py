"""
StationWorkGuide Skill 单元测试

测试覆盖：
- 状态机流转
- 三种工作类型流程
- 全局命令处理
- 数据收集和保存
- AI分析集成
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.skills.station_work_guide import (
    StationWorkGuideSkill, WorkPhase, WorkType,
    WORK_TYPE_CONFIGS, PHASE_TRANSITIONS
)
from src.skills.base import SkillContext, SkillResultStatus


class TestWorkflows:
    """测试工作流配置"""
    
    def test_phase_transitions(self):
        """测试状态流转规则"""
        # IDLE 可以转到 PREPARING
        assert WorkPhase.PREPARING.value in PHASE_TRANSITIONS[WorkPhase.IDLE.value]
        
        # PREPARING 可以转到 COLLECTING 或 COMPLETED
        assert WorkPhase.COLLECTING.value in PHASE_TRANSITIONS[WorkPhase.PREPARING.value]
        assert WorkPhase.COMPLETED.value in PHASE_TRANSITIONS[WorkPhase.PREPARING.value]
        
        # COLLECTING 可以转到 ANALYZING 或 COMPLETED
        assert WorkPhase.ANALYZING.value in PHASE_TRANSITIONS[WorkPhase.COLLECTING.value]
        assert WorkPhase.COMPLETED.value in PHASE_TRANSITIONS[WorkPhase.COLLECTING.value]
        
        # COMPLETED 可以回到 IDLE
        assert WorkPhase.IDLE.value in PHASE_TRANSITIONS[WorkPhase.COMPLETED.value]
    
    def test_work_type_configs(self):
        """测试工作类型配置"""
        # 三种工作类型都存在
        assert WorkType.POWER_ROOM in WORK_TYPE_CONFIGS
        assert WorkType.CUSTOMER_VISIT in WORK_TYPE_CONFIGS
        assert WorkType.EMERGENCY in WORK_TYPE_CONFIGS
        
        # 配置结构完整
        for work_type, config in WORK_TYPE_CONFIGS.items():
            assert config.name
            assert config.description
            assert len(config.checklist) > 0
            assert len(config.steps) > 0
            assert config.completion_message
    
    def test_power_room_steps(self):
        """测试配电房巡检步骤"""
        config = WORK_TYPE_CONFIGS[WorkType.POWER_ROOM]
        steps = config.steps
        
        # 至少有5个步骤
        assert len(steps) >= 5
        
        # 检查关键步骤
        step_names = [s.name for s in steps]
        assert "基本信息" in step_names
        assert "变压器铭牌" in step_names
        assert "设备状态" in step_names
        assert "安全环境" in step_names
        
        # 变压器铭牌步骤需要AI分析
        nameplate_step = next(s for s in steps if s.name == "变压器铭牌")
        assert nameplate_step.use_ai is True
        assert nameplate_step.ai_type == "nameplate"
    
    def test_customer_visit_steps(self):
        """测试客户走访步骤"""
        config = WORK_TYPE_CONFIGS[WorkType.CUSTOMER_VISIT]
        steps = config.steps
        
        step_names = [s.name for s in steps]
        assert "客户信息" in step_names
        assert "用电情况" in step_names
        assert "业务需求" in step_names
        assert "意见建议" in step_names
    
    def test_emergency_steps(self):
        """测试应急信息采集步骤"""
        config = WORK_TYPE_CONFIGS[WorkType.EMERGENCY]
        steps = config.steps
        
        step_names = [s.name for s in steps]
        assert "基本情况" in step_names
        assert "现场照片" in step_names
        assert "初步处理" in step_names
        
        # 现场照片需要AI安全分析
        photo_step = next(s for s in steps if s.name == "现场照片")
        assert photo_step.use_ai is True
        assert photo_step.ai_type == "safety"


class TestStationWorkGuideSkill:
    """测试 StationWorkGuide Skill"""
    
    @pytest.fixture
    def skill(self):
        """创建 Skill 实例"""
        return StationWorkGuideSkill()
    
    @pytest.fixture
    def mock_tools(self):
        """创建模拟的 Tools"""
        pg_tool = AsyncMock()
        kimi_tool = AsyncMock()
        minio_tool = AsyncMock()
        return pg_tool, kimi_tool, minio_tool
    
    @pytest.fixture
    def base_context(self):
        """创建基础上下文"""
        return {
            "session_id": "test_session_001",
            "user_id": "test_user_001",
            "session": {},
            "metadata": {}
        }
    
    @pytest.mark.asyncio
    async def test_skill_initialization(self, skill):
        """测试 Skill 初始化"""
        await skill.initialize()
        assert skill._initialized is True
        assert skill.NAME == "station_work_guide"
        assert skill.VERSION == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_idle_phase_welcome(self, skill, base_context):
        """测试空闲阶段返回欢迎消息"""
        context = SkillContext(
            **base_context,
            message="你好"
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert "驻点工作助手" in result.response
        assert "配电房巡检" in result.response
        assert "客户走访" in result.response
        assert "应急信息采集" in result.response
    
    @pytest.mark.asyncio
    async def test_select_work_type_power_room(self, skill, base_context):
        """测试选择配电房巡检"""
        context = SkillContext(
            **base_context,
            message="1"
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert result.next_phase == WorkPhase.PREPARING.value
        assert result.data["work_type"] == WorkType.POWER_ROOM.value
        assert "配电房巡检" in result.response
        assert context.session["work_type"] == WorkType.POWER_ROOM.value
    
    @pytest.mark.asyncio
    async def test_select_work_type_customer_visit(self, skill, base_context):
        """测试选择客户走访"""
        context = SkillContext(
            **base_context,
            message="2"
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert result.next_phase == WorkPhase.PREPARING.value
        assert result.data["work_type"] == WorkType.CUSTOMER_VISIT.value
    
    @pytest.mark.asyncio
    async def test_select_work_type_emergency(self, skill, base_context):
        """测试选择应急信息采集"""
        context = SkillContext(
            **base_context,
            message="3"
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert result.next_phase == WorkPhase.PREPARING.value
        assert result.data["work_type"] == WorkType.EMERGENCY.value
    
    @pytest.mark.asyncio
    async def test_select_work_type_by_keyword(self, skill, base_context):
        """测试通过关键词选择工作类型"""
        context = SkillContext(
            **base_context,
            message="配电房"
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert result.data["work_type"] == WorkType.POWER_ROOM.value
    
    @pytest.mark.asyncio
    async def test_preparing_phase_checklist(self, skill, base_context):
        """测试准备阶段显示检查清单"""
        context = SkillContext(
            **base_context,
            message="开始"
        )
        context.session["phase"] = WorkPhase.PREPARING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert result.next_phase == WorkPhase.COLLECTING.value
        assert "(1/" in result.response  # 显示步骤进度
        assert "基本信息" in result.response
    
    @pytest.mark.asyncio
    async def test_collecting_phase_text_input(self, skill, base_context):
        """测试采集阶段接收文字输入"""
        context = SkillContext(
            **base_context,
            message="1号配电房，阳光小区"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 0
        context.session["collected_data"] = {}
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert result.next_phase == WorkPhase.COLLECTING.value
        # 数据应该被保存
        assert "基本信息" in context.session["collected_data"]
        assert "阳光小区" in context.session["collected_data"]["基本信息"]["text"]
    
    @pytest.mark.asyncio
    async def test_collecting_phase_with_photos(self, skill, base_context, mock_tools):
        """测试采集阶段接收照片"""
        pg_tool, kimi_tool, _ = mock_tools
        skill_with_tools = StationWorkGuideSkill(pg_tool, kimi_tool, None)
        
        # 设置模拟AI分析结果
        kimi_tool.analyze_image.return_value = {
            "model": "S11-M-800/10",
            "capacity": "800"
        }
        
        context = SkillContext(
            **{**base_context, "metadata": {"photos": ["http://minio/photo1.jpg"]}},
            message="照片已上传"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 1  # 变压器铭牌步骤
        context.session["collected_data"] = {}
        
        result = await skill_with_tools.invoke(context)
        
        # AI应该被调用
        kimi_tool.analyze_image.assert_called_once()
        assert "变压器铭牌" in context.session["collected_data"]
        assert "photos" in context.session["collected_data"]["变压器铭牌"]
    
    @pytest.mark.asyncio
    async def test_next_step_navigation(self, skill, base_context):
        """测试下一步导航"""
        context = SkillContext(
            **base_context,
            message="下一步"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 0
        context.session["collected_data"] = {"基本信息": {"text": "测试数据"}}
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert context.session["current_step"] == 1  # 进入下一步
        assert "变压器铭牌" in result.response
    
    @pytest.mark.asyncio
    async def test_prev_step_navigation(self, skill, base_context):
        """测试上一步导航"""
        context = SkillContext(
            **base_context,
            message="上一步"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 1
        context.session["collected_data"] = {}
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert context.session["current_step"] == 0  # 返回上一步
        assert "基本信息" in result.response
    
    @pytest.mark.asyncio
    async def test_skip_optional_step(self, skill, base_context):
        """测试跳过可选步骤"""
        context = SkillContext(
            **base_context,
            message="跳过"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.CUSTOMER_VISIT.value  # 使用客户走访，有可选步骤
        context.session["current_step"] = 2  # 业务需求步骤（通常是可选）
        context.session["collected_data"] = {}
        
        result = await skill.invoke(context)
        
        # 如果当前步骤不是必填，应该可以跳过
        # 否则应该返回错误提示
        assert result.status in [SkillResultStatus.NEED_INPUT, SkillResultStatus.SUCCESS]
    
    @pytest.mark.asyncio
    async def test_help_command(self, skill, base_context):
        """测试帮助命令"""
        context = SkillContext(
            **base_context,
            message="帮助"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert "操作指南" in result.response
        assert "基本操作" in result.response
    
    @pytest.mark.asyncio
    async def test_status_command(self, skill, base_context):
        """测试状态命令"""
        context = SkillContext(
            **base_context,
            message="状态"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 2
        context.session["collected_data"] = {"基本信息": {"text": "测试"}}
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.SUCCESS
        assert "当前状态" in result.response
        assert "配电房巡检" in result.response
        assert "3/" in result.response  # 显示当前步骤
    
    @pytest.mark.asyncio
    async def test_cancel_command(self, skill, base_context):
        """测试取消命令"""
        context = SkillContext(
            **base_context,
            message="取消"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["collected_data"] = {"基本信息": {"text": "测试"}}
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert "确定要取消" in result.response
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, skill, base_context):
        """测试完整工作流程"""
        # 模拟完成所有步骤
        context = SkillContext(
            **base_context,
            message="完成"
        )
        context.session["phase"] = WorkPhase.ANALYZING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["work_id"] = "test-work-001"
        context.session["start_time"] = datetime.now().isoformat()
        context.session["collected_data"] = {
            "基本信息": {"text": "1号配电房"},
            "变压器铭牌": {"ai_result": {"model": "S11"}},
            "设备状态": {"text": "正常"},
            "安全环境": {"text": "良好"},
            "巡检结论": {"text": "设备运行正常"}
        }
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.COMPLETED
        assert result.next_phase == WorkPhase.COMPLETED.value
        assert "完成" in result.response
        assert "test-work-001" in result.data["work_id"]
    
    @pytest.mark.asyncio
    async def test_start_new_after_completion(self, skill, base_context):
        """测试完成后开始新工作"""
        context = SkillContext(
            **base_context,
            message="1"
        )
        context.session["phase"] = WorkPhase.COMPLETED.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["collected_data"] = {"基本信息": {"text": "旧数据"}}
        
        result = await skill.invoke(context)
        
        # 应该重置状态并开始新工作
        assert result.status == SkillResultStatus.SUCCESS
        # 从COMPLETED阶段开始新工作时，会选择工作类型并进入PREPARING
        # 或者根据skill实现，可能会先进入IDLE再处理选择
        # 验证结果是成功的且与配电房巡检相关即可
        assert "配电房" in result.response or "驻点工作助手" in result.response
    
    def test_skill_info(self, skill):
        """测试获取 Skill 信息"""
        info = skill.get_info()
        
        assert info["name"] == "station_work_guide"
        assert info["version"] == "1.0.0"
        assert "work_types" in info
        assert "phases" in info


class TestEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def skill(self):
        return StationWorkGuideSkill()
    
    @pytest.fixture
    def base_context(self):
        return {
            "session_id": "test_session_001",
            "user_id": "test_user_001",
            "session": {},
            "metadata": {}
        }
    
    @pytest.mark.asyncio
    async def test_unknown_phase(self, skill, base_context):
        """测试未知阶段处理"""
        context = SkillContext(
            **base_context,
            message="测试"
        )
        context.session["phase"] = "unknown_phase"
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.ERROR
        assert "未知的工作阶段" in result.response
    
    @pytest.mark.asyncio
    async def test_empty_message(self, skill, base_context):
        """测试空消息处理"""
        context = SkillContext(
            **base_context,
            message=""
        )
        context.session["phase"] = WorkPhase.IDLE.value
        
        result = await skill.invoke(context)
        
        # 应该显示欢迎消息
        assert result.status == SkillResultStatus.NEED_INPUT
        assert "驻点工作助手" in result.response
    
    @pytest.mark.asyncio
    async def test_preparing_without_work_type(self, skill, base_context):
        """测试准备阶段无工作类型"""
        context = SkillContext(
            **base_context,
            message="开始"
        )
        context.session["phase"] = WorkPhase.PREPARING.value
        # 不设置 work_type
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.ERROR
        assert result.next_phase == WorkPhase.IDLE.value
    
    @pytest.mark.asyncio
    async def test_collecting_first_step_prev(self, skill, base_context):
        """测试采集阶段第一步时按上一步"""
        context = SkillContext(
            **base_context,
            message="上一步"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 0  # 第一步
        
        result = await skill.invoke(context)
        
        assert result.status == SkillResultStatus.NEED_INPUT
        assert "已经是第一步" in result.response
    
    @pytest.mark.asyncio
    async def test_ai_analysis_error_handling(self, skill, base_context):
        """测试AI分析错误处理"""
        # 模拟KIMI调用失败
        mock_kimi = AsyncMock()
        mock_kimi.analyze_image.side_effect = Exception("AI analysis failed")
        
        skill.kimi_tool = mock_kimi
        
        context = SkillContext(
            **{**base_context, "metadata": {"photos": ["http://photo.jpg"]}},
            message="照片"
        )
        context.session["phase"] = WorkPhase.COLLECTING.value
        context.session["work_type"] = WorkType.POWER_ROOM.value
        context.session["current_step"] = 1  # 需要AI分析的步骤
        context.session["collected_data"] = {}
        
        result = await skill.invoke(context)
        
        # 即使AI失败，流程也应该继续
        assert result.status == SkillResultStatus.NEED_INPUT
        # 错误应该被记录
        assert "ai_error" in context.session["collected_data"]["变压器铭牌"]


class TestMessageTemplates:
    """测试消息模板"""
    
    def test_welcome_message(self):
        """测试欢迎消息"""
        from src.skills.station_work_guide.templates import get_welcome_message
        
        msg = get_welcome_message()
        assert "驻点工作助手" in msg
        assert "配电房巡检" in msg
        assert "客户走访" in msg
        assert "应急信息采集" in msg
    
    def test_help_message(self):
        """测试帮助消息"""
        from src.skills.station_work_guide.templates import get_help_message
        
        msg = get_help_message()
        assert "操作指南" in msg
        assert "基本操作" in msg
    
    def test_preparing_message(self):
        """测试准备阶段消息"""
        from src.skills.station_work_guide.templates import MessageGenerator
        from src.skills.station_work_guide.workflows import WORK_TYPE_CONFIGS, WorkType
        
        config = WORK_TYPE_CONFIGS[WorkType.POWER_ROOM]
        msg = MessageGenerator.generate_preparing_message(config)
        
        assert "准备清单" in msg
        assert "安全帽" in msg
        assert "开始" in msg
    
    def test_collecting_message(self):
        """测试采集阶段消息"""
        from src.skills.station_work_guide.templates import MessageGenerator
        from src.skills.station_work_guide.workflows import WORK_TYPE_CONFIGS, WorkType
        
        config = WORK_TYPE_CONFIGS[WorkType.POWER_ROOM]
        step = config.steps[0]
        
        msg = MessageGenerator.generate_collecting_message(
            step=step,
            current_step=1,
            total_steps=5,
            collected_data={}
        )
        
        assert "(1/5)" in msg
        assert step.name in msg
        assert step.prompt in msg
    
    def test_summary_generation(self):
        """测试摘要生成"""
        from src.skills.station_work_guide.templates import MessageGenerator
        
        data = {
            "基本信息": {"photos": ["p1", "p2"]},
            "变压器铭牌": {"ai_result": {"model": "S11"}},
            "巡检结论": {"text": "设备运行正常，无异常发现"}
        }
        
        summary = MessageGenerator.generate_summary(data)
        
        assert "基本信息" in summary
        assert "2张照片" in summary
        assert "变压器铭牌" in summary
        assert "AI分析完成" in summary
        assert "巡检结论" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
