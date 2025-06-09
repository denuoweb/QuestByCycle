document.addEventListener('DOMContentLoaded', () => {  
  const emailInput = document.getElementById('registerEmail');  
  const registerForm = emailInput.closest('form');  
  const formGroup = emailInput.closest('.form-group');  
  const checkUrlBase = "{{ url_for('auth.check_email') }}";  
    
  // Create a hidden login section to show when email exists  
  const loginSection = document.createElement('div');  
  loginSection.id = 'existingUserLogin';  
  loginSection.style.display = 'none';  
  loginSection.innerHTML = `  
    <div class="alert alert-info">This email is already registered. Enter your password to log in.</div>  
    <div class="form-group">  
      <label for="existingUserPassword">Password</label>  
      <input type="password" id="existingUserPassword" class="form-control" autocomplete="current-password">
      <div id="loginError" class="text-danger mt-1" style="display: none;"></div>  
    </div>  
    <div class="form-group">  
      <button type="button" id="loginWithExistingBtn" class="btn btn-primary">Login</button>  
    </div>  
  `;  
    
  // Insert after the email form group  
  formGroup.insertAdjacentElement('afterend', loginSection);  
    
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
        console.error('Error checking email:', err);  
        loginSection.style.display = 'none';  
      });  
  });  
    
  // Handle login with existing account  
  document.getElementById('loginWithExistingBtn').addEventListener('click', () => {  
    const email = emailInput.value.trim();  
    const password = document.getElementById('existingUserPassword').value;  
    const errorDiv = document.getElementById('loginError');  
      
    // Get hidden field values  
    const gameId = document.getElementById('gameIdField').value;  
    const questId = document.getElementById('questIdField').value;  
    const next = document.getElementById('nextField').value;  
      
    // Create form data  
    const formData = new FormData();  
    formData.append('email', email);  
    formData.append('password', password);  
    formData.append('remember_me', 'true');  
      
    // Add context  
    if (gameId) formData.append('game_id', gameId);  
    if (questId) formData.append('quest_id', questId);  
    if (next) formData.append('next', next);  
      
    // Try to log in  
    fetch('{{ url_for("auth.login") }}', {  
      method: 'POST',  
      headers: { 'X-Requested-With': 'XMLHttpRequest' },  
      body: formData,  
      credentials: 'same-origin'  
    })  
    .then(response => response.json().then(payload => ({ status: response.status, payload })))  
    .then(({ status, payload }) => {  
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
      console.error('Login error:', err);  
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
