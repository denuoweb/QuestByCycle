import { initQuill } from './quill_common.js';
    document.addEventListener('DOMContentLoaded', function() {
        const editorEl   = document.querySelector('#description');
        const hiddenEl   = document.querySelector('#description-textarea');

        if (editorEl && hiddenEl) {
            const descriptionEditor = initQuill(editorEl, hiddenEl);
            if (descriptionEditor) descriptionEditor.root.innerHTML = hiddenEl.value;
        }
    });



