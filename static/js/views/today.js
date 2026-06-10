// Today view — capture WHEN 16 rounds were completed + SB/BG quick-checks.
//
// Vow-aware design: japa is binary at the vow level. The data point that
// matters is *when* you finished, not how many you've ticked. Four
// windows + Not yet. Earlier windows color brighter.

import { todayISO, el, formatDate, toast } from "../util.js";
import * as store from "../store.js";

const WINDOWS = [
  { id: "before_8am",  label: "Before 8 AM",  sub: "brāhma-muhūrta window" },
  { id: "before_12pm", label: "Before 12 PM", sub: "morning complete" },
  { id: "before_9pm",  label: "Before 9 PM",  sub: "evening" },
  { id: "before_11pm", label: "Before 11 PM", sub: "before sleep" },
];

export async function render(root) {
  const date = todayISO();
  const current = store.getRounds(date);
  const selected = current?.completion || null;
  const flags = store.getHearingFlags(date);

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" }, formatDate(new Date())));

  // 16-rounds completion card
  const grid = el("div", { class: "completion-grid" });
  for (const w of WINDOWS) {
    const btn = el("button", {
      class: "completion-btn" + (selected === w.id ? " selected" : "") + " win-" + w.id,
    },
      el("div", { class: "completion-tick" }, selected === w.id ? "✓" : ""),
      el("div", { class: "completion-label" }, w.label),
      el("div", { class: "completion-sub" }, w.sub),
    );
    btn.addEventListener("click", () => {
      store.setCompletion(date, w.id);
      toast(`16 rounds · ${w.label} 🪷`);
      render(root);
    });
    grid.appendChild(btn);
  }
  const clearBtn = el("button", {
    class: "completion-btn completion-clear" + (selected === null ? " selected" : ""),
  },
    el("div", { class: "completion-tick" }, selected === null ? "✓" : ""),
    el("div", { class: "completion-label" }, "Not yet"),
    el("div", { class: "completion-sub" }, "japa still ahead"),
  );
  clearBtn.addEventListener("click", () => {
    if (current) store.clearRoundsForDate(date);
    render(root);
  });
  grid.appendChild(clearBtn);

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "16 rounds today"),
    el("p", { style: "color:var(--muted); font-size:0.9rem; margin: 0 0 0.6rem;" },
      "When were the rounds completed? Tap the window that fits."),
    grid,
    selected ? el("div", { class: "meta-line", style: "margin-top:0.6rem;" },
      el("em", {}, `vow complete · `, el("strong", {}, WINDOWS.find(w=>w.id===selected)?.label || ""))
    ) : null,
  ));

  // Quick hearing checks — SB + BG (one tap per day)
  function pill(kind, label, on) {
    const btn = el("button", {
      class: "hearing-pill" + (on ? " on" : ""),
      "data-kind": kind,
    },
      el("span", { class: "hearing-tick" }, on ? "✓" : ""),
      el("span", { class: "hearing-label" }, label),
    );
    btn.addEventListener("click", () => {
      const next = !btn.classList.contains("on");
      store.setHearingFlag(date, kind, next);
      btn.classList.toggle("on", next);
      btn.querySelector(".hearing-tick").textContent = next ? "✓" : "";
      toast(next ? `${label.toUpperCase()} marked` : `${label.toUpperCase()} unmarked`);
    });
    return btn;
  }

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Today's hearing"),
    el("p", { style: "color:var(--muted); font-size:0.9rem; margin: 0 0 0.6rem;" },
      "Optional. Tap once when you've heard SB or BG today."),
    el("div", { class: "hearing-pills" },
      pill("sb", "SB heard", flags.sb),
      pill("bg", "BG heard", flags.bg),
    ),
  ));
}

export const COMPLETION_WINDOWS = WINDOWS;
