/**
 * Advanced Gallery JavaScript
 * Manages layout switching, selection mode, lazy loading, and bulk actions
 */

class AdvancedGallery {
    constructor() {
        this.currentLayout = 'grid';
        this.selectionMode = false;
        this.selectedPhotos = new Set();
        this.photoSearch = null;
        this.photoSelector = null;
        this.lazyLoadObserver = null;
        this.loadedImagesCount = 0;
        this.totalImagesCount = 0;
        
        // Initialize components
        this.init();
    }
    
    init() {
        // Show loading bar
        this.showLoadingBar();
        
        this.loadUserPreferences();
        this.setupLayoutControls();
        this.setupSelectionMode();
        this.setupLazyLoading();
        this.setupBulkActions();
        this.initializePhotoSearch();
        this.initializePhotoSelector();
        this.setupKeyboardShortcuts();
        this.setupResizeHandler();
        
        // Store original photo order
        this.storeOriginalPhotoOrder();
        
        // Setup photo click handlers
        this.setupPhotoClickHandlers();
        
        // Initialize selection count
        this.initializeSelectionCount();
        
        // Apply saved layout immediately
        this.applyLayout(this.currentLayout);
        
        // Hide loading bar and show gallery
        this.hideLoadingBar();
        
        console.log('Advanced Gallery initialized successfully');
    }
    
    /**
     * Load user preferences from localStorage
     */
    loadUserPreferences() {
        const savedLayout = localStorage.getItem('gallery-layout');
        if (savedLayout && ['grid', 'masonry'].includes(savedLayout)) {
            this.currentLayout = savedLayout;
            this.updateLayoutUI();
        }
    }
    
    /**
     * Save user preferences to localStorage
     */
    saveUserPreferences() {
        localStorage.setItem('gallery-layout', this.currentLayout);
    }
    
    /**
     * Store original photo order
     */
    storeOriginalPhotoOrder() {
        const photoGrid = document.getElementById('photo-grid');
        if (photoGrid) {
            this.originalPhotoOrder = Array.from(photoGrid.querySelectorAll('.photo-item'));
            console.log(`Stored original order of ${this.originalPhotoOrder.length} photos`);
        }
    }
    
