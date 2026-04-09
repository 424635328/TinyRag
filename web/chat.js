const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const statusText = document.getElementById("status");
const messages = document.getElementById("messages");
const suggestionButtons = document.querySelectorAll(".suggestion");
const submitButton = form.querySelector('button[type="submit"]');
const chatProvider = document.getElementById("chat-provider");
const healthPath = document.getElementById("health-path");
const debugMode = document.getElementById("debug-mode");
const newSessionButton = document.getElementById("new-session");

let isStreaming = false;
let currentSessionId = loadSessionId();

if (typeof marked !== "undefined" && typeof hljs !== "undefined") {
  marked.setOptions({
    highlight: function (code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value;
        } catch (err) {}
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
  });
}

function renderMarkdown(content) {
  if (!content) return "";
  
  try {
    if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
      const html = marked.parse(content);
      return DOMPurify.sanitize(html);
    }
  } catch (err) {
    console.error("Markdown 渲染失败:", err);
  }
  
  return escapeHtml(content).replace(/\n/g, '<br>');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function createSessionId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadSessionId() {
  const existing = window.localStorage.getItem("tinyrag_chat_session_id");
  if (existing) {
    return existing;
  }
  const created = createSessionId();
  window.localStorage.setItem("tinyrag_chat_session_id", created);
  return created;
}

function saveSessionId(sessionId) {
  currentSessionId = sessionId;
  window.localStorage.setItem("tinyrag_chat_session_id", sessionId);
}

function createCopyButton() {
  const button = document.createElement("button");
  button.className = "copy-button";
  button.setAttribute("aria-label", "复制消息内容");
  
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "14");
  svg.setAttribute("height", "14");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "currentColor");
  
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z");
  
  svg.appendChild(path);
  button.appendChild(svg);
  
  const tooltip = document.createElement("div");
  tooltip.className = "copy-tooltip";
  tooltip.textContent = "复制";
  button.appendChild(tooltip);
  
  return button;
}

function getMessageText(contentElement) {
  if (!contentElement) return "";
  
  let text = "";
  
  // 处理不同类型的内容
  const textNodes = contentElement.querySelectorAll('p, li, code, pre, blockquote');
  if (textNodes.length > 0) {
    textNodes.forEach(node => {
      if (node.tagName === 'PRE') {
        // 处理代码块
        const code = node.querySelector('code');
        if (code) {
          text += code.textContent + '\n\n';
        }
      } else {
        text += node.textContent + '\n';
      }
    });
  } else {
    // 处理纯文本内容
    text = contentElement.textContent;
  }
  
  return text.trim();
}

function copyToClipboard(text) {
  if (!navigator.clipboard) {
    // 回退方法
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      return successful;
    } catch (err) {
      document.body.removeChild(textArea);
      return false;
    }
  }
  
  return navigator.clipboard.writeText(text);
}

function setupCopyButton(button, contentElement) {
  button.addEventListener("click", async () => {
    const text = getMessageText(contentElement);
    
    if (!text) {
      const tooltip = button.querySelector('.copy-tooltip');
      if (tooltip) {
        tooltip.textContent = "无内容可复制";
        tooltip.classList.add("show");
        setTimeout(() => {
          tooltip.classList.remove("show");
        }, 2000);
      }
      return;
    }
    
    try {
      const result = await copyToClipboard(text);
      
      if (result === false) {
        throw new Error("复制失败");
      }
      
      // 显示复制成功的状态
      button.classList.add("copied");
      
      const tooltip = button.querySelector('.copy-tooltip');
      if (tooltip) {
        tooltip.textContent = "已复制";
        tooltip.classList.add("show");
      }
      
      // 恢复按钮状态
      setTimeout(() => {
        button.classList.remove("copied");
        const tooltip = button.querySelector('.copy-tooltip');
        if (tooltip) {
          tooltip.classList.remove("show");
          setTimeout(() => {
            tooltip.textContent = "复制";
          }, 300);
        }
      }, 2000);
    } catch (error) {
      console.error("复制失败:", error);
      const tooltip = button.querySelector('.copy-tooltip');
      if (tooltip) {
        tooltip.textContent = "复制失败";
        tooltip.classList.add("show");
        setTimeout(() => {
          tooltip.classList.remove("show");
          setTimeout(() => {
            tooltip.textContent = "复制";
          }, 300);
        }, 2000);
      }
    }
  });
}

function createLoadingIndicator() {
  const loading = document.createElement("div");
  loading.className = "loading-indicator";
  
  const spinner = document.createElement("div");
  spinner.className = "loading-spinner";
  
  const text = document.createElement("span");
  text.className = "loading-text";
  text.textContent = "正在查找索引...";
  
  loading.append(spinner, text);
  return loading;
}

function createMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message message-${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper";

  // 创建消息操作栏
  const actions = document.createElement("div");
  actions.className = "message-actions";
  
  // 创建复制按钮
  const copyButton = createCopyButton();
  actions.appendChild(copyButton);

  const roleText = document.createElement("p");
  roleText.className = "message-role";
  roleText.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("div");
  body.className = "message-content";
  if (content) {
    if (role === "assistant") {
      body.innerHTML = renderMarkdown(content);
    } else {
      body.textContent = content;
    }
  } else if (role === "assistant") {
    // 添加加载指示器
    body.appendChild(createLoadingIndicator());
  }

  const meta = document.createElement("div");
  meta.className = "message-meta";

  // 设置复制按钮功能
  setupCopyButton(copyButton, body);

  wrapper.append(actions, roleText, body, meta);
  article.append(avatar, wrapper);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  
  if (typeof hljs !== "undefined") {
    body.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }
  
  return { article, body, meta };
}

function updateMessageContent(body, content) {
  body.innerHTML = renderMarkdown(content);
  messages.scrollTop = messages.scrollHeight;
  
  if (typeof hljs !== "undefined") {
    body.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }
}

function createInitialAssistantMessage() {
  const article = document.createElement("article");
  article.className = "message message-assistant";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "AI";

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper";

  // 创建消息操作栏
  const actions = document.createElement("div");
  actions.className = "message-actions";
  
  // 创建复制按钮
  const copyButton = createCopyButton();
  actions.appendChild(copyButton);

  const roleText = document.createElement("p");
  roleText.className = "message-role";
  roleText.textContent = "Assistant";

  const body = document.createElement("div");
  body.className = "message-content";
  body.innerHTML = "<p>欢迎使用 TinyRag！我可以帮你回答关于你本地知识库的问题。</p>";

  const meta = document.createElement("div");
  meta.className = "message-meta";

  // 设置复制按钮功能
  setupCopyButton(copyButton, body);

  wrapper.append(actions, roleText, body, meta);
  article.append(avatar, wrapper);
  messages.appendChild(article);
}

function clearMessages() {
  messages.innerHTML = "";
  createInitialAssistantMessage();
}

function setInteractiveState(disabled) {
  isStreaming = disabled;
  input.disabled = disabled;
  submitButton.disabled = disabled;
  debugMode.disabled = disabled;
  newSessionButton.disabled = disabled;
  suggestionButtons.forEach((button) => {
    button.disabled = disabled;
  });
}

function updateHealthBadge(provider, path, fileCount, ok = true) {
  if (chatProvider) {
    chatProvider.textContent = provider || "Unknown";
  }
  if (healthPath) {
    if (ok) {
      healthPath.textContent = `${path || "知识库路径不可用"} · 已发现 ${fileCount || 0} 个文件`;
    } else {
      healthPath.textContent = path || "知识库路径不可用";
    }
  }
}

function parseSseBlock(block) {
  const dataLines = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim());

  if (!dataLines.length) {
    return null;
  }

  return JSON.parse(dataLines.join("\n"));
}

function addNote(meta, text) {
  const note = document.createElement("p");
  note.className = "message-note";
  note.textContent = text;
  meta.appendChild(note);
}

function renderEvidence(meta, evidence) {
  if (!Array.isArray(evidence) || !evidence.length) {
    return;
  }

  const details = document.createElement("details");
  details.className = "message-details";

  const summary = document.createElement("summary");
  summary.textContent = `参考证据 (${evidence.length})`;

  const list = document.createElement("div");
  list.className = "evidence-list";

  evidence.forEach((item) => {
    const block = document.createElement("div");
    block.className = "evidence-item";

    const head = document.createElement("div");
    head.className = "evidence-head";

    const sourceTag = document.createElement("span");
    sourceTag.className = "evidence-tag";
    sourceTag.textContent = item.source || "unknown";
    head.appendChild(sourceTag);

    if (item.sheet_name) {
      const sheetTag = document.createElement("span");
      sheetTag.className = "evidence-tag";
      sheetTag.textContent = `sheet: ${item.sheet_name}`;
      head.appendChild(sheetTag);
    }

    if (item.record_index) {
      const rowTag = document.createElement("span");
      rowTag.className = "evidence-tag";
      rowTag.textContent = `row: ${item.record_index}`;
      head.appendChild(rowTag);
    }

    if (Array.isArray(item.reasons) && item.reasons.length) {
      const reasonTag = document.createElement("span");
      reasonTag.className = "evidence-tag";
      reasonTag.textContent = item.reasons.join(" + ");
      head.appendChild(reasonTag);
    }

    const preview = document.createElement("p");
    preview.className = "evidence-preview";
    preview.textContent = item.preview || "";

    block.append(head, preview);
    list.appendChild(block);
  });

  details.append(summary, list);
  meta.appendChild(details);
}

