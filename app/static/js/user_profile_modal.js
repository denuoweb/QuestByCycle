function initializeQuill() {
    const editorElement = document.getElementById('editor');
    if (!editorElement) {
        console.error('Quill editor container not found');
        return;
    }

    const quill = new Quill('#editor', {
        theme: 'snow',
        placeholder: 'Write your message here...',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, false] }],
                ['bold', 'italic', 'underline'],
                ['link', 'blockquote', 'code-block'],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }]
            ]
        }
    });

    const form = document.getElementById('messageForm');
    form.onsubmit = function (event) {
        event.preventDefault();  // Prevent the default form submission
        const messageContent = document.querySelector('input[name=content]');
        messageContent.value = quill.root.innerHTML;
        postMessage(form);
    };
}

function postMessage(form) {
    const formData = new FormData(form);
    const messageContent = formData.get('content');

    fetch(`/profile/${form.dataset.userid}/messages`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ content: messageContent })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert('Message posted successfully.');
                showUserProfileModal(form.dataset.userid);  // Reload profile details to reflect changes
            }
        })
        .catch(error => {
            console.error('Error posting message:', error);
            alert('Failed to post message. Please try again.');
        });
}

function showUserProfileModal(userId) {
    fetch(`/profile/${userId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.riding_preferences_choices) {
                console.error('Riding preferences choices data is missing.');
                return;
            }

            const userProfileDetails = document.getElementById('userProfileDetails');
            if (!userProfileDetails) {
                console.error('User profile details container not found');
                return;
            }

            const isCurrentUser = data.current_user_id === data.user.id;

            const messagesHtml = buildMessageTree(data.profile_messages, null, isCurrentUser, data.current_user_id, userId, 0);

            userProfileDetails.innerHTML = `
                <header class="profile-header text-center py-5 mb-4 position-relative bg-gradient-primary">
                    ${data.user.profile_picture ? `
                        <div class="profile-picture-container position-relative mx-auto mb-3">
                            <img src="/static/${data.user.profile_picture}" alt="Profile Picture" class="profile-picture rounded-circle shadow-lg border border-white border-4">
                        </div>` : ''}
                    <div class="header-bg position-absolute w-100 h-100 top-0 start-0 bg-opacity-50"></div>
                    <div class="header-content position-relative z-index-1">
                        <h1 class="display-4 text-white font-weight-bold">${data.user.display_name || data.user.username}'s Profile</h1>
                    </div>
                    <div class="header-decorative-elements position-absolute w-100 h-100 top-0 start-0">
                        <div class="decorative-circle"></div>
                        <div class="decorative-triangle"></div>
                    </div>
                </header>
                <div class="row g-4">
                    <div class="col-md-8">
                        <ul class="nav nav-tabs" id="profileTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <a class="nav-link active" id="profile-tab" data-bs-toggle="tab" href="#profile" role="tab" aria-controls="profile" aria-selected="true">
                                    <i class="bi bi-person-circle me-2"></i>Profile
                                </a>
                            </li>
                            <li class="nav-item" role="presentation">
                                <a class="nav-link" id="bike-tab" data-bs-toggle="tab" href="#bike" role="tab" aria-controls="bike" aria-selected="false">
                                    <i class="bi bi-bicycle me-2"></i>Bike
                                </a>
                            </li>
                            <li class="nav-item" role="presentation">
                                <a class="nav-link" id="badges-earned-tab" data-bs-toggle="tab" href="#badges-earned" role="tab" aria-controls="badges-earned" aria-selected="false">
                                    <i class="bi bi-trophy me-2"></i>Badges Earned
                                </a>
                            </li>
                            <li class="nav-item" role="presentation">
                                <a class="nav-link" id="games-participated-tab" data-bs-toggle="tab" href="#games-participated" role="tab" aria-controls="games-participated" aria-selected="false">
                                    <i class="bi bi-controller me-2"></i>Games Participated
                                </a>
                            </li>
                            <li class="nav-item" role="presentation">
                                <a class="nav-link" id="quest-submissions-tab" data-bs-toggle="tab" href="#quest-submissions" role="tab" aria-controls="quest-submissions" aria-selected="false">
                                    <i class="bi bi-list-quest me-2"></i>Quest Submissions
                                </a>
                            </li>
                        </ul>
                        <div class="tab-content bg-light p-4 rounded shadow-sm" id="profileTabsContent">
                            <div class="tab-pane fade show active" id="profile" role="tabpanel" aria-labelledby="profile-tab">
                                <section class="profile mb-4">
                                    ${isCurrentUser ? `
                                        <!-- View Mode -->
                                        <div id="profileViewMode">
                                        <p><strong>Display Name:</strong> ${data.user.display_name || ''}</p>
                                        <p><strong>Age Group:</strong> ${data.user.age_group || ''}</p>
                                        <p><strong>Interests:</strong> ${data.user.interests || ''}</p>
                                        <p><strong>Riding Preferences:</strong> ${data.user.riding_preferences.join(', ')}</p>
                                        <p><strong>Ride Description:</strong> ${data.user.ride_description || ''}</p>
                                        <button type="button" class="btn btn-primary" onclick="toggleProfileEditMode()">Edit</button>
                                        </div>

                                        <!-- Edit Mode (initially hidden) -->
                                        <div id="profileEditMode" class="d-none">
                                        <form id="editProfileForm" enctype="multipart/form-data" class="needs-validation" novalidate>
                                            <div class="form-group mb-3">
                                                <label for="profilePictureInput" class="form-label">Profile Picture:</label>
                                                <input type="file" class="form-control" id="profilePictureInput" name="profile_picture" accept="image/*">
                                            </div>
                                            <div class="form-group mb-3">
                                                <label for="displayName" class="form-label">Display Name:</label>
                                                <input type="text" class="form-control" id="displayName" name="display_name" value="${data.user.display_name || ''}" required>
                                                <div class="invalid-feedback">Display Name is required.</div>
                                            </div>
                                            <div class="form-group mb-3">
                                                <label for="ageGroup" class="form-label">Age Group:</label>
                                                <select class="form-select" id="ageGroup" name="age_group">
                                                    <option value="teen" ${data.user.age_group === 'teen' ? 'selected' : ''}>Teen</option>
                                                    <option value="adult" ${data.user.age_group === 'adult' ? 'selected' : ''}>Adult</option>
                                                    <option value="senior" ${data.user.age_group === 'senior' ? 'selected' : ''}>Senior</option>
                                                </select>
                                            </div>
                                            <div class="form-group mb-3">
                                                <label for="interests" class="form-label">Interests:</label>
                                                <textarea class="form-control" id="interests" name="interests" rows="3" placeholder="Describe your interests...">${data.user.interests || ''}</textarea>
                                            </div>
                                            <div class="form-group mb-3">
                                                <label for="ridingPreferences" class="form-label"><b>Please specify your riding preferences:</b></label>
                                                <div id="ridingPreferences">
                                                    ${data.riding_preferences_choices.map((choice, index) => `
                                                        <div class="form-check mb-2">
                                                            <input class="form-check-input" type="checkbox" id="ridingPref-${index}" name="riding_preferences" value="${choice[0]}" ${data.user.riding_preferences.includes(choice[0]) ? 'checked' : ''} style="width: 1.25rem; height: 1.25rem;">
                                                            <label class="form-check-label ms-2" for="ridingPref-${index}">${choice[1]}</label>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                            <div class="form-group mb-3">
                                                <label for="rideDescription" class="form-label">Describe the type of riding you like to do:</label>
                                                <textarea class="form-control" id="rideDescription" name="ride_description" rows="3">${data.user.ride_description || ''}</textarea>
                                            </div>
                                            <div class="form-check form-switch mb-3">
                                                <input class="form-check-input" type="checkbox" id="uploadToSocials" name="upload_to_socials" ${data.user.upload_to_socials ? 'checked' : ''}>
                                                <label class="form-check-label" for="uploadToSocials">Cross post to game's social media?</label>
                                            </div>
                                            <div class="form-check form-switch mb-3">
                                                <input class="form-check-input" type="checkbox" id="uploadToMastodon" name="upload_to_mastodon" ${data.user.upload_to_mastodon ? 'checked' : ''}>
                                                <label class="form-check-label" for="uploadToMastodon">Cross post to your federation server?</label>
                                            </div>
                                            <div class="d-flex justify-content-between">
                                                <button type="button" class="btn btn-success" onclick="saveProfile(${userId})"><i class="bi bi-save me-2"></i>Save Profile</button>
                                                <button type="button" class="btn btn-secondary" onclick="toggleProfileEditMode()">Cancel</button>
                                            </div>
                                        </form>
                                        <hr>
                                        <form id="updatePasswordForm" class="d-flex justify-content-between">
                                            <button type="button" class="btn btn-primary w-100 me-2" onclick="window.location.href='/auth/update_password';">
                                                <i class="bi bi-shield-lock-fill me-2"></i>Update Password
                                            </button>
                                        </form>
                                        <hr>
                                        <form id="deleteAccountForm" onsubmit="event.preventDefault(); deleteAccount();" class="d-flex justify-content-between">
                                            <button type="submit" class="btn btn-danger w-100">
                                                <i class="bi bi-trash-fill me-2"></i>Delete My Account
                                            </button>
                                        </form>
                                        </div>
                                    ` : `
                                        <!-- For non-current users, display non-editable details -->
                                        <p><strong>Display Name:</strong> ${data.user.display_name || ''}</p>
                                        <p><strong>Age Group:</strong> ${data.user.age_group || ''}</p>
                                        <p><strong>Interests:</strong> ${data.user.interests || ''}</p>
                                        <p><strong>Riding Preferences:</strong> ${data.user.riding_preferences.join(', ')}</p>
                                        <p><strong>Ride Description:</strong> ${data.user.ride_description || ''}</p>
                                    `}
                                    </section>
                            </div>
                            <div class="tab-pane fade" id="bike" role="tabpanel" aria-labelledby="bike-tab">
                                <section class="bike mb-4">
                                    <h2 class="h2">Bike Details</h2>

                                    ${isCurrentUser ? `
                                        <form id="editBikeForm" class="needs-validation" novalidate>
                                            <div class="form-group mb-3">
                                                <label for="bikePicture" class="form-label">Upload Your Bicycle Picture:</label>
                                                <input type="file" class="form-control" id="bikePicture" name="bike_picture" accept="image/*">
                                            </div>
                                            ${data.user.bike_picture ? `
                                                <div class="form-group mb-3">
                                                    <label for="bikePicturePreview" class="form-label">Current Bicycle Picture:</label>
                                                    <img src="/static/${data.user.bike_picture}" id="bikePicturePreview" alt="Bicycle Picture" class="img-fluid rounded shadow-sm" style="max-width: 100%; height: auto; object-fit: cover;">
                                                </div>
                                            ` : ''}
                                            <div class="form-group mb-3">
                                                <label for="bikeDescription" class="form-label">Bicycle Description:</label>
                                                <textarea class="form-control" id="bikeDescription" name="bike_description" rows="3">${data.user.bike_description || ''}</textarea>
                                            </div>
                                            <div class="d-flex justify-content-between">
                                                <button type="button" class="btn btn-success" onclick="saveBike(${userId})"><i class="bi bi-save me-2"></i>Save Bike Details</button>
                                            </div>
                                        </form>` : `
                                        ${data.user.bike_picture ? `
                                            <div class="form-group mb-3">
                                                <label for="bikePicture">Current Bicycle Picture:</label>
                                                <img src="/static/${data.user.bike_picture}" alt="Bicycle Picture" class="img-fluid rounded shadow-sm">
                                            </div>` : ''}
                                        <p><strong>Bicycle Description:</strong> ${data.user.bike_description || ''}</p>
                                    `}

                                </section>
                            </div>
                            <div class="tab-pane fade" id="badges-earned" role="tabpanel" aria-labelledby="badges-earned-tab">
                                <section class="badges-earned mb-4">
                                    <h2 class="h2">Badges Earned</h2>
                                    <div class="badges-container row g-3">
                                        ${data.user.badges && data.user.badges.length > 0 ? data.user.badges.map(badge => `
                                            <div class="badge-item col-md-4 d-flex flex-column align-items-center text-center p-3 border rounded shadow-sm bg-white">
                                                <img src="/static/images/badge_images/${badge.image}" alt="${badge.name}" class="badge-icon mb-2 rounded-circle shadow-sm" style="width: 100px; height: 100px; object-fit: cover;">
                                                <h3 class="h5 mt-2">${badge.name}</h3>
                                                <p class="text-muted">${badge.description}</p>
                                                <p><strong>Category:</strong> ${badge.category}</p>
                                            </div>`).join('') : '<p class="text-muted">No badges earned yet.</p>'}
                                    </div>
                                </section>
                            </div>
                            <div class="tab-pane fade" id="games-participated" role="tabpanel" aria-labelledby="games-participated-tab">
                                <section class="games-participated mb-4">
                                    <h2 class="h2">Games Participated</h2>
                                    <div class="games-container row g-3">
                                        ${data.participated_games && data.participated_games.length > 0 ? data.participated_games.map(game => `
                                            <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                                                <h3 class="h5">${game.title}</h3>
                                                <p class="text-muted">${game.description}</p>
                                                <p><strong>Start Date:</strong> ${game.start_date}</p>
                                                <p><strong>End Date:</strong> ${game.end_date}</p>
                                            </div>`).join('') : '<p class="text-muted">No games participated in yet.</p>'}
                                    </div>
                                </section>
                            </div>
                            <div class="tab-pane fade" id="quest-submissions" role="tabpanel" aria-labelledby="quest-submissions-tab">
                                <section class="quest-submissions mb-4">
                                    <h2 class="h2">Quest Submissions</h2>
                                    <div class="submissions-container row g-3">
                                        ${data.quest_submissions && data.quest_submissions.length > 0 ? data.quest_submissions.map(submission => `
                                            <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                                                ${submission.image_url ? `<img src="${submission.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height: 200px; object-fit: cover;">` : ''}
                                                <p><strong>Quest:</strong> ${submission.quest.title}</p>
                                                <p class="text-muted">${submission.comment}</p>
                                                <p><strong>Submitted At:</strong> ${submission.timestamp}</p>
                                                <div class="d-flex justify-content-start gap-2">
                                                    ${submission.twitter_url ? `<a href="${submission.twitter_url}" target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>` : ''}
                                                    ${submission.fb_url ? `<a href="${submission.fb_url}" target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>` : ''}
                                                    ${submission.instagram_url ? `<a href="${submission.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>` : ''}
                                                </div>
                                                ${isCurrentUser ? `<button class="btn btn-danger btn-sm mt-2" onclick="deleteSubmission(${submission.id}, 'profileSubmissions', ${data.user.id})">Delete</button>` : ''}
                                            </div>`).join('') : '<p class="text-muted">No quest submissions yet.</p>'}
                                    </div>
                                </section>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <section class="message-board mb-4">
                            <h2 class="h2">Message Board</h2>
                            <form id="messageForm" data-userid="${userId}" class="needs-validation" novalidate>
                                <div class="form-group mb-3">
                                    <div id="editor" class="form-control quill-editor bg-white rounded" style="min-height: 100px;"></div>
                                    <input type="hidden" id="messageContent" name="content" required>
                                    <div class="invalid-feedback">Message cannot be empty.</div>
                                </div>
                                <button type="submit" class="btn btn-primary w-100"><i class="bi bi-send-fill me-2"></i>Post</button>
                            </form>
                            <ul class="list-group mt-3" id="messageBoard">
                                ${messagesHtml}
                            </ul>
                        </section>
                    </div>
                </div>
            `;
            initializeQuill();  // Initialize Quill for all profiles
            openModal('userProfileModal');
        })
        .catch(error => {
            console.error('Failed to load user profile:', error);
            alert('Could not load user profile. Please try again.');
        });
}

