// badge_modal.js

// Cache all badges in a global variable once loaded
window.allBadges = window.allBadges || [];

/**
 * Load all badges from the server endpoint (/badges/badges) if not already cached.
 * Calls the provided callback with the badge array.
 */
function loadAllBadges(callback) {
  if (window.allBadges.length > 0) {
    callback(window.allBadges);
  } else {
    // Get the selected game ID from wherever it's stored in your frontend (e.g., data attribute, global variable)
    const selectedGameId = document.getElementById('game_IdHolder').getAttribute('data-game-id'); // Example: get from a hidden element

    let fetchUrl = '/badges/badges';
    if (selectedGameId && selectedGameId !== '0') { // Check if game_id is valid and not 'None' or '0'
      fetchUrl += `?game_id=${selectedGameId}`; // Append game_id as query parameter
    }

    fetch(fetchUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error("Error fetching badges");
        }
        return response.json();
      })
      .then(data => {
        window.allBadges = data.badges; // Assume data.badges is the array of badge objects
        callback(window.allBadges);
      })
      .catch(error => {
        console.error("Error loading badges:", error);
        callback([]);  // Return an empty array on error
      });
  }
}

/**
 * Open the badge modal and populate it with data.
 * @param {HTMLElement} element - The badge element (entire badge card) that was clicked.
 */
function openBadgeModal(element) {
  // Retrieve data attributes from the clicked badge element
  const badgeId = element.getAttribute('data-badge-id');
  const taskName = element.getAttribute('data-task-name');
  const badgeAwardedCount = parseInt(element.getAttribute('data-badge-awarded-count')) || 1;
  const taskId = element.getAttribute('data-task-id');
  const userCompletions = parseInt(element.getAttribute('data-user-completions')) || 0;

  // Determine if the badge is earned by comparing actual completions to required completions
  const earned = (userCompletions >= badgeAwardedCount);

  loadAllBadges(function(badges) {
    const badge = badges.find(b => b.id == badgeId);
    if (!badge) {
      alert("Badge not found.");
      return;
    }
    
    // Obtain modal DOM elements
    const modalTitle = document.getElementById('badgeModalTitle');
    const modalImage = document.getElementById('badgeModalImage');
    const modalText = document.getElementById('badgeModalText');

    // Set modal title and image source
    modalTitle.textContent = badge.name;
    modalImage.src = (badge.image || 'static/images/default_badge.png');

    let descriptionText = badge.description || 'No description available.';
    let badgeSpecificText = '';

    // Construct a clickable link to the awarding quest if taskName and taskId are available
    if (taskName && taskId) {
      const taskLink = `<a href="#" onclick="openQuestDetailModal('${taskId}')">${taskName}</a>`;
      badgeSpecificText = `<p>Completion Requirement: ${badgeAwardedCount > 1 ? badgeAwardedCount + " times" : badgeAwardedCount + " time"}</p>
                           <p>Your Total Completions: ${userCompletions}</p>
                           <p>${earned ? "You have earned this badge." : "Complete " + taskLink + " to earn this badge."}</p>`;
    }

    // Apply styling and event listeners based on whether the badge is earned
    if (earned) {
      // For earned badges, remove any greying filter and allow normal interaction
      modalImage.style.filter = "none";
      // Remove any previously set contextmenu handler, allowing right-click if needed
      modalImage.oncontextmenu = null;
      modalText.innerHTML = `<p><strong>Awarded!</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
    } else {
      // For unearned badges, apply a greying filter
      modalImage.style.filter = "grayscale(100%) opacity(0.5)";
      // Disable right-click context menu on the badge image
      modalImage.oncontextmenu = function(e) {
         e.preventDefault();
         return false;
      };
      modalText.innerHTML = `<p><strong>Not Awarded Yet</strong></p>${badgeSpecificText}<p>${descriptionText}</p>`;
    }

    // Finally, open the badge modal
    openModal('badgeModal');
  });
}
