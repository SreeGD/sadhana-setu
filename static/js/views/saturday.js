// Saturday Check-in view — observe + set, with dropdown/checkbox pickers
// and an Other affordance for free-text entry.

import { weekQuestions, weeklyFormOptions } from "../content.js";
import { upcomingSaturday, addDays, el, formatDate, toast, collapse } from "../util.js";
import { weekDots, summaryLine } from "../week_summary.js";
import * as store from "../store.js";
import { t } from "../i18n.js";

const OTHER = "__OTHER__";

// ----- pickers -----

function singleSelect(name, options, current, otherText) {
  // Returns { wrapper, get() } for a single-select dropdown + Other text.
  const opts = [
    el("option", { value: "" }, t("saturday.choose")),
    ...options.map(o => el("option", { value: o }, o)),
    el("option", { value: OTHER }, t("saturday.other")),
  ];
  const sel = el("select", { id: name }, ...opts);
  const otherInp = el("input", {
    type: "text",
    placeholder: t("saturday.other_placeholder"),
    style: "margin-top: 0.5rem;",
  });
  // Initialize selection from current value
  let initOther = "";
  if (current) {
    if (options.includes(current)) {
      sel.value = current;
      otherInp.style.display = "none";
    } else {
      sel.value = OTHER;
      initOther = current;
      otherInp.value = current;
    }
  } else {
    otherInp.style.display = "none";
  }
  sel.addEventListener("change", () => {
    otherInp.style.display = sel.value === OTHER ? "block" : "none";
    if (sel.value === OTHER) otherInp.focus();
  });
  const wrap = el("div", { class: "field-wrap" }, sel, otherInp);
  return {
    wrapper: wrap,
    get() {
      if (sel.value === OTHER) return otherInp.value.trim();
      if (!sel.value) return "";
      return sel.value;
    },
  };
}

function multiSelect(name, options, current) {
  // Returns { wrapper, get() }. `current` is the list of strings that were
  // selected before (may contain free-text Other values).
  const cur = new Set(current || []);
  const boxes = options.map(o => {
    const id = `${name}-${options.indexOf(o)}`;
    const cb = el("input", { type: "checkbox", id, value: o });
    if (cur.has(o)) cb.checked = true;
    return { o, cb, label: el("label", { for: id, class: "checkbox-label" }, cb, " ", o) };
  });
  // Collect free-text custom values (anything in `current` not in `options`)
  const customs = (current || []).filter(v => !options.includes(v));
  const otherTa = el("textarea", {
    rows: 2,
    placeholder: t("saturday.other_lines"),
    style: "margin-top: 0.4rem;",
  });
  if (customs.length) otherTa.value = customs.join("\n");
  const wrap = el("div", { class: "field-wrap checkbox-grid" },
    ...boxes.map(b => b.label),
    el("div", { class: "checkbox-other" },
      el("label", { class: "field-sub" }, t("saturday.other_free")),
      otherTa,
    ),
  );
  return {
    wrapper: wrap,
    get() {
      const picked = boxes.filter(b => b.cb.checked).map(b => b.o);
      const others = otherTa.value.split("\n").map(s => s.trim()).filter(Boolean);
      return [...picked, ...others];
    },
  };
}

// ----- main render -----

export async function render(root) {
  const sat = upcomingSaturday();   // Saturday of the calendar week containing today
  const satISO = sat.toISOString().slice(0, 10);
  const weekStart = addDays(sat, -6);
  const today = new Date();
  const isSaturday = today.getDay() === 6;

  const existing = store.getCheckin(satISO);
  const [questions, opts] = await Promise.all([weekQuestions(3), weeklyFormOptions()]);

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" },
    t("saturday.week_of", { start: formatDate(weekStart), end: formatDate(sat) })
  ));

  if (!isSaturday) {
    root.appendChild(el("div", { class: "view-card", style: "background:#FFF5E0;" },
      el("p", { style: "margin:0; color:var(--ink-soft);" },
        t("saturday.not_saturday_short", { weekday: today.toLocaleDateString(undefined, { weekday: "long" }) })),
    ));
  }

  // Week japa review (above Half 1)
  const sLine = summaryLine(sat);
  root.appendChild(el("div", { class: "view-card week-review-card" },
    el("h3", {}, t("saturday.japa_review")),
    weekDots(sat),
    el("p", { style: "margin: 0.6rem 0 0.2rem; color: var(--ink-soft); font-weight: 600;" },
      sLine.primary),
    el("p", { style: "margin: 0; color: var(--muted); font-size: 0.88rem; font-style: italic;" },
      sLine.distribution),
  ));

  // Half 1 — Observe
  const qBlocks = questions.map((q, i) => el("div", { style: "margin-bottom:0.9rem;" },
    el("p", { style: "color:var(--ink-soft); font-weight:600; margin:0.4rem 0 0.2rem;" }, `Q${i + 1}.`),
    el("p", { style: "margin:0 0 0.3rem;" }, q.question),
    q.routes_through ? el("p", { style: "color:var(--muted); font-style:italic; font-size:0.85rem; margin:0 0 0.3rem;" }, t("saturday.routes_through", { route: q.routes_through })) : null,
    el("textarea", {
      id: `q${i}`,
      placeholder: t("saturday.answer_placeholder"),
      rows: 2,
    }, (existing?.answers || [])[i] || ""),
  ));

  root.appendChild(collapse("sat_half1",
    el("summary", { class: "view-card-summary" },
      el("h3", {}, t("saturday.half1")),
    ),
    el("h4", {}, t("saturday.questions")),
    ...qBlocks,
  ));

  // Half 2 — Set
  const tone = singleSelect("tone", opts.tone || [], existing?.tone || "");
  const bhava = singleSelect("bhava", opts.bhava || [], existing?.mood_bhava || "");
  const practices = multiSelect("practices", opts.practices || [], existing?.practices || []);
  const tools = multiSelect("tools", opts.tools || [], existing?.tools_needed || []);
  const priorities = multiSelect("priorities", opts.priorities || [], existing?.priorities || []);

  root.appendChild(collapse("sat_half2",
    el("summary", { class: "view-card-summary" },
      el("h3", {}, t("saturday.half2")),
    ),
    el("label", { class: "field" }, t("saturday.tone_short")),
    tone.wrapper,
    el("label", { class: "field" }, t("saturday.bhava_short")),
    bhava.wrapper,
    el("label", { class: "field" }, t("saturday.practices_short")),
    practices.wrapper,
    el("label", { class: "field" }, t("saturday.tools_short")),
    tools.wrapper,
    el("label", { class: "field" }, t("saturday.priorities_short")),
    priorities.wrapper,
  ));

  const saveBtn = el("button", { class: "primary" }, existing ? t("saturday.update") : t("saturday.save"));
  saveBtn.addEventListener("click", () => {
    const answers = questions.map((_, i) => document.getElementById(`q${i}`).value.trim());
    const payload = {
      tone: tone.get(),
      mood_bhava: bhava.get(),
      practices: practices.get(),
      tools_needed: tools.get(),
      priorities: priorities.get(),
      answers,
      questions: questions.map(q => q.question),
    };
    store.saveCheckin(satISO, payload);
    toast(t("saturday.saved", { date: satISO }));
  });
  root.appendChild(el("div", { style: "text-align:center; margin: 1rem 0;" }, saveBtn));

  if (existing) {
    root.appendChild(el("p", { class: "meta-line" }, `Last saved: ${new Date(existing.submitted_at).toLocaleString()}`));
  }
}
