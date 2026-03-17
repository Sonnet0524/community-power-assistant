# 项目实例化经验 - 2026-03-17

**项目**: 小区供电服务信息助理  
**任务**: 从 PM Agent Template 实例化新仓库  
**时间**: 2026-03-17

---

## 执行步骤

### 1. 准备工作
- 确认新项目路径：`/Users/sonnet/opencode/community-power-assistant`
- 确认目录不存在，避免覆盖

### 2. 复制模板
```bash
mkdir -p /Users/sonnet/opencode/community-power-assistant
cp -r /Users/sonnet/opencode/agent-team-template/* /Users/sonnet/opencode/community-power-assistant/
rm -rf /Users/sonnet/opencode/community-power-assistant/.git
```

### 3. 初始化项目配置

**更新的文件**:
- ✅ README.md - 更新项目名称和目标描述
- ✅ opencode.json - 更新 Agent 描述
- ✅ agents/pm/CATCH_UP.md - 更新项目状态
- ✅ status/agent-status.md - 更新项目信息
- ✅ status/human-admin.md - 更新项目总览

**清空的目录**:
- tasks/ (保留 .gitkeep)
- reports/ (保留 .gitkeep)
- logs/ (保留 .gitkeep)

### 4. 初始化 Git
```bash
cd /Users/sonnet/opencode/community-power-assistant
git init
git add -A
git commit -m "Initial commit: 小区供电服务信息助理..."
```

---

## 关键配置项

| 文件 | 配置项 | 值 |
|------|--------|-----|
| README.md | 项目名称 | 小区供电服务信息助理 |
| README.md | 项目目标 | 基于 OpenCode 开发小区驻点服务助理 |
| opencode.json | Agent 描述 | PM - 小区供电服务信息助理项目管理Agent |
| status/human-admin.md | 项目名称 | 小区供电服务信息助理 |
| agents/pm/CATCH_UP.md | 项目名称 | 小区供电服务信息助理 |

---

## 有效做法

1. **先检查目录是否存在** - 避免意外覆盖
2. **删除 .git 目录** - 确保新项目有独立的 git 历史
3. **保留模板经验文件** - 保留 knowledge-assistant-experiences/ 作为参考
4. **更新所有状态文档** - 确保 PM Agent 启动时能正确了解项目状态
5. **清空空动态目录** - tasks/, reports/, logs/ 保留 .gitkeep

---

## 后续步骤

1. 配置 OpenCode CLI
2. 启动 PM Agent: `./start-pm.sh`
3. 细化项目需求和范围
4. 设计 Agent Team 结构
5. 开始开发任务

---

**耗时**: ~5分钟  
**结果**: 成功创建新项目仓库并初始化
