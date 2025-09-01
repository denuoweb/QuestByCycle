import{l as f,c as C,o as O,e as G,f as q,g as ee,a as te,h as ie,b as oe}from"./chunk-DAj-wEiZ.js";function T(e){const o=document.getElementById("game_IdHolder"),i=o?o.getAttribute("data-game-id"):null,s=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${s}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){f.error("Riding preferences choices missing.");return}const a=document.getElementById("userProfileDetails");if(!a){f.error("Profile details containers not found");return}const n=t.current_user_id===t.user.id;a.innerHTML=`
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
                ${n?`
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
                ${n?`
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
                        ${n?`<button class="btn btn-danger btn-sm mt-2" data-delete-submission="${c.id}">Delete</button>`:""}
                      </div>
                    `).join(""):'<p class="text-muted">No quest submissions yet.</p>'}
                </div>
              </section>
            </div>

          </div> <!-- /.tab-content -->
        </div> <!-- /.row -->
      `;const l=document.getElementById("userProfileModalLabel");l.textContent=`${t.user.display_name||t.user.username}'s Profile`;const m=document.getElementById("followBtn");m&&(m.style.display="");const r=document.getElementById("followerCount");let d=t.user.follower_count;function b(){r&&(r.textContent=`${d} follower${d===1?"":"s"}`)}if(b(),!n&&m){let B=function(){c?(m.textContent="Following",m.classList.remove("btn-primary"),m.classList.add("btn-outline-primary")):(m.textContent="Follow",m.classList.remove("btn-outline-primary"),m.classList.add("btn-primary"))};m&&(m.style.display="",m.classList.remove("d-none"));let c=t.current_user_following;B(),m.onclick=async()=>{const P=c?"unfollow":"follow",{status:p}=await C(`/profile/${t.user.username}/${P}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(p!==200){f.error("Follow toggle failed");return}c=!c,d+=c?1:-1,B(),b()}}else{const c=document.getElementById("followBtn");c&&(c.style.display="none")}O("userProfileModal");const u=document.getElementById("editProfileBtn");u&&u.addEventListener("click",se);const y=document.getElementById("saveProfileBtn");y&&y.addEventListener("click",()=>re(e));const h=document.getElementById("cancelProfileBtn");h&&h.addEventListener("click",c=>{c.preventDefault(),ne(e)});const g=document.getElementById("updatePasswordBtn");g&&g.addEventListener("click",()=>{window.location.href="/auth/update_password"});const E=document.getElementById("saveBikeBtn");E&&E.addEventListener("click",()=>ae(e)),document.querySelectorAll("[data-delete-submission]").forEach(c=>{c.addEventListener("click",()=>{const B=c.getAttribute("data-delete-submission");le(B,"profileSubmissions",t.user.id)})});const L=document.getElementById("deleteAccountForm");L&&L.addEventListener("submit",c=>{c.preventDefault(),de()});const $=document.getElementById("profileTabSelect");$&&($.addEventListener("change",c=>{const B=c.target.value,P=document.querySelector(`#profileTabs a[href="#${B}"]`);P&&new bootstrap.Tab(P).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(c=>{c.addEventListener("shown.bs.tab",B=>{$.value=B.target.getAttribute("href").slice(1)})}))}).catch(t=>{f.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",o=>{e.checkValidity()||(o.preventDefault(),o.stopPropagation()),e.classList.add("was-validated")},!1)});function se(){const e=document.getElementById("profileViewMode"),o=document.getElementById("profileEditMode");if(!e||!o){f.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),o.classList.toggle("d-none")}function ne(e){T(e)}function re(e){const o=document.getElementById("editProfileForm");if(!o){f.error("Edit profile form not found");return}const i=new FormData(o),s=document.getElementById("profilePictureInput");s.files.length>0&&i.append("profile_picture",s.files[0]);const t=[];o.querySelectorAll('input[name="riding_preferences"]:checked').forEach(a=>{t.push(a.value)}),i.delete("riding_preferences"),t.forEach(a=>{i.append("riding_preferences",a)}),C(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:a})=>{if(a.error){let n=`Error: ${a.error}`;if(a.details){const l=[];Object.values(a.details).forEach(m=>{l.push(m.join(", "))}),l.length&&(n+=` - ${l.join("; ")}`)}alert(n)}else alert("Profile updated successfully."),T(e)}).catch(a=>{f.error("Error updating profile:",a),alert("Failed to update profile. Please try again.")})}function ae(e){const o=document.getElementById("editBikeForm");if(!o){f.error("Edit bike form not found");return}const i=new FormData(o),s=document.getElementById("bikePicture");s.files.length>0&&i.append("bike_picture",s.files[0]),C(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),T(e))}).catch(t=>{f.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function le(e,o,i){C(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:s})=>{if(s.success)alert("Submission deleted successfully."),T(i);else throw new Error(s.message)}).catch(s=>{f.error("Error deleting submission:",s),alert("Error during deletion: "+s.message)})}function de(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&C("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{f.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-user-profile]");if(!o)return;e.preventDefault();const i=o.getAttribute("data-user-profile");i&&T(i)});function ce(e){const o=document.querySelector(`meta[name="${e}"]`);return o?o.content:""}const me=Number(ce("current-user-id")||0),ue=ee(),x=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function W(e){G(),q(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!H(i,s.completions,t,e,a)){f.error("populateQuestDetails – required element missing");return}Y(i,s.completions,a,t),O("questDetailModal"),z(),K(e)}).catch(o=>{f.error("Error opening quest detail modal:",o),alert("Sign in to view quest details.")})}function V(e){q(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:o})=>{const{quest:i,userCompletion:s,canVerify:t,nextEligibleTime:a}=o;if(!H(i,s.completions,t,e,a)){f.error("populateQuestDetails - required element missing");return}Y(i,s.completions,a,t),z(),K(e)}).catch(o=>{f.error("Failed to refresh quest detail modal:",o)})}function z(){const e=document.querySelectorAll("img.lazyload"),o=new IntersectionObserver((i,s)=>{i.forEach(t=>{if(t.isIntersecting){const a=t.target;a.src=a.getAttribute("data-src"),a.classList.remove("lazyload"),s.unobserve(a)}})});e.forEach(i=>{o.observe(i)})}function H(e,o,i,s,t){var u,y,h;const a=o>=e.completion_limit?" - complete":"",n={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let g in n)if(!n[g])return f.error(`Error: Missing element ${g}`),!1;const l={badge:(u=n.modalQuestBadgeImage)==null?void 0:u.closest(".quest-detail-item"),badgeAwarded:(y=n.modalQuestBadgeAwarded)==null?void 0:y.closest(".quest-detail-item"),category:(h=n.modalQuestCategory)==null?void 0:h.closest(".quest-detail-item")};for(let g in l)if(!l[g])return f.error(`Error: Missing card element ${g}`),!1;n.modalQuestTitle.innerText=`${e.title}${a}`,n.modalQuestDescription.textContent=e.description,n.modalQuestTips.textContent=e.tips||"No tips available",n.modalQuestPoints.innerText=`${e.points}`,n.modalQuestCategory.innerText=e.category||"No category set";const m=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;n.modalQuestCompletionLimit.innerText=`${m} ${e.frequency}`;const r=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?n.modalQuestBadgeAwarded.innerText=`After ${r}`:n.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":n.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":n.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":n.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":n.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:n.modalQuestVerificationType.innerText="Not specified";break}const d=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:x;n.modalQuestBadgeImage.setAttribute("data-src",d),n.modalQuestBadgeImage.src=x,n.modalQuestBadgeImage.classList.add("lazyload"),n.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(l.badge.classList.add("hidden"),l.badgeAwarded.classList.add("hidden"),l.category.classList.add("hidden")):(l.badge.classList.remove("hidden"),l.badgeAwarded.classList.remove("hidden"),l.category.classList.remove("hidden")),n.modalQuestCompletions.innerText=`Total Completions: ${o}`;const b=t&&new Date(t);return!i&&b&&b>new Date?(n.modalCountdown.innerText=`Next eligible time: ${b.toLocaleString()}`,n.modalCountdown.style.color="red"):(n.modalCountdown.innerText="You are currently eligible to verify!",n.modalCountdown.style.color="green"),be(s,i,e.verification_type),!0}function Y(e,o,i,s){const t=document.querySelector(".user-quest-data");if(!t){f.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${o||0}`},{id:"modalCountdown",value:""}].forEach(n=>{let l=document.getElementById(n.id);l||(l=document.createElement("p"),l.id=n.id,t.appendChild(l)),l.innerText=n.value}),pe(document.getElementById("modalCountdown"),i,s)}function pe(e,o,i){if(!i&&o){const s=new Date(o),t=new Date;if(s>t){const a=s-t;e.innerText=`Next eligible time: ${fe(a)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function fe(e){const o=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),s=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${s}h ${i}m ${o}s`}function be(e,o,i){const s=document.querySelector(".user-quest-data");if(!s){f.error("Parent element .user-quest-data not found");return}if(s.innerHTML="",o){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const a=ge(i.trim().toLowerCase(),e);t.appendChild(a),s.appendChild(t),he(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",s.appendChild(t)}}function ge(e,o){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(o)}/submit`;const s=document.createElement("input");s.type="hidden",s.name="csrf_token",s.value=ue,i.appendChild(s);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(Q("image","Upload a Photo","image/*")),i.appendChild(R());break;case"comment":i.appendChild(N("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(R());break;case"photo_comment":i.appendChild(Q("image","Upload a Photo","image/*")),i.appendChild(N("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(R());break;case"video":i.appendChild(Q("video","Upload a Video","video/*")),i.appendChild(N("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(R());break;case"qr_code":{const a=document.createElement("p");a.className="epic-message",a.textContent="Find and scan the QR code. No submission required here.",i.appendChild(a);break}case"pause":{const a=document.createElement("p");a.className="epic-message",a.textContent="Quest is currently paused.",i.appendChild(a);break}default:{const a=document.createElement("p");a.className="epic-message",a.textContent="Submission requirements are not set correctly.",i.appendChild(a)}}return i}function Q(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const n=document.createElement("input");return n.type="file",n.id=e,n.name=e,n.className="epic-input",n.accept=i,n.required=!0,t.appendChild(n),t}function N(e,o,i,s){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=o,t.appendChild(a);const n=document.createElement("textarea");return n.id=e,n.name=e,n.className="epic-textarea",n.placeholder=i,s&&(n.required=!0),t.appendChild(n),t}function R(){const e=document.createElement("div");e.className="form-group";const o=document.createElement("button");return o.type="submit",o.textContent="Submit Verification",e.appendChild(o),e}function he(e){const o=document.getElementById(`verifyQuestForm-${e}`);if(!o){f.error("Form container not found for quest ID:",e);return}const i=o.querySelector("form");if(!i){f.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(s){Ee(s,e)})}function U(e,o){e&&(o&&o.trim()?(e.href=o,e.style.display="inline"):e.style.display="none")}function ye(e){if(typeof e!="number")return;const o=document.getElementById("total-points");if(!o)return;const i=o.querySelector(".points-emphasized");i?i.textContent=e:o.textContent=`Your Carbon Reduction Points: ${e}`}function ve(e,o,i){const s=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!s)return;const t=s.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=o,t[1].innerText=i)}function J(e){U(document.getElementById("twitterLink"),e.twitter_url),U(document.getElementById("facebookLink"),e.fb_url),U(document.getElementById("instagramLink"),e.instagram_url)}let F=!1;async function Ee(e,o){if(e.preventDefault(),F)return;F=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{te("Uploading...");const s=e.target.querySelector('input[type="file"]'),t=s?s.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const m=await _e(t);if(isFinite(m)&&m>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const a=new FormData(e.target);a.append("user_id",me);const{status:n,json:l}=await C(`/quests/quest/${encodeURIComponent(o)}/submit`,{method:"POST",body:a});if(n!==200)throw n===403&&l.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(l.message||`Server responded with status ${n}`);if(!l.success)throw new Error(l.message);if(!l.success)throw new Error(l.message);ye(l.total_points),J(l),ve(o,l.new_completion_count,l.total_completion_count),V(o),e.target.reset()}catch(s){f.error("Submission error:",s),alert(`Error during submission: ${s.message}`)}finally{F=!1,i&&(i.disabled=!1),ie()}}function _e(e){return new Promise((o,i)=>{try{const s=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(s),o(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(s),i(new Error("metadata error"))},t.src=s}catch(s){i(s)}})}async function K(e){const o=encodeURIComponent(e);try{const{json:i}=await q(`/quests/quest/${o}/submissions`),s=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),a=document.getElementById("instagramLink");if(i&&i.length){const l=i[0],m=document.getElementById("submissionImage"),r=document.getElementById("submissionVideo"),d=document.getElementById("submissionVideoSource"),b=document.getElementById("submissionComment"),u=document.getElementById("submitterProfileLink"),y=document.getElementById("submitterProfileImage"),h=document.getElementById("submitterProfileCaption");l.video_url?(m.hidden=!0,r.hidden=!1,d.src=l.video_url,r.load()):(r.hidden=!0,m.hidden=!1,m.src=l.image_url||x),b.textContent=l.comment||"No comment provided.",u.href=`/profile/${encodeURIComponent(l.user_id)}`,y.src=l.user_profile_picture||x,h.textContent=l.user_display_name||l.user_username||`User ${l.user_id}`,J(l)}else[s,t,a].forEach(l=>{l&&(l.style.display="none")});const n=i.slice().reverse().map(l=>({id:l.id,url:l.image_url||(l.video_url?null:x),video_url:l.video_url,alt:"Submission Image",comment:l.comment,user_id:l.user_id,user_display_name:l.user_display_name,user_username:l.user_username,user_profile_picture:l.user_profile_picture,twitter_url:l.twitter_url,fb_url:l.fb_url,instagram_url:l.instagram_url,quest_id:e}));we(n)}catch(i){f.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function j(e){if(!e)return f.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const o=new URL(e);if(o.protocol==="http:"||o.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(s=>o.pathname.toLowerCase().endsWith(s))}catch{return f.error(`Invalid URL detected: ${e}`),!1}return!1}function we(e){var m;const o=document.getElementById("submissionBoard");if(!o){f.error("submissionBoard element not found");return}o.innerHTML="";const i=((m=document.getElementById("questDetailModal"))==null?void 0:m.getAttribute("data-placeholder-url"))||x,s=j(i)?i:x,t=r=>r.startsWith("/static/"),a=r=>r.replace(/^\/static\//,""),n=window.innerWidth<=480?70:100,l=Math.round(n*(window.devicePixelRatio||2));e.forEach(r=>{let d;if(r.video_url)d=document.createElement("video"),d.src=r.video_url,d.preload="metadata",d.muted=!0,d.playsInline=!0,d.style.objectFit="cover";else{d=document.createElement("img");const b=j(r.url)?r.url:s,u=t(b)?`/resize_image?path=${encodeURIComponent(a(b))}&width=${l}`:b;d.src=x,d.setAttribute("data-src",u),d.classList.add("lazyload"),d.alt=r.alt||"Submission Image"}d.style.width=`${n}px`,d.style.height="auto",d.style.marginRight="10px",r.video_url||(d.onerror=()=>{t(s)?d.src=`/resize_image?path=${encodeURIComponent(a(s))}&width=${l}`:d.src=encodeURI(s)}),d.onclick=()=>M(r),o.appendChild(d)}),z()}function Be(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const o=e.target.closest("[data-quest-detail]");if(o){e.preventDefault(),W(o.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),Be(i))});const Ce=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:W,refreshQuestDetailModal:V},Symbol.toStringTag,{value:"Module"}));let M,k=[],I=-1,S=!1;document.addEventListener("DOMContentLoaded",()=>{const e=r=>document.querySelector(r);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),s=document.getElementById("prevSubmissionBtn"),t=document.getElementById("nextSubmissionBtn"),a=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");M=function(r){const d=e("#submissionDetailModal");d.dataset.submissionId=r.id,d.dataset.questId=r.quest_id||"",S=!!(r.read_only||r.readOnly),Array.isArray(r.album_items)&&(k=r.album_items,I=Number.isInteger(r.album_index)?r.album_index:-1);const b=Number(d.dataset.currentUserId),u=Number(r.user_id)===b,y=d.dataset.isAdmin==="True"||d.dataset.isAdmin==="true",h=e("#editPhotoBtn"),g=e("#photoEditControls"),E=e("#submissionPhotoInput"),L=e("#savePhotoBtn"),$=e("#cancelPhotoBtn"),c=e("#deleteSubmissionBtn");h.hidden=!u||S,c.hidden=!(u||y),g.hidden=!0,h.onclick=()=>{g.hidden=!1,h.hidden=!0,E&&E.click()},$.onclick=()=>{E.value="",g.hidden=!0,h.hidden=!1},c.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const w=d.dataset.submissionId;C(`/quests/quest/delete_submission/${w}`,{method:"POST"}).then(({json:v})=>{if(!v.success)throw new Error(v.message||"Delete failed");oe("submissionDetailModal"),G(),d.dataset.questId&&V(d.dataset.questId),alert("Submission deleted successfully.")}).catch(v=>alert("Error deleting submission: "+v.message))},L.onclick=async()=>{const w=d.dataset.submissionId,v=E.files[0];if(!v)return alert("Please select an image first.");if(v.type.startsWith("video/")&&v.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(v.type.startsWith("image/")&&v.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const D=new FormData;if(v.type.startsWith("video/")){try{const _=await B(v);if(isFinite(_)&&_>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}D.append("video",v)}else D.append("photo",v);C(`/quests/submission/${w}/photo`,{method:"PUT",body:D}).then(({json:_})=>{if(!_.success)throw new Error(_.message||"Upload failed");_.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=_.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=_.image_url),$.click()}).catch(_=>alert(_.message))};function B(w){return new Promise((v,D)=>{try{const _=URL.createObjectURL(w),A=document.createElement("video");A.preload="metadata",A.onloadedmetadata=()=>{URL.revokeObjectURL(_),v(A.duration||0)},A.onerror=()=>{URL.revokeObjectURL(_),D(new Error("metadata error"))},A.src=_}catch(_){D(_)}})}e("#submissionReplyEdit").hidden=u,e("#postReplyBtn").hidden=u,e("#ownerNotice").hidden=!u;const P=e("#submissionRepliesContainer");u?P.hidden=!0:P.hidden=!1;const p={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}};p.profileImg.src=r.user_profile_picture||a,p.profileImgOverlay.src=p.profileImg.src,p.profileCap.textContent=r.user_display_name||r.user_username||"—",p.profileLink.onclick=w=>{w.preventDefault(),T(r.user_id)},p.imgOverlay.parentElement.onclick=p.profileLink.onclick;const X=a;if(r.video_url?(p.img.hidden=!0,p.video.hidden=!1,p.videoSource.src=r.video_url,p.video.load()):(p.video.hidden=!0,p.img.hidden=!1,p.img.src=r.url||X),p.commentRead.textContent=r.comment||"No comment provided.",["tw","fb","ig"].forEach(w=>{const v=w==="tw"?"twitter_url":w==="fb"?"fb_url":"instagram_url";try{new URL(r[v]),p.social[w].href=r[v],p.social[w].style.display="inline-block"}catch{p.social[w].style.display="none"}}),S){p.editBtn.hidden=!0,p.readBox.hidden=!0,p.commentEdit.hidden=!0,p.editBox.hidden=!0;const w=e("#submissionRepliesContainer");w&&(w.style.display="none")}else u?(p.editBtn.hidden=!1,p.readBox.hidden=!1):p.editBtn.hidden=p.readBox.hidden=p.commentEdit.hidden=p.editBox.hidden=!0;const Z=Array.isArray(k)&&k.length>0&&I>=0;s&&t&&(Z?(s.style.display="inline-flex",t.style.display="inline-flex",s.disabled=I<=0,t.disabled=I>=k.length-1):(s.style.display="none",t.style.display="none")),l(),O("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),n(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const r=e("#submissionDetailModal").dataset.submissionId;C(`/quests/submission/${r}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:d})=>{if(!d.success)throw new Error(d.message||"Save failed");e("#submissionComment").textContent=d.comment||"No comment provided.",n(!1)}).catch(d=>alert(`Could not save comment: ${d.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>n(!1));function n(r){e("#submissionComment").hidden=r,e("#commentReadButtons").hidden=r,e("#submissionCommentEdit").hidden=!r,e("#commentEditButtons").hidden=!r}function l(){const r=e("#submissionDetailModal").dataset.submissionId;r&&(q(`/quests/submissions/${r}`).then(({json:d})=>{e("#submissionLikeCount").textContent=d.like_count||0,e("#submissionLikeBtn").classList.toggle("active",d.liked_by_current_user)}),S||q(`/quests/submission/${r}/replies`).then(({json:d})=>{const b=e("#submissionRepliesList");if(!b)return;b.innerHTML="",d.replies.forEach(h=>{const g=document.createElement("div");g.className="reply mb-1";const E=document.createElement("a");E.href="#",E.className="reply-user-link",E.dataset.userId=h.user_id;const L=document.createElement("strong");L.textContent=h.user_display,E.appendChild(L),g.appendChild(E),g.appendChild(document.createTextNode(`: ${h.content}`)),E.addEventListener("click",$=>{$.preventDefault(),T(h.user_id)}),b.appendChild(g)});const u=e("#submissionReplyEdit"),y=e("#postReplyBtn");d.replies.length>=10?(u.disabled=!0,y.disabled=!0,i&&(i.style.display="block")):(u.disabled=!1,y.disabled=!1,i&&(i.style.display="none"))}))}e("#submissionLikeBtn").addEventListener("click",()=>{const r=e("#submissionLikeBtn"),d=e("#submissionDetailModal").dataset.submissionId,b=r.classList.contains("active");C(`/quests/submission/${d}/like`,{method:b?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:u})=>{if(!u.success)throw new Error("Like failed");e("#submissionLikeCount").textContent=u.like_count,r.classList.toggle("active",u.liked)}).catch(u=>alert(u.message))}),e("#postReplyBtn").addEventListener("click",()=>{if(S)return;const r=e("#submissionDetailModal").dataset.submissionId,d=e("#submissionReplyEdit"),b=d.value.trim();!r||!b||C(`/quests/submission/${r}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:b})}).then(({status:u,json:y})=>{if(!y.success){if(y.message==="Reply limit of 10 reached"){m();return}if(u===409&&y.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(y.message||"Error")}const h=e("#submissionRepliesList"),g=document.createElement("div");g.className="reply mb-1";const E=document.createElement("strong");E.textContent=y.reply.user_display,g.appendChild(E),g.appendChild(document.createTextNode(`: ${y.reply.content}`)),h.insertBefore(g,h.firstChild),d.value="",h.children.length>=10&&m()}).catch(u=>alert(u.message))});function m(){const r=e("#submissionReplyEdit"),d=e("#postReplyBtn");r.disabled=!0,d.disabled=!0,i&&(i.style.display="block")}s&&s.addEventListener("click",()=>{if(!Array.isArray(k)||I<=0)return;const r=I-1,d=k[r];d&&M({...d,read_only:S,album_items:k,album_index:r})}),t&&t.addEventListener("click",()=>{if(!Array.isArray(k)||I>=k.length-1)return;const r=I+1,d=k[r];d&&M({...d,read_only:S,album_items:k,album_index:r})})});export{T as a,Ce as q,M as s};
