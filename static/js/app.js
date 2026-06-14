/* Veridex front-end interactions. Vanilla JS, no dependencies.
   Everything degrades gracefully and respects reduced-motion. */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- Mobile drawer ---- */
  var drawer = document.querySelector("[data-drawer]");
  if (drawer) {
    function setDrawer(open) {
      drawer.setAttribute("data-open", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    }
    document.querySelectorAll("[data-drawer-open]").forEach(function (b) {
      b.addEventListener("click", function () { setDrawer(true); });
    });
    document.querySelectorAll("[data-drawer-close]").forEach(function (b) {
      b.addEventListener("click", function () { setDrawer(false); });
    });
    drawer.addEventListener("click", function (e) {
      if (e.target === drawer) setDrawer(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setDrawer(false);
    });
  }

  /* ---- Scroll reveal ---- */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.14, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---- Count-up stats ---- */
  function countUp(el) {
    var target = el.getAttribute("data-count");
    var suffix = el.getAttribute("data-suffix") || "";
    var num = parseFloat(target);
    if (isNaN(num) || reduceMotion) { el.textContent = target + suffix; return; }
    var start = performance.now(), dur = 1200, decimals = (target.split(".")[1] || "").length;
    function tick(now) {
      var p = Math.min((now - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (num * eased).toFixed(decimals) + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target + suffix;
    }
    requestAnimationFrame(tick);
  }
  var counters = document.querySelectorAll("[data-count]");
  if (counters.length && "IntersectionObserver" in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { countUp(en.target); cio.unobserve(en.target); }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(countUp);
  }

  /* ---- IMEI input: group into 4s, digits only, live validity ---- */
  var imei = document.querySelector(".imei-input");
  if (imei) {
    imei.addEventListener("input", function () {
      var digits = imei.value.replace(/\D/g, "").slice(0, 17);
      var grouped = digits.replace(/(.{4})/g, "$1 ").trim();
      imei.value = grouped;
      imei.style.borderColor = digits.length >= 15 ? "var(--brand)" : "";
    });
  }

  /* ---- Service selector (place-order) ---- */
  var radios = document.querySelectorAll('.svc-option input[type="radio"]');
  function syncSelected() {
    document.querySelectorAll(".svc-option").forEach(function (opt) {
      var input = opt.querySelector("input");
      opt.classList.toggle("is-selected", input.checked);
    });
    var checked = document.querySelector('.svc-option input:checked');
    var totalEl = document.querySelector("[data-total]");
    if (checked && totalEl) {
      totalEl.textContent = totalEl.getAttribute("data-prefix") + (checked.getAttribute("data-price") || "");
    }
  }
  radios.forEach(function (r) { r.addEventListener("change", syncSelected); });
  if (radios.length) syncSelected();

  /* ---- Submit → show checking state ---- */
  var form = document.querySelector("[data-verify-form]");
  if (form) {
    form.addEventListener("submit", function () {
      var overlay = document.querySelector(".checking");
      var fields = document.querySelector("[data-form-fields]");
      if (overlay && fields) { overlay.setAttribute("data-on", "true"); fields.style.display = "none"; }
      var btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
    });
  }
})();
