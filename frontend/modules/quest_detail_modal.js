import { openModal } from './modal_common.js';
import { showLoadingModal, hideLoadingModal } from './loading_modal.js';
import { resetModalContent } from './modal_common.js';
import { getCSRFToken, csrfFetchJson, fetchJson } from '../utils.js';
import { showSubmissionDetail } from './submission_detail_modal.js';
import logger from '../logger.js';

/* ------------------------------------------------------------------ */
/*  HELPER: read meta-content                                         */
/* ------------------------------------------------------------------ */
function meta(name) {
  const tag = document.querySelector(`meta[name="${name}"]`);
  return tag ? tag.content : '';
}

/*  Current user ID and CSRF token pulled from <meta> tags.           */
const CURRENT_USER_ID = Number(meta('current-user-id') || 0);
const CSRF_TOKEN = getCSRFToken();
const PLACEHOLDER_IMAGE = document
  .querySelector('meta[name="placeholder-image"]')
  .getAttribute('content');

/* ------------------------------------------------------------------ */
/*  OPEN QUEST DETAIL MODAL                                           */
/* ------------------------------------------------------------------ */
export function openQuestDetailModal(questId) {
  resetModalContent();

  fetchJson(`/quests/detail/${encodeURIComponent(questId)}/user_completion`)
    .then(({ json: data }) => {
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
        logger.error('populateQuestDetails – required element missing');
        return;
      }

      ensureDynamicElementsExistAndPopulate(
        quest,
        userCompletion.completions,
        nextEligibleTime,
        canVerify
      );

      openModal('questDetailModal');
      lazyLoadImages();
      fetchQuestSubmissions(questId);
    })
    .catch(err => {
      logger.error('Error opening quest detail modal:', err);
      alert('Sign in to view quest details.');
    });
}

export function refreshQuestDetailModal(questId) {
  fetchJson(`/quests/detail/${encodeURIComponent(questId)}/user_completion`)
    .then(({ json: data }) => {
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
        logger.error('populateQuestDetails - required element missing');
        return;
      }

      ensureDynamicElementsExistAndPopulate(
        quest,
        userCompletion.completions,
        nextEligibleTime,
        canVerify
      );

      lazyLoadImages();
      fetchQuestSubmissions(questId);
    })
  .catch(err => {
      logger.error('Failed to refresh quest detail modal:', err);
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
    const completeText = userCompletionCount >= quest.completion_limit ? ' - complete' : '';
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
            logger.error(`Error: Missing element ${key}`);
            return false;
        }
    }

    const cards = {
        badge: elements['modalQuestBadgeImage']?.closest('.quest-detail-item'),
        badgeAwarded: elements['modalQuestBadgeAwarded']?.closest('.quest-detail-item'),
        category: elements['modalQuestCategory']?.closest('.quest-detail-item')
    };

    for (let key in cards) {
        if (!cards[key]) {
            logger.error(`Error: Missing card element ${key}`);
            return false;
        }
    }

    elements['modalQuestTitle'].innerText = `${quest.title}${completeText}`;
    elements['modalQuestDescription'].textContent = quest.description;
    elements['modalQuestTips'].textContent = quest.tips || 'No tips available';
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
            elements['modalQuestVerificationType'].innerText = 'Must upload a photo to earn points! Comment optional.';
            break;
        case 'photo':
            elements['modalQuestVerificationType'].innerText = 'Must upload a photo to earn points!';
            break;
        case 'comment':
            elements['modalQuestVerificationType'].innerText = 'Must upload a comment to earn points!';
            break;
        case 'qr_code':
            elements['modalQuestVerificationType'].innerText = 'Find the QR code and post a photo to earn points!';
            break;
        default:
            elements['modalQuestVerificationType'].innerText = 'Not specified';
            break;
    }

    const badgeImagePath = quest.badge && quest.badge.image ? `/static/images/badge_images/${quest.badge.image}` : PLACEHOLDER_IMAGE;
    elements['modalQuestBadgeImage'].setAttribute('data-src', badgeImagePath);
    elements['modalQuestBadgeImage'].src = PLACEHOLDER_IMAGE;
    elements['modalQuestBadgeImage'].classList.add('lazyload');
    elements['modalQuestBadgeImage'].alt = quest.badge && quest.badge.name ? `Badge: ${quest.badge.name}` : 'Default Badge';

    if (quest.badge_option === 'none') {
        cards.badge.classList.add('hidden');
        cards.badgeAwarded.classList.add('hidden');
        cards.category.classList.add('hidden');
    } else {
        cards.badge.classList.remove('hidden');
        cards.badgeAwarded.classList.remove('hidden');
        cards.category.classList.remove('hidden');
    }

    elements['modalQuestCompletions'].innerText = `Total Completions: ${userCompletionCount}`;

    const nextAvailableTime = nextEligibleTime && new Date(nextEligibleTime);
    if (!canVerify && nextAvailableTime && nextAvailableTime > new Date()) {
        elements['modalCountdown'].innerText = `Next eligible time: ${nextAvailableTime.toLocaleString()}`;
        elements['modalCountdown'].style.color = 'red';
    } else {
        elements['modalCountdown'].innerText = 'You are currently eligible to verify!';
        elements['modalCountdown'].style.color = 'green';
    }

    manageVerificationSection(questId, canVerify, quest.verification_type);
    return true;
}

