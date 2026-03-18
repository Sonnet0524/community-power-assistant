# Field Info Agent - 业务逻辑图

> 本文档详细描述了Field Info Agent的完整业务逻辑和流程

---

## 一、整体业务架构图

```mermaid
graph TB
    subgraph 用户层
        A[客户经理/抢修人员<br/>企业微信APP] --> B[文字消息]
        A --> C[照片消息]
        A --> D[位置消息]
    end

    subgraph OpenClaw核心层
        B --> E[WeCom Channel]
        C --> E
        D --> E
        E --> F[Session Manager<br/>会话状态管理]
        F --> G[Intent Recognition<br/>意图识别]
        G --> H{工作类型判断}
    end

    subgraph Skills技能层
        H -->|驻点工作| I[StationWorkGuide<br/>驻点工作引导]
        H -->|照片分析| J[VisionAnalysis<br/>AI照片分析]
        H -->|生成文档| K[DocGeneration<br/>文档生成]
        H -->|应急处置| L[EmergencyGuide<br/>应急指引]
    end

    subgraph Tools工具层
        I --> M[kimi-vision<br/>KIMI多模态]
        I --> N[postgres-query<br/>PostgreSQL]
        I --> O[minio-storage<br/>MinIO存储]
        J --> M
        K --> P[docx-generator<br/>Word生成]
        K --> O
        K --> N
        L --> N
    end

    subgraph 数据层
        N --> Q[(PostgreSQL<br/>结构化数据)]
        O --> R[(MinIO<br/>照片/文档)]
        F --> S[(Redis<br/>会话缓存)]
    end

    subgraph 输出层
        P --> T[Word文档]
        E --> U[企业微信消息]
        I --> U
        J --> U
        K --> U
        L --> U
    end
```

---

## 二、核心业务流程图

### 2.1 驻点工作全流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Field Agent
    participant S as Session Manager
    participant V as Vision Skill
    participant D as Doc Skill
    participant DB as PostgreSQL
    participant M as MinIO

    U->>A: "我今天要去阳光社区驻点"
    A->>S: 创建Session
    S->>DB: 查询社区历史
    DB-->>S: 返回历史记录
    S-->>A: Session创建完成
    A-->>U: 📋 已准备阳光社区工作<br/>历史3次驻点，重点客户2户...

    U->>A: "开始配电房检查"
    A->>S: 更新状态: collecting
    S-->>A: 当前阶段: power_room
    A-->>U: 🔌 配电房检查引导<br/>第1项：变压器整体照片

    U->>A: [发送照片]
    A->>M: 保存照片
    M-->>A: 返回URL
    A->>V: 分析照片
    V->>DB: 保存分析结果
    V-->>A: 设备识别结果
    A-->>U: 📸 照片已保存<br/>设备：箱式变压器，状态正常

    U->>A: "配电房检查好了"
    A->>S: 更新状态: analyzing
    A->>V: 批量分析所有照片
    V-->>A: 分析完成，发现1处异常
    A-->>U: ✅ 分析完成<br/>发现：变压器油位偏低

    U->>A: "生成报告"
    A->>D: 生成驻点工作记录
    D->>DB: 获取完整数据
    D->>M: 下载照片
    D->>M: 生成Word文档
    M-->>D: 返回文档URL
    D->>DB: 记录文档信息
    D-->>A: 文档生成完成
    A-->>U: 📄 报告已生成<br/>[下载链接]
    A->>S: 更新状态: completed
```

---

## 三、状态流转图

### 3.1 Session状态机

```mermaid
stateDiagram-v2
    [*] --> IDLE: 系统启动
    
    IDLE --> PREPARING: 用户说"我要去XX社区"
    PREPARING --> COLLECTING: 确认开始工作
    
    state COLLECTING {
        [*] --> POWER_ROOM: "配电房检查"
        [*] --> CUSTOMER_VISIT: "客户走访"
        [*] --> EMERGENCY: "应急通道"
        
        POWER_ROOM --> POWER_ROOM: 继续采集
        CUSTOMER_VISIT --> CUSTOMER_VISIT: 继续走访
        EMERGENCY --> EMERGENCY: 继续标记
        
        POWER_ROOM --> [*]: 阶段完成
        CUSTOMER_VISIT --> [*]: 阶段完成
        EMERGENCY --> [*]: 阶段完成
    }
    
    COLLECTING --> ANALYZING: "采集完成"
    ANALYZING --> COMPLETED: 分析完成
    COMPLETED --> [*]: 文档生成
    
    COLLECTING --> IDLE: /cancel 取消
    ANALYZING --> IDLE: 超时/取消
