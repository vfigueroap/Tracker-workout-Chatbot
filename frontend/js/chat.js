const messagesArea = document.getElementById("messages-area");
const welcomeState = document.getElementById("welcome-state");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const sessionPill = document.getElementById("session-pill");
const sessionTimer = document.getElementById("session-timer");

let activeSessionId = null;
let sessionStartTime = null;
let timerInterval = null;
let isLoading = false;

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  await loadHistory();
  await checkActiveSession();
}

async function loadHistory() {
  try {
    const data = await api.getChatHistory(60);
    const msgs = (data.messages || []).slice().reverse();
    if (msgs.length > 0) {
      hideWelcome();
      msgs.forEach((m) => {
        if (m.message_type === "text") appendMessage(m.role, m.content, false);
      });
      scrollToBottom(false);
    }
  } catch (e) {
    console.warn("Could not load history", e);
  }
}

async function checkActiveSession() {
  try {
    const s = await api.getActiveSession();
    if (s && s.id) {
      activeSessionId = s.id;
      sessionStartTime = new Date(s.started_at);
      startTimer();
    }
  } catch (_) {}
}

// ── Input auto-resize ─────────────────────────────────────────────────────
chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
  sendBtn.disabled = chatInput.value.trim() === "";
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled) chatForm.dispatchEvent(new Event("submit"));
  }
});

// ── Send message ──────────────────────────────────────────────────────────
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text || isLoading) return;

  hideWelcome();
  appendMessage("user", text);
  chatInput.value = "";
  chatInput.style.height = "auto";
  sendBtn.disabled = true;
  scrollToBottom();

  const typingEl = showTyping();
  isLoading = true;

  try {
    const res = await api.sendMessage(text, activeSessionId);
    typingEl.remove();

    if (res.session_id) {
      if (!activeSessionId) {
        activeSessionId = res.session_id;
        sessionStartTime = new Date();
        startTimer();
      }
      activeSessionId = res.session_id;
    } else if (res.session_id === null && activeSessionId) {
      activeSessionId = null;
      stopTimer();
    }

    if (res.tools_used && res.tools_used.length) {
      appendToolCards(res.tools_used, res.reply);
    } else {
      appendMessage("assistant", res.reply);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage("assistant", `❌ Error: ${err.message}`);
  } finally {
    isLoading = false;
    scrollToBottom();
  }
});

// ── Render helpers ─────────────────────────────────────────────────────────
function appendMessage(role, content, animate = true) {
  const isUser = role === "user";
  const wrapper = document.createElement("div");
  wrapper.className = `msg ${isUser ? "msg-user" : "msg-ai"}`;
  if (!animate) wrapper.style.animation = "none";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = isUser ? "U" : "F";

  const body = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = markdownToHtml(content);

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatTime(new Date());

  body.appendChild(bubble);
  body.appendChild(time);
  wrapper.appendChild(avatar);
  wrapper.appendChild(body);
  messagesArea.appendChild(wrapper);
}

function appendToolCards(tools, reply) {
  const wrapper = document.createElement("div");
  wrapper.className = "msg msg-ai";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "F";

  const body = document.createElement("div");
  body.className = "msg-body";

  // Tool cards
  tools.forEach((toolName) => {
    const card = buildToolCard(toolName);
    if (card) body.appendChild(card);
  });

  // Text reply bubble
  if (reply && reply.trim()) {
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerHTML = markdownToHtml(reply);
    body.appendChild(bubble);
  }

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatTime(new Date());
  body.appendChild(time);

  wrapper.appendChild(avatar);
  wrapper.appendChild(body);
  messagesArea.appendChild(wrapper);
}

function buildToolCard(toolName) {
  const icons = {
    log_exercise: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 4v16M18 4v16M3 8h4m10 0h4M3 16h4m10 0h4"/></svg>`,
    start_workout_session: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    end_workout_session: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>`,
    create_or_update_routine: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
    update_user_profile: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    get_exercise_progress: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  };

  const labels = {
    log_exercise: "Ejercicio registrado",
    start_workout_session: "Sesión iniciada",
    end_workout_session: "Sesión completada",
    create_or_update_routine: "Rutina guardada",
    update_user_profile: "Perfil actualizado",
    get_exercise_progress: "Progreso consultado",
  };

  const card = document.createElement("div");
  card.className = "tool-card";

  card.innerHTML = `
    <div class="tool-card-header">
      ${icons[toolName] || ""}
      <span>${labels[toolName] || toolName}</span>
    </div>
    <div class="tool-card-body" id="tc-${Date.now()}-${Math.random().toString(36).slice(2)}">
    </div>
  `;
  return card;
}

function showTyping() {
  const wrapper = document.createElement("div");
  wrapper.className = "msg msg-ai";
  wrapper.id = "typing-msg";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "F";

  const body = document.createElement("div");
  body.className = "msg-body";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = `<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>`;
  body.appendChild(indicator);

  wrapper.appendChild(avatar);
  wrapper.appendChild(body);
  messagesArea.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ── Welcome / session pill ─────────────────────────────────────────────────
function hideWelcome() {
  welcomeState.style.display = "none";
}

function startTimer() {
  sessionPill.style.display = "flex";
  timerInterval = setInterval(updateTimer, 1000);
  updateTimer();
}

function stopTimer() {
  sessionPill.style.display = "none";
  clearInterval(timerInterval);
}

function updateTimer() {
  if (!sessionStartTime) return;
  const elapsed = Math.floor((Date.now() - sessionStartTime.getTime()) / 1000);
  const m = Math.floor(elapsed / 60);
  const s = elapsed % 60;
  sessionTimer.textContent = `${m}:${String(s).padStart(2, "0")}`;
}

// ── Utilities ─────────────────────────────────────────────────────────────
function scrollToBottom(smooth = true) {
  requestAnimationFrame(() => {
    messagesArea.scrollTo({
      top: messagesArea.scrollHeight,
      behavior: smooth ? "smooth" : "instant",
    });
  });
}

function formatTime(date) {
  return date.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
}

function markdownToHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, `<code style="font-family:var(--font-mono);font-size:0.85em;background:var(--bg-elevated);padding:1px 5px;border-radius:4px">$1</code>`)
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>")
    .replace(/^(.+)$/, "<p>$1</p>");
}

function fillPrompt(text) {
  chatInput.value = text;
  chatInput.dispatchEvent(new Event("input"));
  chatInput.focus();
}

// ── Start ─────────────────────────────────────────────────────────────────
init();
