// Quest detail modal management functions
function openQuestDetailModal(questId) {
    resetModalContent();

    // Show flash messages in the modal
    const flashMessagesContainer = document.getElementById('flash-messages-data');
    const modalFlashContainer = document.getElementById('modal-flash-messages');
    if (flashMessagesContainer && modalFlashContainer) {
        modalFlashContainer.innerHTML = flashMessagesContainer.innerHTML;
    }

    fetch(`/quests/detail/${questId}/user_completion`)
        .then(response => response.json())
        .then(data => {
            const { quest, userCompletion, canVerify, nextEligibleTime } = data;
            if (!populateQuestDetails(quest, userCompletion.completions, canVerify, questId, nextEligibleTime)) {
                console.error('Error: Required elements are missing to populate quest details.');
                return;
            }
            ensureDynamicElementsExistAndPopulate(data.quest, data.userCompletion.completions, data.nextEligibleTime, data.canVerify);

            fetchSubmissions(questId);
            //lazyLoadImages(); // Ensure lazy loading is initialized after populating the content
            openModal('questDetailModal');
        })
        .catch(error => {
            console.error('Error opening quest detail modal:', error);
            alert('Sign in to view quest details.');
        });
}

function lazyLoadImages() {
    const images = document.querySelectorAll('img.lazyload');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');  // Load image by replacing 'data-src' with 'src'
                img.classList.remove('lazyload');
                observer.unobserve(img);  // Stop observing once the image is loaded
            }
        });
    });

    images.forEach(img => {
        imageObserver.observe(img);
    });
}

function populateQuestDetails(quest, userCompletionCount, canVerify, questId, nextEligibleTime) {
    const completeText = userCompletionCount >= quest.completion_limit ? " - complete" : "";
    const elements = {
        'modalQuestTitle': document.getElementById('modalQuestTitle'),
        'modalQuestDescription': document.getElementById('modalQuestDescription'),
        'modalQuestTips': document.getElementById('modalQuestTips'),
        'modalQuestPoints': document.getElementById('modalQuestPoints'),
        'modalQuestCompletionLimit': document.getElementById('modalQuestCompletionLimit'),
        'modalQuestBadgeAwarded': document.getElementById('modalQuestBadgeAwarded'),
        'modalQuestCategory': document.getElementById('modalQuestCategory'),
        'modalQuestVerificationType': document.getElementById('modalQuestVerificationType'),
        'modalQuestBadgeImage': document.getElementById('modalQuestBadgeImage'),
        'modalQuestCompletions': document.getElementById('modalQuestCompletions'),
        'modalCountdown': document.getElementById('modalCountdown')
    };

    // Ensure all required elements exist
    for (let key in elements) {
        if (!elements[key]) {
            console.error(`Error: Missing element ${key}`);
            return false;
        }
    }

    // Update text content for elements
    elements['modalQuestTitle'].innerText = `${quest.title}${completeText}`;
    elements['modalQuestDescription'].innerHTML = quest.description;
    elements['modalQuestTips'].innerHTML = quest.tips || 'No tips available';
    elements['modalQuestPoints'].innerText = `${quest.points}`;
    elements['modalQuestCategory'].innerText = quest.category || 'No category set';
    
    const completionText = quest.completion_limit > 1 ? `${quest.completion_limit} times` : `${quest.completion_limit} time`;
    elements['modalQuestCompletionLimit'].innerText = `${completionText} ${quest.frequency}`;


    const completionTextAward = quest.badge_awarded > 1 ? `${quest.badge_awarded} times` : `${quest.badge_awarded} time`;
    if (quest.badge_awarded != null) {
        elements['modalQuestBadgeAwarded'].innerText = `After ${completionTextAward}`;
    } else {
        elements['modalQuestBadgeAwarded'].innerText = 'No badge awarded';
    }
    switch (quest.verification_type) {
        case 'photo_comment':
            elements['modalQuestVerificationType'].innerText = "Must upload a photo and a comment to earn points!";
            break;
        case 'photo':
            elements['modalQuestVerificationType'].innerText = "Must upload a photo to earn points!";
            break;
        case 'comment':
            elements['modalQuestVerificationType'].innerText = "Must upload a comment to earn points!";
            break;
        case 'qr_code':
            elements['modalQuestVerificationType'].innerText = "Find the QR code and post a photo to earn points!";
            break;
        default:
            elements['modalQuestVerificationType'].innerText = 'Not specified';
            break;
    }

    const badgeImagePath = quest.badge && quest.badge.image ? `/static/images/badge_images/${quest.badge.image}` : '/static/images/badge_images/default_badge.png';
    elements['modalQuestBadgeImage'].src = badgeImagePath;
    elements['modalQuestBadgeImage'].alt = quest.badge && quest.badge.name ? `Badge: ${quest.badge.name}` : 'Default Badge';

    elements['modalQuestCompletions'].innerText = `Total Completions: ${userCompletionCount}`;

    const nextAvailableTime = nextEligibleTime && new Date(nextEligibleTime);
    if (!canVerify && nextAvailableTime && nextAvailableTime > new Date()) {
        elements['modalCountdown'].innerText = `Next eligible time: ${nextAvailableTime.toLocaleString()}`;
        elements['modalCountdown'].style.color = 'red';
    } else {
        elements['modalCountdown'].innerText = "You are currently eligible to verify!";
        elements['modalCountdown'].style.color = 'green';
    }

    manageVerificationSection(questId, canVerify, quest.verification_type, nextEligibleTime);
    return true;
}

