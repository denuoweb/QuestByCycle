import { initQuill } from './quill_common.js';
/* ------------------------------------------------------------------ */
/*  SHOUT‑BOARD ADMIN MODAL                                           */
/* ------------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', () => {
  const modalId   = 'shoutBoardModal';
  const formEl    = document.getElementById('shoutBoardForm');
  const submitBtn = document.getElementById('shoutSubmitBtn');
  let quill = null;

  /* -------------------- initialise Quill once -------------------- */
  if (window.Quill) {
    quill = initQuill('#shoutQuillEditor', '#shoutMessageInput', {
      placeholder: 'Write an announcement…'
    });
  } else {
    console.error('Quill library not found  shoutboard editor will not work.');
  }

  /* clear editor every time the modal opens */
  window.addEventListener('openModal', e => {
    if (e.detail !== modalId) return;
    if (quill) quill.setText('');
  });

  /* ----------------------- handle submit ------------------------ */
  submitBtn.addEventListener('click', () => {
    if (!quill) {
      alert('Editor not ready  please refresh.');
      return;
    }

    const html = quill.root.innerHTML.trim();
    if (html === '' || html === '<p><br></p>') {
      alert('Please enter a message.');
      return;
    }

    const plainText = quill.getText().trim();
    if (plainText.length > 500) {
      alert('Message must be 500 characters or fewer.');
      return;
    }

    document.getElementById('shoutMessageInput').value = html;

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
