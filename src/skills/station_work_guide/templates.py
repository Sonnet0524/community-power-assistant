"""
StationWorkGuide Skill - 模板和消息生成

提供消息模板生成、格式化等功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .workflows import WorkflowConfig, CollectionStep, WorkPhase, get_phase_display_name


class MessageTemplates:
    """消息模板类"""
    
    # 欢迎消息
    WELCOME_MESSAGE = """👋 您好！我是驻点工作助手。

我可以帮助您完成以下工作：

1️⃣ **配电房巡检** - 设备检查和安全评估
2️⃣ **客户走访** - 客户需求收集和反馈
3️⃣ **应急信息采集** - 快速应急情况上报

请发送数字（1/2/3）或关键词开始工作。

💡 **提示**：
• 工作中随时可以发送"取消"退出
• 发送"帮助"查看操作指南"""

    # 工作类型选择确认
    WORK_TYPE_CONFIRM = """您选择了：**{work_type_name}**

{description}

请确认是否开始？发送"开始"继续，或发送其他数字重新选择。"""

    # 准备阶段消息
    PREPARING_MESSAGE = """📋 **{work_type_name}** - 准备清单

请确认已准备以下物品：

{checklist}

✅ 准备好后发送"开始"进入采集阶段
⏸️ 发送"稍后"保存进度稍后继续"""

    # 采集阶段消息
    COLLECTING_MESSAGE = """{progress} **{step_name}**

{prompt}

{hint_section}
---
📊 **已采集数据**：
{collected_data}

💡 **操作提示**：
• 发送照片/文字完成当前步骤
• "下一步" - 确认并继续
• "上一步" - 返回修改
• "跳过" - 跳过此步骤（如允许）
• "取消" - 放弃本次工作"""

    # 分析中消息
    ANALYZING_MESSAGE = """🤖 **正在分析数据...**

请稍候，系统正在处理已采集的信息：
{analysis_items}

⏱️ 预计需要 10-30 秒"""

    # 完成消息
    COMPLETION_MESSAGE = """{completion_message}

📋 **采集数据摘要**：
{summary}

💾 数据已保存到数据库
📄 报告已生成：{report_url}

发送"1"开始新的工作
发送"查看"查看本次详细记录"""

    # 取消确认
    CANCEL_CONFIRM = """⚠️ 确定要取消本次工作吗？

已采集的数据：**{collected_count} 项**

发送"确认取消"放弃所有数据
发送"继续"返回工作"""

    # 帮助信息
    HELP_MESSAGE = """📖 **驻点工作助手 - 操作指南**

**基本操作**：
• 发送数字 1/2/3 选择工作类型
• 发送"开始"进入下一阶段
• 发送"取消"退出当前工作

**采集阶段**：
• 可以直接发送照片或文字
• "下一步"确认当前步骤
• "上一步"返回修改
• "跳过"跳过当前步骤

**状态查看**：
• 发送"状态"查看当前进度
• 发送"数据"查看已采集内容

**需要帮助？**
发送"帮助"随时查看此指南"""

    # 无效输入提示
    INVALID_INPUT = """❓ 抱歉，我没有理解您的意思。

{hint}

发送"帮助"查看操作指南"""

    # 错误提示
    ERROR_MESSAGE = """❌ **发生错误**

{error_message}

请稍后重试，或联系管理员。

