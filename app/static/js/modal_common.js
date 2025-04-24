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
        
        const ev = new CustomEvent('hidden.bs.modal', { bubbles: true });
        modal.dispatchEvent(ev);
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
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
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

function handleGameSelection(selectElement) {
    const selectedValue = selectElement.value;

    // Open the "Join Custom Game" modal if selected
    if (selectedValue === 'join_custom_game') {
        openModal('joinCustomGameModal');
    } else {
        window.location.href = selectedValue;
    }
}

function openLoginModalWithGame({ gameId, questId }) {
    const loginModal = document.getElementById('loginModal');
    const loginForm  = document.getElementById('loginForm');
  
    // 1) Reset the action to bare "/auth/login"
    const baseAction = loginForm.getAttribute('action').split('?')[0];
    loginForm.setAttribute('action', baseAction);
  
    // 2) Fill the hidden inputs
    loginModal.querySelector('input[name="game_id"]').value  = gameId;
    loginModal.querySelector('input[name="quest_id"]').value = questId || '';
  
    // 3) Build the `next` URL so after a successful POST to /auth/login
    //    Flask will redirect back to your index with show_join_custom=0.
    const nextUrl = `/` +
                    `?game_id=${encodeURIComponent(gameId)}` +
                    `&show_join_custom=0`;
    loginModal.querySelector('input[name="next"]').value = nextUrl;
  
    // 4) Finally show the modal
    openModal('loginModal');
  }
  
  
function registerFromLogin() {
    // 1) Grab the values from the login modal:
    const emailVal = document.getElementById('loginEmail')?.value || '';
    const gameId   = document.getElementById('loginGameId')?.value  || '';
    const questId  = document.getElementById('loginQuestId')?.value || '';
    const nextVal  = document.getElementById('loginNext')?.value    || '';
  
    // 2) Inject them into the Register modal:
    document.getElementById('registerEmail').value    = emailVal;
    document.getElementById('gameIdField').value      = gameId;
    document.getElementById('questIdField').value     = questId;
    document.getElementById('nextField').value        = nextVal;
  
    // 3) Switch modals:
    closeModal('loginModal');
    openModal('registerModal');
  
    // 4) (Optional) move focus into the password field:
    document.querySelector('#registerModal input[type="password"]').focus();
  }

function switchToRegisterModal(options = {}) {
    // 1) update the URL on the <form> itself:
    const frm = document
        .getElementById('registerModal')
        .querySelector('form');
    const base = frm.getAttribute('action').split('?')[0];
    const qs = [];
    if (options.gameId)  qs.push(`game_id=${encodeURIComponent(options.gameId)}`);
    if (options.questId) qs.push(`quest_id=${encodeURIComponent(options.questId)}`);
    if (options.next)    qs.push(`next=${encodeURIComponent(options.next)}`);
    frm.setAttribute('action', base + (qs.length ? `?${qs.join('&')}` : ''));
    
    if (options.gameId !== undefined) {
        const gameField = document.getElementById('gameIdField');
        if (gameField) {
            gameField.value = options.gameId;
        }
    }
    if (options.questId !== undefined) {
        const questField = document.getElementById('questIdField');
        if (questField) {
            questField.value = options.questId;
        }
    }
    if (options.next !== undefined) {
        const nextField = document.getElementById('nextField');
        if (nextField) {
            nextField.value = options.next;
        }
    }
    closeModal('loginModal');
    openModal('registerModal');
}

// Call this to show the Forgot Password modal and pre-fill its email
function openForgotPasswordModal() {
    const loginEmailVal   = document.getElementById('loginEmail')?.value || '';
    const forgotEmailInput = document.getElementById('forgotEmail');
    if (forgotEmailInput) {
        forgotEmailInput.value = loginEmailVal;
    }
    const emailErr   = document.getElementById('forgotEmailError');
    const successDiv = document.getElementById('forgotSuccess');
    const btn        = document.getElementById('forgotButton');
    if (emailErr)   emailErr.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
    if (btn)        btn.disabled = false;

    openModal('forgotPasswordModal');
}

// Opens the Reset-Password modal, injecting the token from the URL
function openResetPasswordModal(token) {
    const form    = document.getElementById('resetForm');
    const input   = document.getElementById('resetToken');
    // Read the base action URL that Flask already rendered
    const baseUrl = form.dataset.baseAction;   // e.g. "/auth/reset_password/"
  
    // Append the token to it—no hard-coded "/reset_password/"
    form.setAttribute('action', baseUrl + encodeURIComponent(token));
    // Keep the hidden field in sync (for POST bodies if you prefer)
    input.value = token;
  
    // Clear previous errors/success & re-enable button
    document.getElementById('resetError').style.display   = 'none';
    document.getElementById('resetSuccess').style.display = 'none';
    document.getElementById('resetButton').disabled        = false;
  
    // Finally, open the modal
    openModal('resetPasswordModal');
  }
  