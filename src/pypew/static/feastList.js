// Sortable feast list in the sidebar; configured via data-* attributes.
(function () {
  "use strict";

  const root = document.getElementById("feastList");
  if (!root) {
    return;
  }

  const list = root.querySelector("ul");
  const currentFeast = root.dataset.currentFeast || null;
  const urlTemplate = root.dataset.feastUrlTemplate;

  const SORTS = {
    calendar: {
      btnId: "sortFeastsByCalendar",
      url: root.dataset.indexApiUrl,
      tooltip: "Sort by calendar order (Advent–Trinity then specials)",
    },
    name: {
      btnId: "sortFeastsByName",
      url: root.dataset.indexApiUrl,
      tooltip: "Sort alphabetically",
      sort: (a, b) => String(a.name).localeCompare(String(b.name)),
    },
    upcoming: {
      btnId: "sortFeastsByUpcoming",
      url: root.dataset.upcomingApiUrl,
      tooltip: "Show upcoming feasts",
    },
  };

  const sortBtns = Object.keys(SORTS).map((name) => {
    const btn = document.getElementById(SORTS[name].btnId);
    btn.dataset.sort = name;
    return btn;
  });

  function makeLink(feast) {
    const label = document.createElement("small");
    label.textContent = feast.name;

    const link = document.createElement("a");
    link.href = urlTemplate.replace("__slug__", feast.slug);
    link.classList.add(
      "text-decoration-none",
      currentFeast === null || feast.name === currentFeast
        ? "link-info"
        : "link-secondary"
    );
    pypew.addTooltip(link, feast.next, "right");
    link.append(label);
    return link;
  }

  function draw(feasts, activeSort) {
    list.replaceChildren(
      ...feasts.map((feast) => {
        const li = document.createElement("li");
        li.append(makeLink(feast));
        return li;
      })
    );
    pypew.initTooltips(list);

    sortBtns.forEach((btn) => {
      const active = btn.dataset.sort === activeSort;
      btn.classList.toggle("btn-light", active);
      btn.classList.toggle("btn-secondary", !active);
    });
  }

  async function show(sortName) {
    const sort = SORTS[sortName];
    const response = await fetch(sort.url);
    if (!response.ok) {
      return;
    }
    const feasts = await response.json();
    if (sort.sort) {
      feasts.sort(sort.sort);
    }
    draw(feasts, sortName);
  }

  sortBtns.forEach((btn) => {
    pypew.addTooltip(btn, SORTS[btn.dataset.sort].tooltip);
    btn.onclick = () => show(btn.dataset.sort);
  });

  show("upcoming");
})();