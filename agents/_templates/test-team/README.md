# Test Team 模板

> 🧪 测试框架、测试用例、质量保证

---

## 职责范围

- **测试框架**: 搭建测试环境、测试工具
- **测试用例**: 单元测试、集成测试、E2E测试
- **质量保证**: 覆盖率统计、缺陷跟踪

## 技术栈

- Python: pytest, unittest
- JavaScript: Jest, Mocha
- 覆盖率工具: coverage, nyc
- CI/CD: GitHub Actions, Jenkins

## 边界

**负责**:
- `tests/`
- `test-tools/`
- `test-data/`

**不负责**:
- 业务代码实现（Core/AI Team）
- 系统集成（Integration Team）

## 使用方式

```bash
# 复制模板
cp -r agents/_templates/test-team agents/my-test-team

# 定制 AGENTS.md
vim agents/my-test-team/AGENTS.md

# 配置并注册
# 详见 TEMPLATE-GUIDE.md
```

---

**模板版本**: 1.0  
**最后更新**: 2026-03-08
