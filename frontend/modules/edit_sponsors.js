import { initQuill } from './quill_common.js';
document.addEventListener('DOMContentLoaded', function() {
    const editorEl   = document.querySelector('#description');
    const hiddenEl   = document.querySelector('#description-textarea');
    if (editorEl && hiddenEl) {
        if (window.Quill) {
            initQuill(editorEl, hiddenEl);
        } else {
            console.error('Quill library not found  sponsor editor will not work.');
        }
    }
});

