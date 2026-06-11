// Sadhana Setu service worker.
// Generated from sw.js.template by build_static.py; do not edit sw.js directly.
//
// Strategy:
//   - Same-origin HTML/JS/CSS  → network-first, cache fallback (deploys appear immediately)
//   - Same-origin content/JSON, icons, manifest → cache-first, refresh in background
//   - Cross-origin (audio.iskcondesiretree.com, etc.) → bypass entirely

const CACHE_VERSION = "3b082e2";
const CACHE_NAME = `sadhana-setu-cache-${CACHE_VERSION}`;
const PRECACHE_LIST = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./css/style.css",
  "./js/app.js",
  "./js/content.js",
  "./js/store.js",
  "./js/util.js",
  "./js/views/backup.js",
  "./js/views/prejapa.js",
  "./js/views/saturday.js",
  "./js/views/this_week.js",
  "./js/views/today.js",
  "./js/week_summary.js",
  "./content/affirmations.json",
  "./content/bhajans.json",
  "./content/book_tips.json",
  "./content/daily_verses.json",
  "./content/ekadasi.json",
  "./content/faith_verses.json",
  "./content/inspirations.json",
  "./content/japa_methods.json",
  "./content/nama_tattva.json",
  "./content/sankalpas.json",
  "./content/tips.json",
  "./content/weekly_form_options.json",
  "./content/weekly_lectures.json",
  "./content/weekly_questions.json",
  "./content/weekly_readings.json",
  "./content/weekly_stories.json",
  "./content/weekly_verses.json",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-16.png",
  "./icons/favicon-32.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png"
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // Best-effort: don't fail install if a single file 404s.
      Promise.allSettled(PRECACHE_LIST.map((url) => cache.add(url)))
    )
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      caches.keys().then((names) =>
        Promise.all(
          names
            .filter((n) => n.startsWith("sadhana-setu-cache-") && n !== CACHE_NAME)
            .map((n) => caches.delete(n))
        )
      ),
    ])
  );
});

function isCacheFirst(url) {
  return (
    url.pathname.includes("/content/") ||
    url.pathname.includes("/icons/") ||
    url.pathname.endsWith(".webmanifest") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".ico")
  );
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const fresh = await fetch(request);
    if (fresh && fresh.ok) cache.put(request, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) {
    // Background revalidate
    fetch(request).then((fresh) => {
      if (fresh && fresh.ok) cache.put(request, fresh.clone());
    }).catch(() => {});
    return cached;
  }
  const fresh = await fetch(request);
  if (fresh && fresh.ok) cache.put(request, fresh.clone());
  return fresh;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Cross-origin: let the browser handle natively (audio embeds, etc.).
  if (url.origin !== self.location.origin) return;

  // Never intercept the SW file itself.
  if (url.pathname.endsWith("/sw.js")) return;

  event.respondWith(isCacheFirst(url) ? cacheFirst(req) : networkFirst(req));
});
