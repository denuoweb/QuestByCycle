function openQuestDetailModal(questId) {
    resetModalContent();

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
                img.src = img.getAttribute('data-src');
                img.classList.remove('lazyload');
                observer.unobserve(img);
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

    for (let key in elements) {
        if (!elements[key]) {
            console.error(`Error: Missing element ${key}`);
            return false;
        }
    }

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
    const parentElement = document.querySelector('.user-quest-data');

    const dynamicElements = [
        { id: 'modalQuestCompletions', value: `${userCompletionCount || 0}` },
        { id: 'modalCountdown', value: "" }
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

const userToken = localStorage.getItem('userToken');
window.currentUserId = Number(localStorage.getItem('current_user_id') || 0);

function manageVerificationSection(questId, canVerify, verificationType, nextEligibleTime) {
    const userQuestData = document.querySelector('.user-quest-data');
    userQuestData.innerHTML = '';

    if (canVerify) {
        const verifyForm = document.createElement('div');
        verifyForm.id = `verifyQuestForm-${questId}`;
        verifyForm.className = 'verify-quest-form';
        verifyForm.style.display = 'block';

        const formHTML = getVerificationFormHTML(verificationType.trim().toLowerCase());
        verifyForm.innerHTML = formHTML;
        userQuestData.appendChild(verifyForm);

        setupSubmissionForm(questId);
    }
}

function getVerificationFormHTML(verificationType) {
    let formHTML = '<form enctype="multipart/form-data" class="epic-form">';

    formHTML += '<h2 style="text-align: center;">Verify Your Quest</h2>';

    switch (verificationType) {
        case 'photo':
            formHTML += `
                <div class="form-group">
                    <label for="image" class="epic-label">Upload a Photo</label>
                    <input type="file" id="image" name="image" class="epic-input" accept="image/*" required>
                </div>
                <div class="form-group">
                    <button type="submit>Submit Verification</button>
                </div>`;
            break;
        case 'comment':
            formHTML += `
                <div class="form-group">
                    <label for="verificationComment" class="epic-label">Enter a Comment</label>
                    <textarea id="verificationComment" name="verificationComment" class="epic-textarea" placeholder="Enter a comment..." required></textarea>
                </div>
                <div class="form-group">
                    <button type="submit">Submit Verification</button>
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
                    <button type="submit"">Submit Verification</button>
                </div>`;
            break;
        case 'qr_code':
            formHTML += `<p class="epic-message">Find and scan the QR code. No submission required here.</p>`;
            break;
        case 'pause':
            formHTML += `<p class="epic-message">Quest is currently paused.</p>`;
            break;
        default:
            formHTML += '<p class="epic-message">Submission Requirements not set correctly.</p>';
            break;
    }

    formHTML += '</form>';
    return formHTML;
}

function toggleVerificationForm(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    verifyForm.style.display = verifyForm.style.display === 'none' ? 'block' : 'none';
}

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

function verifyQuest(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    if (verifyForm.style.display === 'none' || verifyForm.style.display === '') {
        verifyForm.style.display = 'block';
    } else {
        verifyForm.style.display = 'none';
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
            twitterLink.href = url;
            twitterLink.textContent = 'Link to Twitter';
        } else {
            twitterLink.href = '#';
            twitterLink.textContent = 'Link Unavailable';
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
            facebookLink.href = url;
            facebookLink.textContent = 'Link to Facebook';
        } else {
            facebookLink.href = '#';
            facebookLink.textContent = 'Link Unavailable';
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
            instagramLink.href = url;
            instagramLink.textContent = 'Link to Instagram';
        } else {
            instagramLink.href = '#';
            instagramLink.textContent = 'Link Unavailable';
        }
    }
}

let isSubmitting = false;

function submitQuestDetails(event, questId) {
    event.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const form = event.target;
    const formData = new FormData(form);
    formData.append('user_id', currentUserId);
    formData.append('sid', socket.id);

    console.debug('Submitting form with data:', formData);

    showLoadingModal();

    fetch(`/quests/quest/${questId}/submit`, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => {
        hideLoadingModal();
        if (!response.ok) {
            if (response.status === 403) {
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
        hideLoadingModal();
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

function fetchSubmissions(questId) {
    fetch(`/quests/quest/${questId}/submissions`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${userToken}`,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
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
                const submitterLink     = document.getElementById('submitterProfileLink');
                const submitterAvatar   = document.getElementById('submitterProfileImage');
                const submitterCaption  = document.getElementById('submitterProfileCaption');

                submissionImage.src = submission.image_url || 'image/placeholdersubmission.png';
                submissionComment.textContent = submission.comment || 'No comment provided.';
                submitterLink.href    = `/profile/${submission.user_id}`;
                submitterAvatar.src   = submission.user_avatar_url || '/static/images/default_profile.png';
                submitterCaption.textContent = submission.username || `User ${submission.user_id}`;

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
                id:   submission.id,
                url: submission.image_url,
                alt: "Submission Image",
                comment: submission.comment,
                user_id: submission.user_id,
                user_display_name:  submission.user_display_name,
                user_username:      submission.user_username,
                user_profile_picture: submission.user_profile_picture,
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

function isValidImageUrl(url) {
    if (!url) {
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    try {
        if (url.startsWith("/")) {
            return true;
        }
        const parsedUrl = new URL(url);
        if (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") {
            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
            return allowedExtensions.some(ext => parsedUrl.pathname.toLowerCase().endsWith(ext));
        }
    } catch (e) {
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    return false;
}

function distributeImages(images) {
    const board = document.getElementById('submissionBoard');
    board.innerHTML = '';

    let fallbackUrl = document.getElementById('questDetailModal').getAttribute('data-placeholder-url');
    if (!fallbackUrl) {
        console.warn("No fallback URL provided in data-placeholder-url attribute.");
        fallbackUrl = '/static/images/default-placeholder.webp';
    }

    const validFallbackUrl = isValidImageUrl(fallbackUrl) ? fallbackUrl : '';
    if (!validFallbackUrl) {
        console.warn("Fallback URL is not valid.");
    }

    images.forEach(image => {
        const img = document.createElement('img');
        
        let finalImageUrl = '';
        if (isValidImageUrl(image.url)) {
            finalImageUrl = image.url;
        } else if (validFallbackUrl) {
            finalImageUrl = validFallbackUrl;
        }

        img.src = finalImageUrl;
        img.alt = "Loaded Image";

        img.onerror = () => {
            console.warn(`Image failed to load, using fallback: ${validFallbackUrl}`);
            if (validFallbackUrl) {
                img.src = validFallbackUrl;
            }
        };

        img.onclick = () => {
            showSubmissionDetail(image);
        };
        img.style.margin = '10px';
        board.appendChild(img);
    });
}
