document.getElementById('gameFilter')?.addEventListener('change', function () {
  const gameId = this.value;
  if (gameId) {
      window.location.href = `/admin/user_management/game/${encodeURIComponent(gameId)}`;
  } else {
    window.location.href = '/admin/user_management';
  }
});

