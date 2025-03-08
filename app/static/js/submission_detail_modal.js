// Submission detail modal management functions
function showSubmissionDetail(image) {
    const submissionModal = document.getElementById('submissionDetailModal');
    document.getElementById('submissionImage').src = image.url;
    document.getElementById('submissionComment').textContent = image.comment || 'No comment provided.';
    document.getElementById('submissionUserLink').onclick = function() {
        showUserProfileModal(image.user_id);
        return false;
    };
    document.getElementById('downloadLink').href = image.url;
    document.getElementById('downloadLink').download = `Image-${image.user_id}`;

    // Update the Twitter link if available
    const twitterLink = document.getElementById('twitterLink');
    if (image.verification_type !== 'comment' && image.twitter_url && isValidUrl(image.twitter_url)) {
        twitterLink.href = image.twitter_url;
        twitterLink.style.display = 'inline';
    } else {
        twitterLink.style.display = 'none';
    }

    // Update the Facebook link if available
    const facebookLink = document.getElementById('facebookLink');
    if (image.fb_url && isValidUrl(image.fb_url)) {
        facebookLink.href = image.fb_url;
        facebookLink.style.display = 'inline';
    } else {
        facebookLink.style.display = 'none';
    }

    // Update the Instagram link if available
    const instagramLink = document.getElementById('instagramLink');
    if (image.instagram_url && isValidUrl(image.instagram_url)) {
        instagramLink.href = image.instagram_url;
        instagramLink.style.display = 'inline';
    } else {
        instagramLink.style.display = 'none';
    }

    // Ensure the submission modal opens on top of the quest detail modal
    const questDetailModalZIndex = parseInt(window.getComputedStyle(document.getElementById('questDetailModal')).zIndex, 10);
    submissionModal.style.zIndex = questDetailModalZIndex + 10; // Adjust z-index to be above the quest detail modal

    // Show the modal
    submissionModal.style.display = 'block';
    submissionModal.style.backgroundColor = 'rgba(0,0,0,0.7)';
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;  // Fails to construct a URL, it's likely not a valid URL
    }
}
