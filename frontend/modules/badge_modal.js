'use strict';
import { openModal } from './modal_common.js';
import logger from '../logger.js';

// Cache loaded badges within this module
let allBadges = [];
const placeholderMeta = document.querySelector('meta[name="placeholder-image"]');
const PLACEHOLDER_IMAGE = placeholderMeta
  ? placeholderMeta.getAttribute('content')
  : '';

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
  } catch {
    // Invalid URL
  }
  return PLACEHOLDER_IMAGE;
}

/**
 * Fetch badges from the server. Updates the global cache and returns it.
 */
async function fetchAllBadges() {
  const gameHolder = document.getElementById('game_IdHolder');
  const selectedGameId = gameHolder ? gameHolder.getAttribute('data-game-id') : null;
  // Build the badge endpoint explicitly to avoid accidental path prefixing
  const query = (selectedGameId && !isNaN(parseInt(selectedGameId, 10)) &&
                 selectedGameId !== '0')
                 ? `?game_id=${selectedGameId}`
                 : '';
  const url = `/badges${query}`;

  const response = await fetch(url, { credentials: 'same-origin' });
  if (!response.ok) {
    throw new Error('Error fetching badges');
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('Error parsing badge data');
  }
  allBadges = Array.isArray(data.badges) ? data.badges : [];
  return allBadges;
}

/**
 * Ensure the global badge cache is populated.
 */
async function ensureBadgeCache() {
  if (!allBadges || allBadges.length === 0) {
    try {
      await fetchAllBadges();
    } catch (err) {
      logger.error('Error loading badges:', err);
      allBadges = [];
    }
  }
}

function buildTaskList(taskNames) {
  if (!taskNames) return null;
  const ul = document.createElement('ul');
  taskNames.split(',').forEach((task) => {
    const li = document.createElement('li');
    li.textContent = task.trim();
    ul.appendChild(li);
  });
  return ul;
}

function findBadgeById(badgeId) {
  return allBadges.find(b => b.id == badgeId);
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
  const response = await fetch(`/quests/detail/${encodeURIComponent(taskId)}/user_completion`);
  if (!response.ok) {
    throw new Error('Failed to fetch user completions');
  }
  const data = await response.json();
  return data.userCompletion ? data.userCompletion.completions : 0;
}

function populateBadgeModal(badge, requiredCount, currentUserCompletions, taskListEl, earned, taskId, taskNames) {
  const modalTitle = document.getElementById('badgeModalTitle');
  const modalImage = document.getElementById('badgeModalImage');
  const modalText = document.getElementById('badgeModalText');

  if (!modalTitle || !modalImage || !modalText) {
    logger.error('Badge modal elements missing');
    return;
  }

  modalTitle.textContent = badge.name;
  modalImage.src = validateImageUrl(badge.image) || PLACEHOLDER_IMAGE;

  modalText.textContent = '';

  const statusP = document.createElement('p');
  const statusStrong = document.createElement('strong');
  statusStrong.textContent = earned ? 'Awarded!' : 'Not Awarded Yet';
  statusP.appendChild(statusStrong);
  modalText.appendChild(statusP);

  if (taskId) {
    const reqP = document.createElement('p');
    reqP.textContent = `Completion Requirement: ${requiredCount > 1 ? requiredCount + ' times' : requiredCount + ' time'}`;
    modalText.appendChild(reqP);

    const totalP = document.createElement('p');
    totalP.textContent = `Your Total Completions: ${currentUserCompletions}`;
    modalText.appendChild(totalP);

    const infoP = document.createElement('p');
    if (earned) {
      infoP.textContent = 'You have earned this badge.';
    } else {
      infoP.append('Complete ');
      const link = document.createElement('a');
      link.href = '#';
      link.dataset.questDetail = taskId;
      link.textContent = taskNames;
      infoP.appendChild(link);
      infoP.append(' to earn this badge.');
    }
    modalText.appendChild(infoP);
  } else {
    const reqP = document.createElement('p');
    reqP.textContent = `Completion Requirements: ${requiredCount} (per task)`;
    modalText.appendChild(reqP);

    const totalP = document.createElement('p');
    totalP.textContent = `Your Total Completions: ${currentUserCompletions}`;
    modalText.appendChild(totalP);

    if (taskListEl) {
      modalText.appendChild(taskListEl);
    }

    const infoP = document.createElement('p');
    infoP.textContent = earned
      ? 'You have earned this badge.'
      : 'Complete one of the above tasks to earn this badge.';
    modalText.appendChild(infoP);
  }

  const descriptionText = badge.description || 'No description available.';
  const descP = document.createElement('p');
  descP.textContent = descriptionText;
  if (earned) {
    modalImage.style.filter = 'none';
    modalImage.oncontextmenu = null;
  } else {
    modalImage.style.filter = 'grayscale(100%) opacity(0.5)';
    modalImage.oncontextmenu = (e) => {
      e.preventDefault();
      return false;
    };
  }
  modalText.appendChild(descP);
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

  const taskListEl = buildTaskList(taskNames);
  const taskIds = taskIdsAttr ? taskIdsAttr.split(',').map(id => id.trim()).filter(Boolean) : [];
  const taskId = taskIds.length === 1 ? taskIds[0] : null;

  await ensureBadgeCache();

  const badge = findBadgeById(badgeId) || getBadgeFromElement(element);

  let currentUserCompletions = userCompletions;
  if (taskId) {
    try {
      currentUserCompletions = await fetchUserCompletions(taskId);
    } catch (err) {
      logger.error('Error fetching user completions:', err);
    }
  }

  const earned = currentUserCompletions >= requiredCount;

  populateBadgeModal(badge, requiredCount, currentUserCompletions, taskListEl, earned, taskId, taskNames);
  openModal('badgeModal');
}

// Preload badge cache on DOMContentLoaded.
document.addEventListener('DOMContentLoaded', () => {
  ensureBadgeCache();
});

// Event delegation for badge modals
document.addEventListener('click', (e) => {
  const badgeEl = e.target.closest('[data-open-badge]');
  if (badgeEl) {
    e.preventDefault();
    openBadgeModal(badgeEl);
  }
});

