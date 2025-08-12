
import { showLoadingModal, hideLoadingModal } from './loading_modal.js';
import { csrfFetchJson } from '../utils.js';
import logger from '../logger.js';

function initSubmitPhotoForm() {
    const submitPhotoForm = document.getElementById('submitPhotoForm');

    if (!submitPhotoForm) {
        logger.error('submitPhotoForm element not found on page.');
        return;
    }

    let isSubmitting = false;

    // Handle form submission
    submitPhotoForm.addEventListener('submit', function(event) {
        event.preventDefault();
        if (isSubmitting) return;
        isSubmitting = true;

        const fileInput = submitPhotoForm.querySelector('input[name="photo"]');
        const file = fileInput ? fileInput.files[0] : null;
        if (file && file.type.startsWith('video/') && file.size > 10 * 1024 * 1024) {
            displayFlashMessage('Video must be 10 MB or smaller.', 'error');
            isSubmitting = false;
            return;
        }
        if (file && file.type.startsWith('image/') && file.size > 8 * 1024 * 1024) {
            displayFlashMessage('Image must be 8 MB or smaller.', 'error');
            isSubmitting = false;
            return;
        }

        showLoadingModal();

        const formData = new FormData(submitPhotoForm);

        csrfFetchJson(submitPhotoForm.action, {
            method: 'POST',
            body: formData
        })
        .then(({ status, json }) => {
            if (status === 200 && json.success) {
                displayFlashMessage(json.message, 'success');
                window.location.href = json.redirect_url;
            } else {
                const msg = json.message || 'Upload failed';
                displayFlashMessage(msg, 'error');
            }
        })
        .catch(error => {
            logger.error('Submission error:', error);
            displayFlashMessage('Error during submission: ' + error.message, 'error');
        })
        .finally(() => {
            isSubmitting = false;
            hideLoadingModal();
        });
    });


    function displayFlashMessage(message, category) {
        const flashMessagesDiv = document.getElementById('flash-messages');
        if (flashMessagesDiv) {
            flashMessagesDiv.innerHTML = '';
            const msgDiv = document.createElement('div');
            msgDiv.className = `flash-message ${category}`;
            msgDiv.textContent = message;
            flashMessagesDiv.appendChild(msgDiv);
        } else {
            logger.warn('Flash messages container not found.');
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSubmitPhotoForm);
} else {
    initSubmitPhotoForm();
}

