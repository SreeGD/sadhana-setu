// Today view — rounds counter + hearing notes capture.

import { todayISO, el, formatTime, formatDate, toast } from "../util.js";
import * as store from "../store.js";

export async function render(root) {
  const date = todayISO();
  const current = store.getRounds(date);
  const count = current?.count || 0;
  const hearing = store.getHearingForDate(date);

  root.innerHTML = "";

  root.appendChild(el("div", { class: "meta-line" }, formatDate(new Date())));

  // Rounds card
  const countSpan = el("div", { class: "count" }, String(count));
  const decBtn = el("button", { "aria-label": "decrease" }, "−");
  const incBtn = el("button", { "aria-label": "increase" }, "+");
  decBtn.addEventListener("click", () => {
    const r = store.decrementRounds(date);
    countSpan.textContent = String(r?.count || 0);
  });
  incBtn.addEventListener("click", () => {
    const r = store.incrementRounds(date);
    countSpan.textContent = String(r.count);
    if (r.count === 16) toast("16 rounds complete — Hare Krishna 🪷");
  });

  const roundsCard = el("div", { class: "view-card" },
    el("h3", {}, "Rounds today"),
    el("div", { class: "rounds-counter" },
      decBtn,
      countSpan,
      incBtn,
    ),
    el("div", { class: "meta-line" },
      el("span", { class: "label" },
        count >= 16 ? "vow complete · 🪷" : `${16 - count} to vow`
      )
    ),
    el("p", { style: "color:var(--muted); font-size:0.85rem; text-align:center; margin:0.3rem 0 0;" },
      "Tap + after each round. The app does not chant for you. It only remembers.")
  );
  root.appendChild(roundsCard);

  // Hearing card
  const sourceInput = el("input", { type: "text", placeholder: "Source (e.g., SB 1.1.1, morning class)" });
  const lineInput = el("textarea", { placeholder: "What you heard. One line is fine — what stayed with you." });
  const addBtn = el("button", { class: "primary" }, "Add note");

  const listUl = el("ul", { class: "entry-list" });

  function renderHearingList() {
    listUl.innerHTML = "";
    const items = store.getHearingForDate(date);
    if (items.length === 0) {
      listUl.appendChild(el("li", { style: "color:var(--muted); font-style:italic;" },
        el("span", { class: "text" }, "No hearing notes today yet.")));
      return;
    }
    for (const h of items) {
      const li = el("li", {},
        el("span", { class: "when" }, formatTime(h.captured_at)),
        el("span", { class: "text" },
          h.source ? el("strong", {}, h.source + ": ") : null,
          h.line
        ),
        el("button", {
          class: "delete",
          title: "Delete",
          onclick: () => {
            store.deleteHearing(h.captured_at);
            renderHearingList();
          },
        }, "✕")
      );
      listUl.appendChild(li);
    }
  }

  addBtn.addEventListener("click", () => {
    const line = lineInput.value.trim();
    if (!line) return;
    store.addHearing(date, line, sourceInput.value.trim());
    sourceInput.value = "";
    lineInput.value = "";
    renderHearingList();
    toast("Note saved");
  });

  renderHearingList();

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Hearing notes"),
    el("label", { class: "field", for: "" }, "Source"),
    sourceInput,
    el("label", { class: "field", for: "" }, "What you heard"),
    lineInput,
    el("div", { style: "margin-top:0.7rem;" }, addBtn),
    el("h4", {}, "Today's entries"),
    listUl,
  ));
}