function ensureDynamicElementsExistAndPopulate(quest, userCompletionCount, nextEligibleTime, canVerify) {
    const parentElement = document.querySelector('.user-quest-data'); // Target the parent element correctly.

    // Define IDs and initial values for dynamic elements.
    const dynamicElements = [
        { id: 'modalQuestCompletions', value: `${userCompletionCount || 0}` },
        { id: 'modalCountdown', value: "" } // Will be updated based on conditions
    ];

    dynamicElements.forEach(elem => {
        let element = document.getElementById(elem.id);
        if (!element) {
            element = document.createElement('p');
            element.id = elem.id;
            parentElement.appendChild(element);
        }
        element.innerText = elem.value;
    });

    // Update the countdown only if necessary.
    updateCountdownElement(document.getElementById('modalCountdown'), nextEligibleTime, canVerify);
}

function updateCountdownElement(countdownElement, nextEligibleTime, canVerify) {
    if (!canVerify && nextEligibleTime) {
        const nextTime = new Date(nextEligibleTime);
        const now = new Date();
        if (nextTime > now) {
            const timeDiffMs = nextTime - now;
            countdownElement.innerText = `Next eligible time: ${formatTimeDiff(timeDiffMs)}`;
        } else {
            countdownElement.innerText = "You are currently eligible to verify!";
        }
    } else {
        countdownElement.innerText = "You are currently eligible to verify!";
    }
}

