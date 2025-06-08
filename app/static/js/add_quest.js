var quillDescription = new Quill('#description-editor', {
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
});

var quillTips = new Quill('#tips-editor', {
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
});

document.getElementById('quest-form').onsubmit = function(e) {
    // Get the Quill editor contents
    var descriptionContent = quillDescription.root.innerHTML.trim();
    var tipsContent = quillTips.root.innerHTML.trim();

    // Check if the Quill editor content is empty
    if (!descriptionContent || descriptionContent === '<p><br></p>') {
        alert('Description is required.');
        e.preventDefault();  // Prevent the form from submitting
        return false;
    }

    // Set the hidden textarea value
    document.getElementById('description').value = descriptionContent;
    document.getElementById('tips').value = tipsContent;
};