document.querySelectorAll('[data-floating-ui-tooltip]').forEach(el => {
    tippy(el, {
        content: el.getAttribute('data-floating-ui-tooltip'),
        placement: 'top',
        animation: 'scale-subtle',
    });
});

document.querySelectorAll('.needs-validation').forEach(form => {
    form.addEventListener('submit', event => {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    }, false);
});


function toggleProfileEditMode() {
    const viewDiv = document.getElementById('profileViewMode');
    const editDiv = document.getElementById('profileEditMode');
  
    if (viewDiv.classList.contains('d-none')) {
      // Currently in edit mode – switch back to view mode.
      viewDiv.classList.remove('d-none');
      editDiv.classList.add('d-none');
    } else {
      // Switch to edit mode.
      viewDiv.classList.add('d-none');
      editDiv.classList.remove('d-none');
    }
  }

  
function saveProfile(userId) {
    const form = document.getElementById('editProfileForm');
    const formData = new FormData(form);

    // Append profile picture to FormData if it exists
    const profilePictureInput = document.getElementById('profilePictureInput');
    if (profilePictureInput.files.length > 0) {
        formData.append('profile_picture', profilePictureInput.files[0]);
    }

    // Collect riding preferences from checkboxes
    const ridingPreferences = [];
    form.querySelectorAll('input[name="riding_preferences"]:checked').forEach((checkbox) => {
        ridingPreferences.push(checkbox.value);
    });

    formData.delete('riding_preferences');
    ridingPreferences.forEach((preference) => {
        formData.append('riding_preferences', preference);
    });

    // Debug: Print form data to the console
    console.log('Form data before submission:');
    formData.forEach((value, key) => {
        console.log(`${key}: ${value}`);
    });

    fetch(`/profile/${userId}/edit`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Server error:', data.error);
            alert(`Error: ${data.error}`);
        } else {
            console.log('Profile updated successfully:', data);
            alert('Profile updated successfully.');
            showUserProfileModal(userId);  // Reload profile details to reflect changes
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        alert('Failed to update profile. Please try again.');
    });
}


