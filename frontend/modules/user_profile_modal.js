import { openModal } from './modal_common.js';
import { csrfFetchJson } from '../utils.js';
import logger from '../logger.js';

export function showUserProfileModal(userId) {
  fetch(`/profile/${userId}`)
    .then(r => r.json())
    .then(data => {
      if (!data.riding_preferences_choices) {
        logger.error('Riding preferences choices missing.');
        return;
      }

      const detailsContainer = document.getElementById('userProfileDetails');

      if (!detailsContainer) {
        logger.error('Profile details containers not found');
        return;
      }

      const isCurrent = data.current_user_id === data.user.id;

      // Render tabs & panes into #userProfileDetails
      detailsContainer.innerHTML = `
          <!-- XS: native select dropdown -->
          <div class="d-block d-sm-none mb-3">
            <select id="profileTabSelect" class="form-select">
              <option value="profile" selected>Profile</option>
              <option value="bike">Bike</option>
              <option value="badges-earned">Badges Earned</option>
              <option value="games-participated">Games Participated</option>
              <option value="quest-submissions">Quest Submissions</option>
            </select>
          </div>

          <!-- SM+ nav-tabs (will scroll horizontally) -->
          <ul class="nav nav-tabs epic-tabs d-none d-sm-flex" id="profileTabs" role="tablist">
            <li class="nav-item" role="presentation">
              <a class="nav-link active" id="profile-tab" data-bs-toggle="tab"
                href="#profile" role="tab" aria-controls="profile" aria-selected="true">
                <i class="bi bi-person-circle me-2"></i>Profile
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a class="nav-link" id="bike-tab" data-bs-toggle="tab"
                 href="#bike" role="tab" aria-controls="bike" aria-selected="false">
                <i class="bi bi-bicycle me-2"></i>Bike
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a class="nav-link" id="badges-earned-tab" data-bs-toggle="tab"
                 href="#badges-earned" role="tab" aria-controls="badges-earned" aria-selected="false">
                <i class="bi bi-trophy me-2"></i>Badges Earned
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a class="nav-link" id="games-participated-tab" data-bs-toggle="tab"
                 href="#games-participated" role="tab" aria-controls="games-participated" aria-selected="false">
                <i class="bi bi-controller me-2"></i>Games Participated
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a class="nav-link" id="quest-submissions-tab" data-bs-toggle="tab"
                 href="#quest-submissions" role="tab" aria-controls="quest-submissions" aria-selected="false">
                <i class="bi bi-list-quest me-2"></i>Quest Submissions
              </a>
            </li>
          </ul>

          <div class="tab-content bg-light p-4 rounded shadow-sm" id="profileTabsContent">

            <!-- 1) PROFILE pane -->
            <div class="tab-pane fade show active" id="profile" role="tabpanel" aria-labelledby="profile-tab">
              <section class="profile mb-4">
                ${isCurrent ? `
                  <div id="profileViewMode">
                    ${data.user.profile_picture ? `
                      <div class="profile-picture-container position-relative mx-auto mb-3">
                        <img src="/static/${data.user.profile_picture}"
                            class="profile-picture rounded-circle shadow-lg border border-white border-4"
                            alt="Profile Picture">
                      </div>` : ''}
                    <p><strong>Display Name:</strong> ${data.user.display_name || ''}</p>
                    <p><strong>Age Group:</strong> ${data.user.age_group || ''}</p>
                    <p><strong>Timezone:</strong> ${data.user.timezone || ''}</p>
                    <p><strong>Interests:</strong> ${data.user.interests || ''}</p>
                    <p><strong>Riding Preferences:</strong> ${data.user.riding_preferences.join(', ')}</p>
                    <p><strong>Ride Description:</strong> ${data.user.ride_description || ''}</p>
                    <button class="btn btn-primary" id="editProfileBtn">Edit</button>
                  </div>
                  <div id="profileEditMode" class="d-none">
                    <form id="editProfileForm" method="post" enctype="multipart/form-data" class="needs-validation" novalidate>
                      <div class="form-group mb-3">
                        <label for="profilePictureInput">Profile Picture:</label>
                        <input type="file" class="form-control" id="profilePictureInput"
                                name="profile_picture" accept="image/*">
                      </div>
                      <div class="form-group mb-3">
                        <label for="displayName">Display Name:</label>
                        <input type="text" class="form-control" id="displayName" name="display_name"
                                value="${data.user.display_name || ''}" required>
                        <div class="invalid-feedback">Display Name is required.</div>
                      </div>
                      <div class="form-group mb-3">
                        <label for="ageGroup">Age Group:</label>
                        <select class="form-select" id="ageGroup" name="age_group">
                          <option value="teen" ${data.user.age_group==='teen'? 'selected':''}>Teen</option>
                          <option value="adult" ${data.user.age_group==='adult'? 'selected':''}>Adult</option>
                          <option value="senior" ${data.user.age_group==='senior'? 'selected':''}>Senior</option>
                        </select>
                      </div>
                      <div class="form-group mb-3">
                        <label for="timezone">Timezone:</label>
                        <select class="form-select" id="timezone" name="timezone">
                          ${data.timezone_choices.map(tz => `
                            <option value="${tz}" ${data.user.timezone===tz?'selected':''}>${tz}</option>
                          `).join('')}
                        </select>
                      </div>
                      <div class="form-group mb-3">
                        <label for="interests">Interests:</label>
                        <textarea class="form-control" id="interests" name="interests" rows="3"
                                  placeholder="Describe your interests...">${data.user.interests || ''}</textarea>
                      </div>
                      <div class="form-group mb-3">
                        <label><b>Please specify your riding preferences:</b></label>
                        <div id="ridingPreferences">
                          ${data.riding_preferences_choices.map((choice, i) => `
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${i}" name="riding_preferences"
                                      value="${choice[0]}"
                                      ${data.user.riding_preferences.includes(choice[0])?'checked':''}>
                              <label class="form-check-label" for="ridingPref-${i}">${choice[1]}</label>
                            </div>
                          `).join('')}
                        </div>
                      </div>
                      <div class="form-group mb-3">
                        <label for="rideDescription">Describe the type of riding you like to do:</label>
                        <textarea class="form-control" id="rideDescription" name="ride_description" rows="3">${data.user.ride_description || ''}</textarea>
                      </div>
                      <div class="form-check form-switch mb-3">
                        <input class="form-check-input" type="checkbox" id="uploadToSocials" name="upload_to_socials"
                                ${data.user.upload_to_socials?'checked':''}>
                        <label class="form-check-label" for="uploadToSocials">Cross post to game's social media?</label>
                      </div>
                      <div class="form-check form-switch mb-3">
                        <input class="form-check-input" type="checkbox" id="uploadToMastodon" name="upload_to_mastodon"
                                ${data.user.upload_to_mastodon?'checked':''}>
                        <label class="form-check-label" for="uploadToMastodon">Cross post to your federation server?</label>
                      </div>
                      ${!data.user.is_admin ? `
                      <div class="mb-3">
                        <button type="button" class="btn btn-warning" id="upgradeToAdminBtn"
                                data-bs-toggle="modal" data-bs-target="#upgradeAdminModal">
                          Upgrade to Admin
                        </button>
                      </div>
                      <div class="modal fade" id="upgradeAdminModal" tabindex="-1"
                           aria-labelledby="upgradeAdminModalLabel" aria-hidden="true">
                        <div class="modal-dialog">
                          <div class="modal-content">
                            <div class="modal-header">
                              <h5 class="modal-title" id="upgradeAdminModalLabel">Upgrade to Admin</h5>
                              <button type="button" class="btn-close" data-bs-dismiss="modal"
                                      aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                              <p>PayPal subscription integration coming soon.</p>
                            </div>
                            <div class="modal-footer">
                              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                          </div>
                        </div>
                      </div>` : ''}
                      <div class="d-flex justify-content-between">
                        <button type="button" class="btn btn-success" id="saveProfileBtn">
                          <i class="bi bi-save me-2"></i>Save Profile
                        </button>
                        <button type="button" class="btn btn-secondary" id="cancelProfileBtn">Cancel</button>
                      </div>
                    </form>
                    <hr>
                    <form id="updatePasswordForm" class="d-flex justify-content-between">
                      <button class="btn btn-primary w-100 me-2" id="updatePasswordBtn">
                        <i class="bi bi-shield-lock-fill me-2"></i>Update Password
                      </button>
                    </form>
                    <hr>
                    <form id="deleteAccountForm">
                      <button class="btn btn-danger w-100">
                        <i class="bi bi-trash-fill me-2"></i>Delete My Account
                      </button>
                    </form>
                  </div>` : `
                  <div id="profileViewMode">
                    ${data.user.profile_picture ? `
                    <div class="profile-picture-container position-relative mx-auto mb-3">
                      <img src="/static/${data.user.profile_picture}"
                          class="profile-picture rounded-circle shadow-lg border border-white border-4"
                          alt="Profile Picture">
                    </div>` : ''}
                    <p><strong>Display Name:</strong> ${data.user.display_name || ''}</p>
                    <p><strong>Age Group:</strong> ${data.user.age_group || ''}</p>
                    <p><strong>Timezone:</strong> ${data.user.timezone || ''}</p>
                    <p><strong>Interests:</strong> ${data.user.interests || ''}</p>
                    <p><strong>Riding Preferences:</strong> ${data.user.riding_preferences.join(', ')}</p>
                    <p><strong>Ride Description:</strong> ${data.user.ride_description || ''}</p>
                  </div>
                `}
              </section>
            </div>

            <!-- 2) BIKE pane -->
            <div class="tab-pane fade" id="bike" role="tabpanel" aria-labelledby="bike-tab">
              <section class="bike mb-4">
                <h2 class="h2">Bike Details</h2>
                ${isCurrent ? `
                  <form id="editBikeForm" class="needs-validation" novalidate>
                    <div class="form-group mb-3">
                      <label for="bikePicture">Upload Your Bicycle Picture:</label>
                      <input type="file" class="form-control" id="bikePicture" name="bike_picture" accept="image/*">
                    </div>
                    ${data.user.bike_picture ? `
                      <div class="form-group mb-3">
                        <label>Current Bicycle Picture:</label>
                        <img src="/static/${data.user.bike_picture}" class="img-fluid rounded shadow-sm" alt="Bicycle Picture">
                      </div>` : ''}
                    <div class="form-group mb-3">
                      <label for="bikeDescription">Bicycle Description:</label>
                      <textarea class="form-control" id="bikeDescription" name="bike_description" rows="3">${data.user.bike_description || ''}</textarea>
                    </div>
                    <div class="d-flex justify-content-between">
                      <button class="btn btn-success" id="saveBikeBtn">
                        <i class="bi bi-save me-2"></i>Save Bike Details
                      </button>
                    </div>
                  </form>` : `
                  <p><strong>Bicycle Description:</strong> ${data.user.bike_description || ''}</p>`}
              </section>
            </div>

            <!-- 3) BADGES EARNED pane -->
            <div class="tab-pane fade" id="badges-earned" role="tabpanel" aria-labelledby="badges-earned-tab">
              <section class="badges-earned mb-4">
                <h2 class="h2">Badges Earned</h2>
                <div class="badge-grid">
                  ${data.user.badges && data.user.badges.length
                    ? data.user.badges.map(badge => `
                      <div class="badge-card">
                        <img src="/static/images/badge_images/${badge.image}" alt="${badge.name}" class="badge-icon" style="width:100px;">
                        <div class="badge-caption">
                          <h3>${badge.name}</h3>
                          <p>${badge.description}</p>
                          <p><strong>Category:</strong> ${badge.category}</p>
                        </div>
                      </div>
                    `).join('') 
                    : '<p class="text-muted">No badges earned yet.</p>'}
                </div>
              </section>
            </div>

            <!-- 4) GAMES PARTICIPATED pane -->
            <div class="tab-pane fade" id="games-participated" role="tabpanel" aria-labelledby="games-participated-tab">
              <section class="games-participated mb-4">
                <h2 class="h2">Games Participated</h2>
                <div class="row g-3">
                  ${data.participated_games && data.participated_games.length
                    ? data.participated_games.map(game => `
                      <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        <h3 class="h5">${game.title}</h3>
                        <p class="text-muted">${game.description}</p>
                        <p><strong>Start Date:</strong> ${game.start_date}</p>
                        <p><strong>End Date:</strong> ${game.end_date}</p>
                      </div>
                    `).join('') 
                    : '<p class="text-muted">No games participated in yet.</p>'}
                </div>
              </section>
            </div>

            <!-- 5) QUEST SUBMISSIONS pane -->
            <div class="tab-pane fade" id="quest-submissions" role="tabpanel" aria-labelledby="quest-submissions-tab">
              <section class="quest-submissions mb-4">
                <h2 class="h2">Quest Submissions</h2>
                <div class="row g-3">
                  ${data.quest_submissions && data.quest_submissions.length
                    ? data.quest_submissions.map(sub => `
                      <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        ${sub.image_url ? `<img src="${sub.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height:200px; object-fit:cover;">` : ''}
                        <p><strong>Quest:</strong> ${sub.quest.title}</p>
                        <p class="text-muted">${sub.comment}</p>
                        <p><strong>Submitted At:</strong> ${sub.timestamp}</p>
                        <div class="d-flex gap-2">
                          ${sub.twitter_url  ? `<a href="${sub.twitter_url}"   target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>`   : ''}
                          ${sub.fb_url       ? `<a href="${sub.fb_url}"        target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>` : ''}
                          ${sub.instagram_url? `<a href="${sub.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>`: ''}
                        </div>
                        ${isCurrent ? `<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${sub.id}">Delete</button>` : ''}
                      </div>
                    `).join('') 
                    : '<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;
      // 2) Set modal title
      const modalTitle = document.getElementById('userProfileModalLabel');
      modalTitle.textContent = `${data.user.display_name || data.user.username}'s Profile`;

      // 2.1) Reset Follow button visibility
      const btn = document.getElementById('followBtn');
      if (btn) {
        btn.style.display = '';      // undo any previous 'display:none'
      }

      // 2.2) Populate follower count
      const followerEl = document.getElementById('followerCount');
      let followerCount = data.user.follower_count;
      function updateFollowerCount() {
        if (followerEl) {
          followerEl.textContent = `${followerCount} follower${followerCount === 1 ? '' : 's'}`;
        }
      }
      updateFollowerCount();

      // 3) Follow/Unfollow button logic
      if (!isCurrent && btn) {
        if (btn) {
          btn.style.display = '';       // clear any previous 'none'
          btn.classList.remove('d-none'); // just in case you ever use that
        }
        let following = data.current_user_following;

        function updateFollowButton() {
          if (following) {
            btn.textContent = 'Following';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-primary');
          } else {
            btn.textContent = 'Follow';
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-primary');
          }
        }

        updateFollowButton();
        btn.onclick = async () => {
          const action = following ? 'unfollow' : 'follow';
          const { status } = await csrfFetchJson(`/profile/${data.user.username}/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });

          if (status !== 200) {
            logger.error('Follow toggle failed');
            return;
          }
          following = !following;
          followerCount += following ? 1 : -1;
          updateFollowButton();
          updateFollowerCount();
        };
      } else {
        // Hide on your own profile
        const btn = document.getElementById('followBtn');
        if (btn) btn.style.display = 'none';
      }

      // 4) Small-screen <select> ↔ tabs synchronization
      openModal('userProfileModal');

      const editBtn = document.getElementById('editProfileBtn');
      if (editBtn) editBtn.addEventListener('click', toggleProfileEditMode);

      const saveBtn = document.getElementById('saveProfileBtn');
      if (saveBtn) saveBtn.addEventListener('click', () => saveProfile(userId));

      const cancelBtn = document.getElementById('cancelProfileBtn');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', evt => {
          evt.preventDefault();
          cancelProfileEdit(userId);
        });
      }

      const updatePasswordBtn = document.getElementById('updatePasswordBtn');
      if (updatePasswordBtn) updatePasswordBtn.addEventListener('click', () => {
        window.location.href = '/auth/update_password';
      });

      const saveBikeBtn = document.getElementById('saveBikeBtn');
      if (saveBikeBtn) saveBikeBtn.addEventListener('click', () => saveBike(userId));

      document.querySelectorAll('[data-delete-submission]').forEach(btn => {
        btn.addEventListener('click', () => {
          const sid = btn.getAttribute('data-delete-submission');
          deleteSubmission(sid, 'profileSubmissions', data.user.id);
        });
      });

      const deleteAccountForm = document.getElementById('deleteAccountForm');
      if (deleteAccountForm) {
        deleteAccountForm.addEventListener('submit', e => {
          e.preventDefault();
          deleteAccount();
        });
      }
      const tabSelect = document.getElementById('profileTabSelect');
      if (tabSelect) {
        tabSelect.addEventListener('change', e => {
          const paneId = e.target.value;
          const trigger = document.querySelector(`#profileTabs a[href="#${paneId}"]`);
          if (trigger) new bootstrap.Tab(trigger).show();
        });
        document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]')
          .forEach(a => {
            a.addEventListener('shown.bs.tab', evt => {
              tabSelect.value = evt.target.getAttribute('href').slice(1);
            });
          });
      }
    })
    .catch(err => {
      logger.error('Failed to load profile:', err);
      alert('Could not load user profile. Please try again.');
    });
}

