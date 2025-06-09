    document.addEventListener('DOMContentLoaded', function() {
        const descriptionEditor = initQuill('#description', '#description-textarea');
        const descriptionTextarea = document.getElementById('description-textarea');

        if (descriptionEditor && descriptionTextarea) {
            descriptionEditor.root.innerHTML = descriptionTextarea.value;
        }
    });


