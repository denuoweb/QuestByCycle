import { getCSRFToken } from '../utils.js';
import logger from '../logger.js';

// Badge management functions
document.addEventListener('DOMContentLoaded', () => {
  loadBadges();
  document.querySelectorAll('[data-toggle-form]').forEach(btn => {
    btn.addEventListener('click', () => toggleForm(btn.dataset.toggleForm));
  });
});

function loadBadges() {
    const badgesBody = document.getElementById('badgesBody');
    if (!badgesBody) {
        return;
    }

    fetch('/badges')
        .then(response => response.json())
        .then(data => {
            badgesBody.innerHTML = '';
            data.badges.forEach(badge => {
                const row = document.createElement('tr');
                row.dataset.badgeId = badge.id;

                const imageHTML = badge.image ? `<img src="${badge.image}" height="50" alt="Badge Image">` : 'No Image';

                row.innerHTML = `
                    <td class="badge-image-manage">${imageHTML}</td>
                    <td class="badge-name">${badge.name}</td>
                    <td class="badge-description">${badge.description}</td>
                    <td class="badge-category">${badge.category || 'None'}</td>
                    <td>
                        <button class="edit-badge" data-badge-id="${badge.id}">Edit</button>
                        <button class="delete-badge" data-badge-id="${badge.id}">Delete</button>
                    </td>
                `;

                row.querySelector('.edit-badge').addEventListener('click', () => editBadge(badge.id));
                row.querySelector('.delete-badge').addEventListener('click', () => deleteBadge(badge.id));

                badgesBody.appendChild(row);
            });
        })
        .catch(error => logger.error('Failed to load badges:', error));
}

function toggleForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.classList.toggle('d-none');
}

function setCategoryOptions(currentCategory) {
    return fetch('/badges/categories')
        .then(response => response.json())
        .then(data => {
            const categories = data.categories || [];
            const select = document.createElement('select');
            select.className = 'form-control badge-category-select';

            const noneOption = document.createElement('option');
            noneOption.value = 'none';
            noneOption.textContent = 'None';
            if (!currentCategory || currentCategory === 'none') {
                noneOption.selected = true;
            }
            select.appendChild(noneOption);

            categories.forEach(category => {
                const opt = document.createElement('option');
                opt.value = category;
                opt.textContent = category;
                if (category === currentCategory) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });

            return select;
        })
        .catch(error => {
            logger.error('Error fetching categories:', error);
            const select = document.createElement('select');
            select.className = 'form-control badge-category-select';
            const noneOption = document.createElement('option');
            noneOption.value = 'none';
            noneOption.textContent = 'None';
            noneOption.selected = true;
            select.appendChild(noneOption);
            return select;
        });
}

function editBadge(badgeId) {
    const row = document.querySelector(`tr[data-badge-id='${badgeId}']`);
    if (!row) {
        logger.error(`Badge row with ID ${badgeId} not found.`);
        return;
    }
    const nameCell = row.querySelector('.badge-name');
    const descriptionCell = row.querySelector('.badge-description');
    const categoryCell = row.querySelector('.badge-category');

    // Instead of .badge-image img, target the entire .badge-image-manage cell
    const imageContainer = row.querySelector('.badge-image-manage');

    // 1) Replace the name cell
    nameCell.textContent = '';
    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.value = nameCell.innerText.trim();
    nameInput.className = 'form-control badge-name-input';
    nameCell.appendChild(nameInput);

    // 2) Replace the description cell
    descriptionCell.textContent = '';
    const descTextarea = document.createElement('textarea');
    descTextarea.className = 'form-control badge-description-textarea';
    descTextarea.value = descriptionCell.innerText.trim();
    descriptionCell.appendChild(descTextarea);

    // 3) Replace or remove the existing <img>
    //    Then inject a file input
    if (imageContainer) {
        // Clear out existing content (be it "No Image" text or <img> tag)
        imageContainer.textContent = '';
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.className = 'form-control-file badge-image-input';
        imageContainer.appendChild(fileInput);
    } else {
        logger.error('Could not find badge-image-manage cell');
    }

    // 4) Call setCategoryOptions(...) to build the <select> for Category
    setCategoryOptions(categoryCell.innerText.trim()).then(selectEl => {
        categoryCell.textContent = '';
        categoryCell.appendChild(selectEl);

        // 5) Change the button label to "Save" and hook up the saveBadge call
        const editButton = row.querySelector('button.edit-badge');
        editButton.innerText = 'Save';
        editButton.onclick = () => saveBadge(badgeId);
    });
}

function saveBadge(badgeId) {
    const row = document.querySelector(`tr[data-badge-id='${badgeId}']`);

    const formData = new FormData();
    formData.append('name', row.querySelector('.badge-name-input').value.trim());
    formData.append('description', row.querySelector('.badge-description-textarea').value.trim());
    formData.append('category', row.querySelector('.badge-category-select').value);

    // If there's a file, attach it
    const imageInput = row.querySelector('.badge-image-input');
    if (imageInput && imageInput.files.length > 0) {
        formData.append('image', imageInput.files[0]);
    }

    // IMPORTANT: Append the CSRF token to the form data if required
    const csrfToken = document.querySelector('[name=csrf_token]').value;
    fetch(`/badges/update/${badgeId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Badge updated successfully');
            window.location.reload();
        } else {
            alert('Failed to update badge: ' + data.message);
        }
    })
    .catch(error => logger.error('Error updating badge:', error));
}


function deleteBadge(badgeId) {
    if (!confirm("Are you sure you want to delete this badge?")) return;

    fetch(`/badges/delete/${badgeId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(`Failed to delete badge: ${data.message}`);
        }
    })
    .catch(error => {
        logger.error('Error deleting badge:', error);
        alert('Error deleting badge. Please check console for details.');
    });
}

function uploadImages() {
    const formData = new FormData(document.getElementById('uploadForm'));
    fetch('/badges/upload_images', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Images uploaded successfully');
        } else {
            alert('Failed to upload images: ' + data.message);
        }
    })
    .catch(error => logger.error('Error uploading images:', error));
}
