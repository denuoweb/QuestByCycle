function refreshCSRFToken() {
    fetch('/refresh-csrf')
        .then(response => response.json())
        .then(data => {
            document.querySelector('meta[name="csrf-token"]').setAttribute('content', data.csrf_token);
        })
        .catch(error => console.error('Error refreshing CSRF token:', error));
}

// Refresh the CSRF token every 15 minutes (900000 milliseconds)
setInterval(refreshCSRFToken, 900000);

function updateMeter(gameId) {
    // Ensure we request the absolute endpoint and include cookies
    fetch(`/games/get_game_points/${gameId}`, { credentials: 'same-origin' })
        .then(response => response.json())
        .then(data => {
            const totalPoints = data.total_game_points;
            const gameGoal = data.game_goal;
            const remainingPoints = gameGoal - totalPoints;
            const heightPercentage = Math.min((totalPoints / gameGoal) * 100, 100);
            document.getElementById('meterBar').style.height = heightPercentage + '%';
            document.documentElement.style.setProperty('--meter-fill-height', heightPercentage + '%');

            document.querySelector('.meter-label').innerText = `Remaining Reduction: ${remainingPoints} / ${gameGoal}`;
        })
        .catch(err => console.error('Failed to update meter:', err));
}

function previewFile() {
    var preview = document.getElementById('profileImageDisplay');
    var file = document.querySelector('input[type=file]').files[0];
    var reader = new FileReader();

    reader.addEventListener("load", function () {
        preview.src = reader.result;
    }, false);

    if (file) {
        reader.readAsDataURL(file);
    }
}

// New function to update the game name in the header using the game ID from the hidden element
function updateGameName() {
    const gameHolder = document.getElementById("game_IdHolder");
    if (!gameHolder) return;

    const gameIdAttr = gameHolder.getAttribute("data-game-id");
    if (!gameIdAttr || isNaN(parseInt(gameIdAttr, 10))) return;
    const gameId = parseInt(gameIdAttr, 10);
    const gameNameHeader = document.getElementById("gameNameHeader");

    if (gameNameHeader) {
        fetch(`/games/get_game/${gameId}`, { credentials: 'same-origin' })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then(data => {
                if (data.name) {
                    gameNameHeader.textContent = data.name;
                } else {
                    gameNameHeader.textContent = "Game Not Found";
                }
            })
            .catch(error => {
                console.error("Error retrieving game name:", error);
                gameNameHeader.textContent = "Error Loading Game";
            });
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const leaderboardButton = document.getElementById('leaderboardButton');
    if (leaderboardButton) {
        leaderboardButton.addEventListener('click', function() {
            const gameId = this.getAttribute('data-game-id');
            showLeaderboardModal(gameId);
            updateMeter(gameId);
        });
    }

    const submissionsButton = document.getElementById('submissionsButton');
    if (submissionsButton) {
        submissionsButton.addEventListener('click', function() {
            if (currentUserId !== 'none') {
                showMySubmissionsModal(currentUserId);
            }
        });
    }

    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(contactForm);
            const request = new XMLHttpRequest();
            request.open('POST', contactForm.action, true);
            request.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            request.onload = function() {
                if (request.status >= 200 && request.status < 400) {
                    const response = JSON.parse(request.responseText);
                    if (response.success) {
                        alert('Your message has been sent successfully.');
                        closeModal('contactModal');
                    } else {
                        alert('Failed to send your message. Please try again.');
                    }
                } else {
                    alert('Failed to send your message. Please try again.');
                }
            };
            request.onerror = function() {
                alert('Failed to send your message. Please try again.');
            };
            request.send(formData);
        });
    }

    // Call the new function to update the game name in the header
    updateGameName();
});

document.addEventListener('DOMContentLoaded', function() {
    const quillEditorContainer = document.getElementById('quill-editor');
    if (quillEditorContainer) {
        var quill = new Quill('#quill-editor', {
            theme: 'snow',
            placeholder: 'Write a message...',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, false] }],
                    ['bold', 'italic', 'underline'],
                    ['link'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['clean']
                ]
            }
        });
        document.querySelector('form').onsubmit = function() {
            var messageInput = document.querySelector('#message-input');
            messageInput.value = quill.root.innerHTML;
            return true;
        };
    }
    document.querySelectorAll('.activity-message').forEach(function(element) {
        element.innerHTML = element.innerHTML.replace(/<\/?p[^>]*>/g, '');
    });
    function scrollMessagesContainer(direction) {
        const scrollAmount = direction === 'up' ? -100 : 100;
        document.querySelector('.shout-messages').scrollBy({
            top: scrollAmount,
            behavior: 'smooth'
        });
    }

    const questSearchInput = document.getElementById('questSearchInput');
    if (questSearchInput) {
        questSearchInput.addEventListener('input', function () {
            const searchValue = this.value.toLowerCase();
            document.querySelectorAll('#questTableBody tr').forEach(row => {
            const title = row.querySelector('td:nth-child(1) button')
                            .textContent.toLowerCase();
            row.style.display = title.includes(searchValue) ? '' : 'none';
            });
        });
    }

    const questCategoryDropdown = document.getElementById('questCategoryDropdown');
    if (questCategoryDropdown) {
    questCategoryDropdown.addEventListener('change', filterQuests);
    }
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
document.addEventListener('DOMContentLoaded', () => {
  const searchBox   = document.getElementById('questSearchInput');
  const categorySel = document.getElementById('questCategoryDropdown');

  if (searchBox)   searchBox  .addEventListener('input',  filterQuests);
  if (categorySel) categorySel.addEventListener('change', filterQuests);
});

/* ---------------------------------------------------------
   Tab switching – scoped to the What’s-Happening widget
--------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  /* locate the widget once – prevents multiple event installs */
  const widget = document.querySelector('#whats-happening-step');
  if (!widget) return;                   // defensive

  const tabButtons  = widget.querySelectorAll('.wh-tab-button');
  const tabContents = widget.querySelectorAll('.wh-tab-content');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-wh-tab');

      /* reset only inside this widget */
      tabButtons .forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      /* activate the chosen tab */
      btn.classList.add('active');
      widget.querySelector(`#wh-${target}-tab`).classList.add('active');
    });
  });
});