function renderDebug(meta, debug) {
  if (!debugMode.checked || !debug) {
    return;
  }

  const details = document.createElement("details");
  details.className = "message-details";

  const summary = document.createElement("summary");
  summary.textContent = "调试信息";

  const block = document.createElement("pre");
  block.className = "debug-block";
  block.textContent = JSON.stringify(debug, null, 2);

  details.append(summary, block);
  meta.appendChild(details);
}

function renderAssistantMeta(meta, payload) {
  meta.innerHTML = "";

  if (payload.rewritten_question && payload.rewritten_question !== payload.question) {
    addNote(meta, `重写问题：${payload.rewritten_question}`);
  }

  if (Array.isArray(payload.entities) && payload.entities.length) {
    addNote(meta, `会话实体：${payload.entities.join(" / ")}`);
  }

  if (payload.reloaded) {
    addNote(meta, "本次回答前已自动重建知识库索引。");
  }

  renderEvidence(meta, payload.evidence);
  renderDebug(meta, payload.debug);
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "健康检查失败");
    }
    updateHealthBadge(data.provider, data.knowledge_path, data.knowledge_file_count, true);
  } catch (error) {
    updateHealthBadge("Unavailable", "请检查后端服务", 0, false);
    statusText.textContent = "健康检查失败，请确认后端已启动。";
  }
}

async function readStream(response, assistantMessage) {
  if (!response.body) {
    throw new Error("浏览器不支持流式响应。");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let finalPayload = null;
  let accumulatedContent = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    while (buffer.includes("\n\n")) {
      const boundary = buffer.indexOf("\n\n");
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const payload = parseSseBlock(block);
      if (!payload) {
        continue;
      }

      if (payload.type === "start") {
        statusText.textContent = payload.reloaded
          ? `已连接 ${payload.provider}，检测到知识库变化，正在重建索引并生成回答...`
          : `已连接 ${payload.provider}，开始生成回答...`;
        continue;
      }

      if (payload.type === "token") {
        accumulatedContent += payload.content;
        updateMessageContent(assistantMessage.body, accumulatedContent);
        continue;
      }

      if (payload.type === "end") {
        finalPayload = payload;
        statusText.textContent = payload.reloaded
          ? `完成，本次由 ${payload.provider} 提供流式回答，且已自动重建知识库索引。`
          : `完成，本次由 ${payload.provider} 提供流式回答。`;
        continue;
      }

      if (payload.type === "error") {
        throw new Error(payload.detail || "流式请求失败。");
      }
    }
  }

  if (!accumulatedContent.trim()) {
    updateMessageContent(assistantMessage.body, "抱歉，这次没有收到模型输出。");
  }

  if (finalPayload) {
    renderAssistantMeta(assistantMessage.meta, finalPayload);
  }
}

async function submitQuestion(question) {
  const cleanQuestion = question.trim();
  if (!cleanQuestion || isStreaming) {
    return;
  }

  createMessage("user", cleanQuestion);
  const assistantMessage = createMessage("assistant", "");

  statusText.textContent = "正在检索知识库并建立多轮会话连接...";
  input.value = "";
  setInteractiveState(true);

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: cleanQuestion,
        session_id: currentSessionId,
        debug: debugMode.checked,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "请求失败。");
    }

    await readStream(response, assistantMessage);
  } catch (error) {
    updateMessageContent(
      assistantMessage.body,
      assistantMessage.body.textContent || `当前请求失败：${error.message}`
    );
    statusText.textContent = "请求失败，请检查模型服务或环境变量配置。";
  } finally {
    setInteractiveState(false);
    input.focus();
  }
}

async function startNewSession() {
  const previousSessionId = currentSessionId;
  const nextSessionId = createSessionId();

  try {
    await fetch("/api/session/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: previousSessionId }),
    });
  } catch (error) {
  }

  saveSessionId(nextSessionId);
  clearMessages();
  statusText.textContent = "已开始新会话。";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await submitQuestion(input.value);
});

input.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    await submitQuestion(input.value);
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    input.value = button.dataset.question || "";
    await submitQuestion(input.value);
  });
});

debugMode.addEventListener("change", () => {
  window.localStorage.setItem("tinyrag_chat_debug_mode", debugMode.checked ? "1" : "0");
});

newSessionButton.addEventListener("click", async () => {
  await startNewSession();
});

debugMode.checked = window.localStorage.getItem("tinyrag_chat_debug_mode") === "1";
loadHealth();

const textarea = document.getElementById("question");
if (textarea) {
  textarea.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 160) + "px";
  });
}
