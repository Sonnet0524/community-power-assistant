"""
EmergencyGuide Skill - 应急处置 Skill

提供应急方案推送和现场处置指引，支持：
- 4种应急类型（停电故障、设备故障、安全事故、敏感客户投诉）
- 敏感客户自动识别
- 应急方案自动生成
- 关怀消息自动发送
- 应急文档生成

Usage:
    from src.skills.emergency_guide.skill import EmergencyGuideSkill
    
    skill = EmergencyGuideSkill()
    result = await skill.invoke({
        "emergency_type": "power_outage",
        "location": "XX街道XX号",
        "severity": "重大",
        "description": "变压器冒烟"
    })
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .templates import EmergencyTemplates


@dataclass
class SkillContext:
    """Skill 上下文"""
    params: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SkillResult:
    """Skill 结果"""
    response: str
    data: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class EmergencyGuideSkill:
    """应急处置 Skill
    
    提供应急处置方案和现场指引，支持：
    - 4种应急类型（停电故障、设备故障、安全事故、敏感客户投诉）
    - 敏感客户自动识别
    - 应急方案自动生成
    - 关怀消息自动发送
    - 应急文档生成
    
    Attributes:
        NAME: Skill 名称
        DESCRIPTION: Skill 描述
        VERSION: Skill 版本
    """
    
    NAME = "emergency_guide"
    DESCRIPTION = "提供应急处置方案和现场指引"
    VERSION = "1.0.0"
    
    def __init__(
        self,
        kimi_tool=None,
        pg_tool=None,
        wecom_tool=None,
        minio_tool=None
    ):
        """初始化 EmergencyGuide Skill
        
        Args:
            kimi_tool: KIMI Tool 实例（用于AI分析）
            pg_tool: PostgreSQL Tool 实例（用于数据查询）
            wecom_tool: 企业微信 Tool 实例（用于发送消息）
            minio_tool: MinIO Tool 实例（用于文件存储）
        """
        self.kimi = kimi_tool
        self.pg = pg_tool
        self.wecom = wecom_tool
        self.minio = minio_tool
        self.templates = EmergencyTemplates()
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """处理应急事件
        
        Args:
            context: Skill 上下文，包含：
                - emergency_type: 应急类型
                - location: 地点
                - severity: 严重程度
                - description: 描述
                - photos: 现场照片列表
                
        Returns:
            SkillResult: 包含回复消息、行动计划、敏感客户列表、文档URL
        """
        try:
            # 提取参数
            emergency_type = context.params.get("emergency_type", "")
            location = context.params.get("location", "")
            severity = context.params.get("severity", "一般")
            description = context.params.get("description", "")
            photos = context.params.get("photos", [])
            
            # 验证应急类型
            if emergency_type not in self.templates.EMERGENCY_TYPES:
                return SkillResult(
                    response=f"不支持的应急类型: {emergency_type}",
                    data={},
                    success=False,
                    error=f"Invalid emergency_type: {emergency_type}"
                )
            
            # 分析应急情况
            analysis = await self._analyze_emergency(
                emergency_type, location, description, photos
            )
            
            # 生成应急方案
            action_plan = await self._generate_action_plan(
                emergency_type, severity, analysis
            )
            
            # 识别敏感客户
            sensitive_customers = await self._identify_sensitive_customers(location)
            
            # 向敏感客户发送关怀消息
            if sensitive_customers:
                await self._send_care_messages(
                    sensitive_customers, 
                    emergency_type, 
                    location,
                    action_plan.get("estimated_time", "待定")
                )
            
            # 生成应急文档
            doc_url = await self._generate_emergency_doc(
                emergency_type, location, action_plan, photos, analysis
            )
            
            # 构建回复
            response = self._build_response(
                emergency_type, severity, action_plan, sensitive_customers, location
            )
            
            return SkillResult(
                response=response,
                data={
                    "action_plan": action_plan,
                    "sensitive_customers": sensitive_customers,
                    "doc_url": doc_url,
                    "contacts_to_notify": action_plan.get("contacts", []),
                    "analysis": analysis
                }
            )
            
        except Exception as e:
            return SkillResult(
                response=f"应急处理失败: {str(e)}",
                data={},
                success=False,
                error=str(e)
            )
    
    async def _analyze_emergency(
        self,
        emergency_type: str,
        location: str,
        description: str,
        photos: List[str]
    ) -> Dict[str, Any]:
        """分析应急情况
        
        使用KIMI分析应急情况，包括照片分析和综合评估
        
        Args:
            emergency_type: 应急类型
            location: 地点
            description: 描述
            photos: 照片URL列表
            
        Returns:
            分析结果字典
        """
        photo_analysis = []
        
        # 如果有照片，先分析照片
        if photos and self.kimi:
            for photo in photos[:3]:  # 最多分析3张
                try:
                    result = await self.kimi.analyze_image(
                        photo,
                        self.templates.get_analysis_prompt("photo_analysis")
                    )
                    photo_analysis.append(result.get("description", str(result)))
                except Exception as e:
                    photo_analysis.append(f"照片分析失败: {str(e)}")
        
        # 如果没有KIMI，返回基础分析
        if not self.kimi:
            return {
                "impact_scope": f"影响范围：{location}及周边区域",
                "possible_causes": ["待现场检查确认"],
                "urgency_level": "中",
                "suggested_actions": ["派遣抢修队伍", "现场安全检查"],
                "required_resources": ["抢修人员", "检测设备"],
                "photo_analysis": photo_analysis
            }
        
        # 使用KIMI进行综合分析
        prompt = self.templates.get_analysis_prompt(
            "emergency_analysis",
            emergency_type=self.templates.get_emergency_type(emergency_type).get("name", ""),
            location=location,
            description=description,
            photo_analysis=json.dumps(photo_analysis, ensure_ascii=False)
        )
        
        try:
            response = await self.kimi.chat([
                {"role": "system", "content": "你是电力应急处理专家"},
                {"role": "user", "content": prompt}
            ])
            
            return self._parse_json_response(response)
        except Exception as e:
            # 如果AI分析失败，返回默认分析
            return {
                "impact_scope": f"影响范围：{location}及周边区域",
                "possible_causes": [description or "待现场检查确认"],
                "urgency_level": "中",
                "suggested_actions": ["派遣抢修队伍", "现场安全检查"],
                "required_resources": ["抢修人员", "检测设备"],
                "error": str(e),
                "photo_analysis": photo_analysis
            }
    
    async def _generate_action_plan(
        self,
        emergency_type: str,
        severity: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成应急方案
        
        根据应急类型和严重程度生成具体的应急方案
        
        Args:
            emergency_type: 应急类型
            severity: 严重程度
            analysis: 分析结果
            
        Returns:
            应急方案字典
        """
        base_plan = self.templates.get_action_plan(emergency_type)
        
        if not base_plan:
            base_plan = {
                "immediate_actions": ["联系相关部门", "现场勘查"],
                "contacts": ["调度中心"],
                "estimated_time": "待定",
                "safety_precautions": ["注意人身安全"]
            }
        
        # 根据严重程度调整
        if severity in ["重大", "危急", "紧急"]:
            base_plan["contacts"] = base_plan.get("contacts", []) + ["公司领导", "应急办"]
            base_plan["escalation_required"] = True
            base_plan["priority"] = "最高"
        elif severity in ["较大", "严重", "重要"]:
            base_plan["contacts"] = base_plan.get("contacts", []) + ["部门领导"]
            base_plan["escalation_required"] = True
            base_plan["priority"] = "高"
        else:
            base_plan["escalation_required"] = False
            base_plan["priority"] = "正常"
        
        # 添加AI分析建议的措施
        if "suggested_actions" in analysis:
            suggested = analysis["suggested_actions"]
            if isinstance(suggested, list) and len(suggested) > 0:
                # 合并建议到即时行动
                existing_actions = base_plan.get("immediate_actions", [])
                base_plan["immediate_actions"] = list(dict.fromkeys(
                    existing_actions + suggested[:3]
                ))
        
        # 添加所需资源
        if "required_resources" in analysis:
            base_plan["required_resources"] = analysis["required_resources"]
        
        return base_plan
    
    async def _identify_sensitive_customers(self, location: str) -> List[Dict[str, Any]]:
        """识别敏感客户
        
        从数据库查询该区域的敏感客户
        标准：医院、学校、重要企业、历史投诉客户
        
        Args:
            location: 地点
            
        Returns:
            敏感客户列表
        """
        if not self.pg:
            # 如果没有数据库连接，返回模拟数据用于测试
            return []
        
        try:
            # 从数据库查询敏感客户
            customers = await self.pg.query(
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
                f"%{location}%"
            )
            
            return [dict(customer) for customer in customers]
        except Exception as e:
            # 查询失败返回空列表
            return []
    
    async def _send_care_messages(
        self,
        customers: List[Dict[str, Any]],
        emergency_type: str,
        location: str,
        eta: str
    ):
        """发送关怀消息
        
        向敏感客户发送关怀消息
        
        Args:
            customers: 客户列表
            emergency_type: 应急类型
            location: 地点
            eta: 预计恢复时间
        """
        if not self.wecom:
            return
        
        emergency_info = {
            "type": self.templates.get_emergency_type(emergency_type).get("name", ""),
            "location": location,
            "eta": eta
        }
        
        for customer in customers:
            try:
                message = self._get_care_message(customer, emergency_info)
                wecom_id = customer.get("wecom_id")
                if wecom_id:
                    await self.wecom.send_text(wecom_id, message)
            except Exception as e:
                # 发送失败继续处理下一个
                continue
    
    def _get_care_message(
        self,
        customer: Dict[str, Any],
        emergency_info: Dict[str, str]
    ) -> str:
        """获取关怀消息
        
        根据客户类型生成相应的关怀消息
        
        Args:
            customer: 客户信息
            emergency_info: 应急信息
            
        Returns:
            关怀消息内容
        """
        customer_type = customer.get("type", "default")
        customer_name = customer.get("name", "用户")
        manager_contact = customer.get("manager_contact", "95598")
        
        return self.templates.get_customer_care_message(
            customer_type=customer_type,
            customer_name=customer_name,
            location=emergency_info["location"],
            emergency_type=emergency_info["type"],
            eta=emergency_info["eta"],
            manager_contact=manager_contact
        )
    
    async def _generate_emergency_doc(
        self,
        emergency_type: str,
        location: str,
        action_plan: Dict[str, Any],
        photos: List[str],
        analysis: Dict[str, Any]
    ) -> str:
        """生成应急文档
        
        生成应急处理的详细文档
        
        Args:
            emergency_type: 应急类型
            location: 地点
            action_plan: 应急方案
            photos: 照片列表
            analysis: 分析结果
            
        Returns:
            文档URL
        """
        try:
            # 构建文档内容
            doc_content = self._build_doc_content(
                emergency_type, location, action_plan, analysis
            )
            
            # 如果有MinIO，上传文档
            if self.minio:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"emergency_{emergency_type}_{timestamp}.md"
                
                # 上传文档
                url = await self.minio.upload_text(
                    bucket="emergency-docs",
                    key=filename,
                    content=doc_content,
                    content_type="text/markdown"
                )
                
                return url
            
            # 如果没有MinIO，返回内容本身
            return doc_content
            
        except Exception as e:
            return f"文档生成失败: {str(e)}"
    
    def _build_doc_content(
        self,
        emergency_type: str,
        location: str,
        action_plan: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """构建文档内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emergency_name = self.templates.get_emergency_type(emergency_type).get("name", emergency_type)
        
        doc = f"""# 应急处置方案

## 基本信息

- **事件类型**：{emergency_name}
- **发生地点**：{location}
- **报告时间**：{timestamp}
- **响应级别**：{action_plan.get('priority', '正常')}

## 影响范围评估

{analysis.get('impact_scope', '待评估')}

## 可能原因

"""
        
        causes = analysis.get('possible_causes', [])
        if causes:
            for cause in causes:
                doc += f"- {cause}\n"
        else:
            doc += "- 待现场检查确认\n"
        
        doc += f"""

## 即时行动

"""
        
        actions = action_plan.get('immediate_actions', [])
        for i, action in enumerate(actions, 1):
            doc += f"{i}. {action}\n"
        
        doc += f"""

## 安全注意事项

"""
        
        precautions = action_plan.get('safety_precautions', [])
        if precautions:
            for precaution in precautions:
                doc += f"- {precaution}\n"
        else:
            doc += "- 注意人身安全\n"
        
        doc += f"""

## 联系人

{', '.join(action_plan.get('contacts', []))}

## 预计处理时间

{action_plan.get('estimated_time', '待定')}

## 所需资源

"""
        
        resources = action_plan.get('required_resources', [])
        if resources:
            for resource in resources:
                doc += f"- {resource}\n"
        else:
            doc += "- 待确认\n"
        
        doc += f"""

---

*此文档由 EmergencyGuide Skill 自动生成*
"""
        
        return doc
    
    def _build_response(
        self,
        emergency_type: str,
        severity: str,
        action_plan: Dict[str, Any],
        sensitive_customers: List[Dict[str, Any]],
        location: str
    ) -> str:
        """构建回复消息
        
        构建给用户看的应急响应消息
        
        Args:
            emergency_type: 应急类型
            severity: 严重程度
            action_plan: 应急方案
            sensitive_customers: 敏感客户列表
            location: 地点
            
        Returns:
            回复消息
        """
        emergency_info = self.templates.get_emergency_type(emergency_type)
        emergency_name = emergency_info.get("name", emergency_type)
        icon = emergency_info.get("icon", "🚨")
        response_level = self.templates.get_response_level(severity)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建行动列表
        actions_text = ""
        for i, action in enumerate(action_plan.get("immediate_actions", []), 1):
            actions_text += f"{i}. {action}\n"
        
        # 敏感客户信息
        sensitive_info = ""
        if sensitive_customers:
            sensitive_info = f"**敏感客户**：已识别 {len(sensitive_customers)} 位敏感客户，已自动发送关怀消息。\n\n"
        
        return self.templates.build_notification(
            "emergency_start",
            emergency_name=emergency_name,
            icon=icon,
            severity=severity,
            response_level=response_level,
            location=location,
            timestamp=timestamp,
            actions=actions_text,
            contacts=', '.join(action_plan.get("contacts", [])),
            estimated_time=action_plan.get("estimated_time", "待定"),
            sensitive_customers_info=sensitive_info
        )
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 响应
        
        从AI响应中提取JSON数据
        
        Args:
            response: AI响应文本
            
        Returns:
            解析后的字典
        """
        try:
            # 查找JSON块
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            # 如果不是JSON，返回包含原始响应的字典
            return {"raw_response": response}
    
    async def health_check(self) -> bool:
        """健康检查
        
        检查 Skill 是否正常工作
        
        Returns:
            True 表示健康
        """
        try:
            # 检查必要的模板是否加载
            if not self.templates.EMERGENCY_TYPES:
                return False
            
            if not self.templates.ACTION_PLAN_TEMPLATES:
                return False
            
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取 Skill 统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "skill": self.NAME,
            "version": self.VERSION,
            "supported_types": list(self.templates.EMERGENCY_TYPES.keys()),
            "kimi_available": self.kimi is not None,
            "pg_available": self.pg is not None,
            "wecom_available": self.wecom is not None,
            "minio_available": self.minio is not None
        }


# 导出
__all__ = ["EmergencyGuideSkill", "SkillContext", "SkillResult"]
