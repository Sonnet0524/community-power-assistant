"""
EmergencyGuide Skill 单元测试

测试覆盖：
- 应急类型验证
- 应急方案生成
- 敏感客户识别
- 关怀消息生成
- 应急文档生成
- 整体调用流程

运行测试：
    pytest tests/skills/test_emergency_guide.py -v
    pytest tests/skills/test_emergency_guide.py --cov=src.skills.emergency_guide --cov-report=html
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# 导入被测试的模块
from src.skills.emergency_guide.skill import (
    EmergencyGuideSkill,
    SkillContext,
    SkillResult
)
from src.skills.emergency_guide.templates import EmergencyTemplates


class TestEmergencyTemplates:
    """测试应急模板类"""
    
    def test_get_emergency_type(self):
        """测试获取应急类型定义"""
        # 测试有效的应急类型
        result = EmergencyTemplates.get_emergency_type("power_outage")
        assert result["name"] == "停电故障"
        assert "icon" in result
        
        result = EmergencyTemplates.get_emergency_type("equipment_fault")
        assert result["name"] == "设备故障"
        
        result = EmergencyTemplates.get_emergency_type("safety_incident")
        assert result["name"] == "安全事故"
        
        result = EmergencyTemplates.get_emergency_type("customer_complaint")
        assert result["name"] == "敏感客户投诉"
        
        # 测试无效的应急类型
        result = EmergencyTemplates.get_emergency_type("invalid_type")
        assert result == {}
    
    def test_get_action_plan(self):
        """测试获取应急方案"""
        # 测试停电故障方案
        plan = EmergencyTemplates.get_action_plan("power_outage")
        assert "immediate_actions" in plan
        assert "contacts" in plan
        assert "estimated_time" in plan
        assert len(plan["immediate_actions"]) >= 5
        
        # 测试设备故障方案
        plan = EmergencyTemplates.get_action_plan("equipment_fault")
        assert "检修班" in plan["contacts"]
        
        # 测试安全事故方案
        plan = EmergencyTemplates.get_action_plan("safety_incident")
        assert "安监部" in plan["contacts"]
        
        # 测试敏感客户投诉方案
        plan = EmergencyTemplates.get_action_plan("customer_complaint")
        assert "客服中心" in plan["contacts"]
        
        # 测试无效的应急类型
        plan = EmergencyTemplates.get_action_plan("invalid")
        assert plan == {}
    
    def test_get_customer_care_message(self):
        """测试获取客户关怀消息"""
        # 测试医院类型
        msg = EmergencyTemplates.get_customer_care_message(
            customer_type="hospital",
            customer_name="中心医院",
            location="XX街道",
            emergency_type="停电故障",
            eta="2小时",
            manager_contact="138-xxxx-xxxx"
        )
        assert "医院" in msg
        assert "中心医院" in msg
        assert "XX街道" in msg
        assert "138-xxxx-xxxx" in msg
        
        # 测试学校类型
        msg = EmergencyTemplates.get_customer_care_message(
            customer_type="school",
            customer_name="第一中学",
            location="XX区",
            emergency_type="停电",
            eta="3小时"
        )
        assert "学校" in msg or "🏫" in msg
        assert "第一中学" in msg
        
        # 测试企业类型
        msg = EmergencyTemplates.get_customer_care_message(
            customer_type="enterprise",
            customer_name="XX工厂",
            location="工业区",
            emergency_type="停电故障",
            eta="1小时"
        )
        assert "企业" in msg or "🏢" in msg
        
        # 测试默认类型
        msg = EmergencyTemplates.get_customer_care_message(
            customer_type="unknown",
            customer_name="用户",
            location="XX小区",
            emergency_type="停电",
            eta="2小时"
        )
        assert "用户" in msg
    
    def test_get_response_level(self):
        """测试获取响应级别"""
        assert EmergencyTemplates.get_response_level("重大") == "一级响应"
        assert EmergencyTemplates.get_response_level("危急") == "一级响应"
        assert EmergencyTemplates.get_response_level("紧急") == "一级响应"
        assert EmergencyTemplates.get_response_level("较大") == "二级响应"
        assert EmergencyTemplates.get_response_level("严重") == "二级响应"
        assert EmergencyTemplates.get_response_level("重要") == "二级响应"
        assert EmergencyTemplates.get_response_level("一般") == "三级响应"
        assert EmergencyTemplates.get_response_level("未知") == "三级响应"
    
    def test_build_notification(self):
        """测试构建通知消息"""
        # 测试应急启动通知
        msg = EmergencyTemplates.build_notification(
            "emergency_start",
            emergency_name="停电故障",
            icon="⚡",
            severity="重大",
            response_level="一级响应",
            location="XX街道",
            timestamp="2026-03-20 14:30:00",
            actions="1. 行动1\n2. 行动2\n",
            contacts="抢修班, 调度中心",
            estimated_time="2小时",
            sensitive_customers_info="已识别2位敏感客户\n"
        )
        assert "停电故障" in msg
        assert "⚡" in msg
        assert "一级响应" in msg
        assert "XX街道" in msg
        assert "抢修班" in msg
        
        # 测试进展更新通知
        msg = EmergencyTemplates.build_notification(
            "progress_update",
            emergency_name="停电故障",
            status="处理中",
            timestamp="2026-03-20 15:00:00",
            progress="已完成故障定位",
            eta="1小时"
        )
        assert "进展更新" in msg
        assert "处理中" in msg
        
        # 测试应急完成通知
        msg = EmergencyTemplates.build_notification(
            "emergency_complete",
            emergency_name="停电故障",
            result="已恢复供电",
            timestamp="2026-03-20 16:00:00",
            duration="1.5小时",
            summary="故障已排除，供电恢复正常"
        )
        assert "应急处理完成" in msg
        assert "已恢复供电" in msg
    
    def test_get_analysis_prompt(self):
        """测试获取分析提示词"""
        prompt = EmergencyTemplates.get_analysis_prompt(
            "emergency_analysis",
            emergency_type="停电故障",
            location="XX街道",
            description="变压器冒烟",
            photo_analysis="[]"
        )
        assert "停电故障" in prompt
        assert "XX街道" in prompt
        assert "变压器冒烟" in prompt
        assert "JSON格式" in prompt
        
        # 测试照片分析提示词
        prompt = EmergencyTemplates.get_analysis_prompt("photo_analysis")
        assert len(prompt) > 0
        
        # 测试无效的提示词类型
        prompt = EmergencyTemplates.get_analysis_prompt("invalid")
        assert prompt == ""


class TestEmergencyGuideSkill:
    """测试 EmergencyGuide Skill"""
    
    @pytest.fixture
    def mock_tools(self):
        """创建模拟工具"""
        kimi = AsyncMock()
        kimi.chat = AsyncMock(return_value='{"impact_scope": "大范围停电", "possible_causes": ["设备老化"], "urgency_level": "高", "suggested_actions": ["立即抢修"], "required_resources": ["抢修车"]}')
        kimi.analyze_image = AsyncMock(return_value={"description": "变压器冒烟"})
        
        pg = AsyncMock()
        pg.query = AsyncMock(return_value=[
            {
                "id": 1,
                "name": "中心医院",
                "type": "hospital",
                "location": "XX街道",
                "is_important": True,
                "complaint_count": 0,
                "contact_phone": "1234567890",
                "wecom_id": "user_001",
                "manager_contact": "138-xxxx-xxxx"
            },
            {
                "id": 2,
                "name": "张先生",
                "type": "default",
                "location": "XX街道XX号",
                "is_important": False,
                "complaint_count": 3,
                "contact_phone": "0987654321",
                "wecom_id": "user_002",
                "manager_contact": ""
            }
        ])
        
        wecom = AsyncMock()
        wecom.send_text = AsyncMock(return_value={"errcode": 0})
        
        minio = AsyncMock()
        minio.upload_text = AsyncMock(return_value="http://minio:9000/emergency-docs/emergency_power_outage_20260320.md")
        
        return {"kimi": kimi, "pg": pg, "wecom": wecom, "minio": minio}
    
    @pytest.fixture
    def skill(self, mock_tools):
        """创建 Skill 实例"""
        return EmergencyGuideSkill(
            kimi_tool=mock_tools["kimi"],
            pg_tool=mock_tools["pg"],
            wecom_tool=mock_tools["wecom"],
            minio_tool=mock_tools["minio"]
        )
    
    @pytest.fixture
    def skill_no_tools(self):
        """创建无工具的 Skill 实例"""
        return EmergencyGuideSkill()
    
    @pytest.mark.asyncio
    async def test_invoke_power_outage(self, skill, mock_tools):
        """测试停电故障应急处理"""
        context = SkillContext(
            params={
                "emergency_type": "power_outage",
                "location": "XX街道XX号",
                "severity": "重大",
                "description": "变压器冒烟"
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is True
        assert "停电故障" in result.response
        assert "⚡" in result.response
        assert "一级响应" in result.response
        assert result.data["action_plan"] is not None
        assert len(result.data["sensitive_customers"]) == 2
        assert "doc_url" in result.data
        
        # 验证工具调用
        mock_tools["pg"].query.assert_called_once()
        mock_tools["wecom"].send_text.assert_called()
        mock_tools["minio"].upload_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invoke_equipment_fault(self, skill):
        """测试设备故障应急处理"""
        context = SkillContext(
            params={
                "emergency_type": "equipment_fault",
                "location": "XX变电站",
                "severity": "严重",
                "description": "主变油温异常"
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is True
        assert "设备故障" in result.response
        assert "🔧" in result.response
        assert result.data["action_plan"] is not None
    
    @pytest.mark.asyncio
    async def test_invoke_safety_incident(self, skill):
        """测试安全事故应急处理"""
        context = SkillContext(
            params={
                "emergency_type": "safety_incident",
                "location": "XX施工现场",
                "severity": "重大",
                "description": "触电事故"
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is True
        assert "安全事故" in result.response
        assert "⚠️" in result.response
    
    @pytest.mark.asyncio
    async def test_invoke_customer_complaint(self, skill):
        """测试敏感客户投诉处理"""
        context = SkillContext(
            params={
                "emergency_type": "customer_complaint",
                "location": "XX医院",
                "severity": "紧急",
                "description": "多次停电投诉"
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is True
        assert "敏感客户投诉" in result.response
        assert "📞" in result.response
    
    @pytest.mark.asyncio
    async def test_invoke_invalid_type(self, skill):
        """测试无效的应急类型"""
        context = SkillContext(
            params={
                "emergency_type": "invalid_type",
                "location": "XX街道",
                "severity": "一般"
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is False
        assert "不支持的应急类型" in result.response
    
    @pytest.mark.asyncio
    async def test_invoke_with_photos(self, skill, mock_tools):
        """测试带照片的应急处理"""
        context = SkillContext(
            params={
                "emergency_type": "power_outage",
                "location": "XX街道",
                "severity": "重大",
                "description": "设备故障",
                "photos": [
                    "http://minio:9000/photos/1.jpg",
                    "http://minio:9000/photos/2.jpg",
                    "http://minio:9000/photos/3.jpg",
                    "http://minio:9000/photos/4.jpg"  # 超过3张，应该只分析前3张
                ]
            }
        )
        
        result = await skill.invoke(context)
        
        assert result.success is True
        # 验证只分析了3张照片
        assert mock_tools["kimi"].analyze_image.call_count == 3
    
    @pytest.mark.asyncio
    async def test_invoke_without_tools(self, skill_no_tools):
        """测试无工具情况下的应急处理"""
        context = SkillContext(
            params={
                "emergency_type": "power_outage",
                "location": "XX街道",
                "severity": "一般",
                "description": "普通故障"
            }
        )
        
        result = await skill_no_tools.invoke(context)
        
        assert result.success is True
        assert "停电故障" in result.response
        # 无工具时敏感客户列表应为空
        assert result.data["sensitive_customers"] == []
    
    @pytest.mark.asyncio
    async def test_analyze_emergency_with_kimi(self, skill):
        """测试使用KIMI进行应急分析"""
        analysis = await skill._analyze_emergency(
            emergency_type="power_outage",
            location="XX街道",
            description="变压器冒烟",
            photos=[]
        )
        
        assert "impact_scope" in analysis
        assert "possible_causes" in analysis
        assert "urgency_level" in analysis
    
    @pytest.mark.asyncio
    async def test_analyze_emergency_without_kimi(self, skill_no_tools):
        """测试无KIMI时的应急分析"""
        analysis = await skill_no_tools._analyze_emergency(
            emergency_type="power_outage",
            location="XX街道",
            description="设备故障",
            photos=[]
        )
        
        assert "impact_scope" in analysis
        assert "suggested_actions" in analysis
        # 应该有默认的分析结果
        assert analysis["impact_scope"] == "影响范围：XX街道及周边区域"
    
    @pytest.mark.asyncio
    async def test_generate_action_plan(self, skill):
        """测试应急方案生成"""
        analysis = {
            "suggested_actions": ["措施1", "措施2", "措施3"],
            "required_resources": ["资源1", "资源2"]
        }
        
        # 测试重大级别
        plan = await skill._generate_action_plan(
            emergency_type="power_outage",
            severity="重大",
            analysis=analysis
        )
        
        assert "escalation_required" in plan
        assert plan["escalation_required"] is True
        assert plan["priority"] == "最高"
        assert "公司领导" in plan["contacts"]
        assert "应急办" in plan["contacts"]
        
        # 测试较大级别
        plan = await skill._generate_action_plan(
            emergency_type="power_outage",
            severity="较大",
            analysis=analysis
        )
        
        assert plan["escalation_required"] is True
        assert plan["priority"] == "高"
        assert "部门领导" in plan["contacts"]
        
        # 测试一般级别
        plan = await skill._generate_action_plan(
            emergency_type="power_outage",
            severity="一般",
            analysis=analysis
        )
        
        assert plan["escalation_required"] is False
        assert plan["priority"] == "正常"
    
    @pytest.mark.asyncio
    async def test_identify_sensitive_customers(self, skill, mock_tools):
        """测试敏感客户识别"""
        customers = await skill._identify_sensitive_customers("XX街道")
        
        assert len(customers) == 2
        assert customers[0]["name"] == "中心医院"
        assert customers[0]["type"] == "hospital"
        assert customers[1]["complaint_count"] == 3
        
        # 验证查询参数
        mock_tools["pg"].query.assert_called_with(
            """
                SELECT 
                    id, name, type, location, 
                    is_important, complaint_count, 
                    contact_phone, wecom_id, manager_contact
                FROM users 
                WHERE location LIKE $1 
                AND (is_important = true OR complaint_count > 0)
                ORDER BY is_important DESC, complaint_count DESC
                """,
            "%XX街道%"
        )
    
    @pytest.mark.asyncio
    async def test_identify_sensitive_customers_no_pg(self, skill_no_tools):
        """测试无数据库时的敏感客户识别"""
        customers = await skill_no_tools._identify_sensitive_customers("XX街道")
        
        assert customers == []
    
    @pytest.mark.asyncio
    async def test_send_care_messages(self, skill, mock_tools):
        """测试发送关怀消息"""
        customers = [
            {
                "name": "中心医院",
                "type": "hospital",
                "wecom_id": "user_001",
                "manager_contact": "138-xxxx-xxxx"
            },
            {
                "name": "张先生",
                "type": "default",
                "wecom_id": "user_002",
                "manager_contact": ""
            }
        ]
        
        await skill._send_care_messages(
            customers=customers,
            emergency_type="power_outage",
            location="XX街道",
            eta="2小时"
        )
        
        # 验证发送了2条消息
        assert mock_tools["wecom"].send_text.call_count == 2
        
        # 验证消息内容
        calls = mock_tools["wecom"].send_text.call_args_list
        # 第一条消息发给医院 - call_args[0]是positional args, call_args[1]是keyword args
        first_call = calls[0]
        assert "user_001" in first_call[0] or first_call[1].get('user_id') == 'user_001'
        # 检查消息内容在args或kwargs中
        message_content = str(first_call)  # 转换为字符串检查
        assert "医院" in message_content or "🏥" in message_content
        # 第二条消息发给普通用户
        second_call = calls[1]
        assert "user_002" in second_call[0] or second_call[1].get('user_id') == 'user_002'
    
    @pytest.mark.asyncio
    async def test_send_care_messages_no_wecom(self, skill_no_tools):
        """测试无企业微信时的关怀消息发送"""
        customers = [
            {"name": "用户1", "type": "default", "wecom_id": "user_001"}
        ]
        
        # 应该正常执行，不报错
        await skill_no_tools._send_care_messages(
            customers=customers,
            emergency_type="power_outage",
            location="XX街道",
            eta="1小时"
        )
    
    @pytest.mark.asyncio
    async def test_generate_emergency_doc(self, skill, mock_tools):
        """测试应急文档生成"""
        action_plan = {
            "immediate_actions": ["行动1", "行动2"],
            "contacts": ["抢修班"],
            "estimated_time": "2小时",
            "safety_precautions": ["注意安全"]
        }
        
        analysis = {
            "impact_scope": "大范围停电",
            "possible_causes": ["设备老化"]
        }
        
        doc_url = await skill._generate_emergency_doc(
            emergency_type="power_outage",
            location="XX街道",
            action_plan=action_plan,
            photos=[],
            analysis=analysis
        )
        
        assert "minio:9000" in doc_url
        mock_tools["minio"].upload_text.assert_called_once()
        
        # 验证文档内容
        call_args = mock_tools["minio"].upload_text.call_args
        content = call_args[1]["content"]
        assert "停电故障" in content
        assert "XX街道" in content
        assert "行动1" in content
        assert "大范围停电" in content
    
    @pytest.mark.asyncio
    async def test_generate_emergency_doc_no_minio(self, skill_no_tools):
        """测试无MinIO时的文档生成"""
        action_plan = {
            "immediate_actions": ["行动1"],
            "contacts": ["抢修班"],
            "estimated_time": "1小时"
        }
        
        analysis = {"impact_scope": "局部停电"}
        
        doc_content = await skill_no_tools._generate_emergency_doc(
            emergency_type="power_outage",
            location="XX街道",
            action_plan=action_plan,
            photos=[],
            analysis=analysis
        )
        
        # 应该返回文档内容字符串
        assert "停电故障" in doc_content
        assert "XX街道" in doc_content
    
    def test_build_response(self, skill):
        """测试回复消息构建"""
        action_plan = {
            "immediate_actions": ["行动1", "行动2"],
            "contacts": ["抢修班", "调度中心"],
            "estimated_time": "2小时"
        }
        
        sensitive_customers = [
            {"name": "中心医院", "type": "hospital"}
        ]
        
        response = skill._build_response(
            emergency_type="power_outage",
            severity="重大",
            action_plan=action_plan,
            sensitive_customers=sensitive_customers,
            location="XX街道"
        )
        
        assert "停电故障" in response
        assert "⚡" in response
        assert "重大" in response
        assert "一级响应" in response
        assert "行动1" in response
        assert "行动2" in response
        assert "抢修班" in response
        assert "已识别 1 位敏感客户" in response
    
    def test_parse_json_response(self, skill):
        """测试JSON响应解析"""
        # 测试带JSON代码块的响应
        response = '''```json
        {"key": "value", "number": 123}
        ```'''
        result = skill._parse_json_response(response)
        assert result["key"] == "value"
        assert result["number"] == 123
        
        # 测试带普通代码块的响应
        response = '''```
        {"key": "value"}
        ```'''
        result = skill._parse_json_response(response)
        assert result["key"] == "value"
        
        # 测试纯JSON响应
        response = '{"key": "value"}'
        result = skill._parse_json_response(response)
        assert result["key"] == "value"
        
        # 测试无效的JSON响应
        response = "这不是JSON"
        result = skill._parse_json_response(response)
        assert "raw_response" in result
        assert result["raw_response"] == "这不是JSON"
    
    @pytest.mark.asyncio
    async def test_health_check(self, skill):
        """测试健康检查"""
        result = await skill.health_check()
        assert result is True
    
    def test_get_stats(self, skill):
        """测试获取统计信息"""
        stats = skill.get_stats()
        
        assert stats["skill"] == "emergency_guide"
        assert stats["version"] == "1.0.0"
        assert "supported_types" in stats
        assert len(stats["supported_types"]) == 4
        assert "kimi_available" in stats
        assert "pg_available" in stats
        assert "wecom_available" in stats
        assert "minio_available" in stats
    
    def test_emergency_types_count(self):
        """测试应急类型数量"""
        templates = EmergencyTemplates()
        assert len(templates.EMERGENCY_TYPES) == 4
        assert "power_outage" in templates.EMERGENCY_TYPES
        assert "equipment_fault" in templates.EMERGENCY_TYPES
        assert "safety_incident" in templates.EMERGENCY_TYPES
        assert "customer_complaint" in templates.EMERGENCY_TYPES
    
    def test_action_plan_severity_adjustments(self):
        """测试不同严重程度的方案调整"""
        asyncio.run(self._test_action_plan_severity())
    
    async def _test_action_plan_severity(self):
        """异步测试方案调整"""
        skill = EmergencyGuideSkill()
        
        # 测试各种严重程度
        for severity in ["重大", "危急", "紧急", "较大", "严重", "重要", "一般"]:
            plan = await skill._generate_action_plan(
                emergency_type="power_outage",
                severity=severity,
                analysis={}
            )
            
            assert "immediate_actions" in plan
            assert "contacts" in plan
            
            if severity in ["重大", "危急", "紧急"]:
                assert plan["priority"] == "最高"
                assert plan["escalation_required"] is True
            elif severity in ["较大", "严重", "重要"]:
                assert plan["priority"] == "高"
                assert plan["escalation_required"] is True
            else:
                assert plan["priority"] == "正常"
                assert plan["escalation_required"] is False


class TestSkillResult:
    """测试 SkillResult 数据类"""
    
    def test_skill_result_default_values(self):
        """测试 SkillResult 默认值"""
        result = SkillResult(
            response="测试响应",
            data={"key": "value"}
        )
        
        assert result.response == "测试响应"
        assert result.data == {"key": "value"}
        assert result.success is True
        assert result.error is None
    
    def test_skill_result_error(self):
        """测试 SkillResult 错误状态"""
        result = SkillResult(
            response="处理失败",
            data={},
            success=False,
            error="错误信息"
        )
        
        assert result.success is False
        assert result.error == "错误信息"


class TestSkillContext:
    """测试 SkillContext 数据类"""
    
    def test_skill_context_creation(self):
        """测试 SkillContext 创建"""
        context = SkillContext(
            params={"key": "value"},
            user_id="user_001",
            session_id="session_001"
        )
        
        assert context.params == {"key": "value"}
        assert context.user_id == "user_001"
        assert context.session_id == "session_001"
        assert isinstance(context.timestamp, datetime)
    
    def test_skill_context_defaults(self):
        """测试 SkillContext 默认值"""
        context = SkillContext(params={})
        
        assert context.params == {}
        assert context.user_id is None
        assert context.session_id is None
        assert isinstance(context.timestamp, datetime)


# 集成测试
class TestEmergencyGuideIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建模拟工具 - 使用 patch 方式避免协程序列化问题
        from unittest.mock import patch, AsyncMock
        
        kimi = AsyncMock()
        kimi.chat = AsyncMock(return_value='{"impact_scope": "大范围停电", "possible_causes": ["设备故障"], "urgency_level": "高", "suggested_actions": ["立即抢修"], "required_resources": ["抢修车"]}')
        kimi.analyze_image = AsyncMock(return_value={"description": "变压器故障", "success": True})
        
        pg = AsyncMock()
        pg.query = AsyncMock(return_value=[
            {
                "id": 1,
                "name": "中心医院",
                "type": "hospital",
                "location": "XX街道",
                "is_important": True,
                "complaint_count": 0,
                "contact_phone": "1234567890",
                "wecom_id": "user_001",
                "manager_contact": "138-xxxx-xxxx"
            }
        ])
        
        wecom = AsyncMock()
        wecom.send_text = AsyncMock(return_value={"errcode": 0})
        
        minio = AsyncMock()
        minio.upload_text = AsyncMock(return_value="http://minio:9000/emergency-docs/doc.md")
        
        # 创建 Skill
        skill = EmergencyGuideSkill(
            kimi_tool=kimi,
            pg_tool=pg,
            wecom_tool=wecom,
            minio_tool=minio
        )
        
        # 执行完整流程 - 不使用照片避免序列化问题
        context = SkillContext(
            params={
                "emergency_type": "power_outage",
                "location": "XX街道XX号配电房",
                "severity": "重大",
                "description": "变压器故障",
                "photos": []  # 空列表避免照片分析
            }
        )
        
        result = await skill.invoke(context)
        
        # 验证结果
        assert result.success is True
        assert result.data["action_plan"] is not None
        assert len(result.data["sensitive_customers"]) == 1
        assert result.data["sensitive_customers"][0]["name"] == "中心医院"
        assert "doc_url" in result.data
        assert len(result.data["contacts_to_notify"]) > 0
        
        # 验证所有工具都被调用
        # kimi.analyze_image 只有在有照片时才会被调用，这里我们没有照片
        kimi.chat.assert_called_once()  # KIMI chat 被调用进行应急分析
        pg.query.assert_called_once()
        wecom.send_text.assert_called_once()
        minio.upload_text.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
