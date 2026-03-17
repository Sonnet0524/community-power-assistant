# Task-002: WPS API Tool开发

## 任务概述

**任务ID**: TASK-002  
**任务名称**: WPS API Tool开发  
**优先级**: 🔴 最高  
**预计工期**: 3-4天  
**依赖**: TASK-001

## 任务目标

开发WPS API Tool，封装WPS开放平台的API调用，包括：
1. Token管理和自动刷新
2. 请求队列（限流控制）
3. 多维表格CRUD操作
4. 文档生成和管理
5. 文件夹操作

## 详细工作内容

### 1. Token管理器

**接口设计**:
```typescript
class WPSTokenManager {
  async getToken(): Promise<string>
  async refreshToken(): Promise<void>
  isTokenValid(): boolean
}
```

**工作内容**:
- [ ] 实现Token获取逻辑
- [ ] 实现Token缓存（内存/Redis）
- [ ] 实现Token自动刷新（提前5分钟）
- [ ] 处理Token失效重试
- [ ] 错误处理和日志记录

**验收标准**:
- Token可正常获取和刷新
- Token有效期内复用缓存
- 失效时自动刷新，业务无感知

### 2. 请求队列（限流控制）

**接口设计**:
```typescript
class WPSRequestQueue {
  async add<T>(fn: () => Promise<T>): Promise<T>
  private async process(): Promise<void>
}
```

**工作内容**:
- [ ] 实现请求队列（Redis队列）
- [ ] 实现速率限制（100次/分钟）
- [ ] 实现请求批量处理
- [ ] 实现失败重试机制（最多3次）
- [ ] 实现超时处理

**验收标准**:
- 请求按队列顺序执行
- 速率不超过100次/分钟
- 失败请求自动重试

### 3. 多维表格操作

**接口设计**:
```typescript
interface WPSKSheetAPI {
  queryRecords(params: QueryParams): Promise<QueryResult>
  insertRecord(params: InsertParams): Promise<InsertResult>
  insertRecords(params: BatchInsertParams): Promise<BatchInsertResult>
  updateRecord(params: UpdateParams): Promise<void>
  deleteRecord(params: DeleteParams): Promise<void>
}
```

**工作内容**:
- [ ] 实现查询记录（支持过滤、排序、分页）
- [ ] 实现单条插入
- [ ] 实现批量插入（最多100条/次）
- [ ] 实现更新记录
- [ ] 实现删除记录
- [ ] 实现表结构查询

**验收标准**:
- 所有CRUD操作正常
- 支持复杂查询条件
- 批量操作性能达标

### 4. 文档操作

**接口设计**:
```typescript
interface WPSDocAPI {
  createDocument(params: CreateParams): Promise<CreateResult>
  generateDocument(params: GenerateParams): Promise<GenerateResult>
  getShareLink(params: ShareParams): Promise<ShareResult>
}
```

**工作内容**:
- [ ] 实现创建文档
- [ ] 实现基于模板生成文档
- [ ] 实现文档内容更新
- [ ] 实现分享链接生成
- [ ] 实现格式转换（docx→pdf）

**验收标准**:
- 文档可正常创建和生成
- 模板填充正确
- 分享链接可访问

### 5. 文件夹操作

**接口设计**:
```typescript
interface WPSFolderAPI {
  createFolder(params: CreateFolderParams): Promise<CreateFolderResult>
  getOrCreatePath(params: PathParams): Promise<FolderResult>
  moveFile(params: MoveParams): Promise<void>
  listFolder(params: ListParams): Promise<ListResult>
}
```

**工作内容**:
- [ ] 实现创建文件夹
- [ ] 实现路径自动创建（如不存在则创建）
- [ ] 实现文件移动
- [ ] 实现文件夹列表查询

**验收标准**:
- 文件夹结构可正常创建
- 路径不存在时自动创建
- 文件可正常移动

### 6. 权限控制

**工作内容**:
- [ ] 实现供电所数据隔离（自动添加station_id过滤）
- [ ] 实现文档访问权限检查
- [ ] 实现操作日志记录
- [ ] 实现敏感数据加密（客户手机号等）

**验收标准**:
- 数据按供电所隔离
- 跨供电所数据不可访问
- 敏感数据加密存储

## 技术规范

### 错误处理
```typescript
class WPSError extends Error {
  code: string
  message: string
  retryable: boolean
}

// 错误分类
- NetworkError: 网络错误，可重试
- RateLimitError: 限流错误，需等待后重试
- AuthError: 认证错误，需刷新Token
- NotFoundError: 资源不存在
- ValidationError: 参数校验错误
```

### 日志记录
```typescript
// 所有API调用需记录
{
  timestamp: Date
  method: string
  params: object
  result: 'success' | 'error'
  duration: number
  error?: string
}
```

### 配置参数
```yaml
wps_api:
  base_url: "https://openapi.wps.cn"
  timeout: 30000  # 30秒
  retry_times: 3
  retry_interval: 1000  # 1秒
  rate_limit: 100  # 次/分钟
  token_refresh_before: 300  # 提前5分钟刷新
```

## 测试要求

### 单元测试
- [ ] Token管理器测试（100%覆盖率）
- [ ] 请求队列测试
- [ ] 每个API方法测试
- [ ] 错误处理测试

### 集成测试
- [ ] 完整CRUD流程测试
- [ ] 并发请求测试
- [ ] 限流测试
- [ ] Token失效恢复测试

### 性能测试
- [ ] 查询性能（< 500ms）
- [ ] 批量插入性能（100条 < 3s）
- [ ] 文档生成性能（< 10s）

## 交付物

1. **源代码**: `src/tools/wps-api/`
2. **类型定义**: `src/tools/wps-api/types.ts`
3. **单元测试**: `tests/tools/wps-api/`
4. **使用文档**: `docs/tools/wps-api.md`
5. **配置示例**: `config/wps.example.yaml`

## 验收标准

- [ ] 所有接口实现并通过测试
- [ ] 请求队列正常工作，不超限制
- [ ] Token自动刷新无中断
- [ ] 错误处理完善，可恢复
- [ ] 文档和示例完整
- [ ] 代码审查通过

## 注意事项

1. **严格遵守WPS API限流**（100次/分钟）
2. **Token有效期2小时**，需提前刷新
3. **文件ID和文件夹ID需持久化存储**
4. **批量操作优先**，减少API调用次数
5. **所有操作需记录日志**，便于问题排查

## 相关文档

- [详细设计方案 - WPS集成](../design/detailed-design-v2.md#wps开放平台集成方案)
- WPS开放平台API文档：https://open.wps.cn/docs
- [技术可行性分析 - WPS能力边界](../analysis/technical-feasibility-analysis.md#wps云文档能力边界深度分析)

---

**创建时间**: 2026-03-17  
**负责人**: 待分配  
**状态**: 待开始  
**依赖**: TASK-001完成