// Tooltip initialization
document.querySelectorAll('[data-floating-ui-tooltip]').forEach(el => {
  tippy(el, {
    content: el.getAttribute('data-floating-ui-tooltip'),
    placement: 'top',
    animation: 'scale-subtle'
  });
});

// Bootstrap-style validation
document.querySelectorAll('.needs-validation').forEach(form => {
  form.addEventListener('submit', event => {
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopPropagation();
    }
    form.classList.add('was-validated');
  }, false);
});

function toggleProfileEditMode() {
  const viewDiv = document.getElementById('profileViewMode');
  const editDiv = document.getElementById('profileEditMode');
  if (!viewDiv || !editDiv) {
    logger.error('Profile edit mode elements missing');
    return;
  }
  viewDiv.classList.toggle('d-none');
  editDiv.classList.toggle('d-none');
}

function cancelProfileEdit(userId) {
  showUserProfileModal(userId);
}

function saveProfile(userId) {
  const form = document.getElementById('editProfileForm');
  if (!form) {
    logger.error('Edit profile form not found');
    return;
  }
  const formData = new FormData(form);
  const profilePictureInput = document.getElementById('profilePictureInput');
  if (profilePictureInput.files.length > 0) {
    formData.append('profile_picture', profilePictureInput.files[0]);
  }
  const ridingPreferences = [];
  form.querySelectorAll('input[name="riding_preferences"]:checked').forEach(cb => {
    ridingPreferences.push(cb.value);
  });
  formData.delete('riding_preferences');
  ridingPreferences.forEach(pref => {
    formData.append('riding_preferences', pref);
  });
  csrfFetchJson(`/profile/${userId}/edit`, {
    method: 'POST',
    body: formData
  })
    .then(({ json }) => {
      if (json.error) {
        let msg = `Error: ${json.error}`;
        if (json.details) {
          const details = [];
          Object.values(json.details).forEach(errArr => {
            details.push(errArr.join(', '));
          });
          if (details.length) msg += ` - ${details.join('; ')}`;
        }
        alert(msg);
      } else {
        alert('Profile updated successfully.');
        showUserProfileModal(userId);
      }
    })
    .catch(err => {
      logger.error('Error updating profile:', err);
      alert('Failed to update profile. Please try again.');
    });
}

