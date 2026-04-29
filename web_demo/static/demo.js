(function () {
  const suggestionBox = document.querySelector(".suggestions");
const hasHistory = localStorage.getItem("chat_history_ntu");

if (suggestionBox && hasHistory) {
  suggestionBox.remove();
}
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const suggestionBtns = Array.from(
    document.querySelectorAll(".suggestion-btn")
  );

  const chatToggle = document.getElementById("chat-toggle");
  const chatCard = document.getElementById("chat-card");
  const chatClose = document.getElementById("chat-close");

  // ===== TOGGLE CHAT =====
  chatToggle.addEventListener("click", () => {
    chatCard.style.display = "flex";
    chatToggle.style.display = "none";
    input.focus();
    requestAnimationFrame(() => {
      log.scrollTop = log.scrollHeight;
    });
  });

  chatClose.addEventListener("click", () => {
    chatCard.style.display = "none";
    chatToggle.style.display = "block";
  });

  // ===== APPEND MESSAGE =====
  function escapeHtml(raw) {
    return String(raw || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderMarkdown(text) {
    const src = String(text || "");
    if (window.marked && typeof window.marked.parse === "function") {
      return window.marked.parse(src, { breaks: true, gfm: true });
    }
    return escapeHtml(src).replace(/\n/g, "<br>");
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function typewriterRender(targetEl, fullText, speedMs) {
    const src = String(fullText || "");
    const step = Math.max(1, Number(speedMs) || 16);
    targetEl.innerHTML = "";

    let buffer = "";
    for (const ch of src) {
      buffer += ch;
      // Render lightweight while typing; apply markdown once complete.
      targetEl.innerHTML = escapeHtml(buffer).replace(/\n/g, "<br>");
      log.scrollTop = log.scrollHeight;
      await sleep(step);
    }

    targetEl.innerHTML = renderMarkdown(src);
  }

  async function appendMessage(role, text, meta) {
    const options = meta || {};
    const div = document.createElement("div");
    div.className = "msg " + role;
    const msgMeta = document.createElement("div");
    msgMeta.className = "msg-meta";
    msgMeta.textContent = role === "user" ? "Bạn" : role === "bot" ? "NTU Bot" : "Hệ thống";
    div.appendChild(msgMeta);

    if (role === "bot" || role === "system") {
      const body = document.createElement("div");
      body.className = "msg-body";
      div.appendChild(body);
      log.appendChild(div);

      const shouldType =
        role === "bot" &&
        !options.instant &&
        options.typewriter !== false;

      if (shouldType) {
        await typewriterRender(body, text, options.typeSpeedMs || 14);
      } else {
        body.innerHTML = renderMarkdown(text);
      }

      if (role !== "bot") {
        requestAnimationFrame(() => {
          log.scrollTop = log.scrollHeight;
        });
        return;
      }
      const actions = document.createElement("div");
      actions.className = "msg-actions";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "msg-action-btn";
      btn.title = "Dịch sang tiếng Anh";
      btn.setAttribute("aria-label", "Dịch sang tiếng Anh");
      btn.textContent = "🌐";

      const viText = String(text || "");
      let showingEn = false;
      let textEn = "";

      btn.addEventListener("click", async () => {
        if (!viText.trim()) return;
        if (!textEn) {
          btn.disabled = true;
          btn.textContent = "…";
          try {
            const res = await fetch("/api/translate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: viText, source: "vi", target: "en" }),
            });
            const data = await res.json();
            textEn = data && data.ok ? String(data.translated_text || "") : "";
            if (!textEn) {
              btn.textContent = "⚠";
              return;
            }
          } catch (e) {
            btn.textContent = "⚠";
            return;
          } finally {
            btn.disabled = false;
          }
        }

        showingEn = !showingEn;
        body.innerHTML = renderMarkdown(showingEn ? textEn : viText);
        btn.textContent = showingEn ? "VI" : "🌐";
        requestAnimationFrame(() => {
          log.scrollTop = log.scrollHeight;
        });
      });

      actions.appendChild(btn);
      div.appendChild(actions);
    } else {
      const body = document.createElement("div");
      body.className = "msg-body";
      body.textContent = text;
      div.appendChild(body);
      log.appendChild(div);
    }
    requestAnimationFrame(() => {
      log.scrollTop = log.scrollHeight;
    });
  }

  // ===== MOVE SUGGESTIONS =====
  function moveSuggestionsToChat() {
    const suggestions = document.querySelector(".suggestions");
    if (!suggestions) return;

    const clone = suggestions.cloneNode(true);
    clone.classList.remove("suggestions");
    clone.classList.add("quick-replies");

    const wrapper = document.createElement("div");
    wrapper.className = "msg bot";

    wrapper.appendChild(clone);
    log.appendChild(wrapper);
    requestAnimationFrame(() => {
      log.scrollTop = log.scrollHeight;
    });

    suggestions.style.display = "none";

    const newBtns = wrapper.querySelectorAll("button");
    newBtns.forEach((btn) => {
      btn.addEventListener("click", function () {
        const message = btn.getAttribute("data-message") || "";
        if (!message.trim()) return;

        wrapper.remove();
        localStorage.setItem("used_suggestion", "true");
        sendMessage(message);
      });
    });
  }

  // ===== TYPING =====
  let typingEl = null;

  function showTyping() {
    typingEl = document.createElement("div");
    typingEl.className = "msg bot typing";

    typingEl.innerHTML = `
      <span class="typing-text">Bạn đợi mình xíu nhé</span>
      <span class="dots">
        <span></span><span></span><span></span>
      </span>
    `;

    log.appendChild(typingEl);
    requestAnimationFrame(() => {
      log.scrollTop = log.scrollHeight;
    });
  }

  function hideTyping() {
    if (typingEl) {
      typingEl.remove();
      typingEl = null;
    }
  }

  // ===== SEND MESSAGE =====
  async function sendMessage(text) {
    const t = text.trim();
    if (!t) return;

    document.querySelectorAll(".quick-replies").forEach(el => el.remove());

    await appendMessage("user", t, { instant: true });
    input.value = "";
    sendBtn.disabled = true;

    showTyping();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ message: t }),
      });

      let data = null;
      try {
        data = await res.json();
      } catch (e) {
        data = { text: "Không đọc được phản hồi từ server.", error: "bad_json" };
      }
      hideTyping();

      if (!res.ok) {
        await appendMessage("system", data.text || "Không gửi được.", { instant: true });
        return;
      }

      if (data.error === "parse_failed") {
        await appendMessage("system", "Lỗi kết nối Rasa.", { instant: true });
        return;
      }

      await appendMessage("bot", data.text || "(Không có phản hồi)", {
        typewriter: true,
        typeSpeedMs: 14,
      });

    } catch (e) {
      await appendMessage(
        "system",
        "Không kết nối được tới server demo. Bạn thử tải lại trang hoặc chạy lại `python web_demo/app.py`.",
        { instant: true }
      );
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    sendMessage(input.value);
  });

  // ===== GỢI Ý GỐC (KHÔNG ĐỤNG) =====
  suggestionBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const message = btn.getAttribute("data-message") || "";
      if (!message.trim()) return;
      sendMessage(message);
    });
  });

  // ===== CHAT HISTORY =====
  (function () {
    const STORAGE_KEY = "chat_history_ntu";

    function saveMessage(role, text) {
      const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      history.push({ role, text });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    }

    function loadHistory() {
      const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");

      const usedSuggestion = localStorage.getItem("used_suggestion");

      if (!history.length) {
        appendMessage(
          "bot",
          "Chào bạn! Mình là chatbot hỗ trợ E-learning NTU. Bạn cần giúp gì?",
          { instant: true, typewriter: false }
        );
      
        if (!usedSuggestion) {
          moveSuggestionsToChat();
        }
      
        return;
      }
      // 👉 LOAD HISTORY
      history.forEach((msg) =>
        appendMessage(msg.role, msg.text, { instant: true, typewriter: false })
      );

      log.scrollTop = log.scrollHeight;
      requestAnimationFrame(() => {
        log.scrollTop = log.scrollHeight;
      });
    }

    // override append
    const oldAppend = appendMessage;

    appendMessage = function (role, text, meta) {
      oldAppend(role, text, meta);
      saveMessage(role, text);
    };

    // 👉 LOAD NGAY (KHÔNG setTimeout)
    loadHistory();
    requestAnimationFrame(() => {
      log.scrollTop = log.scrollHeight;
    });
  })();

})();