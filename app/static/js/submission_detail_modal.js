document.addEventListener('DOMContentLoaded', () => {

  const $    = s => document.querySelector(s);
  const csrf = () => document.querySelector('meta[name="csrf-token"]').getAttribute('content');

  window.showSubmissionDetail = function(image) {
    const modal = $('#submissionDetailModal');
    modal.dataset.submissionId = image.id;

    const me      = Number(modal.dataset.currentUserId);
    const isOwner = Number(image.user_id) === me;


    // ── NEW: grab your photo-edit controls ──
    const editPhotoBtn      = $('#editPhotoBtn');
    const photoEditControls = $('#photoEditControls');
    const photoInput        = $('#submissionPhotoInput');
    const savePhotoBtn      = $('#savePhotoBtn');
    const cancelPhotoBtn    = $('#cancelPhotoBtn');

    // show/hide the “Change Photo” button
    editPhotoBtn.hidden      = !isOwner;
    photoEditControls.hidden = true;

    // wire the click to reveal the file picker
    editPhotoBtn.addEventListener('click', () => {
      photoEditControls.hidden = false;
      editPhotoBtn.hidden      = true;
    });

    // cancel → hide picker, restore button
    cancelPhotoBtn.addEventListener('click', () => {
      photoInput.value         = '';
      photoEditControls.hidden = true;
      editPhotoBtn.hidden      = false;
    });

    // save → upload to server
    savePhotoBtn.addEventListener('click', () => {
      const id   = modal.dataset.submissionId;
      const file = photoInput.files[0];
      if (!file) return alert('Please select an image first.');
      if (file.type.startsWith('video/') && file.size > 10 * 1024 * 1024) {
        alert('Video must be 10 MB or smaller.');
        return;
      }

      const form = new FormData();
      if (file.type.startsWith('video/')) {
        form.append('video', file);
      } else {
        form.append('photo', file);
      }

      fetch(`/quests/submission/${id}/photo`, {
        method:      'PUT',
        credentials: 'same-origin',
        headers:     { 'X-CSRFToken': csrf() },
        body:        form
      })
      .then(r => r.json())
      .then(json => {
        if (!json.success) throw new Error(json.message || 'Upload failed');
        if (json.video_url) {
          $('#submissionImage').hidden = true;
          $('#submissionVideo').hidden = false;
          $('#submissionVideoSource').src = json.video_url;
          $('#submissionVideo').load();
        } else {
          $('#submissionVideo').hidden = true;
          $('#submissionImage').hidden = false;
          $('#submissionImage').src = json.image_url;
        }
        cancelPhotoBtn.click();
      })
      .catch(e => alert(e.message));
    });

    $('#submissionReplyEdit').hidden = isOwner;
    $('#postReplyBtn').hidden        = isOwner;
    $('#ownerNotice').hidden = !isOwner;

    const repliesSection = $('#submissionRepliesContainer');

    if (isOwner) {
      repliesSection.hidden = true;
    } else {
      repliesSection.hidden = false;
    }

  const el = {
      img                  : $('#submissionImage'),
      video                : $('#submissionVideo'),
      videoSource          : $('#submissionVideoSource'),
      imgOverlay           : $('#submitterProfileImageOverlay'),
      commentRead          : $('#submissionComment'),
      commentEdit          : $('#submissionCommentEdit'),
      readBox              : $('#commentReadButtons'),
      editBox              : $('#commentEditButtons'),
      editBtn              : $('#editCommentBtn'),
      profileImg           : $('#submitterProfileImage'),
      profileImgOverlay    : $('#submitterProfileImageOverlay'),
      profileCap           : $('#submitterProfileCaption'),
      profileLink          : $('#submitterProfileLink'),
      social: {
        tw : $('#twitterLink'),
        fb : $('#facebookLink'),
        ig : $('#instagramLink')
      }
    };

    // set picture & caption
    el.profileImg.src        = image.user_profile_picture || '/static/images/default_profile.png';
    el.profileImgOverlay.src = el.profileImg.src;
    el.profileCap.textContent = image.user_display_name || image.user_username || '—';

    // wire up click on both the inline and overlay image
    el.profileLink.onclick   = e => {
      e.preventDefault();
      showUserProfileModal(image.user_id);
    };
    el.imgOverlay.parentElement.onclick = el.profileLink.onclick;

    // submission image & comment
    if (image.video_url) {
      el.img.hidden = true;
      el.video.hidden = false;
      el.videoSource.src = image.video_url;
      el.video.load();
    } else {
      el.video.hidden = true;
      el.img.hidden   = false;
      el.img.src = image.url;
    }
    el.commentRead.textContent = image.comment || 'No comment provided.';

    // social links
    ['tw','fb','ig'].forEach(k=>{
      const prop = k==='tw'?'twitter_url':k==='fb'?'fb_url':'instagram_url';
      try {
        new URL(image[prop]);
        el.social[k].href = image[prop];
        el.social[k].style.display = 'inline-block';
      } catch {
        el.social[k].style.display = 'none';
      }
    });

    // edit controls
    if (isOwner) {
      el.editBtn.hidden = false;
      el.readBox.hidden = false;
    } else {
      el.editBtn.hidden      =
      el.readBox.hidden      =
      el.commentEdit.hidden  =
      el.editBox.hidden      = true;
    }

    loadSubmissionDetails();
    openModal('submissionDetailModal');
  };

  // comment editing
  $('#editCommentBtn').addEventListener('click', () => {
    $('#submissionCommentEdit').value = $('#submissionComment').textContent.trim();
    toggleEdit(true);
  });

  $('#saveCommentBtn').addEventListener('click', () => {
    const id = $('#submissionDetailModal').dataset.submissionId;
    fetch(`/quests/submission/${id}/comment`, {
      method:      'PUT',
      credentials: 'same-origin',
      headers: {
        'Content-Type':'application/json',
        'X-CSRFToken' : csrf()
      },
      body: JSON.stringify({ comment: $('#submissionCommentEdit').value.trim() })
    })
    .then(r=>{ if(!r.ok) throw new Error(r.status); return r.json() })
    .then(j=>{
      if(!j.success) throw new Error(j.message||'Save failed');
      $('#submissionComment').textContent = j.comment||'No comment provided.';
      toggleEdit(false);
    })
    .catch(e=>alert(`Could not save comment: ${e.message}`));
  });

  $('#cancelCommentBtn').addEventListener('click', () => toggleEdit(false));
  function toggleEdit(on){
    $('#submissionComment').hidden      = on;
    $('#commentReadButtons').hidden     = on;
    $('#submissionCommentEdit').hidden  = !on;
    $('#commentEditButtons').hidden     = !on;
  }


  // load like + replies
  function loadSubmissionDetails(){
    const id = $('#submissionDetailModal').dataset.submissionId;
    if(!id) return;

    fetch(`/quests/submissions/${id}`, { credentials:'same-origin' })
      .then(r=>r.json())
      .then(d=>{
        $('#submissionLikeCount').textContent = d.like_count||0;
        $('#submissionLikeBtn').classList.toggle('active', d.liked_by_current_user);
      });

      fetch(`/quests/submission/${id}/replies`, { credentials:'same-origin' })
        .then(r=>r.json())
        .then(d=>{
          const list = $('#submissionRepliesList');
          list.innerHTML = '';
        d.replies.forEach(rep => {
          const div = document.createElement('div');
          div.className = 'reply mb-1';

          // Render the reply author as a clickable link
          div.innerHTML = `
            <a href="#" class="reply-user-link" data-user-id="${rep.user_id}">
              <strong>${rep.user_display}</strong>
            </a>: ${rep.content}
          `;

          // Wire up profile-opening
          const userLink = div.querySelector('.reply-user-link');
          userLink.addEventListener('click', e => {
            e.preventDefault();
            showUserProfileModal(rep.user_id);
          });

          list.appendChild(div);
        });

        const textarea = $('#submissionReplyEdit');
        const btn = $('#postReplyBtn');
        const existingMessage = $('#replyLimitMessage');
        if (d.replies.length >= 10) {
          textarea.disabled = true;
          btn.disabled = true;
          if (!existingMessage) {
            const msg = document.createElement('div');
            msg.id = 'replyLimitMessage';
            msg.className = 'text-muted mt-2';
            msg.textContent = 'Maximum replies reached, sorry.';
            textarea.parentNode.insertBefore(msg, textarea);
          }
        } else {
          textarea.disabled = false;
          btn.disabled = false;
          if (existingMessage) existingMessage.remove();
        }
      });
  }


  // like/unlike
  $('#submissionLikeBtn').addEventListener('click', () => {
    const btn   = $('#submissionLikeBtn');
    const id    = $('#submissionDetailModal').dataset.submissionId;
    const liked = btn.classList.contains('active');

    fetch(`/quests/submission/${id}/like`, {
      method:     liked? 'DELETE' : 'POST',
      credentials:'same-origin',
      headers: {
        'Content-Type':'application/json',
        'X-CSRFToken' : csrf()
      }
    })
    .then(r=>{ if(!r.ok) throw new Error(r.status); return r.json() })
    .then(j=>{
      if(!j.success) throw new Error('Like failed');
      $('#submissionLikeCount').textContent = j.like_count;
      btn.classList.toggle('active', j.liked);
    })
    .catch(e=>alert(e.message));
  });

  // post a reply
  $('#postReplyBtn').addEventListener('click', () => {
    const id      = $('#submissionDetailModal').dataset.submissionId;
    const textarea= $('#submissionReplyEdit');
    const btn     = $('#postReplyBtn');
    const content = textarea.value.trim();
    if(!id||!content) return;

    fetch(`/quests/submission/${id}/replies`, {
      method:      'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type':'application/json',
        'X-CSRFToken' : csrf()
      },
      body: JSON.stringify({ content })
    })
    .then(r => r.json().then(j => ({ ok: r.ok, status: r.status, body: j })))
    .then(({ ok, status, body }) => {
      if (!body.success) {
        // if it’s the “limit reached” response, disable the form and show the message
        if (body.message === 'Reply limit of 10 reached') {
          disableReplyForm();
          return;
        }
        // otherwise it might be a duplicate reply
        if (status === 409 && body.message === 'Duplicate reply') {
          return alert('You have already posted that exact reply.');
        }
        throw new Error(body.message || 'Error');
      }

      // success → inject the new reply
      const list = $('#submissionRepliesList');
      const div = document.createElement('div');
      div.className = 'reply mb-1';
      div.innerHTML = `<strong>${body.reply.user_display}</strong>: ${body.reply.content}`;
      list.insertBefore(div, list.firstChild);

      textarea.value = '';

      // if we’ve just hit 10, disable and show the limit message
      if (list.children.length >= 10) {
        disableReplyForm();
      }
    })
    .catch(e => alert(e.message));
  });

  // helper to hide the form & show a “max replies” notice
  function disableReplyForm() {
    const textarea = $('#submissionReplyEdit');
    const btn      = $('#postReplyBtn');
    textarea.disabled = true;
    btn.disabled      = true;
    if (!$('#replyLimitMessage')) {
      const msg = document.createElement('div');
      msg.id = 'replyLimitMessage';
      msg.className = 'text-muted mt-2';
      msg.textContent = 'Maximum replies reached, sorry.';
      textarea.parentNode.insertBefore(msg, textarea);
    }
  }
});
