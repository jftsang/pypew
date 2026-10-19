(function () {
  "use strict";

  const editor = document.getElementById("serviceItemsEditor");
  if (!editor) {
    return;
  }

  const form = document.getElementById("serviceForm");
  const defaultItemsUrl = form.dataset.defaultItemsUrl;
  const feastField = document.getElementById("primary_feast");
  const secondaryField = document.getElementById("secondary_feasts");
  const hymnSelects = ["introit_hymn", "offertory_hymn", "recessional_hymn"];

  let items = [];

  function emptyItem(type) {
    switch (type) {
      case "misc":
        return { type: "misc", title: "", paragraphs: [], subtitle: null };
      case "collect":
        return { type: "collect", collects: [] };
      case "proper":
        return {
          type: "proper",
          proper_type: "introit",
          title: "",
          paragraphs: [],
          subtitle: null,
        };
      case "reading":
        return {
          type: "reading",
          reading_type: "epistle",
          title: "",
          paragraphs: [],
          subtitle: null,
        };
      case "hymn":
        return { type: "hymn", title: "", music: null };
      case "anthem":
        return {
          type: "anthem",
          title: "Anthem",
          name: null,
          composer: null,
          lyrics: null,
          translation: null,
        };
      default:
        return { type: "misc", title: "", paragraphs: [], subtitle: null };
    }
  }

  function card(item, index) {
    const el = document.createElement("div");
    el.className = "card mb-1";
    el.dataset.index = String(index);

    const header = document.createElement("div");
    header.className =
      "card-header d-flex justify-content-between align-items-center";

    const titleInput = document.createElement("input");
    titleInput.type = "text";
    titleInput.className = "form-control form-control-sm fw-bold";
    titleInput.value = item.title || "";
    titleInput.placeholder = typeLabel(item.type);
    titleInput.style.width = "12rem";
    titleInput.addEventListener("input", function () {
      item.title = titleInput.value;
    });
    header.appendChild(titleInput);

    const controls = document.createElement("div");
    const up = btn("↑", "Move up", function () {
      if (index > 0) {
        const tmp = items[index - 1];
        items[index - 1] = items[index];
        items[index] = tmp;
        render();
      }
    });
    const down = btn("↓", "Move down", function () {
      if (index < items.length - 1) {
        const tmp = items[index + 1];
        items[index + 1] = items[index];
        items[index] = tmp;
        render();
      }
    });
    const addBelow = btn("+", "Add item below", function () {
      items.splice(index + 1, 0, emptyItem("misc"));
      render();
    });
    const remove = btn("×", "Remove", function () {
      items.splice(index, 1);
      render();
    });
    controls.appendChild(up);
    controls.appendChild(down);
    controls.appendChild(addBelow);
    controls.appendChild(remove);
    header.appendChild(controls);
    el.appendChild(header);

    const body = document.createElement("div");
    body.className = "card-body";
    body.appendChild(editorFor(item, index));
    el.appendChild(body);

    return el;
  }

  function btn(text, title, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn btn-sm btn-outline-secondary ms-1";
    b.textContent = text;
    b.title = title;
    b.onclick = onClick;
    return b;
  }

  function typeLabel(t) {
    return {
      misc: "Miscellaneous",
      collect: "Collect",
      proper: "Proper",
      reading: "Reading",
      hymn: "Hymn",
      anthem: "Anthem",
    }[t] || t;
  }

  function editorFor(item, index) {
    const frag = document.createDocumentFragment();

    function field(label, input) {
      const row = document.createElement("div");
      row.className = "mb-1";
      const lab = document.createElement("label");
      lab.className = "form-label small mb-0";
      lab.textContent = label;
      row.appendChild(lab);
      row.appendChild(input);
      return row;
    }

    function textInput(value, onChange, placeholder) {
      const inp = document.createElement("input");
      inp.type = "text";
      inp.className = "form-control form-control-sm";
      inp.value = value == null ? "" : value;
      if (placeholder) {
        inp.placeholder = placeholder;
      }
      inp.addEventListener("input", function () {
        onChange(inp.value);
      });
      return inp;
    }

    function textarea(value, onChange, placeholder) {
      const ta = document.createElement("textarea");
      ta.className = "form-control form-control-sm";
      ta.rows = 3;
      ta.style.minHeight = "4.5em";
      ta.style.resize = "vertical";
      ta.value = (value || []).join("\n");
      // Grow to fit the content, but never below 3 rows.
      function grow() {
        ta.style.height = "auto";
        ta.style.height = Math.max(ta.scrollHeight, 3 * 16) + "px";
      }
      ta.addEventListener("input", grow);
      setTimeout(grow, 0);
      if (placeholder) {
        ta.placeholder = placeholder;
      }
      ta.addEventListener("input", function () {
        onChange(ta.value.split("\n").filter(function (x) {
          return x.length > 0;
        }));
      });
      return ta;
    }

    function select(options, value, onChange) {
      const sel = document.createElement("select");
      sel.className = "form-select form-select-sm";
      options.forEach(function (opt) {
        const o = document.createElement("option");
        o.value = opt.value;
        o.textContent = opt.label;
        if (opt.value === value) {
          o.selected = true;
        }
        sel.appendChild(o);
      });
      sel.addEventListener("change", function () {
        onChange(sel.value);
      });
      return sel;
    }

    function combobox(options, value, onChange) {
      const inp = document.createElement("input");
      inp.type = "text";
      inp.className = "form-control form-control-sm";
      inp.value = value == null ? "" : value;
      inp.setAttribute("list", "hymnList");
      let dl = document.getElementById("hymnList");
      if (!dl) {
        dl = document.createElement("datalist");
        dl.id = "hymnList";
        document.body.appendChild(dl);
      }
      dl.innerHTML = "";
      options.forEach(function (opt) {
        if (!opt.value) return;
        const o = document.createElement("option");
        o.value = opt.value;
        o.textContent = opt.label;
        dl.appendChild(o);
      });
      inp.addEventListener("input", function () {
        onChange(inp.value);
      });
      return inp;
    }

    switch (item.type) {
      case "misc":
        frag.appendChild(field("Subtitle", textInput(item.subtitle, function (v) {
          item.subtitle = v || null;
        }, "Subtitle")));
        frag.appendChild(field("Paragraphs", textarea(item.paragraphs, function (v) {
          item.paragraphs = v;
        }, "One paragraph per line")));
        break;
      case "collect":
        frag.appendChild(field("Collects", textarea(item.collects, function (v) {
          item.collects = v;
        }, "One collect per line")));
        break;
      case "proper":
        frag.appendChild(
          field(
            "Proper type",
            select(
              [
                { value: "introit", label: "Introit" },
                { value: "gradual", label: "Gradual" },
                { value: "alleluia", label: "Alleluia" },
                { value: "tract", label: "Tract" },
                { value: "offertory", label: "Offertory" },
                { value: "communion", label: "Communion" },
                { value: "gat", label: "Gradual & Tract" },
              ],
              item.proper_type,
              function (v) {
                item.proper_type = v;
              }
            )
          )
        );
        frag.appendChild(field("Subtitle", textInput(item.subtitle, function (v) {
          item.subtitle = v || null;
        }, "Subtitle")));
        frag.appendChild(field("Paragraphs", textarea(item.paragraphs, function (v) {
          item.paragraphs = v;
        }, "One paragraph per line")));
        break;
      case "reading":
        frag.appendChild(
          field(
            "Reading type",
            select(
              [
                { value: "ot", label: "Old Testament" },
                { value: "epistle", label: "Epistle" },
                { value: "gospel", label: "Gospel" },
              ],
              item.reading_type,
              function (v) {
                item.reading_type = v;
              }
            )
          )
        );
        frag.appendChild(field("Reference", textInput(item.subtitle, function (v) {
          item.subtitle = v || null;
        })));
        frag.appendChild(field("Paragraphs", textarea(item.paragraphs, function (v) {
          item.paragraphs = v;
        }, "One paragraph per line")));
        break;
      case "hymn":
        frag.appendChild(
          field(
            "Hymn",
            combobox(
              hymnOptions(),
              item.music ? item.music.ref : "",
              function (v) {
                const hymn = hymnByRef(v);
                item.music = hymn || (v ? { title: v, category: "Hymn", ref: v } : null);
              }
            )
          )
        );
        break;
      case "anthem":
        frag.appendChild(field("Anthem name", textInput(item.name, function (v) {
          item.name = v || null;
        }, "Anthem name")));
        frag.appendChild(field("Composer", textInput(item.composer, function (v) {
          item.composer = v || null;
        }, "Composer")));
        frag.appendChild(field("Lyrics", textarea([item.lyrics].filter(Boolean), function (v) {
          item.lyrics = v.length ? v.join("\n") : null;
        }, "Lyrics")));
        frag.appendChild(field("Translation", textarea([item.translation].filter(Boolean), function (v) {
          item.translation = v.length ? v.join("\n") : null;
        }, "Translation")));
        break;
    }
    return frag;
  }

  let hymnList = [];
  function hymnOptions() {
    if (!hymnList.length) {
      hymnList = JSON.parse(form.dataset.hymns || "[]");
    }
    return [{ value: "", label: "None" }].concat(
      hymnList.map(function (h) {
        return { value: h.ref, label: h.ref + " - " + h.title };
      })
    );
  }

  function hymnByRef(ref) {
    if (!ref) {
      return null;
    }
    if (!hymnList.length) {
      hymnList = JSON.parse(form.dataset.hymns || "[]");
    }
    return hymnList.find(function (h) {
      return h.ref === ref;
    }) || null;
  }

  function render() {
    editor.innerHTML = "";
    const addBar = document.createElement("div");
    addBar.className = "mb-2";
    const sel = document.createElement("select");
    sel.className = "form-select form-select-sm d-inline-block w-auto me-2";
    sel.id = "addItemSelect";
    [
      { value: "", label: "Add item…" },
      { value: "collect", label: "Collect" },
      { value: "proper", label: "Proper" },
      { value: "reading", label: "Reading" },
      { value: "hymn", label: "Hymn" },
      { value: "anthem", label: "Anthem" },
      { value: "misc", label: "Miscellaneous" },
    ].forEach(function (opt) {
      const o = document.createElement("option");
      o.value = opt.value;
      o.textContent = opt.label;
      sel.appendChild(o);
    });
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "btn btn-sm btn-outline-primary";
    addBtn.textContent = "Add";
    addBtn.onclick = function () {
      if (sel.value) {
        items.push(emptyItem(sel.value));
        sel.value = "";
        render();
      }
    };
    addBar.appendChild(sel);
    addBar.appendChild(addBtn);
    editor.appendChild(addBar);

    items.forEach(function (item, i) {
      editor.appendChild(card(item, i));
    });
  }

  // Load initial items from the server-rendered service, if any.
  let initial = [];
  try {
    const raw = form.dataset.serviceJson;
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && Array.isArray(parsed.items)) {
        initial = parsed.items;
      }
    }
  } catch (e) {
    initial = [];
  }

  if (initial.length) {
    items = initial;
  } else {
    // Fetch defaults from the server.
    fetchDefaults();
  }

  function fetchDefaults() {
    const payload = {
      title: document.getElementById("title").value,
      date: document.getElementById("date").value,
      time: document.getElementById("time").value,
      primary_feast: document.getElementById("primary_feast").value,
      secondary_feasts: Array.from(
        document.getElementById("secondary_feasts").selectedOptions
      ).map(function (o) {
        return o.value;
      }),
      celebrant: document.getElementById("celebrant").value,
      preacher: document.getElementById("preacher").value,
      introit_hymn: "",
      offertory_hymn: "",
      recessional_hymn: "",
      anthem_group: { title: "", composer: "", lyrics: "", translation: "" },
    };
    fetch(defaultItemsUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        items = data.items || [];
        render();
      })
      .catch(function () {
        items = [];
        render();
      });
  }

  const regenBtn = document.getElementById("regenerateItemsBtn");
  if (regenBtn) {
    regenBtn.onclick = fetchDefaults;
  }

  render();

  // Intercept form submission and POST JSON instead.
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const payload = {
      title: document.getElementById("title").value,
      date: document.getElementById("date").value,
      time: document.getElementById("time").value,
      primary_feast: document.getElementById("primary_feast").value,
      secondary_feasts: Array.from(
        document.getElementById("secondary_feasts").selectedOptions
      ).map(function (o) {
        return o.value;
      }),
      celebrant: document.getElementById("celebrant").value,
      preacher: document.getElementById("preacher").value,
      introit_hymn: "",
      offertory_hymn: "",
      recessional_hymn: "",
      anthem_group: { title: "", composer: "", lyrics: "", translation: "" },
      service_type: "Sung Mass",
      items: items,
    };
    fetch(form.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        return r.text();
      })
      .then(function (html) {
        document.open();
        document.write(html);
        document.close();
      });
  });
})();
