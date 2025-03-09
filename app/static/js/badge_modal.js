// badge_modal.js

// Cache all badges in a global variable once loaded
window.allBadges = window.allBadges || [];

/**
 * Load all badges from the server endpoint (/badges/badges) if not already cached.
 * Calls the provided callback with the badge array.
 */
function loadAllBadges(callback) {
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
  const badgeId = element.getAttribute('data-badge-id');
  const taskNames = element.getAttribute('data-task-name'); // e.g., "Task A, Task B"
  const taskIdsAttr = element.getAttribute('data-task-id');   // e.g., "12" or "12,34"
  const badgeAwardedCount = element.getAttribute('data-badge-awarded-count');
  const userCompletionsAttr = element.getAttribute('data-user-completions');

  // Convert numeric values from strings.
  const requiredCount = parseInt(badgeAwardedCount, 10);
  const userCompletions = parseInt(userCompletionsAttr, 10) || 0;
  // (Do not compute earned here; recalc later based on dynamic completions)

  // Build an HTML list from taskNames.
  let taskListHTML = '';
  if (taskNames) {
    const tasks = taskNames.split(',');
    taskListHTML = `<ul>${tasks.map(task => `<li>${task.trim()}</li>`).join('')}</ul>`;
  }

  // Extract a single task ID if exactly one exists.
  let taskId = null;
  if (taskIdsAttr) {
    const taskIds = taskIdsAttr.split(',').map(id => id.trim()).filter(id => id !== "");
    if (taskIds.length === 1) {
      taskId = taskIds[0];
    }
  }

  // Helper function to open the modal using a given completions value.
  function _openModal(dynamicCompletions) {
    // Use dynamic completions if provided; otherwise, use the aggregated attribute.
    const currentUserCompletions = (typeof dynamicCompletions !== 'undefined') ? dynamicCompletions : userCompletions;
    // Recalculate the earned flag here.
    const earned = currentUserCompletions >= requiredCount;

    // Attempt to find the badge in the global cache.
    let badge = window.allBadges.find(b => b.id == badgeId);
    if (!badge) {
      // Fallback: build a minimal badge object from the element's data attributes.
      badge = {
        id: badgeId,
        name: element.getAttribute('data-badge-name') || "Badge",
        description: element.getAttribute('data-badge-description') || "",
        image: element.getAttribute('data-badge-image') || 'static/images/default_badge.png'
      };
    }

    const modalTitle = document.getElementById('badgeModalTitle');
    const modalImage = document.getElementById('badgeModalImage');
    const modalText = document.getElementById('badgeModalText');

    modalTitle.textContent = badge.name;
    modalImage.src = badge.image ? badge.image : 'static/images/default_badge.png';

    let badgeSpecificText = '';
    if (taskId) {
      // Single-task case: create a clickable link.
      const taskLink = `<a href="#" onclick="openQuestDetailModal('${taskId}')">${taskNames}</a>`;
      badgeSpecificText = `<p>Completion Requirement: ${requiredCount > 1 ? requiredCount + " times" : requiredCount + " time"}</p>
                           <p>Your Total Completions: ${currentUserCompletions}</p>
                           <p>${earned ? "You have earned this badge." : "Complete " + taskLink + " to earn this badge."}</p>`;
    } else {
      // Multiple tasks: display aggregated info.
      badgeSpecificText = `<p>Completion Requirements: ${requiredCount} (per task)</p>
                           <p>Your Total Completions: ${currentUserCompletions}</p>
                           ${taskListHTML}
                           <p>${earned ? "You have earned this badge." : "Complete one of the above tasks to earn this badge."}</p>`;
    }

    const descriptionText = badge.description || 'No description available.';
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
  }

  // For a single task, try to fetch dynamic completions.
  if (taskId) {
    fetch(`/quests/detail/${taskId}/user_completion`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to fetch user completions");
        }
        return response.json();
      })
      .then(data => {
        const dynamicCompletions = data.userCompletion ? data.userCompletion.completions : 0;
        console.debug("Dynamic completions fetched:", dynamicCompletions, "for requiredCount:", requiredCount);
        _openModal(dynamicCompletions);
      })
      .catch(error => {
        console.error("Error fetching user completions:", error);
        _openModal();
      });
  } else {
    // For multiple tasks or if no single taskId exists, use aggregated data.
    _openModal();
  }

  // Ensure badge cache is loaded.
  if (!window.allBadges || window.allBadges.length === 0) {
    loadAllBadges(function(badges) {
      window.allBadges = badges;
      _openModal();
    });
  }
}

// Preload badge cache on DOMContentLoaded.
document.addEventListener('DOMContentLoaded', function() {
  loadAllBadges(function(badges) {
    window.allBadges = badges;
  });
});
