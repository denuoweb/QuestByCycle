import { openModal } from './modal_common.js';
import { showUserProfileModal } from './user_profile_modal.js';
import { showAllSubmissionsModal } from './all_submissions_modal.js';
import logger from '../logger.js';

let leaderboardData = null;
let leaderboardMetric = 'points';
let leaderboardBody;

export async function showLeaderboardModal(selectedGameId) {
    const leaderboardContent = document.getElementById('leaderboardModalContent');
    if (!leaderboardContent) {
        logger.error('Leaderboard modal content element not found. Cannot proceed with displaying leaderboard.');
        alert('Leaderboard modal content element not found. Please ensure the page has loaded completely and the correct ID is used.');
        return;
    }

    try {
        const resp = await fetch(`/leaderboard_partial?game_id=${selectedGameId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'
        });

        if (resp.redirected && resp.url.includes('/auth/login')) {
            window.location.href = resp.url;
            return;
        }

        if (resp.status === 401) {
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
            return;
        }

        if (!resp.ok) {
            throw new Error('Failed to fetch leaderboard data');
        }

        const contentType = resp.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            logger.error('Unexpected content type for leaderboard:', contentType);
            throw new Error('Invalid server response');
        }

        let data;
        try {
            data = await resp.json();
        } catch (e) {
            logger.error('Invalid JSON in leaderboard response', e);
            throw new Error('Invalid server response');
        }
        leaderboardContent.innerHTML = '';
        leaderboardData = data;
        leaderboardMetric = 'points';
        appendGameSelector(leaderboardContent, data, selectedGameId);
        appendCompletionMeter(leaderboardContent, data, selectedGameId);
        appendMetricToggle(leaderboardContent);
        appendSecondaryStatsList(leaderboardContent, data);
        appendLeaderboardTable(leaderboardContent);
        updateLeaderboardRows();
        openModal('leaderboardModal');
    } catch (error) {
        logger.error('Failed to load leaderboard:', error);
        alert('Failed to load leaderboard data. Please try again.');
    }
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

function appendMetricToggle(parentElement) {
    const toggleDiv = document.createElement('div');
    toggleDiv.className = 'form-check form-switch my-3';

    const toggleInput = document.createElement('input');
    toggleInput.className = 'form-check-input';
    toggleInput.type = 'checkbox';
    toggleInput.id = 'metricToggle';

    const toggleLabel = document.createElement('label');
    toggleLabel.className = 'form-check-label';
    toggleLabel.htmlFor = 'metricToggle';
    toggleLabel.textContent = 'Show Completed Quests';

    toggleInput.addEventListener('change', () => {
        leaderboardMetric = toggleInput.checked ? 'quests' : 'points';
        updateLeaderboardRows();
    });

    toggleDiv.appendChild(toggleInput);
    toggleDiv.appendChild(toggleLabel);
    parentElement.appendChild(toggleDiv);
}

function appendSecondaryStatsList(parentElement, data) {
    if (!data.secondary_stats || data.secondary_stats.length === 0) return;
    const list = document.createElement('ul');
    list.className = 'list-group my-3';
    data.secondary_stats.forEach(stat => {
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        item.textContent = stat.label;
        const val = document.createElement('span');
        val.className = 'badge bg-primary rounded-pill';
        val.textContent = stat.value;
        item.appendChild(val);
        list.appendChild(item);
    });
    parentElement.appendChild(list);
}

function appendLeaderboardTable(parentElement) {
    const table = document.createElement('table');
    table.className = 'table table-striped';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Rank', 'Player', 'Points', 'Badges'].forEach((text, idx) => {
        const th = document.createElement('th');
        if (idx === 2) {
            th.id = 'leaderboardMetricHeader';
        }
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    leaderboardBody = document.createElement('tbody');
    table.appendChild(leaderboardBody);
    parentElement.appendChild(table);
}

function appendTableCell(row, content, isLink = false, userId = null) {
    const cell = document.createElement('td');
    if (isLink) {
        const link = document.createElement('a');
        link.href = '#';
        link.onclick = (e) => {
            e.preventDefault();
            showUserProfileModal(userId);
        };
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

function updateLeaderboardRows() {
    if (!leaderboardData || !leaderboardBody) return;
    if (!leaderboardData.top_users || leaderboardData.top_users.length === 0) {
        leaderboardBody.innerHTML = '';
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = 'Join a game to see the leaderboard!';
        row.appendChild(cell);
        leaderboardBody.appendChild(row);
        return;
    }

    leaderboardBody.innerHTML = '';
    const header = document.getElementById('leaderboardMetricHeader');
    if (header) {
        header.textContent = leaderboardMetric === 'quests' ? 'Quests Completed' : 'Points';
    }

    const users = [...leaderboardData.top_users];
    users.sort((a, b) => {
        if (leaderboardMetric === 'quests') {
            return b.completed_quests - a.completed_quests;
        }
        return b.total_points - a.total_points;
    });

    users.forEach((user, index) => {
        const row = document.createElement('tr');
        appendTableCell(row, index + 1);
        const displayName = user.display_name || user.username;
        appendTableCell(row, displayName, true, user.user_id);
        const value = leaderboardMetric === 'quests' ? user.completed_quests : user.total_points;
        appendTableCell(row, value);
        appendTableCell(row, user.badges_awarded);
        leaderboardBody.appendChild(row);
    });
}