```

---

## 四、技能详细流程

### 4.1 StationWorkGuide - 驻点工作引导

```mermaid
flowchart TD
    Start([开始]) --> ReceiveMsg[接收用户消息]
    
    ReceiveMsg --> IntentCheck{意图识别}
    IntentCheck -->|开始驻点| InitSession[初始化Session]
    IntentCheck -->|配电房| PowerRoom[进入配电房阶段]
    IntentCheck -->|客户走访| Customer[进入走访阶段]
    IntentCheck -->|应急通道| Emergency[进入应急阶段]
    IntentCheck -->|完成| Complete[进入完成阶段]
    IntentCheck -->|其他| Prompt[友好提示引导]
    
    InitSession --> QueryHistory[查询社区历史]
    QueryHistory --> GenList[生成工作清单]
    GenList --> SendGuide[发送引导消息]
    SendGuide --> ReceiveMsg
    
    PowerRoom --> CheckItem{检查当前项}
    CheckItem -->|需要照片| RequestPhoto[请求拍摄照片]
    CheckItem -->|需要文字| RequestText[请求文字描述]
    CheckItem -->|完成| NextItem{还有下一项?}
    
    RequestPhoto --> UserPhoto[用户发送照片]
    UserPhoto --> SavePhoto[保存照片]
    SavePhoto --> AnalyzePhoto[AI分析照片]
    AnalyzePhoto --> SendResult[发送分析结果]
    SendResult --> CheckItem
    
    RequestText --> UserText[用户发送文字]
    UserText --> SaveText[保存记录]
    SaveText --> CheckItem
    
    NextItem -->|是| CheckItem
    NextItem -->|否| PhaseComplete[阶段完成]
    PhaseComplete --> AskContinue{是否继续?}
    
    AskContinue -->|继续其他| ReceiveMsg
    AskContinue -->|完成采集| Complete
    
    Complete --> BatchAnalyze[批量分析照片]
    BatchAnalyze --> GenReport[生成工作报告]
    GenReport --> Archive[归档到知识库]
    Archive --> End([结束])
    
    Prompt --> ReceiveMsg
```

### 4.2 VisionAnalysis - 照片AI分析

```mermaid
flowchart TD
    Start([照片接收]) --> Download[下载照片]
    Download --> Preprocess[预处理照片]
    
    Preprocess --> ParallelAnalysis[并行分析]
    
    ParallelAnalysis --> DeviceDetect[设备识别]
    ParallelAnalysis --> DefectDetect[缺陷检测]
    ParallelAnalysis --> StatusEval[状态评估]
    
    DeviceDetect --> DeviceResult[设备类型<br/>型号/规格]
    DefectDetect --> DefectResult[缺陷类型<br/>位置/严重程度]
    StatusEval --> StatusResult[运行状态<br/>健康评分]
    
    DeviceResult --> Merge[结果合并]
    DefectResult --> Merge
    StatusResult --> Merge
    
    Merge --> GenerateDesc[生成自然语言描述]
    GenerateDesc --> SaveResult[保存分析结果]
    SaveResult --> ReturnResult[返回分析结果]
    ReturnResult --> End([结束])
    
    subgraph 分析触发时机
        T1[实时：单张照片接收]
        T2[批量：阶段完成时]
        T3[总结：报告生成时]
    end
```

### 4.3 DocGeneration - 文档生成

```mermaid
flowchart TD
    Start([生成请求]) --> GetSession[获取Session数据]
    
    GetSession --> GetBasic[获取基本信息]
    GetSession --> GetCollection[获取采集数据]
    GetSession --> GetAnalysis[获取分析结果]
    GetSession --> GetPhotos[获取照片列表]
    
    GetBasic --> SelectTemplate[选择文档模板]
    GetCollection --> FormatData[格式化数据]
    GetAnalysis --> FormatData
    GetPhotos --> DownloadPhotos[下载照片]
    
    SelectTemplate --> LoadTemplate[加载Word模板]
    FormatData --> FillData[填充数据字段]
    DownloadPhotos --> InsertPhotos[插入照片]
    
    LoadTemplate --> RenderDoc[渲染文档]
    FillData --> RenderDoc
    InsertPhotos --> RenderDoc
    
    RenderDoc --> GenTables[生成表格]
    GenTables --> ApplyStyle[应用样式]
    ApplyStyle --> SaveTemp[保存临时文件]
    
    SaveTemp --> UploadMinio[上传到MinIO]
    UploadMinio --> RecordDB[记录到数据库]
    RecordDB --> GenUrl[生成下载链接]
    GenUrl --> NotifyUser[通知用户]
    NotifyUser --> End([结束])
