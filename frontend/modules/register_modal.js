import logger from '../logger.js';

document.addEventListener('DOMContentLoaded', () => {
  const emailInput = document.getElementById('registerEmail');
  if (!emailInput) return; // Modal not included on this page

  const modal = document.getElementById('registerModal');
  const checkUrlBase = modal?.dataset.checkUrl || '/auth/check_email';
  const loginSection = document.getElementById('existingUserLogin');
  if (!loginSection) return;
    
  // Handle blur event on email field  
  emailInput.addEventListener('blur', () => {  
    const email = emailInput.value.trim();  
    if (!email) return;  
      
    // Call check_email endpoint  
    fetch(`${checkUrlBase}?email=${encodeURIComponent(email)}`)  
      .then(resp => resp.json())  
      .then(data => {  
        if (data.exists) {  
          // Email exists, show login section  
          loginSection.style.display = 'block';  
        } else {  
          // Email doesn't exist, hide login section  
          loginSection.style.display = 'none';  
        }  
      })  
      .catch(err => {  
        logger.error('Error checking email:', err);  
        loginSection.style.display = 'none';  
      });  
  });  
    
  // Handle login with existing account  
  document.getElementById('loginWithExistingBtn').addEventListener('click', () => {  
    const email = emailInput.value.trim();  
    const password = document.getElementById('existingUserPassword').value;  
    const errorDiv = document.getElementById('loginError');  
      
    // Get hidden field values  
    const gameId = document.getElementById('registerGameId').value;
    const questId = document.getElementById('registerQuestId').value;
    const next = document.getElementById('registerNext').value;
    const showJoin = document.getElementById('registerShowJoinCustom').value;
      
    // Create form data  
    const formData = new FormData();  
    formData.append('email', email);  
    formData.append('password', password);  
    formData.append('remember_me', 'true');  
      
    // Add context  
    if (gameId) formData.append('game_id', gameId);
    if (questId) formData.append('quest_id', questId);
    if (next) formData.append('next', next);
    if (showJoin) formData.append('show_join_custom', showJoin);
      
    // Try to log in  
    fetch('{{ url_for("auth.login") }}', {  
      method: 'POST',  
      headers: { 'X-Requested-With': 'XMLHttpRequest' },  
      body: formData,  
      credentials: 'same-origin'  
    })  
    .then(response => response.json().then(payload => ({ payload })))
    .then(({ payload }) => {
      if (payload.success) {  
        // Successful login → redirect  
        window.location.href = payload.redirect;  
      } else {  
        // Show error  
        errorDiv.textContent = payload.error;  
        errorDiv.style.display = 'block';  
      }  
    })  
    .catch(err => {  
      logger.error('Login error:', err);  
      errorDiv.textContent = 'An error occurred. Please try again.';  
      errorDiv.style.display = 'block';  
    });  
  });  
    
  // Reset login section when email changes  
  emailInput.addEventListener('input', () => {  
    loginSection.style.display = 'none';  
    document.getElementById('loginError').style.display = 'none';  
  });  
});