function saveBike(userId) {
  const form = document.getElementById('editBikeForm');
  if (!form) {
    logger.error('Edit bike form not found');
    return;
  }
  const formData = new FormData(form);
  const bikePictureInput = document.getElementById('bikePicture');
  if (bikePictureInput.files.length > 0) {
    formData.append('bike_picture', bikePictureInput.files[0]);
  }
  csrfFetchJson(`/profile/${userId}/edit-bike`, {
    method: 'POST',
    body: formData
  })
    .then(({ json }) => {
      if (json.error) {
        alert(`Error: ${json.error}`);
      } else {
        alert('Bike details updated successfully.');
        showUserProfileModal(userId);
      }
    })
    .catch(err => {
      logger.error('Error updating bike details:', err);
      alert('Failed to update bike details. Please try again.');
    });
}


function deleteSubmission(submissionId, context, userId) {
  csrfFetchJson(`/quests/quest/delete_submission/${submissionId}`, {
    method: 'DELETE'
  })
    .then(({ json }) => {
      if (json.success) {
        alert('Submission deleted successfully.');
        if (context === 'profileSubmissions') showUserProfileModal(userId);
      } else {
        throw new Error(json.message);
      }
    })
    .catch(err => {
      logger.error('Error deleting submission:', err);
      alert('Error during deletion: ' + err.message);
    });
}

function deleteAccount() {
  if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
    return;
  }

  csrfFetchJson('/auth/delete_account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(() => {
      window.location.href = '/';
    })
    .catch(err => {
      logger.error('Error deleting account:', err);
      alert('Failed to delete account. Please try again.');
    });
}

// delegate clicks to open a user profile
document.addEventListener('click', e => {
  const el = e.target.closest('[data-user-profile]');
  if (!el) return;
  e.preventDefault();
  const uid = el.getAttribute('data-user-profile');
  if (uid) showUserProfileModal(uid);
});

