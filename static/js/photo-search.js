/**
 * Enhanced Photo Search Component - Advanced search with filters
 * Reusable component for navbar, post creation, and other templates
 * 
 * Features:
 * - Real-time search as you type
 * - Advanced filters (raw, camera, date_taken, tags, etc.)
 * - Debounced input to avoid excessive API calls
 * - Highlighted search results
 * - Responsive design using CSS variables
 * - Modular design for easy integration
 * - Loading indicator in input field
 * - Deduplicated camera choices
 */

class PhotoSearch {
    constructor(options = {}) {
        this.options = {
            searchInputSelector: '.photo-search-input',
            resultsContainerSelector: '.photo-search-results',
            photoGridSelector: '.photo-grid',
            searchDelay: 300, // milliseconds
            minSearchLength: 2,
            highlightClass: 'search-highlight',
            noResultsClass: 'no-search-results',
            loadingClass: 'search-loading',
            showFilters: true, // Show advanced filters
            showLoadingInInput: true, // Show loading spinner in input
            navbarMode: false, // Special mode for navbar
            ...options
        };
        
        this.searchTimeout = null;
        this.currentSearchTerm = '';
        this.currentFilters = {
            raw: false,
            camera: ''
        };
        this.allPhotos = [];
        this.filteredPhotos = [];
        this.isInitialized = false;
        this.cameraChoices = new Set(); // Deduplicated camera choices
        
        this.init();
    }
    
    init() {
        this.searchInput = document.querySelector(this.options.searchInputSelector);
        this.resultsContainer = document.querySelector(this.options.resultsContainerSelector);
        this.photoGrid = document.querySelector(this.options.photoGridSelector);
        
        if (!this.searchInput || !this.photoGrid) {
            console.warn('PhotoSearch: Required elements not found', {
                searchInput: this.searchInput,
                photoGrid: this.photoGrid,
                selectors: this.options
            });
            return;
        }
        
        this.setupEventListeners();
        this.collectAllPhotos();
        this.setupFilters();
        this.isInitialized = true;
        
        // PhotoSearch initialized successfully
    }
    
    // Method to refresh the search when switching tabs
    refresh() {
        if (!this.isInitialized) {
            this.init();
            return;
        }
        
        // Recollect photos data (in case new photos were added)
        this.collectAllPhotos();
        
        // Repopulate camera choices after collecting photos
        this.populateCameraChoices();
        
        // Clear current search
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        
        // Reset filters
        this.resetFilters();
        
        // Show all photos
        this.showAllPhotos();
        
        // PhotoSearch refreshed
    }
    
    // Method to destroy the instance
    destroy() {
        if (this.searchInput) {
            this.searchInput.removeEventListener('input', this.handleSearchInput);
            this.searchInput.removeEventListener('keydown', this.handleKeydown);
            this.searchInput.removeEventListener('focus', this.handleFocus);
        }
        
        document.removeEventListener('click', this.handleClickOutside);
        
        // Remove filter event listeners
        this.removeFilterEventListeners();
        
        this.isInitialized = false;
        // PhotoSearch destroyed
    }
    