function ensureDynamicElementsExistAndPopulate(quest, userCompletionCount, nextEligibleTime, canVerify) {
    const parentElement = document.querySelector('.user-quest-data');
    if (!parentElement) {
        logger.error('Parent element .user-quest-data not found');
        return;
    }

    const dynamicElements = [
        { id: 'modalQuestCompletions', value: `${userCompletionCount || 0}` },
        { id: 'modalCountdown', value: '' }
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
            countdownElement.innerText = 'You are currently eligible to verify!';
        }
    } else {
        countdownElement.innerText = 'You are currently eligible to verify!';
    }
}

function formatTimeDiff(ms) {
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / (1000 * 60)) % 60);
    const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
const days = Math.floor(ms / (1000 * 60 * 60 * 24));
    return `${days}d ${hours}h ${minutes}m ${seconds}s`;
}


function manageVerificationSection(questId, canVerify, verificationType) {
    const userQuestData = document.querySelector('.user-quest-data');
    if (!userQuestData) {
        logger.error('Parent element .user-quest-data not found');
        return;
    }
    userQuestData.innerHTML = '';

    if (canVerify) {
        const verifyForm = document.createElement('div');
        verifyForm.id = `verifyQuestForm-${questId}`;
        verifyForm.className = 'verify-quest-form';
        verifyForm.style.display = 'block';

        const formElement = getVerificationFormElement(
          verificationType.trim().toLowerCase(),
          questId
        );
        verifyForm.appendChild(formElement);
        userQuestData.appendChild(verifyForm);

        setupSubmissionForm(questId);
    } else {
        const message = document.createElement('p');
        message.className = 'epic-message text-success';
        message.textContent = 'Thanks for completing the quest.';
        userQuestData.appendChild(message);
    }
}

function getVerificationFormElement(verificationType, questId) {
    const form = document.createElement('form');
    form.enctype = 'multipart/form-data';
    form.className = 'epic-form';
    form.method = 'post';
    form.action = `/quests/quest/${encodeURIComponent(questId)}/submit`;

    const csrf = document.createElement('input');
    csrf.type = 'hidden';
    csrf.name = 'csrf_token';
    csrf.value = CSRF_TOKEN;
    form.appendChild(csrf);

    const heading = document.createElement('h2');
    heading.style.textAlign = 'center';
    heading.textContent = 'Verify Your Quest';
    form.appendChild(heading);

    switch (verificationType) {
        case 'photo':
            form.appendChild(createFileInput('image', 'Upload a Photo', 'image/*', true));
            form.appendChild(createSubmitButton());
            break;
        case 'comment':
            form.appendChild(
                createTextarea('verificationComment', 'Enter a Comment', 'Enter a comment...', true)
            );
            form.appendChild(createSubmitButton());
            break;
        case 'photo_comment':
            form.appendChild(createFileInput('image', 'Upload a Photo', 'image/*', true));
            form.appendChild(
                createTextarea('verificationComment', 'Enter a Comment (optional)', 'Enter a comment...', false)
            );
            form.appendChild(createSubmitButton());
            break;
        case 'video':
            form.appendChild(createFileInput('video', 'Upload a Video', 'video/*', true));
            form.appendChild(
                createTextarea(
                    'verificationComment',
                    'Add a Comment (optional)',
                    'Enter an optional comment...',
                    false
                )
            );
            form.appendChild(createSubmitButton());
            break;
        case 'qr_code': {
            const p = document.createElement('p');
            p.className = 'epic-message';
            p.textContent = 'Find and scan the QR code. No submission required here.';
            form.appendChild(p);
            break;
        }
        case 'pause': {
            const p = document.createElement('p');
            p.className = 'epic-message';
            p.textContent = 'Quest is currently paused.';
            form.appendChild(p);
            break;
        }
        default: {
            const p = document.createElement('p');
            p.className = 'epic-message';
            p.textContent = 'Submission requirements are not set correctly.';
            form.appendChild(p);
        }
    }

    return form;
}

