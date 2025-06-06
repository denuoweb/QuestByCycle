// The version of the cache
const VERSION = "v2"; // Update this version number when changes are made
const CACHE_NAME = `questbycycle-${VERSION}`;

// List of static resources to cache
const APP_STATIC_RESOURCES = [
  // Root
  "/",
  "/offline.html",

  // CSS Files
  "/static/css/all.min.css",
  "/static/css/atom-one-dark.min.css",
  "/static/css/bootstrap.min.css",
  "/static/css/bootstrap.min.css.map",
  "/static/css/3rd/highlight.min.js",
  "/static/css/katex.min.css",
  "/static/css/main.css",
  "/static/css/quill.snow.css",
  "/static/css/quill.snow.css.map",
  "/static/css/3rd/fontawesome/all.min.css",
  "/static/css/3rd/webfonts/fa-brands-400.ttf",
  "/static/css/3rd/webfonts/fa-brands-400.woff2",
  "/static/css/3rd/webfonts/fa-solid-900.ttf",
  "/static/css/3rd/webfonts/fa-solid-900.woff2",

  // JavaScript Files
  "/static/js/all_submissions_modal.js",
  "/static/js/badge_management.js",
  "/static/js/3rd/bootstrap.bundle.min.js",
  "/static/js/3rd/bootstrap.bundle.min.js.map",
  "/static/js/generated_quest.js",
  "/static/js/3rd/highlight.min.js",
  "/static/js/index_management.js",
  "/static/js/3rd/jquery-3.6.0.min.js",
  "/static/js/3rd/katex.min.js",
  "/static/js/leaderboard_modal.js",
  "/static/js/modal_common.js",
  "/static/js/quest_detail_modal.js",
  "/static/js/3rd/quill.js.map",
  "/static/js/3rd/quill.min.js",
  "/static/js/3rd/socket.io.min.js",
  "/static/js/3rd/socket.io.min.js.map",
  "/static/js/submission_detail_modal.js",
  "/static/js/user_management.js",
  "/static/js/user_profile_modal.js",

  // Icons
  "/static/icons/icon_48x48.webp",
  "/static/icons/icon_96x96.webp",
  "/static/icons/icon_192x192.webp",
  "/static/icons/icon_512x512.webp",
  "/static/icons/apple-touch-icon-180x180.png",

  // Images (Add specific files if needed)
  "/static/images/",
];

// Install event
self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        await cache.addAll(APP_STATIC_RESOURCES);
        console.log("Resources cached successfully!");
      } catch (error) {
        console.error("Failed to cache resources:", error);
      }
    })()
  );
});

// Activate event
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const cacheKeys = await caches.keys();
      await Promise.all(
        cacheKeys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log(`Deleting old cache: ${key}`);
            return caches.delete(key);
          }
        })
      );
      await clients.claim();
      notifyClientsAboutUpdate();
    })()
  );
});

// Notify clients about the update
function notifyClientsAboutUpdate() {
  self.clients.matchAll().then((clients) => {
    clients.forEach((client) => {
      client.postMessage({ type: "UPDATE_AVAILABLE" });
    });
  });
}

// Fetch event with offline fallback
self.addEventListener("fetch", (event) => {
  if (event.request.mode === "navigate") {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return cachedResponse || fetch(event.request).catch(() => caches.match("/offline.html"));
      })
    );
    return;
  }

  event.respondWith(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(event.request);
        if (cachedResponse) {
          return cachedResponse;
        }
        const networkResponse = await fetch(event.request);
        if (event.request.url.startsWith(self.location.origin)) {
          cache.put(event.request, networkResponse.clone());
        }
        return networkResponse;
      } catch (error) {
        console.error("Fetch failed; returning offline page instead.", error);
        return caches.match("/offline.html");
      }
    })()
  );
});

// Handle messages from clients
self.addEventListener("message", (event) => {
  if (event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
