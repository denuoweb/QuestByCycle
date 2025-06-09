var quillDescription = initQuill('#description-editor');
var quillTips        = initQuill('#tips-editor');

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
