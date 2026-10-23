/* Sparrow Decider site: shared behaviour. Vanilla JS, no dependencies, no tracking.
   Data for the hero trace and the pico-or-nano widget come from JSON islands in the page,
   which are generated from site/facts.json (see _build/build.py). */
(function () {
  "use strict";
  var doc = document.documentElement;
  var mqReduce = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  function reduced() { return mqReduce.matches; }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function data(id) { var el = document.getElementById(id); if (!el) return null; try { return JSON.parse(el.textContent); } catch (e) { return null; } }
  var status = $("#sr-status");
  function announce(msg) { if (!status) return; status.textContent = ""; setTimeout(function () { status.textContent = msg; }, 30); }

  /* ---------- theme ---------- */
  function applyThemeLabels() {
    var light = doc.getAttribute("data-theme") === "light";
    $$(".theme-toggle").forEach(function (b) { b.setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme"); });
    $$(".theme-name").forEach(function (s) { s.textContent = light ? "Light" : "Dark"; });
    var meta = $('meta[name="theme-color"]'); if (meta) meta.setAttribute("content", light ? "#FAFBFF" : "#0B1020");
  }
  $$(".theme-toggle").forEach(function (b) {
    b.addEventListener("click", function () {
      var next = doc.getAttribute("data-theme") === "light" ? "dark" : "light";
      doc.setAttribute("data-theme", next);
      try { localStorage.setItem("sd-theme", next); } catch (e) { /* storage blocked: theme still switches for this page */ }
      applyThemeLabels();
    });
  });
  applyThemeLabels();

  /* ---------- header hairline ---------- */
  var header = $(".site-header");
  function onScroll() { if (header) header.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* ---------- mobile menu ---------- */
  var menuBtn = $(".menu-btn"), sheet = $("#site-menu");
  function menuOpen() { return sheet && !sheet.hidden; }
  function setMenu(open, restoreFocus) {
    if (!sheet || !menuBtn) return;
    sheet.hidden = !open;
    doc.classList.toggle("menu-open", open);
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    if (open) { var first = $("a, button", sheet); if (first) first.focus(); }
    else if (restoreFocus) menuBtn.focus();
  }
  if (menuBtn && sheet) {
    menuBtn.addEventListener("click", function () { setMenu(!menuOpen(), true); });
    sheet.addEventListener("click", function (e) {
      if (e.target.classList.contains("backdrop")) setMenu(false, true);
      if (e.target.closest("a")) setMenu(false, false);
    });
    document.addEventListener("keydown", function (e) {
      if (!menuOpen()) return;
      if (e.key === "Escape") { setMenu(false, true); return; }
      if (e.key === "Tab") { // trap focus inside header + panel
        var items = $$("a[href], button:not([disabled])", header).filter(function (x) { return x.offsetParent !== null; })
          .concat($$("a[href], button:not([disabled])", sheet));
        var i = items.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); items[items.length - 1].focus(); }
        else if (!e.shiftKey && i === items.length - 1) { e.preventDefault(); items[0].focus(); }
      }
    });
    window.addEventListener("resize", function () { if (window.innerWidth >= 1024 && menuOpen()) setMenu(false, false); });
  }

  /* ---------- copy buttons ---------- */
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (res, rej) {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      var ok = false; try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      ok ? res() : rej();
    });
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".copy-btn");
    if (!btn) return;
    var src = btn.getAttribute("data-copy-target") ? document.getElementById(btn.getAttribute("data-copy-target")) : null;
    var text = btn.getAttribute("data-copy") || (src ? src.textContent : "");
    var label = $(".label", btn), idle = btn.getAttribute("data-label") || "Copy";
    copyText(text).then(function () {
      btn.classList.add("copied");
      if (label) label.textContent = "Copied";
      announce("Copied " + (text.length < 60 ? text : "code") + " to the clipboard");
      clearTimeout(btn._t);
      btn._t = setTimeout(function () { btn.classList.remove("copied"); if (label) label.textContent = idle; }, 1600);
    }).catch(function () {
      var codeEl = src || (btn.parentNode && $("code", btn.parentNode));
      if (codeEl) { var r = document.createRange(); r.selectNodeContents(codeEl); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
      if (label) label.textContent = isMac ? "Press ⌘C" : "Press Ctrl+C";
    });
  });

  /* ---------- reveal + one-shot animations ---------- */
  var revealIO = ("IntersectionObserver" in window) ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add("in"); revealIO.unobserve(en.target); }
    });
  }, { threshold: 0.01, rootMargin: "0px 0px -4% 0px" }) : null;
  $$(".reveal, .stats, .anim, .layers").forEach(function (el) { if (revealIO && !reduced()) revealIO.observe(el); else el.classList.add("in"); });

  /* ---------- pause ambient loops off-screen ---------- */
  if ("IntersectionObserver" in window) {
    $$(".cta, .hero").forEach(function (el) {
      new IntersectionObserver(function (es) { el.classList.toggle("paused", !es[0].isIntersecting); }, { threshold: 0 }).observe(el);
    });
  }

  /* ---------- ARIA tabs (code tabs, tier tabs) ---------- */
  $$("[role=tablist]").forEach(function (list) {
    var tabs = $$("[role=tab]", list);
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        var p = document.getElementById(t.getAttribute("aria-controls"));
        if (p) p.hidden = !on;
      });
      if (focus) { tab.focus(); if (tab.scrollIntoView && list.scrollWidth > list.clientWidth) tab.scrollIntoView({ block: "nearest", inline: "nearest" }); }
      list.dispatchEvent(new CustomEvent("tabchange", { detail: tab }));
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var n = null;
        if (e.key === "ArrowRight") n = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") n = tabs[0];
        else if (e.key === "End") n = tabs[tabs.length - 1];
        if (n) { e.preventDefault(); select(n, true); }
      });
    });
    list._select = select;
  });

  /* ---------- tier ruler ---------- */
  var tierList = $("#tier-tabs"), ruler = $("#ruler");
  function markTier(tier) {
    if (!ruler) return;
    $$(".dot", ruler).forEach(function (d) { var on = d.getAttribute("data-tier") === tier; d.classList.toggle("on", on); });
    $$(".dlabel", ruler).forEach(function (d) { d.classList.toggle("on", d.getAttribute("data-tier") === tier); });
  }
  if (tierList) {
    tierList.addEventListener("tabchange", function (e) { markTier(e.detail.getAttribute("data-tier")); });
    var sel = $("[aria-selected=true]", tierList); if (sel) markTier(sel.getAttribute("data-tier"));
  }
  $$("[data-select-tier]").forEach(function (a) {
    a.addEventListener("click", function () {
      var t = document.getElementById("tt-" + a.getAttribute("data-select-tier"));
      if (t && tierList && tierList._select) tierList._select(t);
    });
  });

  /* ---------- in-page nav highlight ---------- */
  var chips = $$(".inpage .chips a");
  if (chips.length && "IntersectionObserver" in window) {
    var byId = {};
    chips.forEach(function (c) { byId[c.getAttribute("href").slice(1)] = c; });
    var navIO = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting && byId[en.target.id]) {
          chips.forEach(function (c) { c.classList.remove("active"); c.removeAttribute("aria-current"); });
          var c = byId[en.target.id]; c.classList.add("active"); c.setAttribute("aria-current", "true");
          if (c.scrollIntoView && c.parentNode.parentNode.scrollWidth > c.parentNode.parentNode.clientWidth) {
            var row = c.closest(".chips"); if (row) row.scrollTo({ left: c.offsetLeft - 16, behavior: reduced() ? "auto" : "smooth" });
          }
        }
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    Object.keys(byId).forEach(function (id) { var s = document.getElementById(id); if (s) navIO.observe(s); });
  }

  /* ---------- hero decision trace ---------- */
  (function trace() {
    var cfg = data("trace-data"), root = $("#trace");
    if (!cfg || !root) return;
    var el = {
      model: $(".model", root), state: $(".t-state", root), q: $(".t-q", root), bars: $(".t-bars", root),
      scan: $(".t-scan", root), ans: $(".t-answer b", root), n: $(".t-lat .n", root), small: $(".t-lat small", root),
      pause: $(".pause", root)
    };
    var switches = $$(".scene-switch button");
    var LINE = 120, Q_GAP = 0, BAR_GAP = 240, STAG = 40, HOLD = 1800, CHAR = 40;
    var idx = 0, built = -1, st = 0, last = null, playing = !reduced(), visible = true, raf = null;

    function times(s) {
      var tq = s.state.length * LINE + Q_GAP;
      var tb = tq + BAR_GAP;
      var tr = tb + s.options.length * STAG + 200;
      var te = tr + s.resolveMs;
      return { tq: tq, tb: tb, tr: tr, te: te, end: te + s.answer.length * CHAR + HOLD };
    }
    function build(s) {
      el.model.textContent = s.model;
      el.state.innerHTML = "";
      s.state.forEach(function (kv) {
        var sp = document.createElement("span");
        sp.innerHTML = '<span class="k"></span><span class="v"></span>';
        sp.firstChild.textContent = kv[0] + ": "; sp.lastChild.textContent = kv[1];
        el.state.appendChild(sp);
      });
      el.q.textContent = s.question;
      el.bars.innerHTML = "";
      s.options.forEach(function (o) {
        var row = document.createElement("div");
        row.className = "t-bar" + (o[0] === s.answer ? " is-win" : "");
        row.innerHTML = '<span class="o"></span><span class="trk"><span class="fill"></span></span><span class="p"></span>';
        row.firstChild.textContent = o[0];
        el.bars.appendChild(row);
      });
      el.small.textContent = s.caption;
      switches.forEach(function (b, i) { b.setAttribute("aria-pressed", i === idx ? "true" : "false"); });
      built = idx;
    }
    function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function render() {
      var s = cfg.scenes[idx]; if (built !== idx) build(s);
      var T = times(s);
      $$(":scope > span", el.state).forEach(function (sp, i) { sp.classList.toggle("pre", st < i * LINE); });
      el.q.classList.toggle("pre", st < T.tq);
      var prog = Math.max(0, Math.min(1, (st - T.tr) / s.resolveMs));
      var resolved = st >= T.te;
      $$(".t-bar", el.bars).forEach(function (row, i) {
        var o = s.options[i];
        row.classList.toggle("pre", st < T.tb + i * STAG);
        row.querySelector(".fill").style.width = (o[1] * 100 * ease(prog)).toFixed(2) + "%";
        row.querySelector(".p").textContent = resolved ? o[1].toFixed(2) : "";
        row.classList.toggle("win", resolved && o[0] === s.answer);
      });
      root.classList.toggle("resolved", resolved);
      if (st < T.tr) el.n.textContent = (0).toFixed(s.decimals) + " " + s.unit;
      else if (!resolved) el.n.textContent = (s.value * prog).toFixed(s.decimals) + " " + s.unit;
      else el.n.textContent = s.time;
      el.n.classList.toggle("flash", resolved && st - T.te < 90);
      var chars = resolved ? Math.floor((st - T.te) / CHAR) + 1 : 0;
      el.ans.textContent = s.answer.slice(0, Math.max(0, chars));
      if (el.scan) {
        var on = prog > 0 && prog < 1;
        el.scan.style.opacity = on ? 1 : 0;
        if (on) el.scan.style.transform = "translateX(" + (((prog * 2) % 1) * (el.bars.clientWidth + 40)).toFixed(1) + "px)";
      }
      return T.end;
    }
    var wd = null;
    function frame() {
      var t = performance.now();
      raf = null; clearTimeout(wd);
      if (last == null) last = t;
      var dt = Math.min(250, t - last); last = t;
      if (playing && visible) {
        st += dt;
        var end = render();
        if (st >= end) { idx = (idx + 1) % cfg.scenes.length; st = 0; render(); }
      }
      if (playing && visible) schedule(); else last = null;
    }
    // rAF drives the clock; a slow timer keeps it moving where rAF is throttled (some embeds, headless capture).
    function schedule() { raf = requestAnimationFrame(frame); wd = setTimeout(function () { if (raf) { cancelAnimationFrame(raf); frame(); } }, 120); }
    function kick() { if (!raf && playing && visible) { last = null; schedule(); } }
    function showFinal(i) { idx = i; st = 1e9; render(); }
    function setPlaying(p) {
      playing = p;
      if (el.pause) { el.pause.setAttribute("aria-pressed", p ? "false" : "true"); el.pause.setAttribute("aria-label", p ? "Pause animation" : "Play animation"); }
      kick();
    }
    if (el.pause) el.pause.addEventListener("click", function () { setPlaying(!playing); });
    switches.forEach(function (b, i) {
      b.addEventListener("click", function () {
        idx = i; built = -1;
        if (reduced() || !playing) showFinal(i); else { st = 0; render(); }
      });
    });
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; kick(); }, { threshold: 0.1 }).observe(root);
    document.addEventListener("visibilitychange", function () { visible = !document.hidden; kick(); });
    function init() {
      if (reduced()) { doc.classList.add("rm"); playing = false; showFinal(idx); if (el.pause) el.pause.hidden = true; }
      else { doc.classList.remove("rm"); if (el.pause) el.pause.hidden = false; st = 0; built = -1; setPlaying(true); }
    }
    if (mqReduce.addEventListener) mqReduce.addEventListener("change", init);
    init();
  })();

  /* ---------- pico or nano widget ---------- */
  (function widget() {
    var cfg = data("pn-data"), root = $("#pn-widget");
    if (!cfg || !root) return;
    var flow = $("#pn-flow"), hist = [];
    function hl(edges, node) {
      if (!flow) return;
      $$(".edge--on", flow).forEach(function (x) { x.classList.remove("edge--on"); });
      $$(".node--on", flow).forEach(function (x) { x.classList.remove("node--on"); });
      edges.forEach(function (id) { var e = flow.querySelector("#" + id); if (e) e.classList.add("edge--on"); });
      if (node) { var n = flow.querySelector("#" + node); if (n) n.classList.add("node--on"); }
    }
    function histHTML() {
      if (!hist.length) return "";
      return '<ul class="w-hist">' + hist.map(function (h) { return "<li><span>" + h[0] + "</span><b>" + h[1] + "</b></li>"; }).join("") + "</ul>";
    }
    function ask(qi, focus) {
      var q = cfg.questions[qi];
      root.innerHTML = '<div class="w-step">' + histHTML() + '<div class="t-label">question</div><h3 class="q" tabindex="-1">' + q.html +
        '</h3><div class="w-opts"><button type="button" data-a="yes">Yes</button><button type="button" data-a="no">No</button></div>' +
        (hist.length ? '<button type="button" class="w-reset">Start over</button>' : "") + "</div>";
      $$(".w-opts button", root).forEach(function (b) {
        b.addEventListener("click", function () {
          var a = b.getAttribute("data-a");
          hist.push([q.short, a === "yes" ? "Yes" : "No"]);
          var next = q[a];
          if (next.q != null) { hl(next.edges, null); ask(next.q, true); }
          else { hl(next.edges, next.node); result(next.r); }
        });
      });
      var rs = $(".w-reset", root); if (rs) rs.addEventListener("click", reset);
      if (focus) $(".q", root).focus();
    }
    function result(ri) {
      var r = cfg.results[ri];
      root.innerHTML = '<div class="w-step w-result">' + histHTML() + '<div class="t-label">answer</div><h3 class="ans" tabindex="-1">' + r.name + "</h3><p>" + r.html +
        '</p><div class="w-actions">' + r.links + '<button type="button" class="w-reset">Start over</button></div></div>';
      $(".w-reset", root).addEventListener("click", reset);
      $$("[data-select-tier]", root).forEach(function (a) {
        a.addEventListener("click", function () { var t = document.getElementById("tt-" + a.getAttribute("data-select-tier")); var l = $("#tier-tabs"); if (t && l && l._select) l._select(t); });
      });
      $(".ans", root).focus();
      announce("Answer: " + r.name);
    }
    function reset() { hist = []; hl([], null); ask(0, true); }
    ask(0, false);
  })();
})();
