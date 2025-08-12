export function getCSRFToken() {
  const el = document.querySelector('meta[name="csrf-token"]');
  return el ? el.getAttribute('content') : '';
}

export function isDebugMode() {
  const meta = document.querySelector('meta[name="debug-mode"]');
  return meta?.getAttribute('content') === 'true';
}

export async function fetchJson(url, options = {}) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) };
  const opts = {
    credentials: 'same-origin',
    cache: 'no-store',
    ...options,
    headers,
  };
  const res = await fetch(url, opts);
  const json = await res.json().catch(() => ({}));
  return { status: res.status, json };
}

export async function csrfFetchJson(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  headers['X-CSRF-Token'] = getCSRFToken();
  return fetchJson(url, { ...options, headers });
}

export function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
