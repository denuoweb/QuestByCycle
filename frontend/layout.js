
import logger from './logger.js';
import { openModal } from './modules/modal_common.js';
import { csrfFetchJson } from './utils.js';

function sendSkipWaiting(reg) {
  if (reg.waiting) {
    reg.waiting.postMessage({ type: 'SKIP_WAITING' });
  }
}

function isSafeRelativeUrl(url) {
  try {
    const parsed = new URL(url, window.location.origin);
    return (
      parsed.origin === window.location.origin &&
      !["javascript:", "data:", "vbscript:"].includes(parsed.protocol)
    );
  } catch (err) {
    logger.error(`Invalid URL: ${url}`);
    return false;
  }
}

export function initLayout() {
  if ('serviceWorker' in navigator) {
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
    const assetVersion =
      document.querySelector("meta[name='asset-version']")?.content || "";
    navigator.serviceWorker
      .register(`/sw.js?v=${assetVersion}`)
      .then((registration) => {
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              logger.info('Service worker updated; skipping waiting.');
              sendSkipWaiting(registration);
            }
          });
        });

        if ('SyncManager' in window) {
          registration.sync
            .register('sync-notifications')
            .catch((err) => logger.error('Sync registration failed:', err));
        }

        if (registration.periodicSync) {
          registration.periodicSync
            .register('periodic-notifications', { minInterval: 24 * 60 * 60 * 1000 })
            .catch((err) => logger.error('Periodic sync registration failed:', err));
        }

        if ('PushManager' in window && Notification.permission === 'default') {
          Notification.requestPermission();
        }

        if ('sync' in registration) {
          registration.sync.register('sync-requests').catch((err) => {
            logger.error('Background sync registration failed:', err);
          });
        }
      })
      .catch((err) => logger.error('Service Worker registration failed:', err));

    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data.type === 'UPDATE_AVAILABLE') {
        navigator.serviceWorker.getRegistration().then((reg) => {
          if (reg) {
            logger.info('Update available message received; skipping waiting.');
            sendSkipWaiting(reg);
          }
        });
      }
    });
  }

  const installButton = document.getElementById('install');
  const manualInstall = document.getElementById('manual-install');
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  let deferredPrompt = null;
  const leaderboardLink = document.getElementById('leaderboardNavbarLink');

  if (manualInstall) {
    if (isSafari) {
      manualInstall.hidden = false;
    } else {
      manualInstall.hidden = true;
    }
  }

  const userId = document.body.getAttribute('data-user-id');
  if (userId && userId !== 'none') {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    csrfFetchJson(`/profile/${userId}/timezone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timezone: tz })
    }).catch(err => logger.error('Failed to send timezone:', err));
  }

  if (installButton) {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      installButton.hidden = false;

      installButton.addEventListener('click', () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(() => {
          deferredPrompt = null;
          installButton.hidden = true;
        });
      });
    });

    if (!window.beforeinstallprompt) {
      installButton.hidden = true;
      if (!isSafari && manualInstall) manualInstall.hidden = true;
    }

    window.addEventListener('appinstalled', () => {
      installButton.hidden = true;
      if (manualInstall) manualInstall.hidden = true;
    });

    if (navigator.getInstalledRelatedApps) {
      navigator.getInstalledRelatedApps().then((apps) => {
        if (apps.length) installButton.hidden = true;
      });
    }
  }




  if (leaderboardLink) {
    leaderboardLink.addEventListener('click', async (e) => {
      e.preventDefault();
      const gameId = leaderboardLink.getAttribute('data-game-id') || 0;
      const module = await import('./modules/leaderboard_modal.js');
      module.showLeaderboardModal(gameId);
    });
  }

  if ('windowControlsOverlay' in navigator) {
    function updateOverlayPadding() {
      const rect = navigator.windowControlsOverlay.getTitlebarAreaRect();
      document.body.style.paddingTop = rect.height + 'px';
    }
    navigator.windowControlsOverlay.addEventListener('geometrychange', updateOverlayPadding);
    updateOverlayPadding();
  }

  document.querySelectorAll('.modal').forEach((modal) => {
    if (modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }
  });
}

export function handleGameSelection(opt) {
  const val = opt.value;
  if (val === 'join_custom_game') {
    openModal('joinCustomGameModal');
  } else {
    if (isSafeRelativeUrl(val)) {
      window.location.href = val;
    } else {
      logger.error(`Blocked unsafe URL: ${val}`);
    }
  }
}

// Delegate clicks for game selection
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-game-selection]');
  if (!el) return;
  e.preventDefault();
  handleGameSelection({ value: el.getAttribute('data-game-selection') });
});
