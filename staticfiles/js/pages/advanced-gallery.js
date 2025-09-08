// Advanced Gallery Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize gallery when page loads
    initializeAdvancedGallery();
});

function initializeAdvancedGallery() {
    console.log('Initializing Advanced Gallery...');
    
    // Initialize photo search
    initializePhotoSearch();
    
    // Initialize photo selection
    initializePhotoSelection();
    
    // Initialize layout controls
    initializeLayoutControls();
    
    // Initialize lazy loading
    initializeLazyLoading();
    
    // Initialize bulk actions
    initializeBulkActions();
    
    // Show gallery after initialization
    showGallery();
}

function initializePhotoSearch() {
    const searchInput = document.querySelector('.photo-search-input');
    const searchResults = document.querySelector('.photo-search-results');
    
    if (!searchInput || !searchResults) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performPhotoSearch(query);
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

function performPhotoSearch(query) {
    // This would typically make an AJAX request to search photos
    console.log('Searching for:', query);
    // For now, just show a placeholder
    const searchResults = document.querySelector('.photo-search-results');
    searchResults.innerHTML = `<div class="p-3 text-muted">Searching for "${query}"...</div>`;
    searchResults.style.display = 'block';
}

function initializePhotoSelection() {
    const toggleBtn = document.getElementById('toggle-selection-mode');
    const bulkActions = document.getElementById('bulk-actions');
    const photoCheckboxes = document.querySelectorAll('.photo-checkbox');
    const selectedCount = document.getElementById('selected-count');
    
    if (!toggleBtn || !bulkActions) return;
    
    let selectionMode = false;
    
    toggleBtn.addEventListener('click', function() {
        selectionMode = !selectionMode;
        
        if (selectionMode) {
            this.innerHTML = '<i class="fas fa-times"></i> <span class="btn-text">Cancel Selection</span>';
            this.classList.add('btn-primary');
            this.classList.remove('btn-outline-primary');
            bulkActions.style.display = 'flex';
            
            // Show checkboxes
            photoCheckboxes.forEach(checkbox => {
                checkbox.style.display = 'block';
            });
        } else {
            this.innerHTML = '<i class="fas fa-check-square"></i> <span class="btn-text">Select Photos</span>';
            this.classList.remove('btn-primary');
            this.classList.add('btn-outline-primary');
            bulkActions.style.display = 'none';
            
            // Hide checkboxes and uncheck all
            photoCheckboxes.forEach(checkbox => {
                checkbox.style.display = 'none';
                checkbox.checked = false;
            });
            
            updateSelectedCount();
        }
    });
    
    // Update selected count when checkboxes change
    photoCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
    
    function updateSelectedCount() {
        const checked = document.querySelectorAll('.photo-checkbox:checked');
        selectedCount.textContent = checked.length;
    }
}

function initializeLayoutControls() {
    const layoutBtns = document.querySelectorAll('.layout-btn');
    const photoGrid = document.getElementById('photo-grid');
    
    layoutBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const layout = this.dataset.layout;
            
            // Update active button
            layoutBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Apply layout
            if (layout === 'grid') {
                photoGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(250px, 1fr))';
            } else if (layout === 'masonry') {
                photoGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))';
                // Note: True masonry would require a library like Masonry.js
            }
        });
    });
}

