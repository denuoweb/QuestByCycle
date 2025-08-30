import{l as u,c as _,o as A,e as N,f as P,g as G,a as W,h as H,b as Y}from"./chunk-CpEJDg8O.js";function B(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,a=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${a}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){u.error("Riding preferences choices missing.");return}const l=document.getElementById("userProfileDetails");if(!l){u.error("Profile details containers not found");return}const r=t.current_user_id===t.user.id;l.innerHTML=`
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
                          ${t.timezone_choices.map(n=>`
                            <option value="${n}" ${t.user.timezone===n?"selected":""}>${n}</option>
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
                          ${t.riding_preferences_choices.map((n,E)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${E}" name="riding_preferences"
                                      value="${n[0]}"
                                      ${t.user.riding_preferences.includes(n[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${E}">${n[1]}</label>
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
                  ${t.user.badges&&t.user.badges.length?t.user.badges.map(n=>`
                      <div class="badge-card">
                        <img src="/static/images/badge_images/${n.image}" alt="${n.name}" class="badge-icon" style="width:100px;">
                        <div class="badge-caption">
                          <h3>${n.name}</h3>
                          <p>${n.description}</p>
                          <p><strong>Category:</strong> ${n.category}</p>
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
                  ${t.participated_games&&t.participated_games.length?t.participated_games.map(n=>`
                      <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        <h3 class="h5">${n.title}</h3>
                        <p class="text-muted">${n.description}</p>
                        <p><strong>Start Date:</strong> ${n.start_date}</p>
                        <p><strong>End Date:</strong> ${n.end_date}</p>
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
                  ${t.quest_submissions&&t.quest_submissions.length?t.quest_submissions.map(n=>`
                      <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        ${n.image_url?`<img src="${n.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height:200px; object-fit:cover;">`:""}
                        <p><strong>Quest:</strong> ${n.quest.title}</p>
                        <p class="text-muted">${n.comment}</p>
                        <p><strong>Submitted At:</strong> ${n.timestamp}</p>
                        <div class="d-flex gap-2">
                          ${n.twitter_url?`<a href="${n.twitter_url}"   target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>`:""}
                          ${n.fb_url?`<a href="${n.fb_url}"        target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>`:""}
                          ${n.instagram_url?`<a href="${n.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>`:""}
                        </div>
                        ${r?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${n.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const s=document.getElementById("userProfileModalLabel");s.textContent=`${t.user.display_name||t.user.username}'s Profile`;const d=document.getElementById("followBtn");d&&(d.style.display="");const m=document.getElementById("followerCount");let c=t.user.follower_count;function p(){m&&(m.textContent=`${c} follower${c===1?"":"s"}`)}if(p(),!r&&d){let E=function(){n?(d.textContent="Following",d.classList.remove("btn-primary"),d.classList.add("btn-outline-primary")):(d.textContent="Follow",d.classList.remove("btn-outline-primary"),d.classList.add("btn-primary"))};d&&(d.style.display="",d.classList.remove("d-none"));let n=t.current_user_following;E(),d.onclick=async()=>{const y=n?"unfollow":"follow",{status:h}=await _(`/profile/${t.user.username}/${y}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(h!==200){u.error("Follow toggle failed");return}n=!n,c+=n?1:-1,E(),p()}}else{const n=document.getElementById("followBtn");n&&(n.style.display="none")}A("userProfileModal");const f=document.getElementById("editProfileBtn");f&&f.addEventListener("click",J);const b=document.getElementById("saveProfileBtn");b&&b.addEventListener("click",()=>X(e));const g=document.getElementById("cancelProfileBtn");g&&g.addEventListener("click",n=>{n.preventDefault(),K(e)});const v=document.getElementById("updatePasswordBtn");v&&v.addEventListener("click",()=>{window.location.href="/auth/update_password"});const C=document.getElementById("saveBikeBtn");C&&C.addEventListener("click",()=>Z(e)),document.querySelectorAll("[data-delete-submission]").forEach(n=>{n.addEventListener("click",()=>{const E=n.getAttribute("data-delete-submission");ee(E,"profileSubmissions",t.user.id)})});const I=document.getElementById("deleteAccountForm");I&&I.addEventListener("submit",n=>{n.preventDefault(),te()});const $=document.getElementById("profileTabSelect");$&&($.addEventListener("change",n=>{const E=n.target.value,y=document.querySelector(`#profileTabs a[href="#${E}"]`);y&&new bootstrap.Tab(y).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(n=>{n.addEventListener("shown.bs.tab",E=>{$.value=E.target.getAttribute("href").slice(1)})}))}).catch(t=>{u.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function J(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){u.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function K(e){B(e)}function X(e){const o=document.getElementById("editProfileForm");if(!o){u.error("Edit profile form not found");return}const i=new FormData(o),a=document.getElementById("profilePictureInput");a.files.length>0&&i.append("profile_picture",a.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(l=>{t.push(l.value)}),i.delete("riding_preferences"),t.forEach(l=>{i.append("riding_preferences",l)}),_(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:l})=>{if(l.error){let r=`Error: ${l.error}`;if(l.details){const s=[];Object.values(l.details).forEach(d=>{s.push(d.join(", "))}),s.length&&(r+=` - ${s.join("; ")}`)}alert(r)}else alert("Profile updated successfully."),B(e)}).catch(l=>{u.error("Error updating profile:",l),alert("Failed to update profile. Please try again.")})}function Z(e){const o=document.getElementById("editBikeForm");if(!o){u.error("Edit bike form not found");return}const i=new FormData(o),a=document.getElementById("bikePicture");a.files.length>0&&i.append("bike_picture",a.files[0]),_(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),B(e))}).catch(t=>{u.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function ee(e,o,i){_(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:a})=>{if(a.success)alert("Submission deleted successfully."),B(i);else throw new Error(a.message)}).catch(a=>{u.error("Error deleting submission:",a),alert("Error during deletion: "+a.message)})}function te(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&_("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{u.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;e.preventDefault();const i=o.getAttribute("data-user-profile");i&&B(i)});function ie(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const se=Number(ie("current-user-id")||0),oe=G(),w=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function F(e){N(),P(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:a,canVerify:t,nextEligibleTime:l}=o;if(!U(i,a.completions,t,e,l)){u.error("populateQuestDetails – required element missing");return}O(i,a.completions,l,t),A("questDetailModal"),M(),z(e)}).catch(o=>{u.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function Q(e){P(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:a,canVerify:t,nextEligibleTime:l}=o;if(!U(i,a.completions,t,e,l)){u.error("populateQuestDetails - required element missing");return}O(i,a.completions,l,t),M(),z(e)}).catch(o=>{u.error("Failed to refresh quest detail modal:",o)})}function M(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,a)=>{i.forEach(t=>{if(t.isIntersecting){const l=t.target;l.src=l.getAttribute("data-src"),l.classList.remove("lazyload"),a.unobserve(l)}})});e.forEach(i=>{o.observe(i)})}function U(e,o,i,a,t){var f,b,g;const l=o>=e.completion_limit?" - complete":"",r={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let v in r)if(!r[v])return u.error(`Error: Missing element ${v}`),!1;const s={badge:(f=r.modalQuestBadgeImage)==null?void 0:f.closest(".quest-detail-item"),badgeAwarded:(b=r.modalQuestBadgeAwarded)==null?void 0:b.closest(".quest-detail-item"),category:(g=r.modalQuestCategory)==null?void 0:g.closest(".quest-detail-item")};for(let v in s)if(!s[v])return u.error(`Error: Missing card element ${v}`),!1;r.modalQuestTitle.innerText=`${e.title}${l}`,r.modalQuestDescription.textContent=e.description,r.modalQuestTips.textContent=e.tips||"No tips available",r.modalQuestPoints.innerText=`${e.points}`,r.modalQuestCategory.innerText=e.category||"No category set";const d=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;r.modalQuestCompletionLimit.innerText=`${d} ${e.frequency}`;const m=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?r.modalQuestBadgeAwarded.innerText=`After ${m}`:r.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":r.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":r.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":r.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":r.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:r.modalQuestVerificationType.innerText="Not specified";break}const c=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:w;r.modalQuestBadgeImage.setAttribute("data-src",c),r.modalQuestBadgeImage.src=w,r.modalQuestBadgeImage.classList.add("lazyload"),r.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(s.badge.classList.add("hidden"),s.badgeAwarded.classList.add("hidden"),s.category.classList.add("hidden")):(s.badge.classList.remove("hidden"),s.badgeAwarded.classList.remove("hidden"),s.category.classList.remove("hidden")),r.modalQuestCompletions.innerText=`Total Completions: ${o}`;const p=t&&new Date(t);return!i&&p&&p>new Date?(r.modalCountdown.innerText=`Next eligible time: ${p.toLocaleString()}`,r.modalCountdown.style.color="red"):(r.modalCountdown.innerText="You are currently eligible to verify!",r.modalCountdown.style.color="green"),re(a,i,e.verification_type),!0}function O(e,o,i,a){const t=document.querySelector(".user-quest-data");if(!t){u.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(r=>{let s=document.getElementById(r.id);s||(s=document.createElement("p"),s.id=r.id,t.appendChild(s)),s.innerText=r.value}),ne(document.getElementById("modalCountdown"),i,a)}function ne(e,o,i){if(!i&&o){const a=new Date(o),t=new Date;if(a>t){const l=a-t;e.innerText=`Next eligible time: ${ae(l)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function ae(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),a=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${a}h ${i}m ${o}s`}function re(e,o,i){const a=document.querySelector(".user-quest-data");if(!a){u.error("Parent element .user-quest-data not found");return}if(a.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const l=le(i.trim().toLowerCase(),e);t.appendChild(l),a.appendChild(t),de(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",a.appendChild(t)}}function le(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const a=document.createElement("input");a.type="hidden",a.name="csrf_token",a.value=oe,i.appendChild(a);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(T("image","Upload a Photo","image/*")),i.appendChild(x());break;case"comment":i.appendChild(S("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(x());break;case"photo_comment":i.appendChild(T("image","Upload a Photo","image/*")),i.appendChild(S("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(x());break;case"video":i.appendChild(T("video","Upload a Video","video/*")),i.appendChild(S("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(x());break;case"qr_code":{const l=document.createElement("p");l.className="epic-message",l.textContent="Find and scan the QR code. No submission required here.",i.appendChild(l);break}case"pause":{const l=document.createElement("p");l.className="epic-message",l.textContent="Quest is currently paused.",i.appendChild(l);break}default:{const l=document.createElement("p");l.className="epic-message",l.textContent="Submission requirements are not set correctly.",i.appendChild(l)}}return i}function T(e,o,i,a){const t=document.createElement("div");t.className="form-group";const l=document.createElement("label");l.htmlFor=e,l.className="epic-label",l.textContent=o,t.appendChild(l);const r=document.createElement("input");return r.type="file",r.id=e,r.name=e,r.className="epic-input",r.accept=i,r.required=!0,t.appendChild(r),t}function S(e,o,i,a){const t=document.createElement("div");t.className="form-group";const l=document.createElement("label");l.htmlFor=e,l.className="epic-label",l.textContent=o,t.appendChild(l);const r=document.createElement("textarea");return r.id=e,r.name=e,r.className="epic-textarea",r.placeholder=i,a&&(r.required=!0),t.appendChild(r),t}function x(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function de(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){u.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){u.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(a){ue(a,e)})}function D(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function ce(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function me(e,o,i){const a=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!a)return;const t=a.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function V(e){D(document.getElementById("twitterLink"),e.twitter_url),D(document.getElementById("facebookLink"),e.fb_url),D(document.getElementById("instagramLink"),e.instagram_url)}let q=!1;async function ue(e,o){if(e.preventDefault(),q)return;q=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{W("Uploading...");const a=e.target.querySelector('input[type="file"]'),t=a?a.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const l=new FormData(e.target);l.append("user_id",se);const{status:r,json:s}=await _(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:l});if(r!==200)throw r===403&&s.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(s.message||`Server responded with status ${r}`);if(!s.success)throw new Error(s.message);if(!s.success)throw new Error(s.message);ce(s.total_points),V(s),me(o,s.new_completion_count,s.total_completion_count),Q(o),e.target.reset()}catch(a){u.error("Submission error:",a),alert(`Error during submission: ${a.message}`)}finally{q=!1,i&&(i.disabled=!1),H()}}async function z(e){const o=encodeURIComponent(e);try{const{json:i}=await P(`/quests/quest/${o}/submissions`),a=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),l=document.getElementById("instagramLink");if(i&&i.length){const s=i[0],d=document.getElementById("submissionImage"),m=document.getElementById("submissionVideo"),c=document.getElementById("submissionVideoSource"),p=document.getElementById("submissionComment"),f=document.getElementById("submitterProfileLink"),b=document.getElementById("submitterProfileImage"),g=document.getElementById("submitterProfileCaption");s.video_url?(d.hidden=!0,m.hidden=!1,c.src=s.video_url,m.load()):(m.hidden=!0,d.hidden=!1,d.src=s.image_url||w),p.textContent=s.comment||"No comment provided.",f.href=`/profile/${encodeURIComponent(s.user_id)}`,b.src=s.user_profile_picture||w,g.textContent=s.user_display_name||s.user_username||`User ${s.user_id}`,V(s)}else[a,t,l].forEach(s=>{s&&(s.style.display="none")});const r=i.slice().reverse().map(s=>({id:s.id,url:s.image_url||(s.video_url?null:w),video_url:s.video_url,alt:"Submission Image",comment:s.comment,user_id:s.user_id,user_display_name:s.user_display_name,user_username:s.user_username,user_profile_picture:s.user_profile_picture,twitter_url:s.twitter_url,fb_url:s.fb_url,instagram_url:s.instagram_url,quest_id:e}));pe(r)}catch(i){u.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function R(e){if(!e)return u.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(a=>o.pathname.toLowerCase().endsWith(a))}catch{return u.error(`Invalid URL detected: ${e}`),!1}return!1}function pe(e){var d;const o=document.getElementById("submissionBoard");if(!o){u.error("submissionBoard element not found");return}o.innerHTML="";const i=((d=document.getElementById("questDetailModal"))==null?void 0:d.getAttribute("data-placeholder-url"))||w,a=R(i)?i:w,t=m=>m.startsWith("/static/"),l=m=>m.replace(/^\/static\//,""),r=window.innerWidth<=480?70:100,s=Math.round(r*(window.devicePixelRatio||2));e.forEach(m=>{let c;if(m.video_url)c=document.createElement("video"),c.src=m.video_url,c.preload="metadata",c.muted=!0,c.playsInline=!0,c.style.objectFit="cover";else{c=document.createElement("img");const p=R(m.url)?m.url:a,f=t(p)?`/resize_image?path=${encodeURIComponent(l(p))}&width=${s}`:p;c.src=w,c.setAttribute("data-src",f),c.classList.add("lazyload"),c.alt=m.alt||"Submission Image"}c.style.width=`${r}px`,c.style.height="auto",c.style.marginRight="10px",m.video_url||(c.onerror=()=>{t(a)?c.src=`/resize_image?path=${encodeURIComponent(l(a))}&width=${s}`:c.src=encodeURI(a)}),c.onclick=()=>j(m),o.appendChild(c)}),M()}function fe(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),F(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),fe(i))});const ge=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:F,refreshQuestDetailModal:Q},Symbol.toStringTag,{value:"Module"}));let j;document.addEventListener("DOMContentLoaded",()=>{const e=s=>document.querySelector(s);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),a=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");j=function(s){const d=e("#submissionDetailModal");d.dataset.submissionId=s.id,d.dataset.questId=s.quest_id||"";const m=Number(d.dataset.currentUserId),c=Number(s.user_id)===m,p=d.dataset.isAdmin==="True"||d.dataset.isAdmin==="true",f=e("#editPhotoBtn"),b=e("#photoEditControls"),g=e("#submissionPhotoInput"),v=e("#savePhotoBtn"),C=e("#cancelPhotoBtn"),I=e("#deleteSubmissionBtn");f.hidden=!c,I.hidden=!(c||p),b.hidden=!0,f.onclick=()=>{b.hidden=!1,f.hidden=!0},C.onclick=()=>{g.value="",b.hidden=!0,f.hidden=!1},I.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const y=d.dataset.submissionId;_(`/quests/quest/delete_submission/${y}`,{method:"POST"}).then(({json:h})=>{if(!h.success)throw new Error(h.message||"Delete failed");Y("submissionDetailModal"),N(),d.dataset.questId&&Q(d.dataset.questId),alert("Submission deleted successfully.")}).catch(h=>alert("Error deleting submission: "+h.message))},v.onclick=()=>{const y=d.dataset.submissionId,h=g.files[0];if(!h)return alert("Please select an image first.");if(h.type.startsWith("video/")&&h.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(h.type.startsWith("image/")&&h.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const L=new FormData;h.type.startsWith("video/")?L.append("video",h):L.append("photo",h),_(`/quests/submission/${y}/photo`,{method:"PUT",body:L}).then(({json:k})=>{if(!k.success)throw new Error(k.message||"Upload failed");k.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=k.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=k.image_url),C.click()}).catch(k=>alert(k.message))},e("#submissionReplyEdit").hidden=c,e("#postReplyBtn").hidden=c,e("#ownerNotice").hidden=!c;const $=e("#submissionRepliesContainer");c?$.hidden=!0:$.hidden=!1;const n={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}};n.profileImg.src=s.user_profile_picture||a,n.profileImgOverlay.src=n.profileImg.src,n.profileCap.textContent=s.user_display_name||s.user_username||"—",n.profileLink.onclick=y=>{y.preventDefault(),B(s.user_id)},n.imgOverlay.parentElement.onclick=n.profileLink.onclick;const E=a;s.video_url?(n.img.hidden=!0,n.video.hidden=!1,n.videoSource.src=s.video_url,n.video.load()):(n.video.hidden=!0,n.img.hidden=!1,n.img.src=s.url||E),n.commentRead.textContent=s.comment||"No comment provided.",["tw","fb","ig"].forEach(y=>{const h=y==="tw"?"twitter_url":y==="fb"?"fb_url":"instagram_url";try{new URL(s[h]),n.social[y].href=s[h],n.social[y].style.display="inline-block"}catch{n.social[y].style.display="none"}}),c?(n.editBtn.hidden=!1,n.readBox.hidden=!1):n.editBtn.hidden=n.readBox.hidden=n.commentEdit.hidden=n.editBox.hidden=!0,l(),A("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),t(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const s=e("#submissionDetailModal").dataset.submissionId;_(`/quests/submission/${s}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:d})=>{if(!d.success)throw new Error(d.message||"Save failed");e("#submissionComment").textContent=d.comment||"No comment provided.",t(!1)}).catch(d=>alert(`Could not save comment: ${d.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>t(!1));function t(s){e("#submissionComment").hidden=s,e("#commentReadButtons").hidden=s,e("#submissionCommentEdit").hidden=!s,e("#commentEditButtons").hidden=!s}function l(){const s=e("#submissionDetailModal").dataset.submissionId;s&&(P(`/quests/submissions/${s}`).then(({json:d})=>{e("#submissionLikeCount").textContent=d.like_count||0,e("#submissionLikeBtn").classList.toggle("active",d.liked_by_current_user)}),P(`/quests/submission/${s}/replies`).then(({json:d})=>{const m=e("#submissionRepliesList");m.innerHTML="",d.replies.forEach(f=>{const b=document.createElement("div");b.className="reply mb-1";const g=document.createElement("a");g.href="#",g.className="reply-user-link",g.dataset.userId=f.user_id;const v=document.createElement("strong");v.textContent=f.user_display,g.appendChild(v),b.appendChild(g),b.appendChild(document.createTextNode(`: ${f.content}`)),g.addEventListener("click",C=>{C.preventDefault(),B(f.user_id)}),m.appendChild(b)});const c=e("#submissionReplyEdit"),p=e("#postReplyBtn");d.replies.length>=10?(c.disabled=!0,p.disabled=!0,i&&(i.style.display="block")):(c.disabled=!1,p.disabled=!1,i&&(i.style.display="none"))}))}e("#submissionLikeBtn").addEventListener("click",()=>{const s=e("#submissionLikeBtn"),d=e("#submissionDetailModal").dataset.submissionId,m=s.classList.contains("active");_(`/quests/submission/${d}/like`,{method:m?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:c})=>{if(!c.success)throw new Error("Like failed");e("#submissionLikeCount").textContent=c.like_count,s.classList.toggle("active",c.liked)}).catch(c=>alert(c.message))}),e("#postReplyBtn").addEventListener("click",()=>{const s=e("#submissionDetailModal").dataset.submissionId,d=e("#submissionReplyEdit"),m=d.value.trim();!s||!m||_(`/quests/submission/${s}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:m})}).then(({status:c,json:p})=>{if(!p.success){if(p.message==="Reply limit of 10 reached"){r();return}if(c===409&&p.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(p.message||"Error")}const f=e("#submissionRepliesList"),b=document.createElement("div");b.className="reply mb-1";const g=document.createElement("strong");g.textContent=p.reply.user_display,b.appendChild(g),b.appendChild(document.createTextNode(`: ${p.reply.content}`)),f.insertBefore(b,f.firstChild),d.value="",f.children.length>=10&&r()}).catch(c=>alert(c.message))});function r(){const s=e("#submissionReplyEdit"),d=e("#postReplyBtn");s.disabled=!0,d.disabled=!0,i&&(i.style.display="block")}});export{B as a,ge as q,j as s};
