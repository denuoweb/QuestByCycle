
/* ------------------------------------------------------------------ */
/*  HELPER: read meta-content                                         */
/* ------------------------------------------------------------------ */
function meta(name) {
  const tag = document.querySelector(`meta[name="${name}"]`);
  return tag ? tag.content : '';
}

/*  Current user ID and CSRF token pulled from <meta> tags.           */
const CURRENT_USER_ID = Number(meta('current-user-id') || 0);
const CSRF_TOKEN      = meta('csrf-token');

/* ------------------------------------------------------------------ */
/*  OPEN QUEST DETAIL MODAL                                           */
/* ------------------------------------------------------------------ */
function openQuestDetailModal(questId) {
  resetModalContent();

  fetch(`/quests/detail/${questId}/user_completion`, { credentials: 'same-origin' })
    .then(r => r.json())
    .then(data => {
      const { quest, userCompletion, canVerify, nextEligibleTime } = data;
      if (
        !populateQuestDetails(
          quest,
          userCompletion.completions,
          canVerify,
          questId,
          nextEligibleTime
        )
      ) {
        console.error('populateQuestDetails – required element missing');
        return;
      }

      ensureDynamicElementsExistAndPopulate(
        quest,
        userCompletion.completions,
        nextEligibleTime,
        canVerify
      );

      fetchSubmissions(questId);
      openModal('questDetailModal');
    })
    .catch(err => {
      console.error('Error opening quest detail modal:', err);
      alert('Sign in to view quest details.');
    });
}


function lazyLoadImages() {
    const images = document.querySelectorAll('img.lazyload');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.classList.remove('lazyload');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => {
        imageObserver.observe(img);
    });
}

function populateQuestDetails(quest, userCompletionCount, canVerify, questId, nextEligibleTime) {
    const completeText = userCompletionCount >= quest.completion_limit ? " - complete" : "";
    const elements = {
        'modalQuestTitle': document.getElementById('modalQuestTitle'),
        'modalQuestDescription': document.getElementById('modalQuestDescription'),
        'modalQuestTips': document.getElementById('modalQuestTips'),
        'modalQuestPoints': document.getElementById('modalQuestPoints'),
        'modalQuestCompletionLimit': document.getElementById('modalQuestCompletionLimit'),
        'modalQuestBadgeAwarded': document.getElementById('modalQuestBadgeAwarded'),
        'modalQuestCategory': document.getElementById('modalQuestCategory'),
        'modalQuestVerificationType': document.getElementById('modalQuestVerificationType'),
        'modalQuestBadgeImage': document.getElementById('modalQuestBadgeImage'),
        'modalQuestCompletions': document.getElementById('modalQuestCompletions'),
        'modalCountdown': document.getElementById('modalCountdown')
    };

    for (let key in elements) {
        if (!elements[key]) {
            console.error(`Error: Missing element ${key}`);
            return false;
        }
    }

    elements['modalQuestTitle'].innerText = `${quest.title}${completeText}`;
    elements['modalQuestDescription'].innerHTML = quest.description;
    elements['modalQuestTips'].innerHTML = quest.tips || 'No tips available';
    elements['modalQuestPoints'].innerText = `${quest.points}`;
    elements['modalQuestCategory'].innerText = quest.category || 'No category set';
    
    const completionText = quest.completion_limit > 1 ? `${quest.completion_limit} times` : `${quest.completion_limit} time`;
    elements['modalQuestCompletionLimit'].innerText = `${completionText} ${quest.frequency}`;

    const completionTextAward = quest.badge_awarded > 1 ? `${quest.badge_awarded} times` : `${quest.badge_awarded} time`;
    if (quest.badge_awarded != null) {
        elements['modalQuestBadgeAwarded'].innerText = `After ${completionTextAward}`;
    } else {
        elements['modalQuestBadgeAwarded'].innerText = 'No badge awarded';
    }
    switch (quest.verification_type) {
        case 'photo_comment':
            elements['modalQuestVerificationType'].innerText = "Must upload a photo and a comment to earn points!";
            break;
        case 'photo':
            elements['modalQuestVerificationType'].innerText = "Must upload a photo to earn points!";
            break;
        case 'comment':
            elements['modalQuestVerificationType'].innerText = "Must upload a comment to earn points!";
            break;
        case 'qr_code':
            elements['modalQuestVerificationType'].innerText = "Find the QR code and post a photo to earn points!";
            break;
        default:
            elements['modalQuestVerificationType'].innerText = 'Not specified';
            break;
    }

    const badgeImagePath = quest.badge && quest.badge.image ? `/static/images/badge_images/${quest.badge.image}` : '/static/images/badge_images/default_badge.png';
    elements['modalQuestBadgeImage'].src = badgeImagePath;
    elements['modalQuestBadgeImage'].alt = quest.badge && quest.badge.name ? `Badge: ${quest.badge.name}` : 'Default Badge';

    elements['modalQuestCompletions'].innerText = `Total Completions: ${userCompletionCount}`;

    const nextAvailableTime = nextEligibleTime && new Date(nextEligibleTime);
    if (!canVerify && nextAvailableTime && nextAvailableTime > new Date()) {
        elements['modalCountdown'].innerText = `Next eligible time: ${nextAvailableTime.toLocaleString()}`;
        elements['modalCountdown'].style.color = 'red';
    } else {
        elements['modalCountdown'].innerText = "You are currently eligible to verify!";
        elements['modalCountdown'].style.color = 'green';
    }

    manageVerificationSection(questId, canVerify, quest.verification_type, nextEligibleTime);
    return true;
}

