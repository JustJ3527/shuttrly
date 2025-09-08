/**
 * Photo Edit JavaScript
 * Handles photo editing form interactions and validation
 */

class PhotoEditor {
    constructor() {
        this.form = document.querySelector('form');
        this.titleInput = document.querySelector('input[name="title"]');
        this.descriptionInput = document.querySelector('textarea[name="description"]');
        this.tagsInput = document.querySelector('input[name="tags"]');
        this.isPublicCheckbox = document.querySelector('input[name="is_public"]');
        this.isFeaturedCheckbox = document.querySelector('input[name="is_featured"]');
        this.previewTitle = document.querySelector('.photo-info-preview h5');
        this.previewImage = document.querySelector('.preview-image');
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupFormValidation();
        this.setupAutoSave();
        this.setupTagSuggestions();
    }
    
    bindEvents() {
        // Real-time preview updates
        if (this.titleInput) {
            this.titleInput.addEventListener('input', () => {
                this.updatePreview();
            });
        }
        
        if (this.descriptionInput) {
            this.descriptionInput.addEventListener('input', () => {
                this.updatePreview();
            });
        }
        
        if (this.tagsInput) {
            this.tagsInput.addEventListener('input', () => {
                this.updatePreview();
            });
        }
        
        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    this.showValidationErrors();
                } else {
                    this.showLoadingState();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 's':
                        e.preventDefault();
                        this.form.submit();
                        break;
                }
            }
        });
        
        // Auto-save on field blur
        const formFields = [this.titleInput, this.descriptionInput, this.tagsInput];
        formFields.forEach(field => {
            if (field) {
                field.addEventListener('blur', () => {
                    this.autoSave();
                });
            }
        });
    }
    
    setupFormValidation() {
        // Custom validation rules
        this.validationRules = {
            title: {
                minLength: 1,
                maxLength: 200,
                pattern: /^[a-zA-Z0-9\s\-_.,!?()]+$/
            },
            description: {
                maxLength: 1000
            },
            tags: {
                maxLength: 500,
                pattern: /^[a-zA-Z0-9\s\-_,]+$/
            }
        };
        
        // Add validation classes to form fields
        Object.keys(this.validationRules).forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.addEventListener('input', () => {
                    this.validateField(field, fieldName);
                });
            }
        });
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds if there are unsaved changes
        setInterval(() => {
            if (this.hasUnsavedChanges()) {
                this.autoSave();
            }
        }, 30000);
        
        // Warn user before leaving with unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }
    
    setupTagSuggestions() {
        if (this.tagsInput) {
            // Create suggestions container
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'tag-suggestions';
            suggestionsContainer.style.display = 'none';
            this.tagsInput.parentNode.appendChild(suggestionsContainer);
            
            // Common photography tags
            const commonTags = [
                'landscape', 'portrait', 'street', 'nature', 'architecture',
                'macro', 'black-and-white', 'color', 'abstract', 'documentary',
                'wedding', 'event', 'product', 'food', 'travel', 'urban',
                'rural', 'coastal', 'mountain', 'forest', 'desert', 'city',
                'vintage', 'modern', 'artistic', 'commercial', 'personal'
            ];
            
            this.tagsInput.addEventListener('input', () => {
                const inputValue = this.tagsInput.value;
                const lastTag = inputValue.split(',').pop().trim();
                
                if (lastTag.length > 1) {
                    const suggestions = commonTags.filter(tag => 
                        tag.toLowerCase().startsWith(lastTag.toLowerCase()) &&
                        !inputValue.toLowerCase().includes(tag.toLowerCase())
                    );
                    
                    if (suggestions.length > 0) {
                        this.showTagSuggestions(suggestions, suggestionsContainer);
                    } else {
                        suggestionsContainer.style.display = 'none';
                    }
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            });
            
            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!this.tagsInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                    suggestionsContainer.style.display = 'none';
                }
            });
        }
    }
    
    showTagSuggestions(suggestions, container) {
        container.innerHTML = '';
        container.style.display = 'block';
        
        suggestions.slice(0, 5).forEach(tag => {
            const suggestion = document.createElement('div');
            suggestion.className = 'tag-suggestion';
            suggestion.textContent = tag;
            suggestion.addEventListener('click', () => {
                this.addTag(tag);
                container.style.display = 'none';
            });
            container.appendChild(suggestion);
        });
    }
    
    addTag(tag) {
        const currentTags = this.tagsInput.value;
        const tagList = currentTags ? currentTags.split(',').map(t => t.trim()) : [];
        
        if (!tagList.includes(tag)) {
            tagList.push(tag);
            this.tagsInput.value = tagList.join(', ');
            this.updatePreview();
        }
    }
    
    updatePreview() {
        // Update preview title
        if (this.previewTitle && this.titleInput) {
            this.previewTitle.textContent = this.titleInput.value || 'Untitled';
        }
        
        // Update preview description (if we had one)
        // Update preview tags (if we had them)
        
        // Mark as having unsaved changes
        this.markAsUnsaved();
    }
    
    validateField(field, fieldName) {
        const rules = this.validationRules[fieldName];
        const value = field.value;
        let isValid = true;
        let errorMessage = '';
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Check min length
        if (rules.minLength && value.length < rules.minLength) {
            isValid = false;
            errorMessage = `Minimum length is ${rules.minLength} characters.`;
        }
        
        // Check max length
        if (rules.maxLength && value.length > rules.maxLength) {
            isValid = false;
            errorMessage = `Maximum length is ${rules.maxLength} characters.`;
        }
        
        // Check pattern
        if (rules.pattern && value && !rules.pattern.test(value)) {
            isValid = false;
            errorMessage = 'Invalid characters detected.';
        }
        
        // Apply validation classes
        if (isValid && value) {
            field.classList.add('is-valid');
        } else if (!isValid) {
            field.classList.add('is-invalid');
        }
        
        // Show/hide error message
        this.showFieldError(field, errorMessage);
        
        return isValid;
    }
    
    showFieldError(field, message) {
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message if there is one
        if (message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = message;
            field.parentNode.appendChild(errorDiv);
        }
    }
    
    validateForm() {
        let isValid = true;
        
        // Validate each field
        Object.keys(this.validationRules).forEach(fieldName => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (field && !this.validateField(field, fieldName)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showValidationErrors() {
        // Scroll to first error
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
        
        // Show error notification
        this.showNotification('Please correct the errors in the form.', 'error');
    }
    
    showLoadingState() {
        const formContainer = document.querySelector('.edit-form-container');
        if (formContainer) {
            formContainer.classList.add('loading');
        }
        
        // Disable form fields
        const formFields = this.form.querySelectorAll('input, textarea, button');
        formFields.forEach(field => {
            field.disabled = true;
        });
    }
    
    autoSave() {
        if (!this.hasUnsavedChanges()) return;
        
        // Create form data
        const formData = new FormData(this.form);
        
        // Send auto-save request
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-Auto-Save': 'true'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.markAsSaved();
                this.showNotification('Changes auto-saved successfully.', 'success');
            }
        })
        .catch(error => {
            console.error('Auto-save failed:', error);
            this.showNotification('Auto-save failed. Please save manually.', 'warning');
        });
    }
    
    hasUnsavedChanges() {
        // Check if any field has been modified
        const formData = new FormData(this.form);
        const currentData = new URLSearchParams(formData).toString();
        
        return currentData !== this.originalFormData;
    }
    
    markAsUnsaved() {
        // Add visual indicator
        const saveButton = this.form.querySelector('button[type="submit"]');
        if (saveButton) {
            saveButton.innerHTML = '<i class="fas fa-save"></i> Save Changes *';
            saveButton.classList.add('btn-warning');
        }
    }
    
    markAsSaved() {
        // Remove visual indicator
        const saveButton = this.form.querySelector('button[type="submit"]');
        if (saveButton) {
            saveButton.innerHTML = '<i class="fas fa-save"></i> Save Changes';
            saveButton.classList.remove('btn-warning');
        }
        
        // Store current form state
        const formData = new FormData(this.form);
        this.originalFormData = new URLSearchParams(formData).toString();
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
            border-radius: 10px;
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
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
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize photo editor
    window.photoEditor = new PhotoEditor();
    
    // Store original form state for change detection
    const form = document.querySelector('form');
    if (form) {
        const formData = new FormData(form);
        window.photoEditor.originalFormData = new URLSearchParams(formData).toString();
    }
    
    // Setup image preview enhancement
    setupImagePreview();
    
    // Setup form enhancement
    setupFormEnhancement();
});