function createFileInput(id, labelText, accept, required) {
    const wrapper = document.createElement('div');
    wrapper.className = 'form-group';

    const label = document.createElement('label');
    label.htmlFor = id;
    label.className = 'epic-label';
    label.textContent = labelText;
    wrapper.appendChild(label);

    const input = document.createElement('input');
    input.type = 'file';
    input.id = id;
    input.name = id;
    input.className = 'epic-input';
    input.accept = accept;
    if (required) input.required = true;
    wrapper.appendChild(input);

    return wrapper;
}

function createTextarea(id, labelText, placeholder, required) {
    const wrapper = document.createElement('div');
    wrapper.className = 'form-group';

    const label = document.createElement('label');
    label.htmlFor = id;
    label.className = 'epic-label';
    label.textContent = labelText;
    wrapper.appendChild(label);

    const textarea = document.createElement('textarea');
    textarea.id = id;
    textarea.name = id;
    textarea.className = 'epic-textarea';
    textarea.placeholder = placeholder;
    if (required) textarea.required = true;
    wrapper.appendChild(textarea);

    return wrapper;
}

function createSubmitButton() {
    const wrapper = document.createElement('div');
    wrapper.className = 'form-group';

    const button = document.createElement('button');
    button.type = 'submit';
    button.textContent = 'Submit Verification';
    wrapper.appendChild(button);

    return wrapper;
}



function setupSubmissionForm(questId) {
    const container = document.getElementById(`verifyQuestForm-${questId}`);
    if (!container) {
        logger.error('Form container not found for quest ID:', questId);
        return;
    }

    const form = container.querySelector('form');
    if (!form) {
        logger.error('Form element missing for quest ID:', questId);
        return;
    }

    form.addEventListener('submit', function(event) {
        submitQuestDetails(event, questId);
    });
}

function toggleLink(el, url) {
    if (!el) return;
    if (url && url.trim()) {
        el.href = url;
        el.style.display = 'inline';
    } else {
        el.style.display = 'none';
    }
}

function updateScoreboard(totalPoints) {
    if (typeof totalPoints !== 'number') return;
    const container = document.getElementById('total-points');
    if (!container) return;
    const span = container.querySelector('.points-emphasized');
    if (span) {
        span.textContent = totalPoints;
    } else {
        container.textContent = `Your Carbon Reduction Points: ${totalPoints}`;
    }
}

function updateQuestRowCounts(questId, personalCount, totalCount) {
    const row = document.querySelector(`#questTableBody tr[data-quest-id="${questId}"]`);
    if (!row) return;
    const cells = row.querySelectorAll('.quest-stats-cell');
    if (cells.length >= 2) {
        cells[0].innerText = personalCount;
        cells[1].innerText = totalCount;
    }
}

function updateSocialLinks(data) {
    toggleLink(document.getElementById('twitterLink'), data.twitter_url);
    toggleLink(document.getElementById('facebookLink'), data.fb_url);
    toggleLink(document.getElementById('instagramLink'), data.instagram_url);
}

let isSubmitting = false;

