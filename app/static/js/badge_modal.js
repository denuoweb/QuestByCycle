// badge_modal.js

// Cache all badges in a global variable once loaded
window.allBadges = window.allBadges || [];

/**
 * Load all badges from the server endpoint (/badges/badges) if not already cached.
 * Calls the provided callback with the badge array.
 */
function loadAllBadges(callback) {
  // Always fetch fresh badge data (do not use the cached window.allBadges)
  const selectedGameId = document.getElementById('game_IdHolder').getAttribute('data-game-id');
  let fetchUrl = '/badges/badges';
  if (selectedGameId && selectedGameId !== '0') {
    fetchUrl += `?game_id=${selectedGameId}`;
  }
  fetch(fetchUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error("Error fetching badges");
      }
      return response.json();
    })
    .then(data => {
      callback(data.badges);
    })
    .catch(error => {
      console.error("Error loading badges:", error);
      callback([]);  // Return an empty array on error
    });
}


/**
 * Open the badge modal and populate it with data.
 * @param {HTMLElement} element - The badge element (entire badge card) that was clicked.
 */
function openBadgeModal(element) {
  // Retrieve static data from the clicked badge element.
  const badgeId = element.getAttribute('data-badge-id');
  const taskName = element.getAttribute('data-task-name');
  const badgeAwardedCount = parseInt(element.getAttribute('data-badge-awarded-count')) || 1;
  const taskId = element.getAttribute('data-task-id');

  // Helper function to actually open the modal once badges are loaded.
  function _openModal() {
    // Now that window.allBadges is ensured to be loaded, look for the badge.
    const badge = window.allBadges.find(b => b.id == badgeId);
    if (!badge) {
      alert("Badge not found.");
      return;
    }
    // If taskId is not valid, assume 0 completions.
    if (!taskId || taskId === "None") {
      const currentUserCompletions = 0;
      const earned = (currentUserCompletions >= badgeAwardedCount);
  
      const modalTitle = document.getElementById('badgeModalTitle');
      const modalImage = document.getElementById('badgeModalImage');
      const modalText = document.getElementById('badgeModalText');
  
      modalTitle.textContent = badge.name;
      modalImage.src = badge.image ? badge.image : 'static/images/default_badge.png';
  
      let descriptionText = badge.description || 'No description available.';
      let badgeSpecificText = '';
      if (taskName) {
        const taskLink = `<a href="#" onclick="openQuestDetailModal('${taskId}')">${taskName}</a>`;
        badgeSpecificText = `<p>Completion Requirement: ${badgeAwardedCount > 1 ? badgeAwardedCount + " times" : badgeAwardedCount + " time"}</p>
                             <p>Your Total Completions: ${currentUserCompletions}</p>
                             <p>${earned ? "You have earned this badge." : "Complete " + taskLink + " to earn this badge."}</p>`;
      }
  
      if (earned) {
        modalImage.style.filter = "none";
        modalImage.oncontextmenu = null;
        modalText.innerHTML = `<p><strong>Awarded!</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
      } else {
        modalImage.style.filter = "grayscale(100%) opacity(0.5)";
        modalImage.oncontextmenu = function(e) {
          e.preventDefault();
          return false;
        };
        modalText.innerHTML = `<p><strong>Not Awarded Yet</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
      }
      openModal('badgeModal');
      return;
    }
  
    // Otherwise, fetch dynamic completions data.
    fetch(`/quests/detail/${taskId}/user_completion`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to fetch user completions");
        }
        return response.json();
      })
      .then(data => {
        const currentUserCompletions = data.userCompletion ? data.userCompletion.completions : 0;
        console.debug("Current completions:", currentUserCompletions, "Badge Award Count:", badgeAwardedCount);
        const earned = (currentUserCompletions >= badgeAwardedCount);

        const modalTitle = document.getElementById('badgeModalTitle');
        const modalImage = document.getElementById('badgeModalImage');
        const modalText = document.getElementById('badgeModalText');
  
        modalTitle.textContent = badge.name;
        modalImage.src = badge.image ? badge.image : 'static/images/default_badge.png';
  
        let descriptionText = badge.description || 'No description available.';
        let badgeSpecificText = '';
        if (taskName && taskId) {
          const taskLink = `<a href="#" onclick="openQuestDetailModal('${taskId}')">${taskName}</a>`;
          badgeSpecificText = `<p>Completion Requirement: ${badgeAwardedCount > 1 ? badgeAwardedCount + " times" : badgeAwardedCount + " time"}</p>
                               <p>Your Total Completions: ${currentUserCompletions}</p>
                               <p>${earned ? "You have earned this badge." : "Complete " + taskLink + " to earn this badge."}</p>`;
        }
  
        if (earned) {
          modalImage.style.filter = "none";
          modalImage.oncontextmenu = null;
          modalText.innerHTML = `<p><strong>Awarded!</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
        } else {
          modalImage.style.filter = "grayscale(100%) opacity(0.5)";
          modalImage.oncontextmenu = function(e) {
            e.preventDefault();
            return false;
          };
          modalText.innerHTML = `<p><strong>Not Awarded Yet</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
        }
        
        openModal('badgeModal');
      })
      .catch(error => {
        console.error("Error fetching user completions:", error);
        alert("Unable to load badge details. Please try again.");
      });
  }
  
  // If the badge cache is empty, load badges first.
  if (!window.allBadges || window.allBadges.length === 0) {
    loadAllBadges(function(badges) {
      window.allBadges = badges;
      _openModal();
    });
  } else {
    _openModal();
  }
}
