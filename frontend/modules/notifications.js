import { showUserProfileModal } from './user_profile_modal.js';
import { showSubmissionDetail } from './submission_detail_modal.js';
import logger from '../logger.js';

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
  let page           = 0;
  let totalPages     = 1;
  const perPage      = parseInt(menu.dataset.perPage, 10) || 10;
  let displayedCount = 0;

  // --------------------------------------------------------------
  // 2) Payload renderers dispatch table
  // --------------------------------------------------------------
  const payloadRenderers = {
    follow: ({ from_user_name, from_user_id }) => ({
      text: `Now following ${from_user_name}`,
      onClick: () => showUserProfileModal(from_user_id)
    }),
    followed_by: ({ follower_name, follower_id }) => ({
      text: `${follower_name} is now following you`,
      onClick: () => showUserProfileModal(follower_id)
    }),
    submission: ({ actor_name, quest_name, submission_id }) => ({
      text: `${actor_name} submitted a new “${quest_name}” quest`,
      onClick: async () => {
        const r = await fetch(`/quests/submissions/${submission_id}`);
        const img = await r.json();
        showSubmissionDetail(img);
      }
    }),
    profile_message: ({ from_user_name, content, profile_user_id }) => ({
      text: `${from_user_name} says “${content}”`,
      onClick: () => showUserProfileModal(profile_user_id)
    }),
    profile_reply: ({ from_user_name, content, profile_user_id }) => ({
      text: `${from_user_name} replied “${content}”`,
      onClick: () => showUserProfileModal(profile_user_id)
    }),
    submission_like: ({ liker_name, submission_id }) => ({
      text: `${liker_name} liked your submission`,
      onClick: async () => {
        const r = await fetch(`/quests/submissions/${submission_id}`, { credentials: 'same-origin' });
        const img = await r.json();
        showSubmissionDetail(img);
      }
    }),
    submission_reply: ({ actor_name, content, submission_id }) => ({
      text: `${actor_name} replied “${content}”`,
      onClick: async () => {
        const r = await fetch(`/quests/submissions/${submission_id}`, { credentials: 'same-origin' });
        const img = await r.json();
        showSubmissionDetail(img);
      }
    })
    // Add new types here as needed
  };

  // --------------------------------------------------------------
  // 3) Render a single notification <a> element
  // --------------------------------------------------------------
  function renderNotification(n) {
    const handler = payloadRenderers[n.type];
    let text, onClick;

    if (handler && n.payload) {
      try {
        ({ text, onClick } = handler(n.payload));
      } catch (e) {
        logger.error(`Error in handler for ${n.type}:`, e);
      }
    }

    if (!text || !onClick) {
      text = n.payload.summary || JSON.stringify(n.payload);
      onClick = () => { window.location.href = '/notifications/'; };
    }

    const cls = n.is_read ? '' : 'fw-bold';
    const a = document.createElement('a');
    a.href = '#';
    a.className = `dropdown-item ${cls}`;
    a.innerHTML = `
      ${text}
      <small class="text-muted d-block text-center">
        ${new Date(n.when).toLocaleString()}
      </small>`;
    a.addEventListener('click', async (e) => {
      e.preventDefault();
      try { await onClick(); } catch (err) { logger.error(err); }
    });
    const li = document.createElement('li');
    li.appendChild(a);
    return li;
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
      displayedCount = 0;
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
      logger.error(err);
      return;
    }

    if (!resp.ok) {
      loadingLi.textContent = 'Error loading.';
      logger.error('Status:', resp.status, resp.statusText);
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

    // Append each notification with divider between entries
    data.items.forEach(n => {
      if (displayedCount > 0) {
        const dividerLi = document.createElement('li');
        const hr = document.createElement('hr');
        hr.className = 'dropdown-divider';
        dividerLi.appendChild(hr);
        menu.appendChild(dividerLi);
      }
      menu.appendChild(renderNotification(n));
      displayedCount += 1;
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

