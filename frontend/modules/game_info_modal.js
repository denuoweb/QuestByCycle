import { fetchAndShowModal } from './modal_common.js';

export function showGameInfoModal(gameId) {
    const url = '/games/game-info/' + gameId + '?modal=1';
    fetchAndShowModal(url, 'gameInfoModal');
}


