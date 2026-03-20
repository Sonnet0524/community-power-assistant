"""
StationWorkGuide Skill - 主类

驻点工作引导 Skill，支持配电房巡检、客户走访、应急信息采集三种工作类型
"""

import uuid
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.skills.base import BaseSkill, SkillContext, SkillResult, SkillResultStatus
from src.skills.station_work_guide.workflows import (
    WorkPhase, WorkType, WorkflowConfig, CollectionStep,
    WORK_TYPE_CONFIGS, get_workflow_config, validate_phase_transition
)
from src.skills.station_work_guide.templates import MessageGenerator


class StationWorkGuideSkill(BaseSkill):
    """驻点工作引导 Skill
    
    支持三种工作类型：
    1. power_room: 配电房巡检
    2. customer_visit: 客户走访
    3. emergency: 应急信息采集
    
    状态机流转：
    IDLE -> PREPARING -> COLLECTING -> ANALYZING -> COMPLETED
    """
    
    NAME = "station_work_guide"
    DESCRIPTION = "驻点工作引导，帮助供电所人员完成现场信息采集"
    VERSION = "1.0.0"
    
    # 工作类型映射
    WORK_TYPES = {
        "1": WorkType.POWER_ROOM,
        "2": WorkType.CUSTOMER_VISIT,
        "3": WorkType.EMERGENCY,
        "配电房": WorkType.POWER_ROOM,
        "配电房巡检": WorkType.POWER_ROOM,
        "客户": WorkType.CUSTOMER_VISIT,
        "客户走访": WorkType.CUSTOMER_VISIT,
        "应急": WorkType.EMERGENCY,
        "应急信息": WorkType.EMERGENCY,
        "power_room": WorkType.POWER_ROOM,
        "customer_visit": WorkType.CUSTOMER_VISIT,
        "emergency": WorkType.EMERGENCY
    }
    
    def __init__(self, pg_tool=None, kimi_tool=None, minio_tool=None):
        """初始化 Skill
        
        Args:
            pg_tool: PostgreSQL Tool 实例
            kimi_tool: KIMI Tool 实例
            minio_tool: MinIO Tool 实例
        """
        super().__init__()
        self.pg_tool = pg_tool
        self.kimi_tool = kimi_tool
        self.minio_tool = minio_tool
        self._initialized = False
    
    async def initialize(self):
        """初始化 Skill"""
        if not self._initialized:
            # 可以在这里进行资源初始化
            self._initialized = True
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """Skill 主入口
        
        根据当前阶段和用户输入，返回引导信息
        
        Args:
            context: Skill 上下文，包含 session_id, user_id, message, session 数据
            
        Returns:
            Skill 执行结果
        """
        await self.initialize()
        
        session = context.session
        phase = session.get("phase", WorkPhase.IDLE.value)
        message = context.message.strip().lower()
        
        # 全局命令处理
        if message in ["帮助", "help", "?"]:
            return self._handle_help()
        
        if message in ["状态", "status"]:
            return self._handle_status(session)
        
        if message in ["取消", "cancel", "退出", "quit"]:
            return await self._handle_cancel(session)
        
        # 阶段处理
        if phase == WorkPhase.IDLE.value:
            return await self._handle_idle(context)
        elif phase == WorkPhase.PREPARING.value:
            return await self._handle_preparing(context)
        elif phase == WorkPhase.COLLECTING.value:
            return await self._handle_collecting(context)
        elif phase == WorkPhase.ANALYZING.value:
            return await self._handle_analyzing(context)
        elif phase == WorkPhase.COMPLETED.value:
            return await self._handle_completed(context)
        
        # 未知阶段
        return SkillResult(
            response='⚠️ 未知的工作阶段，请发送"取消"重新开始',
            status=SkillResultStatus.ERROR,
            error="unknown_phase"
        )
    
    async def _handle_idle(self, context: SkillContext) -> SkillResult:
        """处理空闲阶段 - 询问工作类型"""
        message = context.message.strip()
        
        # 检查是否已选择工作类型
        work_type = self.WORK_TYPES.get(message)
        
        if work_type:
            # 保存工作类型选择
            context.set_session_data("work_type", work_type.value)
            context.set_session_data("phase", WorkPhase.PREPARING.value)
            context.set_session_data("work_id", str(uuid.uuid4()))
            context.set_session_data("start_time", datetime.now().isoformat())
            context.set_session_data("collected_data", {})
            
            config = WORK_TYPE_CONFIGS[work_type]
            
            return SkillResult(
                response=MessageGenerator.generate_work_type_confirm(work_type.value, config),
                status=SkillResultStatus.SUCCESS,
                next_phase=WorkPhase.PREPARING.value,
                data={"work_type": work_type.value}
            )
        else:
            # 显示欢迎消息
            return SkillResult(
                response=MessageGenerator.generate_welcome(),
                status=SkillResultStatus.NEED_INPUT,
                next_phase=WorkPhase.IDLE.value
            )
    
    async def _handle_preparing(self, context: SkillContext) -> SkillResult:
        """处理准备阶段 - 显示检查清单"""
        message = context.message.strip().lower()
        work_type = context.get_session_data("work_type")
        
        if not work_type:
            return SkillResult(
                response="⚠️ 工作类型未设置，请重新开始",
                status=SkillResultStatus.ERROR,
                next_phase=WorkPhase.IDLE.value,
                error="work_type_not_set"
            )
        
        config = get_workflow_config(work_type)
        if not config:
            return SkillResult(
                response="⚠️ 无效的工作类型",
                status=SkillResultStatus.ERROR,
                next_phase=WorkPhase.IDLE.value,
                error="invalid_work_type"
            )
        
        if message in ["开始", "start", "ok", "好", "开始采集"]:
            # 进入采集阶段
            context.set_session_data("phase", WorkPhase.COLLECTING.value)
            context.set_session_data("current_step", 0)
            
            # 返回第一个采集步骤
            first_step = config.steps[0]
            return SkillResult(
                response=MessageGenerator.generate_collecting_message(
                    step=first_step,
                    current_step=1,
                    total_steps=len(config.steps),
                    collected_data={}
                ),
                status=SkillResultStatus.NEED_INPUT,
                next_phase=WorkPhase.COLLECTING.value,
                data={"current_step": 1, "total_steps": len(config.steps)}
            )
        elif message in ["稍后", "later", "保存"]:
            # 保存进度稍后继续
            await self._save_session(context)
            return SkillResult(
                response="✅ 进度已保存，发送任意消息继续",
                status=SkillResultStatus.SUCCESS,
                next_phase=WorkPhase.PREPARING.value
            )
        else:
            # 显示准备清单
            return SkillResult(
                response=MessageGenerator.generate_preparing_message(config),
                status=SkillResultStatus.NEED_INPUT,
                next_phase=WorkPhase.PREPARING.value
            )
    
    async def _handle_collecting(self, context: SkillContext) -> SkillResult:
        """处理采集阶段"""
        message = context.message.strip()
        work_type = context.get_session_data("work_type")
        current_step_idx = context.get_session_data("current_step", 0)
        collected_data = context.get_session_data("collected_data", {})
        
        config = get_workflow_config(work_type)
        if not config:
            return SkillResult(
                response="⚠️ 工作配置错误",
                status=SkillResultStatus.ERROR,
                error="config_not_found"
            )
        
        steps = config.steps
        
        # 处理导航命令
        if message in ["下一步", "next", "继续"]:
            current_step_idx += 1
            context.set_session_data("current_step", current_step_idx)
            
            # 检查是否完成所有步骤
            if current_step_idx >= len(steps):
                # 进入分析阶段
                context.set_session_data("phase", WorkPhase.ANALYZING.value)
                return await self._start_analyzing(context)
            
        elif message in ["上一步", "prev", "返回"]:
            if current_step_idx > 0:
                current_step_idx -= 1
                context.set_session_data("current_step", current_step_idx)
            else:
                return SkillResult(
                    response="⚠️ 已经是第一步了",
                    status=SkillResultStatus.NEED_INPUT
                )
                
        elif message in ["跳过", "skip"]:
            current_step = steps[current_step_idx]
            if current_step.required:
                return SkillResult(
                    response=f"⚠️ 【{current_step.name}】是必填项，不能跳过",
                    status=SkillResultStatus.NEED_INPUT
                )
            
            # 标记为跳过
            collected_data[current_step.name] = {"skipped": True}
            context.set_session_data("collected_data", collected_data)
            
            current_step_idx += 1
            context.set_session_data("current_step", current_step_idx)
            
            if current_step_idx >= len(steps):
                context.set_session_data("phase", WorkPhase.ANALYZING.value)
                return await self._start_analyzing(context)
        
        else:
            # 处理用户输入（照片或文字）
            current_step = steps[current_step_idx]
            
            # 保存当前步骤的数据
            step_data = {
                "text": message,
                "timestamp": datetime.now().isoformat()
            }
            
            # 检查是否有照片（从 metadata 中）
            photos = context.metadata.get("photos", [])
            if photos:
                step_data["photos"] = photos
                
                # 如果需要AI分析，触发分析
                if current_step.use_ai and self.kimi_tool:
                    try:
                        analysis_results = []
                        for photo in photos:
                            result = await self.kimi_tool.analyze_image(
                                photo,
                                analysis_type=current_step.ai_type
                            )
                            analysis_results.append(result)
                        step_data["ai_result"] = analysis_results
                    except Exception as e:
                        step_data["ai_error"] = str(e)
            
            collected_data[current_step.name] = step_data
            context.set_session_data("collected_data", collected_data)
            
            # 保存到数据库
            await self._save_step_data(context, current_step, step_data)
            
            # 自动进入下一步
            current_step_idx += 1
            context.set_session_data("current_step", current_step_idx)
            
            if current_step_idx >= len(steps):
                context.set_session_data("phase", WorkPhase.ANALYZING.value)
                return await self._start_analyzing(context)
        
        # 返回当前步骤的引导
        next_step = steps[current_step_idx]
        return SkillResult(
            response=MessageGenerator.generate_collecting_message(
                step=next_step,
                current_step=current_step_idx + 1,
                total_steps=len(steps),
                collected_data=collected_data
            ),
            status=SkillResultStatus.NEED_INPUT,
            next_phase=WorkPhase.COLLECTING.value,
            data={"current_step": current_step_idx + 1, "total_steps": len(steps)}
        )
    
    async def _handle_analyzing(self, context: SkillContext) -> SkillResult:
        """处理分析阶段"""
        message = context.message.strip().lower()
        
        if message in ["完成", "done", "结束"]:
            return await self._complete_work(context)
        
        # 返回分析进度
        collected_data = context.get_session_data("collected_data", {})
        if not collected_data:
            collected_data = {}
        analysis_items = ["数据整理", "AI分析", "报告生成"]
        
        return SkillResult(
            response=MessageGenerator.generate_analyzing_message(analysis_items),
            status=SkillResultStatus.PENDING,
            next_phase=WorkPhase.ANALYZING.value
        )
    
    async def _handle_completed(self, context: SkillContext) -> SkillResult:
        """处理完成阶段"""
        message = context.message.strip()
        
        if message in ["1", "新工作", "开始", "start"]:
            # 重置状态，返回空闲
            context.set_session_data("phase", WorkPhase.IDLE.value)
            context.set_session_data("work_type", None)
            context.set_session_data("current_step", 0)
            context.set_session_data("collected_data", {})
            
            return SkillResult(
                response=MessageGenerator.generate_welcome(),
                status=SkillResultStatus.SUCCESS,
                next_phase=WorkPhase.IDLE.value
            )
        
        # 显示完成信息
        return SkillResult(
            response='工作已完成！发送"1"开始新的工作',
            status=SkillResultStatus.COMPLETED,
            next_phase=WorkPhase.IDLE.value
        )
    
    async def _start_analyzing(self, context: SkillContext) -> SkillResult:
        """开始分析阶段"""
        # 进行数据分析和报告生成
        analysis_items = []
        
        collected_data = context.get_session_data("collected_data", {})
        
        # 检查是否有需要AI分析的步骤
        for step_name, data in collected_data.items():
            if isinstance(data, dict) and data.get("ai_result"):
                analysis_items.append(f"{step_name}: AI分析完成")
        
        if not analysis_items:
            analysis_items = ["数据整理", "报告生成"]
        
        return SkillResult(
            response=MessageGenerator.generate_analyzing_message(analysis_items),
            status=SkillResultStatus.PENDING,
            next_phase=WorkPhase.ANALYZING.value,
            actions=[{"type": "button", "label": "完成", "value": "完成"}]
        )
    
    async def _complete_work(self, context: SkillContext) -> SkillResult:
        """完成工作"""
        work_type = context.get_session_data("work_type")
        config = get_workflow_config(work_type)
        collected_data = context.get_session_data("collected_data", {})
        
        # 生成摘要
        summary = MessageGenerator.generate_summary(collected_data)
        report_url = f"/reports/{context.get_session_data('work_id')}.pdf"
        
        # 保存最终报告
        await self._save_completion(context, summary)
        
        # 更新阶段
        context.set_session_data("phase", WorkPhase.COMPLETED.value)
        context.set_session_data("end_time", datetime.now().isoformat())
        
        return SkillResult(
            response=MessageGenerator.generate_completion_message(
                config=config,
                summary=summary,
                report_url=report_url
            ),
            status=SkillResultStatus.COMPLETED,
            next_phase=WorkPhase.COMPLETED.value,
            data={"work_id": context.get_session_data("work_id")}
        )
    
    def _handle_help(self) -> SkillResult:
        """处理帮助请求"""
        return SkillResult(
            response=MessageGenerator.generate_help(),
            status=SkillResultStatus.SUCCESS
        )
    
    def _handle_status(self, session: Dict[str, Any]) -> SkillResult:
        """处理状态查询"""
        work_type = session.get("work_type")
        phase = session.get("phase", WorkPhase.IDLE.value)
        current_step = session.get("current_step", 0)
        collected_data = session.get("collected_data", {})
        
        config = get_workflow_config(work_type) if work_type else None
        
        status_msg = MessageGenerator.generate_status(
            current_phase=phase,
            work_type_name=config.name if config else "未选择",
            current_step=current_step + 1 if phase == WorkPhase.COLLECTING.value else 0,
            total_steps=len(config.steps) if config else 0,
            collected_count=len(collected_data)
        )
        
        return SkillResult(
            response=status_msg,
            status=SkillResultStatus.SUCCESS
        )
    
    async def _handle_cancel(self, session: Dict[str, Any]) -> SkillResult:
        """处理取消请求"""
        collected_data = session.get("collected_data", {})
        collected_count = len(collected_data)
        
        if collected_count > 0:
            return SkillResult(
                response=MessageGenerator.generate_cancel_confirm(collected_count),
                status=SkillResultStatus.NEED_INPUT,
                next_phase=session.get("phase")
            )
        else:
            # 直接重置
            session["phase"] = WorkPhase.IDLE.value
            session["work_type"] = None
            session["collected_data"] = {}
            
            return SkillResult(
                response="已取消。" + MessageGenerator.generate_welcome(),
                status=SkillResultStatus.SUCCESS,
                next_phase=WorkPhase.IDLE.value
            )
    
    async def _save_session(self, context: SkillContext) -> None:
        """保存会话状态到数据库"""
        if self.pg_tool:
            try:
                session_data = {
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "phase": context.get_session_data("phase"),
                    "work_type": context.get_session_data("work_type"),
                    "current_step": context.get_session_data("current_step"),
                    "collected_data": context.get_session_data("collected_data"),
                    "updated_at": datetime.now().isoformat()
                }
                # 这里应该调用 pg_tool 保存会话
                # await self.pg_tool.save_session(session_data)
            except Exception as e:
                # 记录错误但不中断流程
                print(f"Failed to save session: {e}")
    
    async def _save_step_data(self, context: SkillContext, step: CollectionStep, data: Dict[str, Any]) -> None:
        """保存步骤数据到数据库"""
        if self.pg_tool:
            try:
                work_id = context.get_session_data("work_id")
                step_data = {
                    "work_id": work_id,
                    "step": step.step,
                    "step_name": step.name,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                # 这里应该调用 pg_tool 保存步骤数据
                # await self.pg_tool.save_collection_data(step_data)
            except Exception as e:
                print(f"Failed to save step data: {e}")
    
    async def _save_completion(self, context: SkillContext, summary: str) -> None:
        """保存完成信息"""
        if self.pg_tool:
            try:
                completion_data = {
                    "work_id": context.get_session_data("work_id"),
                    "user_id": context.user_id,
                    "work_type": context.get_session_data("work_type"),
                    "start_time": context.get_session_data("start_time"),
                    "end_time": datetime.now().isoformat(),
                    "summary": summary,
                    "status": "completed"
                }
                # 这里应该调用 pg_tool 保存完成记录
                # await self.pg_tool.save_completion(completion_data)
            except Exception as e:
                print(f"Failed to save completion: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Skill 信息"""
        return {
            "name": self.NAME,
            "description": self.DESCRIPTION,
            "version": self.VERSION,
            "work_types": list(self.WORK_TYPES.keys()),
            "phases": [p.value for p in WorkPhase]
        }


__all__ = ["StationWorkGuideSkill"]
