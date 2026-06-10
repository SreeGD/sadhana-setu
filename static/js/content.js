// Content loaders + date-based pickers.
// Mirrors the Python loaders in sadhana_setu/content/.

import { dayOfYear, isoWeek, todayISO } from "./util.js";

const _cache = {};

async function load(name) {
  if (_cache[name]) return _cache[name];
  const r = await fetch(`content/${name}.json`);
  if (!r.ok) throw new Error(`Failed to load ${name}: ${r.status}`);
  _cache[name] = await r.json();
  return _cache[name];
}

function pick(list, n) {
  return list[((n % list.length) + list.length) % list.length];
}

export async function todayAffirmation() {
  const { items } = await load("affirmations");
  return pick(items, dayOfYear());
}

export async function todayFaithVerse() {
  const { items } = await load("faith_verses");
  return pick(items, dayOfYear());
}

export async function todayInspiration() {
  const { items } = await load("inspirations");
  return pick(items, dayOfYear());
}

export async function todayTip() {
  const { items } = await load("tips");
  return pick(items, dayOfYear());
}

export async function todayNamaTattva() {
  const { items } = await load("nama_tattva");
  return pick(items, dayOfYear());
}

export async function todayBookTip() {
  const { items } = await load("book_tips");
  return pick(items, dayOfYear());
}

export async function weekBhajan() {
  const { items } = await load("bhajans");
  return pick(items, isoWeek());
}

export async function weekReading() {
  const { items } = await load("weekly_readings");
  return pick(items, isoWeek());
}

export async function weekJapaMethod() {
  const { items } = await load("japa_methods");
  return pick(items, isoWeek());
}

export async function weekStory() {
  const { items } = await load("weekly_stories");
  return pick(items, isoWeek());
}

export async function weekQuestions(n = 3) {
  const { items } = await load("weekly_questions");
  const week = isoWeek();
  const out = [];
  for (let i = 0; i < n; i++) out.push(pick(items, week * n + i));
  return out;
}

export async function todayEkadasi() {
  const doc = await load("ekadasi");
  const today = todayISO();
  return (doc.dates || []).find(e => e.date === today) || null;
}

export async function todayValue() {
  // Rotating practice-value tag for the meta line.
  const values = [
    "japa", "śravaṇa (hearing)", "kīrtana", "smaraṇa (remembrance)",
    "tṛṇād api sunīcena", "sevā", "śaraṇāgati"
  ];
  return pick(values, dayOfYear());
}
