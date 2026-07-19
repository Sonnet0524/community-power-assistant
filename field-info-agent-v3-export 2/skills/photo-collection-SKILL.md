---
skill_id: photo-collection
name: 照片采集与标注
version: 3.0.0
type: openclaw-skill
category: collection
priority: P0
---

# Photo Collection Skill - 照片采集

> 📸 使用OpenClaw原生读图能力的照片采集与标注

## 一、功能定位

**核心能力**:
- 接收现场照片
- 自动保存到文件夹
- OpenClaw读图理解
- 生成文字标注
- 关联到工作记录

**与旧版区别**:
```yaml
旧版 (v2.x):
  - 调用KIMI多模态API
  - 需要网络请求
  - 复杂JSON解析

新版 (v3.0) - 极简版:
  - 使用OpenClaw内置读图能力
  - 本地处理
  - 简洁文字描述
```

## 二、触发方式

### 2.1 自动触发

```yaml
triggers:
  message_type: "image"
  
  conditions:
    - session.state == "collecting"
    - session.current_phase in ["power_room", "customer_visit", "emergency"]
```

### 2.2 手动触发

```
用户: "分析一下这张照片"
用户: "这是什么设备？"
用户: "保存这张照片"
```

## 三、处理流程

### 3.1 照片接收与保存

```
用户发送图片
    ↓
Agent接收图片消息（WeCom Channel）
    ↓
生成文件名: IMG_{timestamp}_{sequence}.jpg
    ↓
保存到: ./field-data/communities/{小区}/{日期}/photos/
    ↓
记录到当前work-record.md
    ↓
使用OpenClaw读图分析
    ↓
更新照片描述
    ↓
返回用户确认
```

### 3.2 OpenClaw读图配置

```yaml
# openclaw.config.yaml
llm:
  vision_analysis:
    enabled: true
    model: "default"  # 使用OpenClaw默认多模态能力
    
    prompts:
      # 配电房照片分析
      power_room: |
        请分析这张配电房照片：
        1. 识别设备类型和数量
        2. 描述整体环境（整洁度、照明、通道）
        3. 指出明显的安全隐患
        4. 一句话总结
        
      # 变压器照片分析
      transformer: |
        请分析这张变压器照片：
        1. 识别设备型号（如能看到铭牌）
        2. 观察外观状态（清洁度、锈蚀、漏油）
        3. 检查连接部位
        4. 一句话总结
        
      # 通用照片分析
      general: |
        请描述这张照片：
        1. 主要对象是什么？
        2. 整体状态如何？
        3. 有无明显问题？
        4. 一句话总结
```

### 3.3 照片命名规范

```
格式: IMG_{YYYYMMDD}_{HHMMSS}_{SEQ}.jpg

示例:
- IMG_20240317_093015_01.jpg  # 配电房入口
- IMG_20240317_093052_02.jpg  # 1#变压器铭牌
- IMG_20240317_093118_03.jpg  # 2#变压器整体
- IMG_20240317_101520_04.jpg  # 客户走访照片
```

### 3.4 照片标注格式

在work-record.md中记录:

```markdown
### 照片采集记录

#### 配电房照片
1. [IMG_20240317_093015_01.jpg](./photos/IMG_20240317_093015_01.jpg)
   - **时间**: 09:30:15
   - **AI描述**: 配电房入口，环境整洁，照明正常，通道畅通
   - **人工标注**: 1号配电房入口，3号楼地下室

2. [IMG_20240317_093052_02.jpg](./photos/IMG_20240317_093052_02.jpg)
   - **时间**: 09:30:52
   - **AI描述**: 变压器铭牌清晰可见，型号SCB11-500/10，外观正常
   - **人工标注**: 1#变压器铭牌

3. [IMG_20240317_093118_03.jpg](./photos/IMG_20240317_093118_03.jpg)
   - **时间**: 09:31:18
   - **AI描述**: 变压器整体照片，外观清洁，⚠️ 油位偏低需注意
   - **人工标注**: 2#变压器，油位偏低待复查
```

## 四、交互示例

### 4.1 正常采集流程

```
用户: [发送配电房照片]

Agent:
📸 照片已接收并保存
文件名: IMG_20240317_093015_01.jpg

🔍 AI识别结果:
• 对象: 配电房入口
• 环境: 整洁，照明正常
• 状态: 良好
• 问题: 未发现明显异常

✅ 已记录到工作档案
继续拍摄下一张照片，或发送"完成"
```

### 4.2 发现问题场景

```
用户: [发送变压器照片]

Agent:
📸 照片已接收并保存
文件名: IMG_20240317_093118_03.jpg

🔍 AI识别结果:
• 对象: 干式变压器
• 型号: 铭牌显示SCB11-630/10
• 状态: ⚠️ 油位偏低（约正常位置的60%）
• 建议: 建议1个月内复查油位

⚠️ 发现问题已标记
是否添加详细说明？[添加说明] [继续拍摄]
```

