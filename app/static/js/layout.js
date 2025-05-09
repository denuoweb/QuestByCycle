document.addEventListener('DOMContentLoaded', function() {
  // ----------------------------------------------------------------
  // 1) Service Worker registration & update‐available prompt
  // ----------------------------------------------------------------
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register("static/sw.js")
      .then(function(registration) {
        console.log('ServiceWorker registered:', registration);
        registration.addEventListener('updatefound', function() {
          var newWorker = registration.installing;
          newWorker.addEventListener('statechange', function() {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              if (confirm('A new version is available. Reload to update?')) {
                window.location.reload();
              }
            }
          });
        });
      })
      .catch(function(err) {
        console.error('SW registration failed:', err);
      });

    navigator.serviceWorker.addEventListener('message', function(event) {
      console.log('SW message event:', event);
      if (event.data.type === 'UPDATE_AVAILABLE') {
        if (confirm('A new version is available. Reload to update?')) {
          window.location.reload();
        }
      }
    });
  }

  // ----------------------------------------------------------------
  // 2) Cache DOM lookups
  // ----------------------------------------------------------------
  var notifBell     = document.getElementById('notifBell');
  var notifMenu     = document.getElementById('notifMenu');
  var gameBtn       = document.getElementById('gameDropdownButton');
  var installButton = document.getElementById('install');
  var manualInstall = document.getElementById('manual-install');
  var isSafari      = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  var deferredPrompt = null;
  // Grab the real notifications‐fetch URL from our data attribute:
  var notificationsUrl = notifMenu.getAttribute('data-url');

 
  // ----------------------------------------------------------------
  // 3) PWA install prompt & manual‐install UI
  // ----------------------------------------------------------------
  if (isSafari) {
    manualInstall.hidden = false;
    console.log('Safari detected: showing manual instructions.');
  } else {
    manualInstall.hidden = true;
  }

  window.addEventListener('beforeinstallprompt', function(e) {
    console.log('beforeinstallprompt fired:', e);
    e.preventDefault();
    deferredPrompt = e;
    installButton.hidden = false;

    installButton.addEventListener('click', function() {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choice) {
        console.log('User install choice:', choice.outcome);
        deferredPrompt = null;
        installButton.hidden = true;
      });
    });
  });

  if (!window.beforeinstallprompt) {
    installButton.hidden = true;
    if (!isSafari) manualInstall.hidden = true;
  }

  window.addEventListener('appinstalled', function() {
    console.log('PWA installed.');
    installButton.hidden = true;
    manualInstall.hidden = true;
  });

  if (navigator.getInstalledRelatedApps) {
    navigator.getInstalledRelatedApps().then(function(apps) {
      console.log('Related apps:', apps);
      if (apps.length) installButton.hidden = true;
    });
  }

  // ----------------------------------------------------------------
  // 4) Game‐selection helper (exactly as before)
  // ----------------------------------------------------------------
  window.handleGameSelection = function(opt) {
    var val = opt.value;
    if (val === 'join_custom_game') {
      openModal('joinCustomGameModal');
    } else {
      window.location.href = val;
    }
  };

  // ----------------------------------------------------------------
  // 5) Leaderboard click handler
  // ----------------------------------------------------------------
  var leaderboardLink = document.getElementById('leaderboardNavbarLink');
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

  // ----------------------------------------------------------------
  // 6) Notification rendering helper
  // ----------------------------------------------------------------
  function renderNotification(n) {
    var text, onclick;
    switch (n.type) {
      case 'follow':
        text = 'Now following ' + n.payload.from_user_name;
        onclick = 'showUserProfileModal(' + n.payload.from_user_id + '); return false;';
        break;
      case 'submission':
        text = n.payload.actor_name + ' submitted a new “' + n.payload.quest_name + '” quest';
        onclick =
          "fetch('/quests/submissions/" + n.payload.submission_id + "')" +
          ".then(function(r){return r.json();})" +
          ".then(function(img){showSubmissionDetail(img);});" +
          "return false;";
        break;
      case 'profile_message':
        text = n.payload.from_user_name + ' says “' + n.payload.content + '”';
        onclick = 'showUserProfileModal(' + n.payload.profile_user_id + '); return false;';
        break;
      case 'profile_reply':
        text = n.payload.from_user_name + ' replied “' + n.payload.content + '”';
        onclick = 'showUserProfileModal(' + n.payload.profile_user_id + '); return false;';
        break;
      default:
        text = n.payload.summary || JSON.stringify(n.payload);
        onclick = "location.href='/notifications/';";
    }
    var cls = n.is_read ? '' : 'fw-bold';
    return '<a href="#" class="dropdown-item ' + cls + '" onclick="' + onclick + '">' + text + '</a>';
  }

  // ----------------------------------------------------------------
  // 7) Fetch & populate notifications on show.bs.dropdown
  // ----------------------------------------------------------------
  if (notifBell) {
    notifBell.addEventListener('show.bs.dropdown', function() {
      console.log('Opening notifications menu; fetching:', notificationsUrl);

      // show a loading placeholder immediately
      notifMenu.innerHTML =
        '<li class="dropdown-item text-center text-muted">Loading…</li>';

      fetch(notificationsUrl, { credentials: 'same-origin' })
        .then(function(response) {
          console.log('Fetch response:', response.status, response);
          if (!response.ok) {
            throw new Error('Network response was not OK: ' + response.status);
          }
          return response.json();
        })
        .then(function(notes) {
          if (!notes.length) {
            notifMenu.innerHTML =
              '<li class="dropdown-item text-center text-muted">' +
              'No notifications</li>';
          } else {
            notifMenu.innerHTML = notes.map(function(n) {
              return '<li>' +
                renderNotification(n) +
                '<small class="text-muted text-center">' +
                new Date(n.when).toLocaleString() +
                '</small><hr></li>';
            }).join('');
          }
          // remove the unread badge
          var badge = document.querySelector('#notifBellToggle .badge');
          if (badge) badge.remove();
        })
        .catch(function(err) {
          console.error('Notification fetch failed:', err);
          notifMenu.innerHTML =
            '<li class="dropdown-item text-center text-danger">' +
            'Error loading notifications</li>';
        });
    });
  }
  
});