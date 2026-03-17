# Integration Team 模板

> 🔌 系统集成、连接器开发、API 对接

---

## 职责范围

- **系统集成**: 系统间集成、数据同步
- **连接器**: 第三方服务、数据库、API
- **适配器**: 协议适配、数据格式转换

## 技术栈

- HTTP/REST API
- GraphQL
- WebSocket
- OAuth / JWT
- 数据库连接

## 边界

**负责**:
- `src/integration/`
- `src/connectors/`
- `src/adapters/`
- `src/api/`

**不负责**:
- 数据处理（Core Team）
- AI 实现（AI Team）
- 测试（Test Team）

## 使用方式

```bash
# 复制模板
cp -r agents/_templates/integration-team agents/my-integration-team

# 定制 AGENTS.md
vim agents/my-integration-team/AGENTS.md

# 配置并注册
# 详见 TEMPLATE-GUIDE.md
```

---

**模板版本**: 1.0  
**最后更新**: 2026-03-08