function saveBike(userId) {
    const form = document.getElementById('editBikeForm');
    const formData = new FormData(form);

    // Append bicycle picture to FormData if it exists
    const bikePictureInput = document.getElementById('bikePicture');
    if (bikePictureInput.files.length > 0) {
        formData.append('bike_picture', bikePictureInput.files[0]);
    }

    // Debug: Print form data to the console
    console.log('Form data before submission:');
    formData.forEach((value, key) => {
        console.log(`${key}: ${value}`);
    });

    fetch(`/profile/${userId}/edit-bike`, { // Ensure the correct endpoint handles bike information
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Server error:', data.error);
                alert(`Error: ${data.error}`);
            } else {
                console.log('Bike details updated successfully:', data);
                alert('Bike details updated successfully.');
                showUserProfileModal(userId);  // Reload profile details to reflect changes
            }
        })
        .catch(error => {
            console.error('Error updating bike details:', error);
            alert('Failed to update bike details. Please try again.');
        });
}
function buildMessageTree(messages, parentId, isCurrentUser, currentUserId, profileUserId, depth) {
    if (depth > 3) return '';  // Limit replies to a depth of 3

    const nestedMessages = messages.filter(message => message.parent_id === parentId)
        .map(message => {
            const replies = buildMessageTree(messages, message.id, isCurrentUser, currentUserId, profileUserId, depth + 1);
            const canReply = (depth < 2) && (currentUserId === profileUserId ||
                currentUserId === message.author_id ||
                currentUserId === message.user_id ||
                (message.parent_id && currentUserId === messages.find(m => m.id === message.parent_id).author_id));
            const canDelete = currentUserId === message.author_id || currentUserId === profileUserId;

            const displayName = message.author.display_name || message.author.username;

            return `
            <li class="list-group-item ${message.parent_id ? 'reply-message' : ''}" data-messageid="${message.id}">
                <div class="message-content">
                    ${message.content}
                </div>
                <small>Posted by ${displayName} on ${message.timestamp}</small>
                ${message.author_id === currentUserId ? `
                    <div class="mt-2">
                        <button class="btn btn-secondary btn-sm" onclick="editMessage(${message.id}, ${currentUserId})">Edit</button>
                    </div>` : ''}
                ${canDelete ? `
                    <button class="btn btn-danger btn-sm mt-2" onclick="deleteMessage(${message.id}, ${profileUserId})">Delete</button>` : ''}
                ${canReply ? `
                    <button class="btn btn-sm btn-primary mt-2" onclick="showReplyForm(${message.id}, ${profileUserId})">Reply</button>
                    <form id="replyForm-${message.id}" class="reply-form mt-2 d-none" data-messageid="${message.id}">
                        <div class="form-group">
                            <textarea class="form-control" name="replyContent" rows="3"></textarea>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="postReply(${profileUserId}, ${message.id})">Submit Reply</button>
                    </form>` : ''}
                <ul class="list-group mt-2">
                    ${replies}
                </ul>
            </li>
        `;
        }).join('');

    return nestedMessages;
}

