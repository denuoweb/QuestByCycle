import { initQuill } from './quill_common.js';
    document.addEventListener('DOMContentLoaded', function() {
        const editors = ['description', 'description2', 'details', 'awards', 'beyond'];

        editors.forEach(editorId => {
            const editorEl = document.getElementById(editorId);
            const hiddenEl = document.getElementById(`${editorId}-textarea`);
            if (editorEl && hiddenEl) {
                initQuill(editorEl, hiddenEl);
            }
        });
    });

