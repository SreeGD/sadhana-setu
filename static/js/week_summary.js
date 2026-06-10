// Shared week-summary helpers used by This Week and Saturday views.

import { el, addDays } from "./util.js";
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
    const iso = d.toISOString().slice(0, 10);
    const r = store.getRounds(iso);
    const count = r?.count || 0;
    const completion = r?.completion;
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
    grid.appendChild(el("div", { class: `day ${cls}` },
      el("div", { class: "label" }, d.toLocaleDateString(undefined, { weekday: "short" })),
      el("div", { class: "count" }, badge),
      timeLabel ? el("div", { class: "time-label" }, timeLabel) : null,
    ));
  }
  return grid;
}

export function weekJapaSummary(saturdayDate) {
  const days = [];
  for (let i = 6; i >= 0; i--) days.push(addDays(saturdayDate, -i));
  const rounds = days.map(d => store.getRounds(d.toISOString().slice(0, 10)));
  let completedDays = 0;
  let hearingCount = 0;
  const windows = { before_8am: 0, before_12pm: 0, before_9pm: 0, before_11pm: 0 };
  for (let i = 0; i < days.length; i++) {
    const r = rounds[i];
    if (r) {
      if ((r.count || 0) >= 16) completedDays++;
      if (r.completion && windows[r.completion] !== undefined) windows[r.completion]++;
    }
    hearingCount += store.getHearingForDate(days[i].toISOString().slice(0, 10)).length;
  }
  return { completedDays, hearingCount, windows };
}

export function summaryLine(saturdayDate) {
  const s = weekJapaSummary(saturdayDate);
  const dist = Object.entries(s.windows)
    .filter(([, n]) => n > 0)
    .map(([w, n]) => `${WINDOW_LABEL[w]}: ${n}`)
    .join(" · ");
  return {
    primary: `${s.completedDays}/7 days at vow · ${s.hearingCount} hearing notes`,
    distribution: dist || "no completion windows recorded yet",
    ...s,
  };
}
