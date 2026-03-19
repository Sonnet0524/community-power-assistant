# Field Integration Team - 启动文档

> 🔄 启动时读取此文档 - 快速了解当前任务和状态

---

## Quick Status

**Last Updated**: 2026-03-19  
**Status**: 🟢 Active - 刚创建，等待第一个任务  
**Current Task**: 待分配

---

## Current Focus

**Primary Task**: 等待 PM Agent 分配 TASK-003

**项目背景**:
- **项目名称**: Field Info Agent（现场信息收集智能体）
- **项目目标**: 基于 OpenClaw + 企业微信 + KIMI 2.5 的现场信息采集Agent
- **技术栈**: OpenClaw Framework, 企业微信 API, WebSocket, Python

**即将开始的任务**:
1. TASK-003: 企业微信 Channel 配置和开发
2. 后续: OpenClaw Gateway 集成
3. 后续: 消息处理和状态管理

---

## 项目上下文

### Field Info Agent 架构
```
用户层: 企业微信APP（拍照 + 文字输入）
   ↓ WebSocket长连接
OpenClaw Gateway: WeCom Channel + Session Manager + 4 Skills
   ↓ REST API
外部服务: KIMI K2.5 + PostgreSQL + MinIO + Redis（本地部署）
```

### 核心职责
作为 Field Integration Team，你负责：
- ✅ 企业微信 Channel 开发
- ✅ WebSocket 长连接管理
- ✅ OpenClaw Gateway 集成
- ✅ 消息接收、处理和发送
- ✅ 用户身份验证

### 依赖团队
- **PM Agent**: 任务分配和验收
- **Field Core Team**: Skills 和 Tools 开发
- **Field AI Team**: AI 模型调优（后续创建）
- **Field Test Team**: 集成测试（后续创建）

---

## 工作流程

### 1. 接收任务
PM Agent 会创建任务文件在 `tasks/TASK-XXX.md`

### 2. 读取任务
```bash
# 启动时 PM Agent 会告诉你任务文件路径
# 例如：tasks/TASK-003-wecom-channel.md
```

### 3. 执行任务
- 读取任务要求
- 设计方案
- 编写代码
- 本地验证

### 4. 提交报告
完成后写入 `reports/REPORT-XXX.md`

### 5. 等待验收
PM Agent 会 Review 并反馈

---

## 开发规范

### Channel 开发规范
1. 必须实现 OpenClaw Channel 接口
2. 支持文本消息和图片消息
3. 实现消息状态管理
4. 支持流式输出

### 错误处理规范
1. 所有外部调用必须有 try-catch
2. 实现指数退避重试
3. 详细的错误日志
4. 熔断器防止雪崩

### Git 工作流
1. 每个任务一个分支: `feature/TASK-003-xxx`
2. 提交信息规范: `[TASK-003] 描述`
3. 提交前运行测试
4. 完成后通知 PM Agent

---

## 关键文件位置

| 文件/目录 | 路径 | 说明 |
|-----------|------|------|
| 项目总览 | `knowledge-base/field-info-agent/README.md` | 项目介绍 |
| 设计文档 | `knowledge-base/field-info-agent/design/` | 详细设计 |
| 实现结构 | `knowledge-base/field-info-agent/implementation/` | Channel 规范 |
| 任务目录 | `tasks/` | 所有任务文件 |
| 报告目录 | `reports/` | 完成报告 |
| Channel 配置 | `knowledge-base/field-info-agent/implementation/openclaw.config.yaml` | 参考配置 |

---

## 待办事项

- [ ] 完成 TASK-003: 企业微信 Channel 配置和开发
- [ ] 后续: OpenClaw Gateway 集成
- [ ] 后续: 消息状态管理
- [ ] 后续: 流式输出支持

---

## 重要提醒

- ⚠️ **必须先读取任务文件** - 不要凭记忆工作
- ⚠️ **必须处理错误和超时** - 网络调用不可靠
- ⚠️ **不要硬编码敏感信息** - 使用环境变量
- ⚠️ **遇到问题立即报告** - 不要自己硬抗

---

## 企业微信开发参考

### 关键 API
- 消息接收: 企业微信服务器推送
- 消息发送: 主动推送接口
- 素材上传: 临时素材接口
- 用户身份: OAuth2 授权

### 开发环境
- 需要企业微信管理员权限
- 需要配置回调 URL
- 需要配置 IP 白名单

---

**Remember**:
- 你是集成团队，稳定性至关重要
- 完善的错误处理和日志是基本要求
- 及时沟通，不要让问题堆积

---

**Last Updated**: 2026-03-19  
**Next Review**: 分配第一个任务后
