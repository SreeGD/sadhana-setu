// Shared week-summary helpers used by This Week and Saturday views.

import { el, addDays, todayISO } from "./util.js";
import * as store from "./store.js";

const WINDOW_LABEL = {
  before_8am:  "Before 8 AM",
  before_12pm: "Before 12 PM",
  before_9pm:  "Before 9 PM",
  before_11pm: "Before 11 PM",
};

// Short labels shown in the week-dot cell so you can read the time at a glance.
const WINDOW_SHORT = {
  before_8am:  "by 8 am",
  before_12pm: "by noon",
  before_9pm:  "by 9 pm",
  before_11pm: "by 11 pm",
};

export function weekDots(saturdayDate) {
  const days = [];
  for (let i = 6; i >= 0; i--) days.push(addDays(saturdayDate, -i));
  const grid = el("div", { class: "week-dots" });
  for (const d of days) {
    const iso = todayISO(d);
    const r = store.getRounds(iso);
    const count = r?.count || 0;
    const completion = r?.completion;
    const flags = store.getHearingFlags(iso);
    const sankalpa = store.getSankalpa(iso);
    let cls = "empty";
    let badge = "—";
    let timeLabel = "";
    if (completion) {
      cls = "win-" + completion;
      badge = "🪷";
      timeLabel = WINDOW_SHORT[completion] || "";
    } else if (count >= 16) {
      cls = "complete";
      badge = String(count);
    } else if (count > 0) {
      cls = "partial";
      badge = String(count);
    }
    const flagRow = (flags.sb || flags.bg || sankalpa) ? el("div", { class: "flag-row" },
      sankalpa ? el("span", { class: "flag-badge sk", title: "Saṅkalpa made" }, "S") : null,
      flags.sb ? el("span", { class: "flag-badge sb" }, "SB") : null,
      flags.bg ? el("span", { class: "flag-badge bg" }, "BG") : null,
    ) : null;
    grid.appendChild(el("div", { class: `day ${cls}` },
      el("div", { class: "label" }, d.toLocaleDateString(undefined, { weekday: "short" })),
      el("div", { class: "count" }, badge),
      timeLabel ? el("div", { class: "time-label" }, timeLabel) : null,
      flagRow,
    ));
  }
  return grid;
}

export function weekJapaSummary(saturdayDate) {
  const days = [];
  for (let i = 6; i >= 0; i--) days.push(addDays(saturdayDate, -i));
  const rounds = days.map(d => store.getRounds(todayISO(d)));
  let completedDays = 0;
  let sbDays = 0;
  let bgDays = 0;
  let sankalpaDays = 0;
  const windows = { before_8am: 0, before_12pm: 0, before_9pm: 0, before_11pm: 0 };
  for (let i = 0; i < days.length; i++) {
    const iso = todayISO(days[i]);
    const r = rounds[i];
    if (r) {
      if ((r.count || 0) >= 16) completedDays++;
      if (r.completion && windows[r.completion] !== undefined) windows[r.completion]++;
    }
    const f = store.getHearingFlags(iso);
    if (f.sb) sbDays++;
    if (f.bg) bgDays++;
    if (store.getSankalpa(iso)) sankalpaDays++;
  }
  return { completedDays, windows, sbDays, bgDays, sankalpaDays };
}

export function summaryLine(saturdayDate) {
  const s = weekJapaSummary(saturdayDate);
  const dist = Object.entries(s.windows)
    .filter(([, n]) => n > 0)
    .map(([w, n]) => `${WINDOW_LABEL[w]}: ${n}`)
    .join(" · ");
  return {
    primary: `${s.completedDays}/7 at vow · saṅkalpa ${s.sankalpaDays}/7 · SB ${s.sbDays}/7 · BG ${s.bgDays}/7`,
    distribution: dist || "no completion windows recorded yet",
    ...s,
  };
}
