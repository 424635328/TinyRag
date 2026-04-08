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

页面设计参考了仓库里的 `DESIGN.md`，实现为一个 Apple 风格的聊天界面。

### 主页面

启动方式：

```bash
uvicorn web_app:app --reload
```

启动后打开：

```text
http://127.0.0.1:8000
```

### 独立聊天窗口

点击主页面上的"在新窗口中聊天"按钮，会打开一个独立的聊天窗口（1200x800），也可以直接访问：

```text
http://127.0.0.1:8000/chat
```

### 接口说明

- `GET /`：主页面（产品介绍 + 聊天入口）
- `GET /chat`：独立聊天页面
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

为了解决不相关证据被返回的问题，系统现在实现了多层过滤机制：

### 1. 分数阈值过滤
- 文本文档最低分数阈值：12 分
- 结构化文档（Excel/CSV等）最低分数阈值：20 分

### 2. 关键词匹配验证
- 文档内容必须包含至少一个搜索关键词
- 对于结构化文档，还会检查结构化字段值

### 3. 文档类型区分策略
- **文本文档**（txt/md/markdown/pdf）：相对宽松的过滤策略
- **结构化文档**（csv/tsv/json/yaml/xlsx等）：更严格的过滤，必须有明确的关键词匹配

### 4. 优雅降级
- 如果严格过滤后没有结果，优先尝试保留相关的文本文档
- 最后才保留最高分数的单个文档，确保系统不会崩溃

## 9. 可调参数

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

## 10. 这个版本做了什么

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
- **新增**：独立的聊天窗口页面，支持在新窗口中打开。
- **新增**：完整的 Markdown 渲染支持，包括代码语法高亮。
- **新增**：多层证据相关性过滤机制，大幅减少不相关证据的出现。
- **新增**：证据分数显示，方便调试检索效果。
