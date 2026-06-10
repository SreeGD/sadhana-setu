// Date helpers + small DOM utilities.

export function todayISO(d = new Date()) {
  return d.getFullYear() + "-"
       + String(d.getMonth() + 1).padStart(2, "0") + "-"
       + String(d.getDate()).padStart(2, "0");
}

export function dayOfYear(d = new Date()) {
  const start = new Date(d.getFullYear(), 0, 0);
  const diff = (d - start) + (start.getTimezoneOffset() - d.getTimezoneOffset()) * 60 * 1000;
  return Math.floor(diff / 86400000);
}

export function isoWeek(d = new Date()) {
  const target = new Date(d.valueOf());
  const dayNr = (d.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = target.valueOf();
  target.setMonth(0, 1);
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
  }
  return 1 + Math.ceil((firstThursday - target) / 604800000);
}

export function mostRecentSaturday(d = new Date()) {
  // The Saturday on or before `d`. Used for "the week that just ended".
  const out = new Date(d);
  const daysBack = (d.getDay() + 1) % 7; // Saturday = 6; (6+1)%7 = 0
  out.setDate(out.getDate() - daysBack);
  out.setHours(0, 0, 0, 0);
  return out;
}

export function upcomingSaturday(d = new Date()) {
  // The Saturday on or after `d` — i.e. the Saturday of the calendar week
  // that contains `d`. Used for "this week" (Sunday → Saturday containing today).
  const out = new Date(d);
  const daysForward = (6 - d.getDay() + 7) % 7;
  out.setDate(out.getDate() + daysForward);
  out.setHours(0, 0, 0, 0);
  return out;
}

export function addDays(d, n) {
  const out = new Date(d);
  out.setDate(out.getDate() + n);
  return out;
}

export function formatDate(d) {
  return d.toLocaleDateString(undefined, {
    weekday: "long", month: "long", day: "numeric"
  });
}

export function formatTime(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleTimeString(undefined, {hour: "2-digit", minute: "2-digit"}); }
  catch { return iso; }
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    if (typeof c === "string") node.appendChild(document.createTextNode(c));
    else node.appendChild(c);
  }
  return node;
}

// Collapsible <details> card. First child should be a <summary>. State
// persists to localStorage under `c_<id>` (0 = open, 1 = collapsed).
// Default state is OPEN unless user has explicitly collapsed.
export function collapse(id, ...children) {
  const KEY = "c_" + id;
  const closed = localStorage.getItem(KEY) === "1";
  const det = el("details", { class: "view-card collapsible", ...(closed ? {} : { open: "" }) }, ...children);
  det.addEventListener("toggle", () => {
    localStorage.setItem(KEY, det.open ? "0" : "1");
  });
  return det;
}

export function toast(msg, kind = "info") {
  let t = document.getElementById("toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove("show"), 2400);
}
