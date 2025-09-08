/**
 * Collections and Tags Management JavaScript
 * Handles drag & drop, AJAX operations, and UI interactions
 */

class CollectionsManager {
    constructor() {
        this.initializeEventListeners();
        this.initializeDragAndDrop();
    }

    initializeEventListeners() {
        // Tag input formatting
        document.querySelectorAll('.tag-input').forEach(input => {
            input.addEventListener('input', this.formatTagInput.bind(this));
            input.addEventListener('blur', this.finalizeTagFormat.bind(this));
        });

        // Collection actions
        document.querySelectorAll('.collection-action-btn').forEach(btn => {
            btn.addEventListener('click', this.handleCollectionAction.bind(this));
        });

        // Photo selection in collections
        document.querySelectorAll('.photo-selection-item').forEach(item => {
            item.addEventListener('click', this.handlePhotoSelection.bind(this));
        });
    }

    initializeDragAndDrop() {
        const photoGrids = document.querySelectorAll('.photo-grid[data-sortable="true"]');
        photoGrids.forEach(grid => {
            if (typeof Sortable !== 'undefined') {
                new Sortable(grid, {
                    animation: 150,
                    ghostClass: 'sortable-ghost',
                    chosenClass: 'sortable-chosen',
                    dragClass: 'sortable-drag',
                    onStart: () => this.showSaveOrderButton(grid),
                    onEnd: () => this.handlePhotoReorder(grid)
                });
            }
        });
    }

    formatTagInput(event) {
        let value = event.target.value;
        
        // Add # to tags that don't have it
        value = value.replace(/(?<!\s)#/g, ' #');
        value = value.replace(/(?<=\S)(?=#)/g, ' ');
        
        // Remove multiple spaces
        value = value.replace(/\s+/g, ' ').trim();
        
        event.target.value = value;
    }

    finalizeTagFormat(event) {
        let value = event.target.value;
        
        // Split by spaces and format each tag
        const tags = value.split(/\s+/).filter(tag => tag.trim());
        const formattedTags = tags.map(tag => {
            if (tag.startsWith('#')) {
                return tag;
            } else {
                return `#${tag}`;
            }
        });
        
        event.target.value = formattedTags.join(' ');
    }

    handleCollectionAction(event) {
        const action = event.target.dataset.action;
        const collectionId = event.target.dataset.collectionId;
        
        switch (action) {
            case 'delete':
                if (confirm('Are you sure you want to delete this collection? This action cannot be undone.')) {
                    this.deleteCollection(collectionId);
                }
                break;
            case 'edit':
                window.location.href = `/photos/collections/${collectionId}/edit/`;
                break;
            case 'add-photos':
                window.location.href = `/photos/collections/${collectionId}/add-photos/`;
                break;
        }
    }

    handlePhotoSelection(event) {
        const photoItem = event.target.closest('.photo-selection-item');
        if (!photoItem) return;
        
        const checkbox = photoItem.querySelector('.photo-checkbox');
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
            this.updateSelectionSummary();
        }
    }

    updateSelectionSummary() {
        const selectedPhotos = document.querySelectorAll('.photo-checkbox:checked');
        const selectedCount = document.getElementById('selected-count');
        const addPhotosBtn = document.getElementById('add-photos-btn');
        
        if (selectedCount) {
            selectedCount.textContent = selectedPhotos.length;
        }
        
        if (addPhotosBtn) {
            addPhotosBtn.disabled = selectedPhotos.length === 0;
        }
    }

    showSaveOrderButton(grid) {
        const saveBtn = grid.parentElement.querySelector('.save-order-btn');
        if (saveBtn) {
            saveBtn.style.display = 'block';
        }
    }

    handlePhotoReorder(grid) {
        const saveBtn = grid.parentElement.querySelector('.save-order-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePhotoOrder(grid));
        }
    }

    async savePhotoOrder(grid) {
        const photoItems = grid.querySelectorAll('.photo-item');
        const photoOrder = Array.from(photoItems).map(item => 
            item.getAttribute('data-photo-id')
        );
        
        const collectionId = grid.closest('[data-collection-id]')?.dataset.collectionId;
        if (!collectionId) return;
        
        try {
            const response = await fetch(`/photos/collections/${collectionId}/reorder/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    photo_order: photoOrder
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccessMessage('Photo order saved successfully!');
                const saveBtn = grid.parentElement.querySelector('.save-order-btn');
                if (saveBtn) {
                    saveBtn.style.display = 'none';
                }
            } else {
                this.showErrorMessage('Error saving order: ' + data.message);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showErrorMessage('Error saving order. Please try again.');
        }
    }

    async deleteCollection(collectionId) {
        try {
            const response = await fetch(`/photos/collections/${collectionId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                window.location.href = '/photos/collections/';
            } else {
                this.showErrorMessage('Error deleting collection');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showErrorMessage('Error deleting collection');
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name=csrf-token]')?.content;
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'danger');
    }

    showMessage(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

class TagsManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Tag search functionality
        const searchForm = document.querySelector('#tag-search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleTagSearch.bind(this));
        }

        // Tag input formatting
        document.querySelectorAll('.tag-input').forEach(input => {
            input.addEventListener('input', this.formatTagInput.bind(this));
            input.addEventListener('blur', this.finalizeTagFormat.bind(this));
        });
    }

    handleTagSearch(event) {
        const form = event.target;
        const tagsInput = form.querySelector('input[name="tags"]');
        
        if (!tagsInput.value.trim()) {
            event.preventDefault();
            this.showErrorMessage('Please enter at least one tag to search for.');
            return false;
        }
    }

    formatTagInput(event) {
        let value = event.target.value;
        
        // Add # to tags that don't have it
        value = value.replace(/(?<!\s)#/g, ' #');
        value = value.replace(/(?<=\S)(?=#)/g, ' ');
        
        // Remove multiple spaces
        value = value.replace(/\s+/g, ' ').trim();
        
        event.target.value = value;
    }

    finalizeTagFormat(event) {
        let value = event.target.value;
        
        // Split by spaces and format each tag
        const tags = value.split(/\s+/).filter(tag => tag.trim());
        const formattedTags = tags.map(tag => {
            if (tag.startsWith('#')) {
                return tag;
            } else {
                return `#${tag}`;
            }
        });
        
        event.target.value = formattedTags.join(' ');
    }

    showErrorMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
    }
}

// Initialize managers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Collections Manager
    if (document.querySelector('.collection-card, .photo-grid')) {
        new CollectionsManager();
    }
    
    // Initialize Tags Manager
    if (document.querySelector('.tag-input, #tag-search-form')) {
        new TagsManager();
    }
    
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize Bootstrap tabs if available
    if (typeof bootstrap !== 'undefined') {
        var triggerTabList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tab"]'));
        triggerTabList.forEach(function (triggerEl) {
            var tabTrigger = new bootstrap.Tab(triggerEl);
            
            triggerEl.addEventListener('click', function (event) {
                event.preventDefault();
                tabTrigger.show();
            });
        });
    }
});