```

### 4.4 EmergencyGuide - 应急处置

```mermaid
flowchart TD
    Start([应急触发]) --> DetectUrgent{检测紧急关键词}
    
    DetectUrgent -->|停电/故障| PowerOutage[停电应急流程]
    DetectUrgent -->|设备故障| EquipmentFail[设备故障流程]
    DetectUrgent -->|客户投诉| Complaint[紧急投诉处理]
    
    PowerOutage --> QueryInfo[查询应急信息]
    EquipmentFail --> QueryInfo
    Complaint --> QueryInfo
    
    QueryInfo --> GetCommunity[获取社区信息]
    QueryInfo --> GetSensitive[获取敏感客户]
    QueryInfo --> GetEmergencyPlan[获取应急方案]
    
    GetCommunity --> AnalyzeImpact[分析影响范围]
    GetSensitive --> ListSensitive[列出敏感客户]
    GetEmergencyPlan --> ShowGuide[展示应急指引]
    
    AnalyzeImpact --> SendAlert[发送应急通知]
    ListSensitive --> SendAlert
    ShowGuide --> SendAlert
    
    SendAlert --> UserAction{用户操作}
    
    UserAction -->|联系客户| CallCustomer[一键拨打]
    UserAction -->|查看指引| ViewGuide[查看详细指引]
    UserAction -->|导航位置| Navigation[导航到接入点]
    UserAction -->|记录进展| RecordProgress[记录处理进展]
    
    CallCustomer --> Continue{继续处理?}
    ViewGuide --> Continue
    Navigation --> Continue
    RecordProgress --> Continue
    
    Continue -->|是| UserAction
    Continue -->|否| GenReport[生成应急报告]
    GenReport --> Archive[归档应急记录]
    Archive --> End([结束])
```

---

## 五、数据流转图

### 5.1 数据存储架构

```mermaid
graph TB
    subgraph 用户输入
        A1[文字消息]
        A2[照片]
        A3[位置信息]
    end

    subgraph OpenClaw处理
        B[Channel Handler] --> C[Session Manager]
        C --> D[Skills处理]
    end

    subgraph 数据分类存储
        D -->|结构化数据| E1[PostgreSQL]
        D -->|非结构化数据| E2[MinIO]
        D -->|会话状态| E3[Redis]
    end

    subgraph PostgreSQL表
        E1 --> F1[field_sessions<br/>会话表]
        E1 --> F2[field_collections<br/>采集记录表]
        E1 --> F3[photo_analysis<br/>照片分析表]
        E1 --> F4[generated_documents<br/>生成文档表]
        E1 --> F5[community_info<br/>社区信息表]
    end

    subgraph MinIO存储
        E2 --> G1[/photos/<br/>照片存储/]
        E2 --> G2[/documents/<br/>Word文档/]
        E2 --> G3[/templates/<br/>文档模板/]
    end

    subgraph Redis缓存
        E3 --> H1[session:{userId}<br/>活跃会话]
        E3 --> H2[lock:{userId}<br/>并发锁]
    end

    subgraph 数据输出
        F2 --> I[工作记录]
        F4 --> I
        G2 --> I
    end
```

### 5.2 照片处理数据流

```mermaid
sequenceDiagram
    participant U as 用户
    participant WC as 企业微信
    participant CH as WeCom Channel
    participant VA as VisionAnalysis
    participant KM as KIMI Vision
    participant DB as PostgreSQL
    participant MN as MinIO

    U->>WC: 发送照片
    WC->>CH: 图片消息
    CH->>MN: 下载保存
    MN-->>CH: 返回URL
    CH->>VA: 触发分析
    
    VA->>KM: 请求分析<br/>image_url
    KM->>KM: 多模态识别<br/>设备/缺陷/状态
    KM-->>VA: 返回结构化结果
    
    VA->>DB: 保存分析结果<br/>photo_analysis表
    VA->>CH: 返回分析摘要
    CH->>WC: 发送分析结果
    WC->>U: 📸 照片已分析<br/>设备：箱变，状态正常