### 4.3 手动分析请求

```
用户: "分析一下这张照片是什么设备"

Agent:
🔍 照片分析结果:

这张照片显示的是 **高压开关柜**。

• 设备类型: KYN28A-12型中置式开关柜
• 观察状态: 外观正常，指示灯显示运行状态
• 注意事项: 柜门关闭良好，无异常声音
• 建议: 继续保持正常巡检
```

## 五、文件操作

### 5.1 保存照片

```typescript
// 伪代码
async function savePhoto(imageData: Buffer, context: Context) {
  // 1. 生成文件名
  const timestamp = new Date().toISOString()
    .replace(/[-:]/g, '')
    .replace(/\..*/, '');
  const seq = getNextSequence();
  const filename = `IMG_${timestamp}_${seq.toString().padStart(2, '0')}.jpg`;
  
  // 2. 确定路径
  const path = `./field-data/communities/${context.community}/${context.date}/photos/${filename}`;
  
  // 3. 保存文件
  await tools.write_file({
    file_path: path,
    content: imageData,
    encoding: 'binary'
  });
  
  // 4. 使用OpenClaw读图
  const analysis = await tools.vision_analyze({
    image_path: path,
    prompt: getPromptForPhase(context.phase)
  });
  
  // 5. 更新工作记录
  await updateWorkRecord(context, {
    filename,
    timestamp,
    analysis
  });
  
  return { filename, path, analysis };
}
```

### 5.2 读取照片

```typescript
// 在工作记录中引用
function generatePhotoEntry(photo: PhotoInfo): string {
  return `
#### ${photo.filename}
- **拍摄时间**: ${photo.timestamp}
- **AI描述**: ${photo.analysis.summary}
- **位置**: ${photo.analysis.location || '待补充'}
- **状态**: ${photo.analysis.status || '正常'}
- **问题**: ${photo.analysis.issues || '无'}
- **文件**: [查看照片](${photo.path})
`;
}
```

## 六、与Session集成

### 6.1 Session中记录照片

```yaml
session:
  community: "阳光小区"
  date: "2024-03-17"
  phase: "power_room"
  photos:
    - id: "IMG_20240317_093015_01"
      type: "entrance"
      filename: "IMG_20240317_093015_01.jpg"
      description: "配电房入口"
      ai_analysis: "环境整洁，照明正常"
      
    - id: "IMG_20240317_093052_02"
      type: "nameplate"
      filename: "IMG_20240317_093052_02.jpg"
      description: "1#变压器铭牌"
      ai_analysis: "型号SCB11-500/10，清晰可见"
```

### 6.2 阶段关联

```typescript
const photoTypes = {
  power_room: {
    entrance: "配电房入口",
    nameplate: "变压器铭牌",
    equipment: "设备整体",
    environment: "环境照片",
    defect: "缺陷照片"
  },
  customer_visit: {
    customer: "客户合影",
    meter: "电表照片",
    issue: "问题现场"
  },
  emergency: {
    entry_point: "进入点",
    parking: "停放点",
    access_point: "接入点"
  }
};
```

## 七、错误处理

### 7.1 常见错误

| 错误类型 | 处理方式 |
|---------|----------|
| **文件保存失败** | 重试3次，通知用户 |
| **读图失败** | 保存照片，提示"需人工标注" |
| **存储空间不足** | 清理旧照片，提示用户 |
| **文件名冲突** | 自动添加序列号 |

### 7.2 降级处理

```
如果OpenClaw读图失败:
  1. 仍然保存照片文件
  2. 在work-record.md中标记"待人工分析"
  3. 提示用户: "照片已保存，AI分析暂时不可用，请手动添加描述"
```

## 八、配置参数

```yaml
# openclaw.config.yaml
skills:
  photo_collection:
    enabled: true
    priority: high
    
    config:
      # 存储配置
      base_path: "./field-data"
      photo_subdir: "photos"
      
      # 命名配置
      filename_format: "IMG_{timestamp}_{seq}"
      sequence_width: 2
      
      # 读图配置
      vision_analysis:
        enabled: true
        timeout: 30  # 秒
        retry_count: 3
        
      # 质量配置
      max_photos_per_session: 50
      auto_analyze: true
      
    # 提示词配置
    prompts:
      power_room: "分析配电房照片，识别设备，描述环境，指出问题"
      transformer: "分析变压器照片，识别型号，检查外观，注意油位"
      general: "描述照片内容，指出主要对象和状态"
```

---

**技能版本**: 3.0.0  
**适用Agent**: field-collector  
**依赖**: OpenClaw内置读图能力（无需外部API）
