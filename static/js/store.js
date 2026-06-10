// localStorage-backed tracker store. The browser is the database.
//
// Schema (all stored under one key, "sadhana_setu_v1"):
//   {
//     rounds:   { "YYYY-MM-DD": { count, captured_at, note } },
//     hearing:  [ { date, captured_at, source, line } ],
//     checkins: { "YYYY-MM-DD" (saturday): { week_start, tone, mood_bhava, ... } },
//     meta:     { last_export, last_import, schema_version }
//   }

const KEY = "sadhana_setu_v1";

function _read() {
  const raw = localStorage.getItem(KEY);
  if (!raw) return { rounds: {}, hearing: [], checkins: {}, meta: { schema_version: 1 } };
  try { return JSON.parse(raw); }
  catch { return { rounds: {}, hearing: [], checkins: {}, meta: { schema_version: 1 } }; }
}

function _write(s) {
  localStorage.setItem(KEY, JSON.stringify(s));
}

function _now() {
  return new Date().toISOString();
}

// ---------- rounds ----------

export function getRounds(date) {
  return _read().rounds[date] || null;
}

export function setRounds(date, count, note = null) {
  const s = _read();
  s.rounds[date] = { count, captured_at: _now(), note };
  _write(s);
  return s.rounds[date];
}

export function incrementRounds(date) {
  const cur = getRounds(date);
  return setRounds(date, (cur?.count || 0) + 1, cur?.note);
}

export function decrementRounds(date) {
  const cur = getRounds(date);
  if (!cur || cur.count <= 0) return cur;
  return setRounds(date, cur.count - 1, cur.note);
}

export function roundsBetween(startISO, endISO) {
  const all = _read().rounds;
  return Object.entries(all)
    .filter(([d]) => d >= startISO && d <= endISO)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, r]) => ({ date, ...r }));
}

// ---------- hearing notes ----------

export function getHearingForDate(date) {
  return _read().hearing
    .filter(h => h.date === date)
    .sort((a, b) => a.captured_at.localeCompare(b.captured_at));
}

export function addHearing(date, line, source = "") {
  const s = _read();
  s.hearing.push({ date, captured_at: _now(), source, line });
  _write(s);
}

export function deleteHearing(captured_at) {
  const s = _read();
  s.hearing = s.hearing.filter(h => h.captured_at !== captured_at);
  _write(s);
}

export function hearingCountBetween(startISO, endISO) {
  return _read().hearing.filter(h => h.date >= startISO && h.date <= endISO).length;
}

// ---------- weekly check-ins ----------

export function getCheckin(saturdayISO) {
  return _read().checkins[saturdayISO] || null;
}

export function saveCheckin(saturdayISO, payload) {
  const s = _read();
  s.checkins[saturdayISO] = {
    week_start: saturdayISO,
    ...payload,
    submitted_at: _now(),
  };
  _write(s);
  return s.checkins[saturdayISO];
}

export function listCheckins() {
  return Object.values(_read().checkins).sort((a, b) => a.week_start.localeCompare(b.week_start));
}

// ---------- backup / restore ----------

export function exportAll() {
  const s = _read();
  s.meta.last_export = _now();
  _write(s);
  return {
    app: "Sadhana Setu",
    schema_version: 1,
    exported_at: s.meta.last_export,
    rounds: s.rounds,
    hearing: s.hearing,
    checkins: s.checkins,
  };
}

export function importAll(backup, strategy = "merge") {
  if (!backup || backup.schema_version !== 1) {
    throw new Error("Unrecognised backup file (missing schema_version)");
  }
  const s = strategy === "replace"
    ? { rounds: {}, hearing: [], checkins: {}, meta: {} }
    : _read();

  // rounds: keep later captured_at
  for (const [date, r] of Object.entries(backup.rounds || {})) {
    const existing = s.rounds[date];
    if (!existing || (r.captured_at || "") > (existing.captured_at || "")) {
      s.rounds[date] = r;
    }
  }
  // hearing: dedup by (date, captured_at, line)
  const seen = new Set(s.hearing.map(h => `${h.date}|${h.captured_at}|${h.line}`));
  for (const h of (backup.hearing || [])) {
    const k = `${h.date}|${h.captured_at}|${h.line}`;
    if (!seen.has(k)) {
      s.hearing.push(h);
      seen.add(k);
    }
  }
  // checkins: keep later submitted_at
  for (const [week, c] of Object.entries(backup.checkins || {})) {
    const existing = s.checkins[week];
    if (!existing || (c.submitted_at || "") > (existing.submitted_at || "")) {
      s.checkins[week] = c;
    }
  }
  s.meta = s.meta || {};
  s.meta.last_import = _now();
  s.meta.schema_version = 1;
  _write(s);
  return {
    rounds: Object.keys(s.rounds).length,
    hearing: s.hearing.length,
    checkins: Object.keys(s.checkins).length,
  };
}

export function storageSummary() {
  const s = _read();
  return {
    rounds: Object.keys(s.rounds).length,
    hearing: s.hearing.length,
    checkins: Object.keys(s.checkins).length,
    last_export: s.meta?.last_export || null,
    last_import: s.meta?.last_import || null,
    bytes: (localStorage.getItem(KEY) || "").length,
  };
}

export function clearAll() {
  localStorage.removeItem(KEY);
}
