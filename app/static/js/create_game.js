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

        const editors = ['description', 'description2', 'details', 'awards', 'beyond'];

        editors.forEach(editorId => {
            const quillEditor = new Quill(`#${editorId}`, quillOptions);
            const hiddenInput = document.getElementById(`${editorId}-textarea`);

            quillEditor.on('text-change', function() {
                hiddenInput.value = quillEditor.root.innerHTML;
            });
        });
    });
