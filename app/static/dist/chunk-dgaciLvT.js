import{l as p,c as w,o as Q,e as F,f as T,g as H,a as Y,h as J,b as K}from"./chunk-YjL0ziQy.js";function B(e){const s=document.getElementById("game_IdHolder"),i=s?s.getAttribute("data-game-id"):null,n=i&&!isNaN(parseInt(i,10))&&i!=="0"?`?game_id=${i}`:"";fetch(`/profile/${e}${n}`).then(t=>t.json()).then(t=>{if(!t.riding_preferences_choices){p.error("Riding preferences choices missing.");return}const a=document.getElementById("userProfileDetails");if(!a){p.error("Profile details containers not found");return}const r=t.current_user_id===t.user.id;a.innerHTML=`
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
                          ${t.riding_preferences_choices.map((d,m)=>`
                            <div class="form-check mb-2">
                              <input class="form-check-input" type="checkbox"
                                      id="ridingPref-${m}" name="riding_preferences"
                                      value="${d[0]}"
                                      ${t.user.riding_preferences.includes(d[0])?"checked":""}>
                              <label class="form-check-label" for="ridingPref-${m}">${d[1]}</label>
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
      `;const o=document.getElementById("userProfileModalLabel");o.textContent=`${t.user.display_name||t.user.username}'s Profile`;const l=document.getElementById("followBtn");l&&(l.style.display="");const u=document.getElementById("followerCount");let c=t.user.follower_count;function f(){u&&(u.textContent=`${c} follower${c===1?"":"s"}`)}if(f(),!r&&l){let m=function(){d?(l.textContent="Following",l.classList.remove("btn-primary"),l.classList.add("btn-outline-primary")):(l.textContent="Follow",l.classList.remove("btn-outline-primary"),l.classList.add("btn-primary"))};l&&(l.style.display="",l.classList.remove("d-none"));let d=t.current_user_following;m(),l.onclick=async()=>{const $=d?"unfollow":"follow",{status:E}=await w(`/profile/${t.user.username}/${$}`,{method:"POST",headers:{"Content-Type":"application/json"}});if(E!==200){p.error("Follow toggle failed");return}d=!d,c+=d?1:-1,m(),f()}}else{const d=document.getElementById("followBtn");d&&(d.style.display="none")}Q("userProfileModal");const b=document.getElementById("editProfileBtn");b&&b.addEventListener("click",X);const h=document.getElementById("saveProfileBtn");h&&h.addEventListener("click",()=>ee(e));const g=document.getElementById("cancelProfileBtn");g&&g.addEventListener("click",d=>{d.preventDefault(),Z(e)});const _=document.getElementById("updatePasswordBtn");_&&_.addEventListener("click",()=>{window.location.href="/auth/update_password"});const C=document.getElementById("saveBikeBtn");C&&C.addEventListener("click",()=>te(e)),document.querySelectorAll("[data-delete-submission]").forEach(d=>{d.addEventListener("click",()=>{const m=d.getAttribute("data-delete-submission");ie(m,"profileSubmissions",t.user.id)})});const L=document.getElementById("deleteAccountForm");L&&L.addEventListener("submit",d=>{d.preventDefault(),oe()});const P=document.getElementById("profileTabSelect");P&&(P.addEventListener("change",d=>{const m=d.target.value,$=document.querySelector(`#profileTabs a[href="#${m}"]`);$&&new bootstrap.Tab($).show()}),document.querySelectorAll('#profileTabs a[data-bs-toggle="tab"]').forEach(d=>{d.addEventListener("shown.bs.tab",m=>{P.value=m.target.getAttribute("href").slice(1)})}))}).catch(t=>{p.error("Failed to load profile:",t),alert("Could not load user profile. Please try again.")})}document.querySelectorAll("[data-floating-ui-tooltip]").forEach(e=>{tippy(e,{content:e.getAttribute("data-floating-ui-tooltip"),placement:"top",animation:"scale-subtle"})});document.querySelectorAll(".needs-validation").forEach(e=>{e.addEventListener("submit",s=>{e.checkValidity()||(s.preventDefault(),s.stopPropagation()),e.classList.add("was-validated")},!1)});function X(){const e=document.getElementById("profileViewMode"),s=document.getElementById("profileEditMode");if(!e||!s){p.error("Profile edit mode elements missing");return}e.classList.toggle("d-none"),s.classList.toggle("d-none")}function Z(e){B(e)}function ee(e){const s=document.getElementById("editProfileForm");if(!s){p.error("Edit profile form not found");return}const i=new FormData(s),n=document.getElementById("profilePictureInput");n.files.length>0&&i.append("profile_picture",n.files[0]);const t=[];s.querySelectorAll('input[name="riding_preferences"]:checked').forEach(a=>{t.push(a.value)}),i.delete("riding_preferences"),t.forEach(a=>{i.append("riding_preferences",a)}),w(`/profile/${e}/edit`,{method:"POST",body:i}).then(({json:a})=>{if(a.error){let r=`Error: ${a.error}`;if(a.details){const o=[];Object.values(a.details).forEach(l=>{o.push(l.join(", "))}),o.length&&(r+=` - ${o.join("; ")}`)}alert(r)}else alert("Profile updated successfully."),B(e)}).catch(a=>{p.error("Error updating profile:",a),alert("Failed to update profile. Please try again.")})}function te(e){const s=document.getElementById("editBikeForm");if(!s){p.error("Edit bike form not found");return}const i=new FormData(s),n=document.getElementById("bikePicture");n.files.length>0&&i.append("bike_picture",n.files[0]),w(`/profile/${e}/edit-bike`,{method:"POST",body:i}).then(({json:t})=>{t.error?alert(`Error: ${t.error}`):(alert("Bike details updated successfully."),B(e))}).catch(t=>{p.error("Error updating bike details:",t),alert("Failed to update bike details. Please try again.")})}function ie(e,s,i){w(`/quests/quest/delete_submission/${e}`,{method:"POST"}).then(({json:n})=>{if(n.success)alert("Submission deleted successfully."),B(i);else throw new Error(n.message)}).catch(n=>{p.error("Error deleting submission:",n),alert("Error during deletion: "+n.message)})}function oe(){confirm("Are you sure you want to delete your account? This action cannot be undone.")&&w("/auth/delete_account",{method:"POST",headers:{"Content-Type":"application/json"}}).then(()=>{window.location.href="/"}).catch(e=>{p.error("Error deleting account:",e),alert("Failed to delete account. Please try again.")})}document.addEventListener("click",e=>{const s=e.target.closest("[data-user-profile]");if(!s)return;e.preventDefault();const i=s.getAttribute("data-user-profile");i&&B(i)});function se(e){const s=document.querySelector(`meta[name="${e}"]`);return s?s.content:""}const ne=Number(se("current-user-id")||0),re=H(),k=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");function O(e){F(),T(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:s})=>{const{quest:i,userCompletion:n,canVerify:t,nextEligibleTime:a}=s;if(!V(i,n.completions,t,e,a)){p.error("populateQuestDetails – required element missing");return}z(i,n.completions,a,t),Q("questDetailModal"),N(),G(e)}).catch(s=>{p.error("Error opening quest detail modal:",s),alert("Sign in to view quest details.")})}function M(e){T(`/quests/detail/${encodeURIComponent(e)}/user_completion`).then(({json:s})=>{const{quest:i,userCompletion:n,canVerify:t,nextEligibleTime:a}=s;if(!V(i,n.completions,t,e,a)){p.error("populateQuestDetails - required element missing");return}z(i,n.completions,a,t),N(),G(e)}).catch(s=>{p.error("Failed to refresh quest detail modal:",s)})}function N(){const e=document.querySelectorAll("img.lazyload"),s=new IntersectionObserver((i,n)=>{i.forEach(t=>{if(t.isIntersecting){const a=t.target;a.src=a.getAttribute("data-src"),a.classList.remove("lazyload"),n.unobserve(a)}})});e.forEach(i=>{s.observe(i)})}function V(e,s,i,n,t){var b,h,g;const a=s>=e.completion_limit?" - complete":"",r={modalQuestTitle:document.getElementById("modalQuestTitle"),modalQuestDescription:document.getElementById("modalQuestDescription"),modalQuestTips:document.getElementById("modalQuestTips"),modalQuestPoints:document.getElementById("modalQuestPoints"),modalQuestCompletionLimit:document.getElementById("modalQuestCompletionLimit"),modalQuestBadgeAwarded:document.getElementById("modalQuestBadgeAwarded"),modalQuestCategory:document.getElementById("modalQuestCategory"),modalQuestVerificationType:document.getElementById("modalQuestVerificationType"),modalQuestBadgeImage:document.getElementById("modalQuestBadgeImage"),modalQuestCompletions:document.getElementById("modalQuestCompletions"),modalCountdown:document.getElementById("modalCountdown")};for(let _ in r)if(!r[_])return p.error(`Error: Missing element ${_}`),!1;const o={badge:(b=r.modalQuestBadgeImage)==null?void 0:b.closest(".quest-detail-item"),badgeAwarded:(h=r.modalQuestBadgeAwarded)==null?void 0:h.closest(".quest-detail-item"),category:(g=r.modalQuestCategory)==null?void 0:g.closest(".quest-detail-item")};for(let _ in o)if(!o[_])return p.error(`Error: Missing card element ${_}`),!1;r.modalQuestTitle.innerText=`${e.title}${a}`,r.modalQuestDescription.textContent=e.description,r.modalQuestTips.textContent=e.tips||"No tips available",r.modalQuestPoints.innerText=`${e.points}`,r.modalQuestCategory.innerText=e.category||"No category set";const l=e.completion_limit>1?`${e.completion_limit} times`:`${e.completion_limit} time`;r.modalQuestCompletionLimit.innerText=`${l} ${e.frequency}`;const u=e.badge_awarded>1?`${e.badge_awarded} times`:`${e.badge_awarded} time`;switch(e.badge_awarded!=null?r.modalQuestBadgeAwarded.innerText=`After ${u}`:r.modalQuestBadgeAwarded.innerText="No badge awarded",e.verification_type){case"photo_comment":r.modalQuestVerificationType.innerText="Must upload a photo to earn points! Comment optional.";break;case"photo":r.modalQuestVerificationType.innerText="Must upload a photo to earn points!";break;case"comment":r.modalQuestVerificationType.innerText="Must upload a comment to earn points!";break;case"qr_code":r.modalQuestVerificationType.innerText="Find the QR code and post a photo to earn points!";break;default:r.modalQuestVerificationType.innerText="Not specified";break}const c=e.badge&&e.badge.image?`/static/images/badge_images/${e.badge.image}`:k;r.modalQuestBadgeImage.setAttribute("data-src",c),r.modalQuestBadgeImage.src=k,r.modalQuestBadgeImage.classList.add("lazyload"),r.modalQuestBadgeImage.alt=e.badge&&e.badge.name?`Badge: ${e.badge.name}`:"Default Badge",e.badge_option==="none"?(o.badge.classList.add("hidden"),o.badgeAwarded.classList.add("hidden"),o.category.classList.add("hidden")):(o.badge.classList.remove("hidden"),o.badgeAwarded.classList.remove("hidden"),o.category.classList.remove("hidden")),r.modalQuestCompletions.innerText=`Total Completions: ${s}`;const f=t&&new Date(t);return!i&&f&&f>new Date?(r.modalCountdown.innerText=`Next eligible time: ${f.toLocaleString()}`,r.modalCountdown.style.color="red"):(r.modalCountdown.innerText="You are currently eligible to verify!",r.modalCountdown.style.color="green"),de(n,i,e.verification_type),!0}function z(e,s,i,n){const t=document.querySelector(".user-quest-data");if(!t){p.error("Parent element .user-quest-data not found");return}[{id:"modalQuestCompletions",value:`${s||0}`},{id:"modalCountdown",value:""}].forEach(r=>{let o=document.getElementById(r.id);o||(o=document.createElement("p"),o.id=r.id,t.appendChild(o)),o.innerText=r.value}),ae(document.getElementById("modalCountdown"),i,n)}function ae(e,s,i){if(!i&&s){const n=new Date(s),t=new Date;if(n>t){const a=n-t;e.innerText=`Next eligible time: ${le(a)}`}else e.innerText="You are currently eligible to verify!"}else e.innerText="You are currently eligible to verify!"}function le(e){const s=Math.floor(e/1e3%60),i=Math.floor(e/(1e3*60)%60),n=Math.floor(e/(1e3*60*60)%24);return`${Math.floor(e/(1e3*60*60*24))}d ${n}h ${i}m ${s}s`}function de(e,s,i){const n=document.querySelector(".user-quest-data");if(!n){p.error("Parent element .user-quest-data not found");return}if(n.innerHTML="",s){const t=document.createElement("div");t.id=`verifyQuestForm-${e}`,t.className="verify-quest-form",t.style.display="block";const a=ce(i.trim().toLowerCase(),e);t.appendChild(a),n.appendChild(t),me(e)}else{const t=document.createElement("p");t.className="epic-message text-success",t.textContent="Thanks for completing the quest.",n.appendChild(t)}}function ce(e,s){const i=document.createElement("form");i.enctype="multipart/form-data",i.className="epic-form",i.method="post",i.action=`/quests/quest/${encodeURIComponent(s)}/submit`;const n=document.createElement("input");n.type="hidden",n.name="csrf_token",n.value=re,i.appendChild(n);const t=document.createElement("h2");switch(t.style.textAlign="center",t.textContent="Verify Your Quest",i.appendChild(t),e){case"photo":i.appendChild(D("image","Upload a Photo","image/*")),i.appendChild(S());break;case"comment":i.appendChild(q("verificationComment","Enter a Comment","Enter a comment...",!0)),i.appendChild(S());break;case"photo_comment":i.appendChild(D("image","Upload a Photo","image/*")),i.appendChild(q("verificationComment","Enter a Comment (optional)","Enter a comment...",!1)),i.appendChild(S());break;case"video":i.appendChild(D("video","Upload a Video","video/*")),i.appendChild(q("verificationComment","Add a Comment (optional)","Enter an optional comment...",!1)),i.appendChild(S());break;case"qr_code":{const a=document.createElement("p");a.className="epic-message",a.textContent="Find and scan the QR code. No submission required here.",i.appendChild(a);break}case"pause":{const a=document.createElement("p");a.className="epic-message",a.textContent="Quest is currently paused.",i.appendChild(a);break}default:{const a=document.createElement("p");a.className="epic-message",a.textContent="Submission requirements are not set correctly.",i.appendChild(a)}}return i}function D(e,s,i,n){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=s,t.appendChild(a);const r=document.createElement("input");return r.type="file",r.id=e,r.name=e,r.className="epic-input",r.accept=i,r.required=!0,t.appendChild(r),t}function q(e,s,i,n){const t=document.createElement("div");t.className="form-group";const a=document.createElement("label");a.htmlFor=e,a.className="epic-label",a.textContent=s,t.appendChild(a);const r=document.createElement("textarea");return r.id=e,r.name=e,r.className="epic-textarea",r.placeholder=i,n&&(r.required=!0),t.appendChild(r),t}function S(){const e=document.createElement("div");e.className="form-group";const s=document.createElement("button");return s.type="submit",s.textContent="Submit Verification",e.appendChild(s),e}function me(e){const s=document.getElementById(`verifyQuestForm-${e}`);if(!s){p.error("Form container not found for quest ID:",e);return}const i=s.querySelector("form");if(!i){p.error("Form element missing for quest ID:",e);return}i.addEventListener("submit",function(n){fe(n,e)})}function A(e,s){e&&(s&&s.trim()?(e.href=s,e.style.display="inline"):e.style.display="none")}function ue(e){if(typeof e!="number")return;const s=document.getElementById("total-points");if(!s)return;const i=s.querySelector(".points-emphasized");i?i.textContent=e:s.textContent=`Your Carbon Reduction Points: ${e}`}function pe(e,s,i){const n=document.querySelector(`#questTableBody tr[data-quest-id="${e}"]`);if(!n)return;const t=n.querySelectorAll(".quest-stats-cell");t.length>=2&&(t[0].innerText=s,t[1].innerText=i)}function j(e){A(document.getElementById("twitterLink"),e.twitter_url),A(document.getElementById("facebookLink"),e.fb_url),A(document.getElementById("instagramLink"),e.instagram_url)}let R=!1;async function fe(e,s){if(e.preventDefault(),R)return;R=!0;const i=e.target.querySelector('[type="submit"]');i&&(i.disabled=!0);try{Y("Uploading...");const n=e.target.querySelector('input[type="file"]'),t=n?n.files[0]:null;if(t&&t.type.startsWith("video/")&&t.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(t&&t.type.startsWith("image/")&&t.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}if(t&&t.type.startsWith("video/"))try{const l=await be(t);if(isFinite(l)&&l>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}const a=new FormData(e.target);a.append("user_id",ne);const{status:r,json:o}=await w(`/quests/quest/${encodeURIComponent(s)}/submit`,{method:"POST",body:a});if(r!==200)throw r===403&&o.message==="This quest cannot be completed outside of the game dates"?new Error("The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu."):new Error(o.message||`Server responded with status ${r}`);if(!o.success)throw new Error(o.message);if(!o.success)throw new Error(o.message);ue(o.total_points),j(o),pe(s,o.new_completion_count,o.total_completion_count),M(s),e.target.reset()}catch(n){p.error("Submission error:",n),alert(`Error during submission: ${n.message}`)}finally{R=!1,i&&(i.disabled=!1),J()}}function be(e){return new Promise((s,i)=>{try{const n=URL.createObjectURL(e),t=document.createElement("video");t.preload="metadata",t.onloadedmetadata=()=>{URL.revokeObjectURL(n),s(t.duration||0)},t.onerror=()=>{URL.revokeObjectURL(n),i(new Error("metadata error"))},t.src=n}catch(n){i(n)}})}async function G(e){const s=encodeURIComponent(e);try{const{json:i}=await T(`/quests/quest/${s}/submissions`),n=document.getElementById("twitterLink"),t=document.getElementById("facebookLink"),a=document.getElementById("instagramLink");if(i&&i.length){const o=i[0],l=document.getElementById("submissionImage"),u=document.getElementById("submissionVideo"),c=document.getElementById("submissionVideoSource"),f=document.getElementById("submissionComment"),b=document.getElementById("submitterProfileLink"),h=document.getElementById("submitterProfileImage"),g=document.getElementById("submitterProfileCaption");o.video_url?(l.hidden=!0,u.hidden=!1,c.src=o.video_url,u.load()):(u.hidden=!0,l.hidden=!1,l.src=o.image_url||k),f.textContent=o.comment||"No comment provided.",b.href=`/profile/${encodeURIComponent(o.user_id)}`,h.src=o.user_profile_picture||k,g.textContent=o.user_display_name||o.user_username||`User ${o.user_id}`,j(o)}else[n,t,a].forEach(o=>{o&&(o.style.display="none")});const r=i.slice().reverse().map(o=>({id:o.id,url:o.image_url||(o.video_url?null:k),video_url:o.video_url,alt:"Submission Image",comment:o.comment,user_id:o.user_id,user_display_name:o.user_display_name,user_username:o.user_username,user_profile_picture:o.user_profile_picture,twitter_url:o.twitter_url,fb_url:o.fb_url,instagram_url:o.instagram_url,quest_id:e}));ge(r)}catch(i){p.error("Failed to fetch submissions:",i),alert("Could not load submissions. Please try again.")}}function U(e){if(!e)return p.error(`Invalid URL detected: ${e}`),!1;try{if(e.startsWith("/"))return!0;const s=new URL(e);if(s.protocol==="http:"||s.protocol==="https:")return[".jpg",".jpeg",".png",".gif",".webp"].some(n=>s.pathname.toLowerCase().endsWith(n))}catch{return p.error(`Invalid URL detected: ${e}`),!1}return!1}function ge(e){var l;const s=document.getElementById("submissionBoard");if(!s){p.error("submissionBoard element not found");return}s.innerHTML="";const i=((l=document.getElementById("questDetailModal"))==null?void 0:l.getAttribute("data-placeholder-url"))||k,n=U(i)?i:k,t=u=>u.startsWith("/static/"),a=u=>u.replace(/^\/static\//,""),r=window.innerWidth<=480?70:100,o=Math.round(r*(window.devicePixelRatio||2));e.forEach(u=>{let c;if(u.video_url)c=document.createElement("video"),c.src=u.video_url,c.preload="metadata",c.muted=!0,c.playsInline=!0,c.style.objectFit="cover";else{c=document.createElement("img");const f=U(u.url)?u.url:n,b=t(f)?`/resize_image?path=${encodeURIComponent(a(f))}&width=${o}`:f;c.src=k,c.setAttribute("data-src",b),c.classList.add("lazyload"),c.alt=u.alt||"Submission Image"}c.style.width=`${r}px`,c.style.height="auto",c.style.marginRight="10px",u.video_url||(c.onerror=()=>{t(n)?c.src=`/resize_image?path=${encodeURIComponent(a(n))}&width=${o}`:c.src=encodeURI(n)}),c.onclick=()=>W(u),s.appendChild(c)}),N()}function he(e){e.querySelectorAll("span, img").forEach(i=>{i.classList.toggle("hidden")})}document.addEventListener("click",e=>{const s=e.target.closest("[data-quest-detail]");if(s){e.preventDefault(),O(s.getAttribute("data-quest-detail"));return}const i=e.target.closest("[data-toggle-content]");i&&i.closest("#questDetailModal")&&(e.preventDefault(),he(i))});const ve=Object.freeze(Object.defineProperty({__proto__:null,openQuestDetailModal:O,refreshQuestDetailModal:M},Symbol.toStringTag,{value:"Module"}));let W;document.addEventListener("DOMContentLoaded",()=>{const e=o=>document.querySelector(o);if(!e("#submissionDetailModal"))return;const i=document.getElementById("replyLimitMessage"),n=document.querySelector('meta[name="placeholder-image"]').getAttribute("content");W=function(o){const l=e("#submissionDetailModal");l.dataset.submissionId=o.id,l.dataset.questId=o.quest_id||"";const u=Number(l.dataset.currentUserId),c=Number(o.user_id)===u,f=l.dataset.isAdmin==="True"||l.dataset.isAdmin==="true",b=e("#editPhotoBtn"),h=e("#photoEditControls"),g=e("#submissionPhotoInput"),_=e("#savePhotoBtn"),C=e("#cancelPhotoBtn"),L=e("#deleteSubmissionBtn");b.hidden=!c,L.hidden=!(c||f),h.hidden=!0,b.onclick=()=>{h.hidden=!1,b.hidden=!0,g&&g.click()},C.onclick=()=>{g.value="",h.hidden=!0,b.hidden=!1},L.onclick=()=>{if(!confirm("Are you sure you want to delete this submission?"))return;const E=l.dataset.submissionId;w(`/quests/quest/delete_submission/${E}`,{method:"POST"}).then(({json:y})=>{if(!y.success)throw new Error(y.message||"Delete failed");K("submissionDetailModal"),F(),l.dataset.questId&&M(l.dataset.questId),alert("Submission deleted successfully.")}).catch(y=>alert("Error deleting submission: "+y.message))},_.onclick=async()=>{const E=l.dataset.submissionId,y=g.files[0];if(!y)return alert("Please select an image first.");if(y.type.startsWith("video/")&&y.size>25*1024*1024){alert("Video must be 25 MB or smaller.");return}if(y.type.startsWith("image/")&&y.size>8*1024*1024){alert("Image must be 8 MB or smaller.");return}const I=new FormData;if(y.type.startsWith("video/")){try{const v=await P(y);if(isFinite(v)&&v>10){alert("Video must be 10 seconds or shorter.");return}}catch{alert("Unable to read video metadata. Please try another file.");return}I.append("video",y)}else I.append("photo",y);w(`/quests/submission/${E}/photo`,{method:"PUT",body:I}).then(({json:v})=>{if(!v.success)throw new Error(v.message||"Upload failed");v.video_url?(e("#submissionImage").hidden=!0,e("#submissionVideo").hidden=!1,e("#submissionVideoSource").src=v.video_url,e("#submissionVideo").load()):(e("#submissionVideo").hidden=!0,e("#submissionImage").hidden=!1,e("#submissionImage").src=v.image_url),C.click()}).catch(v=>alert(v.message))};function P(E){return new Promise((y,I)=>{try{const v=URL.createObjectURL(E),x=document.createElement("video");x.preload="metadata",x.onloadedmetadata=()=>{URL.revokeObjectURL(v),y(x.duration||0)},x.onerror=()=>{URL.revokeObjectURL(v),I(new Error("metadata error"))},x.src=v}catch(v){I(v)}})}e("#submissionReplyEdit").hidden=c,e("#postReplyBtn").hidden=c,e("#ownerNotice").hidden=!c;const d=e("#submissionRepliesContainer");c?d.hidden=!0:d.hidden=!1;const m={img:e("#submissionImage"),video:e("#submissionVideo"),videoSource:e("#submissionVideoSource"),imgOverlay:e("#submitterProfileImageOverlay"),commentRead:e("#submissionComment"),commentEdit:e("#submissionCommentEdit"),readBox:e("#commentReadButtons"),editBox:e("#commentEditButtons"),editBtn:e("#editCommentBtn"),profileImg:e("#submitterProfileImage"),profileImgOverlay:e("#submitterProfileImageOverlay"),profileCap:e("#submitterProfileCaption"),profileLink:e("#submitterProfileLink"),social:{tw:e("#twitterLink"),fb:e("#facebookLink"),ig:e("#instagramLink")}};m.profileImg.src=o.user_profile_picture||n,m.profileImgOverlay.src=m.profileImg.src,m.profileCap.textContent=o.user_display_name||o.user_username||"—",m.profileLink.onclick=E=>{E.preventDefault(),B(o.user_id)},m.imgOverlay.parentElement.onclick=m.profileLink.onclick;const $=n;o.video_url?(m.img.hidden=!0,m.video.hidden=!1,m.videoSource.src=o.video_url,m.video.load()):(m.video.hidden=!0,m.img.hidden=!1,m.img.src=o.url||$),m.commentRead.textContent=o.comment||"No comment provided.",["tw","fb","ig"].forEach(E=>{const y=E==="tw"?"twitter_url":E==="fb"?"fb_url":"instagram_url";try{new URL(o[y]),m.social[E].href=o[y],m.social[E].style.display="inline-block"}catch{m.social[E].style.display="none"}}),c?(m.editBtn.hidden=!1,m.readBox.hidden=!1):m.editBtn.hidden=m.readBox.hidden=m.commentEdit.hidden=m.editBox.hidden=!0,a(),Q("submissionDetailModal")},e("#editCommentBtn").addEventListener("click",()=>{e("#submissionCommentEdit").value=e("#submissionComment").textContent.trim(),t(!0)}),e("#saveCommentBtn").addEventListener("click",()=>{const o=e("#submissionDetailModal").dataset.submissionId;w(`/quests/submission/${o}/comment`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({comment:e("#submissionCommentEdit").value.trim()})}).then(({json:l})=>{if(!l.success)throw new Error(l.message||"Save failed");e("#submissionComment").textContent=l.comment||"No comment provided.",t(!1)}).catch(l=>alert(`Could not save comment: ${l.message}`))}),e("#cancelCommentBtn").addEventListener("click",()=>t(!1));function t(o){e("#submissionComment").hidden=o,e("#commentReadButtons").hidden=o,e("#submissionCommentEdit").hidden=!o,e("#commentEditButtons").hidden=!o}function a(){const o=e("#submissionDetailModal").dataset.submissionId;o&&(T(`/quests/submissions/${o}`).then(({json:l})=>{e("#submissionLikeCount").textContent=l.like_count||0,e("#submissionLikeBtn").classList.toggle("active",l.liked_by_current_user)}),T(`/quests/submission/${o}/replies`).then(({json:l})=>{const u=e("#submissionRepliesList");u.innerHTML="",l.replies.forEach(b=>{const h=document.createElement("div");h.className="reply mb-1";const g=document.createElement("a");g.href="#",g.className="reply-user-link",g.dataset.userId=b.user_id;const _=document.createElement("strong");_.textContent=b.user_display,g.appendChild(_),h.appendChild(g),h.appendChild(document.createTextNode(`: ${b.content}`)),g.addEventListener("click",C=>{C.preventDefault(),B(b.user_id)}),u.appendChild(h)});const c=e("#submissionReplyEdit"),f=e("#postReplyBtn");l.replies.length>=10?(c.disabled=!0,f.disabled=!0,i&&(i.style.display="block")):(c.disabled=!1,f.disabled=!1,i&&(i.style.display="none"))}))}e("#submissionLikeBtn").addEventListener("click",()=>{const o=e("#submissionLikeBtn"),l=e("#submissionDetailModal").dataset.submissionId,u=o.classList.contains("active");w(`/quests/submission/${l}/like`,{method:u?"DELETE":"POST",headers:{"Content-Type":"application/json"}}).then(({json:c})=>{if(!c.success)throw new Error("Like failed");e("#submissionLikeCount").textContent=c.like_count,o.classList.toggle("active",c.liked)}).catch(c=>alert(c.message))}),e("#postReplyBtn").addEventListener("click",()=>{const o=e("#submissionDetailModal").dataset.submissionId,l=e("#submissionReplyEdit"),u=l.value.trim();!o||!u||w(`/quests/submission/${o}/replies`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:u})}).then(({status:c,json:f})=>{if(!f.success){if(f.message==="Reply limit of 10 reached"){r();return}if(c===409&&f.message==="Duplicate reply")return alert("You have already posted that exact reply.");throw new Error(f.message||"Error")}const b=e("#submissionRepliesList"),h=document.createElement("div");h.className="reply mb-1";const g=document.createElement("strong");g.textContent=f.reply.user_display,h.appendChild(g),h.appendChild(document.createTextNode(`: ${f.reply.content}`)),b.insertBefore(h,b.firstChild),l.value="",b.children.length>=10&&r()}).catch(c=>alert(c.message))});function r(){const o=e("#submissionReplyEdit"),l=e("#postReplyBtn");o.disabled=!0,l.disabled=!0,i&&(i.style.display="block")}});export{B as a,ve as q,W as s};
