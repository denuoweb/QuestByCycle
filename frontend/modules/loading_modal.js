export function showLoadingModal() {
    console.debug('Showing loading modal');
    document.getElementById('loadingModal').style.display = 'flex';
}

export function hideLoadingModal() {
    console.debug('Hiding loading modal');
    document.getElementById('loadingModal').style.display = 'none';
}