function showReplyForm(messageId, profileUserId) {
    document.getElementById(`replyForm-${messageId}`).classList.toggle('d-none');
    document.getElementById(`replyForm-${messageId}`).dataset.profileUserId = profileUserId;
}

function postReply(profileUserId, messageId) {
    const replyForm = document.querySelector(`#replyForm-${messageId}`);
    const replyContent = replyForm.querySelector('textarea[name=replyContent]').value;

    fetch(`/profile/${profileUserId}/messages/${messageId}/reply`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ content: replyContent })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert('Reply posted successfully.');
                showUserProfileModal(profileUserId);  // Reload profile details to reflect changes
            }
        })
        .catch(error => {
            console.error('Error posting reply:', error);
            alert('Failed to post reply. Please try again.');
        });
}

function deleteSubmission(submissionId, context, userId) {
    fetch(`/quests/quest/delete_submission/${submissionId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Submission deleted successfully.');
                if (context === 'profileSubmissions') {
                    showUserProfileModal(userId);  // Reload profile submissions
                }
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting submission:', error);
            alert('Error during deletion: ' + error.message);
        });
}

function deleteAccount() {
    console.log('deleteAccount called');  // Debugging: Log function call

    if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        console.log('Account deletion cancelled by the user.');  // Debugging: Log cancellation
        return;  // Exit if the user does not confirm
    }

    console.log('User confirmed account deletion. Proceeding with deletion request.');  // Debugging: Log confirmation

    fetch(`/auth/delete_account`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => {
        console.log('Received response from server:', response);  // Debugging: Log response

        if (response.redirected) {
            console.log('Redirecting to:', response.url);  // Debugging: Log redirection
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data) {
            console.log('Parsed response data:', data);  // Debugging: Log parsed data
            if (data.error) {
                console.error(`Error received from server: ${data.error}`);  // Debugging: Log server error
                alert(`Error: ${data.error}`);
            } else {
                console.log('Account deletion successful. Redirecting to homepage.');  // Debugging: Log success
                alert('Your account has been successfully deleted.');
                window.location.href = '/';  // Redirect to the homepage or any other page after deletion
            }
        }
    })
    .catch(error => {
        console.error('Error deleting account:', error);  // Debugging: Log fetch error
        alert('Failed to delete account. Please try again.');
    });
}


function editMessage(messageId, userId) {
    const messageElement = document.querySelector(`li[data-messageid="${messageId}"]`);
    const messageContentElement = messageElement.querySelector('.message-content');
    const currentContent = messageContentElement.innerHTML;

    messageContentElement.innerHTML = `
        <textarea class="form-control">${currentContent}</textarea>
        <button class="btn btn-primary mt-2" onclick="saveMessage(${messageId}, ${userId})">Save</button>
        <button class="btn btn-secondary mt-2" onclick="cancelEditMessage(${messageId}, '${currentContent}')">Cancel</button>
    `;
}

function saveMessage(messageId, userId) {
    const messageElement = document.querySelector(`li[data-messageid="${messageId}"]`);
    const messageContentElement = messageElement.querySelector('.message-content textarea');
    const newContent = messageContentElement.value;

    fetch(`/profile/${userId}/messages/${messageId}/edit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ content: newContent })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert('Message updated successfully.');
                showUserProfileModal(userId);  // Reload profile details to reflect changes
            }
        })
        .catch(error => {
            console.error('Error updating message:', error);
            alert('Failed to update message. Please try again.');
        });
}

function cancelEditMessage(messageId, originalContent) {
    const messageElement = document.querySelector(`li[data-messageid="${messageId}"]`);
    const messageContentElement = messageElement.querySelector('.message-content');
    messageContentElement.innerHTML = originalContent;
}

function deleteMessage(messageId, userId) {
    fetch(`/profile/${userId}/messages/${messageId}/delete`, {
        method: 'POST',
        headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Message deleted successfully.');
                showUserProfileModal(userId);  // Reload profile messages to reflect changes
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            console.error('Error deleting message:', error);
            alert('Error during deletion: ' + error.message);
        });
}
