let topZIndex = 1050; // Start with a base z-index for the first modal

// Common modal management functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        topZIndex += 10; // Increment z-index for stacking
        modal.style.zIndex = topZIndex; // Apply the new z-index to the modal
        modal.style.display = 'block';
        document.body.classList.add('body-no-scroll'); // Optional: prevent scrolling when modal is open
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';

        // Decrement z-index to allow stacking of previous modals
        topZIndex -= 10;

        // Restore scrolling if no modals are open
        const openModals = document.querySelectorAll('.modal[style*="display: block"]');
        if (openModals.length === 0) {
            document.body.classList.remove('body-no-scroll');
        }
    }
}

// Reset all modal content and settings to the initial state
function resetModalContent() {
    const twitterLink = document.getElementById('twitterLink');
    if (twitterLink) {
        twitterLink.style.display = 'none';
        twitterLink.href = '#'; // Reset to default or placeholder link
    }

    const facebookLink = document.getElementById('facebookLink');
    if (facebookLink) {
        facebookLink.style.display = 'none';
        facebookLink.href = '#'; // Reset to default or placeholder link
    }

    const instagramLink = document.getElementById('instagramLink');
    if (instagramLink) {
        instagramLink.style.display = 'none';
        instagramLink.href = '#'; // Reset to default or placeholder link
    }

    const modalQuestActions = document.getElementById('modalQuestActions');
    if (modalQuestActions) {
        modalQuestActions.innerHTML = '';
    }
    document.querySelectorAll('[id^="verifyButton-"]').forEach(button => button.remove());
    document.querySelectorAll('[id^="verifyQuestForm-"]').forEach(form => form.remove());
    document.body.classList.remove('body-no-scroll');
}
