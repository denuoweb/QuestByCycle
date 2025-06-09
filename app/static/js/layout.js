document.addEventListener('DOMContentLoaded', function() {
  // --------------------------------------------------------------
  // 1) Service Worker registration & update-available prompt
  // --------------------------------------------------------------
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('/sw.js')
      .then(function(registration) {
        registration.addEventListener('updatefound', function() {
          var newWorker = registration.installing;
          newWorker.addEventListener('statechange', function() {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              if (
                confirm('A new version is available. Reload to update?')
              ) {
                window.location.reload();
              }
            }
          });
        });
        if ('sync' in registration) {
          registration.sync.register('sync-requests').catch(function(err) {
            console.error('Background sync registration failed:', err);
          });
        }
      })
      .catch(function(err) {
        console.error('Service Worker registration failed:', err);
      });

    navigator.serviceWorker.addEventListener('message', function(event) {
      if (event.data.type === 'UPDATE_AVAILABLE') {
        if (
          confirm('A new version is available. Reload to update?')
        ) {
          window.location.reload();
        }
      }
    });
  }

  // --------------------------------------------------------------
  // 2) Cache DOM lookups
  // --------------------------------------------------------------
  var installButton   = document.getElementById('install');
  var manualInstall   = document.getElementById('manual-install');
  var isSafari        = /^((?!chrome|android).)*safari/i.test(
    navigator.userAgent
  );
  var deferredPrompt  = null;
  var leaderboardLink = document.getElementById('leaderboardNavbarLink');
  var gameBtn         = document.getElementById('gameDropdownButton');

  // --------------------------------------------------------------
  // 3) PWA install prompt & manual-install UI
  // --------------------------------------------------------------
  if (isSafari) {
    manualInstall.hidden = false;
  } else {
    manualInstall.hidden = true;
  }

  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt      = e;
    installButton.hidden = false;

    installButton.addEventListener('click', function() {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choice) {
        deferredPrompt      = null;
        installButton.hidden = true;
      });
    });
  });

  if (!window.beforeinstallprompt) {
    installButton.hidden = true;
    if (!isSafari) manualInstall.hidden = true;
  }

  window.addEventListener('appinstalled', function() {
    installButton.hidden = true;
    manualInstall.hidden = true;
  });

  if (navigator.getInstalledRelatedApps) {
    navigator.getInstalledRelatedApps().then(function(apps) {
      if (apps.length) installButton.hidden = true;
    });
  }

  // --------------------------------------------------------------
  // 4) Game-selection helper
  // --------------------------------------------------------------
  window.handleGameSelection = function(opt) {
    var val = opt.value;
    if (val === 'join_custom_game') {
      if (typeof openModal === 'function') {
        openModal('joinCustomGameModal');
      } else {
        window.location.href = '/?show_join_custom=1';
      }
    } else {
      window.location.href = val;
    }
  };

  // --------------------------------------------------------------
  // 5) Leaderboard click handler
  // --------------------------------------------------------------
  if (leaderboardLink) {
    leaderboardLink.addEventListener('click', function(e) {
      e.preventDefault();
      var gameId = leaderboardLink.getAttribute('data-game-id') || 0;
      if (typeof showLeaderboardModal === 'function') {
        showLeaderboardModal(gameId);
      } else {
        console.error('showLeaderboardModal not defined');
      }
    });
  }

  // --------------------------------------------------------------
  // 6) Hoist modals to document.body to avoid clipping
  // --------------------------------------------------------------
  document.querySelectorAll('.modal').forEach(function(modal) {
    if (modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }
  });
});