function initializeLazyLoading() {
    const lazyImages = document.querySelectorAll('.lazy-load');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy-load');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

function initializeBulkActions() {
    // Add to collection
    const addToCollectionBtn = document.getElementById('add-to-collection-btn');
    if (addToCollectionBtn) {
        addToCollectionBtn.addEventListener('click', function() {
            const selectedPhotos = getSelectedPhotos();
            if (selectedPhotos.length === 0) {
                alert('Please select photos first');
                return;
            }
            
            // Show collection modal
            const modal = new bootstrap.Modal(document.getElementById('collectionModal'));
            modal.show();
        });
    }
    
    // Bulk edit
    const bulkEditBtn = document.getElementById('bulk-edit-btn');
    if (bulkEditBtn) {
        bulkEditBtn.addEventListener('click', function() {
            const selectedPhotos = getSelectedPhotos();
            if (selectedPhotos.length === 0) {
                alert('Please select photos first');
                return;
            }
            
            // Show bulk edit modal
            const modal = new bootstrap.Modal(document.getElementById('bulkEditModal'));
            modal.show();
        });
    }
    
    // Bulk delete
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function() {
            const selectedPhotos = getSelectedPhotos();
            if (selectedPhotos.length === 0) {
                alert('Please select photos first');
                return;
            }
            
            if (confirm(`Are you sure you want to delete ${selectedPhotos.length} photos?`)) {
                performBulkDelete(selectedPhotos);
            }
        });
    }
    
    // Confirm add to collection
    const confirmAddBtn = document.getElementById('confirm-add-to-collection');
    if (confirmAddBtn) {
        confirmAddBtn.addEventListener('click', function() {
            const selectedPhotos = getSelectedPhotos();
            const collectionId = document.getElementById('collection-select').value;
            const newCollectionName = document.getElementById('new-collection-name').value;
            
            if (collectionId || newCollectionName) {
                performAddToCollection(selectedPhotos, collectionId, newCollectionName);
            } else {
                alert('Please select a collection or enter a new collection name');
            }
        });
    }
    
    // Confirm bulk edit
    const confirmBulkEditBtn = document.getElementById('confirm-bulk-edit');
    if (confirmBulkEditBtn) {
        confirmBulkEditBtn.addEventListener('click', function() {
            const selectedPhotos = getSelectedPhotos();
            const isPrivate = document.getElementById('bulk-privacy').value;
            const tags = document.getElementById('bulk-tags').value;
            
            performBulkEdit(selectedPhotos, isPrivate, tags);
        });
    }
}

function getSelectedPhotos() {
    const checked = document.querySelectorAll('.photo-checkbox:checked');
    return Array.from(checked).map(checkbox => checkbox.value);
}

function performBulkDelete(photoIds) {
    // This would make an AJAX request to delete photos
    console.log('Deleting photos:', photoIds);
    // For now, just show a message
    alert(`Deleting ${photoIds.length} photos...`);
}

function performAddToCollection(photoIds, collectionId, newCollectionName) {
    // This would make an AJAX request to add photos to collection
    console.log('Adding photos to collection:', { photoIds, collectionId, newCollectionName });
    // For now, just show a message
    alert(`Adding ${photoIds.length} photos to collection...`);
}

function performBulkEdit(photoIds, isPrivate, tags) {
    // This would make an AJAX request to edit photos
    console.log('Bulk editing photos:', { photoIds, isPrivate, tags });
    // For now, just show a message
    alert(`Editing ${photoIds.length} photos...`);
}

function showGallery() {
    const loadingBar = document.getElementById('gallery-loading-bar');
    const loadingText = document.querySelector('.loading-text');
    const galleryContainer = document.querySelector('.advanced-gallery-container');
    
    // Hide loading indicators
    if (loadingBar) {
        loadingBar.classList.remove('show');
        setTimeout(() => {
            loadingBar.style.display = 'none';
        }, 300);
    }
    
    if (loadingText) {
        loadingText.classList.remove('show');
        setTimeout(() => {
            loadingText.style.display = 'none';
        }, 300);
    }
    
    // Show gallery with smooth transition
    if (galleryContainer) {
        galleryContainer.style.opacity = '1';
        galleryContainer.style.visibility = 'visible';
    }
    
    // Update loaded photos count
    const loadedCount = document.getElementById('loaded-photos-count');
    const photoItems = document.querySelectorAll('.photo-item');
    if (loadedCount) {
        loadedCount.textContent = photoItems.length;
    }
    
    console.log('Gallery displayed successfully');
}

// Export functions for global access
window.AdvancedGallery = {
    initializeAdvancedGallery,
    performPhotoSearch,
    getSelectedPhotos,
    performBulkDelete,
    performAddToCollection,
    performBulkEdit
};