function ensureDynamicElementsExistAndPopulate(quest, userCompletionCount, nextEligibleTime, canVerify) {
    const parentElement = document.querySelector('.user-quest-data');

    const dynamicElements = [
        { id: 'modalQuestCompletions', value: `${userCompletionCount || 0}` },
        { id: 'modalCountdown', value: "" }
    ];

    dynamicElements.forEach(elem => {
        let element = document.getElementById(elem.id);
        if (!element) {
            element = document.createElement('p');
            element.id = elem.id;
            parentElement.appendChild(element);
        }
        element.innerText = elem.value;
    });

    updateCountdownElement(document.getElementById('modalCountdown'), nextEligibleTime, canVerify);
}

function updateCountdownElement(countdownElement, nextEligibleTime, canVerify) {
    if (!canVerify && nextEligibleTime) {
        const nextTime = new Date(nextEligibleTime);
        const now = new Date();
        if (nextTime > now) {
            const timeDiffMs = nextTime - now;
            countdownElement.innerText = `Next eligible time: ${formatTimeDiff(timeDiffMs)}`;
        } else {
            countdownElement.innerText = "You are currently eligible to verify!";
        }
    } else {
        countdownElement.innerText = "You are currently eligible to verify!";
    }
}

function formatTimeDiff(ms) {
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / (1000 * 60)) % 60);
    const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
    const days = Math.floor(ms / (1000 * 60 * 60 * 24));
    return `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

function manageVerificationSection(questId, canVerify, verificationType, nextEligibleTime) {
    const userQuestData = document.querySelector('.user-quest-data');
    userQuestData.innerHTML = '';

    if (canVerify) {
        const verifyForm = document.createElement('div');
        verifyForm.id = `verifyQuestForm-${questId}`;
        verifyForm.className = 'verify-quest-form';
        verifyForm.style.display = 'block';

        const formHTML = getVerificationFormHTML(verificationType.trim().toLowerCase());
        verifyForm.innerHTML = formHTML;
        userQuestData.appendChild(verifyForm);

        setupSubmissionForm(questId);
    }
}

function getVerificationFormHTML(verificationType) {
  // container + heading ------------------------------------------------------
  let formHTML = `
    <form enctype="multipart/form-data" class="epic-form">
      <h2 style="text-align:center;">Verify Your Quest</h2>
  `;

  switch (verificationType) {
    /* ─────────────────────────────── PHOTO ONLY ─────────────────────────── */
    case 'photo':
      formHTML += `
        <div class="form-group">
          <label for="image" class="epic-label">Upload a Photo</label>
          <input type="file" id="image" name="image"
                 class="epic-input" accept="image/*" required>
        </div>
        <div class="form-group">
          <button type="submit">Submit Verification</button>
        </div>
      `;
      break;

    /* ─────────────────────────────── COMMENT ONLY ───────────────────────── */
    case 'comment':
      formHTML += `
        <div class="form-group">
          <label for="verificationComment" class="epic-label">Enter a Comment</label>
          <textarea id="verificationComment" name="verificationComment"
                    class="epic-textarea" placeholder="Enter a comment..." required></textarea>
        </div>
        <div class="form-group">
          <button type="submit">Submit Verification</button>
        </div>
      `;
      break;

    /* ──────────────────────────── PHOTO + COMMENT ───────────────────────── */
    case 'photo_comment':
      formHTML += `
        <div class="form-group">
          <label for="image" class="epic-label">Upload a Photo</label>
          <input type="file" id="image" name="image"
                 class="epic-input" accept="image/*" required>
        </div>
        <div class="form-group">
          <label for="verificationComment" class="epic-label">Enter a Comment</label>
          <textarea id="verificationComment" name="verificationComment"
                    class="epic-textarea" placeholder="Enter a comment..." required></textarea>
        </div>
        <div class="form-group">
          <button type="submit">Submit Verification</button>
        </div>
      `;
      break;

    /* ───────────────────────────────── QR CODE ──────────────────────────── */
    case 'qr_code':
      formHTML += `<p class="epic-message">Find and scan the QR code. No submission required here.</p>`;
      break;

    /* ─────────────────────────────────  PAUSE  ──────────────────────────── */
    case 'pause':
      formHTML += `<p class="epic-message">Quest is currently paused.</p>`;
      break;

    /* ───────────────────────────── DEFAULT / ERROR ──────────────────────── */
    default:
      formHTML += `<p class="epic-message">Submission requirements are not set correctly.</p>`;
      break;
  }

  /* close form ------------------------------------------------------------- */
  formHTML += '</form>';
  return formHTML;
}


function toggleVerificationForm(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    verifyForm.style.display = verifyForm.style.display === 'none' ? 'block' : 'none';
}

function setupSubmissionForm(questId) {
    const submissionForm = document.getElementById(`verifyQuestForm-${questId}`);
    if (submissionForm) {
        submissionForm.addEventListener('submit', function(event) {
            showLoadingModal();
            submitQuestDetails(event, questId);
        });
    } else {
        console.error("Form not found for quest ID:", questId);
    }
}

function verifyQuest(questId) {
    const verifyForm = document.getElementById(`verifyQuestForm-${questId}`);
    if (verifyForm.style.display === 'none' || verifyForm.style.display === '') {
        verifyForm.style.display = 'block';
    } else {
        verifyForm.style.display = 'none';
    }
}

function updateTwitterLink(url) {
    const twitterLink = document.getElementById('twitter-link');
    if (twitterLink) {
        console.debug('Twitter link element found, setting href:', url);
        twitterLink.href = url;
        twitterLink.style.display = 'block';
    } else {
        console.debug('Twitter link element not found');
    }
}

function setTwitterLink(url) {
    const twitterLink = document.getElementById('twitterLink');
    if (twitterLink) {
        if (url) {
            twitterLink.href = url;
            twitterLink.textContent = 'Link to Twitter';
        } else {
            twitterLink.href = '#';
            twitterLink.textContent = 'Link Unavailable';
        }
    }
}

function updateFacebookLink(url) {
    const facebookLink = document.getElementById('facebook-link');
    if (facebookLink) {
        console.debug('Facebook link element found, setting href:', url);
        facebookLink.href = url;
        facebookLink.style.display = 'block';
    } else {
        console.debug('Facebook link element not found');
    }
}

function setFacebookLink(url) {
    const facebookLink = document.getElementById('facebookLink');
    if (facebookLink) {
        if (url) {
            facebookLink.href = url;
            facebookLink.textContent = 'Link to Facebook';
        } else {
            facebookLink.href = '#';
            facebookLink.textContent = 'Link Unavailable';
        }
    }
}

function updateInstagramLink(url) {
    const instagramLink = document.getElementById('instagram-link');
    if (instagramLink) {
        console.debug('Instagram link element found, setting href:', url);
        instagramLink.href = url;
        instagramLink.style.display = 'block';
    } else {
        console.debug('Instagram link element not found');
    }
}

function setInstagramLink(url) {
    const instagramLink = document.getElementById('instagramLink');
    if (instagramLink) {
        if (url) {
            instagramLink.href = url;
            instagramLink.textContent = 'Link to Instagram';
        } else {
            instagramLink.href = '#';
            instagramLink.textContent = 'Link Unavailable';
        }
    }
}

let isSubmitting = false;

function submitQuestDetails(event, questId) {
  event.preventDefault();
  if (isSubmitting) return;
  isSubmitting = true;

  const formData = new FormData(event.target);
  formData.append('user_id', CURRENT_USER_ID);
  formData.append('sid', socket.id);

  showLoadingModal();

  fetch(`/quests/quest/${questId}/submit`, {
    method:      'POST',
    body:        formData,
    credentials: 'same-origin',
    headers:     { 'X-CSRF-Token': CSRF_TOKEN }
  })
    .then(res => {
      hideLoadingModal();
      if (!res.ok) {
        if (res.status === 403)
          return res.json().then(d => {
            // special-case message when game is over
            if (
              d.message ===
              'This quest cannot be completed outside of the game dates'
            ) {
              throw new Error(
                'The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu.'
              );
            }
            throw new Error(d.message || `Server responded with status ${res.status}`);
          });
        throw new Error(`Server responded with status ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      if (!data.success) throw new Error(data.message);

      /* --- scoreboard & social links --- */
      if (data.total_points) {
        const el = document.getElementById('total-points');
        if (el) el.innerText = `Total Completed Points: ${data.total_points}`;
      }
      if (data.twitter_url)   updateTwitterLink(data.twitter_url);
      if (data.fb_url)        updateFacebookLink(data.fb_url);
      if (data.instagram_url) updateInstagramLink(data.instagram_url);

      /* Refresh modal with new data and clear the form */
      openQuestDetailModal(questId);
      event.target.reset();
    })
    .catch(err => {
      console.error('Submission error:', err);
      alert(`Error during submission: ${err.message}`);
    })
    .finally(() => {
      isSubmitting = false;
    });
}

