
/**
 * Photo Selector Module
 * A reusable JavaScript module for photo selection functionality
 * 
 * Features:
 * - Click on photos to select/deselect them
 * - Hidden checkboxes for form submission
 * - Support for single and multiple selection modes
 * - Visual feedback for selected state
 * - Easy to integrate in any template
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

class PhotoSelector {
    constructor(options = {}) {
        this.options = {
            // Default options
            containerSelector: '.photo-grid-container',
            photoItemSelector: '.photo-item',
            checkboxSelector: 'input[type="radio"], input[type="checkbox"]',
            selectedClass: 'selected',
            singleSelection: false,
            onSelectionChange: null,
            ...options
        };
        
        this.selectedItems = new Set();
        this.init();
    }
    
    /**
     * Initialize the photo selector
     */
    init() {
        this.container = document.querySelector(this.options.containerSelector);
        if (!this.container) {
            console.warn('PhotoSelector: Container not found');
            return;
        }
        
        this.bindEvents();
        this.hideCheckboxes();
        this.updateVisualState();
    }
    
    /**
     * Bind event listeners to photo items
     */
    bindEvents() {
        // Use event delegation for better performance
        this.container.addEventListener('click', (e) => {
            const photoItem = e.target.closest(this.options.photoItemSelector);
            if (photoItem) {
                this.handlePhotoClick(photoItem, e);
            }
        });
        
        // Handle keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const photoItem = e.target.closest(this.options.photoItemSelector);
                if (photoItem) {
                    this.handlePhotoClick(photoItem, e);
                }
            }
        });
    }
    
    /**
     * Handle photo item clicks
     */
    handlePhotoClick(photoItem, event) {
        // Don't trigger if clicking on interactive elements
        if (event.target.closest('button, a, input, label')) {
            return;
        }
        
        const checkbox = photoItem.querySelector(this.options.checkboxSelector);
        if (!checkbox) return;
        
        if (this.options.singleSelection) {
            this.selectSingle(photoItem, checkbox);
        } else {
            this.toggleSelection(photoItem, checkbox);
        }
        
        // Trigger callback if provided
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedItems());
        }
    }
    
    /**
     * Select a single photo (for radio buttons)
     */
    selectSingle(photoItem, checkbox) {
        // Deselect all other photos
        this.container.querySelectorAll(this.options.photoItemSelector).forEach(item => {
            item.classList.remove(this.options.selectedClass);
            const itemCheckbox = item.querySelector(this.options.checkboxSelector);
            if (itemCheckbox) {
                itemCheckbox.checked = false;
            }
        });
        
        // Select current photo
        photoItem.classList.add(this.options.selectedClass);
        checkbox.checked = true;
        this.selectedItems.clear();
        this.selectedItems.add(checkbox.value);
    }
    
    /**
     * Toggle photo selection (for checkboxes)
     */
    toggleSelection(photoItem, checkbox) {
        if (checkbox.checked) {
            // Deselect
            photoItem.classList.remove(this.options.selectedClass);
            checkbox.checked = false;
            this.selectedItems.delete(checkbox.value);
        } else {
            // Select
            photoItem.classList.add(this.options.selectedClass);
            checkbox.checked = true;
            this.selectedItems.add(checkbox.value);
        }
    }
    
    /**
     * Hide all checkboxes in the container
     */
    hideCheckboxes() {
        const checkboxes = this.container.querySelectorAll(this.options.checkboxSelector);
        checkboxes.forEach(checkbox => {
            // Completely hide the checkbox
            checkbox.style.display = 'none';
            
            // Also hide the label if it exists
            const label = checkbox.nextElementSibling;
            if (label && label.tagName === 'LABEL') {
                label.style.display = 'none';
            }
        });
    }
    
    /**
     * Show all checkboxes (useful for debugging)
     */
    showCheckboxes() {
        const checkboxes = this.container.querySelectorAll(this.options.checkboxSelector);
        checkboxes.forEach(checkbox => {
            checkbox.style.display = '';
            
            const label = checkbox.nextElementSibling;
            if (label && label.tagName === 'LABEL') {
                label.style.display = '';
            }
        });
    }
    
    /**
     * Get all selected photo values
     */
    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
    
    /**
     * Get selected photo elements
     */
    getSelectedElements() {
        return this.container.querySelectorAll(`${this.options.photoItemSelector}.${this.options.selectedClass}`);
    }
    
    /**
     * Select specific photos by value
     */
    selectByValue(values) {
        if (!Array.isArray(values)) {
            values = [values];
        }
        
        this.container.querySelectorAll(this.options.photoItemSelector).forEach(item => {
            const checkbox = item.querySelector(this.options.checkboxSelector);
            if (checkbox && values.includes(checkbox.value)) {
                item.classList.add(this.options.selectedClass);
                checkbox.checked = true;
                this.selectedItems.add(checkbox.value);
            }
        });
    }
    
    /**
     * Clear all selections
     */
    clearSelection() {
        this.container.querySelectorAll(this.options.photoItemSelector).forEach(item => {
            item.classList.remove(this.options.selectedClass);
            const checkbox = item.querySelector(this.options.checkboxSelector);
            if (checkbox) {
                checkbox.checked = false;
            }
        });
        this.selectedItems.clear();
    }
    
    /**
     * Select all visible photos
     */
    selectAll() {
        if (this.options.singleSelection) return;
        
        this.container.querySelectorAll(this.options.photoItemSelector).forEach(item => {
            const checkbox = item.querySelector(this.options.checkboxSelector);
            if (checkbox) {
                item.classList.add(this.options.selectedClass);
                checkbox.checked = true;
                this.selectedItems.add(checkbox.value);
            }
        });
    }
    
    /**
     * Update visual state based on checkbox states
     */
    updateVisualState() {
        this.container.querySelectorAll(this.options.photoItemSelector).forEach(item => {
            const checkbox = item.querySelector(this.options.checkboxSelector);
            if (checkbox && checkbox.checked) {
                item.classList.add(this.options.selectedClass);
                this.selectedItems.add(checkbox.value);
            }
        });
    }
    
    /**
     * Destroy the photo selector and clean up
     */
    destroy() {
        this.showCheckboxes();
        this.container.removeEventListener('click', this.handlePhotoClick);
        this.container.removeEventListener('keydown', this.handlePhotoClick);
    }
}

