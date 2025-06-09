"use strict";
import { openModal } from './modal_common.js';

// Cache all badges in a global variable once loaded
window.allBadges = window.allBadges || [];
const PLACEHOLDER_IMAGE =
  window.PLACEHOLDER_IMAGE ||
  document.querySelector('meta[name="placeholder-image"]').getAttribute('content');
window.PLACEHOLDER_IMAGE = PLACEHOLDER_IMAGE;

/**
 * Validate that a given URL is a safe image source.
 * @param {string} url - The URL to validate.
 * @returns {string} - The validated URL or the placeholder image.
*/
function validateImageUrl(url) {
  try {
    const parsedUrl = new URL(url, window.location.origin);
    if (parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:') {
      return url;
    }
  } catch (e) {
    // Invalid URL
  }
  return PLACEHOLDER_IMAGE;
}

/**
 * Fetch badges from the server. Updates the global cache and returns it.
 */
async function fetchAllBadges() {
  const gameHolder = document.getElementById("game_IdHolder");
  const selectedGameId = gameHolder ? gameHolder.getAttribute("data-game-id") : null;
  // Build the badge endpoint explicitly to avoid accidental path prefixing
  const query = (selectedGameId && !isNaN(parseInt(selectedGameId, 10)) &&
                 selectedGameId !== "0")
                 ? `?game_id=${selectedGameId}`
                 : '';
  const url = `/badges${query}`;

  const response = await fetch(url, { credentials: 'same-origin' });
  if (!response.ok) {
    throw new Error('Error fetching badges');
  }

  const data = await response.json();
  window.allBadges = data.badges;
  return window.allBadges;
}

/**
 * Ensure the global badge cache is populated.
 */
async function ensureBadgeCache() {
  if (!window.allBadges || window.allBadges.length === 0) {
    try {
      await fetchAllBadges();
    } catch (err) {
      console.error('Error loading badges:', err);
      window.allBadges = [];
    }
  }
}

function buildTaskListHTML(taskNames) {
  if (!taskNames) return '';
  const tasks = taskNames.split(',');
  return `<ul>${tasks.map(task => `<li>${escapeHTML(task.trim())}</li>`).join('')}</ul>`;
}

function findBadgeById(badgeId) {
  return window.allBadges.find(b => b.id == badgeId);
}

function getBadgeFromElement(element) {
  return {
    id: element.getAttribute('data-badge-id'),
    name: element.getAttribute('data-badge-name') || 'Badge',
    description: element.getAttribute('data-badge-description') || '',
    image: element.getAttribute('data-badge-image') || PLACEHOLDER_IMAGE
  };
}

async function fetchUserCompletions(taskId) {
  const response = await fetch(`/quests/detail/${taskId}/user_completion`);
  if (!response.ok) {
    throw new Error('Failed to fetch user completions');
  }
  const data = await response.json();
  return data.userCompletion ? data.userCompletion.completions : 0;
}

function populateBadgeModal(badge, requiredCount, currentUserCompletions, taskListHTML, earned, taskId, taskNames) {
  const modalTitle = document.getElementById('badgeModalTitle');
  const modalImage = document.getElementById('badgeModalImage');
  const modalText  = document.getElementById('badgeModalText');

  modalTitle.textContent = badge.name;
  modalImage.src = validateImageUrl(badge.image) || PLACEHOLDER_IMAGE;

  let badgeSpecificText = '';
  if (taskId) {
    const taskLink = `<a href="#" onclick="openQuestDetailModal('${taskId}')">${escapeHTML(taskNames)}</a>`;
    badgeSpecificText = `<p>Completion Requirement: ${requiredCount > 1 ? requiredCount + ' times' : requiredCount + ' time'}</p>` +
                        `<p>Your Total Completions: ${currentUserCompletions}</p>` +
                        `<p>${earned ? 'You have earned this badge.' : 'Complete ' + taskLink + ' to earn this badge.'}</p>`;
  } else {
    badgeSpecificText = `<p>Completion Requirements: ${requiredCount} (per task)</p>` +
                        `<p>Your Total Completions: ${currentUserCompletions}</p>` +
                        `${taskListHTML}` +
                        `<p>${earned ? 'You have earned this badge.' : 'Complete one of the above tasks to earn this badge.'}</p>`;
  }

  const descriptionText = badge.description || 'No description available.';
  if (earned) {
    modalImage.style.filter = 'none';
    modalImage.oncontextmenu = null;
    modalText.innerHTML = `<p><strong>Awarded!</strong></p>${badgeSpecificText}<p>${escapeHTML(descriptionText)}</p>`;
  } else {
    modalImage.style.filter = 'grayscale(100%) opacity(0.5)';
    modalImage.oncontextmenu = e => {
      e.preventDefault();
      return false;
    };
    modalText.innerHTML = `<p><strong>Not Awarded Yet</strong></p>${badgeSpecificText}<p>${escapeHTML(descriptionText)}</p>`;
  }
}

/**
 * Open the badge modal and populate it with data.
 * @param {HTMLElement} element - The badge element that was clicked.
 */
export async function openBadgeModal(element) {
  const badgeId = element.getAttribute('data-badge-id');
  const taskNames = element.getAttribute('data-task-name');
  const taskIdsAttr = element.getAttribute('data-task-id');
  const badgeAwardedCount = element.getAttribute('data-badge-awarded-count');
  const userCompletionsAttr = element.getAttribute('data-user-completions');

  const requiredCount = parseInt(badgeAwardedCount, 10);
  const userCompletions = parseInt(userCompletionsAttr, 10) || 0;

  const taskListHTML = buildTaskListHTML(taskNames);
  const taskIds = taskIdsAttr ? taskIdsAttr.split(',').map(id => id.trim()).filter(Boolean) : [];
  const taskId = taskIds.length === 1 ? taskIds[0] : null;

  await ensureBadgeCache();

  const badge = findBadgeById(badgeId) || getBadgeFromElement(element);

  let currentUserCompletions = userCompletions;
  if (taskId) {
    try {
      currentUserCompletions = await fetchUserCompletions(taskId);
    } catch (err) {
      console.error('Error fetching user completions:', err);
    }
  }

  const earned = currentUserCompletions >= requiredCount;

  populateBadgeModal(badge, requiredCount, currentUserCompletions, taskListHTML, earned, taskId, taskNames);
  openModal('badgeModal');
}

// Preload badge cache on DOMContentLoaded.
document.addEventListener('DOMContentLoaded', () => {
  ensureBadgeCache();
});

// Expose globally for inline handlers
window.openBadgeModal = openBadgeModal;