/**********************************************************************
 *  2. fetchSubmissions                                               *
 **********************************************************************/
function fetchSubmissions(questId) {
  fetch(`/quests/quest/${questId}/submissions`, {
    method:      'GET',
    credentials: 'same-origin'
  })
    .then(res => {
      if (!res.ok) throw new Error(`Server responded with status ${res.status}`);
      return res.json();
    })
    .then(submissions => {
      /* top three social links in the modal header */
      const twitterLink   = document.getElementById('twitterLink');
      const facebookLink  = document.getElementById('facebookLink');
      const instagramLink = document.getElementById('instagramLink');

      if (submissions && submissions.length) {
        const s              = submissions[0];   // newest submission
        const imgEl          = document.getElementById('submissionImage');
        const commentEl      = document.getElementById('submissionComment');
        const profileLink    = document.getElementById('submitterProfileLink');
        const profileImg     = document.getElementById('submitterProfileImage');
        const profileCaption = document.getElementById('submitterProfileCaption');

        imgEl.src          = s.image_url || '/static/images/default-placeholder.webp';
        commentEl.textContent = s.comment || 'No comment provided.';

        profileLink.href   = `/profile/${s.user_id}`;
        profileImg.src     = s.user_profile_picture || '/static/images/default_profile.png';
        profileCaption.textContent =
          s.user_display_name || s.user_username || `User ${s.user_id}`;

        /* social links visibility */
        const toggle = (el, url) => {
          if (url && url.trim()) {
            el.href = url;
            el.style.display = 'inline';
          } else {
            el.style.display = 'none';
          }
        };
        toggle(twitterLink,   s.twitter_url);
        toggle(facebookLink,  s.fb_url);
        toggle(instagramLink, s.instagram_url);
      } else {
        twitterLink.style.display = facebookLink.style.display =
          instagramLink.style.display = 'none';
      }

      /* build thumbnails for all submissions */
      const gallery = submissions
        .slice()                       // clone
        .reverse()                     // newest first
        .map(sub => ({
          id:                  sub.id,
          url:                 sub.image_url,
          alt:                 'Submission Image',
          comment:             sub.comment,
          user_id:             sub.user_id,
          user_display_name:   sub.user_display_name,
          user_username:       sub.user_username,
          user_profile_picture: sub.user_profile_picture,
          twitter_url:         sub.twitter_url,
          fb_url:              sub.fb_url,
          instagram_url:       sub.instagram_url
        }));

      distributeImages(gallery);
    })
    .catch(err => {
      console.error('Failed to fetch submissions:', err);
      alert('Could not load submissions. Please try again.');
    });
}