    setupEventListeners() {
        // Real-time search input
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });
        
        // Clear search on escape key
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
        
        // Focus management
        this.searchInput.addEventListener('focus', () => {
            this.handleFocus();
        });
        
        // Click outside to close results
        document.addEventListener('click', (e) => {
            this.handleClickOutside(e);
        });
    }
    
    handleSearchInput(value) {
        this.currentSearchTerm = value;
        
        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Show loading indicator in input if enabled
        if (this.options.showLoadingInInput) {
            this.showInputLoading();
        }
        
        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.performSearch(value);
        }, this.options.searchDelay);
    }
    
    handleKeydown(e) {
        if (e.key === 'Escape') {
            this.clearSearch();
        }
    }
    
    handleFocus() {
        // Don't show dropdown results on focus
        // this.showResults(); // Commented out to disable dropdown
    }
    
    handleClickOutside(e) {
        // Don't handle click outside since we don't show dropdown
        // if (!this.searchInput.contains(e.target) && !this.resultsContainer.contains(e.target)) {
        //     this.hideResults();
        // }
    }
    
    setupFilters() {
        if (!this.options.showFilters) return;
        
        // Generate unique instance ID for this PhotoSearch instance
        this.instanceId = Math.random().toString(36).substr(2, 9);
        
        // Create filters container
        const filtersContainer = this.createFiltersContainer();
        
        // Find or create the search container wrapper
        let searchContainer = this.searchInput.closest('.photo-search-container');
        if (!searchContainer) {
            // Wrap the search input in a container if it doesn't exist
            searchContainer = document.createElement('div');
            searchContainer.className = 'photo-search-container';
            this.searchInput.parentNode.insertBefore(searchContainer, this.searchInput);
            searchContainer.appendChild(this.searchInput);
        }
        
        // Add inline-filters class to the search container
        searchContainer.classList.add('has-inline-filters');
        
        // Append filters right after the search input
        searchContainer.appendChild(filtersContainer);
        
        // Store reference to filters container
        this.filtersContainer = filtersContainer;
        
        // Setup filter event listeners
        this.setupFilterEventListeners();
        
        // Populate camera choices after filters are created
        this.populateCameraChoices();
    }
    
    createFiltersContainer() {
        const container = document.createElement('div');
        container.className = 'photo-search-filters-inline';
        container.dataset.instanceId = this.instanceId;
        container.innerHTML = `
            <div class="inline-filter">
                <input type="checkbox" id="filter-raw-${this.instanceId}" class="filter-checkbox-inline" data-instance="${this.instanceId}">
                <label for="filter-raw-${this.instanceId}" class="filter-label-inline" title="Show only RAW format photos">
                    <i class="fas fa-file-code"></i> RAW
                </label>
            </div>
            
            <div class="inline-filter">
                <select id="filter-camera-${this.instanceId}" class="filter-select-inline" data-instance="${this.instanceId}" title="Filter by camera">
                    <option value="">All cameras</option>
                </select>
            </div>
            
            <button type="button" class="btn-clear-filters-inline" data-instance="${this.instanceId}" title="Clear all filters">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        return container;
    }
    
    setupFilterEventListeners() {
        if (!this.filtersContainer) return;
        
        // Use scoped selectors for this instance - simplified for inline filters
        const clearFiltersBtn = this.filtersContainer.querySelector(`[data-instance="${this.instanceId}"].btn-clear-filters-inline`);
        
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }
        
        // Individual filter change listeners with instant filtering
        const rawCheckbox = this.filtersContainer.querySelector(`#filter-raw-${this.instanceId}`);
        const cameraSelect = this.filtersContainer.querySelector(`#filter-camera-${this.instanceId}`);
        
        if (rawCheckbox) {
            rawCheckbox.addEventListener('change', (e) => {
                this.currentFilters.raw = e.target.checked;
                this.performSearch(this.currentSearchTerm);
            });
        }
        
        if (cameraSelect) {
            cameraSelect.addEventListener('change', (e) => {
                this.currentFilters.camera = e.target.value;
                this.performSearch(this.currentSearchTerm);
            });
        }
    }
    
    removeFilterEventListeners() {
        // Remove the specific filters container for this instance
        if (this.filtersContainer && this.filtersContainer.parentNode) {
            this.filtersContainer.parentNode.removeChild(this.filtersContainer);
        }
    }
    
    resetFilters() {
        this.currentFilters = {
            raw: false,
            camera: ''
        };
        
        // Reset UI with instance-specific selectors
        if (this.instanceId && this.filtersContainer) {
            const rawCheckbox = this.filtersContainer.querySelector(`#filter-raw-${this.instanceId}`);
            const cameraSelect = this.filtersContainer.querySelector(`#filter-camera-${this.instanceId}`);
            
            if (rawCheckbox) rawCheckbox.checked = false;
            if (cameraSelect) cameraSelect.value = '';
        }
        
        // Refresh search
        this.performSearch(this.currentSearchTerm);
    }
    
    applyFilters() {
        this.performSearch(this.currentSearchTerm);
    }
    
    setupStyles() {
        // Styles are now loaded via external CSS file (photo-search.css)
        // This method is kept for backward compatibility but does nothing
        // Using external CSS file (photo-search.css)
    }
    
    collectAllPhotos() {
        // Collect all photos from the current grid
        const photoItems = this.photoGrid.querySelectorAll('.photo-item');
        this.allPhotos = Array.from(photoItems).map(item => {
            const photoId = item.dataset.photoId;
            const img = item.querySelector('img');
            const title = item.querySelector('.photo-info small')?.textContent || 'Untitled';
            
            // Extract additional data from data attributes or hidden fields
            const description = item.dataset.description || '';
            const tags = item.dataset.tags || '';
            const dateTaken = item.dataset.dateTaken || item.dataset.date || ''; // Prioritize date_taken
            const camera = item.dataset.camera || '';
            const isRaw = item.dataset.raw === 'true' || item.dataset.raw === '1';
            
            // Add camera to choices if not empty
            if (camera && camera.trim()) {
                this.cameraChoices.add(camera);
            }
            
            return {
                element: item,
                id: photoId,
                title: title,
                description: description,
                tags: tags,
                thumbnail: img?.src || '',
                dateTaken: dateTaken,
                camera: camera,
                isRaw: isRaw,
                searchText: `${title} ${description} ${tags} ${dateTaken} ${camera}`.toLowerCase()
            };
        });
        
        this.filteredPhotos = [...this.allPhotos];
    }
    
    populateCameraChoices() {
        if (!this.instanceId || !this.filtersContainer) {
            return;
        }
        
        const cameraSelect = this.filtersContainer.querySelector(`#filter-camera-${this.instanceId}`);
        if (!cameraSelect) {
            return;
        }
        
        // Clear existing options except "All cameras"
        cameraSelect.innerHTML = '<option value="">All cameras</option>';
        
        // Add unique camera choices
        if (this.cameraChoices.size > 0) {
            Array.from(this.cameraChoices).sort().forEach(camera => {
                if (camera && camera.trim()) { // Only add non-empty cameras
                    const option = document.createElement('option');
                    option.value = camera;
                    option.textContent = camera;
                    cameraSelect.appendChild(option);
                }
            });
        }
    }
    
    performSearch(searchTerm) {
        this.currentSearchTerm = searchTerm.trim().toLowerCase();
        
        // Hide loading indicator
        this.hideInputLoading();
        
        if (this.currentSearchTerm.length < this.options.minSearchLength && !this.hasActiveFilters()) {
            this.showAllPhotos();
            this.hideResults();
            this.removeSearchStats();
            return;
        }
        
        // Filter photos based on search term
        this.filteredPhotos = this.allPhotos.filter(photo => 
            photo.searchText.includes(this.currentSearchTerm)
        );
        
        // Apply filters
        this.filteredPhotos = this.filteredPhotos.filter(photo => {
            const matchesSearchTerm = photo.searchText.includes(this.currentSearchTerm);
            
            // Apply actual filter logic
            if (this.currentFilters.raw && !photo.isRaw) return false;
            if (this.currentFilters.camera && photo.camera !== this.currentFilters.camera) return false;

            return matchesSearchTerm;
        });
        
        // Update display
        this.updatePhotoGrid();
        
        // Don't show dropdown results - only update the grid
        // this.showSearchResults(); // Commented out to disable dropdown
        
        // Update search stats
        this.updateSearchStats();
    }
    
    hasActiveFilters() {
        return this.currentFilters.raw || 
               this.currentFilters.camera;
    }
    
    updatePhotoGrid() {
        // Hide all photos first
        this.allPhotos.forEach(photo => {
            photo.element.style.display = 'none';
        });
        
        // Show filtered photos
        this.filteredPhotos.forEach(photo => {
            photo.element.style.display = 'block';
        });
        
        // Show/hide no results message
        const noPhotosElement = this.photoGrid.querySelector('.no-photos');
        if (noPhotosElement) {
            noPhotosElement.style.display = this.filteredPhotos.length === 0 ? 'block' : 'none';
        }
    }
    
    showSearchResults() {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = '';
        
        if (this.filteredPhotos.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="${this.options.noResultsClass}">
                    <i class="fas fa-search"></i>
                    No photos found matching "${this.currentSearchTerm}"
                </div>
            `;
        } else {
            this.filteredPhotos.forEach(photo => {
                const resultItem = this.createSearchResultItem(photo);
                this.resultsContainer.appendChild(resultItem);
            });
        }
        
        this.showResults();
    }
    
    createSearchResultItem(photo) {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.dataset.photoId = photo.id;
        
        // Highlight search terms in title
        const highlightedTitle = this.highlightSearchTerms(photo.title, this.currentSearchTerm);
        
        item.innerHTML = `
            <img src="${photo.thumbnail}" alt="${photo.title}" class="search-result-thumbnail">
            <div class="search-result-info">
                <div class="search-result-title">${highlightedTitle}</div>
                <div class="search-result-meta">
                    ${photo.dateTaken ? `<span><i class="fas fa-calendar"></i> ${photo.dateTaken}</span>` : ''}
                    ${photo.camera ? `<span><i class="fas fa-camera"></i> ${photo.camera}</span>` : ''}
                    ${photo.isRaw ? `<span><i class="fas fa-file-code"></i> RAW</span>` : ''}
                    ${photo.tags ? `
                        <div class="search-result-tags">
                            ${photo.tags.split(',').map(tag => 
                                `<span class="search-result-tag">${tag.trim()}</span>`
                            ).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Add click handler to scroll to photo
        item.addEventListener('click', () => {
            this.scrollToPhoto(photo.id);
            this.hideResults();
        });
        
        return item;
    }
    
    highlightSearchTerms(text, searchTerm) {
        if (!searchTerm) return text;
        
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<span class="' + this.options.highlightClass + '">$1</span>');
    }
    
    scrollToPhoto(photoId) {
        const photoElement = document.querySelector(`[data-photo-id="${photoId}"]`);
        if (photoElement) {
            photoElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
            
            // Add temporary highlight
            photoElement.style.outline = '3px solid var(--primary-default)';
            setTimeout(() => {
                photoElement.style.outline = '';
            }, 2000);
        }
    }
    
    updateSearchStats() {
        // Update or create stats display
        let statsElement = this.searchInput.parentNode.querySelector('.photo-search-stats');
        
        if (!statsElement) {
            statsElement = document.createElement('div');
            statsElement.className = 'photo-search-stats';
            this.searchInput.parentNode.appendChild(statsElement);
        }
        
        statsElement.innerHTML = `
            <span>${this.filteredPhotos.length} of ${this.allPhotos.length} photos</span>
            <button class="search-clear-btn" title="Clear search">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add clear button functionality
        const clearBtn = statsElement.querySelector('.search-clear-btn');
        clearBtn.addEventListener('click', () => {
            this.clearSearch();
        });
    }
    
    showAllPhotos() {
        this.allPhotos.forEach(photo => {
            photo.element.style.display = 'block';
        });
        
        // Hide no results message
        const noPhotosElement = this.photoGrid.querySelector('.no-photos');
        if (noPhotosElement) {
            noPhotosElement.style.display = 'none';
        }
    }
    
    clearSearch() {
        this.searchInput.value = '';
        this.currentSearchTerm = '';
        this.showAllPhotos();
        this.hideResults();
        this.hideInputLoading();
        
        // Remove stats
        this.removeSearchStats();
    }
    
    showResults() {
        if (this.resultsContainer) {
            this.resultsContainer.classList.add('active');
        }
    }
    
    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.classList.remove('active');
        }
    }
    
    removeSearchStats() {
        const statsElement = this.searchInput.parentNode.querySelector('.photo-search-stats');
        if (statsElement) {
            statsElement.remove();
        }
    }
    
    // Public method to refresh photos (useful when photos are dynamically added)
    refresh() {
        this.collectAllPhotos();
        if (this.currentSearchTerm) {
            this.performSearch(this.currentSearchTerm);
        } else {
            this.showAllPhotos();
            this.removeSearchStats();
        }
    }

    // Public method to destroy the component
    destroy() {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Remove event listeners
        this.searchInput.removeEventListener('input', this.handleSearchInput);
        this.searchInput.removeEventListener('keydown', this.handleKeydown);
        this.searchInput.removeEventListener('focus', this.handleFocus);
        
        // Note: Styles are now in external CSS file (photo-search.css)
    }
    
    showInputLoading() {
        if (this.searchInput && this.options.showLoadingInInput && !this.options.navbarMode) {
            const container = this.searchInput.closest('.photo-search-container');
            if (container) {
                container.classList.add('loading');
            }
        }
    }
    
    hideInputLoading() {
        if (this.searchInput && this.options.showLoadingInInput) {
            const container = this.searchInput.closest('.photo-search-container');
            if (container) {
                container.classList.remove('loading');
            }
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoSearch;
} else if (typeof window !== 'undefined') {
    window.PhotoSearch = PhotoSearch;
}
