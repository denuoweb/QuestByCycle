// The version of the cache
const VERSION = "v5"; // Update this version number when changes are made
const CACHE_NAME = `questbycycle-${VERSION}`;

// List of static resources to cache
const APP_STATIC_RESOURCES = [
  // Root
  "/",
  "/offline.html",

  // CSS Files
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
  "/static/js/push.js",

  // Icons
  "/static/icons/icon_48x48.webp",
  "/static/icons/icon_96x96.webp",
  "/static/icons/icon_192x192.webp",
  "/static/icons/icon_512x512.webp",
  "/static/icons/apple-touch-icon-180x180.png",

  // Images (Add specific files if needed)
  "/static/images/",
];

// -------------------- Background Sync Helpers --------------------
const DB_NAME = "questbycycle-sync";
const STORE_NAME = "queued";

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (event) => {
      event.target.result.createObjectStore(STORE_NAME, { autoIncrement: true });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function queueRequest(data) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).add(data);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function iterateRequests(callback) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const cursorReq = store.openCursor();
    cursorReq.onsuccess = async (event) => {
      const cursor = event.target.result;
      if (cursor) {
        await callback(cursor.value, cursor.key);
        cursor.continue();
      } else {
        resolve();
      }
    };
    cursorReq.onerror = () => reject(cursorReq.error);
  });
}

async function deleteRequest(key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function processQueue() {
  await iterateRequests(async (req, key) => {
    try {
      await fetch(req.url, {
        method: req.method,
        headers: req.headers,
        body: req.body,
      });
      await deleteRequest(key);
    } catch (err) {
      console.error("Background sync failed for", req.url, err);
    }
  });
}

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
      let isUpdate = false;
      await Promise.all(
        cacheKeys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log(`Deleting old cache: ${key}`);
            isUpdate = true;
            return caches.delete(key);
          }
        })
      );
      await clients.claim();
      if (isUpdate) {
        notifyClientsAboutUpdate();
      }
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

// Determine if a request should be cached
function shouldCacheRequest(request) {
  if (request.method !== "GET") {
    return false;
  }
  const acceptHeader = request.headers.get("Accept") || "";
  if (acceptHeader.includes("application/json")) {
    return false;
  }
  const url = new URL(request.url);
  return url.origin === self.location.origin;
}

// Fetch event with offline fallback
self.addEventListener("fetch", (event) => {
  // Queue non-GET requests when offline
  if (["POST", "PUT", "DELETE"].includes(event.request.method)) {
    event.respondWith(
      (async () => {
        try {
          return await fetch(event.request.clone());
        } catch (err) {
          const headers = {};
          for (const [k, v] of event.request.headers.entries()) {
            headers[k] = v;
          }
          const body = await event.request.clone().text();
          await queueRequest({ url: event.request.url, method: event.request.method, headers, body });
          if ("sync" in self.registration) {
            await self.registration.sync.register("sync-requests");
          }
          return new Response(JSON.stringify({ queued: true }), {
            status: 202,
            headers: { "Content-Type": "application/json" },
          });
        }
      })()
    );
    return;
  }

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
        if (shouldCacheRequest(event.request)) {
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

// Triggered when network becomes available
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-requests") {
    event.waitUntil(processQueue());
  }
});

// Handle messages from clients
self.addEventListener("message", (event) => {
  if (event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// ---------------------------------------------------------------------------
// Background sync to refresh notifications
// ---------------------------------------------------------------------------
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-notifications") {
    event.waitUntil(fetch("/notifications/unread_count"));
  }
});

// ---------------------------------------------------------------------------
// Periodic background sync for notification count
// ---------------------------------------------------------------------------
self.addEventListener("periodicsync", (event) => {
  if (event.tag === "periodic-notifications") {
    event.waitUntil(fetch("/notifications/unread_count"));
  }
});

// ---------------------------------------------------------------------------
// Push notifications support
// ---------------------------------------------------------------------------
self.addEventListener("push", (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { body: event.data.text() };
    }
  }
  const title = data.title || "QuestByCycle";
  const options = {
    body: data.body || "",
    icon: "/static/icons/icon_96x96.webp",
    data,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow("/notifications/"));
  const url = event.notification.data && event.notification.data.url;
  if (url) {
    event.waitUntil(clients.openWindow(url));
  }
});
