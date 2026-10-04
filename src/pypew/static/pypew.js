// Shared frontend helpers, loaded by every page via base.html.
(function () {
  "use strict";

  /**
   * Mark an element as needing a Bootstrap tooltip, using the tooltip text as
   * its title. Pair with initTooltips() to actually show it.
   */
  function addTooltip(elem, text, placement) {
    elem.dataset.bsToggle = "tooltip";
    elem.dataset.bsPlacement = placement || "top";
    elem.title = text;
  }

  /**
   * Show every tooltip within `root` that addTooltip() marked. Safe to call
   * repeatedly; already-initialised elements are left alone.
   */
  function initTooltips(root) {
    const scope = root || document;
    scope
      .querySelectorAll('[data-bs-toggle="tooltip"]')
      .forEach(function (elem) {
        if (!bootstrap.Tooltip.getInstance(elem)) {
          new bootstrap.Tooltip(elem);
        }
      });
  }

  /** Convenience wrapper around the vendored notify.js toast library. */
  function toast(message, color) {
    notify({ message: message, color: color || "default", timeout: 2000 });
  }

  /** Mark the navbar link matching the current URL as active. */
  function initNavbar() {
    document.querySelectorAll(".navbar-nav .nav-link").forEach(function (link) {
      if (link.href === window.location.href) {
        link.classList.add("active");
      }
    });
  }

  /** Wire every .js-print button to the browser print dialog. */
  function initPrintButtons(root) {
    const scope = root || document;
    scope.querySelectorAll(".js-print").forEach(function (btn) {
      btn.onclick = function () {
        window.print();
      };
    });
  }

  function init() {
    initNavbar();
    initTooltips();
    initPrintButtons();
  }

  window.pypew = {
    addTooltip: addTooltip,
    initPrintButtons: initPrintButtons,
    initTooltips: initTooltips,
    toast: toast,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();