function showSubmissionDetail(image) {
    const submissionModal   = document.getElementById('submissionDetailModal');
    const submissionImage   = document.getElementById('submissionImage');
    const submissionComment = document.getElementById('submissionComment');
  
    submissionImage.src = image.url;
    submissionComment.textContent = image.comment || 'No comment provided.';
  
    // —— Avatar + caption ——  
    const profileFrame   = document.getElementById('submitterProfileFrame');
    const profileImage   = document.getElementById('submitterProfileImage');
    const profileCaption = document.getElementById('submitterProfileCaption');
    const profileLink    = document.getElementById('submitterProfileLink');

    // 1) set the <img> src to the value from the server (or fallback)
    profileImage.src = image.user_profile_picture
        || '/static/images/default_profile.png';
    profileFrame.style.display = 'block';

    // 2) inject the username below
    profileCaption.textContent = image.user_display_name
        || image.user_username
        || 'Unknown User';

    // 3) clicking the avatar/caption opens the same modal as your button
    profileLink.onclick = function(e) {
        e.preventDefault();
        showUserProfileModal(image.user_id);
        return false;
    };
  
    // re‐wire the download link
    const downloadLink = document.getElementById('downloadLink');
    downloadLink.href = image.url;
    downloadLink.download = `Image-${image.user_id}`;
  
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
  
    openModal('submissionDetailModal');
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;  // Fails to construct a URL, it's likely not a valid URL
    }
}
