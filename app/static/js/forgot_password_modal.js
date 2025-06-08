document.addEventListener('DOMContentLoaded', () => {
  const form          = document.getElementById('forgotForm');
  const emailErr      = document.getElementById('forgotEmailError');
  const successDiv    = document.getElementById('forgotSuccess');
  const btn           = document.getElementById('forgotButton');
  const emailInput    = document.getElementById('forgotEmail');
  const emailDisplay  = document.getElementById('forgotEmailDisplay');

  const modal = document.getElementById('forgotPasswordModal');
  const observer = new MutationObserver(() => {
    if (modal.style.display === 'block') {
      emailDisplay.textContent = emailInput.value;
    }
  });
  observer.observe(modal, { attributes: true, attributeFilter: ['style'] });

  form.addEventListener('submit', e => {
    e.preventDefault();
    emailErr.style.display   = 'none';
    successDiv.style.display = 'none';

    fetch(form.action, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: new FormData(form),
      credentials: 'same-origin'
    })
    .then(r => r.json().then(json => ({ status: r.status, json })))
    .then(({ json }) => {
      if (json.success) {
        successDiv.textContent   = json.message;
        successDiv.style.display = 'block';
        btn.disabled             = true;
      } else {
        emailErr.textContent   = json.error || 'An error occurred.';
        emailErr.style.display = 'block';
      }
    })
    .catch(_ => {
      form.submit();
    });
  });
});
