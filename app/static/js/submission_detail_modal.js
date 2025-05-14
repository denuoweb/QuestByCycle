document.addEventListener('DOMContentLoaded', () => {

  /* helpers ---------------------------------------------------------------- */
  const $     = s => document.querySelector(s);
  const csrf  = () => (document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/) ?? [])[1] || '';

  /* public entry ----------------------------------------------------------- */
  window.showSubmissionDetail = function (image) {

    const modal = $('#submissionDetailModal');
    const idNow = Number(modal.dataset.currentUserId);        // owner id from DOM
    const isOwner = Number(image.user_id) === idNow;

    /* get every element fresh each open ----------------------------------- */
    const el = {
      img          : $('#submissionImage'),
      commentRead  : $('#submissionComment'),
      commentEdit  : $('#submissionCommentEdit'),
      readBox      : $('#commentReadButtons'),
      editBox      : $('#commentEditButtons'),
      editBtn      : $('#editCommentBtn'),
      profileImg   : $('#submitterProfileImage'),
      profileCap   : $('#submitterProfileCaption'),
      profileLink  : $('#submitterProfileLink'),
      social : {
        tw : $('#twitterLink'),
        fb : $('#facebookLink'),
        ig : $('#instagramLink')
      }
    };

    /* populate fixed fields ------------------------------------------------ */
    el.img.src = image.url;
    el.commentRead.textContent = image.comment || 'No comment provided.';

    el.profileImg.src = image.user_profile_picture || '/static/images/default_profile.png';
    el.profileCap.textContent = image.user_display_name || image.user_username || '—';
    el.profileLink.onclick = e => { e.preventDefault(); showUserProfileModal(image.user_id); };

    link(el.social.tw, image.twitter_url);
    link(el.social.fb, image.fb_url);
    link(el.social.ig, image.instagram_url);

    /* owner controls ------------------------------------------------------- */
    if (isOwner) {
      el.editBtn.hidden = false;
      el.readBox.hidden = false;
      modal.dataset.submissionId = image.id;
    } else {
      el.editBtn.hidden  =
      el.readBox.hidden  =
      el.commentEdit.hidden =
      el.editBox.hidden  = true;
      delete modal.dataset.submissionId;
    }

    /* show modal ----------------------------------------------------------- */
    openModal('submissionDetailModal');
  };

  /* static wiring of buttons ---------------------------------------------- */
  $('#editCommentBtn').addEventListener('click', () => {
    $('#submissionCommentEdit').value = $('#submissionComment').textContent.trim();
    toggleEdit(true);
  });

  $('#saveCommentBtn').addEventListener('click', () => {
    const modal = $('#submissionDetailModal');
    const submissionId = modal.dataset.submissionId;
    if (!submissionId) return;

    fetch(`/quests/submission/${submissionId}/comment`, {
      method      : 'PUT',
      credentials : 'same-origin',
      headers     : { 'Content-Type':'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
      body        : JSON.stringify({ comment: $('#submissionCommentEdit').value.trim() })
    })
    .then(r => r.json().then(j => ({ok:r.ok, j})))
    .then(({ok,j}) => {
      if (!ok || !j.success) throw new Error(j.message || 'Save failed');
      $('#submissionComment').textContent = j.comment || 'No comment provided.';
      toggleEdit(false);
    })
    .catch(e => alert(`Could not save comment: ${e.message}`));
  });

  $('#cancelCommentBtn').addEventListener('click', () => toggleEdit(false));

  /* helpers ---------------------------------------------------------------- */
  function toggleEdit(on) {
    $('#submissionComment').hidden      = on;
    $('#commentReadButtons').hidden     = on;
    $('#submissionCommentEdit').hidden  = !on;
    $('#commentEditButtons').hidden     = !on;
  }

  function link(anchor, url) {
    try {
      new URL(url);
      anchor.href = url;
      anchor.style.display = 'inline-block';
    } catch { anchor.style.display = 'none'; }
  }

});
