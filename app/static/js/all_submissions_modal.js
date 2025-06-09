const PLACEHOLDER_IMAGE = document.querySelector('meta[name="placeholder-image"]').getAttribute('content');

function showAllSubmissionsModal(gameId) {
    fetch(`/quests/quest/all_submissions?game_id=${gameId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayAllSubmissions(data.submissions, data.is_admin);
            openModal('allSubmissionsModal'); // Ensure this is the last modal opened if stacking
        })
        .catch(error => {
            console.error('Error fetching all submissions:', error);
            alert('Error fetching all submissions: ' + error.message);
        });
}

function displayAllSubmissions(submissions, isAdmin) {
    const container = document.getElementById('allSubmissionsContainer');
    if (!container) {
        console.error('allSubmissionsContainer element not found.');
        return;  // Exit if the container element is not found
    }
    container.innerHTML = ''; // Clear previous submissions
    submissions.forEach(submission => {
        const card = document.createElement('div');
        card.className = 'submission-card';

        const img = document.createElement('img');
        img.src = submission.image_url || PLACEHOLDER_IMAGE;
        img.alt = 'Quest Submission';
        img.className = 'submission-image';

        const info = document.createElement('div');
        info.className = 'submission-info';

        const userDetails = document.createElement('p');
        userDetails.textContent = `User: ${submission.user_display_name || submission.user_username}`;
        userDetails.className = 'submission-user-details';

        const timestamp = document.createElement('p');
        const formattedTimestamp = new Date(submission.timestamp).toLocaleString('en-US', {
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true
        });
        timestamp.textContent = `Submitted on: ${formattedTimestamp}`;
        timestamp.className = 'submission-timestamp';

        const comment = document.createElement('p');
        comment.textContent = `Comment: ${submission.comment}`;
        comment.className = 'submission-comment';

        const twitterLink = document.createElement('p');
        twitterLink.textContent = `Twitter: ${submission.twitter_url || 'N/A'}`;
        twitterLink.className = 'submission-comment';

        const facebookLink = document.createElement('p');
        facebookLink.textContent = `Facebook: ${submission.fb_url || 'N/A'}`;
        facebookLink.className = 'submission-comment';

        const instagramLink = document.createElement('p');
        instagramLink.textContent = `Instagram: ${submission.instagram_url || 'N/A'}`;
        instagramLink.className = 'submission-comment';

        info.appendChild(userDetails);
        info.appendChild(timestamp);
        info.appendChild(comment);
        info.appendChild(twitterLink);
        info.appendChild(facebookLink);
        info.appendChild(instagramLink);

        if (isAdmin) {
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.className = 'button delete-button';
            deleteButton.addEventListener('click', function(event) {
                event.stopPropagation();  // Prevent triggering card click event
                deleteSubmission(submission.id, 'allSubmissions');
            });
            card.appendChild(deleteButton);
        }

        card.appendChild(img);
        card.appendChild(info);

        // Make the card clickable to show the submission detail modal
        card.addEventListener('click', function() {  
            showSubmissionDetail({
                url: submission.image_url || submission.video_url,
                video_url: submission.video_url,
                comment: submission.comment,
                user_id: submission.user_id,  
                user_display_name: submission.user_display_name || submission.user_username,  
                user_profile_picture: submission.user_profile_picture,
                twitter_url: submission.twitter_url,  
                fb_url: submission.fb_url,  
                instagram_url: submission.instagram_url,  
                verification_type: 'image'  
            });  
            openModal('submissionDetailModal');  
        });

        container.appendChild(card);
    });
}



function deleteSubmission(submissionId) {
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
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting submission:', error);
            alert('Error during deletion: ' + error.message);
        });
}
