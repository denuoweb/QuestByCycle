import { openModal } from './modal_common.js';

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
                const csrfToken = document.querySelector('[name=csrf_token]').value;

                fetch('/ai/generate_quest', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ description: questDescription, game_id: gameId })
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => Promise.reject({
                            status: response.status,
                            statusText: response.statusText,
                            errorMessage: data.error
                        }));
                    }
                    return response.json();
                })
                .then(data => {
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
                                const csrfToken = document.querySelector('[name=csrf_token]').value;
                
                                fetch(`/ai/create_quest`, {
                                    method: 'POST',
                                    headers: {
                                        'X-CSRFToken': csrfToken
                                    },
                                    body: formData
                                }).then(response => response.json())
                                .then(result => {
                                    // Handle the response here
                                    window.location.href = '/';

                                    console.log(result);
                                }).catch(error => {
                                    console.error('Error:', error);
                                });
                            });
                        }

                        // Add the generate AI badge functionality
                        const generateAIImageBtn = document.getElementById('generateAIImage');
                        const badgeDescriptionInput = document.getElementById('badge_description');
                        const aiBadgeImage = document.getElementById('aiBadgeImage');
                        const aiBadgeFilenameInput = document.getElementById('aiBadgeFilename');
                    
                        if (!generateAIImageBtn || !badgeDescriptionInput || !aiBadgeImage || !aiBadgeFilenameInput) {
                            console.error("One or more elements not found in the DOM");
                            return;
                        }
                    
                        generateAIImageBtn.addEventListener('click', function() {
                            console.log("Generate AI Image button clicked");
                    
                            const badgeDescription = badgeDescriptionInput.value;
                            console.log("Badge Description:", badgeDescription);
                    
                            if (!badgeDescription) {
                                alert('Please enter a badge description first.');
                                return;
                            }
                    
                            fetch('/ai/generate_badge_image', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                                },
                                body: JSON.stringify({ badge_description: badgeDescription })
                            })
                            .then(response => response.json())
                            .then(data => {
                                console.log("Response data:", data);
                                if (data.error) {
                                    alert('Error generating badge image: ' + data.error);
                                } else {
                                    const imageFilename = `${data.filename}`;
                                    const imageURL = `static/images/badge_images/${data.filename}`;
                                    aiBadgeImage.src = imageURL;
                                    aiBadgeImage.style.display = 'block';
                                    aiBadgeFilenameInput.value = imageFilename;
                                }
                            })
                            .catch(error => {
                                console.error('Fetch error:', error);
                                alert('Error: ' + error);
                            });
                        });
                    }
                })
                .catch(error => {
                    alert('Error generating quest: ' + (error.errorMessage || error.statusText));
                });
            });
        } else {
            console.error("Form '#questCreationForm' not found.");
        }
    }
});

