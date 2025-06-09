import { computePosition, offset, flip } from 'https://cdn.jsdelivr.net/npm/@floating-ui/dom@1.6.10/+esm';

document.addEventListener('DOMContentLoaded', function () {
    const submitPhotoForm = document.getElementById('submitPhotoForm');
    const floatingModal = document.getElementById('floating-modal');
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

        showFloatingModal();

        const formData = new FormData(submitPhotoForm);

        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        formData.append('csrf_token', csrfToken);

        fetch(submitPhotoForm.action, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.message); });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayFlashMessage(data.message, 'success');
                window.location.href = data.redirect_url;
            } else {
                displayFlashMessage(data.message, 'error');
            }
        })
        .catch(error => {
            console.error("Submission error:", error);
            displayFlashMessage('Error during submission: ' + error.message, 'error');
        })
        .finally(() => {
            isSubmitting = false;
            hideFloatingModal();
        });
    });

    function showFloatingModal() {
        floatingModal.style.display = 'block';
        computePosition(submitPhotoForm, floatingModal, {
            placement: 'top',
            middleware: [offset(10), flip()]
        }).then(({ x, y }) => {
            floatingModal.style.left = `${x}px`;
            floatingModal.style.top = `${y}px`;
        });
    }

    function hideFloatingModal() {
        floatingModal.style.display = 'none';
    }

    function displayFlashMessage(message, category) {
        const flashMessagesDiv = document.getElementById('flash-messages');
        if (flashMessagesDiv) {
            flashMessagesDiv.innerHTML = `
                <div class="flash-message ${category}">
                    ${message}
                </div>
            `;
        } else {
            console.warn('Flash messages container not found.');
        }
    }
});
