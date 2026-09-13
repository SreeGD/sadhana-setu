// i18n for the static app (spec 004, FR-012 — parity with sadhana_setu/i18n.py).
//
// Catalogs are emitted by build_static.py into static/i18n/:
//   i18n/ui/<locale>.json               — UI strings (te/kn/ta only when the catalog is REVIEWED;
//                                          an unreviewed catalog is emitted as {} ⇒ English fallback)
//   i18n/content/<locale>/<library>.json — REVIEWED content rows only (Constitution V)
// The static build is a published site, so there is no machine-draft opt-in here.

export const LOCALES = { en: "English", te: "తెలుగు", kn: "ಕನ್ನಡ", ta: "தமிழ்" };
const KEY = "sadhana_setu_locale";

let _locale = "en";
let _ui = {};
let _en = {};
const _content = {};

export function getLocale() { return _locale; }

async function fetchJSON(path) {
  try {
    const r = await fetch(path);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

// Load (or reload) the catalogs for `locale`; falls back to English silently.
export async function init(locale) {
  const stored = locale || localStorage.getItem(KEY) || "en";
  _locale = Object.prototype.hasOwnProperty.call(LOCALES, stored) ? stored : "en";
  localStorage.setItem(KEY, _locale);
  document.documentElement.lang = _locale;
  _en = (await fetchJSON("i18n/ui/en.json")) || {};
  _ui = _locale === "en" ? _en : ((await fetchJSON(`i18n/ui/${_locale}.json`)) || {});
  for (const k of Object.keys(_content)) delete _content[k];
  return _locale;
}

export async function setLocale(locale) {
  await init(locale);
}

// UI string with per-key English fallback; never blank (FR-002).
export function t(key, fmt) {
  let s = _ui[key];
  if (s == null) s = _en[key];
  if (s == null) s = key;
  if (fmt) for (const [k, v] of Object.entries(fmt)) s = s.split(`{${k}}`).join(String(v));
  return s;
}

async function contentRows(library) {
  if (_locale === "en") return [];
  if (!(library in _content)) {
    _content[library] = (await fetchJSON(`i18n/content/${_locale}/${library}.json`)) || [];
  }
  return _content[library];
}

// REVIEWED translation of one content field, else the English original (FR-003/004).
// `idx` is the item's position in its library (the overlay id, data-model.md).
export async function localizeContent(library, idx, field, english) {
  if (_locale === "en" || idx < 0) return english;
  const rows = await contentRows(library);
  const row = rows.find(r => String(r.id) === String(idx) && r.reviewed === true);
  return (row && row[field]) || english;
}

// Same, by item identity within its library list.
export async function localizeItem(library, items, item, field, english) {
  return localizeContent(library, Array.isArray(items) ? items.indexOf(item) : -1, field, english);
}

// Apply `data-i18n="key"` attributes across static markup (nav tabs, footer, tagline).
export function applyStatic(rootEl = document) {
  for (const node of rootEl.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
}
