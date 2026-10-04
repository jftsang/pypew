// Client-side behaviour for the pew sheet form; configured via data-* attributes.
(function () {
  "use strict";

  const form = document.getElementById("serviceForm");
  if (!form) {
    return;
  }

  const urlTemplate = form.dataset.feastDateUrlTemplate;

  const titleField = document.getElementById("title");
  const titleH3 = document.getElementById("titleH3");
  const primaryFeastField = document.getElementById("primary_feast");
  const secondaryFeastsField = document.getElementById("secondary_feasts");
  const dateField = document.getElementById("date");

  /** Format a Date as YYYY-MM-DD using its local calendar fields. */
  function toISODate(date) {
    const mmdd = [date.getMonth() + 1, date.getDate()].map((n) =>
      String(n).padStart(2, "0")
    );
    return [date.getFullYear()].concat(mmdd).join("-");
  }

  /** Parse a YYYY-MM-DD string as a local date, avoiding UTC parsing. */
  function fromISODate(value) {
    const [y, m, d] = value.split("-").map(Number);
    return new Date(y, m - 1, d);
  }

  function setTitle() {
    const primary = primaryFeastField.selectedOptions[0].text;
    const secondary = Array.from(secondaryFeastsField.selectedOptions).map(
      (opt) => opt.text
    );
    const title = secondary.length
      ? primary + " (" + secondary.join(", ") + ")"
      : primary;

    titleH3.textContent = title;
    titleField.value = title;
  }

  async function updateDateFromPrimaryFeast() {
    const response = await fetch(
      urlTemplate.replace("__slug__", primaryFeastField.value)
    );
    if (!response.ok) {
      return;
    }
    const date = await response.json();
    if (date !== null) {
      dateField.value = date;
    }
  }

  function setDate(date) {
    dateField.value = toISODate(date);
  }

  function shiftDate(days) {
    const date = fromISODate(dateField.value);
    date.setDate(date.getDate() + days);
    setDate(date);
  }

  const today = new Date();
  const sunday = new Date(today);
  sunday.setDate(today.getDate() + ((7 - today.getDay()) % 7));

  const dateButtons = [
    ["prev-week-btn", "7 days earlier", () => shiftDate(-7)],
    ["today-btn", "Set the date to today", () => setDate(today)],
    ["sunday-btn", "Set the date to this Sunday", () => setDate(sunday)],
    ["next-week-btn", "7 days later", () => shiftDate(7)],
  ];

  dateButtons.forEach(([id, tooltip, onClick]) => {
    const btn = document.getElementById(id);
    btn.onclick = onClick;
    btn.onmouseenter = () => dateField.classList.add("bg-warning");
    btn.onmouseleave = () => dateField.classList.remove("bg-warning");
    pypew.addTooltip(btn, tooltip);
  });

  setTitle();
  primaryFeastField.addEventListener("change", setTitle);
  secondaryFeastsField.addEventListener("change", setTitle);

  updateDateFromPrimaryFeast();
  primaryFeastField.addEventListener("change", updateDateFromPrimaryFeast);
})();