function showLeaderboardModal(selectedGameId) {
    const leaderboardContent = document.getElementById('leaderboardModalContent');
    if (!leaderboardContent) {
        console.error('Leaderboard modal content element not found. Cannot proceed with displaying leaderboard.');
        alert('Leaderboard modal content element not found. Please ensure the page has loaded completely and the correct ID is used.');
        return;
    }
    fetch('/leaderboard_partial?game_id=' + selectedGameId)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch leaderboard data');
            }
            return response.json();
        })
        .then(data => {
            leaderboardContent.innerHTML = '';
            appendGameSelector(leaderboardContent, data, selectedGameId);
            appendCompletionMeter(leaderboardContent, data, selectedGameId);
            appendLeaderboardTable(leaderboardContent, data);
            openModal('leaderboardModal');
        })
        .catch(error => {
            console.error('Failed to load leaderboard:', error);
            alert('Failed to load leaderboard data. Please try again.');
        });
}

function appendGameSelector(parentElement, data, selectedGameId) {
    if (data.games && data.games.length > 1) {
        const form = document.createElement('form');
        form.method = 'get';
        form.action = '#';  // Update with correct endpoint if needed

        const selectLabel = document.createElement('label');
        selectLabel.for = 'game_Select';
        selectLabel.textContent = 'Select Game:';
        form.appendChild(selectLabel);

        const select = document.createElement('select');
        select.name = 'game_id';
        select.id = 'game_Select';
        select.className = 'form-control';
        select.onchange = () => form.submit();  // Adjust as needed for actual use
        data.games.forEach(game => {
            const option = document.createElement('option');
            option.value = game.id;
            option.textContent = game.title;
            option.selected = (game.id === selectedGameId);
            select.appendChild(option);
        });
        form.appendChild(select);
        parentElement.appendChild(form);
    }
}

function appendLeaderboardTable(parentElement, data) {
    if (data.top_users && data.top_users.length > 0) {
        const table = document.createElement('table');
        table.className = 'table table-striped';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Rank', 'Player', 'Points'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        data.top_users.forEach((user, index) => {
            const row = document.createElement('tr');
            appendTableCell(row, index + 1);
            const displayName = user.display_name || user.username;  // Use display name or fallback to username
            appendTableCell(row, displayName, true, user.user_id);
            appendTableCell(row, user.total_points);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        parentElement.appendChild(table);
    } else {
        const p = document.createElement('p');
        p.textContent = 'Join a game to see the leaderboard!';
        parentElement.appendChild(p);
    }
}

function appendTableCell(row, content, isLink = false, userId = null) {
    const cell = document.createElement('td');
    if (isLink) {
        const link = document.createElement('a');
        link.href = "javascript:void(0)";
        link.onclick = () => showUserProfileModal(userId);
        link.textContent = content;
        cell.appendChild(link);
    } else {
        cell.textContent = content;
    }
    row.appendChild(cell);
}

function appendCompletionMeter(parentElement, data, selectedGameId) {
    if (data.total_game_points && data.game_goal) {
        const meterContainer = document.createElement('div');
        meterContainer.className = 'completion-meter-container';

        // Adding the inspirational text
        const inspirationalText = document.createElement('div');
        inspirationalText.className = 'inspirational-text';
        inspirationalText.textContent = 'It takes a village to enact change…';
        meterContainer.appendChild(inspirationalText);

        // Calculate remaining points and percentage reduction
        const remainingPoints = data.game_goal - data.total_game_points;
        const percentReduction = Math.min((data.total_game_points / data.game_goal) * 100, 100);

        const meterLabel = document.createElement('div');
        meterLabel.className = 'meter-label';
        meterLabel.textContent = `Carbon Reduction Points: ${data.total_game_points} / ${data.game_goal} (Remaining: ${remainingPoints})`;
        meterContainer.appendChild(meterLabel);

        const completionMeter = document.createElement('div');
        completionMeter.className = 'completion-meter';
        completionMeter.id = 'completionMeter'; // Added ID for targeting
        completionMeter.addEventListener('click', () => showAllSubmissionsModal(selectedGameId));

        const clickText = document.createElement('div');
        clickText.className = 'click-text';
        clickText.textContent = 'Click to view all game submissions!';
        completionMeter.appendChild(clickText);

        const meterBar = document.createElement('div');
        meterBar.className = 'meter-bar';
        meterBar.id = 'meterBar';
        meterBar.style.height = '0%';
        meterBar.style.opacity = '1'; // Set initial opacity to 1 (0% transparent)
        meterBar.dataset.label = `${percentReduction.toFixed(1)}% Reduced`;
        completionMeter.appendChild(meterBar);

        meterContainer.appendChild(completionMeter);
        parentElement.appendChild(meterContainer);

        setTimeout(() => {
            meterBar.style.height = `${percentReduction}%`;
            meterBar.style.opacity = `${1 - percentReduction / 100}`; // Update opacity based on percent reduction
            updateMeterBackground(percentReduction, selectedGameId);
        }, 100);
    }
}


function updateMeterBackground(percent, selectedGameId) {
    const completionMeter = document.getElementById('completionMeter');
    const imageIndex = 9 - Math.min(Math.floor(percent / 10), 9); // Invert the index for the clearest image at 100%
    completionMeter.style.backgroundImage = `url('/static/images/leaderboard/smoggy_skyline_${selectedGameId}_${imageIndex}.png')`;
}
