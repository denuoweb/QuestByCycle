let topZIndex = 1050; // Start with a base z-index for the first modal

// Common modal management functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        topZIndex += 10; // Increment z-index for stacking
        modal.style.zIndex = topZIndex; // Apply the new z-index to the modal
        modal.style.display = 'block';
        document.body.classList.add('body-no-scroll'); // Optional: prevent scrolling when modal is open
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';

        // Decrement z-index to allow stacking of previous modals
        topZIndex -= 10;

        // Restore scrolling if no modals are open
        const openModals = document.querySelectorAll('.modal[style*="display: block"]');
        if (openModals.length === 0) {
            document.body.classList.remove('body-no-scroll');
        }
    }
}

// Reset all modal content and settings to the initial state
function resetModalContent() {
    const twitterLink = document.getElementById('twitterLink');
    if (twitterLink) {
        twitterLink.style.display = 'none';
        twitterLink.href = '#'; // Reset to default or placeholder link
    }

    const facebookLink = document.getElementById('facebookLink');
    if (facebookLink) {
        facebookLink.style.display = 'none';
        facebookLink.href = '#'; // Reset to default or placeholder link
    }

    const instagramLink = document.getElementById('instagramLink');
    if (instagramLink) {
        instagramLink.style.display = 'none';
        instagramLink.href = '#'; // Reset to default or placeholder link
    }

    const modalQuestActions = document.getElementById('modalQuestActions');
    if (modalQuestActions) {
        modalQuestActions.innerHTML = '';
    }
    document.querySelectorAll('[id^="verifyButton-"]').forEach(button => button.remove());
    document.querySelectorAll('[id^="verifyQuestForm-"]').forEach(form => form.remove());
    document.body.classList.remove('body-no-scroll');
}

function updateModalHiddenFields(modalId, options) {
    // options is an object e.g., { gameId: 1, questId: 2, next: '/somepath' }
    // Find the modal element.
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Update hidden fields if they exist.
    if (options.gameId !== undefined) {
        const gameField = modal.querySelector('input[name="game_id"]');
        if (gameField) {
            gameField.value = options.gameId;
        }
    }
    if (options.questId !== undefined) {
        const questField = modal.querySelector('input[name="quest_id"]');
        if (questField) {
            questField.value = options.questId;
        }
    }
    if (options.next !== undefined) {
        const nextField = modal.querySelector('input[name="next"]');
        if (nextField) {
            nextField.value = options.next;
        }
    }
}

function openLoginModalWithOptions(options) {
    updateModalHiddenFields('loginModal', options);
    openModal('loginModal');
}

function openRegisterModalWithOptions(options) {
    updateModalHiddenFields('registerModal', options);
    openModal('registerModal');
}

function openLoginModalWithGame(options) {
    const loginModal = document.getElementById('loginModal');
    const loginForm = loginModal.querySelector('form');
    
    // Optionally, update the form action itself if needed:
    const baseLoginUrl = "{{ url_for('auth.login') }}";
    // Create a query string using the passed options.
    const params = [];
    if (options.gameId) {
        params.push("game_id=" + encodeURIComponent(options.gameId));
    }
    if (options.questId) {
        params.push("quest_id=" + encodeURIComponent(options.questId));
    }
    if (options.next) {
        params.push("next=" + encodeURIComponent(options.next));
    }
    const newActionUrl = baseLoginUrl + (params.length ? "?" + params.join("&") : "");
    loginForm.setAttribute('action', newActionUrl);

    openModal("loginModal");
}

function switchToRegisterModal(options = {}) {
    // Update hidden fields on the register modal if they exist.
    if (options.gameId !== undefined) {
        const gameField = document.getElementById('gameIdField');
        if (gameField) gameField.value = options.gameId;
    }
    if (options.questId !== undefined) {
        const questField = document.getElementById('questIdField');
        if (questField) questField.value = options.questId;
    }
    if (options.next !== undefined) {
        const nextField = document.getElementById('nextField');
        if (nextField) nextField.value = options.next;
    }
    
    // Close the login modal and open the register modal.
    closeModal('loginModal');
    openModal('registerModal');
}
