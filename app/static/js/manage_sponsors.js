    document.addEventListener('DOMContentLoaded', function() {
        const quillOptions = {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'font': [] }, { 'size': [] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'script': 'sub'}, { 'script': 'super' }],
                    [{ 'header': 1 }, { 'header': 2 }, { 'header': 3 }, { 'header': 4 }, { 'header': 5 }, { 'header': 6 }, 'blockquote', 'code-block'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }, { 'indent': '-1'}, { 'indent': '+1' }],
                    [{ 'direction': 'rtl' }, { 'align': [] }],
                    ['link', 'image', 'video', 'formula'],
                    ['clean']
                ]
            }
        };

        const descriptionEditor = new Quill('#description', quillOptions);
        const descriptionTextarea = document.getElementById('description-textarea');

        if (descriptionTextarea) { // Ensure the element exists before interacting with it
            descriptionEditor.on('text-change', function() {
                descriptionTextarea.value = descriptionEditor.root.innerHTML;
            });

            // Set initial value if there's any data
            descriptionEditor.root.innerHTML = descriptionTextarea.value;
        }
    });


