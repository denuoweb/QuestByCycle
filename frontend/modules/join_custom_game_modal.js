document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('#customGameList .list-group-item').forEach(function (item) {
        item.addEventListener('click', function () {
            const code = this.getAttribute('data-game-code');
            if (confirm('Do you want to join ‘' + this.textContent.trim() + '’?')) {
                document.getElementById('customGameCodeInput').value = code;
                document.getElementById('joinCustomGameForm').submit();
            }
        });
    });

    const modalEl = document.getElementById('joinCustomGameModal');
    const hasJoined = modalEl.dataset.hasJoined === "1";
    const joinDemoUrl = modalEl.dataset.joinDemoUrl;

    let joinedCustomGame = false;
    document.getElementById('joinCustomGameForm')
        .addEventListener('submit', () => { joinedCustomGame = true; });

    modalEl.addEventListener('hidden.bs.modal', function () {
        if (!joinedCustomGame && !hasJoined) {
            window.location.href = joinDemoUrl;
        }
    });
});

export {};
