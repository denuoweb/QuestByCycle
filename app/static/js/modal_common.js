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

function openRegisterModalWithOptions(options = {}) {
    // 1) rewrite the <form> action so a full‐page POST carries the same ?game_id…etc
    const form = document.getElementById('registerForm');
    const base = form.getAttribute('action').split('?')[0];
    const qs   = [];
    if (options.gameId)      qs.push(`game_id=${encodeURIComponent(options.gameId)}`);
    if (options.questId)     qs.push(`quest_id=${encodeURIComponent(options.questId)}`);
    if (options.next)        qs.push(`next=${encodeURIComponent(options.next)}`);
    if (options.showJoinCustom !== undefined) {
      qs.push(`show_join_custom=${encodeURIComponent(options.showJoinCustom)}`);
    }
    form.setAttribute('action', base + (qs.length ? `?${qs.join('&')}` : ''));
  
    // 2) mirror into the hidden inputs
    if (options.gameId       !== undefined) document.getElementById('registerGameId').value       = options.gameId;
    if (options.questId      !== undefined) document.getElementById('registerQuestId').value      = options.questId;
    if (options.next         !== undefined) document.getElementById('registerNext').value         = options.next;
    if (options.showJoinCustom !== undefined) document.getElementById('registerShowJoinCustom').value = options.showJoinCustom;
  
    // 3) swap modals
    closeModal('loginModal');
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

function openLoginModalWithGame({ gameId, questId = '' }) {
    const loginForm       = document.getElementById('loginForm');
    const loginGameId     = document.getElementById('loginGameId');
    const loginQuestId    = document.getElementById('loginQuestId');
    const loginNext       = document.getElementById('loginNext');
    const loginShowJoin   = document.getElementById('loginShowJoinCustom');
    // If you forward custom codes through login, add:
    // const loginCustomCode = document.getElementById('loginCustomGameCode');
  
    // 1) Build the “next” path so that after login we land back in game context
    const nextPath = `/?game_id=${encodeURIComponent(gameId)}&show_join_custom=0`;
  
    // 2) Set the hidden inputs so registerFromLogin() can read them
    loginGameId.value        = gameId;
    loginQuestId.value       = questId;
    loginShowJoin.value      = '0';
    loginNext.value          = nextPath;
    // loginCustomCode.value  = customCode; // if you need it
  
    // 3) Also embed them in the form’s action URL for non‐AJAX fallbacks
    const baseAction = loginForm.getAttribute('action').split('?')[0];
    const params     = new URLSearchParams({
      game_id:         gameId,
      quest_id:        questId,
      show_join_custom: 0,
      next:            nextPath
    });
    loginForm.setAttribute('action', `${baseAction}?${params.toString()}`);
  
    // 4) Finally, show the modal
    openModal('loginModal');
  }
  
  function registerFromLogin() {
    // Read from login modal
    const gameId    = document.getElementById('loginGameId').value    || '';
    const questId   = document.getElementById('loginQuestId').value   || '';
    const next      = document.getElementById('loginNext').value      || '';
    const showJoin  = document.getElementById('loginShowJoinCustom').value || '';
    const customCode = (document.getElementById('loginCustomGameCode') || {}).value || '';
  
    // Mirror into register modal’s hidden inputs
    document.getElementById('registerGameId').value         = gameId;
    document.getElementById('registerQuestId').value        = questId;
    document.getElementById('registerNext').value           = next;
    document.getElementById('registerShowJoinCustom').value = showJoin;
    document.getElementById('registerCustomGameCode').value = customCode;
  
    // Rebuild registerForm action URL
    const registerForm = document.getElementById('registerForm');
    const baseAction   = registerForm.getAttribute('action').split('?')[0];
    const params       = new URLSearchParams();
    if (gameId)     params.set('game_id',         gameId);
    if (questId)    params.set('quest_id',        questId);
    if (next)       params.set('next',            next);
    if (showJoin)   params.set('show_join_custom', showJoin);
    if (customCode) params.set('custom_game_code', customCode);
  
    registerForm.setAttribute('action', `${baseAction}?${params.toString()}`);
  
    // Swap modals
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

// --------------------------------------------------------
// Auto-open reset-password modal if URL contains show_reset=1 & token
// --------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);

    // Only trigger if show_reset=1 and a token is present
    if (params.get('show_reset') === '1') {
        const token = params.get('token');
        if (token) {
            // Open the reset modal, injecting the token
            openResetPasswordModal(token);

            // Optional: strip query params so the modal
            // does not re-open on reload / back-button.
            history.replaceState(
                null,
                '',
                window.location.pathname
            );
        } else {
            console.warn('show_reset=1 present but no token in URL');
        }
    }
});

// ────────────────────────────────────────────────────────────
// Auto-open the “Join Custom Game” modal if show_join_custom=1
// and there's no game_id in the URL.
// ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Debug: confirm this script runs
    console.log('modal_common: checking show_join_custom…', window.location.search);
    
    const params     = new URLSearchParams(window.location.search);
    const showJoin   = params.get('show_join_custom') === '1';
    const hasGameId  = params.has('game_id');
  
    if (showJoin && !hasGameId) {
      console.log('modal_common: opening joinCustomGameModal');
      openModal('joinCustomGameModal');
    }
  });
  
// ─────────────────────────────────────────────────────────────────
// Auto‐open the login modal for QR links like:
//   ?show_login=1&next=https://questbycycle.org/17
// and extract `17` as the gameId.
// ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const params    = new URLSearchParams(window.location.search);
  const showLogin = params.get('show_login') === '1';
  if (!showLogin) return;

  // 1. Try to read explicit game_id param
  let gameId = params.get('game_id') || '';

  // 2. If none, parse it out of `next` (e.g. /17)
  if (!gameId) {
    const rawNext = params.get('next');
    if (rawNext) {
      try {
        const parsed = new URL(rawNext, window.location.origin);
        const candidate = parsed.pathname.replace(/^\/+/, '');  // "17"
        if (/^\d+$/.test(candidate)) {
          gameId = candidate;
        }
      } catch (e) {
        console.warn('Failed to parse next URL for gameId:', e);
      }
    }
  }

  // 3. And now open the login modal *exactly* as if they had clicked your
  //    openLoginModalWithGame({ gameId: 17 }) link:
  openLoginModalWithGame({ gameId, questId: '' });
});

// ─────────────────────────────────────────────────────────────────
// If we loaded via /auth/login?next=https://…/NNN (or any ?next=…),
// automatically pop the login modal and join game NNN on submit.
// ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // We only want to do this for QR‐style links that don't go through index.
  // Check if URL path starts with "/auth/login"
  if (!window.location.pathname.startsWith('/auth/login')) {
    return;
  }

  const params    = new URLSearchParams(window.location.search);
  const rawNext   = params.get('next');
  if (!rawNext) {
    return;
  }

  let gameId = params.get('game_id') || '';

  // If game_id not explicit, parse it from next’s path: e.g. "/17"
  if (!gameId) {
    try {
      const parsed = new URL(rawNext, window.location.origin);
      const candidate = parsed.pathname.replace(/^\/+/, ''); // “17”
      if (/^\d+$/.test(candidate)) {
        gameId = candidate;
      }
    } catch (e) {
      console.warn('Could not parse next URL for gameId:', e);
    }
  }

  if (!gameId) {
    return;
  }

  // Now open the login modal just as if they clicked openLoginModalWithGame({gameId})
  openLoginModalWithGame({ gameId, questId: '' });
});
