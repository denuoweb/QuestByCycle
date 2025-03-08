function showGameInfoModal(gameId) {
    // Adjust the URL based on your blueprint's URL prefix (assumed to be /games)
    fetch('/games/game-info/' + gameId + '?modal=1')
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch game info");
            }
            return response.text();
        })
        .then(html => {
            // Remove any existing modal with the same ID, if present.
            let existingModal = document.getElementById('gameInfoModal');
            if (existingModal) {
                existingModal.parentNode.removeChild(existingModal);
            }
            // Create a temporary container and set its innerHTML to the fetched HTML
            let tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            // Assume that the first child is our complete modal element.
            let modalElement = tempDiv.firstElementChild;
            // Append the modal element to the document body
            document.body.appendChild(modalElement);
            // Display the modal by setting its display style to block (or using your preferred method)
            document.getElementById('gameInfoModal').style.display = 'block';
        })
        .catch(error => {
            console.error("Error loading game info:", error);
            alert("Failed to load game info. Please try again later.");
        });
}

// Expose the function globally so it can be called by inline onclick attributes.
window.showGameInfoModal = showGameInfoModal;
