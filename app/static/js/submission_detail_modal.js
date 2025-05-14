// === app/static/js/submission_detail_modal.js ===

/**
 * Display and optionally allow in-place editing of a quest submission.
 * @param {Object} image - Submission data from server
 */
function showSubmissionDetail(image) {
    // Elements
    const modal         = document.getElementById('submissionDetailModal');
    const submissionImg = document.getElementById('submissionImage');
    const commentEl     = document.getElementById('submissionComment');
    const profileFrame  = document.getElementById('submitterProfileFrame');
    const profileImg    = document.getElementById('submitterProfileImage');
    const profileCap    = document.getElementById('submitterProfileCaption');
    const profileLink   = document.getElementById('submitterProfileLink');
    const twitterLink   = document.getElementById('twitterLink');
    const facebookLink  = document.getElementById('facebookLink');
    const instagramLink = document.getElementById('instagramLink');

    // 1) Set up image
    submissionImg.src = image.url;
    submissionImg.style.width      = '100%';
    submissionImg.style.height     = 'auto';
    submissionImg.style.maxHeight  = '80vh';
    submissionImg.style.objectFit  = 'contain';

    // 2) Populate comment and enable edit for owner
    // Remove any previous handlers
    commentEl.removeEventListener('blur', handleCommentSave);
    commentEl.removeEventListener('keydown', handleCommentKeydown);

    commentEl.textContent = image.comment || 'No comment provided.';

    if (image.user_id === window.currentUserId) {
        // Make editable
        commentEl.contentEditable = 'true';
        commentEl.classList.add('editable-comment');
        // Store submission ID
        modal.dataset.submissionId = image.id;
        // Attach handlers
        commentEl.addEventListener('keydown', handleCommentKeydown);
        commentEl.addEventListener('blur', handleCommentSave);
    } else {
        commentEl.contentEditable = 'false';
        commentEl.classList.remove('editable-comment');
        delete modal.dataset.submissionId;
    }

    // 3) Avatar + caption
    profileImg.src   = image.user_profile_picture || '/static/images/default_profile.png';
    profileFrame.style.display = 'block';
    profileCap.textContent = image.user_display_name || image.user_username || '—';
    profileLink.onclick = function(e) {
        e.preventDefault();
        showUserProfileModal(image.user_id);
        return false;
    };

    // 4) Social links
    updateSocialLink(twitterLink, image.twitter_url, image.verification_type !== 'comment');
    updateSocialLink(facebookLink, image.fb_url);
    updateSocialLink(instagramLink, image.instagram_url);

    // 5) Show modal
    openModal('submissionDetailModal');
}

/**
 * Save the edited comment when the element loses focus.
 * Uses PUT /submission/:id/comment
 */
function handleCommentSave(event) {
    const modal         = document.getElementById('submissionDetailModal');
    const submissionId  = modal.dataset.submissionId;
    const newComment    = event.target.textContent.trim();

    if (!submissionId) return;

    fetch(`/submission/${submissionId}/comment`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken':  getCsrfToken()
        },
        credentials: 'same-origin',
        body: JSON.stringify({ comment: newComment })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        if (status !== 200 || !data.success) {
            throw new Error(data.message || 'Save failed');
        }
        console.log('Comment saved:', data);
    })
    .catch(err => {
        console.error('Failed to save comment:', err);
        alert('Could not save comment. Please try again.');
    });
}

/**
 * Handle Enter/Escape keys in editable comment. Enter = save, Escape = cancel.
 */
function handleCommentKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        e.target.blur();
    }
    if (e.key === 'Escape') {
        e.preventDefault();
        // revert text
        const modal       = document.getElementById('submissionDetailModal');
        const submissionId = modal.dataset.submissionId;
        // re-fetch original comment from dataset or server as needed
        // For simplicity, just blur to re-load modal when reopened
        e.target.blur();
    }
}

/**
 * Show or hide a social link based on URL validity and extra condition.
 */
function updateSocialLink(linkEl, url, extraCondition = true) {
    if (extraCondition && isValidUrl(url)) {
        linkEl.href = url;
        linkEl.style.display = 'inline-block';
    } else {
        linkEl.style.display = 'none';
    }
}

/** Validate URL string. */
function isValidUrl(string) {
    try { return Boolean(new URL(string)); }
    catch { return false; }
}

/** Read CSRF token from cookie. */
function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}