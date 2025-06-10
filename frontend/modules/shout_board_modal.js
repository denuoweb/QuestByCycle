/* ------------------------------------------------------------------ */
/*  SHOUT‑BOARD ADMIN MODAL                                           */
/* ------------------------------------------------------------------ */
import { closeModal } from './modal_common.js';
document.addEventListener('DOMContentLoaded', () => {
  const modalId   = 'shoutBoardModal';
  const formEl    = document.getElementById('shoutBoardForm');
  const submitBtn = document.getElementById('shoutSubmitBtn');
  const messageInput = document.getElementById('shoutMessageInput');

  /* clear editor every time the modal opens */
  window.addEventListener('openModal', e => {
    if (e.detail === modalId && messageInput) messageInput.value = '';
  });

  /* ----------------------- handle submit ------------------------ */
  submitBtn.addEventListener('click', () => {
    const text = messageInput ? messageInput.value.trim() : '';
    if (!text) {
      alert('Please enter a message.');
      return;
    }
    if (text.length > 500) {
      alert('Message must be 500 characters or fewer.');
      return;
    }

    const data = new FormData(formEl);
    fetch(formEl.action, {
      method      : 'POST',
      body        : data,
      credentials : 'same-origin'
    })
      .then(r => {
        if (!r.ok) throw new Error(`Server responded ${r.status}`);
        return r.text();
      })
      .then(() => {
        closeModal(modalId);
        location.reload();
      })
      .catch(err => {
        console.error('Failed to post shout:', err);
        alert('Could not post. Please try again.');
      });
  });
});
