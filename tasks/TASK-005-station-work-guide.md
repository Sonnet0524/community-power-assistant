# Task-005: StationWorkGuide Skill 开发

## 任务概述

**任务ID**: TASK-005  
**任务名称**: StationWorkGuide Skill（驻点工作引导）  
**优先级**: 🔴 最高  
**预计耗时**: 40-60分钟  
**依赖**: TASK-002 ✅, TASK-003 ✅, TASK-004 ✅  
**负责团队**: Field Core Team

## 任务目标

开发驻点工作引导 Skill，为供电所人员提供：
1. 工作开始前准备清单
2. 配电房信息采集引导
3. 客户走访对话模板
4. 应急信息快速采集

## Skill设计

### Skill定义

```yaml
# knowledge-base/field-info-agent/implementation/skills/station-work-guide/SKILL.md
skill:
  name: station_work_guide
  description: 驻点工作引导Skill，帮助供电所人员完成现场工作
  version: 1.0.0
  
  input:
    - user_message: str          # 用户输入
    - session_context: dict      # 会话上下文
    - current_phase: str         # 当前阶段
    
  output:
    - response: str              # 回复消息
    - next_phase: str            # 下一阶段
    - actions: list              # 建议操作
    - data_to_collect: dict      # 待采集数据
```

### 工作流程状态机

```python
class WorkPhase(Enum):
    IDLE = "idle"                          # 空闲
    PREPARING = "preparing"               # 准备阶段
    COLLECTING = "collecting"             # 采集中
    ANALYZING = "analyzing"               # 分析中
    COMPLETED = "completed"               # 已完成

# 状态流转
PHASE_TRANSITIONS = {
    "idle": ["preparing"],
    "preparing": ["collecting", "completed"],
    "collecting": ["analyzing", "completed"],
    "analyzing": ["collecting", "completed"],
    "completed": ["idle"]
}
```

## 详细工作内容

### 1. Skill 主类

**文件**: `src/skills/station_work_guide/skill.py`

```python
class StationWorkGuideSkill(BaseSkill):
    """驻点工作引导 Skill"""
    
    NAME = "station_work_guide"
    DESCRIPTION = "驻点工作引导，帮助完成现场信息采集"
    
    # 工作类型
    WORK_TYPES = {
        "power_room": "配电房巡检",
        "customer_visit": "客户走访",
        "emergency": "应急信息采集"
    }
    
    async def invoke(self, context: SkillContext) -> SkillResult:
        """
        Skill 主入口
        
        根据当前阶段和用户输入，返回引导信息
        """
        phase = context.session.get("phase", "idle")
        work_type = context.session.get("work_type")
        
        if phase == "idle":
            return await self._handle_idle(context)
        elif phase == "preparing":
            return await self._handle_preparing(context, work_type)
        elif phase == "collecting":
            return await self._handle_collecting(context, work_type)
        elif phase == "analyzing":
            return await self._handle_analyzing(context)
        
        return SkillResult(response="未知阶段，请重新开始")
```

### 2. 准备阶段

**功能**: 工作开始前的检查清单

```python
async def _handle_idle(self, context: SkillContext) -> SkillResult:
    """处理空闲阶段 - 询问工作类型"""
    return SkillResult(
        response="""请选择工作类型：
1. 配电房巡检
2. 客户走访  
3. 应急信息采集

发送数字或关键词即可开始。""",
        actions=[
            {"type": "select", "options": ["1", "2", "3"]}
        ]
    )

async def _handle_preparing(self, context: SkillContext, work_type: str) -> SkillResult:
    """处理准备阶段 - 显示检查清单"""
    
    checklists = {
        "power_room": [
            "□ 安全帽、绝缘手套",
            "□ 巡检记录表",
            "□ 测温仪",
            "□ 相机/手机"
        ],
        "customer_visit": [
            "□ 客户资料",
            "□ 走访记录表", 
            "□ 宣传资料",
            "□ 名片"
        ],
        "emergency": [
            "□ 应急工具包",
            "□ 对讲机",
            "□ 应急联系人名单"
        ]
    }
    
    checklist = checklists.get(work_type, [])
    
    return SkillResult(
        response=f"""📋 {self.WORK_TYPES[work_type]} - 准备清单

{'\n'.join(checklist)}

准备好后发送"开始"进入采集阶段。""",
        next_phase="collecting"
    )
```

### 3. 采集阶段

**配电房采集流程**:

```python
POWER_ROOM_COLLECTION = [
    {
        "step": 1,
        "name": "基本信息",
        "prompt": "请拍摄配电房外观照片，并告诉我：\n1. 配电房名称/编号\n2. 所属小区/单位",
        "data_type": ["photo", "text"],
        "required": True
    },
    {
        "step": 2, 
        "name": "变压器铭牌",
        "prompt": "请拍摄变压器铭牌照片，系统将自动识别型号、容量等信息。",
        "data_type": ["photo"],
        "required": True,
        "use_ai": True  # 使用KIMI分析
    },
    {
        "step": 3,
        "name": "设备状态", 
        "prompt": "请拍摄主要设备照片，包括：\n- 高压柜\n- 低压柜\n- 变压器外观\n是否有异常发热、异响、异味？",
        "data_type": ["photo", "text"],
        "required": True
    },
    {
        "step": 4,
        "name": "安全环境",
        "prompt": "请拍摄配电房环境照片：\n- 通道是否畅通\n- 消防设施\n- 通风情况\n有无安全隐患？",
        "data_type": ["photo", "text"],
        "required": True
    }
]
```

### 4. 客户走访流程

```python
CUSTOMER_VISIT_TEMPLATE = """
您好，我是{station_name}供电所的客户经理{name}。

本次走访是想了解您近期的用电情况，包括：
1. 用电是否稳定？
2. 电费账单是否清楚？
3. 有没有用电方面的问题或建议？
4. 是否需要办理用电业务？

麻烦您了，大概需要5-10分钟。
"""

CUSTOMER_COLLECTION = [
    {
        "step": 1,
        "name": "客户信息",
        "prompt": "请确认客户信息：\n- 户名\n- 用电地址\n- 联系电话",
        "data_type": ["text"]
    },
    {
        "step": 2,
        "name": "用电情况",
        "prompt": "近期用电是否稳定？有无停电、电压不稳等问题？",
        "data_type": ["text", "voice"]
    },
    {
        "step": 3,
        "name": "业务需求",
        "prompt": "是否有增容、改类、新装等业务需求？",
        "data_type": ["text"]
    },
    {
        "step": 4,
        "name": "意见建议",
        "prompt": "对供电服务有什么意见或建议？",
        "data_type": ["text", "voice"]
    }
]
```

### 5. 数据收集与存储

```python
async def _save_collection_data(
    self, 
    session_id: str,
    step_data: dict
):
    """保存采集的数据"""
    # 使用 PostgreSQL Tool 保存
    await self.pg_tool.save_task_data(
        session_id=session_id,
        step=step_data["step"],
        data_type=step_data["type"],
        content=step_data["content"],
        photos=step_data.get("photos", [])
    )
    
    # 如果有照片，使用KIMI分析
    if step_data.get("photos") and step_data.get("use_ai"):
        for photo in step_data["photos"]:
            analysis = await self.kimi_tool.analyze_image(
                photo,
                analysis_type=step_data["ai_type"]
            )
            step_data["ai_result"] = analysis
```

### 6. 引导回复生成

```python
def generate_guidance(
    self,
    current_step: int,
    total_steps: int,
    prompt: str,
    collected_data: dict
) -> str:
    """生成引导回复"""
    
    progress = f"({current_step}/{total_steps})"
    
    response = f"""{progress} {prompt}

已采集数据：
{self._format_collected_data(collected_data)}

提示：发送照片和文字信息，完成后发送"下一步"。
发送"上一步"可修改之前的采集内容。
发送"取消"放弃本次工作。"""
    
    return response
```

## 交付物

1. **Skill 主类**: `src/skills/station_work_guide/skill.py`
2. **Skill 定义**: `knowledge-base/field-info-agent/implementation/skills/station-work-guide/SKILL.md`
3. **工作流配置**: `src/skills/station_work_guide/workflows.py`
4. **模板文件**: `src/skills/station_work_guide/templates.py`
5. **单元测试**: `tests/skills/test_station_work_guide.py`
6. **使用文档**: `docs/skills/station-work-guide.md`

## 验收标准

- [ ] Skill 可在 OpenClaw 框架中注册和调用
- [ ] 支持3种工作类型（配电房/客户走访/应急）
- [ ] 状态机流转正确
- [ ] 数据正确保存到数据库
- [ ] 照片自动触发KIMI分析
- [ ] 单元测试覆盖率 >90%
- [ ] 文档完整

## 集成点

- **依赖 PostgreSQL Tool**: 保存采集数据
- **依赖 MinIO Tool**: 存储照片
- **依赖 KIMI Tool**: 照片分析
- **依赖 WeCom Channel**: 消息收发

## 报告要求

完成后请提交报告到: `reports/REPORT-005-station-work-guide.md`

---

**创建时间**: 2026-03-20  
**负责团队**: Field Core Team  
**状态**: 待开始  
**依赖**: Phase 1 全部完成 ✅