发送"取消"退出当前工作"""


class MessageGenerator:
    """消息生成器"""
    
    @staticmethod
    def generate_welcome() -> str:
        """生成欢迎消息"""
        return MessageTemplates.WELCOME_MESSAGE
    
    @staticmethod
    def generate_work_type_confirm(work_type: str, config: WorkflowConfig) -> str:
        """生成工作类型确认消息"""
        return MessageTemplates.WORK_TYPE_CONFIRM.format(
            work_type_name=config.name,
            description=config.description
        )
    
    @staticmethod
    def generate_preparing_message(config: WorkflowConfig) -> str:
        """生成准备阶段消息"""
        checklist_text = "\n".join(config.checklist)
        return MessageTemplates.PREPARING_MESSAGE.format(
            work_type_name=config.name,
            checklist=checklist_text
        )
    
    @staticmethod
    def generate_collecting_message(
        step: CollectionStep,
        current_step: int,
        total_steps: int,
        collected_data: Dict[str, Any]
    ) -> str:
        """生成采集阶段消息"""
        progress = f"({current_step}/{total_steps})"
        
        # 格式化已采集数据
        collected_text = MessageGenerator._format_collected_data(collected_data)
        
        # 额外提示
        hint_section = ""
        if step.hint:
            hint_section = f"\n💡 **提示**：{step.hint}\n"
        
        return MessageTemplates.COLLECTING_MESSAGE.format(
            progress=progress,
            step_name=step.name,
            prompt=step.prompt,
            hint_section=hint_section,
            collected_data=collected_text
        )
    
    @staticmethod
    def generate_analyzing_message(analysis_items: List[str]) -> str:
        """生成分析中消息"""
        items_text = "\n".join([f"  • {item}" for item in analysis_items])
        return MessageTemplates.ANALYZING_MESSAGE.format(
            analysis_items=items_text
        )
    
    @staticmethod
    def generate_completion_message(
        config: WorkflowConfig,
        summary: str,
        report_url: str
    ) -> str:
        """生成完成消息"""
        return MessageTemplates.COMPLETION_MESSAGE.format(
            completion_message=config.completion_message,
            summary=summary,
            report_url=report_url
        )
    
    @staticmethod
    def generate_cancel_confirm(collected_count: int) -> str:
        """生成取消确认消息"""
        return MessageTemplates.CANCEL_CONFIRM.format(
            collected_count=collected_count
        )
    
    @staticmethod
    def generate_help() -> str:
        """生成帮助消息"""
        return MessageTemplates.HELP_MESSAGE
    
    @staticmethod
    def generate_invalid_input(hint: str = "请按照提示操作") -> str:
        """生成无效输入提示"""
        return MessageTemplates.INVALID_INPUT.format(hint=hint)
    
    @staticmethod
    def generate_error(error_message: str) -> str:
        """生成错误消息"""
        return MessageTemplates.ERROR_MESSAGE.format(
            error_message=error_message
        )
    
    @staticmethod
    def generate_status(
        current_phase: str,
        work_type_name: str,
        current_step: int,
        total_steps: int,
        collected_count: int
    ) -> str:
        """生成状态消息"""
        phase_display = get_phase_display_name(current_phase)
        
        status_text = f"""📊 **当前状态**

📝 工作类型：{work_type_name}
🔄 当前阶段：{phase_display}
📸 采集进度：{current_step}/{total_steps} 步
💾 已采数据：{collected_count} 项

---

"""
        
        if current_phase == WorkPhase.COLLECTING.value:
            status_text += "继续发送照片或文字完成当前步骤"
        elif current_phase == WorkPhase.PREPARING.value:
            status_text += '发送"开始"进入采集阶段'
        elif current_phase == WorkPhase.IDLE.value:
            status_text += "发送 1/2/3 选择工作类型"
        
        return status_text
    
    @staticmethod
    def _format_collected_data(collected_data: Dict[str, Any]) -> str:
        """格式化已采集数据"""
        if not collected_data:
            return "暂无"
        
        lines = []
        for key, value in collected_data.items():
            if isinstance(value, list):
                # 照片列表
                lines.append(f"• {key}: {len(value)} 张照片")
            elif isinstance(value, dict):
                # AI分析结果
                lines.append(f"• {key}: AI分析完成")
            elif isinstance(value, str) and len(value) > 30:
                # 长文本截断
                lines.append(f"• {key}: {value[:30]}...")
            else:
                lines.append(f"• {key}: {value}")
        
        return "\n".join(lines) if lines else "暂无"
    
    @staticmethod
    def generate_summary(data: Dict[str, Any]) -> str:
        """生成数据摘要"""
        lines = []
        
        for step_name, step_data in data.items():
            if isinstance(step_data, dict):
                if "ai_result" in step_data:
                    lines.append(f"✓ {step_name}: AI分析完成")
                elif "photos" in step_data:
                    lines.append(f"✓ {step_name}: {len(step_data['photos'])}张照片")
                elif "text" in step_data:
                    text = step_data["text"]
                    if len(text) > 20:
                        text = text[:20] + "..."
                    lines.append(f"✓ {step_name}: {text}")
            elif isinstance(step_data, list):
                lines.append(f"✓ {step_name}: {len(step_data)}项数据")
            elif isinstance(step_data, str):
                if len(step_data) > 20:
                    step_data = step_data[:20] + "..."
                lines.append(f"✓ {step_name}: {step_data}")
        
        return "\n".join(lines) if lines else "暂无数据"


# 快捷函数
def get_welcome_message() -> str:
    """获取欢迎消息"""
    return MessageGenerator.generate_welcome()


def get_help_message() -> str:
    """获取帮助消息"""
    return MessageGenerator.generate_help()


__all__ = [
    "MessageTemplates",
    "MessageGenerator",
    "get_welcome_message",
    "get_help_message"
]