    /**
     * Setup layout control buttons
     */
    setupLayoutControls() {
        const layoutButtons = document.querySelectorAll('.layout-btn');
        
        layoutButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const layout = e.currentTarget.dataset.layout;
                this.switchLayout(layout);
            });
        });
    }
    
    /**
     * Switch between grid and masonry layouts
     */
    switchLayout(layout) {
        if (layout === this.currentLayout) return;
        
        this.currentLayout = layout;
        this.updateLayoutUI();
        this.applyLayout(layout);
        this.saveUserPreferences();
        
        console.log(`Layout switched to: ${layout}`);
    }
    
    /**
     * Apply layout to the photo grid
     */
    applyLayout(layout) {
        const photoGrid = document.getElementById('photo-grid');
        if (!photoGrid) return;
        
        if (layout === 'masonry') {
            photoGrid.classList.add('masonry');
            this.createMasonryLayout();
        } else {
            photoGrid.classList.remove('masonry');
            this.createGridLayout();
        }
    }
    
    /**
     * Update layout button states
     */
    updateLayoutUI() {
        const layoutButtons = document.querySelectorAll('.layout-btn');
        
        layoutButtons.forEach(button => {
            if (button.dataset.layout === this.currentLayout) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }
    
    /**
     * Create masonry layout with flexible columns
     */
    createMasonryLayout() {
        const photoGrid = document.getElementById('photo-grid');
        if (!photoGrid) return;
        
        // Store original order if not already stored
        if (!this.originalPhotoOrder) {
            this.originalPhotoOrder = Array.from(photoGrid.querySelectorAll('.photo-item'));
        }
        
        const photoItems = this.originalPhotoOrder;
        if (photoItems.length === 0) return;
        
        // Calculate optimal column count based on screen width (fewer columns for larger photos)
        const screenWidth = window.innerWidth;
        let columnCount = 3; // Default - fewer columns for larger photos
        
        if (screenWidth <= 575) {
            columnCount = 2;
        } else if (screenWidth <= 900) {
            columnCount = 2;
        } else if (screenWidth <= 1200) {
            columnCount = 3;
        } else {
            columnCount = 4;
        }
        
        // Clear existing content
        photoGrid.innerHTML = '';
        
        // Create columns
        const columns = [];
        for (let i = 0; i < columnCount; i++) {
            const column = document.createElement('div');
            column.className = 'photo-column';
            column.setAttribute('data-column', i + 1);
            columns.push(column);
            photoGrid.appendChild(column);
        }
        
        // Distribute photos to columns using height balancing
        const columnHeights = new Array(columnCount).fill(0);
        
        photoItems.forEach(photoItem => {
            // Find the shortest column
            let shortestColumnIndex = 0;
            let minHeight = columnHeights[0];
            
            for (let i = 1; i < columnCount; i++) {
                if (columnHeights[i] < minHeight) {
                    minHeight = columnHeights[i];
                    shortestColumnIndex = i;
                }
            }
            
            // Add photo to shortest column
            columns[shortestColumnIndex].appendChild(photoItem);
            
            // Estimate height (this will be more accurate once images load)
            const estimatedHeight = this.estimatePhotoHeight(photoItem);
            columnHeights[shortestColumnIndex] += estimatedHeight;
        });
        
        console.log(`Masonry layout created with ${columnCount} columns`);
        
        // Update photo click handlers after layout change
        this.setupPhotoClickHandlers();
    }
    
    /**
     * Create grid layout
     */
    createGridLayout() {
        const photoGrid = document.getElementById('photo-grid');
        if (!photoGrid) return;
        
        // Use original order if available, otherwise get current items
        const photoItems = this.originalPhotoOrder || Array.from(photoGrid.querySelectorAll('.photo-item'));
        if (photoItems.length === 0) return;
        
        // Clear existing content
        photoGrid.innerHTML = '';
        
        // Add all photos back to grid in original order
        photoItems.forEach(photoItem => {
            photoGrid.appendChild(photoItem);
        });
        
        console.log('Grid layout created');
        
        // Update photo click handlers after layout change
        this.setupPhotoClickHandlers();
    }
    
    /**
     * Estimate photo height for masonry layout
     */
    estimatePhotoHeight(photoItem) {
        const img = photoItem.querySelector('img');
        if (!img) return 200;
        
        // Try to get actual dimensions from data attributes first
        const dataWidth = img.dataset.width;
        const dataHeight = img.dataset.height;
        
        if (dataWidth && dataHeight && parseInt(dataWidth) > 0 && parseInt(dataHeight) > 0) {
            const aspectRatio = parseInt(dataWidth) / parseInt(dataHeight);
            const columnWidth = (window.innerWidth - 100) / this.getColumnCount(); // Approximate column width
            return (columnWidth / aspectRatio) + 20; // Add some padding
        }
        
        // Try to get natural dimensions
        if (img.naturalWidth && img.naturalHeight && img.naturalWidth > 0) {
            const aspectRatio = img.naturalWidth / img.naturalHeight;
            const columnWidth = (window.innerWidth - 100) / this.getColumnCount();
            return (columnWidth / aspectRatio) + 20;
        }
        
        // Fallback to common aspect ratios
        const commonRatios = [1.5, 0.67, 1.0, 1.33]; // Landscape, Portrait, Square, Other
        const randomRatio = commonRatios[Math.floor(Math.random() * commonRatios.length)];
        const columnWidth = (window.innerWidth - 100) / this.getColumnCount();
        return (columnWidth / randomRatio) + 20;
    }
    
    /**
     * Get current column count based on screen width
     */
    getColumnCount() {
        const screenWidth = window.innerWidth;
        if (screenWidth <= 575) return 2;
        if (screenWidth <= 900) return 2;
        if (screenWidth <= 1200) return 3;
        return 4;
    }
    
    /**
     * Regenerate masonry layout (useful for testing)
     */
    regenerateMasonryLayout() {
        if (this.currentLayout === 'masonry') {
            // Re-store original order before regenerating
            this.storeOriginalPhotoOrder();
            this.createMasonryLayout();
        }
    }
    
    /**
     * Setup selection mode toggle
     */
    setupSelectionMode() {
        const toggleButton = document.getElementById('toggle-selection-mode');
        const bulkActions = document.getElementById('bulk-actions');
        const photoGrid = document.getElementById('photo-grid');
        
        if (!toggleButton || !bulkActions || !photoGrid) return;
        
        toggleButton.addEventListener('click', () => {
            this.toggleSelectionMode();
        });
    }
    
    /**
     * Toggle selection mode on/off
     */
    toggleSelectionMode() {
        this.selectionMode = !this.selectionMode;
        
        const toggleButton = document.getElementById('toggle-selection-mode');
        const bulkActions = document.getElementById('bulk-actions');
        const photoGrid = document.getElementById('photo-grid');
        const photoItems = document.querySelectorAll('.photo-item');
        
        if (this.selectionMode) {
            // Enable selection mode
            toggleButton.classList.add('active');
            toggleButton.querySelector('.btn-text').textContent = 'Exit Selection';
            bulkActions.style.display = 'flex';
            photoGrid.classList.add('selection-mode');
            
            // Add selection class to items (checkboxes remain hidden)
            photoItems.forEach(item => {
                item.classList.add('selection-mode');
                const checkbox = item.querySelector('.photo-checkbox');
                if (checkbox) {
                    checkbox.style.display = 'none'; // Keep checkboxes hidden
                }
            });
            
            // Initialize photo selector if not already done
            if (!this.photoSelector) {
                this.initializePhotoSelector();
            }
            
        } else {
            // Disable selection mode
            toggleButton.classList.remove('active');
            toggleButton.querySelector('.btn-text').textContent = 'Select Photos';
            bulkActions.style.display = 'none';
            photoGrid.classList.remove('selection-mode');
            
            // Hide checkboxes and remove selection class
            photoItems.forEach(item => {
                item.classList.remove('selection-mode', 'selected');
                const checkbox = item.querySelector('.photo-checkbox');
                if (checkbox) {
                    checkbox.style.display = 'none';
                    checkbox.checked = false;
                }
            });
            
            // Clear selection
            this.selectedPhotos.clear();
            this.updateSelectionCount();
        }
        
        // Update photo click handlers when selection mode changes
        this.setupPhotoClickHandlers();
        
        console.log(`Selection mode: ${this.selectionMode ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Setup photo click handlers
     */
    setupPhotoClickHandlers() {
        const photoItems = document.querySelectorAll('.photo-item');
        
        photoItems.forEach(photoItem => {
            // Remove existing click handlers to avoid duplicates
            const existingHandler = photoItem._clickHandler;
            if (existingHandler) {
                photoItem.removeEventListener('click', existingHandler);
            }
            
            // Create new click handler
            const clickHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (this.selectionMode) {
                    // In selection mode: toggle selection
                    this.togglePhotoSelection(photoItem);
                } else {
                    // In normal mode: go to photo details
                    this.goToPhotoDetails(photoItem);
                }
            };
            
            // Store reference to handler for later removal
            photoItem._clickHandler = clickHandler;
            
            // Add new click handler
            photoItem.addEventListener('click', clickHandler);
        });
    }
    
    /**
     * Toggle photo selection
     */
    togglePhotoSelection(photoItem) {
        const checkbox = photoItem.querySelector('.photo-checkbox');
        if (checkbox) {
            checkbox.checked = !checkbox.checked;
            photoItem.classList.toggle('selected', checkbox.checked);
            
            // Update our internal selection tracking
            const photoId = photoItem.dataset.photoId;
            if (checkbox.checked) {
                this.selectedPhotos.add(photoId);
            } else {
                this.selectedPhotos.delete(photoId);
            }
            
            // Update selection count
            this.updateSelectionCount();
        }
    }
    
    /**
     * Go to photo details page
     */
    goToPhotoDetails(photoItem) {
        const photoId = photoItem.dataset.photoId;
        if (photoId) {
            // Get the photo detail URL from the hidden link
            const detailLink = photoItem.querySelector('.photo-detail-link');
            if (detailLink) {
                window.location.href = detailLink.href;
            } else {
                // Fallback: construct URL
                window.location.href = `/photos/${photoId}/`;
            }
        }
    }
    
    /**
     * Initialize PhotoSearch component
     */
    initializePhotoSearch() {
        try {
            this.photoSearch = new PhotoSearch({
                searchInputSelector: '.photo-search-input',
                resultsContainerSelector: '.photo-search-results',
                photoGridSelector: '#photo-grid',
                showFilters: true,
                showLoadingInInput: true,
                navbarMode: false,
                searchDelay: 300
            });
            
            console.log('PhotoSearch initialized successfully');
        } catch (error) {
            console.error('Failed to initialize PhotoSearch:', error);
        }
    }
    
    /**
     * Initialize PhotoSelector component
     */
    initializePhotoSelector() {
        try {
            // Check if the container exists before initializing
            const container = document.querySelector('#photo-grid-container');
            if (!container) {
                console.warn('PhotoSelector: Container #photo-grid-container not found');
                return;
            }
            
            this.photoSelector = new PhotoSelector({
                containerSelector: '#photo-grid-container',
                photoItemSelector: '.photo-item',
                checkboxSelector: '.photo-checkbox',
                selectedClass: 'selected',
                singleSelection: false,
                onSelectionChange: (selectedItems) => {
                    this.selectedPhotos = new Set(selectedItems);
                    this.updateSelectionCount();
                }
            });
            
            console.log('PhotoSelector initialized successfully');
        } catch (error) {
            console.error('Failed to initialize PhotoSelector:', error);
        }
    }
    
    /**
     * Update selection count display
     */
    updateSelectionCount() {
        const countElement = document.getElementById('selected-count');
        if (countElement) {
            countElement.textContent = this.selectedPhotos.size;
            console.log(`Selection count updated: ${this.selectedPhotos.size} photos selected`);
        } else {
            console.warn('Selected count element not found');
        }
    }
    
    /**
     * Initialize selection count
     */
    initializeSelectionCount() {
        // Clear any existing selections
        this.selectedPhotos.clear();
        this.updateSelectionCount();
    }
    
    /**
     * Show loading bar
     */
    showLoadingBar() {
        const loadingBar = document.getElementById('gallery-loading-bar');
        if (loadingBar) {
            loadingBar.classList.remove('hidden');
        }
    }
    
    /**
     * Hide loading bar and show gallery
     */
    hideLoadingBar() {
        const loadingBar = document.getElementById('gallery-loading-bar');
        const galleryContainer = document.querySelector('.advanced-gallery-container');
        
        if (loadingBar && galleryContainer) {
            // Add ready class to gallery
            galleryContainer.classList.add('ready');
            
            // Hide loading bar after a short delay
            setTimeout(() => {
                loadingBar.classList.add('hidden');
            }, 500);
        }
    }
    
    /**
     * Setup lazy loading with Intersection Observer
     */
    setupLazyLoading() {
        // Check if Intersection Observer is supported
        if (!('IntersectionObserver' in window)) {
            // Fallback: load all images immediately
            this.loadAllImages();
            return;
        }
        
        // Create intersection observer
        this.lazyLoadObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    this.loadImage(img);
                    this.lazyLoadObserver.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px', // Start loading 50px before image comes into view
            threshold: 0.01
        });
        
        // Observe all lazy images
        const lazyImages = document.querySelectorAll('.lazy-load');
        this.totalImagesCount = lazyImages.length;
        lazyImages.forEach(img => {
            this.lazyLoadObserver.observe(img);
        });
        
        // Update loaded count display
        this.updateLoadedCount();
        
        console.log(`Lazy loading setup for ${lazyImages.length} images`);
    }
    
    /**
     * Load a specific image
     */
    loadImage(img) {
        const src = img.dataset.src;
        if (src) {
            img.src = src;
            img.classList.remove('lazy-load');
            img.classList.add('loaded');
            
            // Increment loaded count
            this.loadedImagesCount++;
            this.updateLoadedCount();
        }
    }
    
    /**
     * Update loaded images count display
     */
    updateLoadedCount() {
        const loadedCountElement = document.getElementById('loaded-photos-count');
        if (loadedCountElement) {
            loadedCountElement.textContent = this.loadedImagesCount;
        }
    }
    
    /**
     * Load all images immediately (fallback)
     */
    loadAllImages() {
        const lazyImages = document.querySelectorAll('.lazy-load');
        lazyImages.forEach(img => {
            this.loadImage(img);
        });
    }
    
    /**
     * Setup bulk action handlers
     */
    setupBulkActions() {
        // Add to collection
        const addToCollectionBtn = document.getElementById('add-to-collection-btn');
        if (addToCollectionBtn) {
            addToCollectionBtn.addEventListener('click', () => {
                this.showCollectionModal();
            });
        }
        
        // Create post
        const createPostBtn = document.getElementById('create-post-btn');
        if (createPostBtn) {
            createPostBtn.addEventListener('click', () => {
                this.createPostWithSelected();
            });
        }
        
        // Bulk edit
        const bulkEditBtn = document.getElementById('bulk-edit-btn');
        if (bulkEditBtn) {
            bulkEditBtn.addEventListener('click', () => {
                this.showBulkEditModal();
            });
        }
        
        // Bulk delete
        const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', () => {
                this.bulkDeletePhotos();
            });
        }
        
        // Collection modal handlers
        this.setupCollectionModal();
        this.setupBulkEditModal();
    }
    
    /**
     * Show collection selection modal
     */
    showCollectionModal() {
        if (this.selectedPhotos.size === 0) {
            alert('Please select photos first');
            return;
        }
        
        const modal = document.getElementById('collectionModal');
        if (modal) {
            // Reset form
            document.getElementById('collection-select').value = '';
            document.getElementById('new-collection-name').value = '';
            
            // Show modal (assuming Bootstrap modal)
            if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('show');
            } else {
                modal.style.display = 'block';
                modal.classList.add('show');
            }
        }
    }
    
    /**
     * Setup collection modal handlers
     */
    setupCollectionModal() {
        const confirmBtn = document.getElementById('confirm-add-to-collection');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.addToCollection();
            });
        }
    }
    
    /**
     * Add selected photos to collection
     */
    addToCollection() {
        const collectionSelect = document.getElementById('collection-select');
        const newCollectionName = document.getElementById('new-collection-name');
        
        let collectionId = collectionSelect.value;
        let collectionName = newCollectionName.value.trim();
        
        if (!collectionId && !collectionName) {
            alert('Please select a collection or enter a new collection name');
            return;
        }
        
        if (this.selectedPhotos.size === 0) {
            alert('No photos selected');
            return;
        }
        
        // Prepare data
        const data = {
            photo_ids: Array.from(this.selectedPhotos).join(','),
            collection_id: collectionId,
            new_collection_name: collectionName
        };
        
        // Show loading state
        this.showLoading();
        
        // Make AJAX request
        fetch('/photos/add-to-collection/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            this.hideLoading();
            
            if (result.success) {
                alert(`Successfully added ${this.selectedPhotos.size} photos to collection`);
                this.closeModal('collectionModal');
                this.toggleSelectionMode(); // Exit selection mode
            } else {
                alert('Error: ' + (result.message || 'Failed to add photos to collection'));
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error adding photos to collection:', error);
            alert('Error adding photos to collection');
        });
    }
    
    /**
     * Create post with selected photos
     */
    createPostWithSelected() {
        if (this.selectedPhotos.size === 0) {
            alert('Please select photos first');
            return;
        }
        
        // Redirect to post creation with selected photos
        const photoIds = Array.from(this.selectedPhotos).join(',');
        window.location.href = `/posts/create/?selected_photos=${photoIds}`;
    }
    
    /**
     * Show bulk edit modal
     */
    showBulkEditModal() {
        if (this.selectedPhotos.size === 0) {
            alert('Please select photos first');
            return;
        }
        
        const modal = document.getElementById('bulkEditModal');
        if (modal) {
            // Reset form
            document.getElementById('bulk-privacy').value = '';
            document.getElementById('bulk-tags').value = '';
            
            // Show modal
            if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('show');
            } else {
                modal.style.display = 'block';
                modal.classList.add('show');
            }
        }
    }
    
    /**
     * Setup bulk edit modal handlers
     */
    setupBulkEditModal() {
        const confirmBtn = document.getElementById('confirm-bulk-edit');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.bulkEditPhotos();
            });
        }
    }
    
    /**
     * Apply bulk edit changes
     */
    bulkEditPhotos() {
        const privacy = document.getElementById('bulk-privacy').value;
        const tags = document.getElementById('bulk-tags').value.trim();
        
        if (!privacy && !tags) {
            alert('Please select changes to apply');
            return;
        }
        
        if (this.selectedPhotos.size === 0) {
            alert('No photos selected');
            return;
        }
        
        // Prepare data
        const data = {
            photo_ids: Array.from(this.selectedPhotos).join(','),
            action: 'bulk_edit',
            is_private: privacy,
            tags: tags
        };
        
        // Show loading state
        this.showLoading();
        
        // Make AJAX request
        fetch('/photos/advanced-bulk-actions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            this.hideLoading();
            
            if (result.success) {
                alert(`Successfully updated ${this.selectedPhotos.size} photos`);
                this.closeModal('bulkEditModal');
                this.toggleSelectionMode(); // Exit selection mode
                // Reload page to show changes
                window.location.reload();
            } else {
                alert('Error: ' + (result.message || 'Failed to update photos'));
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error updating photos:', error);
            alert('Error updating photos');
        });
    }
    
    /**
     * Bulk delete selected photos
     */
    bulkDeletePhotos() {
        if (this.selectedPhotos.size === 0) {
            alert('Please select photos first');
            return;
        }
        
        const confirmMessage = `Are you sure you want to delete ${this.selectedPhotos.size} photos? This action cannot be undone.`;
        if (!confirm(confirmMessage)) {
            return;
        }
        
        // Prepare data
        const data = {
            photo_ids: Array.from(this.selectedPhotos).join(','),
            action: 'delete'
        };
        
        // Show loading state
        this.showLoading();
        
        // Make AJAX request
        fetch('/photos/advanced-bulk-actions/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            this.hideLoading();
            
            if (result.success) {
                alert(`Successfully deleted ${this.selectedPhotos.size} photos`);
                this.toggleSelectionMode(); // Exit selection mode
                // Reload page to show changes
                window.location.reload();
            } else {
                alert('Error: ' + (result.message || 'Failed to delete photos'));
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error deleting photos:', error);
            alert('Error deleting photos');
        });
    }
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts when not in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Ctrl/Cmd + A: Select all photos (when in selection mode)
            if ((e.ctrlKey || e.metaKey) && e.key === 'a' && this.selectionMode) {
                e.preventDefault();
                this.selectAllPhotos();
            }
            
            // Escape: Exit selection mode
            if (e.key === 'Escape' && this.selectionMode) {
                this.toggleSelectionMode();
            }
            
            // G: Toggle grid layout
            if (e.key === 'g' && !this.selectionMode) {
                this.switchLayout('grid');
            }
            
            // M: Toggle masonry layout
            if (e.key === 'm' && !this.selectionMode) {
                this.switchLayout('masonry');
            }
            
            // S: Toggle selection mode
            if (e.key === 's' && !this.selectionMode) {
                this.toggleSelectionMode();
            }
        });
    }
    
    /**
     * Select all visible photos
     */
    selectAllPhotos() {
        if (!this.selectionMode) return;
        
        const visiblePhotos = document.querySelectorAll('.photo-item:not([style*="display: none"])');
        visiblePhotos.forEach(item => {
            const checkbox = item.querySelector('.photo-checkbox');
            if (checkbox) {
                checkbox.checked = true;
                item.classList.add('selected');
            }
        });
        
        // Update selection count
        this.selectedPhotos = new Set(Array.from(visiblePhotos).map(item => {
            const checkbox = item.querySelector('.photo-checkbox');
            return checkbox ? checkbox.value : null;
        }).filter(id => id !== null));
        
        this.updateSelectionCount();
    }
    
    /**
     * Close modal
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('hide');
            } else {
                modal.style.display = 'none';
                modal.classList.remove('show');
            }
        }
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        const container = document.querySelector('.advanced-gallery-container');
        if (container) {
            container.classList.add('gallery-loading');
        }
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        const container = document.querySelector('.advanced-gallery-container');
        if (container) {
            container.classList.remove('gallery-loading');
        }
    }
    
    /**
     * Get CSRF token from cookies
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
    
    /**
     * Setup resize handler for responsive masonry
     */
    setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (this.currentLayout === 'masonry') {
                    this.createMasonryLayout();
                }
            }, 250); // Debounce resize events
        });
    }
    
    /**
     * Destroy the gallery instance
     */
    destroy() {
        // Clean up observers
        if (this.lazyLoadObserver) {
            this.lazyLoadObserver.disconnect();
        }
        
        // Clean up components
        if (this.photoSearch && typeof this.photoSearch.destroy === 'function') {
            this.photoSearch.destroy();
        }
        
        if (this.photoSelector && typeof this.photoSelector.destroy === 'function') {
            this.photoSelector.destroy();
        }
        
        console.log('Advanced Gallery destroyed');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the advanced gallery
    window.advancedGallery = new AdvancedGallery();
    
    // Make it globally accessible for debugging
    console.log('Advanced Gallery available as window.advancedGallery');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedGallery;
}
