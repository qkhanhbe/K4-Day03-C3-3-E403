document.addEventListener("DOMContentLoaded", () => {
  // --- State Variables ---
  let currentMode = "react"; // "react", "baseline", "compare"
  let currentProvider = "gemini";
  let currentModel = "gemini-2.0-flash";
  let testCases = [];
  let lastTraceData = null;

  // --- DOM Elements ---
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");
  const welcomeCard = document.getElementById("welcomeCard");
  const testCasesList = document.getElementById("testCasesList");
  const testCaseCount = document.getElementById("testCaseCount");
  const providerBadge = document.getElementById("providerBadge");
  const activeModelPill = document.getElementById("activeModelPill");

  // Mode Buttons
  const modeReact = document.getElementById("modeReact");
  const modeBaseline = document.getElementById("modeBaseline");
  const modeCompare = document.getElementById("modeCompare");

  // Tab Buttons & Panels
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  // Modals
  const configModal = document.getElementById("configModal");
  const openConfigModalBtn = document.getElementById("openConfigModalBtn");
  const closeConfigModalBtn = document.getElementById("closeConfigModalBtn");
  const saveConfigBtn = document.getElementById("saveConfigBtn");
  const providerSelect = document.getElementById("providerSelect");
  const modelInput = document.getElementById("modelInput");

  // Other controls
  const clearMessagesBtn = document.getElementById("clearMessagesBtn");
  const newChatBtn = document.getElementById("newChatBtn");
  const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
  const sidebar = document.getElementById("sidebar");
  const inspectLastTraceBtn = document.getElementById("inspectLastTraceBtn");
  const traceJsonContainer = document.getElementById("traceJsonContainer");
  const traceJsonText = document.getElementById("traceJsonText");

  // --- Initialize App ---
  init();

  async function init() {
    await fetchStatus();
    await fetchTestCases();
    setupEventListeners();
  }

  // --- Fetch API Status ---
  async function fetchStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        currentProvider = data.provider || "gemini";
        currentModel = data.model || "gemini-2.0-flash";
        
        providerBadge.textContent = `Provider: ${currentProvider.toUpperCase()}`;
        activeModelPill.textContent = currentModel;
        providerSelect.value = currentProvider;
        modelInput.value = currentModel;
      }
    } catch (e) {
      console.warn("Could not fetch API status:", e);
    }
  }

  // --- Fetch Test Cases ---
  async function fetchTestCases() {
    try {
      const res = await fetch("/api/test-cases");
      if (res.ok) {
        testCases = await res.json();
        testCaseCount.textContent = testCases.length;
        renderTestCases();
      }
    } catch (e) {
      testCasesList.innerHTML = `<div class="text-xs text-red-400 p-2">Không thể tải test cases.</div>`;
    }
  }

  // --- Render Test Cases in Sidebar ---
  function renderTestCases() {
    if (!testCases || testCases.length === 0) {
      testCasesList.innerHTML = `<div class="text-xs text-slate-500 p-2 italic">Không có test cases nào.</div>`;
      return;
    }

    testCasesList.innerHTML = testCases.map((tc, index) => {
      const isRedFlag = tc.expected_alter_ego === "RED_FLAG" || tc.question.includes("tự tử") || tc.question.includes("chết");
      return `
        <button 
          data-index="${index}"
          class="test-case-item w-full text-left p-2 rounded-lg hover:bg-white/5 border border-transparent hover:border-white/10 transition group text-xs flex items-start justify-between gap-2"
        >
          <div class="space-y-0.5 overflow-hidden">
            <div class="font-bold ${isRedFlag ? 'text-red-400' : 'text-slate-200'} group-hover:text-emerald-400 truncate">
              ${isRedFlag ? '🚨 Red Flag' : `TC ${index + 1}: ${tc.category || 'Test Case'}`}
            </div>
            <div class="text-[11px] text-slate-400 truncate">${tc.question}</div>
          </div>
          <span class="text-[9px] font-mono px-1.5 py-0.5 rounded ${isRedFlag ? 'bg-red-500/20 text-red-300' : 'bg-slate-800 text-slate-400'}">
            ${tc.expected_alter_ego || 'TC'}
          </span>
        </button>
      `;
    }).join("");

    // Attach click listeners
    document.querySelectorAll(".test-case-item").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.getAttribute("data-index"));
        if (testCases[idx]) {
          userInput.value = testCases[idx].question;
          adjustTextareaHeight();
          switchTab("chat");
          submitForm();
        }
      });
    });
  }

  // --- Setup Event Listeners ---
  function setupEventListeners() {
    // Mode switcher
    modeReact.addEventListener("click", () => setMode("react"));
    modeBaseline.addEventListener("click", () => setMode("baseline"));
    modeCompare.addEventListener("click", () => setMode("compare"));

    // Tabs navigation
    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");
        switchTab(targetTab);
      });
    });

    // Auto resize textarea
    userInput.addEventListener("input", adjustTextareaHeight);

    // Keyboard submit (Enter to send, Shift+Enter for new line)
    userInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitForm();
      }
    });

    // Form submit
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      submitForm();
    });

    // Sample chips click
    document.querySelectorAll(".sample-prompt-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const text = btn.querySelector(".text-slate-400").textContent.replace(/^"|"$/g, "");
        userInput.value = text;
        adjustTextareaHeight();
        submitForm();
      });
    });

    // Clear chat
    clearMessagesBtn.addEventListener("click", clearChat);
    newChatBtn.addEventListener("click", clearChat);

    // Toggle sidebar
    toggleSidebarBtn.addEventListener("click", () => {
      sidebar.classList.toggle("-ml-72");
    });

    // Modal
    openConfigModalBtn.addEventListener("click", () => configModal.classList.remove("hidden"));
    closeConfigModalBtn.addEventListener("click", () => configModal.classList.add("hidden"));
    saveConfigBtn.addEventListener("click", () => {
      currentProvider = providerSelect.value;
      currentModel = modelInput.value.trim() || "gemini-2.0-flash";
      providerBadge.textContent = `Provider: ${currentProvider.toUpperCase()}`;
      activeModelPill.textContent = currentModel;
      configModal.classList.add("hidden");
    });

    // Inspect trace
    if (inspectLastTraceBtn) {
      inspectLastTraceBtn.addEventListener("click", () => {
        if (lastTraceData) {
          traceJsonContainer.classList.remove("hidden");
          traceJsonText.textContent = JSON.stringify(lastTraceData, null, 2);
        } else {
          alert("Chưa có dữ liệu Trace Log lượt chạy nào. Hãy gửi tin nhắn trước!");
        }
      });
    }
  }

  // --- Set Active Mode ---
  function setMode(mode) {
    currentMode = mode;
    [modeReact, modeBaseline, modeCompare].forEach(btn => btn.classList.remove("active"));
    if (mode === "react") modeReact.classList.add("active");
    if (mode === "baseline") modeBaseline.classList.add("active");
    if (mode === "compare") modeCompare.classList.add("active");
  }

  // --- Switch Active Tab ---
  function switchTab(tabId) {
    tabBtns.forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
    });
    tabContents.forEach(content => {
      content.classList.toggle("active", content.id === `tab-${tabId}`);
      content.classList.toggle("hidden", content.id !== `tab-${tabId}`);
    });
  }

  // --- Adjust Textarea Height ---
  function adjustTextareaHeight() {
    userInput.style.height = "auto";
    userInput.style.height = `${Math.min(userInput.scrollHeight, 128)}px`;
  }

  // --- Clear Chat ---
  function clearChat() {
    const messages = chatMessages.querySelectorAll(".message-row");
    messages.forEach(m => m.remove());
    if (welcomeCard) welcomeCard.classList.remove("hidden");
  }

  // --- Submit Form & Execute Chat ---
  async function submitForm() {
    const query = userInput.value.trim();
    if (!query) return;

    // Hide welcome card
    if (welcomeCard) welcomeCard.classList.add("hidden");

    // Clear input
    userInput.value = "";
    adjustTextareaHeight();

    // Render User Message
    renderUserMessage(query);

    // Disable send button & show loading state
    sendBtn.disabled = true;
    const loadingId = renderLoadingState();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          mode: currentMode,
          provider: currentProvider,
          model: currentModel
        })
      });

      // Remove loading indicator
      document.getElementById(loadingId)?.remove();

      if (res.ok) {
        const data = await res.json();
        lastTraceData = data;
        renderAssistantResponse(data);
      } else {
        renderErrorMessage("Không thể kết nối tới server. Vui lòng kiểm tra lại dịch vụ.");
      }
    } catch (e) {
      document.getElementById(loadingId)?.remove();
      renderErrorMessage(`Lỗi thực thi: ${e.message}`);
    } finally {
      sendBtn.disabled = false;
      scrollToBottom();
    }
  }

  // --- Render User Message ---
  function renderUserMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message-row flex justify-end animate-fade-in";
    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 max-w-xl">
        <div class="bg-emerald-600/90 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm shadow-md font-medium leading-relaxed">
          ${escapeHtml(text)}
        </div>
        <div class="w-8 h-8 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center text-slate-300 text-xs font-bold shrink-0">
          <i class="fa-solid fa-user"></i>
        </div>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
  }

  // --- Render Loading State ---
  function renderLoadingState() {
    const id = `loading-${Date.now()}`;
    const msgDiv = document.createElement("div");
    msgDiv.id = id;
    msgDiv.className = "message-row flex justify-start animate-fade-in";
    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 max-w-xl">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 text-xs font-bold shrink-0">
          <i class="fa-solid fa-brain animate-pulse"></i>
        </div>
        <div class="bg-surface-950 border border-white/10 text-slate-300 rounded-2xl rounded-tl-none px-4 py-3 text-xs shadow-md flex items-center gap-3">
          <div class="flex space-x-1">
            <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
            <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
            <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
          </div>
          <span>Đang thực thi suy luận ReAct Loop...</span>
        </div>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
    return id;
  }

  // --- Render Assistant Response ---
  function renderAssistantResponse(data) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message-row animate-fade-in space-y-4";

    if (currentMode === "compare" && data.baseline && data.react) {
      // Side-by-Side Layout
      msgDiv.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- Baseline Column -->
          <div class="bg-surface-950 border border-blue-500/30 rounded-2xl p-4 shadow-xl space-y-3">
            <div class="flex items-center justify-between border-b border-white/10 pb-2">
              <span class="font-bold text-blue-400 text-xs flex items-center gap-1.5">
                <i class="fa-solid fa-robot"></i> 🤖 Baseline Chatbot (Cấp 2)
              </span>
              <span class="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded font-mono">Không Tool</span>
            </div>
            <div class="text-xs text-slate-300 leading-relaxed space-y-2">
              ${formatMarkdown(data.baseline.text)}
            </div>
          </div>

          <!-- ReAct Column -->
          <div class="bg-surface-950 border border-emerald-500/30 rounded-2xl p-4 shadow-xl space-y-3">
            <div class="flex items-center justify-between border-b border-white/10 pb-2">
              <span class="font-bold text-emerald-400 text-xs flex items-center gap-1.5">
                <i class="fa-solid fa-wand-magic-sparkles"></i> 🧠 ReAct Agent (Cấp 3)
              </span>
              <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded font-mono">Thought -> Action</span>
            </div>
            ${renderReActSteps(data.react.steps)}
            <div class="text-xs text-slate-200 leading-relaxed border-t border-white/10 pt-3">
              ${formatMarkdown(data.react.final_answer)}
            </div>
          </div>
        </div>
      `;
    } else if (currentMode === "baseline" && data.baseline) {
      // Baseline Only
      msgDiv.innerHTML = `
        <div class="flex items-start gap-3 max-w-2xl">
          <div class="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div class="bg-surface-950 border border-blue-500/20 text-slate-200 rounded-2xl rounded-tl-none p-5 text-xs shadow-xl leading-relaxed space-y-3">
            <div class="font-bold text-blue-400 mb-1">🤖 Chatbot Baseline (Cấp 2):</div>
            ${formatMarkdown(data.baseline.text)}
          </div>
        </div>
      `;
    } else if (data.react) {
      // ReAct Agent Only
      const isRedFlag = data.react.guardrail_triggered === "RED_FLAG";
      msgDiv.innerHTML = `
        <div class="flex items-start gap-3 max-w-2xl">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 text-xs font-bold shrink-0">
            <i class="fa-solid fa-brain"></i>
          </div>
          <div class="bg-surface-950 border ${isRedFlag ? 'border-red-500/50' : 'border-emerald-500/30'} text-slate-200 rounded-2xl rounded-tl-none p-5 text-xs shadow-xl space-y-4 w-full">
            <div class="flex items-center justify-between border-b border-white/10 pb-2">
              <span class="font-bold text-emerald-400 text-xs flex items-center gap-1.5">
                <i class="fa-solid fa-wand-magic-sparkles"></i> 🧠 ReAct Execution Chain
              </span>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded ${isRedFlag ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-300'}">
                ${isRedFlag ? '🚨 RED_FLAG ALERT' : `${data.react.iterations} Iteration(s)`}
              </span>
            </div>

            <!-- Steps Accordion -->
            ${renderReActSteps(data.react.steps)}

            <!-- Final Answer Card -->
            <div class="pt-2 border-t border-white/10 leading-relaxed text-slate-200">
              ${formatMarkdown(data.react.final_answer)}
            </div>
          </div>
        </div>
      `;
    }

    chatMessages.appendChild(msgDiv);
    scrollToBottom();
  }

  // --- Render Steps Accordion ---
  function renderReActSteps(steps) {
    if (!steps || steps.length === 0) return "";

    return `
      <div class="space-y-2 my-2">
        ${steps.map(step => `
          <div class="step-card bg-surface-900 border border-white/10 rounded-xl p-3 space-y-2 text-xs">
            <div class="flex items-center justify-between font-mono font-semibold text-slate-300">
              <span class="flex items-center gap-1.5 text-emerald-400">
                <i class="fa-solid fa-circle-nodes text-[10px]"></i> Step ${step.step_number}
              </span>
              <span class="bg-white/5 border border-white/10 text-cyan-300 px-2 py-0.5 rounded text-[10px]">
                Tool: ${step.action}
              </span>
            </div>
            
            <div class="text-slate-300 font-medium">
              <strong class="text-amber-400 font-mono">🧠 Thought:</strong> ${escapeHtml(step.thought)}
            </div>

            ${step.action !== "none" ? `
              <div class="bg-black/40 rounded-lg p-2 font-mono text-[11px] space-y-1">
                <div class="text-purple-300">🛠️ Action Input: <span class="text-slate-400">${JSON.stringify(step.action_input)}</span></div>
                <div class="text-emerald-300">👁️ Observation:</div>
                <pre class="text-slate-300 overflow-x-auto text-[10px] bg-black/50 p-1.5 rounded">${JSON.stringify(step.observation, null, 2)}</pre>
              </div>
            ` : ""}
          </div>
        `).join("")}
      </div>
    `;
  }

  // --- Render Error Message ---
  function renderErrorMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message-row flex justify-start animate-fade-in";
    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 max-w-xl">
        <div class="w-8 h-8 rounded-xl bg-red-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </div>
        <div class="bg-surface-950 border border-red-500/40 text-red-300 rounded-2xl rounded-tl-none p-4 text-xs shadow-md">
          ${escapeHtml(text)}
        </div>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
  }

  // --- Scroll Chat to Bottom ---
  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // --- Helpers ---
  function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    return text
      .replace(/### (.*?)\n/g, '<h3 class="text-sm font-bold text-white mt-3 mb-1">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-emerald-300">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')
      .replace(/`([^`]+)`/g, '<code class="bg-white/10 px-1.5 py-0.5 rounded font-mono text-[11px] text-cyan-300">$1</code>')
      .replace(/\n/g, '<br>');
  }
});
