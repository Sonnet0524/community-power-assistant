# Core Team 模板

> 🔧 数据处理、工具开发、基础架构

---

## 职责范围

- **数据处理**: 解析、清洗、转换、验证
- **工具开发**: CLI 工具、数据处理库
- **基础架构**: 核心模块、性能优化

## 技术栈

- Python / Node.js / Go（根据项目）
- 数据处理库（Pandas, NumPy 等）
- 测试框架（pytest, Jest 等）

## 边界

**负责**:
- `src/core/`
- `src/data-processing/`
- `tools/`

**不负责**:
- AI/ML 实现（AI Team）
- 系统集成（Integration Team）
- 测试框架（Test Team）

## 使用方式

```bash
# 复制模板
cp -r agents/_templates/core-team agents/my-core-team

# 定制 AGENTS.md
vim agents/my-core-team/AGENTS.md

# 配置并注册
# 详见 TEMPLATE-GUIDE.md
```

---

**模板版本**: 1.0  
**最后更新**: 2026-03-08
