import{l as b,c as I,o as G,e as K,f as R,g as ne,a as re,h as ae,b as le}from"./chunk-B6D9f9jm.js";function T(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,s=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${s}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){b.error("Riding preferences choices missing.");return}const a=document.getElementById("userProfileDetails");if(!a){b.error("Profile details containers not found");return}const r=t.current_user_id===t.user.id;a.innerHTML=`
          <!-- XS: native select dropdown -->
          <div class="d-block d-sm-none mb-3">
            <select id="profileTabSelect" class="form-select">
              <option value="profile" selected>Profile</option>
              <option value="bike">Bike</option>
              ${t.has_badges?'<option value="badges-earned">Badges Earned</option>':""}
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
            ${t.has_badges?`
            <li class="nav-item" role="presentation">
              <a class="nav-link" id="badges-earned-tab" data-bs-toggle="tab"
                 href="#badges-earned" role="tab" aria-controls="badges-earned" aria-selected="false">
                <i class="bi bi-trophy me-2"></i>Badges Earned
              </a>
            </li>`:""}
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
                ${r?`
                  <div id="profileViewMode">
                    ${t.user.profile_picture?`
                      <div class="profile-picture-container position-relative mx-auto mb-3">
                        <img src="/static/${t.user.profile_picture}"
                            class="profile-picture rounded-circle shadow-lg border border-white border-4"
                            alt="Profile Picture">
                      </div>`:""}
                    <p><strong>Display Name:</strong> ${t.user.display_name||""}</p>
                    <p><strong>Age Group:</strong> ${t.user.age_group||""}</p>
                    <p><strong>Timezone:</strong> ${t.user.timezone||""}</p>
                    <p><strong>Interests:</strong> ${t.user.interests||""}</p>
                    <p><strong>Riding Preferences:</strong> ${t.user.riding_preferences.join(", ")}</p>
                    <p><strong>Ride Description:</strong> ${t.user.ride_description||""}</p>
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
                                value="${t.user.display_name||""}" required>
                        <div class="invalid-feedback">Display Name is required.</div>
                      </div>
                      <div class="form-group mb-3">
                        <label for="ageGroup">Age Group:</label>
                        <select class="form-select" id="ageGroup" name="age_group">
                          <option value="teen" ${t.user.age_group==="teen"?"selected":""}>Teen</option>
                          <option value="adult" ${t.user.age_group==="adult"?"selected":""}>Adult</option>
                          <option value="senior" ${t.user.age_group==="senior"?"selected":""}>Senior</option>
                        </select>
                      </div>
                      <div class="form-group mb-3">
                        <label for="timezone">Timezone:</label>
                        <select class="form-select" id="timezone" name="timezone">
                          ${t.timezone_choices.map(d=>`
                            <option value="${d}" ${t.user.timezone===d?"selected":""}>${d}</option>
                          `).join("")}
                        </select>
                      </div>
                      <div class="form-group mb-3">
                        <label for="interests">Interests:</label>
                        <textarea class="form-control" id="interests" name="interests" rows="3"
                                  placeholder="Describe your interests...">${t.user.interests||""}</textarea>
                      </div>
                      <div class="form-group mb-3">
                        <label><b>Please specify your riding preferences:</b></label>
                        <div id="ridingPreferences">
                          ${t.riding_preferences_choices.map((d,B)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${B}" name="riding_preferences"
                                      value="${d[0]}"
                                      ${t.user.riding_preferences.includes(d[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${B}">${d[1]}</label>
                            </div>
                          `).join("")}
                        </div>
                      </div>
                      <div class="form-group mb-3">
                        <label for="rideDescription">Describe the type of riding you like to do:</label>
                        <textarea class="form-control" id="rideDescription" name="ride_description" rows="3">${t.user.ride_description||""}</textarea>
                      </div>
                      <div class="form-check form-switch mb-3">
                        <input class="form-check-input" type="checkbox" id="uploadToSocials" name="upload_to_socials"
                                ${t.user.upload_to_socials?"checked":""}>
                        <label class="form-check-label" for="uploadToSocials">Cross post to game's social media?</label>
                      </div>
                      <div class="form-check form-switch mb-3">
                        <input class="form-check-input" type="checkbox" id="uploadToMastodon" name="upload_to_mastodon"
                                ${t.user.upload_to_mastodon?"checked":""}>
                        <label class="form-check-label" for="uploadToMastodon">Cross post to your federation server?</label>
                      </div>
                      ${t.user.is_admin?"":`
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
                      </div>`}
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
                  </div>`:`
                  <div id="profileViewMode">
                    ${t.user.profile_picture?`
                    <div class="profile-picture-container position-relative mx-auto mb-3">
                      <img src="/static/${t.user.profile_picture}"
                          class="profile-picture rounded-circle shadow-lg border border-white border-4"
                          alt="Profile Picture">
                    </div>`:""}
                    <p><strong>Display Name:</strong> ${t.user.display_name||""}</p>
                    <p><strong>Age Group:</strong> ${t.user.age_group||""}</p>
                    <p><strong>Timezone:</strong> ${t.user.timezone||""}</p>
                    <p><strong>Interests:</strong> ${t.user.interests||""}</p>
                    <p><strong>Riding Preferences:</strong> ${t.user.riding_preferences.join(", ")}</p>
                    <p><strong>Ride Description:</strong> ${t.user.ride_description||""}</p>
                  </div>
                `}
              </section>
            </div>

            <!-- 2) BIKE pane -->
            <div class="tab-pane fade" id="bike" role="tabpanel" aria-labelledby="bike-tab">
              <section class="bike mb-4">
                <h2 class="h2">Bike Details</h2>
                ${r?`
                  <form id="editBikeForm" class="needs-validation" novalidate>
                    <div class="form-group mb-3">
                      <label for="bikePicture">Upload Your Bicycle Picture:</label>
                      <input type="file" class="form-control" id="bikePicture" name="bike_picture" accept="image/*">
                    </div>
                    ${t.user.bike_picture?`
                      <div class="form-group mb-3">
                        <label>Current Bicycle Picture:</label>
                        <img src="/static/${t.user.bike_picture}" class="img-fluid rounded shadow-sm" alt="Bicycle Picture">
                      </div>`:""}
                    <div class="form-group mb-3">
                      <label for="bikeDescription">Bicycle Description:</label>
                      <textarea class="form-control" id="bikeDescription" name="bike_description" rows="3">${t.user.bike_description||""}</textarea>
                    </div>
                    <div class="d-flex justify-content-between">
                      <button class="btn btn-success" id="saveBikeBtn">
                        <i class="bi bi-save me-2"></i>Save Bike Details
                      </button>
                    </div>
                  </form>`:`
                  <p><strong>Bicycle Description:</strong> ${t.user.bike_description||""}</p>`}
              </section>
            </div>

            ${t.has_badges?`
            <!-- 3) BADGES EARNED pane -->
            <div class="tab-pane fade" id="badges-earned" role="tabpanel" aria-labelledby="badges-earned-tab">
              <section class="badges-earned mb-4">
                <h2 class="h2">Badges Earned</h2>
                <div class="badge-grid">
                  ${t.user.badges&&t.user.badges.length?t.user.badges.map(d=>`
                      <div class="badge-card">
                        <img src="/static/images/badge_images/${d.image}" alt="${d.name}" class="badge-icon" style="width:100px;">
                        <div class="badge-caption">
                          <h3>${d.name}</h3>
                          <p>${d.description}</p>
                          <p><strong>Category:</strong> ${d.category}</p>
                        </div>
                      </div>
                    `).join(""):'<p class="text-muted">No badges earned yet.</p>'}
                </div>
              </section>
            </div>
            `:""}

            <!-- 4) GAMES PARTICIPATED pane -->
            <div class="tab-pane fade" id="games-participated" role="tabpanel" aria-labelledby="games-participated-tab">
              <section class="games-participated mb-4">
                <h2 class="h2">Games Participated</h2>
                <div class="row g-3">
                  ${t.participated_games&&t.participated_games.length?t.participated_games.map(d=>`
                      <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        <h3 class="h5">${d.title}</h3>
                        <p class="text-muted">${d.description}</p>
                        <p><strong>Start Date:</strong> ${d.start_date}</p>
                        <p><strong>End Date:</strong> ${d.end_date}</p>
                      </div>
                    `).join(""):'<p class="text-muted">No games participated in yet.</p>'}
                </div>
              </section>
            </div>

            <!-- 5) QUEST SUBMISSIONS pane -->
            <div class="tab-pane fade" id="quest-submissions" role="tabpanel" aria-labelledby="quest-submissions-tab">
              <section class="quest-submissions mb-4">
                <h2 class="h2">Quest Submissions</h2>
                <div class="row g-3">
                  ${t.quest_submissions&&t.quest_submissions.length?t.quest_submissions.map(d=>`
                      <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        ${d.image_url?`<img src="${d.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height:200px; object-fit:cover;">`:""}
                        <p><strong>Quest:</strong> ${d.quest.title}</p>
                        <p class="text-muted">${d.comment}</p>
                        <p><strong>Submitted At:</strong> ${d.timestamp}</p>
                        <div class="d-flex gap-2">
                          ${d.twitter_url?`<a href="${d.twitter_url}"   target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>`:""}
                          ${d.fb_url?`<a href="${d.fb_url}"        target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>`:""}
                          ${d.instagram_url?`<a href="${d.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>`:""}
                        </div>
                        ${r?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${d.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const l=document.getElementById("userProfileModalLabel");l.textContent=`${t.user.display_name||t.user.username}'s Profile`;const m=document.getElementById("followBtn");m&&(m.style.display="");const g=document.getElementById("followerCount");let u=t.user.follower_count;function n(){g&&(g.textContent=`${u} follower${u===1?"":"s"}`)}if(n(),!r&&m){let B=function(){d?(m.textContent="Following",m.classList.remove("btn-primary"),m.classList.add("btn-outline-primary")):(m.textContent="Follow",m.classList.remove("btn-outline-primary"),m.classList.add("btn-primary"))};m&&(m.style.display="",m.classList.remove("d-none"));let d=t.current_user_following;B(),m.onclick=async()=>{const P=d?"unfollow":"follow",{status:U}=await I(`/profile/${t.user.username}/${P}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(U!==200){b.error("Follow toggle failed");return}d=!d,u+=d?1:-1,B(),n()}}else{const d=document.getElementById("followBtn");d&&(d.style.display="none")}G("userProfileModal");const c=document.getElementById("editProfileBtn");c&&c.addEventListener("click",de);const h=document.getElementById("saveProfileBtn");h&&h.addEventListener("click",()=>me(e));const p=document.getElementById("cancelProfileBtn");p&&p.addEventListener("click",d=>{d.preventDefault(),ce(e)});const y=document.getElementById("updatePasswordBtn");y&&y.addEventListener("click",()=>{window.location.href="/auth/update_password"});const w=document.getElementById("saveBikeBtn");w&&w.addEventListener("click",()=>ue(e)),document.querySelectorAll("[data-delete-submission]").forEach(d=>{d.addEventListener("click",()=>{const B=d.getAttribute("data-delete-submission");pe(B,"profileSubmissions",t.user.id)})});const C=document.getElementById("deleteAccountForm");C&&C.addEventListener("submit",d=>{d.preventDefault(),fe()});const E=document.getElementById("profileTabSelect");E&&(E.addEventListener("change",d=>{const B=d.target.value,P=document.querySelector(`#profileTabs a[href="#${B}"]`);P&&new bootstrap.Tab(P).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(d=>{d.addEventListener("shown.bs.tab",B=>{E.value=B.target.getAttribute("href").slice(1)})}))}).catch(t=>{b.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function de(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){b.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function ce(e){T(e)}function me(e){const o=document.getElementById("editProfileForm");if(!o){b.error("Edit profile form not found");return}const i=new FormData(o),s=document.getElementById("profilePictureInput");s.files.length>0&&i.append("profile_picture",s.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(a=>{t.push(a.value)}),i.delete("riding_preferences"),t.forEach(a=>{i.append("riding_preferences",a)}),I(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:a})=>{if(a.error){let r=`Error: ${a.error}`;if(a.details){const l=[];Object.values(a.details).forEach(m=>{l.push(m.join(", "))}),l.length&&(r+=` - ${l.join("; ")}`)}alert(r)}else alert("Profile updated successfully."),T(e)}).catch(a=>{b.error("Error updating profile:",a),alert("Failed to update profile. Please try again.")})}function ue(e){const o=document.getElementById("editBikeForm");if(!o){b.error("Edit bike form not found");return}const i=new FormData(o),s=document.getElementById("bikePicture");s.files.length>0&&i.append("bike_picture",s.files[0]),I(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),T(e))}).catch(t=>{b.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function pe(e,o,i){I(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:s})=>{if(s.success)alert("Submission deleted successfully."),T(i);else throw new Error(s.message)}).catch(s=>{b.error("Error deleting submission:",s),alert("Error during deletion: "+s.message)})}function fe(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&I("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{b.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;e.preventDefault();const i=o.getAttribute("data-user-profile");i&&T(i)});function be(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const ge=Number(be("current-user-id")||0),he=ne(),L=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function X(e){K(),R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!Z(i,s.completions,t,e,a)){b.error("populateQuestDetails – required element missing");return}ee(i,s.completions,a,t),G("questDetailModal"),H(),ie(e)}).catch(o=>{b.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function W(e){R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!Z(i,s.completions,t,e,a)){b.error("populateQuestDetails - required element missing");return}ee(i,s.completions,a,t),H(),ie(e)}).catch(o=>{b.error("Failed to refresh quest detail modal:",o)})}function H(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,s)=>{i.forEach(t=>{if(t.isIntersecting){const a=t.target;a.src=a.getAttribute("data-src"),a.classList.remove("lazyload"),s.unobserve(a)}})});e.forEach(i=>{o.observe(i)})}function Z(e,o,i,s,t){var c,h,p;const a=o>=e.completion_limit?" - complete":"",r={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let y in r)if(!r[y])return b.error(`Error: Missing element ${y}`),!1;const l={badge:(c=r.modalQuestBadgeImage)==null?void 0:c.closest(".quest-detail-item"),badgeAwarded:(h=r.modalQuestBadgeAwarded)==null?void 0:h.closest(".quest-detail-item"),category:(p=r.modalQuestCategory)==null?void 0:p.closest(".quest-detail-item")};for(let y in l)if(!l[y])return b.error(`Error: Missing card element ${y}`),!1;r.modalQuestTitle.innerText=`${e.title}${a}`,r.modalQuestDescription.textContent=e.description,r.modalQuestTips.textContent=e.tips||"No tips available",r.modalQuestPoints.innerText=`${e.points}`,r.modalQuestCategory.innerText=e.category||"No category set";const m=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;r.modalQuestCompletionLimit.innerText=`${m} ${e.frequency}`;const g=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?r.modalQuestBadgeAwarded.innerText=`After ${g}`:r.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":r.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":r.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":r.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":r.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:r.modalQuestVerificationType.innerText="Not specified";break}const u=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:L;r.modalQuestBadgeImage.setAttribute("data-src",u),r.modalQuestBadgeImage.src=L,r.modalQuestBadgeImage.classList.add("lazyload"),r.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(l.badge.classList.add("hidden"),l.badgeAwarded.classList.add("hidden"),l.category.classList.add("hidden")):(l.badge.classList.remove("hidden"),l.badgeAwarded.classList.remove("hidden"),l.category.classList.remove("hidden")),r.modalQuestCompletions.innerText=`Total Completions: ${o}`;const n=t&&new Date(t);return!i&&n&&n>new Date?(r.modalCountdown.innerText=`Next eligible time: ${n.toLocaleString()}`,r.modalCountdown.style.color="red"):(r.modalCountdown.innerText="You are currently eligible to verify!",r.modalCountdown.style.color="green"),Ee(s,i,e.verification_type),!0}function ee(e,o,i,s){const t=document.querySelector(".user-quest-data");if(!t){b.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(r=>{let l=document.getElementById(r.id);l||(l=document.createElement("p"),l.id=r.id,t.appendChild(l)),l.innerText=r.value}),ye(document.getElementById("modalCountdown"),i,s)}function ye(e,o,i){if(!i&&o){const s=new Date(o),t=new Date;if(s>t){const a=s-t;e.innerText=`Next eligible time: ${ve(a)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function ve(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),s=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${s}h ${i}m ${o}s`}function Ee(e,o,i){const s=document.querySelector(".user-quest-data");if(!s){b.error("Parent element .user-quest-data not found");return}if(s.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const a=_e(i.trim().toLowerCase(),e);t.appendChild(a),s.appendChild(t),we(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",s.appendChild(t)}}function _e(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const s=document.createElement("input");s.type="hidden",s.name="csrf_token",s.value=he,i.appendChild(s);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(Q());break;case"comment":i.appendChild(O("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(Q());break;case"photo_comment":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(O("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(Q());break;case"video":i.appendChild(F("video","Upload a Video","video/*")),i.appendChild(O("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(Q());break;case"qr_code":{const a=document.createElement("p");a.className="epic-message",a.textContent="Find and scan the QR code. No submission required here.",i.appendChild(a);break}case"pause":{const a=document.createElement("p");a.className="epic-message",a.textContent="Quest is currently paused.",i.appendChild(a);break}default:{const a=document.createElement("p");a.className="epic-message",a.textContent="Submission requirements are not set correctly.",i.appendChild(a)}}return i}function F(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const r=document.createElement("input");return r.type="file",r.id=e,r.name=e,r.className="epic-input",r.accept=i,r.required=!0,t.appendChild(r),t}function O(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const r=document.createElement("textarea");return r.id=e,r.name=e,r.className="epic-textarea",r.placeholder=i,s&&(r.required=!0),t.appendChild(r),t}function Q(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function we(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){b.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){b.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(s){ke(s,e)})}function V(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function Ce(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function Be(e,o,i){const s=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!s)return;const t=s.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function te(e){V(document.getElementById("twitterLink"),e.twitter_url),V(document.getElementById("facebookLink"),e.fb_url),V(document.getElementById("instagramLink"),e.instagram_url)}let z=!1;async function ke(e,o){if(e.preventDefault(),z)return;z=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{re("Uploading...");const s=e.target.querySelector('input[type="file"]'),t=s?s.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const m=await $e(t);if(isFinite(m)&&m>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const a=new FormData(e.target);a.append("user_id",ge);const{status:r,json:l}=await I(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:a});if(r!==200)throw r===403&&l.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(l.message||`Server responded with status ${r}`);if(!l.success)throw new Error(l.message);if(!l.success)throw new Error(l.message);Ce(l.total_points),te(l),Be(o,l.new_completion_count,l.total_completion_count),W(o),e.target.reset()}catch(s){b.error("Submission error:",s),alert(`Error during submission: ${s.message}`)}finally{z=!1,i&&(i.disabled=!1),ae()}}function $e(e){return new Promise((o,i)=>{try{const s=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(s),o(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(s),i(new Error("metadata error"))},t.src=s}catch(s){i(s)}})}async function ie(e){const o=encodeURIComponent(e);try{const{json:i}=await R(`/quests/quest/${o}/submissions`),s=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),a=document.getElementById("instagramLink");if(i&&i.length){const l=i[0],m=document.getElementById("submissionImage"),g=document.getElementById("submissionVideo"),u=document.getElementById("submissionVideoSource"),n=document.getElementById("submissionComment"),c=document.getElementById("submitterProfileLink"),h=document.getElementById("submitterProfileImage"),p=document.getElementById("submitterProfileCaption");l.video_url?(m.hidden=!0,g.hidden=!1,u.src=l.video_url,g.load()):(g.hidden=!0,m.hidden=!1,m.src=l.image_url||L),n.textContent=l.comment||"No comment provided.",c.href=`/profile/${encodeURIComponent(l.user_id)}`,h.src=l.user_profile_picture||L,p.textContent=l.user_display_name||l.user_username||`User ${l.user_id}`,te(l)}else[s,t,a].forEach(l=>{l&&(l.style.display="none")});const r=i.slice().reverse().map(l=>({id:l.id,url:l.image_url||(l.video_url?null:L),video_url:l.video_url,alt:"Submission Image",comment:l.comment,user_id:l.user_id,user_display_name:l.user_display_name,user_username:l.user_username,user_profile_picture:l.user_profile_picture,twitter_url:l.twitter_url,fb_url:l.fb_url,instagram_url:l.instagram_url,quest_id:e}));Ie(r)}catch(i){b.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function J(e){if(!e)return b.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(s=>o.pathname.toLowerCase().endsWith(s))}catch{return b.error(`Invalid URL detected: ${e}`),!1}return!1}function Ie(e){var m;const o=document.getElementById("submissionBoard");if(!o){b.error("submissionBoard element not found");return}o.innerHTML="";const i=((m=document.getElementById("questDetailModal"))==null?void 0:m.getAttribute("data-placeholder-url"))||L,s=J(i)?i:L,t=g=>g.startsWith("/static/"),a=g=>g.replace(/^\/static\//,""),r=window.innerWidth<=480?70:100,l=Math.round(r*(window.devicePixelRatio||2));e.forEach(g=>{let u;if(g.video_url)u=document.createElement("video"),u.src=g.video_url,u.preload="metadata",u.muted=!0,u.playsInline=!0,u.style.objectFit="cover";else{u=document.createElement("img");const n=J(g.url)?g.url:s,c=t(n)?`/resize_image?path=${encodeURIComponent(a(n))}&width=${l}`:n;u.src=L,u.setAttribute("data-src",c),u.classList.add("lazyload"),u.alt=g.alt||"Submission Image"}u.style.width=`${r}px`,u.style.height="auto",u.style.marginRight="10px",g.video_url||(u.onerror=()=>{t(s)?u.src=`/resize_image?path=${encodeURIComponent(a(s))}&width=${l}`:u.src=encodeURI(s)}),u.onclick=()=>N(g),o.appendChild(u)}),H()}function xe(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),X(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),xe(i))});const Pe=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:X,refreshQuestDetailModal:W},Symbol.toStringTag,{value:"Module"}));let N,$=[],x=-1,S=!1,j=new Image,D=null,q=null;document.addEventListener("DOMContentLoaded",()=>{const e=n=>document.querySelector(n);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),s=document.getElementById("prevSubmissionBtn"),t=document.getElementById("nextSubmissionBtn"),a=document.querySelector('meta[name="placeholder-image"]').getAttribute("content"),r=()=>{const n=e("#submissionImage"),c=e("#submissionVideo"),h=e("#submissionVideoSource");n&&(n.src=""),c&&h&&(c.pause(),h.src="",c.load()),j.src=""},l=()=>{if(j.src="",!Array.isArray($))return;const n=$[x+1];!n||n.video_url||(j.src=n.url)};N=function(n){const c=e("#submissionDetailModal");c.dataset.submissionId=n.id,c.dataset.questId=n.quest_id||"",S=!!(n.read_only||n.readOnly),Array.isArray(n.album_items)&&($=n.album_items,x=Number.isInteger(n.album_index)?n.album_index:-1),r(),D&&D.abort(),q&&q.abort();const h=Number(c.dataset.currentUserId),p=Number(n.user_id)===h,y=c.dataset.isAdmin==="True"||c.dataset.isAdmin==="true",w=e("#editPhotoBtn"),C=e("#photoEditControls"),E=e("#submissionPhotoInput"),d=e("#savePhotoBtn"),B=e("#cancelPhotoBtn"),P=e("#deleteSubmissionBtn");w.hidden=!p||S,P.hidden=!(p||y),C.hidden=!0,w.onclick=()=>{C.hidden=!1,w.hidden=!0,E&&E.click()},B.onclick=()=>{E.value="",C.hidden=!0,w.hidden=!1},P.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const k=c.dataset.submissionId;I(`/quests/quest/delete_submission/${k}`,{method:"POST"}).then(({json:v})=>{if(!v.success)throw new Error(v.message||"Delete failed");le("submissionDetailModal"),K(),c.dataset.questId&&W(c.dataset.questId),alert("Submission deleted successfully.")}).catch(v=>alert("Error deleting submission: "+v.message))},d.onclick=async()=>{const k=c.dataset.submissionId,v=E.files[0];if(!v)return alert("Please select an image first.");if(v.type.startsWith("video/")&&v.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(v.type.startsWith("image/")&&v.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const A=new FormData;if(v.type.startsWith("video/")){try{const _=await U(v);if(isFinite(_)&&_>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}A.append("video",v)}else A.append("photo",v);I(`/quests/submission/${k}/photo`,{method:"PUT",body:A}).then(({json:_})=>{if(!_.success)throw new Error(_.message||"Upload failed");_.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=_.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=_.image_url),B.click()}).catch(_=>alert(_.message))};function U(k){return new Promise((v,A)=>{try{const _=URL.createObjectURL(k),M=document.createElement("video");M.preload="metadata",M.onloadedmetadata=()=>{URL.revokeObjectURL(_),v(M.duration||0)},M.onerror=()=>{URL.revokeObjectURL(_),A(new Error("metadata error"))},M.src=_}catch(_){A(_)}})}e("#submissionReplyEdit").hidden=p,e("#postReplyBtn").hidden=p,e("#ownerNotice").hidden=!p;const Y=e("#submissionRepliesContainer");p?Y.hidden=!0:Y.hidden=!1;const f={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}};f.profileImg.src=n.user_profile_picture||a,f.profileImgOverlay.src=f.profileImg.src,f.profileCap.textContent=n.user_display_name||n.user_username||"—",f.profileLink.onclick=k=>{k.preventDefault(),T(n.user_id)},f.imgOverlay.parentElement.onclick=f.profileLink.onclick;const oe=a;if(n.video_url?(f.img.hidden=!0,f.video.hidden=!1,f.videoSource.src=n.video_url,f.video.load()):(f.video.hidden=!0,f.img.hidden=!1,f.img.src=n.url||oe),f.commentRead.textContent=n.comment||"No comment provided.",["tw","fb","ig"].forEach(k=>{const v=k==="tw"?"twitter_url":k==="fb"?"fb_url":"instagram_url";try{new URL(n[v]),f.social[k].href=n[v],f.social[k].style.display="inline-block"}catch{f.social[k].style.display="none"}}),S){f.editBtn.hidden=!0,f.readBox.hidden=!0,f.commentEdit.hidden=!0,f.editBox.hidden=!0;const k=e("#submissionRepliesContainer");k&&(k.style.display="none")}else p?(f.editBtn.hidden=!1,f.readBox.hidden=!1):f.editBtn.hidden=f.readBox.hidden=f.commentEdit.hidden=f.editBox.hidden=!0;const se=Array.isArray($)&&$.length>0&&x>=0;s&&t&&(se?(s.style.display="inline-flex",t.style.display="inline-flex",s.disabled=x<=0,t.disabled=x>=$.length-1):(s.style.display="none",t.style.display="none")),g(),l(),G("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),m(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const n=e("#submissionDetailModal").dataset.submissionId;I(`/quests/submission/${n}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:c})=>{if(!c.success)throw new Error(c.message||"Save failed");e("#submissionComment").textContent=c.comment||"No comment provided.",m(!1)}).catch(c=>alert(`Could not save comment: ${c.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>m(!1));function m(n){e("#submissionComment").hidden=n,e("#commentReadButtons").hidden=n,e("#submissionCommentEdit").hidden=!n,e("#commentEditButtons").hidden=!n}function g(){const n=e("#submissionDetailModal").dataset.submissionId;n&&(D&&D.abort(),D=new AbortController,R(`/quests/submissions/${n}`,{signal:D.signal}).then(({json:c})=>{e("#submissionLikeCount").textContent=c.like_count||0,e("#submissionLikeBtn").classList.toggle("active",c.liked_by_current_user)}).catch(c=>{c.name!=="AbortError"&&console.error(c)}),S||(q&&q.abort(),q=new AbortController,R(`/quests/submission/${n}/replies`,{signal:q.signal}).then(({json:c})=>{const h=e("#submissionRepliesList");if(!h)return;h.innerHTML="",c.replies.forEach(w=>{const C=document.createElement("div");C.className="reply mb-1";const E=document.createElement("a");E.href="#",E.className="reply-user-link",E.dataset.userId=w.user_id;const d=document.createElement("strong");d.textContent=w.user_display,E.appendChild(d),C.appendChild(E),C.appendChild(document.createTextNode(`: ${w.content}`)),E.addEventListener("click",B=>{B.preventDefault(),T(w.user_id)}),h.appendChild(C)});const p=e("#submissionReplyEdit"),y=e("#postReplyBtn");c.replies.length>=10?(p.disabled=!0,y.disabled=!0,i&&(i.style.display="block")):(p.disabled=!1,y.disabled=!1,i&&(i.style.display="none"))}).catch(c=>{c.name!=="AbortError"&&console.error(c)})))}e("#submissionLikeBtn").addEventListener("click",()=>{const n=e("#submissionLikeBtn"),c=e("#submissionDetailModal").dataset.submissionId,h=n.classList.contains("active");I(`/quests/submission/${c}/like`,{method:h?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:p})=>{if(!p.success)throw new Error("Like failed");e("#submissionLikeCount").textContent=p.like_count,n.classList.toggle("active",p.liked)}).catch(p=>alert(p.message))}),e("#postReplyBtn").addEventListener("click",()=>{if(S)return;const n=e("#submissionDetailModal").dataset.submissionId,c=e("#submissionReplyEdit"),h=c.value.trim();!n||!h||I(`/quests/submission/${n}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:h})}).then(({status:p,json:y})=>{if(!y.success){if(y.message==="Reply limit of 10 reached"){u();return}if(p===409&&y.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(y.message||"Error")}const w=e("#submissionRepliesList"),C=document.createElement("div");C.className="reply mb-1";const E=document.createElement("strong");E.textContent=y.reply.user_display,C.appendChild(E),C.appendChild(document.createTextNode(`: ${y.reply.content}`)),w.insertBefore(C,w.firstChild),c.value="",w.children.length>=10&&u()}).catch(p=>alert(p.message))});function u(){const n=e("#submissionReplyEdit"),c=e("#postReplyBtn");n.disabled=!0,c.disabled=!0,i&&(i.style.display="block")}s&&s.addEventListener("click",()=>{if(!Array.isArray($)||x<=0)return;const n=x-1,c=$[n];c&&N({...c,read_only:S,album_items:$,album_index:n})}),t&&t.addEventListener("click",()=>{if(!Array.isArray($)||x>=$.length-1)return;const n=x+1,c=$[n];c&&N({...c,read_only:S,album_items:$,album_index:n})})});export{T as a,Pe as q,N as s};