/**
 * Utility function to create a photo selector with common configurations
 */
function createPhotoSelector(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`PhotoSelector: Container with ID '${containerId}' not found`);
        return null;
    }
    
    return new PhotoSelector({
        containerSelector: `#${containerId}`,
        ...options
    });
}

/**
 * Initialize photo selectors for common use cases
 */
function initializePhotoSelectors() {
    // Single photo selection (radio buttons)
    const singlePhotoSelector = createPhotoSelector('photo-grid-container-single', {
        singleSelection: true,
        onSelectionChange: (selectedItems) => {
            console.log('Single photo selected:', selectedItems);
        }
    });
    
    // Multiple photos selection (checkboxes)
    const multiplePhotoSelector = createPhotoSelector('photo-grid-container-multiple', {
        singleSelection: false,
        onSelectionChange: (selectedItems) => {
            console.log('Multiple photos selected:', selectedItems);
        }
    });
    
    // Collection selection (radio buttons)
    const collectionSelector = createPhotoSelector('collection-grid-container', {
        singleSelection: true,
        onSelectionChange: (selectedItems) => {
            console.log('Collection selected:', selectedItems);
        }
    });
    
    // Store selectors globally for access
    window.photoSelectors = {
        single_photo: singlePhotoSelector,
        multiple_photos: multiplePhotoSelector,
        collection: collectionSelector
    };
    
    return window.photoSelectors;
}

/**
 * Initialize when DOM is ready
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePhotoSelectors);
} else {
    initializePhotoSelectors();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PhotoSelector, createPhotoSelector, initializePhotoSelectors };
}
