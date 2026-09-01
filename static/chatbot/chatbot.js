/* SportSphere FAQ Chatbot widget (vanilla JS, no dependencies, no AI).
 * Embeds a floating launcher + compact chat popup in the bottom-right corner.
 * Configure the API base URL and WhatsApp details via the global object below
 * BEFORE this script loads, e.g.:
 *   window.SportSphereChatbot = { apiBaseUrl: "/api/v1/chat/", ... };
 */
(function () {
  "use strict";

  var CONFIG = Object.assign(
    {
      apiBaseUrl: "/api/v1/chat/", // trailing slash
      whatsappNumber: "15550214001", // E.164: +1 (555) 021-4001
      whatsappMessage:
        "Hello Sportsphere Academy! I would like to get more information.",
    },
    window.SportSphereChatbot || {}
  );

  var CSS_URL =
    CONFIG.cssUrl ||
    CONFIG.apiBaseUrl.replace(/\/[^/]*\/?$/, "/") + "static/chatbot/chatbot.css";

  var state = { faqs: null, loaded: false };

  function loadCss() {
    if (document.getElementById("ss-chatbot-css")) return;
    var link = document.createElement("link");
    link.id = "ss-chatbot-css";
    link.rel = "stylesheet";
    link.href = CSS_URL;
    document.head.appendChild(link);
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  /* Convert [label](url) markdown-style links in answers to safe anchors. */
  function renderAnswer(text) {
    var safe = escapeHtml(text);
    return safe.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      function (_, label, url) {
        var href = escapeHtml(url);
        if (/^https?:|^mailto:/i.test(url)) {
          return '<a href="' + href + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(label) + "</a>";
        }
        return escapeHtml(label);
      }
    );
  }

  function buildLauncher() {
    var btn = document.createElement("button");
    btn.id = "ss-chatbot-launcher";
    btn.type = "button";
    btn.setAttribute("aria-label", "Open FAQ chatbot");
    btn.innerHTML =
      '<svg class="ss-chat-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.02 2 11c0 2.32 1.02 4.43 2.75 6.02L4 22l4.05-1.45c1.02.32 2.1.48 3.28.48 5.52 0 10-4.02 10-9s-4.48-9-10-9zM8 13c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>' +
      '<svg class="ss-close-icon" viewBox="0 0 24 24"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
    btn.addEventListener("click", toggle);
    document.body.appendChild(btn);
    return btn;
  }

  function buildPopup() {
    var popup = document.createElement("div");
    popup.id = "ss-chatbot-popup";
    popup.setAttribute("role", "dialog");
    popup.innerHTML =
      '<div id="ss-chatbot-header">' +
      '  <div class="ss-logo">⚽</div>' +
      '  <div><div class="ss-title">SportSphere Academy</div>' +
      '  <div class="ss-subtitle">FAQ Assistant</div></div>' +
      '  <button id="ss-chatbot-close" type="button" aria-label="Close chat">&times;</button>' +
      "</div>" +
      '<div id="ss-chatbot-body"></div>' +
      '<div id="ss-chatbot-footer">' +
      '  <a class="ss-btn ss-primary ss-wa-btn" target="_blank" rel="noopener noreferrer">' +
      '    <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-8.6 15l-1.4 5 5.1-1.3A10 10 0 1 0 12 2zm5.6 14.2c-.24.67-1.4 1.28-1.95 1.32-.53.05-1.02.29-2.8-.55-2.13-1.03-3.48-3.68-3.58-3.85-.11-.17-.86-1.14-.86-2.18s.53-1.55.72-1.76c.19-.21.41-.26.55-.26l.4.01c.12.01.3-.05.46.35.17.42.58 1.45.63 1.55.05.1.08.22.02.35-.06.13-.1.21-.2.33l-.3.35c-.18.18-.37.36-.16.72.2.35.9 1.47 1.94 2.4 1.33 1.18 1.93 1.4 2.25 1.5.3.11.5.1.68-.05.2-.15.85-1.02 1.1-1.38.24-.35.48-.29.6-.21.34.14.1.21.1.21.9.53 1.02.72 1.2.93.1.15.15.38.05.57z"/></svg>' +
      '    <span>Chat on WhatsApp</span>' +
      "  </a>" +
      "</div>";
    popup.querySelector("#ss-chatbot-close").addEventListener("click", close);
    var waBtn = popup.querySelector(".ss-wa-btn");
    waBtn.href = whatsappUrl();
    document.body.appendChild(popup);
    return popup;
  }
function whatsappUrl() {
    return (
      "https://wa.me/" +
      encodeURIComponent(CONFIG.whatsappNumber) +
      "?text=" +
      encodeURIComponent(CONFIG.whatsappMessage)
    );
  }

  var launcher, popup, body;

  function toggle() {
    if (popup.classList.contains("ss-open")) return close();
    open();
  }

  function open() {
    launcher.classList.add("ss-open");
    popup.classList.add("ss-open");
    if (!state.loaded) {
      loadFaqs();
    } else {
      renderQuestions();
    }
  }

  function close() {
    launcher.classList.remove("ss-open");
    popup.classList.remove("ss-open");
  }

  function addBot(text, asHtml) {
    var m = document.createElement("div");
    m.className = "ss-msg ss-bot";
    m.innerHTML = asHtml ? text : escapeHtml(text);
    body.appendChild(m);
    return m;
  }

  function addUser(text) {
    var m = document.createElement("div");
    m.className = "ss-msg ss-user";
    m.textContent = text;
    body.appendChild(m);
    return m;
  }

  function scrollBottom() {
    body.scrollTop = body.scrollHeight;
  }

  function showLoading() {
    body.innerHTML = '<div class="ss-status">Loading…</div>';
    scrollBottom();
  }

  function renderQuestions() {
    body.innerHTML = "";
    addBot("Hi! Welcome to SportSphere Academy. How can we help you?");
    if (!state.faqs || !state.faqs.length) {
      addBot("Sorry, no FAQ questions are available right now.");
      scrollBottom();
      return;
    }
    var options = document.createElement("div");
    options.className = "ss-options";
    state.faqs.forEach(function (faq) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "ss-option";
      b.textContent = faq.question;
      b.addEventListener("click", function () {
        answerQuestion(faq);
      });
      options.appendChild(b);
    });
    body.appendChild(options);
    scrollBottom();
  }

  function answerQuestion(faq) {
    addUser(faq.question);
    var status = document.createElement("div");
    status.className = "ss-status";
    status.textContent = "…";
    body.appendChild(status);
    scrollBottom();

    fetch(CONFIG.apiBaseUrl + "faqs/" + faq.id + "/answer/")
      .then(function (r) {
        if (!r.ok) throw new Error("Request failed with status " + r.status);
        return r.json();
      })
      .then(function (payload) {
        status.remove();
        addBot(renderAnswer(payload.data.answer), true);
        addBackRow();
        scrollBottom();
      })
      .catch(function () {
        status.remove();
        addBot("Sorry, I could not fetch the answer. Please try again.");
        addBackRow();
        scrollBottom();
      });
  }

  function addBackRow() {
    var row = document.createElement("div");
    row.className = "ss-back-row";
    var back = document.createElement("button");
    back.type = "button";
    back.className = "ss-btn";
    back.textContent = "← Back to questions";
    back.addEventListener("click", renderQuestions);
    row.appendChild(back);
    body.appendChild(row);
    scrollBottom();
  }

  function loadFaqs() {
    showLoading();
    fetch(CONFIG.apiBaseUrl + "faqs/")
      .then(function (r) {
        if (!r.ok) throw new Error("Request failed with status " + r.status);
        return r.json();
      })
      .then(function (payload) {
        state.faqs = payload.data || [];
        state.loaded = true;
        renderQuestions();
      })
      .catch(function () {
        state.loaded = true;
        body.innerHTML = "";
        addBot("Sorry, I could not load the questions right now.");
        scrollBottom();
      });
  }

  function init() {
    if (document.getElementById("ss-chatbot-popup")) return;
    loadCss();
    launcher = buildLauncher();
    popup = buildPopup();
    body = popup.querySelector("#ss-chatbot-body");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();