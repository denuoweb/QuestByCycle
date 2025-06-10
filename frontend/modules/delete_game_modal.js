import { openModal } from './modal_common.js';
import logger from '../logger.js';

let deleteInterval;

export function openDeleteGameModal(gameId) {
  const modal = document.getElementById('deleteGameModal');
  const form  = document.getElementById('deleteGameForm');
  const input = document.getElementById('deleteGameConfirmInput');
  const countdown = document.getElementById('deleteGameCountdown');
  const timerSpan = document.getElementById('deleteGameTimer');
  const confirmBtn = document.getElementById('deleteGameConfirmBtn');

  if (!modal || !form || !input || !countdown || !timerSpan || !confirmBtn) {
    logger.warn('Delete game modal elements missing');
    return;
  }

  modal.dataset.gameId = gameId;
  form.action = `/games/delete_game/${gameId}`;
  input.value = '';
  confirmBtn.disabled = true;
  countdown.hidden = true;
  timerSpan.textContent = '5';
  openModal('deleteGameModal');
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('deleteGameConfirmInput');
  const confirmBtn = document.getElementById('deleteGameConfirmBtn');
  const countdown = document.getElementById('deleteGameCountdown');
  const timerSpan = document.getElementById('deleteGameTimer');
  const undoBtn = document.getElementById('deleteGameUndo');
  const form = document.getElementById('deleteGameForm');

  // If any of the required elements are missing, skip attaching
  if (!input || !confirmBtn || !countdown || !timerSpan || !undoBtn || !form) {
    return;
  }

  input.addEventListener('input', () => {
    confirmBtn.disabled = input.value.trim().toLowerCase() !== 'delete';
  });

  confirmBtn.addEventListener('click', () => {
    let seconds = 5;
    countdown.hidden = false;
    timerSpan.textContent = seconds.toString();
    deleteInterval = setInterval(() => {
      seconds -= 1;
      timerSpan.textContent = seconds.toString();
      if (seconds <= 0) {
        clearInterval(deleteInterval);
        form.submit();
      }
    }, 1000);
  });

  undoBtn.addEventListener('click', () => {
    clearInterval(deleteInterval);
    countdown.hidden = true;
    timerSpan.textContent = '5';
    input.value = '';
    confirmBtn.disabled = true;
  });
});

// Expose globally for inline handlers
window.openDeleteGameModal = openDeleteGameModal;