function formatTimeDiff(ms) {
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / (1000 * 60)) % 60);
    const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
    const days = Math.floor(ms / (1000 * 60 * 60 * 24));
    return `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

// Quest detail modal verification functions
const userToken = localStorage.getItem('userToken');
const currentUserId = localStorage.getItem('current_user_id');

// Function to manage the dynamic creation and adjustment of the verification form
function manageVerificationSection(questId, canVerify, verificationType, nextEligibleTime) {
    const userQuestData = document.querySelector('.user-quest-data');
    userQuestData.innerHTML = '';

    if (canVerify) {
        const verifyForm = document.createElement('div');
        verifyForm.id = `verifyQuestForm-${questId}`;
        verifyForm.className = 'verify-quest-form';
        verifyForm.style.display = 'block'; // Show by default

        // Ensure verificationType is correctly passed and utilized
        const formHTML = getVerificationFormHTML(verificationType.trim().toLowerCase());
        verifyForm.innerHTML = formHTML;
        userQuestData.appendChild(verifyForm);

        setupSubmissionForm(questId);
    }

    console.log("Next Eligible Time:", nextEligibleTime);
    console.log("Can Verify:", canVerify);
    console.log("Countdown Element:", document.getElementById('modalCountdown'));
}

function getVerificationFormHTML(verificationType) {
    let formHTML = '<form enctype="multipart/form-data" class="epic-form">';

    // Insert the centered header for verifying the quest
    formHTML += '<h2 style="text-align: center;">Verify Your Quest</h2>';

    // Explicitly handle each case
    switch (verificationType) {
        case 'photo':
            formHTML += `
                <div class="form-group">
                    <label for="image" class="epic-label">Upload a Photo</label>
                    <input type="file" id="image" name="image" class="epic-input" accept="image/*" required>
                </div>
                <div class="form-group">
                    <button type="submit" class="epic-button">Submit Verification</button>
                </div>`;
            break;
        case 'comment':
            formHTML += `
                <div class="form-group">
                    <label for="verificationComment" class="epic-label">Enter a Comment</label>
                    <textarea id="verificationComment" name="verificationComment" class="epic-textarea" placeholder="Enter a comment..." required></textarea>
                </div>
                <div class="form-group">
                    <button type="submit" class="epic-button">Submit Verification</button>
                </div>`;
            break;
        case 'photo_comment':
            formHTML += `
                <div class="form-group">
                    <label for="image" class="epic-label">Upload a Photo</label>
                    <input type="file" id="image" name="image" class="epic-input" accept="image/*" required>
                </div>
                <div class="form-group">
                    <label for="verificationComment" class="epic-label">Enter a Comment</label>
                    <textarea id="verificationComment" name="verificationComment" class="epic-textarea" placeholder="Enter a comment..." required></textarea>
                </div>
                <div class="form-group">
                    <button type="submit" class="epic-button">Submit Verification</button>
                </div>`;
            break;
        case 'qr_code':
            formHTML += `<p class="epic-message">Find and scan the QR code. No submission required here.</p>`;
            // No button is added for QR code case
            break;
        case 'pause':
            formHTML += `<p class="epic-message">Quest is currently paused.</p>`;
            // No button is added for pause case
            break;
        default:
            // Handle cases where no verification is needed or provide a default case
            formHTML += '<p class="epic-message">Submission Requirements not set correctly.</p>';
            break;
    }

    formHTML += '</form>';
    return formHTML;
}

// Toggle the display of the verification form
function toggleVerificationForm(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    verifyForm.style.display = verifyForm.style.display === 'none' ? 'block' : 'none';
}

// Setup submission form with event listener
function setupSubmissionForm(questId) {
    const submissionForm = document.getElementById(`verifyQuestForm-${questId}`);
    if (submissionForm) {
        submissionForm.addEventListener('submit', function(event) {
            showLoadingModal();
            submitQuestDetails(event, questId);
        });
    } else {
        console.error("Form not found for quest ID:", questId);
    }
}

// Define verifyQuest function to handle verification form toggling
function verifyQuest(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    if (verifyForm.style.display === 'none' || verifyForm.style.display === '') {
        verifyForm.style.display = 'block';  // Show the form
    } else {
        verifyForm.style.display = 'none';  // Hide the form
    }
}

function updateTwitterLink(url) {
    const twitterLink = document.getElementById('twitter-link');
    if (twitterLink) {
        console.debug('Twitter link element found, setting href:', url);
        twitterLink.href = url;
        twitterLink.style.display = 'block';
    } else {
        console.debug('Twitter link element not found');
    }
}

function setTwitterLink(url) {
    const twitterLink = document.getElementById('twitterLink');
    if (twitterLink) {
        if (url) {
            twitterLink.href = url;  // Set the href attribute with the received Twitter URL
            twitterLink.textContent = 'Link to Twitter';  // Optional: Update button text if necessary
        } else {
            twitterLink.href = '#';  // Reset or provide a fallback URL
            twitterLink.textContent = 'Link Unavailable';  // Handle cases where the URL isn't available
        }
    }
}

function updateFacebookLink(url) {
    const facebookLink = document.getElementById('facebook-link');
    if (facebookLink) {
        console.debug('Facebook link element found, setting href:', url);
        facebookLink.href = url;
        facebookLink.style.display = 'block';
    } else {
        console.debug('Facebook link element not found');
    }
}

function setFacebookLink(url) {
    const facebookLink = document.getElementById('facebookLink');
    if (facebookLink) {
        if (url) {
            facebookLink.href = url;  // Set the href attribute with the received FB URL
            facebookLink.textContent = 'Link to Facebook';  // Optional: Update button text if necessary
        } else {
            facebookLink.href = '#';  // Reset or provide a fallback URL
            facebookLink.textContent = 'Link Unavailable';  // Handle cases where the URL isn't available
        }
    }
}

function updateInstagramLink(url) {
    const instagramLink = document.getElementById('instagram-link');
    if (instagramLink) {
        console.debug('Instagram link element found, setting href:', url);
        instagramLink.href = url;
        instagramLink.style.display = 'block';
    } else {
        console.debug('Instagram link element not found');
    }
}

function setInstagramLink(url) {
    const instagramLink = document.getElementById('instagramLink');
    if (instagramLink) {
        if (url) {
            instagramLink.href = url;  // Set the href attribute with the received Instagram URL
            instagramLink.textContent = 'Link to Instagram';  // Optional: Update button text if necessary
        } else {
            instagramLink.href = '#';  // Reset or provide a fallback URL
            instagramLink.textContent = 'Link Unavailable';  // Handle cases where the URL isn't available
        }
    }
}

// Handle Quest Submissions with streamlined logic
let isSubmitting = false;

function submitQuestDetails(event, questId) {
    event.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const form = event.target;
    const formData = new FormData(form);
    formData.append('user_id', currentUserId); // Add user_id to form data
    formData.append('sid', socket.id); // Add sid to form data

    console.debug('Submitting form with data:', formData);

    showLoadingModal(); // Show the loading modal

    fetch(`/quests/quest/${questId}/submit`, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => {
        hideLoadingModal(); // Hide the loading modal upon receiving the response
        if (!response.ok) {
            if (response.status === 403) {
                // Handle the specific case where the game is out of date
                return response.json().then(data => {
                    if (data.message === 'This quest cannot be completed outside of the game dates') {
                        throw new Error('The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu.');
                    }
                    throw new Error(data.message || `Server responded with status ${response.status}`);
                });
            }
            throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.debug('Response data:', data);

        if (!data.success) {
            throw new Error(data.message);
        }
        if (data.total_points) {
            const totalPointsElement = document.getElementById('total-points');
            if (totalPointsElement) {
                console.debug('Updating total points:', data.total_points);
                totalPointsElement.innerText = `Total Completed Points: ${data.total_points}`;
            }
        }
        if (data.twitter_url) {
            console.debug('Updating Twitter link:', data.twitter_url);
            updateTwitterLink(data.twitter_url);
        }
        if (data.fb_url) {
            console.debug('Updating Facebook link:', data.fb_url);
            updateFacebookLink(data.fb_url);
        }
        if (data.instagram_url) {
            console.debug('Updating Instagram link:', data.instagram_url);
            updateInstagramLink(data.instagram_url);
        }
        openQuestDetailModal(questId);
        form.reset();
    })
    .catch(error => {
        hideLoadingModal(); // Ensure the loading modal is hidden on error
        console.error("Submission error:", error);
        if (error.message === 'The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu.') {
            alert('The game has ended, and you can no longer submit quests for this game. Join a new game in the game dropdown menu.');
        } else {
            alert('Error during submission: ' + error.message);
        }
    })
    .finally(() => {
        isSubmitting = false;
    });
}

// Fetch and Display Submissions
function fetchSubmissions(questId) {
    fetch(`/quests/quest/${questId}/submissions`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${userToken}`, // Assuming Bearer token is used
                'Content-Type': 'application/json'
            },
            credentials: 'include' // For cookies, this might be necessary
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            return response.json();
        })
        .then(submissions => {
            console.debug('Fetched submissions:', submissions);

            const twitterLink = document.getElementById('twitterLink');
            const facebookLink = document.getElementById('facebookLink');
            const instagramLink = document.getElementById('instagramLink');

            if (submissions && submissions.length > 0) {
                const submission = submissions[0];
                const submissionImage = document.getElementById('submissionImage');
                const submissionComment = document.getElementById('submissionComment');
                const submissionProfileLink = document.getElementById('submissionProfileLink');
                const downloadLink = document.getElementById('downloadLink');

                submissionImage.src = submission.image_url || 'image/placeholdersubmission.png';
                submissionComment.textContent = submission.comment || 'No comment provided.';
                submissionProfileLink.href = `/user/profile/${submission.user_id}`;
                downloadLink.href = submission.image_url || '#';
                downloadLink.download = `SubmissionImage-${submission.user_id}`;

                if (submission.twitter_url && submission.twitter_url.trim() !== '') {
                    twitterLink.href = submission.twitter_url;
                    twitterLink.style.display = 'inline';
                } else {
                    twitterLink.style.display = 'none';
                }

                if (submission.fb_url && submission.fb_url.trim() !== '') {
                    facebookLink.href = submission.fb_url;
                    facebookLink.style.display = 'inline';
                } else {
                    facebookLink.style.display = 'none';
                }

                if (submission.instagram_url && submission.instagram_url.trim() !== '') {
                    instagramLink.href = submission.instagram_url;
                    instagramLink.style.display = 'inline';
                } else {
                    instagramLink.style.display = 'none';
                }

            } else {
                twitterLink.style.display = 'none';
                facebookLink.style.display = 'none';
                instagramLink.style.display = 'none';

            }

            const images = submissions.reverse().map(submission => ({
                url: submission.image_url,
                alt: "Submission Image",
                comment: submission.comment,
                user_id: submission.user_id,
                twitter_url: submission.twitter_url,
                fb_url: submission.fb_url,
                instagram_url: submission.instagram_url,

            }));
            distributeImages(images);
        })
        .catch(error => {
            console.error('Failed to fetch submissions:', error.message);
            alert('Could not load submissions. Please try again.');
        });
}

