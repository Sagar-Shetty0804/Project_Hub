/* ProjectHub UI behaviour — plain JS, no framework. */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ($("[name=csrfmiddlewaretoken]") || {}).value;

  /* ---------- theme toggle ---------- */
  $$("[data-theme-toggle]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) { /* storage unavailable */ }
    })
  );

  /* ---------- header shadow on scroll ---------- */
  const header = $(".site-header");
  if (header) {
    const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 4);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- mobile nav ---------- */
  const menuBtn = $(".menu-toggle");
  if (menuBtn) menuBtn.addEventListener("click", () => $(".nav").classList.toggle("open"));

  /* ---------- dropdowns ---------- */
  $$("[data-dropdown]").forEach((dd) => {
    const trigger = $("[data-dropdown-trigger]", dd);
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = !dd.classList.contains("open");
      $$("[data-dropdown].open").forEach((o) => o.classList.remove("open"));
      dd.classList.toggle("open", open);
      trigger.setAttribute("aria-expanded", open);
    });
  });
  document.addEventListener("click", (e) => {
    $$("[data-dropdown].open").forEach((dd) => { if (!dd.contains(e.target)) dd.classList.remove("open"); });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") $$("[data-dropdown].open").forEach((dd) => dd.classList.remove("open"));
  });

  /* ---------- toasts ---------- */
  $$(".toast").forEach((t, i) => {
    const close = () => { t.classList.add("leaving"); setTimeout(() => t.remove(), 350); };
    const btn = $("button", t);
    if (btn) btn.addEventListener("click", close);
    t.style.animationDelay = i * 80 + "ms";
    let timer = setTimeout(close, 5000 + i * 300);
    t.addEventListener("mouseenter", () => { clearTimeout(timer); t.style.setProperty("--paused", 1); });
    t.addEventListener("mouseleave", () => { timer = setTimeout(close, 2000); });
  });

  /* ---------- reveal on scroll (with stagger) ---------- */
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -40px 0px", threshold: 0.05 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
  }

  /* ---------- count-up numbers ---------- */
  const countUp = (el) => {
    const target = parseFloat(el.dataset.count);
    if (isNaN(target) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const dur = 900, start = performance.now();
    const step = (now) => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if ("IntersectionObserver" in window) {
    const cio = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { countUp(en.target); cio.unobserve(en.target); } });
    });
    $$("[data-count]").forEach((el) => cio.observe(el));
  }

  /* ---------- like / bookmark toggles (AJAX with graceful fallback) ---------- */
  $$("form[data-toggle]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = $("button", form);
      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: { "X-CSRFToken": csrf(), "X-Requested-With": "XMLHttpRequest" },
        });
        const data = await res.json();
        btn.classList.toggle("active", data.active);
        btn.classList.remove("pop"); void btn.offsetWidth; btn.classList.add("pop");
        const count = $("[data-count-label]", btn);
        if (count && data.count !== undefined) count.textContent = data.count;
        const label = $("[data-label]", btn);
        if (label) label.textContent = data.active ? label.dataset.on : label.dataset.off;
      } catch (err) {
        form.submit();
      }
    });
  });

  /* ---------- dropzones with upload progress ---------- */
  const fmtSize = (b) => (b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(1) + " MB");

  $$("[data-dropzone]").forEach((zone) => {
    const form = zone.closest("form");
    const input = $("input[type=file]", zone);
    const list = $(".dz-list", zone);
    const bar = form && $(".upload-progress", form);
    let picked = []; // [{file, path}]

    const render = () => {
      if (!list) return;
      list.innerHTML = "";
      picked.slice(0, 60).forEach(({ file, path }) => {
        const row = document.createElement("div");
        row.innerHTML = `<span class="mono truncate"></span><span class="muted nowrap"></span>`;
        row.children[0].textContent = path || file.name;
        row.children[1].textContent = fmtSize(file.size);
        list.appendChild(row);
      });
      if (picked.length > 60) {
        const more = document.createElement("div");
        more.textContent = `…and ${picked.length - 60} more`;
        list.appendChild(more);
      }
      list.classList.toggle("show", picked.length > 0);
      const title = $(".dz-title", zone);
      if (title && picked.length) title.textContent = `${picked.length} file${picked.length > 1 ? "s" : ""} ready`;
    };

    // Any file input in the form (e.g. a separate "choose folder" input) feeds the same list
    const inputs = form ? $$("input[type=file]", form) : [input];
    inputs.forEach((inp) => inp.addEventListener("change", () => {
      picked = Array.from(inp.files).map((f) => ({ file: f, path: f.webkitRelativePath || "" }));
      render();
    }));

    ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove("drag"); }));

    // Walk dropped folders so the vault keeps the folder structure
    const walk = (entry, prefix) => new Promise((resolve) => {
      if (entry.isFile) {
        entry.file((f) => resolve([{ file: f, path: prefix + f.name }]), () => resolve([]));
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        const all = [];
        const readBatch = () => reader.readEntries(async (entries) => {
          if (!entries.length) {
            const nested = await Promise.all(all.map((en) => walk(en, prefix + entry.name + "/")));
            resolve(nested.flat());
          } else { all.push(...entries); readBatch(); }
        }, () => resolve([]));
        readBatch();
      } else resolve([]);
    });

    zone.addEventListener("drop", async (e) => {
      const items = Array.from(e.dataTransfer.items || []);
      if (items.length && items[0].webkitGetAsEntry) {
        const entries = items.map((it) => it.webkitGetAsEntry()).filter(Boolean);
        picked = (await Promise.all(entries.map((en) => walk(en, "")))).flat();
      } else {
        picked = Array.from(e.dataTransfer.files).map((f) => ({ file: f, path: "" }));
      }
      render();
    });

    if (!form) return;
    form.addEventListener("submit", (e) => {
      if (!picked.length) {
        if (!input.files.length) { e.preventDefault(); zone.classList.add("drag"); setTimeout(() => zone.classList.remove("drag"), 500); }
        return;
      }
      e.preventDefault();
      const fd = new FormData();
      $$("input:not([type=file]), textarea, select", form).forEach((el) => { if (el.name) fd.append(el.name, el.value); });
      const field = input.name;
      picked.forEach(({ file, path }) => { fd.append(field, file, file.name); fd.append("paths", path); });

      const xhr = new XMLHttpRequest();
      xhr.open("POST", form.action);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      xhr.setRequestHeader("X-CSRFToken", csrf());
      const submitBtn = $("[type=submit]", form);
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Uploading…"; }
      if (bar) bar.classList.add("show");
      xhr.upload.addEventListener("progress", (ev) => {
        if (!ev.lengthComputable || !bar) return;
        const pct = Math.round((ev.loaded / ev.total) * 100);
        $(".progress > span", bar).style.setProperty("--w", pct + "%");
        $(".pct", bar).textContent = pct < 100 ? pct + "%" : "Processing…";
      });
      xhr.onload = () => {
        try { window.location = JSON.parse(xhr.responseText).redirect || window.location.href; }
        catch (err) { window.location.reload(); }
      };
      xhr.onerror = () => { alert("Upload failed. Check your connection and try again."); window.location.reload(); };
      xhr.send(fd);
    });
  });

  /* ---------- lightbox ---------- */
  const items = $$("[data-lightbox]");
  if (items.length) {
    const lb = document.createElement("div");
    lb.className = "lightbox";
    lb.innerHTML = `
      <button class="lb-btn lb-close" aria-label="Close"><svg class="i"><use href="#i-x"/></svg></button>
      <button class="lb-btn lb-prev" aria-label="Previous"><svg class="i"><use href="#i-chevron-left"/></svg></button>
      <figure style="margin:0"><img alt=""><figcaption class="cap"></figcaption></figure>
      <button class="lb-btn lb-next" aria-label="Next"><svg class="i"><use href="#i-chevron-right"/></svg></button>`;
    document.body.appendChild(lb);
    let idx = 0;
    const show = (i) => {
      idx = (i + items.length) % items.length;
      const img = $("img", lb);
      img.style.transform = "scale(.96)";
      img.src = items[idx].dataset.lightbox;
      img.onload = () => { img.style.transform = ""; };
      $(".cap", lb).textContent = items[idx].dataset.caption || "";
    };
    const close = () => lb.classList.remove("open");
    items.forEach((el, i) => el.addEventListener("click", (e) => { e.preventDefault(); show(i); lb.classList.add("open"); }));
    $(".lb-close", lb).addEventListener("click", close);
    $(".lb-prev", lb).addEventListener("click", () => show(idx - 1));
    $(".lb-next", lb).addEventListener("click", () => show(idx + 1));
    lb.addEventListener("click", (e) => { if (e.target === lb) close(); });
    document.addEventListener("keydown", (e) => {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") show(idx + 1);
      if (e.key === "ArrowLeft") show(idx - 1);
    });
    if (items.length < 2) $$(".lb-prev, .lb-next", lb).forEach((b) => b.remove());
  }

  /* ---------- dialogs ---------- */
  $$("[data-open-dialog]").forEach((btn) =>
    btn.addEventListener("click", () => { const d = document.getElementById(btn.dataset.openDialog); if (d) d.showModal(); })
  );
  $$("dialog [data-close]").forEach((btn) => btn.addEventListener("click", () => btn.closest("dialog").close()));
  $$("dialog.modal").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));

  /* ---------- confirm before destructive actions ---------- */
  $$("[data-confirm]").forEach((el) =>
    el.addEventListener("submit", (e) => { if (!confirm(el.dataset.confirm)) e.preventDefault(); })
  );

  /* ---------- copy to clipboard ---------- */
  $$("[data-copy]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        const old = btn.innerHTML;
        btn.innerHTML = '<svg class="i i-sm"><use href="#i-check"/></svg> Copied';
        setTimeout(() => (btn.innerHTML = old), 1600);
      } catch (e) { /* clipboard blocked */ }
    })
  );

  /* ---------- auto-submit filters ---------- */
  $$("form[data-autosubmit] select").forEach((s) => s.addEventListener("change", () => s.form.submit()));

  /* ---------- textarea: tab inserts spaces in code editor ---------- */
  $$("textarea.editor").forEach((ta) =>
    ta.addEventListener("keydown", (e) => {
      if (e.key !== "Tab") return;
      e.preventDefault();
      const s = ta.selectionStart, end = ta.selectionEnd;
      ta.value = ta.value.slice(0, s) + "    " + ta.value.slice(end);
      ta.selectionStart = ta.selectionEnd = s + 4;
    })
  );

  /* ---------- warn about unsaved edits ---------- */
  $$("form[data-dirty-guard]").forEach((form) => {
    let dirty = false;
    form.addEventListener("input", () => (dirty = true));
    form.addEventListener("submit", () => (dirty = false));
    window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
  });
})();
