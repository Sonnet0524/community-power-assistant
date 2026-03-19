# Field Core Team

## 简介

Field Core Team 是 Field Info Agent 项目的核心开发团队，负责：
- OpenClaw Skill 开发
- Tool 开发（数据库、文件存储）
- 业务逻辑实现
- 数据模型和 Schema

## 团队配置

- **路径**: `agents/field-core/`
- **AGENTS.md**: `agents/field-core/AGENTS.md`
- **CATCH_UP.md**: `agents/field-core/CATCH_UP.md`

## 启动方式

```bash
# 方式1: 使用 opencode
opencode run --agent field-core "[任务描述]"

# 方式2: 使用启动脚本
./start-field-core.sh
```

## 主要职责

1. **OpenClaw Skill 开发**
   - StationWorkGuide Skill（驻点工作引导）
   - VisionAnalysis Skill（照片智能分析）
   - DocGeneration Skill（文档自动生成）
   - EmergencyGuide Skill（应急处置）

2. **Tool 开发**
   - PostgreSQL Tool
   - MinIO Tool
   - Redis Tool
   - KIMI API Tool

3. **数据模型**
   - PostgreSQL Schema 设计
   - 数据访问层实现
   - 数据库迁移脚本

## 输出规范

- 代码必须包含单元测试（覆盖率 >80%）
- 遵循 OpenClaw Skill 标准
- 提交前运行所有测试
- 报告写入 `reports/` 目录

## 相关文档

- [项目总览](../../knowledge-base/field-info-agent/README.md)
- [设计文档](../../knowledge-base/field-info-agent/design/)
- [实现结构](../../knowledge-base/field-info-agent/implementation/)
- [Skill 标准](../../knowledge-base/field-info-agent/OPENCLAW-SKILLS-STANDARD.md)

---

**创建日期**: 2026-03-19  
**维护者**: PM Agent
