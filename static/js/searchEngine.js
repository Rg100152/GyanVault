/* ============================================================
   GyanVault — instant search + Ctrl+K command palette
   No framework, no page reloads.  Curated by Raj Gautam.
   ============================================================ */

(function () {
  "use strict";

  var FALLBACK_IMAGE =
    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=400&q=70";

  var state = {
    resources: [],
    q: "",
    category: "",
    format: "",
    difficulty: "",
    sort: "latest",
    savedOnly: document.body.dataset.savedOnly === "true"
  };

  var $ = function (selector, root) {
    return (root || document).querySelector(selector);
  };

  var els = {
    grid: $("#resourceGrid"),
    empty: $("#emptyState"),
    count: $("#resultCount"),
    skeletons: $("#skeletons"),
    search: $("#searchInput"),
    clear: $("#searchClear"),
    reset: $("#resetFilters"),
    sort: $("#sortSelect"),
    statTotal: $("#statTotal"),
    statViews: $("#statViews"),
    statDownloads: $("#statDownloads"),
    cmdk: $("#cmdk"),
    cmdkInput: $("#cmdkInput"),
    cmdkResults: $("#cmdkResults"),
    cmdkCount: $("#cmdkCount")
  };

  var paletteIndex = 0;
  var paletteItems = [];

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function formatCount(n) {
    n = Number(n) || 0;
    if (n >= 1000) {
      return (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, "") + "k";
    }
    return String(n);
  }

  function badgeClass(format) {
    var f = String(format || "").toLowerCase();
    if (f.indexOf("video") !== -1) return "badge badge--video";
    if (f.indexOf("repo") !== -1) return "badge badge--repo";
    if (f.indexOf("ebook") !== -1) return "badge badge--ebook";
    return "badge badge--format";
  }

  var EYE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="2.6"/></svg>';
  var DOWN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 19h16"/></svg>';

  /* -------------------- Data -------------------- */

  function fetchResources() {
    fetch("/api/resources?limit=250")
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (payload) {
        state.resources = payload.resources || [];
        if (els.skeletons) els.skeletons.hidden = true;
        renderGrid();
      })
      .catch(function () {
        if (els.skeletons) els.skeletons.hidden = true;
        if (els.count) els.count.textContent = "Could not load the vault — refresh to retry.";
      });
  }

  function refreshStats() {
    fetch("/api/stats")
      .then(function (r) { return r.json(); })
      .then(function (s) {
        if (els.statTotal) els.statTotal.textContent = s.total;
        if (els.statViews) els.statViews.textContent = Number(s.views).toLocaleString();
        if (els.statDownloads) els.statDownloads.textContent = Number(s.downloads).toLocaleString();
      })
      .catch(function () { /* stats are cosmetic */ });
  }

  function matches(resource, query) {
    var haystack = [
      resource.title,
      resource.category,
      resource.format,
      resource.difficulty,
      resource.tags,
      resource.description
    ].join(" ").toLowerCase();
    return query
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean)
      .every(function (term) { return haystack.indexOf(term) !== -1; });
  }

  function filteredResources() {
    var list = state.resources.filter(function (r) {
      if (state.savedOnly && !(window.GyanVaultDrawer && window.GyanVaultDrawer.isSaved(r.id))) return false;
      if (state.format && r.format !== state.format) return false;
      if (state.category && r.category !== state.category) return false;
      if (state.difficulty && r.difficulty !== state.difficulty) return false;
      if (state.q && !matches(r, state.q)) return false;
      return true;
    });

    list.sort(function (a, b) {
      switch (state.sort) {
        case "popular": return (b.downloads - a.downloads) || (b.views - a.views);
        case "viewed": return b.views - a.views;
        case "title": return String(a.title).localeCompare(String(b.title));
        default:
          if (a.created_at !== b.created_at) return a.created_at < b.created_at ? 1 : -1;
          return b.id - a.id;
      }
    });
    return list;
  }

  /* -------------------- Cards -------------------- */

  function cardMarkup(resource, index) {
    var id = Number(resource.id);
    var image = resource.image_url || FALLBACK_IMAGE;
    var saved = window.GyanVaultDrawer && window.GyanVaultDrawer.isSaved(id);

    return (
      '<article class="resource-card" tabindex="0" role="button" data-action="preview" data-id="' + id + '"' +
      ' aria-label="Preview ' + escapeHtml(resource.title) + '"' +
      ' style="animation-delay:' + Math.min(index * 28, 420) + 'ms">' +
        '<div class="card__media">' +
          '<img src="' + escapeHtml(image) + '" alt="" loading="lazy" ' +
          'onerror="this.src=\'' + FALLBACK_IMAGE + '\'">' +
          '<div class="card__badges">' +
            '<span class="badge">' + escapeHtml(resource.category) + "</span>" +
            '<span class="' + badgeClass(resource.format) + '">' + escapeHtml(resource.format) + "</span>" +
          "</div>" +
        "</div>" +
        '<div class="card__body">' +
          '<span class="card__category">' + escapeHtml(resource.difficulty) + " · " + escapeHtml(resource.format) + "</span>" +
          '<h3 class="card__title">' + escapeHtml(resource.title) + "</h3>" +
          '<p class="card__desc">' + escapeHtml(resource.description) + "</p>" +
          '<div class="card__footer">' +
            '<button class="card__bookmark' + (saved ? " is-saved" : "") + '" type="button" ' +
              'data-action="bookmark" data-id="' + id + '" title="Bookmark" aria-label="Bookmark">' +
              (saved ? "★" : "☆") +
            "</button>" +
            '<span class="card__stat" data-stat="views" title="Views">' + EYE + formatCount(resource.views) + "</span>" +
            '<span class="card__stat" data-stat="downloads" title="Downloads">' + DOWN + formatCount(resource.downloads) + "</span>" +
            '<span class="card__preview">Preview →</span>' +
          "</div>" +
        "</div>" +
      "</article>"
    );
  }

  function renderGrid() {
    if (!els.grid) return;
    var list = filteredResources();
    els.grid.innerHTML = list.map(cardMarkup).join("");
    if (els.empty) els.empty.hidden = list.length > 0;
    if (els.count) {
      var suffix = state.savedOnly ? " in your saved vault" : "";
      els.count.textContent =
        "Showing " + list.length + " of " + state.resources.length + " resources" + suffix +
        (state.q ? ' · matching “' + state.q + '”' : "");
    }
    if (window.GyanVaultDrawer && window.GyanVaultDrawer.syncBookmarks) {
      window.GyanVaultDrawer.syncBookmarks();
    }
  }

  function updateCardCounter(id, column, value) {
    if (!els.grid) return;
    var card = els.grid.querySelector('[data-action="preview"][data-id="' + id + '"]');
    if (!card) return;
    var stat = card.querySelector('[data-stat="' + column + '"]');
    if (stat) {
      var icon = column === "views" ? EYE : DOWN;
      stat.innerHTML = icon + formatCount(value);
    }
    state.resources.forEach(function (r) {
      if (Number(r.id) === Number(id)) r[column] = value;
    });
  }

  /* -------------------- Command palette -------------------- */

  function openPalette() {
    if (!els.cmdk) return;
    els.cmdk.hidden = false;
    document.body.classList.add("overlay-open");
    if (els.cmdkInput) {
      els.cmdkInput.value = state.q || "";
      renderPalette(els.cmdkInput.value);
      window.requestAnimationFrame(function () {
        els.cmdk.focus();
        els.cmdkInput.focus();
        els.cmdkInput.select();
      });
    }
  }

  function closePalette() {
    if (!els.cmdk || els.cmdk.hidden) return;
    els.cmdk.classList.remove("is-open");
    els.cmdk.hidden = true;
    paletteItems = [];
    if (!(window.GyanVaultDrawer && window.GyanVaultDrawer.isOpen())) {
      document.body.classList.remove("overlay-open");
    }
  }

  function paletteMarkup(resource, index) {
    var selected = index === paletteIndex ? " is-selected" : "";
    return (
      '<button class="cmdk-item' + selected + '" type="button" data-palette-id="' + resource.id + '">' +
        '<img class="cmdk-item__thumb" src="' + escapeHtml(resource.image_url || FALLBACK_IMAGE) + '" alt="" ' +
          'onerror="this.src=\'' + FALLBACK_IMAGE + '\'">' +
        '<span class="cmdk-item__body">' +
          '<span class="cmdk-item__title">' + escapeHtml(resource.title) + "</span>" +
          '<span class="cmdk-item__sub">' + escapeHtml(resource.category) + " · " + escapeHtml(resource.format) + "</span>" +
        "</span>" +
        '<span class="cmdk-item__enter">↵</span>' +
      "</button>"
    );
  }

  function renderPalette(query) {
    if (!els.cmdkResults) return;
    var term = (query || "").trim();
    paletteItems = state.resources
      .filter(function (r) { return !term || matches(r, term); })
      .slice(0, 8);
    paletteIndex = 0;
    els.cmdkResults.innerHTML = paletteItems.length
      ? paletteItems.map(paletteMarkup).join("")
      : '<div class="cmdk-empty">No indexed resource matches that query.</div>';
    if (els.cmdkCount) els.cmdkCount.textContent = paletteItems.length + " result(s)";
  }

  function movePalette(step) {
    if (!paletteItems.length) return;
    paletteIndex = (paletteIndex + step + paletteItems.length) % paletteItems.length;
    var nodes = els.cmdkResults.querySelectorAll(".cmdk-item");
    for (var i = 0; i < nodes.length; i++) nodes[i].classList.toggle("is-selected", i === paletteIndex);
    if (nodes[paletteIndex]) nodes[paletteIndex].scrollIntoView({ block: "nearest" });
  }

  function choosePaletteItem() {
    var item = paletteItems[paletteIndex];
    if (!item) return;
    closePalette();
    if (window.GyanVaultDrawer) window.GyanVaultDrawer.open(item.id);
  }

  /* -------------------- Events -------------------- */

  function onChipClick(event, key) {
    var chip = event.target.closest("[" + key + "]");
    if (!chip) return;
    var container = chip.parentElement;
    container.querySelectorAll("[" + key + "]").forEach(function (node) {
      node.classList.remove("is-active");
    });
    chip.classList.add("is-active");
    state[key.replace("data-", "")] = chip.getAttribute(key) || "";
    renderGrid();
  }

  function bindEvents() {
    if (els.search) {
      els.search.addEventListener("input", function () {
        state.q = els.search.value.trim();
        if (els.clear) els.clear.hidden = !state.q;
        renderGrid();
      });
    }
    if (els.clear) {
      els.clear.addEventListener("click", function () {
        if (els.search) els.search.value = "";
        state.q = "";
        els.clear.hidden = true;
        renderGrid();
        if (els.search) els.search.focus();
      });
    }
    if (els.sort) {
      els.sort.addEventListener("change", function () {
        state.sort = els.sort.value;
        renderGrid();
      });
    }
    var formatChips = $("#formatChips");
    var categoryChips = $("#categoryChips");
    var difficultyFilter = $("#difficultyFilter");
    if (formatChips) formatChips.addEventListener("click", function (e) { onChipClick(e, "data-format"); });
    if (categoryChips) categoryChips.addEventListener("click", function (e) { onChipClick(e, "data-category"); });
    if (difficultyFilter) difficultyFilter.addEventListener("click", function (e) { onChipClick(e, "data-difficulty"); });

    if (els.reset) {
      els.reset.addEventListener("click", function () {
        state.q = state.category = state.format = state.difficulty = "";
        state.sort = "latest";
        if (els.search) els.search.value = "";
        if (els.clear) els.clear.hidden = true;
        if (els.sort) els.sort.value = "latest";
        document.querySelectorAll("[data-format],[data-category],[data-difficulty]").forEach(function (node) {
          node.classList.toggle("is-active", (node.getAttribute("data-format") ||
            node.getAttribute("data-category") || node.getAttribute("data-difficulty")) === "");
        });
        renderGrid();
      });
    }

    var trigger = $("#cmdkTrigger");
    var shortcut = $("#searchShortcut");
    if (trigger) trigger.addEventListener("click", openPalette);
    if (shortcut) shortcut.addEventListener("click", openPalette);
    document.querySelectorAll("[data-close-cmdk]").forEach(function (node) {
      node.addEventListener("click", closePalette);
    });

    if (els.cmdkInput) {
      els.cmdkInput.addEventListener("input", function () { renderPalette(els.cmdkInput.value); });
    }
    if (els.cmdkResults) {
      els.cmdkResults.addEventListener("click", function (event) {
        var item = event.target.closest("[data-palette-id]");
        if (!item) return;
        paletteItems.forEach(function (r, i) {
          if (String(r.id) === item.getAttribute("data-palette-id")) paletteIndex = i;
        });
        choosePaletteItem();
      });
      els.cmdkResults.addEventListener("mousemove", function (event) {
        var item = event.target.closest("[data-palette-id]");
        if (!item) return;
        var nodes = els.cmdkResults.querySelectorAll(".cmdk-item");
        for (var i = 0; i < nodes.length; i++) {
          if (nodes[i] === item && paletteIndex !== i) {
            paletteIndex = i;
            for (var j = 0; j < nodes.length; j++) {
              nodes[j].classList.toggle("is-selected", j === i);
            }
            break;
          }
        }
      });
    }

    document.addEventListener("keydown", function (event) {
      var key = (event.key || "").toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === "k") {
        event.preventDefault();
        if (els.cmdk && !els.cmdk.hidden) closePalette();
        else openPalette();
        return;
      }
      if (!els.cmdk || els.cmdk.hidden) return;
      if (key === "escape") { event.preventDefault(); closePalette(); return; }
      if (key === "arrowdown") { event.preventDefault(); movePalette(1); return; }
      if (key === "arrowup") { event.preventDefault(); movePalette(-1); return; }
      if (key === "enter") { event.preventDefault(); choosePaletteItem(); }
    });
  }

  /* -------------------- Public API -------------------- */

  window.GyanVault = {
    state: state,
    escapeHtml: escapeHtml,
    formatCount: formatCount,
    fallbackImage: FALLBACK_IMAGE,
    renderGrid: renderGrid,
    refreshStats: refreshStats,
    updateCardCounter: updateCardCounter,
    openPalette: openPalette,
    closePalette: closePalette,
    isPaletteOpen: function () { return !!(els.cmdk && !els.cmdk.hidden); }
  };

  document.addEventListener("DOMContentLoaded", function () {
    bindEvents();
    fetchResources();
  });
})();
