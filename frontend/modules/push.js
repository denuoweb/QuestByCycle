import logger from '../logger.js';

document.addEventListener('DOMContentLoaded', () => {
  if (
    typeof window === 'undefined' ||
    typeof navigator === 'undefined' ||
    !('serviceWorker' in navigator) ||
    !('PushManager' in window)
  ) {
    return;
  }

  navigator.serviceWorker.ready.then(async (reg) => {
    try {
      const res = await fetch('/push/public_key');
      if (!res.ok) return;
      let public_key;
      try {
        ({ public_key } = await res.json());
      } catch (err) {
        logger.error('Push setup failed', err);
        return;
      }
      if (!public_key) return;

      const existing = await reg.pushManager.getSubscription();
      if (existing) return;

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      });
      await fetch('/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription: sub }),
      });
    } catch (err) {
      logger.error('Push setup failed', err);
    }
  });
});

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

