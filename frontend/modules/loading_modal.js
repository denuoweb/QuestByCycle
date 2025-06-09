function showLoadingModal() {
    console.debug('Showing loading modal');
    document.getElementById('loadingModal').style.display = 'flex';
}

function hideLoadingModal() {
    console.debug('Hiding loading modal');
    document.getElementById('loadingModal').style.display = 'none';
}

export {};
