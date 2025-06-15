import { showLoadingModal, hideLoadingModal } from './loading_modal.js';
import { showAllSubmissionsModal } from './all_submissions_modal.js';
import { closeModal } from './modal_common.js';
import logger from '../logger.js';
const refreshCSRFToken = async () => {
  try {
    const res  = await fetch('/refresh-csrf');
    const data = await res.json();
    document
      .querySelector('meta[name="csrf-token"]')
      .setAttribute('content', data.csrf_token);
  } catch (err) {
    logger.error('Error refreshing CSRF token:', err);
  }
};

// Refresh the CSRF token every 15 minutes
setInterval(refreshCSRFToken, 900000);

const updateMeter = async gameId => {
  try {
    const r = await fetch(`/games/get_game_points/${gameId}`, {
      credentials: 'same-origin'
    });
    const data = await r.json();
    const totalPoints     = data.total_game_points;
    const gameGoal        = data.game_goal;
    const remainingPoints = gameGoal - totalPoints;
    const heightPercent   = Math.min((totalPoints / gameGoal) * 100, 100);

    const meterBar = document.getElementById('meterBar');
    const label = document.querySelector('.meter-label');
    if (meterBar) meterBar.style.height = `${heightPercent}%`;
    document.documentElement.style.setProperty('--meter-fill-height', `${heightPercent}%`);
    if (label) {
      label.innerText = `Remaining Reduction: ${remainingPoints} / ${gameGoal}`;
    }
  } catch (err) {
    logger.error('Failed to update meter:', err);
  }
};


function updateGameName() {
  const gameHolder = document.getElementById('game_IdHolder');
  const gameNameHeader = document.getElementById('gameNameHeader');
  if (!gameHolder || !gameNameHeader) return;

  const gameId = gameHolder.getAttribute('data-game-id');

  fetch(`/games/get_game/${gameId}`, { credentials: 'same-origin' })
    .then(response => {
      if (!response.ok) {
        logger.error(
          `Failed fetching game name; URL returned status ${response.status} (${response.statusText})`
        );
        // show a user-friendly message in the header
        gameNameHeader.textContent = 'Error Loading Game';
        // still throw so downstream .catch() will run
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      gameNameHeader.textContent = data.name || 'Game Not Found';
    })
    .catch(error => {
      logger.error('Error retrieving game name:', error);
      gameNameHeader.textContent = 'Error Loading Game';
    });
}


document.addEventListener('DOMContentLoaded', () => {
  const leaderboardButton = document.getElementById('leaderboardButton');
  if (leaderboardButton) {
    leaderboardButton.addEventListener('click', async () => {
      const gameId = leaderboardButton.getAttribute('data-game-id');
      const module = await import('./leaderboard_modal.js');
      module.showLeaderboardModal(gameId);
      updateMeter(gameId);
    });
  }

  const submissionsButton = document.getElementById('submissionsButton');
  if (submissionsButton) {
    submissionsButton.addEventListener('click', () => {
      if (currentUserId !== 'none') showAllSubmissionsModal(currentUserId);
    });
  }

  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', async e => {
      e.preventDefault();
      const formData = new FormData(contactForm);
      showLoadingModal();
      try {
        const r = await fetch(contactForm.action, {
          method: 'POST',
          body: formData,
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await r.json();
        if (r.ok && data.success) {
          alert('Your message has been sent successfully.');
          closeModal('contactModal');
        } else {
          alert('Failed to send your message. Please try again.');
        }
      } catch {
        alert('Failed to send your message. Please try again.');
      } finally {
        hideLoadingModal();
      }
    });
  }

  const messageInput = document.getElementById('message-input');
  if (messageInput) {
    document.querySelector('form').onsubmit = () => true;
  }

  document.querySelectorAll('.activity-message').forEach(el => {
    el.innerHTML = el.innerHTML.replace(/<\/?p[^>]*>/g, '');
  });

  const searchBox = document.getElementById('questSearchInput');
  const categorySel = document.getElementById('questCategoryDropdown');
  if (searchBox) searchBox.addEventListener('input', filterQuests);
  if (categorySel) categorySel.addEventListener('change', filterQuests);

  const widget = document.querySelector('#whats-happening-step');
  if (widget) {
    const tabButtons  = widget.querySelectorAll('.wh-tab-button');
    const tabContents = widget.querySelectorAll('.wh-tab-content');

    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-wh-tab');
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        widget.querySelector(`#wh-${target}-tab`).classList.add('active');
      });
    });
  }

  const qButtons       = document.querySelectorAll('.quest-tab-navigation .quest-tab-button');
  const qContents      = document.querySelectorAll('.quest-tab-content');
  const searchInput    = document.getElementById('questSearchInput');
  const categoryGroup  = document.getElementById('questCategoryGroup');
  if (qButtons.length && qContents.length) {
    qButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-quest-tab');
        qButtons.forEach(b => b.classList.remove('active'));
        qContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`${target}-tab`).classList.add('active');

        if (target === 'calendar-quests') {
          if (searchInput) searchInput.style.display = 'none';
          if (categoryGroup) categoryGroup.style.display = 'none';
        } else {
          if (searchInput) searchInput.style.display = '';
          if (categoryGroup) categoryGroup.style.display = '';
        }
      });
    });
  }

  updateGameName();
});

// Combined filtering function for both search input and category dropdown
function filterQuests() {
  const searchValue      = document.getElementById('questSearchInput').value.trim().toLowerCase();
  const selectedCategory = document.getElementById('questCategoryDropdown').value;
  const rows             = document.querySelectorAll('#questTableBody tr.quest-row');

  rows.forEach(row => {
    /* correct selector: the real title is in <span class="quest-title"> */
    const title    = row.querySelector('.quest-title').textContent.toLowerCase();
    const category = row.dataset.category || 'Not Set';

    const matchesSearch    = title.includes(searchValue);
    const matchesCategory  = selectedCategory === 'all' || category === selectedCategory;

    row.style.display = (matchesSearch && matchesCategory) ? '' : 'none';
  });
}

/* attach listeners once */
// additional event listeners are installed in the main DOMContentLoaded handler

