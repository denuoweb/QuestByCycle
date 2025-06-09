import { initQuill } from './quill_common.js';

document.addEventListener('DOMContentLoaded', () => {
  // Only initialise the editors when the elements exist on the page.
  const descriptionEl = document.querySelector('#description-editor');
  const tipsEl        = document.querySelector('#tips-editor');

  const quillDescription = (descriptionEl && window.Quill) ? initQuill(descriptionEl) : null;
  const quillTips        = (tipsEl && window.Quill) ? initQuill(tipsEl) : null;
  if ((!window.Quill) && (descriptionEl || tipsEl)) {
    console.error('Quill library not found  quest editor will not work.');
  }

  const questForm = document.getElementById('quest-form');
  if (questForm && quillDescription && quillTips) {
    questForm.addEventListener('submit', e => {
      const descriptionContent = quillDescription.root.innerHTML.trim();
      const tipsContent        = quillTips.root.innerHTML.trim();

      if (!descriptionContent || descriptionContent === '<p><br></p>') {
        alert('Description is required.');
        e.preventDefault();
        return false;
      }

      document.getElementById('description').value = descriptionContent;
      document.getElementById('tips').value        = tipsContent;
    });
  }
});

