export function getCSRFToken() {
  const el = document.querySelector('meta[name="csrf-token"]');
  return el ? el.getAttribute('content') : '';
}

export async function fetchJson(url, options = {}) {
  const opts = { credentials: 'same-origin', ...options };
  const res = await fetch(url, opts);
  const json = await res.json().catch(() => ({}));
  return { status: res.status, json };
}

export function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// backwards compatibility
window.getCSRFToken = getCSRFToken;
window.fetchJson = fetchJson;
window.escapeHTML = escapeHTML;