function isValidImageUrl(url) {
    if (!url) {
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    try {
        if (url.startsWith("/")) {
            return true;
        }
        const parsedUrl = new URL(url);
        if (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") {
            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
            return allowedExtensions.some(ext => parsedUrl.pathname.toLowerCase().endsWith(ext));
        }
    } catch (e) {
        console.error(`Invalid URL detected: ${url}`);
        return false;
    }
    return false;
}

function distributeImages(images) {
    const board = document.getElementById('submissionBoard');
    board.innerHTML = '';

    const rawFallback =
        document.getElementById('questDetailModal')
                .getAttribute('data-placeholder-url') ||
        '/static/images/default-placeholder.webp';

    const isLocal   = url => url.startsWith('/static/');
    const localPath = url => url.replace(/^\/static\//, '');    // “images/foo.webp”
    const onScreenW = window.innerWidth <= 480 ? 70 : 100;      // how wide it’s DRAWN
    const reqWidth  = onScreenW * (window.devicePixelRatio || 2); // 2× for sharpness

    images.forEach(imgData => {
        const thumb   = document.createElement('img');
        const rawSrc  = isValidImageUrl(imgData.url) ? imgData.url : rawFallback;
        const thumbSrc = isLocal(rawSrc)
            ? `/resize_image?path=${encodeURIComponent(localPath(rawSrc))}&width=${reqWidth}`
            : rawSrc;  // external → use as-is

        thumb.setAttribute('data-src', thumbSrc);   // lazy-load
        thumb.classList.add('lazyload');
        thumb.alt = imgData.alt || 'Submission Image';
        thumb.style.width  = `${onScreenW}px`;       // display size
        thumb.style.height = 'auto';
        thumb.style.marginRight = '10px';

        thumb.onerror = () => {
            if (isLocal(rawFallback)) {
                thumb.src = `/resize_image?path=${encodeURIComponent(localPath(rawFallback))}&width=${reqWidth}`;
            } else {
                thumb.src = rawFallback;
            }
        };

        thumb.onclick = () => showSubmissionDetail(imgData);
        board.appendChild(thumb);
    });

    lazyLoadImages();
}