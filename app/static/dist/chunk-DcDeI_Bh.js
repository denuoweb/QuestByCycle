import{l as b,c as x,o as G,e as K,f as R,g as ae,a as le,h as de,b as ce}from"./chunk-BCdQlTZx.js";function T(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,s=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${s}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){b.error("Riding preferences choices missing.");return}const a=document.getElementById("userProfileDetails");if(!a){b.error("Profile details containers not found");return}const r=t.current_user_id===t.user.id;a.innerHTML=`
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
                          ${t.timezone_choices.map(c=>`
                            <option value="${c}" ${t.user.timezone===c?"selected":""}>${c}</option>
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
                          ${t.riding_preferences_choices.map((c,B)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${B}" name="riding_preferences"
                                      value="${c[0]}"
                                      ${t.user.riding_preferences.includes(c[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${B}">${c[1]}</label>
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
                  ${t.user.badges&&t.user.badges.length?t.user.badges.map(c=>`
                      <div class="badge-card">
                        <img src="/static/images/badge_images/${c.image}" alt="${c.name}" class="badge-icon" style="width:100px;">
                        <div class="badge-caption">
                          <h3>${c.name}</h3>
                          <p>${c.description}</p>
                          <p><strong>Category:</strong> ${c.category}</p>
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
                  ${t.participated_games&&t.participated_games.length?t.participated_games.map(c=>`
                      <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        <h3 class="h5">${c.title}</h3>
                        <p class="text-muted">${c.description}</p>
                        <p><strong>Start Date:</strong> ${c.start_date}</p>
                        <p><strong>End Date:</strong> ${c.end_date}</p>
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
                  ${t.quest_submissions&&t.quest_submissions.length?t.quest_submissions.map(c=>`
                      <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        ${c.image_url?`<img src="${c.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height:200px; object-fit:cover;">`:""}
                        <p><strong>Quest:</strong> ${c.quest.title}</p>
                        <p class="text-muted">${c.comment}</p>
                        <p><strong>Submitted At:</strong> ${c.timestamp}</p>
                        <div class="d-flex gap-2">
                          ${c.twitter_url?`<a href="${c.twitter_url}"   target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>`:""}
                          ${c.fb_url?`<a href="${c.fb_url}"        target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>`:""}
                          ${c.instagram_url?`<a href="${c.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>`:""}
                        </div>
                        ${r?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${c.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const l=document.getElementById("userProfileModalLabel");l.textContent=`${t.user.display_name||t.user.username}'s Profile`;const m=document.getElementById("followBtn");m&&(m.style.display="");const g=document.getElementById("followerCount");let p=t.user.follower_count;function n(){g&&(g.textContent=`${p} follower${p===1?"":"s"}`)}if(n(),!r&&m){let B=function(){c?(m.textContent="Following",m.classList.remove("btn-primary"),m.classList.add("btn-outline-primary")):(m.textContent="Follow",m.classList.remove("btn-outline-primary"),m.classList.add("btn-primary"))};m&&(m.style.display="",m.classList.remove("d-none"));let c=t.current_user_following;B(),m.onclick=async()=>{const P=c?"unfollow":"follow",{status:U}=await x(`/profile/${t.user.username}/${P}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(U!==200){b.error("Follow toggle failed");return}c=!c,p+=c?1:-1,B(),n()}}else{const c=document.getElementById("followBtn");c&&(c.style.display="none")}G("userProfileModal");const d=document.getElementById("editProfileBtn");d&&d.addEventListener("click",me);const h=document.getElementById("saveProfileBtn");h&&h.addEventListener("click",()=>pe(e));const f=document.getElementById("cancelProfileBtn");f&&f.addEventListener("click",c=>{c.preventDefault(),ue(e)});const y=document.getElementById("updatePasswordBtn");y&&y.addEventListener("click",()=>{window.location.href="/auth/update_password"});const k=document.getElementById("saveBikeBtn");k&&k.addEventListener("click",()=>fe(e)),document.querySelectorAll("[data-delete-submission]").forEach(c=>{c.addEventListener("click",()=>{const B=c.getAttribute("data-delete-submission");be(B,"profileSubmissions",t.user.id)})});const C=document.getElementById("deleteAccountForm");C&&C.addEventListener("submit",c=>{c.preventDefault(),ge()});const E=document.getElementById("profileTabSelect");E&&(E.addEventListener("change",c=>{const B=c.target.value,P=document.querySelector(`#profileTabs a[href="#${B}"]`);P&&new bootstrap.Tab(P).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(c=>{c.addEventListener("shown.bs.tab",B=>{E.value=B.target.getAttribute("href").slice(1)})}))}).catch(t=>{b.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function me(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){b.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function ue(e){T(e)}function pe(e){const o=document.getElementById("editProfileForm");if(!o){b.error("Edit profile form not found");return}const i=new FormData(o),s=document.getElementById("profilePictureInput");s.files.length>0&&i.append("profile_picture",s.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(a=>{t.push(a.value)}),i.delete("riding_preferences"),t.forEach(a=>{i.append("riding_preferences",a)}),x(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:a})=>{if(a.error){let r=`Error: ${a.error}`;if(a.details){const l=[];Object.values(a.details).forEach(m=>{l.push(m.join(", "))}),l.length&&(r+=` - ${l.join("; ")}`)}alert(r)}else alert("Profile updated successfully."),T(e)}).catch(a=>{b.error("Error updating profile:",a),alert("Failed to update profile. Please try again.")})}function fe(e){const o=document.getElementById("editBikeForm");if(!o){b.error("Edit bike form not found");return}const i=new FormData(o),s=document.getElementById("bikePicture");s.files.length>0&&i.append("bike_picture",s.files[0]),x(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),T(e))}).catch(t=>{b.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function be(e,o,i){x(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:s})=>{if(s.success)alert("Submission deleted successfully."),T(i);else throw new Error(s.message)}).catch(s=>{b.error("Error deleting submission:",s),alert("Error during deletion: "+s.message)})}function ge(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&x("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{b.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;e.preventDefault();const i=o.getAttribute("data-user-profile");i&&T(i)});function he(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const ye=Number(he("current-user-id")||0),ve=ae(),L=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function X(e){K(),R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!Z(i,s.completions,t,e,a)){b.error("populateQuestDetails – required element missing");return}ee(i,s.completions,a,t),G("questDetailModal"),H(),ie(e)}).catch(o=>{b.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function W(e){R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!Z(i,s.completions,t,e,a)){b.error("populateQuestDetails - required element missing");return}ee(i,s.completions,a,t),H(),ie(e)}).catch(o=>{b.error("Failed to refresh quest detail modal:",o)})}function H(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,s)=>{i.forEach(t=>{if(t.isIntersecting){const a=t.target;a.src=a.getAttribute("data-src"),a.classList.remove("lazyload"),s.unobserve(a)}})});e.forEach(i=>{o.observe(i)})}function Z(e,o,i,s,t){var d,h,f;const a=o>=e.completion_limit?" - complete":"",r={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let y in r)if(!r[y])return b.error(`Error: Missing element ${y}`),!1;const l={badge:(d=r.modalQuestBadgeImage)==null?void 0:d.closest(".quest-detail-item"),badgeAwarded:(h=r.modalQuestBadgeAwarded)==null?void 0:h.closest(".quest-detail-item"),category:(f=r.modalQuestCategory)==null?void 0:f.closest(".quest-detail-item")};for(let y in l)if(!l[y])return b.error(`Error: Missing card element ${y}`),!1;r.modalQuestTitle.innerText=`${e.title}${a}`,r.modalQuestDescription.textContent=e.description,r.modalQuestTips.textContent=e.tips||"No tips available",r.modalQuestPoints.innerText=`${e.points}`,r.modalQuestCategory.innerText=e.category||"No category set";const m=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;r.modalQuestCompletionLimit.innerText=`${m} ${e.frequency}`;const g=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?r.modalQuestBadgeAwarded.innerText=`After ${g}`:r.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":r.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":r.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":r.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":r.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:r.modalQuestVerificationType.innerText="Not specified";break}const p=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:L;r.modalQuestBadgeImage.setAttribute("data-src",p),r.modalQuestBadgeImage.src=L,r.modalQuestBadgeImage.classList.add("lazyload"),r.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(l.badge.classList.add("hidden"),l.badgeAwarded.classList.add("hidden"),l.category.classList.add("hidden")):(l.badge.classList.remove("hidden"),l.badgeAwarded.classList.remove("hidden"),l.category.classList.remove("hidden")),r.modalQuestCompletions.innerText=`Total Completions: ${o}`;const n=t&&new Date(t);return!i&&n&&n>new Date?(r.modalCountdown.innerText=`Next eligible time: ${n.toLocaleString()}`,r.modalCountdown.style.color="red"):(r.modalCountdown.innerText="You are currently eligible to verify!",r.modalCountdown.style.color="green"),we(s,i,e.verification_type),!0}function ee(e,o,i,s){const t=document.querySelector(".user-quest-data");if(!t){b.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(r=>{let l=document.getElementById(r.id);l||(l=document.createElement("p"),l.id=r.id,t.appendChild(l)),l.innerText=r.value}),_e(document.getElementById("modalCountdown"),i,s)}function _e(e,o,i){if(!i&&o){const s=new Date(o),t=new Date;if(s>t){const a=s-t;e.innerText=`Next eligible time: ${Ee(a)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function Ee(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),s=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${s}h ${i}m ${o}s`}function we(e,o,i){const s=document.querySelector(".user-quest-data");if(!s){b.error("Parent element .user-quest-data not found");return}if(s.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const a=ke(i.trim().toLowerCase(),e);t.appendChild(a),s.appendChild(t),Ce(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",s.appendChild(t)}}function ke(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const s=document.createElement("input");s.type="hidden",s.name="csrf_token",s.value=ve,i.appendChild(s);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(Q());break;case"comment":i.appendChild(O("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(Q());break;case"photo_comment":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(O("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(Q());break;case"video":i.appendChild(F("video","Upload a Video","video/*")),i.appendChild(O("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(Q());break;case"qr_code":{const a=document.createElement("p");a.className="epic-message",a.textContent="Find and scan the QR code. No submission required here.",i.appendChild(a);break}case"pause":{const a=document.createElement("p");a.className="epic-message",a.textContent="Quest is currently paused.",i.appendChild(a);break}default:{const a=document.createElement("p");a.className="epic-message",a.textContent="Submission requirements are not set correctly.",i.appendChild(a)}}return i}function F(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const r=document.createElement("input");return r.type="file",r.id=e,r.name=e,r.className="epic-input",r.accept=i,r.required=!0,t.appendChild(r),t}function O(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const r=document.createElement("textarea");return r.id=e,r.name=e,r.className="epic-textarea",r.placeholder=i,s&&(r.required=!0),t.appendChild(r),t}function Q(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function Ce(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){b.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){b.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(s){Ie(s,e)})}function V(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function Be(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function $e(e,o,i){const s=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!s)return;const t=s.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function te(e){V(document.getElementById("twitterLink"),e.twitter_url),V(document.getElementById("facebookLink"),e.fb_url),V(document.getElementById("instagramLink"),e.instagram_url)}let z=!1;async function Ie(e,o){if(e.preventDefault(),z)return;z=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{le("Uploading...");const s=e.target.querySelector('input[type="file"]'),t=s?s.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const m=await xe(t);if(isFinite(m)&&m>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const a=new FormData(e.target);a.append("user_id",ye);const{status:r,json:l}=await x(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:a});if(r!==200)throw r===403&&l.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(l.message||`Server responded with status ${r}`);if(!l.success)throw new Error(l.message);if(!l.success)throw new Error(l.message);Be(l.total_points),te(l),$e(o,l.new_completion_count,l.total_completion_count),W(o),e.target.reset()}catch(s){b.error("Submission error:",s),alert(`Error during submission: ${s.message}`)}finally{z=!1,i&&(i.disabled=!1),de()}}function xe(e){return new Promise((o,i)=>{try{const s=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(s),o(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(s),i(new Error("metadata error"))},t.src=s}catch(s){i(s)}})}async function ie(e){const o=encodeURIComponent(e);try{const{json:i}=await R(`/quests/quest/${o}/submissions`),s=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),a=document.getElementById("instagramLink");if(i&&i.length){const l=i[0],m=document.getElementById("submissionImage"),g=document.getElementById("submissionVideo"),p=document.getElementById("submissionVideoSource"),n=document.getElementById("submissionComment"),d=document.getElementById("submitterProfileLink"),h=document.getElementById("submitterProfileImage"),f=document.getElementById("submitterProfileCaption");l.video_url?(m.hidden=!0,g.hidden=!1,p.src=l.video_url,g.load()):(g.hidden=!0,m.hidden=!1,m.src=l.image_url||L),n.textContent=l.comment||"No comment provided.",d.href=`/profile/${encodeURIComponent(l.user_id)}`,h.src=l.user_profile_picture||L,f.textContent=l.user_display_name||l.user_username||`User ${l.user_id}`,te(l)}else[s,t,a].forEach(l=>{l&&(l.style.display="none")});const r=i.slice().reverse().map(l=>({id:l.id,url:l.image_url||(l.video_url?null:L),video_url:l.video_url,alt:"Submission Image",comment:l.comment,user_id:l.user_id,user_display_name:l.user_display_name,user_username:l.user_username,user_profile_picture:l.user_profile_picture,twitter_url:l.twitter_url,fb_url:l.fb_url,instagram_url:l.instagram_url,quest_id:e}));Le(r)}catch(i){b.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function J(e){if(!e)return b.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(s=>o.pathname.toLowerCase().endsWith(s))}catch{return b.error(`Invalid URL detected: ${e}`),!1}return!1}function Le(e){var m;const o=document.getElementById("submissionBoard");if(!o){b.error("submissionBoard element not found");return}o.innerHTML="";const i=((m=document.getElementById("questDetailModal"))==null?void 0:m.getAttribute("data-placeholder-url"))||L,s=J(i)?i:L,t=g=>g.startsWith("/static/"),a=g=>g.replace(/^\/static\//,""),r=window.innerWidth<=480?70:100,l=Math.round(r*(window.devicePixelRatio||2));e.forEach(g=>{let p;if(g.video_url)p=document.createElement("video"),p.src=g.video_url,p.preload="metadata",p.muted=!0,p.playsInline=!0,p.style.objectFit="cover";else{p=document.createElement("img");const n=J(g.url)?g.url:s,d=t(n)?`/resize_image?path=${encodeURIComponent(a(n))}&width=${l}`:n;p.src=L,p.setAttribute("data-src",d),p.classList.add("lazyload"),p.alt=g.alt||"Submission Image"}p.style.width=`${r}px`,p.style.height="auto",p.style.marginRight="10px",g.video_url||(p.onerror=()=>{t(s)?p.src=`/resize_image?path=${encodeURIComponent(a(s))}&width=${l}`:p.src=encodeURI(s)}),p.onclick=()=>N(g),o.appendChild(p)}),H()}function Pe(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),X(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),Pe(i))});const Te=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:X,refreshQuestDetailModal:W},Symbol.toStringTag,{value:"Module"}));let N,_=[],I=-1,S=!1,j=new Image,D=null,q=null;document.addEventListener("DOMContentLoaded",()=>{const e=n=>document.querySelector(n);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),s=document.getElementById("prevSubmissionBtn"),t=document.getElementById("nextSubmissionBtn"),a=document.querySelector('meta[name="placeholder-image"]').getAttribute("content"),r=()=>{const n=e("#submissionImage"),d=e("#submissionVideo"),h=e("#submissionVideoSource");n&&(n.src=""),d&&h&&(d.pause(),h.src="",d.load()),j.src=""},l=()=>{if(j.src="",!Array.isArray(_))return;const n=_[I+1];!n||n.video_url||(j.src=n.url)};N=function(n){const d=e("#submissionDetailModal");d.dataset.submissionId=n.id,d.dataset.questId=n.quest_id||"",S=!!(n.read_only||n.readOnly),Array.isArray(n.album_items)&&(_=n.album_items,I=Number.isInteger(n.album_index)?n.album_index:-1),r(),D&&D.abort(),q&&q.abort();const h=Number(d.dataset.currentUserId),f=Number(n.user_id)===h,y=d.dataset.isAdmin==="True"||d.dataset.isAdmin==="true",k=e("#editPhotoBtn"),C=e("#photoEditControls"),E=e("#submissionPhotoInput"),c=e("#savePhotoBtn"),B=e("#cancelPhotoBtn"),P=e("#deleteSubmissionBtn");k.hidden=!f||S,P.hidden=!(f||y),C.hidden=!0,k.onclick=()=>{C.hidden=!1,k.hidden=!0,E&&E.click()},B.onclick=()=>{E.value="",C.hidden=!0,k.hidden=!1},P.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const $=d.dataset.submissionId;x(`/quests/quest/delete_submission/${$}`,{method:"POST"}).then(({json:v})=>{if(!v.success)throw new Error(v.message||"Delete failed");ce("submissionDetailModal"),K(),d.dataset.questId&&W(d.dataset.questId),alert("Submission deleted successfully.")}).catch(v=>alert("Error deleting submission: "+v.message))},c.onclick=async()=>{const $=d.dataset.submissionId,v=E.files[0];if(!v)return alert("Please select an image first.");if(v.type.startsWith("video/")&&v.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(v.type.startsWith("image/")&&v.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const A=new FormData;if(v.type.startsWith("video/")){try{const w=await U(v);if(isFinite(w)&&w>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}A.append("video",v)}else A.append("photo",v);x(`/quests/submission/${$}/photo`,{method:"PUT",body:A}).then(({json:w})=>{if(!w.success)throw new Error(w.message||"Upload failed");w.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=w.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=w.image_url),B.click()}).catch(w=>alert(w.message))};function U($){return new Promise((v,A)=>{try{const w=URL.createObjectURL($),M=document.createElement("video");M.preload="metadata",M.onloadedmetadata=()=>{URL.revokeObjectURL(w),v(M.duration||0)},M.onerror=()=>{URL.revokeObjectURL(w),A(new Error("metadata error"))},M.src=w}catch(w){A(w)}})}e("#submissionReplyEdit").hidden=f,e("#postReplyBtn").hidden=f,e("#ownerNotice").hidden=!f;const Y=e("#submissionRepliesContainer");f?Y.hidden=!0:Y.hidden=!1;const u={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}},oe=e("#submissionLikeBtn"),se=e("#submissionLikeCount");se.textContent=Number.isInteger(n.like_count)?n.like_count:0,oe.classList.toggle("active",!!n.liked_by_current_user),u.profileImg.src=n.user_profile_picture||a,u.profileImgOverlay.src=u.profileImg.src,u.profileCap.textContent=n.user_display_name||n.user_username||"—",u.profileLink.onclick=$=>{$.preventDefault(),T(n.user_id)},u.profileImg.onclick=u.profileLink.onclick,u.profileCap.onclick=u.profileLink.onclick,u.imgOverlay.parentElement.onclick=u.profileLink.onclick;const ne=a;if(n.video_url?(u.img.hidden=!0,u.video.hidden=!1,u.videoSource.src=n.video_url,u.video.load()):(u.video.hidden=!0,u.img.hidden=!1,u.img.src=n.url||ne),u.commentRead.textContent=n.comment||"No comment provided.",["tw","fb","ig"].forEach($=>{const v=$==="tw"?"twitter_url":$==="fb"?"fb_url":"instagram_url";try{new URL(n[v]),u.social[$].href=n[v],u.social[$].style.display="inline-block"}catch{u.social[$].style.display="none"}}),S){u.editBtn.hidden=!0,u.readBox.hidden=!0,u.commentEdit.hidden=!0,u.editBox.hidden=!0;const $=e("#submissionRepliesContainer");$&&($.style.display="none")}else f?(u.editBtn.hidden=!1,u.readBox.hidden=!1):u.editBtn.hidden=u.readBox.hidden=u.commentEdit.hidden=u.editBox.hidden=!0;const re=Array.isArray(_)&&_.length>0&&I>=0;s&&t&&(re?(s.style.display="inline-flex",t.style.display="inline-flex",s.disabled=I<=0,t.disabled=I>=_.length-1):(s.style.display="none",t.style.display="none")),g(),l(),G("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),m(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const n=e("#submissionDetailModal").dataset.submissionId;x(`/quests/submission/${n}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:d})=>{if(!d.success)throw new Error(d.message||"Save failed");e("#submissionComment").textContent=d.comment||"No comment provided.",m(!1)}).catch(d=>alert(`Could not save comment: ${d.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>m(!1));function m(n){e("#submissionComment").hidden=n,e("#commentReadButtons").hidden=n,e("#submissionCommentEdit").hidden=!n,e("#commentEditButtons").hidden=!n}function g(){const n=e("#submissionDetailModal").dataset.submissionId;n&&(D&&D.abort(),D=new AbortController,R(`/quests/submissions/${n}`,{signal:D.signal}).then(({json:d})=>{e("#submissionLikeCount").textContent=d.like_count||0,e("#submissionLikeBtn").classList.toggle("active",d.liked_by_current_user),Array.isArray(_)&&I>=0&&(_[I].like_count=d.like_count,_[I].liked_by_current_user=d.liked_by_current_user)}).catch(d=>{d.name!=="AbortError"&&console.error(d)}),S||(q&&q.abort(),q=new AbortController,R(`/quests/submission/${n}/replies`,{signal:q.signal}).then(({json:d})=>{const h=e("#submissionRepliesList");if(!h)return;h.innerHTML="",d.replies.forEach(k=>{const C=document.createElement("div");C.className="reply mb-1";const E=document.createElement("a");E.href="#",E.className="reply-user-link",E.dataset.userId=k.user_id;const c=document.createElement("strong");c.textContent=k.user_display,E.appendChild(c),C.appendChild(E),C.appendChild(document.createTextNode(`: ${k.content}`)),E.addEventListener("click",B=>{B.preventDefault(),T(k.user_id)}),h.appendChild(C)});const f=e("#submissionReplyEdit"),y=e("#postReplyBtn");d.replies.length>=10?(f.disabled=!0,y.disabled=!0,i&&(i.style.display="block")):(f.disabled=!1,y.disabled=!1,i&&(i.style.display="none"))}).catch(d=>{d.name!=="AbortError"&&console.error(d)})))}e("#submissionLikeBtn").addEventListener("click",()=>{const n=e("#submissionLikeBtn"),d=e("#submissionDetailModal").dataset.submissionId,h=n.classList.contains("active");x(`/quests/submission/${d}/like`,{method:h?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:f})=>{if(!f.success)throw new Error("Like failed");e("#submissionLikeCount").textContent=f.like_count,n.classList.toggle("active",f.liked),Array.isArray(_)&&I>=0&&(_[I].like_count=f.like_count,_[I].liked_by_current_user=f.liked)}).catch(f=>alert(f.message))}),e("#postReplyBtn").addEventListener("click",()=>{if(S)return;const n=e("#submissionDetailModal").dataset.submissionId,d=e("#submissionReplyEdit"),h=d.value.trim();!n||!h||x(`/quests/submission/${n}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:h})}).then(({status:f,json:y})=>{if(!y.success){if(y.message==="Reply limit of 10 reached"){p();return}if(f===409&&y.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(y.message||"Error")}const k=e("#submissionRepliesList"),C=document.createElement("div");C.className="reply mb-1";const E=document.createElement("strong");E.textContent=y.reply.user_display,C.appendChild(E),C.appendChild(document.createTextNode(`: ${y.reply.content}`)),k.insertBefore(C,k.firstChild),d.value="",k.children.length>=10&&p()}).catch(f=>alert(f.message))});function p(){const n=e("#submissionReplyEdit"),d=e("#postReplyBtn");n.disabled=!0,d.disabled=!0,i&&(i.style.display="block")}s&&s.addEventListener("click",()=>{if(!Array.isArray(_)||I<=0)return;const n=I-1,d=_[n];d&&N({...d,read_only:S,album_items:_,album_index:n})}),t&&t.addEventListener("click",()=>{if(!Array.isArray(_)||I>=_.length-1)return;const n=I+1,d=_[n];d&&N({...d,read_only:S,album_items:_,album_index:n})})});export{T as a,Te as q,N as s};
