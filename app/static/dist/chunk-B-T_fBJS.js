import{l as b,c as x,o as G,e as K,f as R,g as le,a as de,h as ce,b as me}from"./chunk-DfIU-FO0.js";function T(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,s=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${s}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){b.error("Riding preferences choices missing.");return}const d=document.getElementById("userProfileDetails");if(!d){b.error("Profile details containers not found");return}const l=t.current_user_id===t.user.id;d.innerHTML=`
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
                ${l?`
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
                          ${t.timezone_choices.map(a=>`
                            <option value="${a}" ${t.user.timezone===a?"selected":""}>${a}</option>
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
                          ${t.riding_preferences_choices.map((a,C)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${C}" name="riding_preferences"
                                      value="${a[0]}"
                                      ${t.user.riding_preferences.includes(a[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${C}">${a[1]}</label>
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
                ${l?`
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
                  ${t.user.badges&&t.user.badges.length?t.user.badges.map(a=>`
                      <div class="badge-card">
                        <img src="/static/images/badge_images/${a.image}" alt="${a.name}" class="badge-icon" style="width:100px;">
                        <div class="badge-caption">
                          <h3>${a.name}</h3>
                          <p>${a.description}</p>
                          <p><strong>Category:</strong> ${a.category}</p>
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
                  ${t.participated_games&&t.participated_games.length?t.participated_games.map(a=>`
                      <div class="game-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        <h3 class="h5">${a.title}</h3>
                        <p class="text-muted">${a.description}</p>
                        <p><strong>Start Date:</strong> ${a.start_date}</p>
                        <p><strong>End Date:</strong> ${a.end_date}</p>
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
                  ${t.quest_submissions&&t.quest_submissions.length?t.quest_submissions.map(a=>`
                      <div class="submission-item col-md-6 p-3 border rounded shadow-sm bg-white">
                        ${a.image_url?`<img src="${a.image_url}" alt="Submission Image" class="img-fluid rounded mb-2" style="max-height:200px; object-fit:cover;">`:""}
                        <p><strong>Quest:</strong> ${a.quest.title}</p>
                        <p class="text-muted">${a.comment}</p>
                        <p><strong>Submitted At:</strong> ${a.timestamp}</p>
                        <div class="d-flex gap-2">
                          ${a.twitter_url?`<a href="${a.twitter_url}"   target="_blank" class="btn btn-sm btn-twitter"><i class="bi bi-twitter"></i></a>`:""}
                          ${a.fb_url?`<a href="${a.fb_url}"        target="_blank" class="btn btn-sm btn-facebook"><i class="bi bi-facebook"></i></a>`:""}
                          ${a.instagram_url?`<a href="${a.instagram_url}" target="_blank" class="btn btn-sm btn-instagram"><i class="bi bi-instagram"></i></a>`:""}
                        </div>
                        ${l?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${a.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const r=document.getElementById("userProfileModalLabel");r.textContent=`${t.user.display_name||t.user.username}'s Profile`;const u=document.getElementById("followBtn");u&&(u.style.display="");const g=document.getElementById("followerCount");let p=t.user.follower_count;function I(){g&&(g.textContent=`${p} follower${p===1?"":"s"}`)}if(I(),!l&&u){let C=function(){a?(u.textContent="Following",u.classList.remove("btn-primary"),u.classList.add("btn-outline-primary")):(u.textContent="Follow",u.classList.remove("btn-outline-primary"),u.classList.add("btn-primary"))};u&&(u.style.display="",u.classList.remove("d-none"));let a=t.current_user_following;C(),u.onclick=async()=>{const L=a?"unfollow":"follow",{status:Q}=await x(`/profile/${t.user.username}/${L}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(Q!==200){b.error("Follow toggle failed");return}a=!a,p+=a?1:-1,C(),I()}}else{const a=document.getElementById("followBtn");a&&(a.style.display="none")}G("userProfileModal");const n=document.getElementById("editProfileBtn");n&&n.addEventListener("click",ue);const c=document.getElementById("saveProfileBtn");c&&c.addEventListener("click",()=>fe(e));const y=document.getElementById("cancelProfileBtn");y&&y.addEventListener("click",a=>{a.preventDefault(),pe(e)});const f=document.getElementById("updatePasswordBtn");f&&f.addEventListener("click",()=>{window.location.href="/auth/update_password"});const h=document.getElementById("saveBikeBtn");h&&h.addEventListener("click",()=>be(e)),document.querySelectorAll("[data-delete-submission]").forEach(a=>{a.addEventListener("click",()=>{const C=a.getAttribute("data-delete-submission");ge(C,"profileSubmissions",t.user.id)})});const k=document.getElementById("deleteAccountForm");k&&k.addEventListener("submit",a=>{a.preventDefault(),he()});const E=document.getElementById("profileTabSelect");E&&(E.addEventListener("change",a=>{const C=a.target.value,L=document.querySelector(`#profileTabs a[href="#${C}"]`);L&&new bootstrap.Tab(L).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(a=>{a.addEventListener("shown.bs.tab",C=>{E.value=C.target.getAttribute("href").slice(1)})}))}).catch(t=>{b.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function ue(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){b.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function pe(e){T(e)}function fe(e){const o=document.getElementById("editProfileForm");if(!o){b.error("Edit profile form not found");return}const i=new FormData(o),s=document.getElementById("profilePictureInput");s.files.length>0&&i.append("profile_picture",s.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(d=>{t.push(d.value)}),i.delete("riding_preferences"),t.forEach(d=>{i.append("riding_preferences",d)}),x(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:d})=>{if(d.error){let l=`Error: ${d.error}`;if(d.details){const r=[];Object.values(d.details).forEach(u=>{r.push(u.join(", "))}),r.length&&(l+=` - ${r.join("; ")}`)}alert(l)}else alert("Profile updated successfully."),T(e)}).catch(d=>{b.error("Error updating profile:",d),alert("Failed to update profile. Please try again.")})}function be(e){const o=document.getElementById("editBikeForm");if(!o){b.error("Edit bike form not found");return}const i=new FormData(o),s=document.getElementById("bikePicture");s.files.length>0&&i.append("bike_picture",s.files[0]),x(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),T(e))}).catch(t=>{b.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function ge(e,o,i){x(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:s})=>{if(s.success)alert("Submission deleted successfully."),T(i);else throw new Error(s.message)}).catch(s=>{b.error("Error deleting submission:",s),alert("Error during deletion: "+s.message)})}function he(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&x("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{b.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;e.preventDefault();const i=o.getAttribute("data-user-profile");i&&T(i)});function ye(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const ve=Number(ye("current-user-id")||0),_e=le(),P=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function X(e){K(),R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:d}=o;if(!Z(i,s.completions,t,e,d)){b.error("populateQuestDetails – required element missing");return}ee(i,s.completions,d,t),G("questDetailModal"),H(),ie(e)}).catch(o=>{b.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function W(e){R(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:d}=o;if(!Z(i,s.completions,t,e,d)){b.error("populateQuestDetails - required element missing");return}ee(i,s.completions,d,t),H(),ie(e)}).catch(o=>{b.error("Failed to refresh quest detail modal:",o)})}function H(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,s)=>{i.forEach(t=>{if(t.isIntersecting){const d=t.target;d.src=d.getAttribute("data-src"),d.classList.remove("lazyload"),s.unobserve(d)}})});e.forEach(i=>{o.observe(i)})}function Z(e,o,i,s,t){var n,c,y;const d=o>=e.completion_limit?" - complete":"",l={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let f in l)if(!l[f])return b.error(`Error: Missing element ${f}`),!1;const r={badge:(n=l.modalQuestBadgeImage)==null?void 0:n.closest(".quest-detail-item"),badgeAwarded:(c=l.modalQuestBadgeAwarded)==null?void 0:c.closest(".quest-detail-item"),category:(y=l.modalQuestCategory)==null?void 0:y.closest(".quest-detail-item")};for(let f in r)if(!r[f])return b.error(`Error: Missing card element ${f}`),!1;l.modalQuestTitle.innerText=`${e.title}${d}`,l.modalQuestDescription.textContent=e.description,l.modalQuestTips.textContent=e.tips||"No tips available",l.modalQuestPoints.innerText=`${e.points}`,l.modalQuestCategory.innerText=e.category||"No category set";const u=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;l.modalQuestCompletionLimit.innerText=`${u} ${e.frequency}`;const g=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?l.modalQuestBadgeAwarded.innerText=`After ${g}`:l.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":l.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":l.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":l.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":l.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:l.modalQuestVerificationType.innerText="Not specified";break}const p=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:P;l.modalQuestBadgeImage.setAttribute("data-src",p),l.modalQuestBadgeImage.src=P,l.modalQuestBadgeImage.classList.add("lazyload"),l.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(r.badge.classList.add("hidden"),r.badgeAwarded.classList.add("hidden"),r.category.classList.add("hidden")):(r.badge.classList.remove("hidden"),r.badgeAwarded.classList.remove("hidden"),r.category.classList.remove("hidden")),l.modalQuestCompletions.innerText=`Total Completions: ${o}`;const I=t&&new Date(t);return!i&&I&&I>new Date?(l.modalCountdown.innerText=`Next eligible time: ${I.toLocaleString()}`,l.modalCountdown.style.color="red"):(l.modalCountdown.innerText="You are currently eligible to verify!",l.modalCountdown.style.color="green"),ke(s,i,e.verification_type),!0}function ee(e,o,i,s){const t=document.querySelector(".user-quest-data");if(!t){b.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(l=>{let r=document.getElementById(l.id);r||(r=document.createElement("p"),r.id=l.id,t.appendChild(r)),r.innerText=l.value}),Ee(document.getElementById("modalCountdown"),i,s)}function Ee(e,o,i){if(!i&&o){const s=new Date(o),t=new Date;if(s>t){const d=s-t;e.innerText=`Next eligible time: ${we(d)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function we(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),s=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${s}h ${i}m ${o}s`}function ke(e,o,i){const s=document.querySelector(".user-quest-data");if(!s){b.error("Parent element .user-quest-data not found");return}if(s.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const d=Ce(i.trim().toLowerCase(),e);t.appendChild(d),s.appendChild(t),Be(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",s.appendChild(t)}}function Ce(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const s=document.createElement("input");s.type="hidden",s.name="csrf_token",s.value=_e,i.appendChild(s);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(N());break;case"comment":i.appendChild(O("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(N());break;case"photo_comment":i.appendChild(F("image","Upload a Photo","image/*")),i.appendChild(O("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(N());break;case"video":i.appendChild(F("video","Upload a Video","video/*")),i.appendChild(O("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(N());break;case"qr_code":{const d=document.createElement("p");d.className="epic-message",d.textContent="Find and scan the QR code. No submission required here.",i.appendChild(d);break}case"pause":{const d=document.createElement("p");d.className="epic-message",d.textContent="Quest is currently paused.",i.appendChild(d);break}default:{const d=document.createElement("p");d.className="epic-message",d.textContent="Submission requirements are not set correctly.",i.appendChild(d)}}return i}function F(e,o,i,s){const t=document.createElement("div");t.className="form-group";const d=document.createElement("label");d.htmlFor=e,d.className="epic-label",d.textContent=o,t.appendChild(d);const l=document.createElement("input");return l.type="file",l.id=e,l.name=e,l.className="epic-input",l.accept=i,l.required=!0,t.appendChild(l),t}function O(e,o,i,s){const t=document.createElement("div");t.className="form-group";const d=document.createElement("label");d.htmlFor=e,d.className="epic-label",d.textContent=o,t.appendChild(d);const l=document.createElement("textarea");return l.id=e,l.name=e,l.className="epic-textarea",l.placeholder=i,s&&(l.required=!0),t.appendChild(l),t}function N(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function Be(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){b.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){b.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(s){xe(s,e)})}function V(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function $e(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function Ie(e,o,i){const s=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!s)return;const t=s.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function te(e){V(document.getElementById("twitterLink"),e.twitter_url),V(document.getElementById("facebookLink"),e.fb_url),V(document.getElementById("instagramLink"),e.instagram_url)}let z=!1;async function xe(e,o){if(e.preventDefault(),z)return;z=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{de("Uploading...");const s=e.target.querySelector('input[type="file"]'),t=s?s.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const u=await Le(t);if(isFinite(u)&&u>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const d=new FormData(e.target);d.append("user_id",ve);const{status:l,json:r}=await x(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:d});if(l!==200)throw l===403&&r.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(r.message||`Server responded with status ${l}`);if(!r.success)throw new Error(r.message);if(!r.success)throw new Error(r.message);$e(r.total_points),te(r),Ie(o,r.new_completion_count,r.total_completion_count),W(o),e.target.reset()}catch(s){b.error("Submission error:",s),alert(`Error during submission: ${s.message}`)}finally{z=!1,i&&(i.disabled=!1),ce()}}function Le(e){return new Promise((o,i)=>{try{const s=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(s),o(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(s),i(new Error("metadata error"))},t.src=s}catch(s){i(s)}})}async function ie(e){const o=encodeURIComponent(e);try{const{json:i}=await R(`/quests/quest/${o}/submissions`),s=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),d=document.getElementById("instagramLink");if(i&&i.length){const r=i[0],u=document.getElementById("submissionImage"),g=document.getElementById("submissionVideo"),p=document.getElementById("submissionVideoSource"),I=document.getElementById("submissionComment"),n=document.getElementById("submitterProfileLink"),c=document.getElementById("submitterProfileImage"),y=document.getElementById("submitterProfileCaption");r.video_url?(u.hidden=!0,g.hidden=!1,p.src=r.video_url,g.load()):(g.hidden=!0,u.hidden=!1,u.src=r.image_url||P),I.textContent=r.comment||"No comment provided.",n.href=`/profile/${encodeURIComponent(r.user_id)}`,c.src=r.user_profile_picture||P,y.textContent=r.user_display_name||r.user_username||`User ${r.user_id}`,te(r)}else[s,t,d].forEach(r=>{r&&(r.style.display="none")});const l=i.slice().reverse().map(r=>({id:r.id,url:r.image_url||(r.video_url?null:P),video_url:r.video_url,alt:"Submission Image",comment:r.comment,user_id:r.user_id,user_display_name:r.user_display_name,user_username:r.user_username,user_profile_picture:r.user_profile_picture,twitter_url:r.twitter_url,fb_url:r.fb_url,instagram_url:r.instagram_url,quest_id:e}));Pe(l)}catch(i){b.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function J(e){if(!e)return b.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(s=>o.pathname.toLowerCase().endsWith(s))}catch{return b.error(`Invalid URL detected: ${e}`),!1}return!1}function Pe(e){var u;const o=document.getElementById("submissionBoard");if(!o){b.error("submissionBoard element not found");return}o.innerHTML="";const i=((u=document.getElementById("questDetailModal"))==null?void 0:u.getAttribute("data-placeholder-url"))||P,s=J(i)?i:P,t=g=>g.startsWith("/static/"),d=g=>g.replace(/^\/static\//,""),l=window.innerWidth<=480?70:100,r=Math.round(l*(window.devicePixelRatio||2));e.forEach(g=>{let p;if(g.video_url)p=document.createElement("video"),p.src=g.video_url,p.preload="metadata",p.muted=!0,p.playsInline=!0,p.style.objectFit="cover";else{p=document.createElement("img");const I=J(g.url)?g.url:s,n=t(I)?`/resize_image?path=${encodeURIComponent(d(I))}&width=${r}`:I;p.src=P,p.setAttribute("data-src",n),p.classList.add("lazyload"),p.alt=g.alt||"Submission Image"}p.style.width=`${l}px`,p.style.height="auto",p.style.marginRight="10px",g.video_url||(p.onerror=()=>{t(s)?p.src=`/resize_image?path=${encodeURIComponent(d(s))}&width=${r}`:p.src=encodeURI(s)}),p.onclick=()=>U(g),o.appendChild(p)}),H()}function Se(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),X(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),Se(i))});const Ae=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:X,refreshQuestDetailModal:W},Symbol.toStringTag,{value:"Module"}));let U,v=[],$=-1,S=!1,j=new Image,D=null,q=null;document.addEventListener("DOMContentLoaded",()=>{const e=n=>document.querySelector(n);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),s=document.getElementById("prevSubmissionBtn"),t=document.getElementById("nextSubmissionBtn"),d=document.querySelector('meta[name="placeholder-image"]').getAttribute("content"),l=()=>{const n=e("#submissionImage"),c=e("#submissionVideo"),y=e("#submissionVideoSource");n&&(n.onload=null,n.onerror=null,n.src=""),c&&y&&(c.onloadeddata=null,c.pause(),y.src="",c.load()),j.src=""},r=n=>{!s||!t||(n?(s.disabled=!0,t.disabled=!0):(s.disabled=$<=0,t.disabled=$>=v.length-1))},u=()=>{if(j.src="",!Array.isArray(v))return;const n=v[$+1];!n||n.video_url||(j.src=n.url)};U=function(n){const c=e("#submissionDetailModal");c.dataset.submissionId=n.id,c.dataset.questId=n.quest_id||"",S=!!(n.read_only||n.readOnly),Array.isArray(n.album_items)&&(v=n.album_items,$=Number.isInteger(n.album_index)?n.album_index:-1),l(),D&&D.abort(),q&&q.abort(),r(!0);const y=Number(c.dataset.currentUserId),f=Number(n.user_id)===y,h=c.dataset.isAdmin==="True"||c.dataset.isAdmin==="true",k=e("#editPhotoBtn"),E=e("#photoEditControls"),a=e("#submissionPhotoInput"),C=e("#savePhotoBtn"),L=e("#cancelPhotoBtn"),Q=e("#deleteSubmissionBtn");k.hidden=!f||S,Q.hidden=!(f||h),E.hidden=!0,k.onclick=()=>{E.hidden=!1,k.hidden=!0,a&&a.click()},L.onclick=()=>{a.value="",E.hidden=!0,k.hidden=!1},Q.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const B=c.dataset.submissionId;x(`/quests/quest/delete_submission/${B}`,{method:"POST"}).then(({json:_})=>{if(!_.success)throw new Error(_.message||"Delete failed");me("submissionDetailModal"),K(),c.dataset.questId&&W(c.dataset.questId),alert("Submission deleted successfully.")}).catch(_=>alert("Error deleting submission: "+_.message))},C.onclick=async()=>{const B=c.dataset.submissionId,_=a.files[0];if(!_)return alert("Please select an image first.");if(_.type.startsWith("video/")&&_.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(_.type.startsWith("image/")&&_.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const A=new FormData;if(_.type.startsWith("video/")){try{const w=await oe(_);if(isFinite(w)&&w>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}A.append("video",_)}else A.append("photo",_);x(`/quests/submission/${B}/photo`,{method:"PUT",body:A}).then(({json:w})=>{if(!w.success)throw new Error(w.message||"Upload failed");w.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=w.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=w.image_url),L.click()}).catch(w=>alert(w.message))};function oe(B){return new Promise((_,A)=>{try{const w=URL.createObjectURL(B),M=document.createElement("video");M.preload="metadata",M.onloadedmetadata=()=>{URL.revokeObjectURL(w),_(M.duration||0)},M.onerror=()=>{URL.revokeObjectURL(w),A(new Error("metadata error"))},M.src=w}catch(w){A(w)}})}e("#submissionReplyEdit").hidden=f,e("#postReplyBtn").hidden=f,e("#ownerNotice").hidden=!f;const Y=e("#submissionRepliesContainer");f?Y.hidden=!0:Y.hidden=!1;const m={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}},se=e("#submissionLikeBtn"),ne=e("#submissionLikeCount");ne.textContent=Number.isInteger(n.like_count)?n.like_count:0,se.classList.toggle("active",!!n.liked_by_current_user),m.profileImg.src=n.user_profile_picture||d,m.profileImgOverlay.src=m.profileImg.src,m.profileCap.textContent=n.user_display_name||n.user_username||"—",m.profileLink.onclick=B=>{B.preventDefault(),T(n.user_id)},m.profileImg.onclick=m.profileLink.onclick,m.profileCap.onclick=m.profileLink.onclick,m.imgOverlay.parentElement.onclick=m.profileLink.onclick;const re=d;if(n.video_url?(m.img.hidden=!0,m.video.hidden=!1,m.videoSource.src=n.video_url,m.video.load(),m.video.onloadeddata=()=>r(!1)):(m.video.hidden=!0,m.img.hidden=!1,m.img.src=n.url||re,m.img.complete?r(!1):(m.img.onload=()=>r(!1),m.img.onerror=()=>r(!1))),m.commentRead.textContent=n.comment||"No comment provided.",["tw","fb","ig"].forEach(B=>{const _=B==="tw"?"twitter_url":B==="fb"?"fb_url":"instagram_url";try{new URL(n[_]),m.social[B].href=n[_],m.social[B].style.display="inline-block"}catch{m.social[B].style.display="none"}}),S){m.editBtn.hidden=!0,m.readBox.hidden=!0,m.commentEdit.hidden=!0,m.editBox.hidden=!0;const B=e("#submissionRepliesContainer");B&&(B.style.display="none")}else f?(m.editBtn.hidden=!1,m.readBox.hidden=!1):m.editBtn.hidden=m.readBox.hidden=m.commentEdit.hidden=m.editBox.hidden=!0;const ae=Array.isArray(v)&&v.length>0&&$>=0;s&&t&&(ae?(s.style.display="inline-flex",t.style.display="inline-flex"):(s.style.display="none",t.style.display="none")),p(),u(),G("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),g(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const n=e("#submissionDetailModal").dataset.submissionId;x(`/quests/submission/${n}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:c})=>{if(!c.success)throw new Error(c.message||"Save failed");e("#submissionComment").textContent=c.comment||"No comment provided.",g(!1)}).catch(c=>alert(`Could not save comment: ${c.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>g(!1));function g(n){e("#submissionComment").hidden=n,e("#commentReadButtons").hidden=n,e("#submissionCommentEdit").hidden=!n,e("#commentEditButtons").hidden=!n}function p(){const n=e("#submissionDetailModal").dataset.submissionId;n&&(D&&D.abort(),D=new AbortController,R(`/quests/submissions/${n}`,{signal:D.signal}).then(({json:c})=>{e("#submissionLikeCount").textContent=c.like_count||0,e("#submissionLikeBtn").classList.toggle("active",c.liked_by_current_user),Array.isArray(v)&&$>=0&&(v[$].like_count=c.like_count,v[$].liked_by_current_user=c.liked_by_current_user)}).catch(c=>{c.name!=="AbortError"&&console.error(c)}),S||(q&&q.abort(),q=new AbortController,R(`/quests/submission/${n}/replies`,{signal:q.signal}).then(({json:c})=>{const y=e("#submissionRepliesList");if(!y)return;y.innerHTML="",c.replies.forEach(k=>{const E=document.createElement("div");E.className="reply mb-1";const a=document.createElement("a");a.href="#",a.className="reply-user-link",a.dataset.userId=k.user_id;const C=document.createElement("strong");C.textContent=k.user_display,a.appendChild(C),E.appendChild(a),E.appendChild(document.createTextNode(`: ${k.content}`)),a.addEventListener("click",L=>{L.preventDefault(),T(k.user_id)}),y.appendChild(E)});const f=e("#submissionReplyEdit"),h=e("#postReplyBtn");c.replies.length>=10?(f.disabled=!0,h.disabled=!0,i&&(i.style.display="block")):(f.disabled=!1,h.disabled=!1,i&&(i.style.display="none"))}).catch(c=>{c.name!=="AbortError"&&console.error(c)})))}e("#submissionLikeBtn").addEventListener("click",()=>{var f;const n=e("#submissionLikeBtn"),c=((f=v[$])==null?void 0:f.id)||e("#submissionDetailModal").dataset.submissionId;if(!c){alert("Like failed");return}const y=n.classList.contains("active");x(`/quests/submission/${c}/like`,{method:y?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:h})=>{if(!h.success)throw new Error(h.message||"Like failed");e("#submissionLikeCount").textContent=h.like_count,n.classList.toggle("active",h.liked),Array.isArray(v)&&$>=0&&(v[$].like_count=h.like_count,v[$].liked_by_current_user=h.liked)}).catch(h=>alert(h.message))}),e("#postReplyBtn").addEventListener("click",()=>{if(S)return;const n=e("#submissionDetailModal").dataset.submissionId,c=e("#submissionReplyEdit"),y=c.value.trim();!n||!y||x(`/quests/submission/${n}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:y})}).then(({status:f,json:h})=>{if(!h.success){if(h.message==="Reply limit of 10 reached"){I();return}if(f===409&&h.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(h.message||"Error")}const k=e("#submissionRepliesList"),E=document.createElement("div");E.className="reply mb-1";const a=document.createElement("strong");a.textContent=h.reply.user_display,E.appendChild(a),E.appendChild(document.createTextNode(`: ${h.reply.content}`)),k.insertBefore(E,k.firstChild),c.value="",k.children.length>=10&&I()}).catch(f=>alert(f.message))});function I(){const n=e("#submissionReplyEdit"),c=e("#postReplyBtn");n.disabled=!0,c.disabled=!0,i&&(i.style.display="block")}s&&s.addEventListener("click",()=>{if(!Array.isArray(v)||$<=0)return;const n=$-1,c=v[n];c&&U({...c,read_only:S,album_items:v,album_index:n})}),t&&t.addEventListener("click",()=>{if(!Array.isArray(v)||$>=v.length-1)return;const n=$+1,c=v[n];c&&U({...c,read_only:S,album_items:v,album_index:n})})});export{T as a,Ae as q,U as s};