async function submitQuestDetails(event, questId) {
  event.preventDefault();
  if (isSubmitting) return;
  isSubmitting = true;
  const submitBtn = event.target.querySelector('[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;

  try {
    showLoadingModal('Uploading...');
    const fileInput = event.target.querySelector('input[type="file"]');
    const file      = fileInput ? fileInput.files[0] : null;
    if (file && file.type.startsWith('video/') && file.size > 25 * 1024 * 1024) {
      alert('Video must be 25 MB or smaller.');
      return;
    }
    if (file && file.type.startsWith('image/') && file.size > 8 * 1024 * 1024) {
      alert('Image must be 8 MB or smaller.');
      return;
    }
    // Enforce 10s max duration for videos on the client side
    if (file && file.type.startsWith('video/')) {
      try {
        const duration = await getVideoDuration(file);
        if (isFinite(duration) && duration > 10.0) {
          alert('Video must be 10 seconds or shorter.');
          return;
        }
      } catch (e) {
        alert('Unable to read video metadata. Please try another file.');
        return;
      }
    }

    const formData = new FormData(event.target);
    formData.append('user_id', CURRENT_USER_ID);

    const { status, json: data } = await csrfFetchJson(`/quests/quest/${encodeURIComponent(questId)}/submit`, {
      method: 'POST',
      body: formData
    });

    if (status !== 200) {
      if (status === 403 && data.message === 'This quest cannot be completed outside of the game dates') {
        throw new Error('The game has ended and you can no longer submit quests. Join a new game in the game dropdown menu.');
      }
      throw new Error(data.message || `Server responded with status ${status}`);
    }

    if (!data.success) throw new Error(data.message);
    if (!data.success) throw new Error(data.message);

    updateScoreboard(data.total_points);
    updateSocialLinks(data);
    updateQuestRowCounts(questId, data.new_completion_count, data.total_completion_count);

    refreshQuestDetailModal(questId);
    event.target.reset();
  } catch (err) {
    logger.error('Submission error:', err);
    alert(`Error during submission: ${err.message}`);
  } finally {
    isSubmitting = false;
    if (submitBtn) submitBtn.disabled = false;
    hideLoadingModal();
  }
}

// helper: read duration from a local File via a temporary <video>
function getVideoDuration(file) {
  return new Promise((resolve, reject) => {
    try {
      const url = URL.createObjectURL(file);
      const v = document.createElement('video');
      v.preload = 'metadata';
      v.onloadedmetadata = () => {
        URL.revokeObjectURL(url);
        resolve(v.duration || 0);
      };
      v.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('metadata error'));
      };
      v.src = url;
    } catch (err) {
      reject(err);
    }
  });
}

/**********************************************************************
 *  2. fetchQuestSubmissions                                          *
 **********************************************************************/
async function fetchQuestSubmissions(questId) {
  const safeQuestId = encodeURIComponent(questId);
  try {
    const { json: submissions } = await fetchJson(`/quests/quest/${safeQuestId}/submissions`);

    const twitterLink   = document.getElementById('twitterLink');
    const facebookLink  = document.getElementById('facebookLink');
    const instagramLink = document.getElementById('instagramLink');

    if (submissions && submissions.length) {
      const s              = submissions[0];   // newest submission
      const imgEl          = document.getElementById('submissionImage');
      const vidEl          = document.getElementById('submissionVideo');
      const vidSrc         = document.getElementById('submissionVideoSource');
      const commentEl      = document.getElementById('submissionComment');
      const profileLink    = document.getElementById('submitterProfileLink');
      const profileImg     = document.getElementById('submitterProfileImage');
      const profileCaption = document.getElementById('submitterProfileCaption');

      if (s.video_url) {
        imgEl.hidden = true;
        vidEl.hidden = false;
        vidSrc.src   = s.video_url;
        vidEl.load();
      } else {
        vidEl.hidden = true;
        imgEl.hidden = false;
        imgEl.src    = s.image_url || PLACEHOLDER_IMAGE;
      }
      commentEl.textContent = s.comment || 'No comment provided.';

      if (profileLink && profileLink.tagName === 'A' && CURRENT_USER_ID) {
        profileLink.href = `/profile/${encodeURIComponent(s.user_id)}`;
      } else if (profileLink) {
        profileLink.removeAttribute('href');
      }
      profileImg.src     = s.user_profile_picture || PLACEHOLDER_IMAGE;
      profileCaption.textContent =
        s.user_display_name || s.user_username || `User ${s.user_id}`;

      updateSocialLinks(s);
    } else {
      [twitterLink, facebookLink, instagramLink].forEach(el => {
        if (el) el.style.display = 'none';
      });
    }

    const gallery = submissions
      .slice()                       // clone
      .reverse()                     // newest first
      .map(sub => ({
        id:                  sub.id,
        url:                 sub.image_url || (sub.video_url ? null : PLACEHOLDER_IMAGE),
        video_url:           sub.video_url,
        alt:                 'Submission Image',
        comment:             sub.comment,
        user_id:             sub.user_id,
        user_display_name:   sub.user_display_name,
        user_username:       sub.user_username,
        user_profile_picture: sub.user_profile_picture,
        twitter_url:         sub.twitter_url,
        fb_url:              sub.fb_url,
        instagram_url:       sub.instagram_url,
        quest_id:            questId
      }));

    distributeImages(gallery);
  } catch (err) {
    logger.error('Failed to fetch submissions:', err);
    alert('Could not load submissions. Please try again.');
  }
}

