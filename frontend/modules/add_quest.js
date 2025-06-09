document.addEventListener('DOMContentLoaded', () => {
  const questForm = document.getElementById('quest-form');
  if (questForm) {
    questForm.addEventListener('submit', e => {
      const description = document.getElementById('description').value.trim();
      if (!description) {
        alert('Description is required.');
        e.preventDefault();
      }
    });
  }
});

