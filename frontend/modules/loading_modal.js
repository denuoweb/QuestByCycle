import logger from '../logger.js';
import { openModal, closeModal } from './modal_common.js';

let visibleCount = 0;
let autoHideTimer = null;

function setStatus(text) {
  const el = document.getElementById('loadingStatus');
  if (el && typeof text === 'string') el.textContent = text;
}

export function showLoadingModal(statusText = null) {
  if (statusText) setStatus(statusText);
  if (visibleCount === 0) {
    logger.debug('Showing loading modal');
    openModal('loadingModal');
  }
  visibleCount += 1;
  if (autoHideTimer) clearTimeout(autoHideTimer);
  // Safety: auto-close after 30s to prevent stuck overlay
  autoHideTimer = setTimeout(() => {
    logger.warn('Loading modal auto-hide triggered after timeout.');
    visibleCount = 0;
    closeModal('loadingModal');
  }, 30000);
}

export function hideLoadingModal() {
  if (visibleCount > 0) visibleCount -= 1;
  if (visibleCount === 0) {
    logger.debug('Hiding loading modal');
    if (autoHideTimer) {
      clearTimeout(autoHideTimer);
      autoHideTimer = null;
    }
    closeModal('loadingModal');
  }
}

export function updateLoadingStatus(text) {
  setStatus(text);
}
