# TinyRag

一个从零开始的 LangChain RAG 最小项目，默认走本地轻量方案：

- Embedding: `BAAI/bge-small-zh-v1.5`
- Vector Store: `FAISS`
- LLM: `Ollama + qwen2.5:1.5b`

同时也支持切换到 `DeepSeek API`，不需要改核心代码，只要改环境变量。

## 项目结构

```text
.
├─ knowledge/knowledge.txt
├─ knowledge/guide.md
├─ src/tinyrag/config.py
├─ src/tinyrag/prompting.py
├─ src/tinyrag/rag.py
├─ src/tinyrag/runtime.py
├─ src/tinyrag/context_compressor.py
├─ src/tinyrag/web.py
├─ web/index.html
├─ web/chat.html
├─ web/styles.css
├─ web/chat.css
├─ web/app.js
├─ web/chat.js
├─ web/test-markdown.html
├─ .env.example
├─ langchain_rag.py
├─ web_app.py
├─ CONTEXT_COMPRESSION_DESIGN.md
├─ CONTEXT_COMPRESSION_EVALUATION.md
└─ requirements.txt
```

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 准备模型

### 方案 A：本地 Ollama

先启动 Ollama，并拉取模型：

```bash
ollama pull qwen2.5:1.5b
ollama serve
```

默认配置已经是 `ollama`，不改 `.env` 也可以直接跑。

### 方案 B：DeepSeek API

