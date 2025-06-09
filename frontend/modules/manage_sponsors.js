import { initQuill } from './quill_common.js';
    document.addEventListener('DOMContentLoaded', function() {
        const editorEl   = document.querySelector('#description');
        const hiddenEl   = document.querySelector('#description-textarea');

        if (editorEl && hiddenEl) {
            if (window.Quill) {
                const descriptionEditor = initQuill(editorEl, hiddenEl);
                if (descriptionEditor) descriptionEditor.root.innerHTML = hiddenEl.value;
            } else {
                console.error('Quill library not found  sponsor editor will not work.');
            }
        }
    });



