const refreshCSRFToken = async () => {
  try {
    const res  = await fetch('/refresh-csrf');
    const data = await res.json();
    document
      .querySelector('meta[name="csrf-token"]')
      .setAttribute('content', data.csrf_token);
  } catch (err) {
    console.error('Error refreshing CSRF token:', err);
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

    document.getElementById('meterBar').style.height = `${heightPercent}%`;
    document.documentElement.style.setProperty('--meter-fill-height', `${heightPercent}%`);
    document.querySelector('.meter-label').innerText =
      `Remaining Reduction: ${remainingPoints} / ${gameGoal}`;
  } catch (err) {
    console.error('Failed to update meter:', err);
  }
};

const previewFile = () => {
  const preview = document.getElementById('profileImageDisplay');
  const file    = document.querySelector('input[type=file]')?.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => { preview.src = reader.result; };
  reader.readAsDataURL(file);
};

// New function to update the game name in the header using the game ID from the hidden element
const updateGameName = async () => {
  const holder = document.getElementById('game_IdHolder');
  if (!holder) return;

  const gameId = Number(holder.dataset.gameId);
  if (!gameId) return;

  const header = document.getElementById('gameNameHeader');
  if (!header) return;

  try {
    const url = new URL(`/games/get_game/${gameId}`, window.location.origin);
    const r = await fetch(url, { credentials: 'same-origin' });
    if (!r.ok) throw new Error('Network response was not ok');
    const data = await r.json();
    header.textContent = data.name || 'Game Not Found';
  } catch (err) {
    console.error('Error retrieving game name:', err);
    header.textContent = 'Error Loading Game';
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const leaderboardButton = document.getElementById('leaderboardButton');
  if (leaderboardButton) {
    leaderboardButton.addEventListener('click', () => {
      const gameId = leaderboardButton.getAttribute('data-game-id');
      showLeaderboardModal(gameId);
      updateMeter(gameId);
    });
  }

  const submissionsButton = document.getElementById('submissionsButton');
  if (submissionsButton) {
    submissionsButton.addEventListener('click', () => {
      if (currentUserId !== 'none') showMySubmissionsModal(currentUserId);
    });
  }

  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', async e => {
      e.preventDefault();
      const formData = new FormData(contactForm);
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
      }
    });
  }

  const quillEditorContainer = document.getElementById('quill-editor');
  if (quillEditorContainer) {
    const quill = new Quill('#quill-editor', {
      theme: 'snow',
      placeholder: 'Write a message...',
      modules: { toolbar: [[{ header: [1, 2, false] }], ['bold', 'italic', 'underline'], ['link'], [{ list: 'ordered' }, { list: 'bullet' }], ['clean']] }
    });
    document.querySelector('form').onsubmit = () => {
      document.querySelector('#message-input').value = quill.root.innerHTML;
      return true;
    };
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
