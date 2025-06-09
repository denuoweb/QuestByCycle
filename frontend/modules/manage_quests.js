import { initQuill } from './quill_common.js';
    const game_Id = document.getElementById('game_Data').dataset.gameId;
    const VerificationTypes = {
        qr_code: "QR Code",
        photo: "Photo Upload",
        comment: "Comment",
        photo_comment: "Photo Upload and Comment",
        video: "Video Upload"
    };

    let badges = [];  // Define badges globally

    document.addEventListener('DOMContentLoaded', async function() {
        await loadBadges();
        loadQuests(game_Id);
    });

    async function loadBadges() {
        try {
            const response = await fetch('/badges');
            if (!response.ok) throw new Error('Failed to fetch badges');
            const data = await response.json();
            badges = data.badges || [];
        } catch (error) {
            console.error('Error fetching badges:', error);
        }
    }

    function addQuest() {
        const formData = new FormData(document.getElementById('addQuestForm'));
        fetch(`/quests/game/${game_Id}/add_quest`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': getCSRFToken(),
                'Accept': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Quest added successfully.');
                loadQuests(game_Id);
            } else {
                alert('Failed to add quest');
            }
        })
        .catch(error => console.error('Error:', error));
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
        processEditableFields(card, originalData);
        setupEditAndCancelButtons(card, questId, originalData);

        initializeQuillEditors(card);
    }

    function deleteAllQuests() {
        // First confirmation pop-up
        if (confirm('Are you sure you want to delete all quests? This action cannot be undone.')) {
            
            // Fetch the game title before showing the second confirmation pop-up
            fetch(`/quests/game/${game_Id}/get_title`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch game title');
                return response.json();
            })
            .then(data => {
                const gameTitle = data.title;
                
                // Second confirmation pop-up with game title
                if (confirm(`This will delete all quests for the game: "${gameTitle}". Are you absolutely sure? This action cannot be undone.`)) {
                    // Proceed with deletion if the user confirms
                    fetch(`/quests/game/${game_Id}/delete_all`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRF-Token': getCSRFToken(),
                            'Accept': 'application/json',
                        },
                    })
                    .then(response => {
                        if (!response.ok) throw new Error('Failed to delete all quests');
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            alert('All quests deleted successfully');
                            loadQuests(game_Id);
                        } else {
                            alert(`Failed to delete quests: ${data.message}`);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Failed to delete all quests. Please check the console for more details.');
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching game title:', error);
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
            daily: "Daily",
            weekly: "Weekly",
            monthly: "Monthly",
        };
        Object.entries(frequencyOptions).forEach(([key, display]) => {
            const isSelected = (currentFrequencyValue === key.toLowerCase()) ? 'selected' : '';
            frequencySelectHTML += `<option value="${key}" ${isSelected}>${display}</option>`;
        });
        frequencySelectHTML += '</select>';
        frequencyElement.innerHTML = frequencySelectHTML;
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

    function processEditableFields(card, originalData) {
        const editableFields = [
            { name: "title", type: "text" },
            { name: "description", type: "textarea" },
            { name: "tips", type: "textarea" },
            { name: "points", type: "number" },
            { name: "badge_awarded", type: "number" },
            { name: "completion_limit", type: "number" },
            { name: "category", type: "text" },
            { name: "enabled", type: "select", options: ["Yes", "No"] },
            { name: "is_sponsored", type: "select", options: ["Yes", "No"] },
        ];

        editableFields.forEach(field => {
            const cell = card.querySelector(`.editable[data-name="${field.name}"]`);
            if (!cell) return;
            updateEditableField(cell, field);
        });
    }

    function updateEditableField(cell, field) {
        let currentValue = cell.getAttribute('data-value') || cell.innerHTML.trim();
        let inputElement;

        if (field.type === "select") {
            inputElement = document.createElement("select");
            inputElement.name = field.name;
            field.options.forEach(option => {
                const optionElement = document.createElement("option");
                optionElement.value = option;
                optionElement.text = option;
                if (currentValue === optionElement.text) {
                    optionElement.selected = true;
                }
                inputElement.appendChild(optionElement);
            });
        } else if (field.type === "textarea") {
            inputElement = document.createElement("textarea");
            inputElement.name = field.name;
            inputElement.value = currentValue;
        } else {
            inputElement = document.createElement("input");
            inputElement.type = field.type;
            inputElement.name = field.name;
            inputElement.value = currentValue;
        }
        cell.innerHTML = '';
        cell.appendChild(inputElement);

        // Initialize Quill editor for description and tips
        if (field.name === "description" || field.name === "tips") {
            const editor = document.createElement('div');
            editor.className = 'quill-editor';
            cell.innerHTML = '';
            cell.appendChild(editor);
            
            const quill = initQuill(editor);

            quill.root.innerHTML = currentValue;
            cell.__quill = quill;
        }
    }

    function setupEditAndCancelButtons(card, questId, originalData) {
        const editButton = card.querySelector(".edit-button");
        editButton.innerText = "Save";
        editButton.onclick = () => saveQuest(questId);

        const cancelButton = document.createElement("button");
        cancelButton.innerText = "Cancel";
        cancelButton.className = "btn btn-secondary ms-2 cancel-button";
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

        editButton.innerText = "Edit";
        editButton.onclick = () => editQuest(questId);
        card.querySelector(".cancel-button").remove();
    }

    function saveQuest(questId) {
        const card = document.querySelector(`#quest-${questId}`);
        let questData = {};

        card.querySelectorAll('input, select, textarea').forEach(input => {
            let value = input.value;
            if (input.name === 'enabled') {
                value = input.value === 'Yes';
            } else if (input.name === 'is_sponsored') {
                value = input.value === 'Yes';
            } else if (input.name === 'badge_id' && value === '') {
                value = null;
            }

            questData[input.name] = value;
        });

        // Get the Quill editor contents
        const descriptionEditor = card.querySelector('.quill-editor-container[data-name="description"]').__quill;
        const tipsEditor = card.querySelector('.quill-editor-container[data-name="tips"]').__quill;

        const descriptionContent = descriptionEditor.root.innerHTML.trim();
        const tipsContent = tipsEditor.root.innerHTML.trim();

        // Add the Quill editor contents to questData
        questData['description'] = descriptionContent;
        questData['tips'] = tipsContent;

        fetch(`/quests/quest/${questId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCSRFToken(),
            },
            body: JSON.stringify(questData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Quest updated successfully.');
                loadQuests(game_Id);
            } else {
                alert('Failed to update quest. Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error updating quest:', error);
            alert('Error updating quest. Please check console for details.');
        });
    }

    function loadQuests(game_Id) {
        fetch(`/quests/game/${game_Id}/quests`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json'}
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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

                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title editable" data-name="title">${quest.title}</h5>
                        <div class="card-text editable quill-editor-container" data-name="description">${quest.description}</div>
                        <div class="card-text editable quill-editor-container" data-name="tips">${quest.tips || ''}</div>
                        <p class="card-text"><strong>Points:</strong> <span class="editable" data-name="points">${quest.points}</span></p>
                        <p class="card-text"><strong>Completion Limit:</strong> <span class="editable" data-name="completion_limit">${quest.completion_limit}</span></p>
                        <p class="card-text"><strong>Enabled:</strong> <span class="editable" data-name="enabled">${quest.enabled ? 'Yes' : 'No'}</span></p>
                        <p class="card-text"><strong>Pinned:</strong> <span class="editable" data-name="is_sponsored">${quest.is_sponsored ? 'Yes' : 'No'}</span></p>
                        <p class="card-text"><strong>Verification:</strong> <span class="editable" data-name="verification_type" data-value="${quest.verification_type}">${verificationTypeText}</span></p>
                        <p class="card-text"><strong>Badge:</strong> <span class="editable" data-name="badge_name">${badgeName}</span></p>
                        <p class="card-text"><strong>Badge Awarded:</strong> <span class="editable" data-name="badge_awarded">${badgeAwarded}</span></p>
                        <p class="card-text"><strong>Frequency:</strong> <span class="editable" data-name="frequency" data-value="${quest.frequency}">${frequencyDisplayText}</span></p>
                        <p class="card-text"><strong>Category:</strong> <span class="editable" data-name="category">${categoryText}</span></p>
                        <div class="d-flex justify-content-between">
                            <button class="btn btn-warning edit-button" onclick="editQuest(${quest.id})">Edit</button>
                            <button class="btn btn-danger" onclick="deleteQuest(${quest.id})">Delete</button>
                            <button class="btn btn-info" onclick="window.location.href = '/quests/generate_qr/${quest.id}'">Generate QR Code</button>
                        </div>
                    </div>
                `;

                questsBody.appendChild(card);
            });

            initializeQuillEditors();
        })
        .catch(error => console.error('Failed to load quests:', error));
    }

    function deleteQuest(questId) {
        fetch(`/quests/quest/${questId}/delete`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-Token': getCSRFToken(),
                'Accept': 'application/json',
            },
        })
        .then(response => {
            if (!response.ok) throw new Error('Failed to delete quest');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Quest deleted successfully');
                loadQuests(game_Id);
            } else {
                alert(`Failed to delete quest: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete quest. Please check the console for more details.');
        });
    }

    function importQuests() {
        const form = document.getElementById('importQuestsForm');
        const formData = new FormData(form);

        fetch(`/quests/game/${game_Id}/import_quests`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': getCSRFToken(),
                'Accept': 'application/json',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.redirectUrl) {
                alert('Quests imported successfully');
                loadQuests(game_Id);
            } else {
                alert('Failed to import quests: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error importing quests:', error);
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
            console.error('Error generating QR code:', error);
            alert('Failed to generate QR code. Please check console for more details.');
        });
    }

    function initializeQuillEditors(card) {
        if (card) {
            const descriptionEditorContainer = card.querySelector('.quill-editor-container[data-name="description"]');
            const tipsEditorContainer = card.querySelector('.quill-editor-container[data-name="tips"]');

            if (descriptionEditorContainer && !descriptionEditorContainer.__quill) {
                const quillDescription = initQuill(descriptionEditorContainer);
                descriptionEditorContainer.__quill = quillDescription;
            }

            if (tipsEditorContainer && !tipsEditorContainer.__quill) {
                const quillTips = initQuill(tipsEditorContainer);
                tipsEditorContainer.__quill = quillTips;
            }
        }
    }


