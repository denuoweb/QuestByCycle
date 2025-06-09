import { initQuill } from './quill_common.js';
    document.addEventListener('DOMContentLoaded', function() {
        const editors = ['description', 'description2', 'details', 'awards', 'beyond'];

        editors.forEach(editorId => {
            initQuill(`#${editorId}`, `#${editorId}-textarea`);
        });
    });

