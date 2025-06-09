(function(window){
  'use strict';

  window.getCSRFToken = function() {
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute('content') : '';
  };

  window.fetchJson = async function(url, options = {}) {
    const opts = { credentials: 'same-origin', ...options };
    const res = await fetch(url, opts);
    const json = await res.json().catch(() => ({}));
    return { status: res.status, json };
  };

})(window);
