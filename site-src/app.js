(function () {
  var root = document.documentElement;
  var btn = document.getElementById("theme");
  var saved = null;
  try { saved = localStorage.getItem("omo-theme"); } catch (e) {}
  if (saved === "light" || saved === "dark") {
    root.setAttribute("data-theme", saved);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    root.setAttribute("data-theme", "dark");
  } else {
    root.setAttribute("data-theme", "light");
  }
  function syncLabel() {
    if (!btn) return;
    btn.textContent = root.getAttribute("data-theme") === "dark" ? "Светлая" : "Тёмная";
  }
  syncLabel();
  if (btn) btn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("omo-theme", next); } catch (e) {}
    syncLabel();
    renderMermaid();
  });

  // Поиск по search-index.json
  var input = document.getElementById("search");
  var box = document.getElementById("results");
  var index = null;
  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function load() {
    if (index) return Promise.resolve(index);
    return fetch("./search-index.json").then(function (r) { return r.json(); }).then(function (j) {
      index = j;
      return j;
    }).catch(function () { return []; });
  }
  function snippet(text, q) {
    var low = text.toLowerCase();
    var at = low.indexOf(q);
    if (at < 0) return esc(text.slice(0, 140)) + "…";
    var from = Math.max(0, at - 60);
    var to = Math.min(text.length, at + q.length + 80);
    var part = esc(text.slice(from, to));
    return (from > 0 ? "…" : "") + part.replace(esc(q), "<mark>" + esc(q) + "</mark>") + (to < text.length ? "…" : "");
  }
  function render(list, q) {
    if (!box) return;
    if (!q) { box.hidden = true; box.innerHTML = ""; return; }
    if (!list.length) {
      box.hidden = false;
      box.innerHTML = '<div class="empty">Ничего не найдено. Попробуйте другое слово.</div>';
      return;
    }
    box.hidden = false;
    box.innerHTML = list.map(function (it) {
      return '<a href="' + it.url + '"><strong>' + esc(it.title) + "</strong><small>" + snippet(it.text, q) + "</small></a>";
    }).join("");
  }
  if (input) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      if (q.length < 2) { render([], ""); return; }
      load().then(function (idx) {
        var out = [];
        for (var k = 0; k < idx.length && out.length < 7; k++) {
          var e = idx[k];
          var hay = (e.title + " " + e.headings.join(" ") + " " + e.text).toLowerCase();
          if (hay.indexOf(q) >= 0) out.push(e);
        }
        render(out, q);
      });
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") { input.value = ""; render([], ""); input.blur(); }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "/" && document.activeElement !== input) { ev.preventDefault(); input.focus(); }
    });
    document.addEventListener("click", function (ev) {
      if (box && !box.hidden && !ev.target.closest(".search")) { box.hidden = true; }
    });
  }

  // Mermaid: рендерим схемы, при ошибке оставляем исходник
  function renderMermaid() {
    try {
      if (window.mermaid) {
        var dark = root.getAttribute("data-theme") === "dark";
        window.mermaid.initialize({
          startOnLoad: false, securityLevel: "loose",
          theme: dark ? "dark" : "default"
        });
        window.mermaid.run({ querySelector: ".mermaid" }).then(function () {
          document.querySelectorAll(".mermaid-wrap").forEach(function (w) {
            var src = w.querySelector(".mermaid-source");
            var svg = w.querySelector("svg");
            if (src && svg) src.style.display = "none";
          });
        }).catch(function () {});
      }
    } catch (e) {}
  }
  window.addEventListener("load", function () {
    setTimeout(renderMermaid, 50);
    setTimeout(renderMermaid, 600);
  });
})();
