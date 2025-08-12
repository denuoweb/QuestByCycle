import { fetchJson, csrfFetchJson } from '../utils.js';
import logger from '../logger.js';

    let game_Id = null;
    const VerificationTypes = {
        qr_code: 'QR Code',
        photo: 'Photo Upload',
        comment: 'Comment',
        photo_comment: 'Photo Upload and Comment',
        video: 'Video Upload'
    };

    const BadgeOptions = {
        none: 'No Badge (points only)',
        individual: 'Individual Badge',
        category: 'Category Badge',
        both: 'Both Individual and Category'
    };

    let badges = [];  // Define badges globally

    function initManageQuests() {
        const gameEl = document.getElementById('game_Data');
        if (!gameEl) {
            return;
        }
        game_Id = gameEl.dataset.gameId;

        const delBtn = document.getElementById('deleteAllQuestsBtn');
        if (delBtn) delBtn.addEventListener('click', deleteAllQuests);

        const importBtn = document.getElementById('importQuestsBtn');
        if (importBtn) importBtn.addEventListener('click', importQuests);

        loadBadges().then(() => loadQuests(game_Id));
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initManageQuests);
    } else {
        initManageQuests();
    }

    async function loadBadges() {
        try {
            const response = await fetch('/badges');
            if (!response.ok) throw new Error('Failed to fetch badges');
            const data = await response.json();
            badges = data.badges || [];
        } catch (error) {
            logger.error('Error fetching badges:', error);
        }
    }


    function editQuest(questId) {
        const card = document.querySelector(`#quest-${questId}`);
        const originalData = {};

        card.querySelectorAll('.editable').forEach(field => {
            originalData[field.getAttribute('data-name')] = field.innerHTML;
        });

        processVerification(card);
        processFrequency(card);
        processBadge(card);
        processBadgeOption(card);
        processEditableFields(card);
        setupEditAndCancelButtons(card, questId, originalData);
    }

    function deleteAllQuests() {
        // First confirmation pop-up
        if (confirm('Are you sure you want to delete all quests? This action cannot be undone.')) {
            
            // Fetch the game title before showing the second confirmation pop-up
            fetchJson(`/quests/game/${game_Id}/get_title`)
            .then(({ json: data }) => {
                const gameTitle = data.title;
                
                // Second confirmation pop-up with game title
                if (confirm(`This will delete all quests for the game: "${gameTitle}". Are you absolutely sure? This action cannot be undone.`)) {
                    // Proceed with deletion if the user confirms
                    csrfFetchJson(`/quests/game/${game_Id}/delete_all`, { method: 'DELETE' })
                    .then(({ json: data }) => {
                        if (data.success) {
                            alert('All quests deleted successfully');
                            loadQuests(game_Id);
                        } else {
                            alert(`Failed to delete quests: ${data.message}`);
                        }
                    })
                    .catch(error => {
                        logger.error('Error:', error);
                        alert('Failed to delete all quests. Please check the console for more details.');
                    });
                }
            })
            .catch(error => {
                logger.error('Error fetching game title:', error);
                alert('Failed to fetch game title. Please check the console for more details.');
            });
        }
    }

    function processVerification(card) {
        const verificationElement = card.querySelector('.editable[data-name="verification_type"]');
        const currentVerificationType = verificationElement.getAttribute('data-value').toLowerCase();

        let verificationTypeSelectHTML = '<select name="verification_type" class="editable-select">';
        Object.entries(VerificationTypes).forEach(([key, display]) => {
            const isSelected = (currentVerificationType === key.toLowerCase()) ? 'selected' : '';
            verificationTypeSelectHTML += `<option value="${key}" ${isSelected}>${display}</option>`;
        });
        verificationTypeSelectHTML += '</select>';
        verificationElement.innerHTML = verificationTypeSelectHTML;
    }

    function processFrequency(card) {
        const frequencyElement = card.querySelector('.editable[data-name="frequency"]');
        const currentFrequencyValue = frequencyElement.getAttribute('data-value').toLowerCase();
        let frequencySelectHTML = '<select name="frequency" class="editable-select">';
        const frequencyOptions = {
            daily: 'Daily',
            weekly: 'Weekly',
            monthly: 'Monthly',
        };
        Object.entries(frequencyOptions).forEach(([key, display]) => {
            const isSelected = (currentFrequencyValue === key.toLowerCase()) ? 'selected' : '';
            frequencySelectHTML += `<option value="${key}" ${isSelected}>${display}</option>`;
        });
        frequencySelectHTML += '</select>';
        frequencyElement.innerHTML = frequencySelectHTML;
    }

    function processBadgeOption(card) {
        const optionElement = card.querySelector('.editable[data-name="badge_option"]');
        const currentOption = optionElement.getAttribute('data-value') || optionElement.innerText.trim();
        let optionSelectHTML = '<select name="badge_option" class="editable-select">';
        Object.entries(BadgeOptions).forEach(([key, label]) => {
            const selected = (currentOption === key) ? 'selected' : '';
            optionSelectHTML += `<option value="${key}" ${selected}>${label}</option>`;
        });
        optionSelectHTML += '</select>';
        optionElement.innerHTML = optionSelectHTML;

        const badgeSelect = card.querySelector('select[name="badge_id"]');
        const optionSelect = optionElement.querySelector('select');

        function toggleBadge() {
            if (['none', 'category'].includes(optionSelect.value)) {
                badgeSelect.value = '';
                badgeSelect.disabled = true;
            } else {
                badgeSelect.disabled = false;
            }
        }

        if (badgeSelect) {
            toggleBadge();
            optionSelect.addEventListener('change', toggleBadge);
        }
    }

    function processBadge(card) {
        const badgeCell = card.querySelector('.editable[data-name="badge_name"]');
        let currentBadgeName = badgeCell.innerText.trim();
        let badgeSelectHTML = '<select name="badge_id" class="editable-select"><option value="">None</option>';
        badges.forEach(badge => {
            const isSelected = (currentBadgeName === badge.name) ? 'selected' : '';
            badgeSelectHTML += `<option value="${badge.id}" ${isSelected}>${badge.name}</option>`;
        });
        badgeSelectHTML += '</select>';
        badgeCell.innerHTML = badgeSelectHTML;
    }

    function processEditableFields(card) {
        const editableFields = [
            { name: 'title', type: 'text' },
            { name: 'description', type: 'textarea' },
            { name: 'tips', type: 'textarea' },
            { name: 'points', type: 'number' },
            { name: 'badge_awarded', type: 'number' },
            { name: 'completion_limit', type: 'number' },
            { name: 'category', type: 'text' },
            { name: 'enabled', type: 'select', options: ['Yes', 'No'] },
            { name: 'is_sponsored', type: 'select', options: ['Yes', 'No'] },
        ];

        editableFields.forEach(field => {
            const cell = card.querySelector(`.editable[data-name="${field.name}"]`);
            if (!cell) return;
            updateEditableField(cell, field);
        });
    }

    function updateEditableField(cell, field) {
        let currentValue = cell.getAttribute('data-value') || cell.textContent.trim();
        let inputElement;

        if (field.type === 'select') {
            inputElement = document.createElement('select');
            inputElement.name = field.name;
            field.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.text = option;
                if (currentValue === optionElement.text) {
                    optionElement.selected = true;
                }
                inputElement.appendChild(optionElement);
            });
        } else if (field.type === 'textarea') {
            inputElement = document.createElement('textarea');
            inputElement.name = field.name;
            inputElement.value = currentValue;
        } else {
            inputElement = document.createElement('input');
            inputElement.type = field.type;
            inputElement.name = field.name;
            inputElement.value = currentValue;
        }
        cell.innerHTML = '';
        cell.appendChild(inputElement);

        // Textareas handle editing for description and tips
    }

    function setupEditAndCancelButtons(card, questId, originalData) {
        const editButton = card.querySelector('.edit-button');
        editButton.innerText = 'Save';
        editButton.onclick = () => saveQuest(questId);

        const cancelButton = document.createElement('button');
        cancelButton.innerText = 'Cancel';
        cancelButton.className = 'btn btn-secondary ms-2 cancel-button';
        cancelButton.onclick = () => {
            cancelEditQuest(card, originalData, editButton, questId);
        };

        editButton.parentNode.insertBefore(cancelButton, editButton.nextSibling);
    }

    function cancelEditQuest(card, originalData, editButton, questId) {
        Object.entries(originalData).forEach(([name, html]) => {
            const cell = card.querySelector(`.editable[data-name="${name}"]`);
            if (cell) {
                cell.innerHTML = html;
            }
        });

        editButton.innerText = 'Edit';
        editButton.onclick = () => editQuest(questId);
        card.querySelector('.cancel-button').remove();
    }

    function saveQuest(questId) {
        const card = document.querySelector(`#quest-${questId}`);
        let questData = {};

        card.querySelectorAll('input, select, textarea').forEach(input => {
            let value = input.value;
            if (typeof value === 'string') {
                value = value.trim();
            }
            if (input.name === 'enabled') {
                value = input.value === 'Yes';
            } else if (input.name === 'is_sponsored') {
                value = input.value === 'Yes';
            } else if (input.name === 'badge_id' && value === '') {
                value = null;
            }

            questData[input.name] = value;
        });



        csrfFetchJson(`/quests/quest/${questId}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(questData),
        })
        .then(({ json }) => {
            if (json.success) {
                alert('Quest updated successfully.');
                loadQuests(game_Id);
            } else {
                alert('Failed to update quest. Error: ' + json.message);
            }
        })
        .catch(error => {
            logger.error('Error updating quest:', error);
            alert('Error updating quest. Please check console for details.');
        });
    }

    function loadQuests(game_Id) {
        fetchJson(`/quests/game/${game_Id}/quests`)
        .then(({ json: data }) => {
            const questsBody = document.getElementById('questsBody');
            questsBody.innerHTML = '';

            data.quests.forEach(quest => {
                const card = document.createElement('div');
                card.className = 'card';
                card.id = `quest-${quest.id}`;

                const verificationTypeText = quest.verification_type.toLowerCase();
                const badgeName = quest.badge_name || 'None';
                const frequencyDisplayText = quest.frequency || 'Not Set';
                const categoryText = quest.category || 'Not Set';
                const badgeAwarded = quest.badge_awarded || 'Not Set';
                const badgeOptionText = BadgeOptions[quest.badge_option] || quest.badge_option;

                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title editable" data-name="title">${quest.title}</h5>
                        <div class="card-text editable" data-name="description">${quest.description}</div>
                        <div class="card-text editable" data-name="tips">${quest.tips || ''}</div>
                        <p class="card-text"><strong>Points:</strong> <span class="editable" data-name="points">${quest.points}</span></p>
                        <p class="card-text"><strong>Completion Limit:</strong> <span class="editable" data-name="completion_limit">${quest.completion_limit}</span></p>
                        <p class="card-text"><strong>Enabled:</strong> <span class="editable" data-name="enabled">${quest.enabled ? 'Yes' : 'No'}</span></p>
                        <p class="card-text"><strong>Pinned:</strong> <span class="editable" data-name="is_sponsored">${quest.is_sponsored ? 'Yes' : 'No'}</span></p>
                        <p class="card-text"><strong>Verification:</strong> <span class="editable" data-name="verification_type" data-value="${quest.verification_type}">${verificationTypeText}</span></p>
                        <p class="card-text"><strong>Badge:</strong> <span class="editable" data-name="badge_name">${badgeName}</span></p>
                        <p class="card-text"><strong>Badge Awarded:</strong> <span class="editable" data-name="badge_awarded">${badgeAwarded}</span></p>
                        <p class="card-text"><strong>Badge Option:</strong> <span class="editable"
                            data-name="badge_option" data-value="${quest.badge_option}">${badgeOptionText}</span></p>
                        <p class="card-text"><strong>Frequency:</strong> <span class="editable" data-name="frequency" data-value="${quest.frequency}">${frequencyDisplayText}</span></p>
                        <p class="card-text"><strong>Category:</strong> <span class="editable" data-name="category">${categoryText}</span></p>
                        <p class="card-text"><strong>Quest ID:</strong> ${quest.id}</p>
                        <p class="card-text"><strong>Game ID:</strong> ${quest.game_id}</p>
                        <p class="card-text"><strong>Badge ID:</strong> ${quest.badge_id ?? 'N/A'}</p>
                        <div class="d-flex justify-content-between">
                            <button class="btn btn-warning edit-button" data-quest-id="${quest.id}">Edit</button>
                            <button class="btn btn-danger delete-button" data-quest-id="${quest.id}">Delete</button>
                            <button class="btn btn-info qr-button" data-quest-id="${quest.id}">Generate QR Code</button>
                        </div>
                    </div>
                `;

                questsBody.appendChild(card);

                const editBtn = card.querySelector('.edit-button');
                const delBtn = card.querySelector('.delete-button');
                const qrBtn = card.querySelector('.qr-button');

                if (editBtn) editBtn.addEventListener('click', () => editQuest(quest.id));
                if (delBtn) delBtn.addEventListener('click', () => deleteQuest(quest.id));
                if (qrBtn) qrBtn.addEventListener('click', () => generateQRCode(quest.id));
            });

        })
        .catch(error => logger.error('Failed to load quests:', error));
    }

    function deleteQuest(questId) {
        csrfFetchJson(`/quests/quest/${questId}/delete`, { method: 'DELETE' })
        .then(({ json }) => {
            if (json.success) {
                alert('Quest deleted successfully');
                loadQuests(game_Id);
            } else {
                alert(`Failed to delete quest: ${json.message}`);
            }
        })
        .catch(error => {
            logger.error('Error:', error);
            alert('Failed to delete quest. Please check the console for more details.');
        });
    }

    function importQuests() {
        const form = document.getElementById('importQuestsForm');
        const formData = new FormData(form);

        csrfFetchJson(`/quests/game/${game_Id}/import_quests`, {
            method: 'POST',
            body: formData
        })
        .then(({ json }) => {
            if (json.success && json.redirectUrl) {
                alert('Quests imported successfully');
                loadQuests(game_Id);
            } else {
                alert('Failed to import quests: ' + json.message);
            }
        })
        .catch(error => {
            logger.error('Error importing quests:', error);
        });
    }

    function generateQRCode(questId) {
        const url = `/quests/generate_qr/${questId}`;

        fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Failed to generate QR code');
            return response.blob();
        })
        .then(blob => {
            const imageFilename = URL.createObjectURL(blob);
            window.open(imageFilename, '_blank');
        })
        .catch(error => {
            logger.error('Error generating QR code:', error);
            alert('Failed to generate QR code. Please check console for more details.');
        });
    }




