import{l as b,c as x,o as Y,e as ne,f as Q,g as be,a as ge,h as he,b as ye}from"./chunk-BoqWdYVj.js";function A(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,s=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${s}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){b.error("Riding preferences choices missing.");return}const l=document.getElementById("userProfileDetails");if(!l){b.error("Profile details containers not found");return}const a=t.current_user_id===t.user.id;l.innerHTML=`
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
                ${a?`
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
                          ${t.riding_preferences_choices.map((d,f)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${f}" name="riding_preferences"
                                      value="${d[0]}"
                                      ${t.user.riding_preferences.includes(d[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${f}">${d[1]}</label>
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
                ${a?`
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
                        ${a?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${d.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const r=document.getElementById("userProfileModalLabel");r.textContent=`${t.user.display_name||t.user.username}'s Profile`;const u=document.getElementById("followBtn");u&&(u.style.display="");const h=document.getElementById("followerCount");let p=t.user.follower_count;function w(){h&&(h.textContent=`${p} follower${p===1?"":"s"}`)}if(w(),!a&&u){let f=function(){d?(u.textContent="Following",u.classList.remove("btn-primary"),u.classList.add("btn-outline-primary")):(u.textContent="Follow",u.classList.remove("btn-outline-primary"),u.classList.add("btn-primary"))};u&&(u.style.display="",u.classList.remove("d-none"));let d=t.current_user_following;f(),u.onclick=async()=>{const k=d?"unfollow":"follow",{status:P}=await x(`/profile/${t.user.username}/${k}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(P!==200){b.error("Follow toggle failed");return}d=!d,p+=d?1:-1,f(),w()}}else{const d=document.getElementById("followBtn");d&&(d.style.display="none")}Y("userProfileModal");const B=document.getElementById("editProfileBtn");B&&B.addEventListener("click",ve);const L=document.getElementById("saveProfileBtn");L&&L.addEventListener("click",()=>_e(e));const n=document.getElementById("cancelProfileBtn");n&&n.addEventListener("click",d=>{d.preventDefault(),Ee(e)});const c=document.getElementById("updatePasswordBtn");c&&c.addEventListener("click",()=>{window.location.href="/auth/update_password"});const E=document.getElementById("saveBikeBtn");E&&E.addEventListener("click",()=>ke(e)),document.querySelectorAll("[data-delete-submission]").forEach(d=>{d.addEventListener("click",()=>{const f=d.getAttribute("data-delete-submission");we(f,"profileSubmissions",t.user.id)})});const y=document.getElementById("deleteAccountForm");y&&y.addEventListener("submit",d=>{d.preventDefault(),Ce()});const g=document.getElementById("profileTabSelect");g&&(g.addEventListener("change",d=>{const f=d.target.value,k=document.querySelector(`#profileTabs a[href="#${f}"]`);k&&new bootstrap.Tab(k).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(d=>{d.addEventListener("shown.bs.tab",f=>{g.value=f.target.getAttribute("href").slice(1)})}))}).catch(t=>{b.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function ve(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){b.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function Ee(e){A(e)}function _e(e){const o=document.getElementById("editProfileForm");if(!o){b.error("Edit profile form not found");return}const i=new FormData(o),s=document.getElementById("profilePictureInput");s.files.length>0&&i.append("profile_picture",s.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(l=>{t.push(l.value)}),i.delete("riding_preferences"),t.forEach(l=>{i.append("riding_preferences",l)}),x(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:l})=>{if(l.error){let a=`Error: ${l.error}`;if(l.details){const r=[];Object.values(l.details).forEach(u=>{r.push(u.join(", "))}),r.length&&(a+=` - ${r.join("; ")}`)}alert(a)}else alert("Profile updated successfully."),A(e)}).catch(l=>{b.error("Error updating profile:",l),alert("Failed to update profile. Please try again.")})}function ke(e){const o=document.getElementById("editBikeForm");if(!o){b.error("Edit bike form not found");return}const i=new FormData(o),s=document.getElementById("bikePicture");s.files.length>0&&i.append("bike_picture",s.files[0]),x(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),A(e))}).catch(t=>{b.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function we(e,o,i){x(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:s})=>{if(s.success)alert("Submission deleted successfully."),A(i);else throw new Error(s.message)}).catch(s=>{b.error("Error deleting submission:",s),alert("Error during deletion: "+s.message)})}function Ce(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&x("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{b.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;const i=document.body.dataset.userId;if(!i||i==="none")return;e.preventDefault();const s=o.getAttribute("data-user-profile");s&&A(s)});function Be(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const re=Number(Be("current-user-id")||0),$e=be(),T=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function ae(e){ne(),Q(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:l}=o;if(!le(i,s.completions,t,e,l)){b.error("populateQuestDetails – required element missing");return}de(i,s.completions,l,t),Y("questDetailModal"),K(),me(e)}).catch(o=>{b.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function J(e){Q(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:l}=o;if(!le(i,s.completions,t,e,l)){b.error("populateQuestDetails - required element missing");return}de(i,s.completions,l,t),K(),me(e)}).catch(o=>{b.error("Failed to refresh quest detail modal:",o)})}function K(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,s)=>{i.forEach(t=>{if(t.isIntersecting){const l=t.target;l.src=l.getAttribute("data-src"),l.classList.remove("lazyload"),s.unobserve(l)}})});e.forEach(i=>{o.observe(i)})}function le(e,o,i,s,t){var B,L,n;const l=o>=e.completion_limit?" - complete":"",a={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let c in a)if(!a[c])return b.error(`Error: Missing element ${c}`),!1;const r={badge:(B=a.modalQuestBadgeImage)==null?void 0:B.closest(".quest-detail-item"),badgeAwarded:(L=a.modalQuestBadgeAwarded)==null?void 0:L.closest(".quest-detail-item"),category:(n=a.modalQuestCategory)==null?void 0:n.closest(".quest-detail-item")};for(let c in r)if(!r[c])return b.error(`Error: Missing card element ${c}`),!1;a.modalQuestTitle.innerText=`${e.title}${l}`,a.modalQuestDescription.textContent=e.description,a.modalQuestTips.textContent=e.tips||"No tips available",a.modalQuestPoints.innerText=`${e.points}`,a.modalQuestCategory.innerText=e.category||"No category set";const u=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;a.modalQuestCompletionLimit.innerText=`${u} ${e.frequency}`;const h=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?a.modalQuestBadgeAwarded.innerText=`After ${h}`:a.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":a.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":a.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":a.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":a.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:a.modalQuestVerificationType.innerText="Not specified";break}const p=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:T;a.modalQuestBadgeImage.setAttribute("data-src",p),a.modalQuestBadgeImage.src=T,a.modalQuestBadgeImage.classList.add("lazyload"),a.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(r.badge.classList.add("hidden"),r.badgeAwarded.classList.add("hidden"),r.category.classList.add("hidden")):(r.badge.classList.remove("hidden"),r.badgeAwarded.classList.remove("hidden"),r.category.classList.remove("hidden")),a.modalQuestCompletions.innerText=`Total Completions: ${o}`;const w=t&&new Date(t);return!i&&w&&w>new Date?(a.modalCountdown.innerText=`Next eligible time: ${w.toLocaleString()}`,a.modalCountdown.style.color="red"):(a.modalCountdown.innerText="You are currently eligible to verify!",a.modalCountdown.style.color="green"),Le(s,i,e.verification_type),!0}function de(e,o,i,s){const t=document.querySelector(".user-quest-data");if(!t){b.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(a=>{let r=document.getElementById(a.id);r||(r=document.createElement("p"),r.id=a.id,t.appendChild(r)),r.innerText=a.value}),Ie(document.getElementById("modalCountdown"),i,s)}function Ie(e,o,i){if(!i&&o){const s=new Date(o),t=new Date;if(s>t){const l=s-t;e.innerText=`Next eligible time: ${xe(l)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function xe(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),s=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${s}h ${i}m ${o}s`}function Le(e,o,i){const s=document.querySelector(".user-quest-data");if(!s){b.error("Parent element .user-quest-data not found");return}if(s.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const l=Pe(i.trim().toLowerCase(),e);t.appendChild(l),s.appendChild(t),Se(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",s.appendChild(t)}}function Pe(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const s=document.createElement("input");s.type="hidden",s.name="csrf_token",s.value=$e,i.appendChild(s);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(z("image","Upload a Photo","image/*")),i.appendChild(N());break;case"comment":i.appendChild(j("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(N());break;case"photo_comment":i.appendChild(z("image","Upload a Photo","image/*")),i.appendChild(j("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(N());break;case"video":i.appendChild(z("video","Upload a Video","video/*")),i.appendChild(j("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(N());break;case"qr_code":{const l=document.createElement("p");l.className="epic-message",l.textContent="Find and scan the QR code. No submission required here.",i.appendChild(l);break}case"pause":{const l=document.createElement("p");l.className="epic-message",l.textContent="Quest is currently paused.",i.appendChild(l);break}default:{const l=document.createElement("p");l.className="epic-message",l.textContent="Submission requirements are not set correctly.",i.appendChild(l)}}return i}function z(e,o,i,s){const t=document.createElement("div");t.className="form-group";const l=document.createElement("label");l.htmlFor=e,l.className="epic-label",l.textContent=o,t.appendChild(l);const a=document.createElement("input");return a.type="file",a.id=e,a.name=e,a.className="epic-input",a.accept=i,a.required=!0,t.appendChild(a),t}function j(e,o,i,s){const t=document.createElement("div");t.className="form-group";const l=document.createElement("label");l.htmlFor=e,l.className="epic-label",l.textContent=o,t.appendChild(l);const a=document.createElement("textarea");return a.id=e,a.name=e,a.className="epic-textarea",a.placeholder=i,s&&(a.required=!0),t.appendChild(a),t}function N(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function Se(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){b.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){b.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(s){De(s,e)})}function G(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function Te(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function Ae(e,o,i){const s=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!s)return;const t=s.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function ce(e){G(document.getElementById("twitterLink"),e.twitter_url),G(document.getElementById("facebookLink"),e.fb_url),G(document.getElementById("instagramLink"),e.instagram_url)}let W=!1;async function De(e,o){if(e.preventDefault(),W)return;W=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{ge("Uploading...");const s=e.target.querySelector('input[type="file"]'),t=s?s.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const u=await Re(t);if(isFinite(u)&&u>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const l=new FormData(e.target);l.append("user_id",re);const{status:a,json:r}=await x(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:l});if(a!==200)throw a===403&&r.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(r.message||`Server responded with status ${a}`);if(!r.success)throw new Error(r.message);if(!r.success)throw new Error(r.message);Te(r.total_points),ce(r),Ae(o,r.new_completion_count,r.total_completion_count),J(o),e.target.reset()}catch(s){b.error("Submission error:",s),alert(`Error during submission: ${s.message}`)}finally{W=!1,i&&(i.disabled=!1),he()}}function Re(e){return new Promise((o,i)=>{try{const s=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(s),o(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(s),i(new Error("metadata error"))},t.src=s}catch(s){i(s)}})}async function me(e){const o=encodeURIComponent(e);try{const{json:i}=await Q(`/quests/quest/${o}/submissions`),s=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),l=document.getElementById("instagramLink");if(i&&i.length){const r=i[0],u=document.getElementById("submissionImage"),h=document.getElementById("submissionVideo"),p=document.getElementById("submissionVideoSource"),w=document.getElementById("submissionComment"),B=document.getElementById("submitterProfileLink"),L=document.getElementById("submitterProfileImage"),n=document.getElementById("submitterProfileCaption");r.video_url?(u.hidden=!0,h.hidden=!1,p.src=r.video_url,h.load()):(h.hidden=!0,u.hidden=!1,u.src=r.image_url||T),w.textContent=r.comment||"No comment provided.",B&&B.tagName==="A"&&re?B.href=`/profile/${encodeURIComponent(r.user_id)}`:B&&B.removeAttribute("href"),L.src=r.user_profile_picture||T,n.textContent=r.user_display_name||r.user_username||`User ${r.user_id}`,ce(r)}else[s,t,l].forEach(r=>{r&&(r.style.display="none")});const a=i.slice().reverse().map(r=>({id:r.id,url:r.image_url||(r.video_url?null:T),video_url:r.video_url,alt:"Submission Image",comment:r.comment,user_id:r.user_id,user_display_name:r.user_display_name,user_username:r.user_username,user_profile_picture:r.user_profile_picture,twitter_url:r.twitter_url,fb_url:r.fb_url,instagram_url:r.instagram_url,quest_id:e}));qe(a)}catch(i){b.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function se(e){if(!e)return b.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(s=>o.pathname.toLowerCase().endsWith(s))}catch{return b.error(`Invalid URL detected: ${e}`),!1}return!1}function qe(e){var u;const o=document.getElementById("submissionBoard");if(!o){b.error("submissionBoard element not found");return}o.innerHTML="";const i=((u=document.getElementById("questDetailModal"))==null?void 0:u.getAttribute("data-placeholder-url"))||T,s=se(i)?i:T,t=h=>h.startsWith("/static/"),l=h=>h.replace(/^\/static\//,""),a=window.innerWidth<=480?70:100,r=Math.round(a*(window.devicePixelRatio||2));e.forEach(h=>{let p;if(h.video_url)p=document.createElement("video"),p.src=h.video_url,p.preload="metadata",p.muted=!0,p.playsInline=!0,p.style.objectFit="cover";else{p=document.createElement("img");const w=se(h.url)?h.url:s,B=t(w)?`/resize_image?path=${encodeURIComponent(l(w))}&width=${r}`:w;p.src=T,p.setAttribute("data-src",B),p.classList.add("lazyload"),p.alt=h.alt||"Submission Image"}p.style.width=`${a}px`,p.style.height="auto",p.style.marginRight="10px",h.video_url||(p.onerror=()=>{t(s)?p.src=`/resize_image?path=${encodeURIComponent(l(s))}&width=${r}`:p.src=encodeURI(s)}),p.onclick=()=>U(h),o.appendChild(p)}),K()}function Me(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),ae(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),Me(i))});const Ne=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:ae,refreshQuestDetailModal:J},Symbol.toStringTag,{value:"Module"}));let U,v=[],I=-1,S=!1,H=new Image,R=null,q=null;document.addEventListener("DOMContentLoaded",()=>{const e=n=>document.querySelector(n);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),s=document.getElementById("prevSubmissionBtn"),t=document.getElementById("nextSubmissionBtn"),l=document.querySelector('meta[name="placeholder-image"]').getAttribute("content"),a=()=>{const n=e("#submissionImage"),c=e("#submissionVideo"),E=e("#submissionVideoSource");n&&(n.onload=null,n.onerror=null,n.src=""),c&&E&&(c.onloadeddata=null,c.pause(),E.src="",c.load()),H.src=""},r=n=>{!s||!t||(n?(s.disabled=!0,t.disabled=!0):(s.disabled=I<=0,t.disabled=I>=v.length-1))},u=()=>{if(H.src="",!Array.isArray(v))return;const n=v[I+1];!n||n.video_url||(H.src=n.url)};U=function(n){const c=e("#submissionDetailModal");c.dataset.submissionId=n.id,c.dataset.questId=n.quest_id||"",S=!!!c.dataset.currentUserId||!!(n.read_only||n.readOnly),Array.isArray(n.album_items)&&(v=n.album_items,I=Number.isInteger(n.album_index)?n.album_index:-1),a(),R&&R.abort(),q&&q.abort(),r(!0);const y=Number(c.dataset.currentUserId),g=Number(n.user_id)===y,d=c.dataset.isAdmin==="True"||c.dataset.isAdmin==="true",f=e("#editPhotoBtn"),k=e("#photoEditControls"),P=e("#submissionPhotoInput"),F=e("#savePhotoBtn"),X=e("#cancelPhotoBtn"),Z=e("#deleteSubmissionBtn");f.hidden=!g||S,Z.hidden=!(g||d),k.hidden=!0,f.onclick=()=>{k.hidden=!1,f.hidden=!0,P&&P.click()},X.onclick=()=>{P.value="",k.hidden=!0,f.hidden=!1},Z.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const $=c.dataset.submissionId;x(`/quests/quest/delete_submission/${$}`,{method:"POST"}).then(({json:_})=>{if(!_.success)throw new Error(_.message||"Delete failed");ye("submissionDetailModal"),ne(),c.dataset.questId&&J(c.dataset.questId),alert("Submission deleted successfully.")}).catch(_=>alert("Error deleting submission: "+_.message))},F.onclick=async()=>{const $=c.dataset.submissionId,_=P.files[0];if(!_)return alert("Please select an image first.");if(_.type.startsWith("video/")&&_.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(_.type.startsWith("image/")&&_.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const D=new FormData;if(_.type.startsWith("video/")){try{const C=await ue(_);if(isFinite(C)&&C>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}D.append("video",_)}else D.append("photo",_);x(`/quests/submission/${$}/photo`,{method:"PUT",body:D}).then(({json:C})=>{if(!C.success)throw new Error(C.message||"Upload failed");C.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=C.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=C.image_url),X.click()}).catch(C=>alert(C.message))};function ue($){return new Promise((_,D)=>{try{const C=URL.createObjectURL($),M=document.createElement("video");M.preload="metadata",M.onloadedmetadata=()=>{URL.revokeObjectURL(C),_(M.duration||0)},M.onerror=()=>{URL.revokeObjectURL(C),D(new Error("metadata error"))},M.src=C}catch(C){D(C)}})}const ee=e("#submissionReplyEdit");ee&&(ee.hidden=g);const te=e("#postReplyBtn");te&&(te.hidden=g);const ie=e("#ownerNotice");ie&&(ie.hidden=!g);const O=e("#submissionRepliesContainer");O&&(g?O.hidden=!0:O.hidden=!1);const m={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}},V=e("#submissionLikeBtn"),oe=e("#submissionLikeCount");oe&&(oe.textContent=Number.isInteger(n.like_count)?n.like_count:0),V&&(V.classList.toggle("active",!!n.liked_by_current_user),S&&(V.style.display="none")),m.profileImg.src=n.user_profile_picture||l,m.profileImgOverlay.src=m.profileImg.src,m.profileCap.textContent=n.user_display_name||n.user_username||"—",S?(m.profileLink.onclick=null,m.profileImg.onclick=null,m.profileCap.onclick=null,m.imgOverlay&&m.imgOverlay.parentElement&&(m.imgOverlay.parentElement.onclick=null)):(m.profileLink.onclick=$=>{$.preventDefault(),A(n.user_id)},m.profileImg.onclick=m.profileLink.onclick,m.profileCap.onclick=m.profileLink.onclick,m.imgOverlay.parentElement.onclick=m.profileLink.onclick);const pe=l;if(n.video_url?(m.img.hidden=!0,m.video.hidden=!1,m.videoSource.src=n.video_url,m.video.load(),m.video.onloadeddata=()=>r(!1)):(m.video.hidden=!0,m.img.hidden=!1,m.img.src=n.url||pe,m.img.complete?r(!1):(m.img.onload=()=>r(!1),m.img.onerror=()=>r(!1))),m.commentRead.textContent=n.comment||"No comment provided.",["tw","fb","ig"].forEach($=>{const _=$==="tw"?"twitter_url":$==="fb"?"fb_url":"instagram_url";try{new URL(n[_]),m.social[$].href=n[_],m.social[$].style.display="inline-block"}catch{m.social[$].style.display="none"}}),S){m.editBtn.hidden=!0,m.readBox.hidden=!0,m.commentEdit.hidden=!0,m.editBox.hidden=!0;const $=e("#submissionRepliesContainer");$&&($.style.display="none")}else g?(m.editBtn.hidden=!1,m.readBox.hidden=!1):m.editBtn.hidden=m.readBox.hidden=m.commentEdit.hidden=m.editBox.hidden=!0;const fe=Array.isArray(v)&&v.length>0&&I>=0;s&&t&&(fe?(s.style.display="inline-flex",t.style.display="inline-flex"):(s.style.display="none",t.style.display="none")),p(),u(),Y("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),h(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const n=e("#submissionDetailModal").dataset.submissionId;x(`/quests/submission/${n}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:c})=>{if(!c.success)throw new Error(c.message||"Save failed");e("#submissionComment").textContent=c.comment||"No comment provided.",h(!1)}).catch(c=>alert(`Could not save comment: ${c.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>h(!1));function h(n){e("#submissionComment").hidden=n,e("#commentReadButtons").hidden=n,e("#submissionCommentEdit").hidden=!n,e("#commentEditButtons").hidden=!n}function p(){const n=e("#submissionDetailModal").dataset.submissionId;n&&(R&&R.abort(),R=new AbortController,Q(`/quests/submissions/${n}`,{signal:R.signal}).then(({json:c})=>{const E=e("#submissionLikeCount"),y=e("#submissionLikeBtn");E&&(E.textContent=c.like_count||0),y&&y.classList.toggle("active",c.liked_by_current_user),Array.isArray(v)&&I>=0&&(v[I].like_count=c.like_count,v[I].liked_by_current_user=c.liked_by_current_user)}).catch(c=>{c.name!=="AbortError"&&console.error(c)}),S||(q&&q.abort(),q=new AbortController,Q(`/quests/submission/${n}/replies`,{signal:q.signal}).then(({json:c})=>{const E=e("#submissionRepliesList");if(!E)return;E.innerHTML="",c.replies.forEach(d=>{const f=document.createElement("div");f.className="reply mb-1";const k=document.createElement("a");k.href="#",k.className="reply-user-link",k.dataset.userId=d.user_id;const P=document.createElement("strong");P.textContent=d.user_display,k.appendChild(P),f.appendChild(k),f.appendChild(document.createTextNode(`: ${d.content}`)),k.addEventListener("click",F=>{F.preventDefault(),A(d.user_id)}),E.appendChild(f)});const y=e("#submissionReplyEdit"),g=e("#postReplyBtn");y&&g&&(c.replies.length>=10?(y.disabled=!0,g.disabled=!0,i&&(i.style.display="block")):(y.disabled=!1,g.disabled=!1,i&&(i.style.display="none")))}).catch(c=>{c.name!=="AbortError"&&console.error(c)})))}const w=e("#submissionLikeBtn");w&&w.addEventListener("click",()=>{var E;const n=((E=v[I])==null?void 0:E.id)||e("#submissionDetailModal").dataset.submissionId;if(!n){alert("Like failed");return}const c=w.classList.contains("active");x(`/quests/submission/${n}/like`,{method:c?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:y})=>{if(!y.success)throw new Error(y.message||"Like failed");const g=e("#submissionLikeCount");g&&(g.textContent=y.like_count),w.classList.toggle("active",y.liked),Array.isArray(v)&&I>=0&&(v[I].like_count=y.like_count,v[I].liked_by_current_user=y.liked)}).catch(y=>alert(y.message))});const B=e("#postReplyBtn");B&&B.addEventListener("click",()=>{if(S)return;const n=e("#submissionDetailModal").dataset.submissionId,c=e("#submissionReplyEdit");if(!c)return;const E=c.value.trim();!n||!E||x(`/quests/submission/${n}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:E})}).then(({status:y,json:g})=>{if(!g.success){if(g.message==="Reply limit of 10 reached"){L();return}if(y===409&&g.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(g.message||"Error")}const d=e("#submissionRepliesList"),f=document.createElement("div");f.className="reply mb-1";const k=document.createElement("strong");k.textContent=g.reply.user_display,f.appendChild(k),f.appendChild(document.createTextNode(`: ${g.reply.content}`)),d.insertBefore(f,d.firstChild),c.value="",d.children.length>=10&&L()}).catch(y=>alert(y.message))});function L(){const n=e("#submissionReplyEdit"),c=e("#postReplyBtn");n&&(n.disabled=!0),c&&(c.disabled=!0),i&&(i.style.display="block")}s&&s.addEventListener("click",()=>{if(!Array.isArray(v)||I<=0)return;const n=I-1,c=v[n];c&&U({...c,read_only:S,album_items:v,album_index:n})}),t&&t.addEventListener("click",()=>{if(!Array.isArray(v)||I>=v.length-1)return;const n=I+1,c=v[n];c&&U({...c,read_only:S,album_items:v,album_index:n})})});export{A as a,Ne as q,U as s};
