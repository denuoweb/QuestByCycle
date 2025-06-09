import { initQuill } from './quill_common.js';
document.addEventListener('DOMContentLoaded', function() {
    const editorEl   = document.querySelector('#description');
    const hiddenEl   = document.querySelector('#description-textarea');
    if (editorEl && hiddenEl) {
        initQuill(editorEl, hiddenEl);
    }
});

