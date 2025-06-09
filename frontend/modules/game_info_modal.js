function showGameInfoModal(gameId) {
    const url = '/games/game-info/' + gameId + '?modal=1';
    fetchAndShowModal(url, 'gameInfoModal');
}

// Expose the function globally so it can be called by inline onclick attributes.
window.showGameInfoModal = showGameInfoModal;

