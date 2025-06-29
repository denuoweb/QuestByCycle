import { openModal } from './modal_common.js';
import { csrfFetchJson } from '../utils.js';
import logger from '../logger.js';

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button[data-game-id]');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            openQuestCreationModal(this);
        });
    });

    function openQuestCreationModal(button) {
        const form = document.getElementById('questCreationForm');
        const gameId = button.getAttribute('data-game-id');

        if (form) {
            form.addEventListener('submit', function(event) {
                event.preventDefault();

                const questDescription = document.getElementById('questDescription').value;

                csrfFetchJson('/ai/generate_quest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: questDescription, game_id: gameId })
                })
                .then(({ json }) => {
                    const data = json;
                    if (data.generated_quest_html) {
                        document.getElementById('generatedQuestContent').innerHTML = data.generated_quest_html;

                        openModal('generateAIQuestModal');
                
                        const modalForm = document.getElementById('generateAIQuestModalForm');
                        if (modalForm) {
                            modalForm.setAttribute('data-game-id', gameId);
                        }
                        if (modalForm) {
                            // Add event listener for the form submission
                            modalForm.addEventListener('submit', function(e) {
                                e.preventDefault();
                                const formData = new FormData(modalForm);

                                csrfFetchJson('/ai/create_quest', {
                                    method: 'POST',
                                    body: formData
                                }).then(({ json }) => {
                                    window.location.href = '/';
                                    logger.log(json);
                                }).catch(error => {
                                    logger.error('Error:', error);
                                });
                            });
                        }

                        // Add the generate AI badge functionality
                        const generateAIImageBtn = document.getElementById('generateAIImage');
                        const badgeDescriptionInput = document.getElementById('badge_description');
                        const aiBadgeImage = document.getElementById('aiBadgeImage');
                        const aiBadgeFilenameInput = document.getElementById('aiBadgeFilename');
                    
                        if (!generateAIImageBtn || !badgeDescriptionInput || !aiBadgeImage || !aiBadgeFilenameInput) {
                            logger.error('One or more elements not found in the DOM');
                            return;
                        }
                    
                        generateAIImageBtn.addEventListener('click', function() {
                            logger.log('Generate AI Image button clicked');
                    
                            const badgeDescription = badgeDescriptionInput.value;
                            logger.log('Badge Description:', badgeDescription);
                    
                            if (!badgeDescription) {
                                alert('Please enter a badge description first.');
                                return;
                            }
                    
                            csrfFetchJson('/ai/generate_badge_image', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ badge_description: badgeDescription })
                            })
                            .then(({ json }) => {
                                logger.log('Response data:', json);
                                if (json.error) {
                                    alert('Error generating badge image: ' + json.error);
                                } else {
                                    const imageFilename = `${json.filename}`;
                                    const imageURL = `static/images/badge_images/${json.filename}`;
                                    aiBadgeImage.src = imageURL;
                                    aiBadgeImage.style.display = 'block';
                                    aiBadgeFilenameInput.value = imageFilename;
                                }
                            })
                            .catch(error => {
                                logger.error('Fetch error:', error);
                                alert('Error: ' + error);
                            });
                        });
                    }
                })
                .catch(error => {
                    alert('Error generating quest: ' + error.message);
                });
            });
        } else {
            logger.error('Form \'#questCreationForm\' not found.');
        }
    }
});

