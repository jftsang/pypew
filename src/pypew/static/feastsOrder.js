// Drag-and-drop reordering of the feast list; the resulting order is
// written into a hidden field as JSON when the form is submitted.
(function () {
  "use strict";

  const list = document.getElementById("feastOrderList");
  if (!list) {
    return;
  }

  const input = document.getElementById("feastOrderInput");
  let dragged = null;

  function updateInput() {
    const slugs = Array.from(
      list.querySelectorAll("li[data-slug]")
    ).map((item) => item.dataset.slug);
    input.value = JSON.stringify(slugs);
  }

  list.addEventListener("dragstart", (event) => {
    const item = event.target.closest("li[data-slug]");
    if (!item) {
      return;
    }
    dragged = item;
    item.classList.add("feast-dragging");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", item.dataset.slug);
  });

  list.addEventListener("dragover", (event) => {
    if (!dragged) {
      return;
    }
    event.preventDefault();
    const item = event.target.closest("li[data-slug]");
    if (!item || item === dragged) {
      return;
    }
    const rect = item.getBoundingClientRect();
    const before = event.clientY < rect.top + rect.height / 2;
    list.insertBefore(dragged, before ? item : item.nextSibling);
  });

  list.addEventListener("drop", (event) => {
    if (dragged) {
      event.preventDefault();
    }
  });

  list.addEventListener("dragend", () => {
    if (dragged) {
      dragged.classList.remove("feast-dragging");
    }
    dragged = null;
    updateInput();
  });
})();
