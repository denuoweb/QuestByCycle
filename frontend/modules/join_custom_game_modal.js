document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('joinCustomGameModal');
    if (!modalEl) return;

    document.querySelectorAll('#customGameList .list-group-item').forEach(function (item) {
        item.addEventListener('click', function () {
            const code = this.getAttribute('data-game-code');
            if (confirm('Do you want to join ‘' + this.textContent.trim() + '’?')) {
                document.getElementById('customGameCodeInput').value = code;
                document.getElementById('joinCustomGameForm').submit();
            }
        });
    });
    const hasAnyGames = modalEl.dataset.hasAnyGames === '1';
    const joinDemoUrl = modalEl.dataset.joinDemoUrl;

    let joinedCustomGame = false;
    document.getElementById('joinCustomGameForm')
        .addEventListener('submit', () => { joinedCustomGame = true; });

    modalEl.addEventListener('hidden.bs.modal', function () {
        // Only auto-join the demo if the user has no games at all.
        if (!joinedCustomGame && !hasAnyGames) {
            window.location.href = joinDemoUrl;
        }
    });
});