```

---

## 六、集成架构图

### 6.1 系统整体集成

```mermaid
graph TB
    subgraph 外部服务
        W1[企业微信服务器]
        W2[KIMI K2.5 API]
    end

    subgraph 内部服务
        subgraph OpenClaw运行时
            G[OpenClaw Gateway]
            SM[Session Manager]
        end
        
        subgraph Skills
            S1[StationWorkGuide]
            S2[VisionAnalysis]
            S3[DocGeneration]
            S4[EmergencyGuide]
        end
        
        subgraph Tools
            T1[WeCom API Tool]
            T2[KIMI Vision Tool]
            T3[Docx Generator]
            T4[PostgreSQL Query]
            T5[MinIO Storage]
        end
    end

    subgraph 数据存储
        D1[(PostgreSQL)]
        D2[(MinIO)]
        D3[(Redis)]
    end

    W1 <-->|HTTPS回调| G
    G --> SM
    SM --> S1
    SM --> S2
    SM --> S3
    SM --> S4
    
    S1 --> T4
    S1 --> T5
    S2 --> T2
    S3 --> T3
    S3 --> T5
    S4 --> T4
    
    T1 --> W1
    T2 --> W2
    T4 --> D1
    T5 --> D2
    SM --> D3
```

---

## 七、业务场景流程

### 7.1 场景1：完整的驻点工作流程

```mermaid
journey
    title 阳光社区驻点工作完整流程
    section 出发前
        启动驻点工作: 5: 用户
        接收工作清单: 5: Agent
    section 配电房
        到达配电房: 5: 用户
        拍摄变压器照片: 5: 用户
        AI分析照片: 5: Agent
        记录设备状态: 4: 用户
        检查高压侧: 5: 用户
        检查低压侧: 5: 用户
        拍摄环境照片: 4: 用户
    section 客户走访
        开始走访: 5: 用户
        走访重点客户: 5: 用户
        记录用电情况: 4: 用户
        排查安全隐患: 5: 用户
    section 完成
        确认采集完成: 5: 用户
        批量分析照片: 5: Agent
        生成工作报告: 5: Agent
        发送文档链接: 5: Agent
```

### 7.2 场景2：应急处置流程

```mermaid
journey
    title 阳光小区停电应急响应
    section 应急启动
        报告停电故障: 5: 抢修人员
        Agent启动应急: 5: Agent
        查询应急资料: 5: Agent
    section 影响分析
        确认影响范围: 4: 抢修人员
        分析敏感客户: 5: Agent
        列出关怀清单: 5: Agent
    section 现场处理
        联系物业确认: 4: 抢修人员
        安抚敏感客户: 5: 抢修人员
        查看应急指引: 5: Agent
        导航到接入点: 4: Agent
    section 记录归档
        记录处理过程: 5: 抢修人员
        生成应急报告: 5: Agent
        更新知识库: 5: Agent
```

---

## 八、关键决策点

### 8.1 技术决策

| 决策点 | 选择方案 | 决策理由 |
|--------|----------|----------|
| **语音输入** | 仅文字输入 | 用户使用语音输入法转文字 |
| **图像识别** | KIMI 2.5多模态 | 国产模型，理解能力强，合规性好 |
| **文档存储** | 本地MinIO | 数据主权，完全自主控制 |
| **数据存储** | PostgreSQL | 结构化数据，版本化管理 |
| **会话管理** | Redis | 高性能，支持过期自动清理 |

### 8.2 业务决策

| 决策点 | 选择方案 | 决策理由 |
|--------|----------|----------|
| **交互方式** | 自然语言（零命令） | 降低学习成本，提高接受度 |
| **照片分析** | 实时+批量结合 | 采集时简单确认，完成后深度分析 |
| **文档生成** | 自动+手动触发 | 阶段完成自动生成，支持随时生成 |
| **数据版本** | 全版本化 | 支持历史追溯，永不丢失 |

---

## 九、异常处理流程

```mermaid
flowchart TD
    Start([异常发生]) --> Classify{异常分类}
    
    Classify -->|网络异常| Network[网络处理]
    Classify -->|AI分析失败| AIFail[AI容错]
    Classify -->|用户误操作| UserErr[用户引导]
    Classify -->|系统错误| SysErr[系统恢复]
    
    Network --> Retry[自动重试3次]
    Retry --> RetrySuccess{成功?}
    RetrySuccess -->|是| Continue[继续流程]
    RetrySuccess -->|否| NotifyNet[通知网络问题]
    NotifyNet --> PromptRetry[提示用户重试]
    
    AIFail --> UseCache[使用缓存结果]
    UseCache --> CacheExist{有缓存?}
    CacheExist -->|是| ReturnCache[返回缓存]
    CacheExist -->|否| ManualInput[提示手动输入]
    
    UserErr --> FriendlyPrompt[友好提示]
    FriendlyPrompt --> GuideBack[引导回到正轨]
    
    SysErr --> LogError[记录错误日志]
    LogError --> SaveProgress[保存当前进度]
    SaveProgress --> NotifyAdmin[通知管理员]
    
    Continue --> End([结束])
    ReturnCache --> End
    ManualInput --> End
    GuideBack --> End
    NotifyAdmin --> End
```

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-18  
**作者**: PM Agent
