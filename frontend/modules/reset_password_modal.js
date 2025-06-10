import { submitFormJson } from './modal_common.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('resetForm');
    if (!form) return;

    const errDiv     = document.getElementById('resetError');
    const successDiv = document.getElementById('resetSuccess');
    const btn        = document.getElementById('resetButton');

    form.addEventListener('submit', e => {
        e.preventDefault();
        errDiv.style.display     = 'none';
        successDiv.style.display = 'none';

        submitFormJson(form)
            .then(({ json }) => {
                if (json.success) {
                    successDiv.textContent   = json.message;
                    successDiv.style.display = 'block';
                    btn.disabled             = true;

                    if (json.redirect) {
                        setTimeout(() => {
                            window.location.href = json.redirect;
                        }, 1200);
                    }
                } else {
                    errDiv.textContent   = json.error || 'Unable to reset password.';
                    errDiv.style.display = 'block';
                }
            })
            .catch(err => {
                console.error('Reset-password AJAX error:', err);
                form.submit();
            });
    });
});

