# Field Integration Team

## 简介

Field Integration Team 是 Field Info Agent 项目的系统集成团队，负责：
- 企业微信 Channel 开发
- OpenClaw Gateway 集成
- 第三方 API 对接
- 系统间通信

## 团队配置

- **路径**: `agents/field-integration/`
- **AGENTS.md**: `agents/field-integration/AGENTS.md`
- **CATCH_UP.md**: `agents/field-integration/CATCH_UP.md`

## 启动方式

```bash
# 方式1: 使用 opencode
opencode run --agent field-integration "[任务描述]"

# 方式2: 使用启动脚本
./start-field-integration.sh
```

## 主要职责

1. **企业微信 Channel 开发**
   - 企业微信应用接入
   - WebSocket 长连接管理
   - 消息接收和发送
   - 用户身份验证

2. **OpenClaw Gateway 集成**
   - Gateway 配置
   - Channel 注册
   - Session 管理

3. **API 对接**
   - 企业微信 API 对接
   - KIMI API 调用封装
   - 内部服务 API 对接

4. **消息处理**
   - 文本消息处理
   - 图片消息处理
   - 消息状态管理
   - 流式输出支持

## 输出规范

- 完善的错误处理
- 重试和熔断机制
- 详细的日志记录
- 报告写入 `reports/` 目录

## 相关文档

- [项目总览](../../knowledge-base/field-info-agent/README.md)
- [设计文档](../../knowledge-base/field-info-agent/design/)
- [实现结构](../../knowledge-base/field-info-agent/implementation/)
- [企业微信开发文档](https://developer.work.weixin.qq.com/)

---

**创建日期**: 2026-03-19  
**维护者**: PM Agent
