/* Generative AI for Developers · RR Skillverse handbook by Raushan Ranjan (MCT)
   Page helpers: theme, mobile sidebar, page filter, code/prompt boxes with copy,
   "on this page" rail, progress tracking (per browser), drill catalogue filter. */
(function () {
  var root = document.documentElement;

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value);
    } catch (e) { return null; }
    return null;
  }

  function isDark() {
    var a = root.getAttribute("data-theme");
    if (a) return a === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  var ICON_SPARK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 4.9L19 9.8l-5.1 1.9L12 17l-1.9-5.3L5 9.8l5.1-1.9z"/><path d="M19 15l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/></svg>';
  var ICON_PEN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/></svg>';

  function copyButton(getText, cls) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "copy-btn" + (cls ? " " + cls : "");
    b.textContent = "Copy";
    b.addEventListener("click", function () {
      var text = getText();
      var done = function () { b.textContent = "Copied"; setTimeout(function () { b.textContent = "Copy"; }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { b.textContent = "Select & copy"; });
      } else { b.textContent = "Select & copy"; }
    });
    return b;
  }

  function langOf(name) {
    var m = /\.([a-z0-9]+)$/i.exec(name || "");
    var map = { py: "python", js: "javascript", html: "html", json: "json", txt: "text", md: "markdown", ps1: "powershell", sh: "bash", env: "env", example: "env", toml: "toml" };
    return m ? (map[m[1].toLowerCase()] || m[1]) : "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    // ----- Theme -----
    var tbtn = document.querySelector("[data-theme-toggle]");
    if (tbtn) tbtn.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      root.setAttribute("data-theme", next);
      store("genai-theme", next);
    });

    // ----- Mobile sidebar -----
    var body = document.body;
    var openBtn = document.querySelector("[data-nav-open]");
    if (openBtn) openBtn.addEventListener("click", function () { body.classList.add("nav-open"); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-nav-close]"), function (el) {
      el.addEventListener("click", function () { body.classList.remove("nav-open"); });
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") body.classList.remove("nav-open"); });
    var active = document.querySelector(".sb-link.active");
    if (active && active.scrollIntoView) active.scrollIntoView({ block: "center" });

    // ----- Sidebar filter -----
    var filter = document.querySelector("[data-nav-filter]");
    if (filter) filter.addEventListener("input", function () {
      var q = filter.value.trim().toLowerCase();
      Array.prototype.forEach.call(document.querySelectorAll(".sb-nav .sb-link, .sb-nav .sb-module"), function (a) {
        a.classList.toggle("sb-hidden", q && a.textContent.toLowerCase().indexOf(q) === -1);
      });
      Array.prototype.forEach.call(document.querySelectorAll(".sb-mod"), function (d) {
        if (q) d.open = !!d.querySelector(".sb-link:not(.sb-hidden)");
        d.classList.toggle("sb-hidden", q && !d.querySelector(".sb-link:not(.sb-hidden)") && d.querySelector("summary").textContent.toLowerCase().indexOf(q) === -1);
      });
      Array.prototype.forEach.call(document.querySelectorAll(".sb-section"), function (s) {
        s.classList.toggle("sb-hidden", q && !s.querySelector(".sb-link:not(.sb-hidden), .sb-module:not(.sb-hidden)"));
      });
    });

    // ----- Reading progress -----
    var bar = document.querySelector(".progress");
    if (bar) {
      var onScroll = function () {
        var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
        bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    // ----- Editor-style code boxes -----
    Array.prototype.forEach.call(document.querySelectorAll("pre.code, pre.term"), function (pre) {
      var isTerm = pre.classList.contains("term");
      var box = document.createElement("div");
      box.className = "codebox" + (isTerm ? " term" : "");
      var head = document.createElement("div");
      head.className = "codebox-head";
      var name = pre.getAttribute("data-file") || (isTerm ? "Terminal" : "");
      head.innerHTML = '<span class="fname"></span>';
      head.querySelector(".fname").textContent = name;
      head.appendChild(copyButton(function () {
        if (!isTerm) return pre.innerText;
        // copy commands only: drop prompt markers and output lines marked .o
        var clone = pre.cloneNode(true);
        Array.prototype.forEach.call(clone.querySelectorAll(".ps, .o"), function (n) { n.remove(); });
        return clone.innerText.replace(/\n{2,}/g, "\n").trim();
      }));
      pre.parentNode.insertBefore(box, pre);
      box.appendChild(head);
      box.appendChild(pre);
    });

    // ----- Prompt and template boxes -----
    Array.prototype.forEach.call(document.querySelectorAll(".prompt-box, .template-box"), function (box) {
      var pre = box.querySelector("pre");
      if (!pre) return;
      var isTemplate = box.classList.contains("template-box");
      var head = document.createElement("div");
      head.className = "prompt-head";
      head.innerHTML = '<span class="ptitle"></span><span class="ptools"></span>';
      head.querySelector(".ptitle").textContent = box.getAttribute("data-title") || (isTemplate ? "Prompt template · fill in the blanks" : "Prompt · paste into your AI assistant");
      head.querySelector(".ptools").textContent = isTemplate ? "" : (box.getAttribute("data-tools") || "Copilot · Claude Code · Codex");
      head.appendChild(copyButton(function () { return pre.innerText; }));
      box.insertBefore(head, pre);
    });

    // ----- Progress tracking (this browser only) -----
    function doneKey(id) { return "genai-done:" + id; }
    Array.prototype.forEach.call(document.querySelectorAll("input[data-done], input[data-page-done]"), function (cb) {
      var id = cb.getAttribute("data-done") || cb.getAttribute("data-page-done");
      cb.checked = store(doneKey(id)) === "1";
      cb.addEventListener("change", function () {
        store(doneKey(id), cb.checked ? "1" : null);
        if (cb.hasAttribute("data-page-done")) markSidebar();
      });
    });
    function markSidebar() {
      Array.prototype.forEach.call(document.querySelectorAll(".sb-link[data-page-id]"), function (a) {
        a.classList.toggle("done", store(doneKey(a.getAttribute("data-page-id"))) === "1");
      });
    }
    markSidebar();

    // ----- Open <details> targeted by the URL hash -----
    function openHash() {
      var el = location.hash && document.getElementById(location.hash.slice(1));
      if (el && el.tagName === "DETAILS") el.open = true;
    }
    window.addEventListener("hashchange", openHash);
    openHash();

    // ----- Drill catalogue filter -----
    var fbar = document.querySelector("[data-drill-filter]");
    if (fbar) fbar.addEventListener("click", function (e) {
      var btn = e.target.closest("button");
      if (!btn) return;
      Array.prototype.forEach.call(fbar.querySelectorAll("button"), function (b) { b.classList.toggle("on", b === btn); });
      var want = btn.getAttribute("data-step");
      Array.prototype.forEach.call(document.querySelectorAll(".drill-table tbody tr[data-steps]"), function (tr) {
        tr.style.display = !want || tr.getAttribute("data-steps").split(",").indexOf(want) !== -1 ? "" : "none";
      });
    });

    // ----- On this page rail -----
    var otp = document.querySelector(".otp");
    var heads = Array.prototype.slice.call(document.querySelectorAll(".content h2[id], .content .phase[id], .content .drill[id]"));
    if (otp && heads.length > 2) {
      var title = document.createElement("div");
      title.className = "otp-title";
      title.textContent = "On this page";
      otp.appendChild(title);
      var links = heads.map(function (h) {
        var a = document.createElement("a");
        a.href = "#" + h.id;
        var label = h.classList.contains("drill") ? (h.querySelector(".drill-id").textContent + " · " + h.getAttribute("data-title"))
                  : h.classList.contains("phase") ? h.querySelector("h2").textContent : h.textContent;
        a.textContent = label;
        otp.appendChild(a);
        return a;
      });
      if ("IntersectionObserver" in window) {
        var current = null;
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (!en.isIntersecting) return;
            var i = heads.indexOf(en.target);
            if (current) current.classList.remove("active");
            current = links[i];
            current.classList.add("active");
          });
        }, { rootMargin: "-80px 0px -70% 0px" });
        heads.forEach(function (h) { io.observe(h); });
      }
    }
  });
})();

