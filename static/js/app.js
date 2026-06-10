// Sadhana Setu — static app entry. View routing + footer summary refresh.

import * as prejapa from "./views/prejapa.js";
import * as today from "./views/today.js";
import * as this_week from "./views/this_week.js";
import * as saturday from "./views/saturday.js";
import * as backup from "./views/backup.js";
import { storageSummary } from "./store.js";

// ---------- font size ----------
const FONT_SIZE_KEY = "sadhana_setu_font_size";
const SIZES = [13, 15, 17, 19, 21];

function applyFontSize(px) {
  document.documentElement.style.fontSize = px + "px";
}
function currentSize() {
  const v = parseInt(localStorage.getItem(FONT_SIZE_KEY), 10);
  return SIZES.includes(v) ? v : 17;
}
function nudgeFont(direction) {
  const cur = currentSize();
  let idx = SIZES.indexOf(cur);
  if (idx === -1) idx = SIZES.indexOf(17);
  const next = SIZES[Math.max(0, Math.min(SIZES.length - 1, idx + direction))];
  localStorage.setItem(FONT_SIZE_KEY, String(next));
  applyFontSize(next);
}
applyFontSize(currentSize());
document.getElementById("font-smaller")?.addEventListener("click", () => nudgeFont(-1));
document.getElementById("font-bigger")?.addEventListener("click", () => nudgeFont(+1));
document.getElementById("font-reset")?.addEventListener("click", () => {
  localStorage.setItem(FONT_SIZE_KEY, "17");
  applyFontSize(17);
});

const views = {
  prejapa: prejapa.render,
  today: today.render,
  this_week: this_week.render,
  saturday: saturday.render,
  backup: backup.render,
};

const root = document.getElementById("root");

function refreshFooter() {
  const s = storageSummary();
  document.getElementById("storage-summary").textContent =
    `${s.rounds} days · ${s.hearing} notes · ${s.checkins} check-ins on this device`;
}

async function show(name) {
  for (const btn of document.querySelectorAll("[data-view]")) {
    btn.classList.toggle("active", btn.dataset.view === name);
  }
  try {
    await views[name](root);
  } catch (e) {
    root.innerHTML = `<div class="view-card" style="border-left-color:#8B0000;">
      <h3 style="color:#8B0000;">Error rendering view</h3>
      <pre style="white-space:pre-wrap;">${(e?.stack || e?.message || String(e))}</pre>
    </div>`;
  }
  refreshFooter();
  window.scrollTo(0, 0);
}

for (const btn of document.querySelectorAll("[data-view]")) {
  btn.addEventListener("click", () => show(btn.dataset.view));
}

// Boot
window.addEventListener("load", () => show("prejapa"));
