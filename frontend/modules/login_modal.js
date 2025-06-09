document.addEventListener('DOMContentLoaded', () => {
  const form     = document.getElementById('loginForm');
  const modal    = document.getElementById('loginModal');
  if (!form || !modal) return; // Modal not present on this page

  const pwdError  = document.getElementById('passwordError');
  const forgotDiv = document.getElementById('forgotContainer');
  const checkUrl  = modal.dataset.checkUrl;

  // AJAX submit
  form.addEventListener('submit', e => {
    e.preventDefault();
    pwdError.style.display = 'none';
    forgotDiv.innerHTML   = '';

    window.submitFormJson(form)
      .then(({ json }) => {
        if (json.success) {
          window.location.href = json.redirect;
        } else {
          pwdError.textContent = json.error;
          pwdError.style.display = 'block';
          if (json.show_forgot) {
            const a = document.createElement('a');
            a.href      = 'javascript:void(0)';
            a.textContent = 'Forgot password?';
            a.className = 'd-block mt-1';
            a.onclick   = window.openForgotPasswordModal;
            forgotDiv.appendChild(a);
          }
        }
      })
      .catch(() => form.submit());
  });

  // email-exists check
  const emailIn = document.getElementById('loginEmail');
  const loginBtn = document.getElementById('loginButton');
  const emailErr = document.getElementById('emailError');

  function resetState() {
    loginBtn.disabled = true;
    emailErr.style.display = 'none';
    emailErr.textContent = '';
  }

  resetState();

  emailIn.addEventListener('blur', () => {
    const email = emailIn.value.trim();
    if (!email) return resetState();
    fetch(`${checkUrl}?email=${encodeURIComponent(email)}`)
      .then(r => r.json())
      .then(d => {
        if (d.exists) {
          loginBtn.disabled = false;
        } else {
          loginBtn.disabled = true;
          emailErr.textContent = 'This email is not registered. Please register first.';
          emailErr.style.display = 'block';
        }
      })
      .catch(() => loginBtn.disabled = false);
  });

  emailIn.addEventListener('input', resetState);
});

