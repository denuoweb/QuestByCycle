function handleGameSelection(selectElement) {
    const selectedValue = selectElement.value;

    // Open the "Join Custom Game" modal if selected
    if (selectedValue === 'join_custom_game') {
        openModal('joinCustomGameModal');
    } else {
        window.location.href = selectedValue;
    }
}