"""
StationWorkGuide Skill - 工作流配置

定义完整的状态机和工作流程配置
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


class WorkPhase(Enum):
    """工作阶段枚举
    
    定义驻点工作的完整状态流转
    """
    IDLE = "idle"                          # 空闲 - 等待选择工作类型
    PREPARING = "preparing"                # 准备阶段 - 显示检查清单
    COLLECTING = "collecting"              # 采集中 - 信息采集
    ANALYZING = "analyzing"                # 分析中 - AI分析处理
    COMPLETED = "completed"                # 已完成


class WorkType(Enum):
    """工作类型枚举"""
    POWER_ROOM = "power_room"              # 配电房巡检
    CUSTOMER_VISIT = "customer_visit"      # 客户走访
    EMERGENCY = "emergency"                # 应急信息采集


class CollectionStepStatus(Enum):
    """采集步骤状态"""
    PENDING = "pending"                    # 待完成
    IN_PROGRESS = "in_progress"            # 进行中
    COMPLETED = "completed"                # 已完成
    SKIPPED = "skipped"                    # 已跳过


# 状态机流转规则
PHASE_TRANSITIONS: Dict[str, List[str]] = {
    WorkPhase.IDLE.value: [WorkPhase.PREPARING.value],
    WorkPhase.PREPARING.value: [WorkPhase.COLLECTING.value, WorkPhase.COMPLETED.value],
    WorkPhase.COLLECTING.value: [WorkPhase.ANALYZING.value, WorkPhase.COMPLETED.value],
    WorkPhase.ANALYZING.value: [WorkPhase.COLLECTING.value, WorkPhase.COMPLETED.value],
    WorkPhase.COMPLETED.value: [WorkPhase.IDLE.value]
}


@dataclass
class CollectionStep:
    """采集步骤定义"""
    step: int                              # 步骤序号
    name: str                              # 步骤名称
    prompt: str                            # 引导提示词
    data_types: List[str]                  # 支持的数据类型 ["photo", "text", "voice"]
    required: bool = True                  # 是否必填
    use_ai: bool = False                   # 是否使用AI分析
    ai_type: str = "general"               # AI分析类型
    hint: str = ""                         # 额外提示


@dataclass
class WorkflowConfig:
    """工作流配置"""
    work_type: WorkType
    name: str
    description: str
    steps: List[CollectionStep]
    checklist: List[str]
    completion_message: str


# 工作类型配置
WORK_TYPE_CONFIGS: Dict[WorkType, WorkflowConfig] = {
    WorkType.POWER_ROOM: WorkflowConfig(
        work_type=WorkType.POWER_ROOM,
        name="配电房巡检",
        description="配电房设备巡检和安全检查",
        checklist=[
            "□ 安全帽、绝缘手套",
            "□ 巡检记录表",
            "□ 测温仪",
            "□ 相机/手机"
        ],
        steps=[
            CollectionStep(
                step=1,
                name="基本信息",
                prompt="请拍摄配电房外观照片，并告诉我：\n1. 配电房名称/编号\n2. 所属小区/单位",
                data_types=["photo", "text"],
                required=True
            ),
            CollectionStep(
                step=2,
                name="变压器铭牌",
                prompt="请拍摄变压器铭牌照片，系统将自动识别型号、容量等信息。",
                data_types=["photo"],
                required=True,
                use_ai=True,
                ai_type="nameplate",
                hint="请确保铭牌清晰可见，光线充足"
            ),
            CollectionStep(
                step=3,
                name="设备状态",
                prompt="请拍摄主要设备照片，包括：\n- 高压柜\n- 低压柜\n- 变压器外观\n是否有异常发热、异响、异味？",
                data_types=["photo", "text"],
                required=True
            ),
            CollectionStep(
                step=4,
                name="安全环境",
                prompt="请拍摄配电房环境照片：\n- 通道是否畅通\n- 消防设施\n- 通风情况\n有无安全隐患？",
                data_types=["photo", "text"],
                required=True,
                use_ai=True,
                ai_type="safety"
            ),
            CollectionStep(
                step=5,
                name="巡检结论",
                prompt="巡检总结：\n1. 设备总体状态\n2. 发现的问题\n3. 建议措施",
                data_types=["text"],
                required=True
            )
        ],
        completion_message="✅ 配电房巡检完成！数据已保存，分析报告已生成。"
    ),
    
    WorkType.CUSTOMER_VISIT: WorkflowConfig(
        work_type=WorkType.CUSTOMER_VISIT,
        name="客户走访",
        description="客户走访和需求收集",
        checklist=[
            "□ 客户资料",
            "□ 走访记录表",
            "□ 宣传资料",
            "□ 名片"
        ],
        steps=[
            CollectionStep(
                step=1,
                name="客户信息",
                prompt="请确认客户信息：\n- 户名\n- 用电地址\n- 联系电话\n- 用电类别",
                data_types=["text"],
                required=True
            ),
            CollectionStep(
                step=2,
                name="用电情况",
                prompt="近期用电是否稳定？有无停电、电压不稳等问题？",
                data_types=["text", "voice"],
                required=True
            ),
            CollectionStep(
                step=3,
                name="业务需求",
                prompt="是否有增容、改类、新装等业务需求？",
                data_types=["text"],
                required=False
            ),
            CollectionStep(
                step=4,
                name="意见建议",
                prompt="对供电服务有什么意见或建议？",
                data_types=["text", "voice"],
                required=False
            ),
            CollectionStep(
                step=5,
                name="走访小结",
                prompt="走访总结：\n1. 客户满意度\n2. 主要问题\n3. 后续跟进事项",
                data_types=["text"],
                required=True
            )
        ],
        completion_message="✅ 客户走访完成！感谢客户的配合。"
    ),
    
    WorkType.EMERGENCY: WorkflowConfig(
        work_type=WorkType.EMERGENCY,
        name="应急信息采集",
        description="应急情况快速信息采集",
        checklist=[
            "□ 应急工具包",
            "□ 对讲机",
            "□ 应急联系人名单",
            "□ 安全警示标识"
        ],
        steps=[
            CollectionStep(
                step=1,
                name="基本情况",
                prompt="请快速描述应急情况：\n1. 故障地点\n2. 故障现象\n3. 影响范围",
                data_types=["text", "voice"],
                required=True
            ),
            CollectionStep(
                step=2,
                name="现场照片",
                prompt="请拍摄现场照片（多角度），记录设备状态和周围环境。",
                data_types=["photo"],
                required=True,
                use_ai=True,
                ai_type="safety"
            ),
            CollectionStep(
                step=3,
                name="初步处理",
                prompt="已采取的应急措施：",
                data_types=["text"],
                required=True
            ),
            CollectionStep(
                step=4,
                name="后续安排",
                prompt="后续处理计划和人员安排：",
                data_types=["text"],
                required=True
            )
        ],
        completion_message="⚠️ 应急信息采集完成！请立即上报并启动应急预案。"
    )
}


def get_workflow_config(work_type: str) -> Optional[WorkflowConfig]:
    """获取工作流配置
    
    Args:
        work_type: 工作类型字符串
        
    Returns:
        工作流配置或None
    """
    try:
        wt = WorkType(work_type)
        return WORK_TYPE_CONFIGS.get(wt)
    except ValueError:
        return None


def validate_phase_transition(current_phase: str, next_phase: str) -> bool:
    """验证状态流转是否有效
    
    Args:
        current_phase: 当前阶段
        next_phase: 目标阶段
        
    Returns:
        是否允许流转
    """
    allowed = PHASE_TRANSITIONS.get(current_phase, [])
    return next_phase in allowed


def get_phase_display_name(phase: str) -> str:
    """获取阶段显示名称"""
    display_names = {
        WorkPhase.IDLE.value: "🟢 等待开始",
        WorkPhase.PREPARING.value: "📋 准备中",
        WorkPhase.COLLECTING.value: "📸 采集中",
        WorkPhase.ANALYZING.value: "🤖 分析中",
        WorkPhase.COMPLETED.value: "✅ 已完成"
    }
    return display_names.get(phase, phase)


__all__ = [
    "WorkPhase",
    "WorkType",
    "CollectionStepStatus",
    "PHASE_TRANSITIONS",
    "CollectionStep",
    "WorkflowConfig",
    "WORK_TYPE_CONFIGS",
    "get_workflow_config",
    "validate_phase_transition",
    "get_phase_display_name"
]
