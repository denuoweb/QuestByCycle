export function initLayout() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              if (confirm('A new version is available. Reload to update?')) {
                window.location.reload();
              }
            }
          });
        });

        if ('SyncManager' in window) {
          registration.sync
            .register('sync-notifications')
            .catch((err) => console.error('Sync registration failed:', err));
        }

        if (registration.periodicSync) {
          registration.periodicSync
            .register('periodic-notifications', { minInterval: 24 * 60 * 60 * 1000 })
            .catch((err) => console.error('Periodic sync registration failed:', err));
        }

        if ('PushManager' in window && Notification.permission === 'default') {
          Notification.requestPermission();
        }

        if ('sync' in registration) {
          registration.sync.register('sync-requests').catch((err) => {
            console.error('Background sync registration failed:', err);
          });
        }
      })
      .catch((err) => console.error('Service Worker registration failed:', err));

    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data.type === 'UPDATE_AVAILABLE') {
        if (confirm('A new version is available. Reload to update?')) {
          window.location.reload();
        }
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
    leaderboardLink.addEventListener('click', (e) => {
      e.preventDefault();
      const gameId = leaderboardLink.getAttribute('data-game-id') || 0;
      if (typeof window.showLeaderboardModal === 'function') {
        window.showLeaderboardModal(gameId);
      } else {
        console.error('showLeaderboardModal not defined');
      }
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
    if (typeof window.openModal === 'function') {
      window.openModal('joinCustomGameModal');
    } else {
      window.location.href = '/?show_join_custom=1';
    }
  } else {
    window.location.href = val;
  }
}

window.handleGameSelection = handleGameSelection;