function isValidImageUrl(url) {
    if (!url) {
        logger.error(`Invalid URL detected: ${url}`);
        return false;
    }
    try {
        if (url.startsWith('/')) {
            return true;
        }
        const parsedUrl = new URL(url);
        if (parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:') {
            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
            return allowedExtensions.some(ext => parsedUrl.pathname.toLowerCase().endsWith(ext));
        }
    } catch {
        logger.error(`Invalid URL detected: ${url}`);
        return false;
    }
    return false;
}

function distributeImages(images) {
    const board = document.getElementById('submissionBoard');
    if (!board) {
        logger.error('submissionBoard element not found');
        return;
    }
    board.innerHTML = '';

    const rawFallbackRaw =
        document.getElementById('questDetailModal')?.getAttribute('data-placeholder-url') ||
        PLACEHOLDER_IMAGE;
    const rawFallback = isValidImageUrl(rawFallbackRaw) ? rawFallbackRaw : PLACEHOLDER_IMAGE;

    const isLocal   = url => url.startsWith('/static/');
    const localPath = url => url.replace(/^\/static\//, '');    // “images/foo.webp”
    const onScreenW = window.innerWidth <= 480 ? 70 : 100;      // how wide it's DRAWN
    const reqWidth  = Math.round(onScreenW * (window.devicePixelRatio || 2)); // 2× for sharpness

    images.forEach(imgData => {
        let thumb;
        if (imgData.video_url) {
            thumb = document.createElement('video');
            thumb.src = imgData.video_url;
            thumb.preload = 'metadata';
            thumb.muted = true;
            thumb.playsInline = true;
            thumb.style.objectFit = 'cover';
        } else {
            thumb = document.createElement('img');
            const rawSrc = isValidImageUrl(imgData.url) ? imgData.url : rawFallback;
            const thumbSrc = isLocal(rawSrc)
                ? `/resize_image?path=${encodeURIComponent(localPath(rawSrc))}&width=${reqWidth}`
                : rawSrc;
            thumb.src = PLACEHOLDER_IMAGE;
            thumb.setAttribute('data-src', thumbSrc);
            thumb.classList.add('lazyload');
            thumb.alt = imgData.alt || 'Submission Image';
        }

        thumb.style.width = `${onScreenW}px`;
        thumb.style.height = 'auto';
        thumb.style.marginRight = '10px';

        if (imgData.video_url) {
            // no lazy load for videos
        } else {
            thumb.onerror = () => {
                if (isLocal(rawFallback)) {
                    thumb.src = `/resize_image?path=${encodeURIComponent(localPath(rawFallback))}&width=${reqWidth}`;
                } else {
                    thumb.src = encodeURI(rawFallback);
                }
            };
        }

        thumb.onclick = () => showSubmissionDetail(imgData);
        board.appendChild(thumb);
    });

    lazyLoadImages();
}

function toggleContent(element) {
    const contents = element.querySelectorAll('span, img');
    contents.forEach(content => {
        content.classList.toggle('hidden');
    });
}


// Event delegation for quest detail triggers and toggles
document.addEventListener('click', (e) => {
    const questEl = e.target.closest('[data-quest-detail]');
    if (questEl) {
        e.preventDefault();
        openQuestDetailModal(questEl.getAttribute('data-quest-detail'));
        return;
    }

    const toggleEl = e.target.closest('[data-toggle-content]');
    if (toggleEl && toggleEl.closest('#questDetailModal')) {
        e.preventDefault();
        toggleContent(toggleEl);
    }
});
