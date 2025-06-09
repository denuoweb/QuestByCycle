import { initQuill } from './quill_common.js';
const quillDescription = initQuill('#description-editor');
const quillTips = initQuill('#tips-editor');

document.getElementById('quest-form')?.addEventListener('submit', e => {
  const descriptionContent = quillDescription.root.innerHTML.trim();
  const tipsContent = quillTips.root.innerHTML.trim();

  if (!descriptionContent || descriptionContent === '<p><br></p>') {
    alert('Description is required.');
    e.preventDefault();
    return false;
  }

  document.getElementById('description').value = descriptionContent;
  document.getElementById('tips').value = tipsContent;
});

