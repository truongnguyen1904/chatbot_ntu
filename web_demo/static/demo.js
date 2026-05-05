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

  function sleep(ms) {
    return new Promise(function (resolve) {
      setTimeout(resolve, ms);
    });
  }

  /** Gõ theo grapheme cluster (emoji/ghép dấu không bị tách đôi). */
  function graphemeSegments(src) {
    const s = String(src || "");
    if (typeof Intl !== "undefined" && typeof Intl.Segmenter === "function") {
      try {
        var seg = new Intl.Segmenter(undefined, { granularity: "grapheme" });
        return Array.from(seg.segment(s), function (x) {
          return x.segment;
        });
      } catch (e) {}
    }
    return Array.from(s);
  }

  /**
   * List chuẩn Markdown: `- ` hoặc `* ` (có khoảng sau marker).
   * Chỉ escape `-` khi viết `-nhấn mạnh` không có khoảng → tránh hiểu nhầm list.
   */
  function shieldNonListMarkers(md) {
    return String(md || "")
      .split("\n")
      .map(function (line) {
        if (/^\s*[-*]\s+\S/.test(line)) return line;
        var hm = /^(\s*)(-)(\S.*)$/.exec(line);
        if (hm) return hm[1] + "\\" + hm[2] + hm[3];
        return line;
      })
      .join("\n");
  }

  /**
   * Chèn dòng trống giữa các block để list / bold / heading không dính nhau (marked thoát list đúng).
   * Ví dụ: sau `- list1` phải tách khỏi `**ss**`; sau `**ss**` tách khỏi list mới.
   */
  function normalizeMarkdownBlocks(md) {
    var lines = String(md || "")
      .replace(/\r\n/g, "\n")
      .split("\n");
    var out = [];

    function isBlank(line) {
      return !String(line || "").trim();
    }

    function isMdListLine(line) {
      return (
        /^\s*[-*+]\s+\S/.test(line) || /^\s*\d+\.\s+\S/.test(line)
      );
    }

    function isBoldWrappedLine(line) {
      var t = String(line || "").trim();
      return t.startsWith("**") && t.endsWith("**") && t.length >= 4;
    }

    function needsSep(prevLine, currLine) {
      if (!prevLine || isBlank(currLine)) return false;
    
      var prevList = isMdListLine(prevLine);
      var currList = isMdListLine(currLine);
    
      var currTrim = String(currLine || "").trim();
    
      var currStartsBold = /^\s*\*\*/.test(currLine);
      var currIsHeading = /^#{1,6}\s+\S/.test(currTrim);
    
      var prevBoldClosed = isBoldWrappedLine(prevLine);
      var prevHeading = /^#{1,6}\s+\S/.test(String(prevLine || "").trim());
    
      // 🔥 RULE 1: List → non-list => luôn tách
      if (prevList && !currList) return true;
    
      // 🔥 RULE 2: Bold/Heading → List => tách
      if ((prevBoldClosed || prevHeading) && currList) return true;
    
      // 🔥 RULE 3: Bold → Bold (tránh dính block)
      if (prevBoldClosed && currStartsBold) return true;
    
      return false;
    }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (i > 0 && needsSep(lines[i - 1], line)) {
        if (out.length === 0 || !isBlank(out[out.length - 1])) out.push("");
      }
      out.push(line);
    }
    return out.join("\n");
  }

  /**
   * Khi đang gõ: chỉ hiển thị plain text — ẩn ** # - list marker * nhấn mạnh (không parse MD).
   */
  function stripMarkdownSyntaxForTyping(raw) {
    var t = String(raw);
    t = t.replace(/\*{1,2}$/g, "");
    t = t.replace(/_{1,2}$/g, "");
    t = t.replace(/\*{2}/g, "");
    t = t.replace(/^#{1,6}\s+/gm, "");
    t = t.replace(/\*([^*\n]+)\*/g, "$1");
    t = t.replace(/^(\s*)[\-\*\+]\s+/gm, "$1• ");
    return t;
  }

  function prepareMarkdownForParse(text) {
    var src = fixEmojiBoldMarkdown(String(text || ""));
    src = shieldNonListMarkers(src);
    src = normalizeMarkdownBlocks(src);
    return src;
  }

  /**
   * Một số phiên bản marked tách ** ngay trước emoji thành <strong> chỉ có emoji → bubble chỉ thấy icon.
   * Đưa cụm emoji ra ngoài: **👋 Chào...** → 👋 **Chào...**
   */
  function fixEmojiLeadingBold(line) {
    const s = String(line || "");
    return s.replace(
      /^\s*\*\*((?:\p{Extended_Pictographic}|\uFE0F|\u200D)+)\s+(.*?)\*\*\s*$/u,
      (_, emj, inner) => `${emj} **${inner}**`
    );
  }

  function fixEmojiBoldMarkdown(src) {
    return String(src || "")
      .split("\n")
      .map((ln) => fixEmojiLeadingBold(ln))
      .join("\n");
  }

  function getMarkedParseFn() {
    const m = window.marked;
    if (!m) return null;
    if (typeof m.parse === "function") return m.parse.bind(m);
    if (typeof m === "function") return m;
    return null;
  }

  function renderMarkdown(text) {
    var src = prepareMarkdownForParse(text);
    const parseFn = getMarkedParseFn();
    if (!parseFn) {
      return (
        '<div class="chat-md">' + escapeHtml(src).replace(/\n/g, "<br>") + "</div>"
      );
    }
    try {
      var opts = { breaks: true, gfm: true };
      var html = parseFn(src, opts);
      if (html && typeof html.then === "function") {
        return (
          '<div class="chat-md">' + escapeHtml(src).replace(/\n/g, "<br>") + "</div>"
        );
      }
      return '<div class="chat-md">' + html + "</div>";
    } catch (e) {
      return (
        '<div class="chat-md">' + escapeHtml(src).replace(/\n/g, "<br>") + "</div>"
      );
    }
  }
  async function typewriterRender(targetEl, fullText, speedMs) {
    var src = String(fullText || "");
    targetEl.innerHTML = "";
    targetEl.classList.add("typing-plain");

    var step = Math.max(4, Number(speedMs) || 8);
    var perTick = 4;
    var buffer = "";
    var parts = graphemeSegments(src);

    for (var i = 0; i < parts.length; i += perTick) {
      buffer += parts.slice(i, i + perTick).join("");
      targetEl.textContent = stripMarkdownSyntaxForTyping(buffer);
      log.scrollTop = log.scrollHeight;
      await sleep(step);
    }

    targetEl.classList.remove("typing-plain");
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
        typeSpeedMs: 12,
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