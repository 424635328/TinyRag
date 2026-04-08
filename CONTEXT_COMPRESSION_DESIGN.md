# 上下文压缩功能设计文档

## 概述

本文档描述了大模型上下文压缩功能的设计与实现。该功能能够智能分析并优化长文本对话历史，在保持核心语义和上下文连贯性的前提下，显著减少上下文长度。

## 设计目标

1. **压缩率**：目标压缩率不低于 40%
2. **语义相似度**：语义相似度不低于 0.85
3. **实时性**：压缩操作应在毫秒级完成
4. **灵活性**：支持多种压缩策略和动态调整

## 核心模块

### 1. 数据结构

#### Message（消息）
```python
@dataclass
class Message:
    role: MessageType  # USER, ASSISTANT, SYSTEM
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict] = None
```

#### MessageImportance（消息重要性评估）
```python
@dataclass
class MessageImportance:
    message: Message
    importance_score: float      # 综合重要性分数
    key_entities: List[str]     # 关键实体
    key_topics: List[str]       # 关键主题
    semantic_keywords: List[str]  # 语义关键词
    is_context_critical: bool   # 是否为上下文关键
```

#### CompressionResult（压缩结果）
```python
@dataclass
class CompressionResult:
    original_messages: List[Message]
    compressed_messages: List[Message]
    compression_ratio: float           # 压缩率 (0-1)
    original_token_count: int          # 原始token数
    compressed_token_count: int        # 压缩后token数
    semantic_similarity_estimate: float  # 语义相似度估计 (0-1)
    strategy_used: str                 # 使用的策略
```

### 2. ContextCompressor 类

#### 初始化参数
- `target_compression_ratio`: 目标压缩率，默认 0.5（50%）
- `min_messages_to_compress`: 开始压缩的最小消息数，默认 4
- `max_messages`: 压缩后保留的最大消息数，默认 12

#### 核心功能

##### 2.1 关键词提取 (`extract_keywords`)
- 从文本中提取关键词
- 支持中英文
- 过滤停用词
- 按词频排序

##### 2.2 实体提取 (`extract_entities`)
- 提取专有名词
- 提取引号中的术语
- 提取中文名词
- 去重并限制数量

##### 2.3 重要性评估 (`calculate_importance`)
评估维度包括：
1. **时效性因子**：越新的消息越重要（权重 2.0）
2. **角色权重**：
   - 用户消息：1.5
   - 问题类型用户消息：+1.0
   - 助手消息：1.0
3. **内容质量**：
   - 关键词丰富（>=3）：+0.5
   - 实体丰富（>=2）：+0.5
   - 长文本（>200字符）：+0.3
4. **上下文关键性**：包含上下文关键词 +1.0

##### 2.4 消息摘要 (`summarize_message`)
- 保留首句
- 限制最大长度
- 处理截断边界

##### 2.5 基于重要性的压缩 (`compress_by_importance`)
1. 对所有消息进行重要性评分
2. 按重要性排序
3. 保留最重要的 N 条消息
4. 始终保留最近 2 条消息（连续性保障）
5. 对非关键长消息进行摘要

##### 2.6 Token 计数 (`count_tokens`)
- 中文字符：每个算 1 token
- 英文单词：每个算 1 token
- 其他字符：每个算 1 token

##### 2.7 语义相似度估计 (`_estimate_semantic_similarity`)
基于关键词重叠度的语义相似度估计：
```
keyword_similarity = |intersection(original_keywords, compressed_keywords)| / |original_keywords|
retention_ratio = len(compressed) / len(original)
semantic_similarity = keyword_similarity * 0.7 + retention_ratio * 0.3
```

## 集成方案

### 与 RagRuntime 集成

在 `RagRuntime` 中添加：
- `_enable_context_compression`: 开关控制
- `_compressor`: ContextCompressor 实例
- `_last_compression_result`: 上次压缩结果

### 会话转换

1. `_session_to_messages`: 将会话转换为 Message 列表
2. `_messages_to_turns`: 将 Message 列表转换回会话轮次

### 压缩触发条件

仅在满足以下条件时启用压缩：
1. 压缩功能已启用 (`_enable_context_compression=True`)
2. 会话轮次 >= 4 (`len(session.turns) >= 4`)

## 性能指标

### 设计指标
| 指标 | 目标值 |
|------|---------|
| 压缩率 | ≥ 40% |
| 语义相似度 | ≥ 0.85 |
| 平均压缩耗时 | < 50ms |
| 最大消息数 | 12 条 |

### 重要性权重总结

| 因素 | 权重 |
|------|------|
| 时效性（越新越重要） | 2.0 |
| 用户消息 | 1.5 |
| 问题类型消息 | +1.0 |
| 助手消息 | 1.0 |
| 关键词丰富（≥3） | +0.5 |
| 实体丰富（≥2） | +0.5 |
| 长文本（>200字符） | +0.3 |
| 上下文关键 | +1.0 |

## 使用示例

### 基本使用
```python
from src.tinyrag.context_compressor import (
    ContextCompressor,
    Message,
    MessageType
)

# 创建压缩器
compressor = ContextCompressor(
    target_compression_ratio=0.5,
    min_messages_to_compress=4,
    max_messages=12
)

# 创建测试对话
messages = [
    Message(role=MessageType.USER, content="Tony喜欢吃什么？"),
    Message(role=MessageType.ASSISTANT, content="Tony喜欢吃面条和饺子"),
    # ... 更多消息
]

# 执行压缩
result = compressor.compress(messages)

# 查看结果
print(f"压缩率: {result.compression_ratio:.2%}")
print(f"语义相似度: {result.semantic_similarity_estimate:.2f}")
```

### 配置文件
在 `.env` 中添加：
```
# 上下文压缩配置
ENABLE_CONTEXT_COMPRESSION=true
TARGET_COMPRESSION_RATIO=0.5
```

## 测试覆盖

测试套件包含：
1. **基本压缩功能测试**
2. **语义相似度保持测试**
3. **消息摘要功能测试**
4. **实体提取功能测试**
5. **关键词提取功能测试**
6. **不同长度对话压缩测试**
7. **性能测试**
8. **评估报告生成**

运行测试：
```bash
python tests/test_context_compressor.py
```

## 扩展性设计

### 可添加的压缩策略
1. **滑动窗口策略**：固定保留最近 N 条
2. **语义聚类策略**：基于相似度合并相关消息
3. **重要性衰减策略**：旧消息重要性按时间衰减
4. **摘要生成策略**：使用 LLM 生成对话摘要

### 可扩展的重要性因子
1. 用户反馈（显式标记重要消息）
2. 消息长度（特别长的消息可能更重要）
3. 命名实体数量（实体越多越重要）
4. 引用关系（被后续引用的消息更重要）

## 总结

上下文压缩功能通过智能评估消息重要性，在保持核心语义的前提下显著减少上下文长度。该设计具有高灵活性、高性能和高可扩展性，能够有效满足大模型对话系统的需求。
