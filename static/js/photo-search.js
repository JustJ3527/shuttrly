/**
 * Photo Search Component - Real-time search for photos
 * Reusable component that can be easily integrated into other templates
 * 
 * Features:
 * - Real-time search as you type
 * - Searches across multiple fields (title, description, tags, date)
 * - Debounced input to avoid excessive API calls
 * - Highlighted search results
 * - Responsive design using CSS variables from base.scss
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
            ...options
        };
        
        this.searchTimeout = null;
        this.currentSearchTerm = '';
        this.allPhotos = [];
        this.filteredPhotos = [];
        
        this.init();
    }
    
    init() {
        this.searchInput = document.querySelector(this.options.searchInputSelector);
        this.resultsContainer = document.querySelector(this.options.resultsContainerSelector);
        this.photoGrid = document.querySelector(this.options.photoGridSelector);
        
        if (!this.searchInput || !this.photoGrid) {
            console.warn('PhotoSearch: Required elements not found');
            return;
        }
        
        this.setupEventListeners();
        this.collectAllPhotos();
        this.setupStyles();
    }
    
    setupEventListeners() {
        // Real-time search input
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });
        
        // Clear search on escape key
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            }
        });
        
        // Focus management
        this.searchInput.addEventListener('focus', () => {
            this.showResults();
        });
        
        // Click outside to close results
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.resultsContainer.contains(e.target)) {
                this.hideResults();
            }
        });
    }
    
    setupStyles() {
        // Add custom styles if not already present
        if (!document.getElementById('photo-search-styles')) {
            const style = document.createElement('style');
            style.id = 'photo-search-styles';
            style.textContent = this.getCustomStyles();
            document.head.appendChild(style);
        }
    }
    
    getCustomStyles() {
        return `
            .photo-search-container {
                position: relative;
                margin-bottom: 1.5rem;
            }
            
            .photo-search-input {
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid var(--text-200);
                border-radius: 0.5rem;
                font-size: 1rem;
                background: var(--background-default);
                color: var(--text-default);
                transition: all 0.3s ease;
                font-family: 'Garet';
            }
            
            .photo-search-input:focus {
                outline: none;
                border-color: var(--primary-default);
                box-shadow: 0 0 0 3px rgba(81, 31%, 52%, 0.1);
            }
            
            .photo-search-input::placeholder {
                color: var(--text-400);
            }
            
            .photo-search-results {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: var(--background-default);
                border: 2px solid var(--text-200);
                border-top: none;
                border-radius: 0 0 0.5rem 0.5rem;
                max-height: 300px;
                overflow-y: auto;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                display: none;
            }
            
            .photo-search-results.active {
                display: block;
            }
            
            .search-result-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.75rem 1rem;
                border-bottom: 1px solid var(--text-200);
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .search-result-item:last-child {
                border-bottom: none;
            }
            
            .search-result-item:hover {
                background: var(--text-100);
            }
            
            .search-result-item.selected {
                background: var(--primary-100);
                color: var(--primary-default);
            }
            
            .search-result-thumbnail {
                width: 40px;
                height: 40px;
                border-radius: 0.25rem;
                object-fit: cover;
                flex-shrink: 0;
            }
            
            .search-result-info {
                flex: 1;
                min-width: 0;
            }
            
            .search-result-title {
                font-weight: 600;
                margin-bottom: 0.25rem;
                color: var(--text-default);
            }
            
            .search-result-meta {
                font-size: 0.875rem;
                color: var(--text-500);
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
            }
            
            .search-result-tags {
                display: flex;
                gap: 0.25rem;
                flex-wrap: wrap;
            }
            
            .search-result-tag {
                background: var(--primary-100);
                color: var(--primary-default);
                padding: 0.125rem 0.5rem;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .search-highlight {
                background: var(--primary-200);
                color: var(--primary-default);
                padding: 0.125rem 0.25rem;
                border-radius: 0.25rem;
                font-weight: 600;
            }
            
            .no-search-results {
                padding: 1rem;
                text-align: center;
                color: var(--text-500);
                font-style: italic;
            }
            
            .search-loading {
                padding: 1rem;
                text-align: center;
                color: var(--text-500);
            }
            
            .search-loading::after {
                content: '';
                display: inline-block;
                width: 1rem;
                height: 1rem;
                border: 2px solid var(--text-300);
                border-radius: 50%;
                border-top-color: var(--primary-default);
                animation: spin 1s linear infinite;
                margin-left: 0.5rem;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .photo-search-stats {
                margin-top: 0.5rem;
                font-size: 0.875rem;
                color: var(--text-500);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .search-clear-btn {
                background: none;
                border: none;
                color: var(--text-400);
                cursor: pointer;
                padding: 0.25rem;
                border-radius: 0.25rem;
                transition: all 0.2s ease;
            }
            
            .search-clear-btn:hover {
                color: var(--text-default);
                background: var(--text-100);
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .photo-search-results {
                    max-height: 250px;
                }
                
                .search-result-item {
                    padding: 0.5rem 0.75rem;
                }
                
                .search-result-thumbnail {
                    width: 35px;
                    height: 35px;
                }
            }
        `;
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
            const date = item.dataset.date || '';
            
            return {
                element: item,
                id: photoId,
                title: title,
                description: description,
                tags: tags,
                date: date,
                thumbnail: img?.src || '',
                searchText: `${title} ${description} ${tags} ${date}`.toLowerCase()
            };
        });
        
        this.filteredPhotos = [...this.allPhotos];
    }
    
    handleSearchInput(searchTerm) {
        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Set new timeout for debounced search
        this.searchTimeout = setTimeout(() => {
            this.performSearch(searchTerm);
        }, this.options.searchDelay);
    }
    
    performSearch(searchTerm) {
        this.currentSearchTerm = searchTerm.trim().toLowerCase();
        
        if (this.currentSearchTerm.length < this.options.minSearchLength) {
            this.showAllPhotos();
            this.hideResults();
            return;
        }
        
        // Filter photos based on search term
        this.filteredPhotos = this.allPhotos.filter(photo => 
            photo.searchText.includes(this.currentSearchTerm)
        );
        
        // Update display
        this.updatePhotoGrid();
        this.showSearchResults();
        
        // Update search stats
        this.updateSearchStats();
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
                    ${photo.date ? `<span><i class="fas fa-calendar"></i> ${photo.date}</span>` : ''}
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
        
        // Remove stats
        const statsElement = this.searchInput.parentNode.querySelector('.photo-search-stats');
        if (statsElement) {
            statsElement.remove();
        }
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
    
    // Public method to refresh photos (useful when photos are dynamically added)
    refresh() {
        this.collectAllPhotos();
        if (this.currentSearchTerm) {
            this.performSearch(this.currentSearchTerm);
        }
    }
    
    // Public method to destroy the component
    destroy() {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Remove event listeners
        this.searchInput.removeEventListener('input', this.handleSearchInput);
        this.searchInput.removeEventListener('keydown', this.handleSearchInput);
        this.searchInput.removeEventListener('focus', this.handleSearchInput);
        
        // Remove custom styles
        const customStyles = document.getElementById('photo-search-styles');
        if (customStyles) {
            customStyles.remove();
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoSearch;
} else if (typeof window !== 'undefined') {
    window.PhotoSearch = PhotoSearch;
}
