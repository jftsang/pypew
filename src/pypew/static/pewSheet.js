// Pew sheet page buttons; URLs come from data-* attributes.
(function () {
  "use strict";

  const copyBtn = document.getElementById("copyUrlBtn");
  if (copyBtn) {
    copyBtn.onclick = () => {
      navigator.clipboard
        .writeText(window.location.href)
        .then(() => pypew.toast("Link copied to clipboard.", "success"));
    };
  }

  const docxBtn = document.getElementById("makeDocxBtn");
  if (docxBtn) {
    docxBtn.href += window.location.search;
  }

  const clearHistLink = document.getElementById("clearHistLink");
  if (clearHistLink) {
    clearHistLink.onclick = (event) => {
      event.preventDefault();
      if (!confirm("Clear pew sheet history? This cannot be undone!")) {
        return;
      }
      fetch(clearHistLink.dataset.clearHistoryUrl, { method: "delete" }).then(
        (response) => {
          if (!response.ok) {
            return;
          }
          document
            .querySelectorAll("li.previous-service")
            .forEach((li) => li.remove());
          pypew.toast("History cleared.", "success");
        }
      );
    };
  }
})();