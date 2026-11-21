/* ============================================================
   GyanVault — slide-over preview, counters & bookmarks
   Bookmarks are stored locally per browser (no login required).
   Curated by Raj Gautam.
   ============================================================ */

(function () {
  "use strict";

  var STORAGE_KEY = "gyanvault_bookmarks";
  var drawer = document.getElementById("drawer");
  var cover = document.getElementById("drawerCover");
  var badges = document.getElementById("drawerBadges");
  var titleEl = document.getElementById("drawerTitle");
  var descriptionEl = document.getElementById("drawerDescription");
  var tagsEl = document.getElementById("drawerTags");
  var metaEl = document.getElementById("drawerMeta");
  var openLink = document.getElementById("drawerOpen");
  var downloadBtn = document.getElementById("drawerDownload");
  var downloadCount = document.getElementById("drawerDownloads");
  var bookmarkBtn = document.getElementById("drawerBookmark");

  var current = null;
  var bookmarks = loadBookmarks();
  var closeTimer = null;

  function loadBookmarks() {
    try {
      var parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      if (!Array.isArray(parsed)) return [];
      return parsed.map(Number).filter(function (n) { return !isNaN(n); });
    } catch (error) {
      return [];
    }
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
    } catch (error) {
      /* private browsing — bookmarks simply stay in memory */
    }
  }

  function isSaved(id) {
    return bookmarks.indexOf(Number(id)) !== -1;
  }

  function toggleBookmark(id) {
    id = Number(id);
    var index = bookmarks.indexOf(id);
    if (index === -1) bookmarks.push(id);
    else bookmarks.splice(index, 1);
    persist();
    syncBookmarks();
    if (current && Number(current.id) === id) updateDrawerBookmark();
    if (window.GyanVault && window.GyanVault.state.savedOnly) window.GyanVault.renderGrid();
  }

  function syncBookmarks() {
    document.querySelectorAll(".card__bookmark").forEach(function (button) {
      var saved = isSaved(button.getAttribute("data-id"));
      button.classList.toggle("is-saved", saved);
      button.textContent = saved ? "★" : "☆";
    });
    updateDrawerBookmark();
  }

  function updateDrawerBookmark() {
    if (!bookmarkBtn || !current) return;
    var saved = isSaved(current.id);
    bookmarkBtn.classList.toggle("is-saved", saved);
    bookmarkBtn.textContent = saved ? "★" : "☆";
    bookmarkBtn.setAttribute("aria-label", saved ? "Remove bookmark" : "Bookmark resource");
  }

  function findResource(id) {
    if (!window.GyanVault) return null;
    var found = null;
    window.GyanVault.state.resources.forEach(function (r) {
      if (Number(r.id) === Number(id)) found = r;
    });
    return found;
  }

  function badgeMarkup(resource) {
    var esc = window.GyanVault ? window.GyanVault.escapeHtml : function (v) { return String(v); };
    var fmt = String(resource.format || "").toLowerCase();
    var cls = fmt.indexOf("video") !== -1 ? "badge--video"
      : fmt.indexOf("repo") !== -1 ? "badge--repo"
      : fmt.indexOf("ebook") !== -1 ? "badge--ebook" : "badge--format";
    return (
      '<span class="badge">' + esc(resource.category) + "</span>" +
      '<span class="badge ' + cls + '">' + esc(resource.format) + "</span>" +
      '<span class="badge">' + esc(resource.difficulty) + "</span>"
    );
  }

  function render(resource) {
    current = resource;
    var esc = window.GyanVault ? window.GyanVault.escapeHtml : function (v) { return String(v); };
    var fmt = window.GyanVault ? window.GyanVault.formatCount : function (n) { return String(n); };
    var image = resource.image_url || (window.GyanVault ? window.GyanVault.fallbackImage : "");

    cover.innerHTML = '<img src="' + esc(image) + '" alt="">';
    var img = cover.querySelector("img");
    if (img && window.GyanVault) {
      img.onerror = function () { this.src = window.GyanVault.fallbackImage; };
    }

    badges.innerHTML = badgeMarkup(resource);
    titleEl.textContent = resource.title || "";
    descriptionEl.textContent = resource.description || "No description available for this resource.";

    var tags = String(resource.tags || "").split(",").map(function (t) { return t.trim(); }).filter(Boolean);
    tagsEl.innerHTML = tags.map(function (tag) { return '<span class="tag">#' + esc(tag) + "</span>"; }).join("");

    metaEl.innerHTML =
      "<div><dt>Views</dt><dd>" + fmt(resource.views) + "</dd></div>" +
      "<div><dt>Downloads</dt><dd>" + fmt(resource.downloads) + "</dd></div>" +
      "<div><dt>Added</dt><dd>" + esc(String(resource.created_at || "").slice(0, 10)) + "</dd></div>";

    openLink.href = resource.resource_url || "#";
    downloadCount.textContent = fmt(resource.downloads);
    updateDrawerBookmark();

    drawer.hidden = false;
    document.body.classList.add("overlay-open");
    if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; }
    window.requestAnimationFrame(function () { drawer.classList.add("is-open"); });

    recordCounter("view");
  }

  function open(id) {
    var resource = findResource(id);
    if (resource) { render(resource); return; }
    fetch("/api/resources/" + encodeURIComponent(id))
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (payload) { render(payload.resource); })
      .catch(function () { /* resource vanished — ignore */ });
  }

  function close() {
    if (!drawer || drawer.hidden) return;
    drawer.classList.remove("is-open");
    closeTimer = window.setTimeout(function () {
      drawer.hidden = true;
      if (!(window.GyanVault && window.GyanVault.isPaletteOpen())) {
        document.body.classList.remove("overlay-open");
      }
    }, 380);
  }

  function isOpen() {
    return !!(drawer && !drawer.hidden);
  }

  function recordCounter(column) {
    if (!current) return;
    var id = current.id;
    fetch("/api/resources/" + id + "/" + column, { method: "POST" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (payload) {
        if (!payload || typeof payload[column] !== "number") return;
        current[column] = payload[column];
        if (column === "views") {
          var views = metaEl.querySelectorAll("dd")[0];
          if (views) views.textContent = window.GyanVault ? window.GyanVault.formatCount(payload.views) : payload.views;
        } else {
          downloadCount.textContent = window.GyanVault ? window.GyanVault.formatCount(payload.downloads) : payload.downloads;
        }
        if (window.GyanVault) {
          window.GyanVault.updateCardCounter(id, column, payload[column]);
          if (column === "downloads") window.GyanVault.refreshStats();
        }
      })
      .catch(function () { /* counter failure must not break the UI */ });
  }

  function triggerDownload() {
    if (!current) return;
    var url = current.resource_url;
    if (url) {
      var link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
    recordCounter("download");
  }

  /* -------------------- Events -------------------- */

  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-close-drawer]")) { close(); return; }

    var bookmark = event.target.closest('[data-action="bookmark"]');
    if (bookmark) {
      event.preventDefault();
      event.stopPropagation();
      toggleBookmark(bookmark.getAttribute("data-id"));
      return;
    }

    if (event.target.closest("#drawerDownload")) { triggerDownload(); return; }

    var card = event.target.closest('.resource-card[data-action="preview"]');
    if (card) { open(card.getAttribute("data-id")); }
  });

  document.addEventListener("keydown", function (event) {
    var key = (event.key || "").toLowerCase();
    if (key === "escape") {
      if (window.GyanVault && window.GyanVault.isPaletteOpen()) return;
      close();
      return;
    }
    if ((key === "enter" || key === " ") && event.target.classList &&
        event.target.classList.contains("resource-card")) {
      event.preventDefault();
      open(event.target.getAttribute("data-id"));
    }
  });

  window.GyanVaultDrawer = {
    open: open,
    close: close,
    isOpen: isOpen,
    isSaved: isSaved,
    toggleBookmark: toggleBookmark,
    syncBookmarks: syncBookmarks
  };
})();
