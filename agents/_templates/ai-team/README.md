# AI Team 模板

> 🤖 向量嵌入、语义搜索、机器学习

---

## 职责范围

- **向量嵌入**: 文本向量化、嵌入模型
- **语义搜索**: 向量索引、相似度计算
- **机器学习**: 模型训练、调优、评估

## 技术栈

- Python
- 嵌入模型（sentence-transformers, OpenAI 等）
- 向量数据库（FAISS, Milvus 等）
- ML 框架（PyTorch, TensorFlow 等）

## 边界

**负责**:
- `src/ai/`
- `src/embedding/`
- `src/search/`
- `models/`

**不负责**:
- 数据处理（Core Team）
- 系统集成（Integration Team）
- 测试框架（Test Team）

## 使用方式

```bash
# 复制模板
cp -r agents/_templates/ai-team agents/my-ai-team

# 定制 AGENTS.md
vim agents/my-ai-team/AGENTS.md

# 配置并注册
# 详见 TEMPLATE-GUIDE.md
```

---

**模板版本**: 1.0  
**最后更新**: 2026-03-08
