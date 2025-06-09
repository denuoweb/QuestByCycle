document.addEventListener('DOMContentLoaded', () => {
  // --------------------------------------------------------------
  // 0) Ensure the notifications menu exists on this page
  // --------------------------------------------------------------
  const menu = document.getElementById('notifMenu');
  if (!menu) {
    // No notifications menu on this page → nothing to do
    return;
  }

  // --------------------------------------------------------------
  // 1) Cache DOM references
  // --------------------------------------------------------------
  const notifBellToggle = document.getElementById('notifBellToggle');
  const loadingLi       = menu.querySelector('#notifLoading');
  const footerLi        = menu.querySelector('li.dropdown-footer');
  const loadMoreBtn     = footerLi.querySelector('#loadMoreBtn');

  // API endpoint URL for fetching notifications
  const apiUrl = menu.dataset.url;

  // Pagination state
  let page       = 0;
  let totalPages = 1;
  const perPage  = parseInt(menu.dataset.perPage, 10) || 10;

  // --------------------------------------------------------------
  // 2) Payload renderers dispatch table
  // --------------------------------------------------------------
  const payloadRenderers = {
    follow: ({ from_user_name, from_user_id }) => ({
      text: `Now following ${from_user_name}`,
      onclick: `showUserProfileModal(${from_user_id}); return false;`
    }),
    followed_by: ({ follower_name, follower_id }) => ({
      text: `${follower_name} is now following you`,
      onclick: `showUserProfileModal(${follower_id}); return false;`
    }),
    submission: ({ actor_name, quest_name, submission_id }) => ({
      text: `${actor_name} submitted a new “${quest_name}” quest`,
      onclick: `fetch('/quests/submissions/${submission_id}')` +
               `.then(r => r.json()).then(img => showSubmissionDetail(img)); return false;`
    }),
    profile_message: ({ from_user_name, content, profile_user_id }) => ({
      text: `${from_user_name} says “${content}”`,
      onclick: `showUserProfileModal(${profile_user_id}); return false;`
    }),
    profile_reply: ({ from_user_name, content, profile_user_id }) => ({
      text: `${from_user_name} replied “${content}”`,
      onclick: `showUserProfileModal(${profile_user_id}); return false;`
    }),
    submission_like: ({ liker_name, submission_id }) => ({
      text: `${liker_name} liked your submission`,
      onclick: `fetch('/quests/submissions/${submission_id}', { credentials: 'same-origin' })` +
               `.then(r => r.json()).then(img => showSubmissionDetail(img)); return false;`
    }),
    submission_reply: ({ actor_name, content, submission_id }) => ({
      text: `${actor_name} replied “${content}”`,
      onclick: `fetch('/quests/submissions/${submission_id}', { credentials: 'same-origin' })` +
               `.then(r => r.json()).then(img => showSubmissionDetail(img)); return false;`
    })
    // Add new types here as needed
  };

  // --------------------------------------------------------------
  // 3) Render a single notification <a> element
  // --------------------------------------------------------------
  function renderNotification(n) {
    const handler = payloadRenderers[n.type];
    let text, onclick;

    if (handler && n.payload) {
      try {
        ({ text, onclick } = handler(n.payload));
      } catch (e) {
        console.error(`Error in handler for ${n.type}:`, e);
      }
    }

    // Fallback if no handler or error
    if (!text || !onclick) {
      text = n.payload.summary || JSON.stringify(n.payload);
      onclick = "location.href='/notifications/';";
    }

    const cls = n.is_read ? '' : 'fw-bold';
    return `
      <a href="#" class="dropdown-item ${cls}" onclick="${onclick}">
        ${text}
        <small class="text-muted d-block text-center">
          ${new Date(n.when).toLocaleString()}
        </small>
      </a>
    `;
  }

  // --------------------------------------------------------------
  // 4) Safely remove a node if present
  // --------------------------------------------------------------
  function safeRemove(node) {
    if (node && node.parentNode === menu) {
      menu.removeChild(node);
    }
  }

  // --------------------------------------------------------------
  // 5) Fetch, paginate, and render notifications
  // --------------------------------------------------------------
  async function fetchPage(p) {
    // On first page, clear existing items (preserve loader/footer)
    if (p === 1) {
      Array.from(menu.children).forEach(child => {
        if (child !== loadingLi && child !== footerLi) {
          menu.removeChild(child);
        }
      });
      page = 0;
    }

    // Ensure loader and footer at bottom
    safeRemove(loadingLi);
    safeRemove(footerLi);
    menu.appendChild(loadingLi);
    menu.appendChild(footerLi);

    // Show loader
    loadingLi.style.display  = '';
    loadMoreBtn.disabled     = true;

    let resp;
    try {
      resp = await fetch(
        `${apiUrl}?page=${p}&per_page=${perPage}`,
        { credentials: 'include' }
      );
    } catch (err) {
      loadingLi.textContent = 'Network error.';
      console.error(err);
      return;
    }

    if (!resp.ok) {
      loadingLi.textContent = 'Error loading.';
      console.error('Status:', resp.status, resp.statusText);
      return;
    }

    const data = await resp.json();
    page       = data.page;
    totalPages = data.total_pages;

    // Remove loader/footer before rendering
    safeRemove(loadingLi);
    safeRemove(footerLi);

    // Remove unread badge on first load
    const badge = notifBellToggle.querySelector('.badge');
    if (badge) badge.remove();

    // Append each notification
    data.items.forEach(n => {
      menu.insertAdjacentHTML('beforeend', renderNotification(n));
    });

    // Re-add loader/footer
    menu.appendChild(loadingLi);
    menu.appendChild(footerLi);

    // Hide loader, update button
    loadingLi.style.display  = 'none';
    loadMoreBtn.disabled     = (page >= totalPages);
  }

  // --------------------------------------------------------------
  // 6) Event listeners: open dropdown & load more
  // --------------------------------------------------------------
  notifBellToggle.addEventListener('show.bs.dropdown', () => {
    if (page === 0) fetchPage(1);
  });

  loadMoreBtn.addEventListener('click', (event) => {
    // Prevent button from closing the dropdown
    event.preventDefault();
    event.stopPropagation();
    if (page < totalPages) fetchPage(page + 1);
  });
});

export {};
