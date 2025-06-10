import logger from '../logger.js';

export function showLoadingModal() {
    logger.debug('Showing loading modal');
    document.getElementById('loadingModal').style.display = 'flex';
}

export function hideLoadingModal() {
    logger.debug('Hiding loading modal');
    document.getElementById('loadingModal').style.display = 'none';
}