// Function to check if a URL is a valid image URL
function isValidImageUrl(url) {
    if (!url) {
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    try {
        if (url.startsWith("/")) {
            // Allow relative paths that start with '/'
            return true;
        }
        const parsedUrl = new URL(url);
        // Check the URL scheme to make sure it's HTTP or HTTPS only
        if (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") {
            // Allow only URLs ending in common image extensions (e.g., .jpg, .png, etc.)
            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
            return allowedExtensions.some(ext => parsedUrl.pathname.toLowerCase().endsWith(ext));
        }
    } catch (e) {
        // If the URL constructor throws, the URL is invalid
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    return false;
}

function distributeImages(images) {
    const board = document.getElementById('submissionBoard');
    board.innerHTML = ''; // Clear existing content

    // Get and validate the fallback URL from the DOM
    let fallbackUrl = document.getElementById('questDetailModal').getAttribute('data-placeholder-url');
    if (!fallbackUrl) {
        console.warn("No fallback URL provided in data-placeholder-url attribute.");
        // Set a default fallback image URL if none is provided
        fallbackUrl = '/static/images/default-placeholder.webp'; // Update to a valid placeholder image path if available
    }

    const validFallbackUrl = isValidImageUrl(fallbackUrl) ? fallbackUrl : '';
    if (!validFallbackUrl) {
        console.warn("Fallback URL is not valid.");
    }

    images.forEach(image => {
        const img = document.createElement('img');
        
        let finalImageUrl = '';
        if (isValidImageUrl(image.url)) {
            finalImageUrl = image.url;  // Assign the validated URL directly
        } else if (validFallbackUrl) {
            // Use the validated fallback URL if image.url is invalid
            finalImageUrl = validFallbackUrl;
        }

        // Log the image URL being used
        console.log(`Using image URL: ${finalImageUrl}`);
        img.src = finalImageUrl;

        img.alt = "Loaded Image";

        // Set onerror to use the fallback URL if the image fails to load
        img.onerror = () => {
            console.warn(`Image failed to load, using fallback: ${validFallbackUrl}`);
            if (validFallbackUrl) {
                img.src = validFallbackUrl;
            }
        };

        img.onclick = () => {
            console.log("Image clicked:", finalImageUrl);
            showSubmissionDetail(image);
        };
        img.style.margin = '10px'; // Add some margin between images if needed
        board.appendChild(img); // Append directly to the board
    });
}