把 `.env.example` 复制为 `.env`，然后填写：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=你的密钥
```

说明：

- 我没有把真实密钥写进仓库文件，避免泄漏。
- LangChain 会通过 OpenAI 兼容接口访问 DeepSeek。

## 3. 知识库组织方式

现在默认读取整个 `knowledge/` 目录，而不是单个文本文件。

支持格式：

- `.txt`
- `.md`
- `.markdown`
- `.pdf`
- `.csv`
- `.tsv`
- `.json`
- `.jsonl`
- `.yaml`
- `.yml`
- `.xlsx`
- `.xlsm`
- `.xltx`
- `.xltm`

热重载行为：

- 新增文件：下一次提问前自动重建索引
- 修改文件：下一次提问前自动重建索引
- 删除文件：下一次提问前自动重建索引

示例：

```text
knowledge/
├─ knowledge.txt
├─ guide.md
└─ handbook.pdf
```

## 4. 如何扩展知识库

最简单的扩展方式，就是把新的资料文件直接放进 `knowledge/` 目录。

推荐步骤：

1. 准备资料文件，格式可以是文本、Markdown、PDF、CSV、TSV、JSON、YAML 或 Excel
2. 把文件复制到 `knowledge/` 目录，或者放到它的子目录中
3. 保持文件内容尽量清晰，避免扫描质量很差的 PDF
4. 重新提问一次，系统会在下一次请求前自动检测变更并重建索引

推荐目录结构：

```text
knowledge/
├─ company/
│  ├─ reimbursement.md
│  └─ handbook.pdf
├─ product/
│  ├─ faq.md
│  ├─ pricing.txt
│  └─ features.xlsx
├─ hr/
│  └─ staff.csv
└─ policy.yaml
```

扩展建议：

- `Markdown` 适合 FAQ、制度说明、产品文档、操作手册
- `PDF` 适合正式制度、白皮书、合同附件、导出的文档
- `CSV / TSV` 适合名录、配置表、统计表、产品列表
- `Excel` 适合多工作表台账、运营表、人员信息表、价格表
- `JSON / YAML` 适合结构化配置、知识条目、元数据文件
- 尽量把不同主题放进不同子目录，后续排查来源会更方便
- 文件名尽量有语义，比如 `travel_policy.md`、`employee_handbook.pdf`
- 如果是从别处复制来的长文档，建议先清理无关页眉页脚和空白页
- 对表格文件，尽量保证首行是字段名，这样检索效果更稳定

热重载规则：

- 新增文件后，不需要手动重启服务，下一次提问会自动重建索引
- 修改已有文件后，下一次提问会自动重建索引
- 删除无效文件后，下一次提问会自动重建索引
- Web 页面状态栏会提示本次回答是否触发了自动重建

排查建议：

- 如果新增文件后没有生效，先确认 `.env` 中使用的是 `KNOWLEDGE_PATH=knowledge`
- 确认文件扩展名在支持列表内
- 确认 PDF 不是纯图片扫描件；如果是纯图片 PDF，目前不会自动 OCR
- 旧版 `.xls` 暂未直接支持，建议先另存为 `.xlsx` 或 `.csv`
- 可以访问 `/api/health` 查看当前识别到的知识库文件列表

## 5. 运行

单次提问：

```bash
python langchain_rag.py --question "出差打车能报销多少钱？"
```

运行内置演示：

```bash
python langchain_rag.py --demo
```

进入交互模式：

```bash
python langchain_rag.py
```

## 6. Web 页面

### 全新现代化前端设计

TinyRag 现在采用了全新的现代化前端设计，具有以下特点：

- **现代简约风格**：采用 Inter 字体和蓝色系配色方案
- **响应式设计**：完美适配桌面端、平板和移动端
- **丰富的动画效果**：平滑的过渡动画和微交互
- **沉浸式体验**：深度和层次感设计
- **专业的布局**：清晰的信息架构和视觉层次

### 主页面

启动方式：

```bash
uvicorn web_app:app --reload --host 127.0.0.1 --port 8008
```

启动后打开：

```text
http://127.0.0.1:8008
```

主页面包含以下模块：
- **英雄区域**：系统核心价值展示和聊天入口
- **核心功能**：六大核心功能特性展示
- **工作原理**：RAG 流程可视化展示
- **开始使用**：快速启动指南
- **页脚**：完整的导航和信息

### 独立聊天窗口

点击主页面上的"开始聊天"按钮，会尝试在新标签页中打开聊天窗口。如果浏览器阻止了弹出窗口，会自动在当前页面跳转。也可以直接访问：

```text
http://127.0.0.1:8008/chat
```

### 接口说明

- `GET /`：主页面（产品介绍 + 聊天入口）
- `GET /chat`：独立聊天页面（沉浸式 MacOS 风格）
- `GET /test-markdown`：Markdown 渲染测试页面
- `GET /api/health`：健康检查
- `POST /api/session/reset`：重置指定会话的上下文记忆
- `POST /api/chat`：提交问题并返回回答
- `POST /api/chat/stream`：流式返回回答，页面默认使用这个接口

说明：

- `/api/health` 会返回当前知识库路径、已发现文件数量、文件列表和上次重建时间。
- 页面会在提问时提示本次是否触发了知识库自动重建。
- 页面会保留最近几轮对话上下文，用于解析"他 / 它 / 这个 / 上述对象"等指代。
- 页面支持开启调试信息，查看问题重写、命中来源和检索证据。
- 页面支持手动开始新会话，清空当前多轮上下文。
- 主页面和独立聊天窗口使用独立的会话存储，互不干扰。
- 系统支持上下文压缩，当会话达到 4 轮以上时会自动启用，目标压缩率 ≥ 40%。

请求示例：

```json
{
  "question": "GL-FATA的rank是多少？",
  "session_id": "demo-session",
  "debug": true
}
```

重置会话示例：

```json
{
  "session_id": "demo-session"
}
```

## 7. Markdown 渲染

现在系统支持完整的 Markdown 渲染，包括：

- 标题（H1-H6）
- 无序列表和有序列表（含嵌套）
- 行内代码和代码块（带语法高亮）
- 引用块
- 链接和图片
- 表格（支持对齐）
- 粗体、斜体、粗斜体、删除线

语法高亮支持：
- JavaScript
- Python
- CSS
- HTML
- Bash
- JSON
- YAML

安全防护：
- 使用 DOMPurify 防止 XSS 攻击
- 所有 HTML 输出都经过安全净化处理

## 8. 证据相关性优化

为了解决不相关证据被返回的问题，系统实现了严格的多层过滤机制：

### 1. 分数阈值过滤
- **文本文档最低分数阈值**：18 分（从 12 分提高）
- **结构化文档最低分数阈值**：35 分（从 20 分大幅提高）

### 2. 关键词匹配验证
- 文档内容必须包含至少一个搜索关键词
- 对于结构化文档，必须同时有实体匹配和字段匹配
- 新增 `_count_keyword_matches()` 函数精确统计匹配次数

### 3. 文档类型区分策略
- **文本文档**（txt/md/markdown/pdf）：相对宽松的过滤策略
- **结构化文档**（csv/tsv/json/yaml/xlsx等）：非常严格的过滤，必须同时满足：
  - 分数 ≥ 35 分
  - 实体关键词匹配
  - 字段关键词匹配

### 4. 直接答案验证（大幅增强）
- 结构化数据直接回答前，必须验证：
  - 问题中提取到搜索关键词
  - 记录内容包含实体关键词匹配
  - 字段名称包含问题关键词匹配
- 缺少任一条件都不会返回直接答案，改为让 LLM 生成

### 5. 关键词提取优化
- 新增通用术语过滤（GENERIC_TERMS）
- 避免把 "rank"、"score"、"什么"、"多少" 等通用词作为关键词
- 提高关键词匹配的准确性

### 6. 优雅降级
- 如果严格过滤后没有结果，优先尝试保留相关的文本文档
- 最后才保留最高分数的单个文档，确保系统不会崩溃
- 但直接答案功能在无匹配时会被禁用

## 9. 上下文压缩功能

系统支持智能的上下文压缩，在保持语义连贯的前提下减少 token 消耗。

### 核心特性

- **基于语义理解的关键信息提取**：自动提取消息中的关键词和实体
- **上下文重要性评估**：多维度评分（时效性、角色、内容质量、上下文关键性）
- **动态压缩策略**：自动适应不同对话场景
- **消息摘要功能**：对长文本进行智能摘要
- **语义相似度估计**：基于关键词重叠度评估压缩质量

### 性能指标

| 指标 | 目标值 |
|------|---------|
| 压缩率 | ≥ 40% |
| 语义相似度 | ≥ 0.85 |
| 平均压缩耗时 | < 50ms |
| 触发阈值 | ≥ 4 轮对话 |

### 配置选项

```env
# 在 runtime.py 中可配置
ENABLE_CONTEXT_COMPRESSION=true
TARGET_COMPRESSION_RATIO=0.5
MIN_MESSAGES_TO_COMPRESS=4
MAX_MESSAGES_AFTER_COMPRESSION=12
```

### 详细文档

- `CONTEXT_COMPRESSION_DESIGN.md`：完整的设计文档
- `CONTEXT_COMPRESSION_EVALUATION.md`：性能评估报告
- `tests/test_context_compressor.py`：单元测试套件

### 健康检查

`/api/health` 接口会返回：
- `context_compression_enabled`：压缩功能是否启用
- `last_compression_result`：最近一次压缩结果（压缩率、语义相似度等）

## 10. 可调参数

`.env` 里最常改的是这些：

```env
KNOWLEDGE_PATH=knowledge
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=auto
CHUNK_SIZE=150
CHUNK_OVERLAP=30
RETRIEVER_K=2
TEMPERATURE=0.1
```

补充说明：

- `EMBEDDING_DEVICE=auto` 时，代码会优先尝试 `cuda`，否则自动退回 `cpu`。
- `CHUNK_SIZE` 和 `RETRIEVER_K` 越大，召回上下文越多，但响应也会更慢。
- 如果你后面想把 FAISS 换成云向量库，只需要替换 `src/tinyrag/rag.py` 里的向量库构建部分。
- `KNOWLEDGE_PATH` 可以是单个文件，也可以是目录；推荐直接指向 `knowledge/`。

## 11. 问题排查指南

### 响应不准确？
1. 检查知识库中是否真的包含相关信息
2. 开启页面的"显示调试信息"，查看：
   - 重写后的问题是否正确
   - 检索到的证据是否相关
   - 证据分数是否足够高
3. 如果证据不相关但分数高，可能是：
   - 文档切分不够合理（调整 CHUNK_SIZE）
   - 嵌入模型对某些专业领域理解不够
   - 尝试更明确的提问方式

### 找不到答案？
1. 确认文件已放入正确的 `knowledge/` 目录
2. 检查文件扩展名是否在支持列表内
3. 访问 `/api/health` 确认文件被识别
4. 试着用更简单的关键词提问
5. 如果是 PDF，确认不是纯图片扫描件

### 证据还是不相关？
1. 最新版本已大幅提高过滤阈值（文本文档 18 分，结构化文档 35 分）
2. 结构化文档现在要求同时有实体匹配和字段匹配
3. 直接答案功能会在无匹配时自动禁用
4. 如果还不够，可以进一步提高 `_filter_low_score_threshold()` 的返回值

### 上下文太长？
1. 系统会在 4 轮对话后自动启用上下文压缩
2. 压缩目标是减少 40% 以上 token，同时保持 85% 以上语义相似度
3. 可以通过"新会话"按钮清空当前上下文

### 前端界面问题？
1. 确保浏览器支持现代 CSS 特性（backdrop-filter、grid 等）
2. 清除浏览器缓存，刷新页面
3. 检查浏览器控制台是否有 JavaScript 错误
4. 确认网络连接正常

## 12. 这个版本做了什么

- 用 LangChain LCEL 串起了加载、切分、检索、提示词、生成五段流程。
- 保留了适合 4GB 显存的本地默认组合。
- 额外加了可切换的 DeepSeek API 后端，方便后续换模型。
- 入口脚本支持单问、演示、交互三种模式。
- 额外补了一个可直接运行的 Web 聊天界面，页面风格按 `DESIGN.md` 约束实现。
- Web 端已接入流式输出，问题提交后会逐步渲染回答内容。
- 知识库现在支持 `txt / md / markdown / pdf / csv / tsv / json / yaml / xlsx` 等多格式混合加载。
- 知识库现在支持热重载，文件新增、修改、删除后会在下一次提问时自动重建索引。
- 系统现在支持多轮会话上下文、问题重写、实体记忆和代词解析。
- 系统现在支持混合检索、表格字段感知，以及高置信度结构化字段直答。
- 页面现在会展示参考证据，并可选显示调试信息，方便排查检索与理解问题。
- **新增**：独立的聊天窗口页面，支持在新窗口中打开，采用沉浸式 MacOS 风格设计。
- **新增**：完整的 Markdown 渲染支持，包括代码语法高亮。
- **新增**：超严格的多层证据相关性过滤机制，大幅减少不相关证据的出现。
- **新增**：证据分数显示，方便调试检索效果。
- **新增**：智能上下文压缩功能，支持长对话历史优化，压缩率 ≥ 40%，语义相似度 ≥ 0.85。
- **新增**：直接答案验证机制，结构化数据回答前必须通过实体和字段双重匹配验证。
- **新增**：通用术语过滤，避免把 "rank"、"score"、"什么"、"多少" 等作为关键词。
- **新增**：全新现代化前端设计，采用 Inter 字体和蓝色系配色方案。
- **新增**：响应式设计，完美适配桌面端、平板和移动端。
- **新增**：丰富的动画效果和平滑过渡，提升用户体验。
- **新增**：专业的布局和视觉层次，提高信息传达效果。
- **新增**：移动端响应式菜单，优化小屏幕体验。
- **新增**：元素进入视口动画，增强页面生动性。
- **新增**：悬停效果和微动画，提升交互体验。