// Image preview enhancement
function setupImagePreview() {
    const previewImage = document.querySelector('.preview-image');
    if (previewImage) {
        // Add click to enlarge functionality
        previewImage.style.cursor = 'pointer';
        previewImage.addEventListener('click', () => {
            showImageModal(previewImage.src, previewImage.alt);
        });
        
        // Add hover effect
        previewImage.addEventListener('mouseenter', () => {
            previewImage.style.transform = 'scale(1.05)';
            previewImage.style.transition = 'transform 0.3s ease';
        });
        
        previewImage.addEventListener('mouseleave', () => {
            previewImage.style.transform = 'scale(1)';
        });
    }
}

// Show image in modal
function showImageModal(src, alt) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-overlay"></div>
        <div class="image-modal-content">
            <button class="image-modal-close">&times;</button>
            <img src="${src}" alt="${alt}" class="image-modal-image">
        </div>
    `;
    
    // Style the modal
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .image-modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
        }
        
        .image-modal-content {
            position: relative;
            max-width: 90%;
            max-height: 90%;
            z-index: 1;
        }
        
        .image-modal-close {
            position: absolute;
            top: -40px;
            right: 0;
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
            z-index: 2;
        }
        
        .image-modal-image {
            max-width: 100%;
            max-height: 100%;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Close modal on click
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('image-modal-close')) {
            modal.remove();
        }
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', function closeOnEscape(e) {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', closeOnEscape);
        }
    });
}

// Form enhancement
function setupFormEnhancement() {
    // Add character counters
    const textFields = document.querySelectorAll('input[type="text"], textarea');
    textFields.forEach(field => {
        const maxLength = field.maxLength;
        if (maxLength) {
            const counter = document.createElement('div');
            counter.className = 'character-counter';
            counter.style.cssText = `
                font-size: 0.8rem;
                color: #666;
                text-align: right;
                margin-top: 0.25rem;
            `;
            
            field.parentNode.appendChild(counter);
            
            const updateCounter = () => {
                const current = field.value.length;
                const remaining = maxLength - current;
                counter.textContent = `${current}/${maxLength} characters`;
                
                if (remaining < 10) {
                    counter.style.color = '#dc3545';
                } else if (remaining < 50) {
                    counter.style.color = '#ffc107';
                } else {
                    counter.style.color = '#666';
                }
            };
            
            field.addEventListener('input', updateCounter);
            updateCounter(); // Initial count
        }
    });
    
    // Add form reset confirmation
    const resetButton = document.querySelector('button[type="reset"]');
    if (resetButton) {
        resetButton.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to reset all changes?')) {
                e.preventDefault();
            }
        });
    }
}

// Export class for global access
window.PhotoEditor = PhotoEditor;