// Concept maps: expand/collapse all, find a term, jump to a connected topic.
(function () {
  const map = document.querySelector("[data-cmap]");
  if (!map) return;
  const all = () => map.querySelectorAll("details");
  const openTo = (el) => { for (let d = el; d; d = d.parentElement.closest("details")) d.open = true; };
  document.querySelector('[data-cm="expand"]')?.addEventListener("click", () => all().forEach((d) => (d.open = true)));
  document.querySelector('[data-cm="collapse"]')?.addEventListener("click", () =>
    all().forEach((d) => (d.open = d.classList.contains("cm-root"))));
  map.addEventListener("click", (e) => {
    const btn = e.target.closest(".cm-link");
    if (!btn) return;
    const target = document.getElementById(btn.dataset.target);
    if (!target) return;
    openTo(target);
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("cm-flash");
    setTimeout(() => target.classList.remove("cm-flash"), 1600);
  });
  const jump = () => {                      // links from the overview picture: #t-tokens
    const target = location.hash && document.getElementById(location.hash.slice(1));
    if (target && target.classList.contains("cm-topic")) { openTo(target); target.classList.add("cm-flash");
      setTimeout(() => target.classList.remove("cm-flash"), 1600); }
  };
  window.addEventListener("hashchange", jump); jump();
  const filter = document.querySelector('[data-cm="filter"]');
  filter?.addEventListener("input", () => {
    const q = filter.value.trim().toLowerCase();
    map.querySelectorAll(".cm-topic").forEach((t) => {
      const hit = !q || t.textContent.toLowerCase().includes(q);
      t.classList.toggle("cm-hidden", !hit);
      if (q && hit) openTo(t.parentElement);
    });
  });
})();
