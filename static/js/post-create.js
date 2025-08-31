/**
 * Post Creation JavaScript - Optimized for Performance
 * Features: Lazy loading, debounced search, efficient DOM manipulation
 */

(function() {
    'use strict';
    
    // Performance optimization utilities
    const debounce = (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };
    
    // Throttle function for scroll events
    const throttle = (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };
    
    class PostCreator {
        constructor() {
            this.lazyLoadObserver = null;
            this.allPhotos = [];
            this.searchTimeout = null;
            this.init();
        }
        
        init() {
            this.initPhotoSearch();
            this.initSelectionHandlers();
            this.initUtilityButtons();
            this.initFormValidation();
            this.initAutoSave();
            this.initHTMXHandlers();
        }
        
        // Lazy loading implementation with Intersection Observer
        initLazyLoading() {
            if ('IntersectionObserver' in window) {
                this.lazyLoadObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            this.loadImage(img);
                        }
                    });
                }, {
                    rootMargin: '50px 0px',
                    threshold: 0.1
                });
                
                this.observeLazyImages();
            } else {
                // Fallback for older browsers
                this.loadAllImages();
            }
        }
        
        observeLazyImages() {
            document.querySelectorAll('.lazy').forEach(img => {
                this.lazyLoadObserver.observe(img);
            });
        }
        
        loadImage(img) {
            if (img.dataset.src && !img.src.startsWith('data:')) {
                const tempImg = new Image();
                tempImg.onload = () => {
                    img.src = tempImg.src;
                    img.classList.add('loaded');
                    img.classList.remove('lazy');
                    this.lazyLoadObserver.unobserve(img);
                };
                tempImg.onerror = () => {
                    console.warn('Failed to load image:', img.dataset.src);
                    img.classList.add('error');
                    this.lazyLoadObserver.unobserve(img);
                };
                tempImg.src = img.dataset.src;
            }
        }
        
        loadAllImages() {
            document.querySelectorAll('.lazy').forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    img.classList.remove('lazy');
                }
            });
        }
        
        // Optimized photo search with virtual scrolling
        initPhotoSearch() {
            const searchInput = document.querySelector('.photo-search-input');
            if (!searchInput) return;
            
            // Collect all photos data once for efficient searching
            this.collectPhotoData();
            
            const performSearch = debounce((term) => {
                this.performSearch(term);
            }, 300);
            
            searchInput.addEventListener('input', (e) => {
                performSearch(e.target.value);
            });
            
            // Clear search on escape
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    this.performSearch('');
                }
            });
        }
        
        collectPhotoData() {
            this.allPhotos = Array.from(document.querySelectorAll('.photo-item')).map(item => {
                const infoElement = item.querySelector('.photo-info small');
                return {
                    element: item,
                    id: item.dataset.photoId,
                    searchText: [
                        item.dataset.description || '',
                        item.dataset.tags || '',
                        item.dataset.date || '',
                        infoElement?.textContent || ''
                    ].join(' ').toLowerCase()
                };
            });
        }
        
        performSearch(term) {
            const searchTerm = term.toLowerCase().trim();
            
            if (searchTerm.length < 2) {
                this.showAllPhotos();
                return;
            }
            
            // Use DocumentFragment for efficient DOM updates
            const fragment = document.createDocumentFragment();
            let visibleCount = 0;
            
            this.allPhotos.forEach(photo => {
                const shouldShow = photo.searchText.includes(searchTerm);
                if (shouldShow) {
                    photo.element.style.display = 'block';
                    visibleCount++;
                } else {
                    photo.element.style.display = 'none';
                }
            });
            
            this.updateSearchStats(visibleCount, this.allPhotos.length);
        }
        
        showAllPhotos() {
            this.allPhotos.forEach(photo => {
                photo.element.style.display = 'block';
            });
            this.updateSearchStats(this.allPhotos.length, this.allPhotos.length);
        }
        
        updateSearchStats(visible, total) {
            const statsElement = document.querySelector('.search-stats');
            if (statsElement) {
                statsElement.textContent = `${visible} of ${total} photos`;
            }
        }
        
        // Efficient selection handlers using event delegation
        initSelectionHandlers() {
            document.addEventListener('change', (e) => {
                const target = e.target;
                
                if (target.name === 'selected_photo') {
                    this.handleSinglePhotoSelection(target);
                } else if (target.name === 'selected_photos') {
                    this.handleMultiplePhotoSelection();
                } else if (target.name === 'selected_collection') {
                    this.handleCollectionSelection(target);
                }
            });
        }
        
        handleSinglePhotoSelection(radio) {
            if (!radio.checked) return;
            
            const photoIdsField = document.getElementById(window.photoIdsFieldId);
            if (photoIdsField) {
                photoIdsField.value = radio.value;
            }
            
            // Efficient visual selection update
            const previousSelected = document.querySelector('.photo-item.selected');
            if (previousSelected) {
                previousSelected.classList.remove('selected');
            }
            
            radio.closest('.photo-item').classList.add('selected');
        }
        
        handleMultiplePhotoSelection() {
            const selectedPhotos = Array.from(document.querySelectorAll('input[name="selected_photos"]:checked'))
                .map(cb => cb.value);
            
            const photoIdsField = document.getElementById(window.photoIdsFieldId);
            if (photoIdsField) {
                photoIdsField.value = selectedPhotos.join(',');
            }
            
            // Batch DOM updates for better performance
            requestAnimationFrame(() => {
                document.querySelectorAll('.photo-item').forEach(item => {
                    const checkbox = item.querySelector('input[name="selected_photos"]');
                    if (checkbox) {
                        item.classList.toggle('selected', checkbox.checked);
                    }
                });
            });
            
            this.updateSelectionCount(selectedPhotos.length);
        }
        
        handleCollectionSelection(radio) {
            if (!radio.checked) return;
            
            const collectionIdField = document.getElementById(window.collectionIdFieldId);
            if (collectionIdField) {
                collectionIdField.value = radio.value;
            }
            
            // Efficient visual selection update
            const previousSelected = document.querySelector('.collection-item.selected');
            if (previousSelected) {
                previousSelected.classList.remove('selected');
            }
            
            radio.closest('.collection-item').classList.add('selected');
        }
        
        updateSelectionCount(count) {
            const countElement = document.querySelector('.selection-count');
            if (countElement) {
                countElement.textContent = count > 0 ? `${count} selected` : '';
            }
        }
        
        // Utility buttons for bulk operations
        initUtilityButtons() {
            // Select all visible photos
            const selectAllBtn = document.getElementById('select-all-photos');
            if (selectAllBtn) {
                selectAllBtn.addEventListener('click', () => {
                    const visibleCheckboxes = Array.from(document.querySelectorAll('input[name="selected_photos"]'))
                        .filter(cb => cb.closest('.photo-item').style.display !== 'none');
                    
                    const allSelected = visibleCheckboxes.length > 0 && visibleCheckboxes.every(cb => cb.checked);
                    
                    // Batch update for performance
                    visibleCheckboxes.forEach(cb => {
                        cb.checked = !allSelected;
                    });
                    
                    this.handleMultiplePhotoSelection();
                    
                    // Update button text
                    selectAllBtn.innerHTML = allSelected 
                        ? '<i class="fas fa-check-square"></i> Select All Visible'
                        : '<i class="fas fa-square"></i> Deselect All';
                });
            }
            
            // Clear selection
            const clearBtn = document.getElementById('clear-selection');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    document.querySelectorAll('input[name="selected_photos"]:checked').forEach(cb => {
                        cb.checked = false;
                    });
                    this.handleMultiplePhotoSelection();
                });
            }
        }
        
        // Enhanced form validation with better UX
        initFormValidation() {
            const form = document.getElementById('post-create-form');
            const submitBtn = document.getElementById('submit-btn');
            
            if (!form || !submitBtn) return;
            
            form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    return false;
                }
                
                this.showSubmitLoading(submitBtn);
            });
        }
        
        validateForm() {
            const postType = window.currentPostType;
            let isValid = true;
            let errorMessage = '';
            
            // Remove previous error alerts
            const previousAlert = document.querySelector('.validation-alert');
            if (previousAlert) {
                previousAlert.remove();
            }
            
            if (postType === 'single_photo') {
                const photoIdsField = document.getElementById(window.photoIdsFieldId);
                if (!photoIdsField?.value) {
                    errorMessage = 'Please select a photo for your post';
                    isValid = false;
                }
            } else if (postType === 'multiple_photos') {
                const photoIdsField = document.getElementById(window.photoIdsFieldId);
                if (!photoIdsField?.value) {
                    errorMessage = 'Please select at least one photo for your post';
                    isValid = false;
                }
            } else if (postType === 'collection') {
                const collectionIdField = document.getElementById(window.collectionIdFieldId);
                if (!collectionIdField?.value) {
                    errorMessage = 'Please select a collection for your post';
                    isValid = false;
                }
            }
            
            if (!isValid) {
                this.showValidationError(errorMessage);
            }
            
            return isValid;
        }
        
        showValidationError(message) {
            const form = document.getElementById('post-create-form');
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning alert-dismissible fade show validation-alert';
            alertDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            form.insertBefore(alertDiv, form.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
        
        showSubmitLoading(submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Post...';
        }
        
        // Auto-save functionality with localStorage
        initAutoSave() {
            const descriptionField = document.querySelector(`#${window.descriptionFieldId}`);
            const titleField = document.querySelector(`#${window.titleFieldId}`);
            
            if (!descriptionField || !titleField) return;
            
            const autoSaveDraft = debounce(() => {
                this.saveDraft(titleField.value, descriptionField.value);
            }, 5000);
            
            [descriptionField, titleField].forEach(field => {
                field.addEventListener('input', autoSaveDraft);
            });
            
            // Load existing draft
            this.loadDraft(titleField, descriptionField);
        }
        
        saveDraft(title, description) {
            const draft = {
                title,
                description,
                post_type: window.currentPostType,
                timestamp: new Date().toISOString()
            };
            
            try {
                localStorage.setItem(`post_draft_${window.currentPostType}`, JSON.stringify(draft));
                this.showAutoSaveIndicator();
            } catch (e) {
                console.warn('Could not save draft:', e);
            }
        }
        
        loadDraft(titleField, descriptionField) {
            try {
                const savedDraft = localStorage.getItem(`post_draft_${window.currentPostType}`);
                if (savedDraft && !descriptionField.value && !titleField.value) {
                    const draft = JSON.parse(savedDraft);
                    if (draft.title) titleField.value = draft.title;
                    if (draft.description) descriptionField.value = draft.description;
                    
                    this.showDraftLoadedNotification();
                }
            } catch (e) {
                console.warn('Could not load draft:', e);
            }
        }
        
        showAutoSaveIndicator() {
            // Simple visual feedback for auto-save
            const indicator = document.querySelector('.auto-save-indicator');
            if (indicator) {
                indicator.style.opacity = '1';
                setTimeout(() => {
                    indicator.style.opacity = '0';
                }, 2000);
            }
        }
        
        showDraftLoadedNotification() {
            console.log('Draft restored from previous session');
        }
        
        // HTMX integration for dynamic content loading
        initHTMXHandlers() {
            document.body.addEventListener('htmx:afterSwap', (event) => {
                if (event.target.id === 'post-content-area') {
                    // Re-initialize components for new content
                    setTimeout(() => {
                        this.reinitialize();
                    }, 100);
                }
            });
            
            // Loading states for HTMX
            document.body.addEventListener('htmx:beforeRequest', this.showHTMXLoading);
            document.body.addEventListener('htmx:afterRequest', this.hideHTMXLoading);
        }
        
        reinitialize() {
            // Re-initialize everything
            this.initPhotoSearch();
            this.initUtilityButtons();
            this.initFormValidation();
            this.initAutoSave();
        }
        
        showHTMXLoading() {
            const indicator = document.getElementById('loading-indicator');
            if (indicator) {
                indicator.style.display = 'block';
            }
        }
        
        hideHTMXLoading() {
            const indicator = document.getElementById('loading-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }
        
        // Cleanup method
        destroy() {
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
        }
    }
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        window.postCreator = new PostCreator();
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (window.postCreator) {
            window.postCreator.destroy();
        }
    });
    
})();
