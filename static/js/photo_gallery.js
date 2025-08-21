        /**
        * VSCO-Style Photo Gallery JavaScript
        * Handles responsive masonry grid and interactive features
        * 
        * Features:
        * - Advanced column balancing algorithm targeting 9% max height variation
        * - Intelligent photo distribution with pre-calculated heights
        * - Maintains chronological order while optimizing layout
        * - Lazy loading with optimized loading strategies
        * - Responsive design with automatic column adjustment
        * - Debug mode for testing and optimization
        */

        // Configuration constants
        const CONFIG = {
            COLUMN_BREAKPOINTS: [
                { min: 0, max: 575, columns: 2 },
                { min: 576, max: 767, columns: 3 },
                { min: 768, max: 999, columns: 3 },
                { min: 1000, max: 1399, columns: 4 },
                { min: 1400, max: Infinity, columns: 5 }
            ],
            TARGET_VARIATION: 9,
            MAX_ITERATIONS: 100,
            RESIZE_DEBOUNCE: 100,
            LAYOUT_TRANSITION_DURATION: 300,
            LAZY_LOADING_BUFFER: 100,
            MAX_CONCURRENT_LOADS: 3,
            INITIAL_LOAD_DELAY: 50
        };

        // Utility functions
        const utils = {
            /**
            * Debounce function to limit function calls
            */
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
            },

            /**
            * Get CSRF token from various sources
            */
            getCSRFToken() {
                // Try input element first
                const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (inputToken) {
                    return inputToken.value;
                }

                // Fallback to cookie
                const cookieToken = utils.getCookie('csrftoken');
                if (cookieToken) {
                    return cookieToken;
                }

                // Fallback to meta tag
                const metaToken = document.querySelector('meta[name=csrf-token]');
                if (metaToken) {
                    return metaToken.getAttribute('content');
                }

                return '';
            },

            /**
            * Get cookie value by name
            */
            getCookie(name) {
                if (!document.cookie || document.cookie === '') {
                    return null;
                }

                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        return decodeURIComponent(cookie.substring(name.length + 1));
                    }
                }
                return null;
            },

            /**
            * Calculate height variation percentage between columns
            */
            calculateHeightVariation(columnHeights) {
                if (columnHeights.length === 0) return 0;
                
                const maxHeight = Math.max(...columnHeights);
                const minHeight = Math.min(...columnHeights);
                
                if (maxHeight === 0) return 0;
                
                return ((maxHeight - minHeight) / maxHeight) * 100;
            },

            /**
            * Estimate photo height based on aspect ratio and container width
            */
            estimatePhotoHeight(photoElement, columnWidth) {
                const img = photoElement.querySelector('img');
                if (!img) return 200;

                let aspectRatio = 1.0;

                // Try to get actual dimensions
                if (img.dataset.width && img.dataset.height) {
                    aspectRatio = parseInt(img.dataset.width) / parseInt(img.dataset.height);
                } else if (img.naturalWidth && img.naturalHeight) {
                    aspectRatio = img.naturalWidth / img.naturalHeight;
                } else {
                    // Use common photo ratios with weighted selection
                    const commonRatios = [
                        { ratio: 1.5, weight: 0.4 },   // Landscape (most common)
                        { ratio: 0.67, weight: 0.3 },  // Portrait
                        { ratio: 1.0, weight: 0.2 },   // Square
                        { ratio: 1.33, weight: 0.1 }   // Other
                    ];
                    
                    const random = Math.random();
                    let cumulativeWeight = 0;
                    for (const item of commonRatios) {
                        cumulativeWeight += item.weight;
                        if (random <= cumulativeWeight) {
                            aspectRatio = item.ratio;
                            break;
                        }
                    }
                }

                const padding = 20;
                const height = (columnWidth / aspectRatio) + padding;
                
                // Clamp height to reasonable bounds
                return Math.max(150, Math.min(800, height));
            }
        };

        // Notification system
        class NotificationManager {
            constructor() {
                this.init();
            }

            init() {
                this.addStyles();
            }

            addStyles() {
                const style = document.createElement('style');
                style.textContent = `
                    .notification {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
                        padding: 1rem 1.5rem;
                        transform: translateX(400px);
                        transition: transform 0.3s ease;
                        z-index: 9999;
                        max-width: 300px;
                    }
                    
                    .notification.show {
                        transform: translateX(0);
                    }
                    
                    .notification-content {
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                    }
                    
                    .notification-success {
                        border-left: 4px solid #28a745;
                    }
                    
                    .notification-success i {
                        color: #28a745;
                    }
                    
                    .notification-error {
                        border-left: 4px solid #dc3545;
                    }
                    
                    .notification-error i {
                        color: #dc3545;
                    }
                    
                    .photo-item.deleting {
                        opacity: 0;
                        transform: scale(0.8);
                        transition: all 0.3s ease;
                    }
                    
                    .masonry-grid.layout-transitioning {
                        opacity: 0.8;
                        transition: opacity 0.1s ease;
                    }
                    
                    .photo-item.fade-in {
                        animation: fadeIn 0.5s ease-in-out;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
                document.head.appendChild(style);
            }

            show(message, type = 'info') {
                const notification = document.createElement('div');
                notification.className = `notification notification-${type}`;
                notification.innerHTML = `
                    <div class="notification-content">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                        <span>${message}</span>
                    </div>
                `;

                document.body.appendChild(notification);

                // Show notification
                setTimeout(() => {
                    notification.classList.add('show');
                }, 100);

                // Hide and remove
                setTimeout(() => {
                    notification.classList.remove('show');
                    setTimeout(() => {
                        notification.remove();
                    }, 300);
                }, 3000);
            }
        }

        // Enhanced Lazy Loading Implementation
        class LazyImageLoader {
            constructor() {
                this.images = document.querySelectorAll('.lazy-image');
                this.loadingCount = 0;
                this.maxConcurrentLoads = CONFIG.MAX_CONCURRENT_LOADS;
                this.loadedImages = new Set();
                this.observer = null;
                this.isInitialized = false;
                this.debugMode = false;
                
                this.init();
            }
            
            init() {
                this.updateImages();
                
                if ('IntersectionObserver' in window) {
                    this.initIntersectionObserver();
                } else {
                    this.initFallback();
                }
                
                // Load first few images immediately for better UX
                this.loadInitialImages();
                
                this.isInitialized = true;
            }
            
            updateImages() {
                this.images = document.querySelectorAll('.lazy-image');
                if (this.debugMode) {
                    console.log(`Updated images list: ${this.images.length} images found`);
                }
            }
            
            reinitialize() {
                if (this.debugMode) {
                    console.log('Reinitializing LazyImageLoader...');
                }
                
                // Disconnect existing observer if any
                if (this.observer) {
                    this.observer.disconnect();
                    this.observer = null;
                }
                
                // Reset state
                this.loadedImages.clear();
                this.loadingCount = 0;
                
                // Update images list and reinitialize
                this.updateImages();
                
                if ('IntersectionObserver' in window) {
                    this.initIntersectionObserver();
                } else {
                    this.initFallback();
                }
                
                // Load initial images for new layout
                this.loadInitialImages();
                
                if (this.debugMode) {
                    console.log('LazyImageLoader reinitialized successfully');
                }
            }

            initIntersectionObserver() {
                this.observer = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            this.loadImage(img);
                            observer.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: `${CONFIG.LAZY_LOADING_BUFFER}px 0px`,
                    threshold: 0.01
                });

                this.images.forEach(img => this.observer.observe(img));
                
                if (this.debugMode) {
                    console.log('IntersectionObserver initialized');
                }
            }

            initFallback() {
                if (this.debugMode) {
                    console.log('Using fallback lazy loading');
                }
                this.loadVisibleImages();
                window.addEventListener('scroll', this.throttleScroll.bind(this));
            }

            loadInitialImages() {
                // Load first few images immediately for better initial experience
                const columnCount = window.photoGallery ? window.photoGallery.columnCount : 3;
                const initialCount = Math.min(columnCount * 2, 6);
                
                const initialImages = Array.from(this.images).slice(0, initialCount);
                
                if (this.debugMode) {
                    console.log(`Loading ${initialImages.length} initial images for ${columnCount} columns`);
                }
                
                initialImages.forEach((img, index) => {
                    if (!img.classList.contains('loaded') && !img.classList.contains('loading')) {
                        setTimeout(() => {
                            this.loadImage(img);
                        }, index * CONFIG.INITIAL_LOAD_DELAY);
                    }
                });
            }

            loadImage(img) {
                if (img.classList.contains('loaded') || img.classList.contains('loading')) {
                    return;
                }

                if (this.loadingCount >= this.maxConcurrentLoads) {
                    setTimeout(() => this.loadImage(img), 100);
                    return;
                }

                this.loadingCount++;
                img.classList.add('loading');

                const dataSrc = img.getAttribute('data-src');
                if (!dataSrc) {
                    console.warn('No data-src attribute found for image:', img);
                    this.loadingCount--;
                    return;
                }

                if (this.debugMode) {
                    console.log(`Loading image: ${dataSrc}`);
                }

                const tempImg = new Image();
                
                tempImg.onload = () => {
                    img.src = dataSrc;
                    img.classList.remove('loading');
                    img.classList.add('loaded');
                    this.loadedImages.add(img);
                    this.loadingCount--;
                    
                    // Add fade-in animation to photo item
                    const photoItem = img.closest('.photo-item');
                    if (photoItem) {
                        photoItem.classList.add('fade-in');
                        setTimeout(() => photoItem.classList.add('loaded'), 100);
                    }
                    
                    // Update loaded count
                    this.updateLoadedCount();
                    
                    // Trigger masonry layout update if needed
                    if (window.photoGallery && window.photoGallery.layoutMasonry) {
                        const currentWidth = window.photoGallery.grid.offsetWidth;
                        if (Math.abs(currentWidth - window.photoGallery.lastContainerWidth) > 100) {
                            window.photoGallery.layoutMasonry();
                        }
                    }
                };

                tempImg.onerror = () => {
                    img.classList.remove('loading');
                    this.loadingCount--;
                    console.warn('Failed to load image:', dataSrc);
                    
                    // Fallback to original file if thumbnail fails
                    const originalSrc = img.getAttribute('data-original');
                    if (originalSrc && originalSrc !== dataSrc) {
                        if (this.debugMode) {
                            console.log(`Trying fallback: ${originalSrc}`);
                        }
                        img.src = originalSrc;
                        img.classList.add('loaded');
                        this.loadedImages.add(img);
                        this.updateLoadedCount();
                    }
                };

                tempImg.src = dataSrc;
            }
            
            handleColumnChange() {
                if (this.debugMode) {
                    console.log('Handling column change in lazy loading...');
                }
                
                setTimeout(() => {
                    this.updateImages();
                    this.loadVisibleImages();
                    
                    if (this.observer) {
                        this.images.forEach(img => {
                            if (!img.classList.contains('loaded') && !img.classList.contains('loading')) {
                                this.observer.observe(img);
                            }
                        });
                    }
                    
                    this.updateLoadedCount();
                    
                    if (this.debugMode) {
                        console.log(`Lazy loading updated for new layout: ${this.images.length} images, ${this.loadedImages.size} loaded`);
                    }
                }, 200);
            }
            
            optimizeForColumns(columnCount) {
                if (this.debugMode) {
                    console.log(`Optimizing lazy loading for ${columnCount} columns`);
                }
                
                // Adjust loading strategy based on column count
                if (columnCount <= 2) {
                    this.maxConcurrentLoads = 4;
                } else if (columnCount <= 4) {
                    this.maxConcurrentLoads = 3;
                } else {
                    this.maxConcurrentLoads = 2;
                }
                
                if (this.debugMode) {
                    console.log(`Adjusted max concurrent loads to: ${this.maxConcurrentLoads}`);
                }
            }

            updateLoadedCount() {
                const loadedImages = this.loadedImages.size;
                const totalImages = this.images.length;
                const loadedCountElement = document.getElementById('loaded-count');
                
                if (loadedCountElement) {
                    loadedCountElement.textContent = loadedImages;
                    
                    if (loadedImages === totalImages) {
                        loadedCountElement.style.color = '#28a745';
                        loadedCountElement.innerHTML = `<i class="fas fa-check"></i> ${loadedImages}`;
                        if (this.debugMode) {
                            console.log('All images loaded successfully!');
                        }
                    }
                }
                
                if (this.debugMode) {
                    console.log(`Loaded: ${loadedImages}/${totalImages} images`);
                }
            }

            loadVisibleImages() {
                const windowHeight = window.innerHeight;
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

                this.images.forEach(img => {
                    if (img.classList.contains('loaded') || img.classList.contains('loading')) {
                        return;
                    }

                    const rect = img.getBoundingClientRect();
                    const isVisible = rect.top < windowHeight + 200;

                    if (isVisible) {
                        this.loadImage(img);
                    }
                });
            }
            
            throttleScroll() {
                if (this.scrollThrottle) return;
                this.scrollThrottle = true;
                
                setTimeout(() => {
                    this.loadVisibleImages();
                    this.scrollThrottle = false;
                }, 100);
            }
        }

        // Main Photo Gallery Class
        class PhotoGallery {
            constructor() {
                this.grid = document.getElementById('masonry-grid');
                this.currentPhotoId = null;
                this.resizeTimeout = null;
                this.columns = [];
                this.columnCount = 0;
                this.debugMode = false;
                this.photoOrder = [];
                this.isCreatingLayout = false;
                this.lastContainerWidth = 0;
                this.notificationManager = new NotificationManager();
                
                this.init();
            }
            
            init() {
                this.setupMasonryGrid();
                this.setupEventListeners();
                this.setupDeleteHandlers();
                
                // Force initial layout calculation after a short delay
                setTimeout(() => {
                    this.forceInitialLayout();
                }, 100);
            }
            
            setupMasonryGrid() {
                if (!this.grid) return;
                
                this.layoutMasonry();
                this.setupResizeHandlers();
                
                // Handle orientation change for mobile devices
                window.addEventListener('orientationchange', () => {
                    setTimeout(() => {
                        this.layoutMasonry();
                    }, 100);
                });
            }
            
            setupResizeHandlers() {
                const debouncedResize = utils.debounce(() => {
                    this.layoutMasonry();
                }, CONFIG.RESIZE_DEBOUNCE);
                
                // Multiple resize event listeners for better cross-browser support
                window.addEventListener('resize', debouncedResize, { passive: true });
                window.addEventListener('orientationchange', debouncedResize, { passive: true });
                
                // Handle viewport changes (useful for mobile browsers)
                if (window.visualViewport) {
                    window.visualViewport.addEventListener('resize', debouncedResize, { passive: true });
                }
                
                // Use ResizeObserver for more precise container size detection
                if (window.ResizeObserver) {
                    const resizeObserver = new ResizeObserver((entries) => {
                        for (let entry of entries) {
                            if (entry.target === this.grid) {
                                const newWidth = entry.contentRect.width;
                                if (Math.abs(newWidth - this.lastContainerWidth) > 50) {
                                    this.lastContainerWidth = newWidth;
                                    debouncedResize();
                                }
                            }
                        }
                    });
                    
                    if (this.grid) {
                        resizeObserver.observe(this.grid);
                    }
                }
                
                this.setupMediaQueryListeners();
                this.lastContainerWidth = this.grid ? this.grid.offsetWidth : 0;
            }
            
            setupMediaQueryListeners() {
                CONFIG.COLUMN_BREAKPOINTS.forEach(breakpoint => {
                    const mediaQuery = window.matchMedia(`(min-width: ${breakpoint.min}px) and (max-width: ${breakpoint.max}px)`);
                    
                    const handleChange = (e) => {
                        if (e.matches) {
                            if (this.debugMode) {
                                console.log(`Media query matched: ${breakpoint.min}px - ${breakpoint.max}px (${breakpoint.columns} columns)`);
                            }
                            this.handleBreakpointChange(breakpoint.columns);
                        }
                    };
                    
                    mediaQuery.addEventListener('change', handleChange);
                    
                    // Initial check
                    if (mediaQuery.matches) {
                        handleChange({ matches: true });
                    }
                });
            }
            
            handleBreakpointChange(newColumnCount) {
                if (this.columnCount !== newColumnCount) {
                    if (this.debugMode) {
                        console.log(`Breakpoint change detected: ${this.columnCount} → ${newColumnCount} columns`);
                    }
                    
                    this.showColumnChangeIndicator(this.columnCount, newColumnCount);
                    
                    if (this.photoOrder && this.photoOrder.length > 0) {
                        if (this.debugMode) {
                            console.log('Preserving photo order during breakpoint change...');
                            console.log('Current order before change:', this.photoOrder.map(item => item.photoId));
                        }
                    }
                    
                    this.columnCount = newColumnCount;
                    this.createColumnLayout();
                }
            }
            
            showColumnChangeIndicator(oldCount, newCount) {
                const indicator = document.createElement('div');
                indicator.className = 'column-change-indicator';
                indicator.innerHTML = `
                    <div class="indicator-content">
                        <i class="fas fa-columns"></i>
                        <span>${oldCount} → ${newCount} colonnes</span>
                    </div>
                `;
                
                document.body.appendChild(indicator);
                
                setTimeout(() => indicator.classList.add('show'), 100);
                setTimeout(() => {
                    indicator.classList.remove('show');
                    setTimeout(() => indicator.remove(), 300);
                }, 2000);
            }
            
            forceLayoutUpdate() {
                if (this.debugMode) {
                    console.log('Forcing layout update...');
                }
                this.layoutMasonry();
            }
            
            forceInitialLayout() {
                if (this.debugMode) {
                    console.log('Forcing initial layout calculation...');
                }
                
                this.columnCount = 0;
                this.layoutMasonry();
                
                setTimeout(() => {
                    if (this.debugMode) {
                        console.log('Double-checking layout after images load...');
                    }
                    this.layoutMasonry();
                }, 500);
            }
            
            optimizeColumns(targetVariation = CONFIG.TARGET_VARIATION) {
                if (this.debugMode) {
                    console.log(`Manual column optimization triggered with target variation: ${targetVariation}%`);
                }
                
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const currentPhotos = Array.from(document.querySelectorAll('.photo-item'));
                
                if (currentPhotos.length === 0) {
                    console.warn('No photos to optimize');
                    return;
                }
                
                const tempPhotoOrder = currentPhotos.map((photo, index) => ({
                    element: photo,
                    originalIndex: index,
                    photoId: photo.dataset.photoId || `temp_${index}`,
                    currentPosition: index
                }));
                
                const originalPhotoOrder = this.photoOrder;
                this.photoOrder = tempPhotoOrder;
                
                this.columns.forEach(column => {
                    column.innerHTML = '';
                });
                
                const distributionResult = this.calculateOptimalDistributionWithTarget(tempPhotoOrder, targetVariation);
                
                if (this.debugMode) {
                    console.log('Optimization result:', distributionResult);
                }
                
                this.applyOptimizedDistribution(distributionResult);
                this.photoOrder = originalPhotoOrder;
                
                setTimeout(() => {
                    window.scrollTo(0, scrollTop);
                }, 200);
                
                if (this.debugMode) {
                    console.log(`Manual column optimization completed. Target: ${targetVariation}%, Achieved: ${distributionResult.finalVariation.toFixed(1)}%`);
                }
            }
            
            getLayoutInfo() {
                return {
                    columnCount: this.columnCount,
                    containerWidth: this.grid ? this.grid.offsetWidth : 0,
                    viewportWidth: window.innerWidth,
                    isMobile: window.innerWidth <= 575,
                    isTablet: window.innerWidth > 575 && window.innerWidth <= 1199,
                    isDesktop: window.innerWidth >= 1200,
                    columns: this.columns.length,
                    photosPerColumn: this.columns.map(col => col.querySelectorAll('.photo-item').length),
                    columnHeights: this.columns.map(col => {
                        const photos = col.querySelectorAll('.photo-item');
                        let totalHeight = 0;
                        photos.forEach(photo => {
                            totalHeight += this.estimatePhotoHeight(photo);
                        });
                        return Math.round(totalHeight);
                    })
                };
            }
            
            setDebugMode(enabled) {
                this.debugMode = enabled;
                console.log(`Debug mode ${enabled ? 'enabled' : 'disabled'}`);
                
                if (window.lazyLoader) {
                    window.lazyLoader.debugMode = enabled;
                }
            }
            
            layoutMasonry() {
                if (!this.grid) return;
                
                const containerWidth = this.grid.offsetWidth;
                const viewportWidth = window.innerWidth;
                
                if (containerWidth === 0) {
                    if (this.debugMode) {
                        console.log('Container width is 0, waiting for proper measurement...');
                    }
                    setTimeout(() => this.layoutMasonry(), 50);
                    return;
                }
                
                const isMobile = viewportWidth <= 575;
                const isTablet = viewportWidth > 575 && viewportWidth <= 1199;
                const isDesktop = viewportWidth >= 1200;
                
                const columnCount = this.calculateOptimalColumnCount(containerWidth, viewportWidth, isMobile, isTablet, isDesktop);
                
                if (this.debugMode) {
                    console.log(`Layout calculation: container=${containerWidth}px, viewport=${viewportWidth}px, calculated=${columnCount} columns, current=${this.columnCount} columns`);
                }
                
                if (this.columnCount !== columnCount || !this.columns || this.columns.length === 0) {
                    if (this.debugMode) {
                        console.log(`Column count changed from ${this.columnCount} to ${columnCount} (container: ${containerWidth}px, viewport: ${viewportWidth}px)`);
                    }
                    this.columnCount = columnCount;
                    this.createColumnLayout();
                }
                
                this.updateCSSProperties(columnCount, containerWidth, viewportWidth);
                
                if (this.photoOrder && this.photoOrder.length > 0 && this.debugMode) {
                    setTimeout(() => {
                        this.verifyPhotoOrder();
                    }, 500);
                }
            }
            
            calculateOptimalColumnCount(containerWidth, viewportWidth, isMobile, isTablet, isDesktop) {
                if (containerWidth >= 1400) return 5;
                if (containerWidth >= 1000) return 4;
                if (containerWidth >= 768) return 3;
                if (containerWidth >= 576) return 2;
                
                if (isMobile) {
                    return 2;
                } else if (isTablet) {
                    return containerWidth >= 900 ? 3 : 2;
                } else {
                    return containerWidth >= 1000 ? 4 : 3;
                }
            }
            
            updateCSSProperties(columnCount, containerWidth, viewportWidth) {
                this.grid.style.setProperty('--column-count', columnCount);
                this.grid.style.setProperty('--container-width', `${containerWidth}px`);
                this.grid.style.setProperty('--viewport-width', `${viewportWidth}px`);
                
                this.grid.classList.remove('mobile-layout', 'tablet-layout', 'desktop-layout');
                if (viewportWidth <= 575) {
                    this.grid.classList.add('mobile-layout');
                } else if (viewportWidth <= 1199) {
                    this.grid.classList.add('tablet-layout');
                } else {
                    this.grid.classList.add('desktop-layout');
                }
            }
            
            createColumnLayout() {
                if (!this.grid) return;
                
                if (this.isCreatingLayout) {
                    if (this.debugMode) {
                        console.log('Layout creation already in progress, skipping');
                    }
                    return;
                }
                
                this.isCreatingLayout = true;
                
                if (this.debugMode) {
                    console.log(`Creating column layout with ${this.columnCount} columns`);
                }
                
                this.grid.classList.add('layout-transitioning');
                
                const photoItems = document.querySelectorAll('.photo-item');
                if (this.debugMode) {
                    console.log(`Found ${photoItems.length} photos to distribute`);
                }
                
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                this.storePhotoOrder(photoItems);
                
                this.grid.innerHTML = '';
                this.columns = [];
                
                // Create columns with staggered animation
                for (let i = 0; i < this.columnCount; i++) {
                    const column = document.createElement('div');
                    column.className = 'photo-column';
                    column.setAttribute('data-column', i + 1);
                    column.style.opacity = '0';
                    column.style.transform = 'translateY(20px)';
                    
                    this.columns.push(column);
                    this.grid.appendChild(column);
                    
                    setTimeout(() => {
                        column.style.transition = 'all 0.3s ease';
                        column.style.opacity = '1';
                        column.style.transform = 'translateY(0)';
                    }, i * 50);
                }
                
                this.distributePhotosToColumns(photoItems);
                
                setTimeout(() => {
                    window.scrollTo(0, scrollTop);
                    this.grid.classList.remove('layout-transitioning');
                    this.isCreatingLayout = false;
                    this.relaunchLazyLoading();
                }, CONFIG.LAYOUT_TRANSITION_DURATION);
            }
            
            storePhotoOrder(photoItems) {
                const currentOrder = Array.from(photoItems).map((photo, index) => ({
                    element: photo,
                    originalIndex: index,
                    photoId: photo.dataset.photoId,
                    title: photo.querySelector('.photo-title')?.textContent || '',
                    date: photo.dataset.date || '',
                    currentPosition: index
                }));
                
                if (this.photoOrder && this.photoOrder.length > 0) {
                    if (this.debugMode) {
                        console.log('Preserving existing photo order during layout change');
                    }
                    this.photoOrder = this.photoOrder.map((storedItem, index) => {
                        const currentItem = currentOrder.find(item => item.photoId === storedItem.photoId);
                        if (currentItem) {
                            return {
                                ...storedItem,
                                element: currentItem.element,
                                currentPosition: currentItem.currentPosition
                            };
                        }
                        return storedItem;
                    });
                } else {
                    this.photoOrder = currentOrder;
                }
                
                if (this.debugMode) {
                    console.log(`Stored photo order: ${this.photoOrder.length} photos`);
                    console.log('Photo order details:', this.photoOrder.map(item => ({
                        photoId: item.photoId,
                        originalIndex: item.originalIndex,
                        currentPosition: item.currentPosition
                    })));
                }
            }
            
            addPhotosToGrid(newPhotos) {
                if (!this.columns || this.columns.length === 0) {
                    console.warn('Columns not initialized, creating layout first');
                    this.createColumnLayout();
                    return;
                }
                
                if (!newPhotos || newPhotos.length === 0) {
                    if (this.debugMode) {
                        console.log('No new photos to add');
                    }
                    return;
                }
                
                if (this.debugMode) {
                    console.log(`Adding ${newPhotos.length} new photos using advanced column balancing algorithm`);
                }
                
                const currentPhotos = Array.from(document.querySelectorAll('.photo-item'));
                const allPhotos = [...currentPhotos, ...newPhotos];
                
                const tempPhotoOrder = allPhotos.map((photo, index) => ({
                    element: photo,
                    originalIndex: index,
                    photoId: photo.dataset.photoId || `temp_${index}`,
                    currentPosition: index
                }));
                
                const originalPhotoOrder = this.photoOrder;
                this.photoOrder = tempPhotoOrder;
                
                this.optimizeColumns(CONFIG.TARGET_VARIATION);
                this.photoOrder = originalPhotoOrder;
                
                this.setupEventListeners();
                this.setupDeleteHandlers();
                this.relaunchLazyLoading();
                
                if (this.debugMode) {
                    console.log('Advanced photo redistribution completed for new photos');
                }
            }
            
            relaunchLazyLoading() {
                if (this.debugMode) {
                    console.log('Relaunching lazy loading for new layout...');
                }
                
                setTimeout(() => {
                    if (window.lazyLoader) {
                        window.lazyLoader.handleColumnChange();
                        window.lazyLoader.optimizeForColumns(this.columnCount);
                        
                        setTimeout(() => {
                            this.updateColumnHeightsAfterImageLoad();
                        }, 1000);
                    } else {
                        if (this.debugMode) {
                            console.log('Creating new LazyImageLoader...');
                        }
                        window.lazyLoader = new LazyImageLoader();
                        window.lazyLoader.debugMode = this.debugMode;
                        
                        if (window.lazyLoader.optimizeForColumns) {
                            window.lazyLoader.optimizeForColumns(this.columnCount);
                        }
                        
                        setTimeout(() => {
                            this.updateColumnHeightsAfterImageLoad();
                        }, 1000);
                    }
                }, 100);
            }
            
            distributePhotosToColumns(photoItems = null) {
                if (!this.columns || this.columns.length === 0) {
                    console.warn('Columns not initialized, creating layout first');
                    this.createColumnLayout();
                    return;
                }
                
                if (this.columns.some(col => col.querySelector('.photo-item'))) {
                    if (this.debugMode) {
                        console.log('Photos already distributed, skipping');
                    }
                    return;
                }
                
                if (!photoItems) {
                    photoItems = document.querySelectorAll('.photo-item');
                }
                
                if (!photoItems || photoItems.length === 0) {
                    if (this.debugMode) {
                        console.log('No photos to distribute');
                    }
                    return;
                }
                
                if (this.debugMode) {
                    console.log(`Distributing ${photoItems.length} photos to ${this.columnCount} columns using advanced balancing algorithm`);
                }
                
                if (!this.photoOrder || this.photoOrder.length === 0) {
                    console.error('No photo order stored! Cannot distribute photos correctly.');
                    return;
                }
                
                if (this.debugMode) {
                    console.log('Using stored photo order for distribution:');
                    this.photoOrder.forEach((item, index) => {
                        console.log(`  ${index + 1}. Photo ID: ${item.photoId}, Original Index: ${item.originalIndex}`);
                    });
                }
                
                const distributionResult = this.calculateOptimalDistribution(this.photoOrder);
                
                if (this.debugMode) {
                    console.log('Optimal distribution calculated:', distributionResult);
                }
                
                const columnFragments = Array.from({ length: this.columnCount }, () => document.createDocumentFragment());
                
                distributionResult.columnAssignments.forEach((columnIndex, photoIndex) => {
                    const photoData = this.photoOrder[photoIndex];
                    const photoClone = photoData.element.cloneNode(true);
                    
                    photoClone.dataset.originalIndex = photoData.originalIndex;
                    photoClone.dataset.photoId = photoData.photoId;
                    photoClone.dataset.currentPosition = photoData.currentPosition;
                    photoClone.dataset.columnIndex = columnIndex;
                    photoClone.classList.add('loading');
                    
                    columnFragments[columnIndex].appendChild(photoClone);
                    
                    if (this.debugMode) {
                        console.log(`Photo ${photoData.photoId} (original index: ${photoData.originalIndex}) → Column ${columnIndex + 1}`);
                    }
                });
                
                columnFragments.forEach((colFragment, colIndex) => {
                    if (colFragment.children.length > 0) {
                        this.columns[colIndex].appendChild(colFragment);
                    }
                });
                
                if (this.debugMode) {
                    console.log('Final distribution statistics:');
                    console.log(`  Target variation: ${CONFIG.TARGET_VARIATION}%`);
                    console.log(`  Achieved variation: ${distributionResult.finalVariation.toFixed(1)}%`);
                    console.log(`  Column heights:`, distributionResult.finalHeights.map(h => `${h.toFixed(1)}px`));
                    console.log(`  Distribution quality: ${distributionResult.finalVariation <= CONFIG.TARGET_VARIATION ? '✅ EXCELLENT' : distributionResult.finalVariation <= 15 ? '⚠️ GOOD' : '❌ NEEDS IMPROVEMENT'}`);
                }
                
                setTimeout(() => {
                    const newPhotos = document.querySelectorAll('.photo-item.loading');
                    newPhotos.forEach((photo, index) => {
                        requestAnimationFrame(() => {
                            photo.classList.remove('loading');
                            photo.classList.add('loaded');
                        });
                    });
                }, 50);
                
                this.setupEventListeners();
                this.setupDeleteHandlers();
                
                if (this.debugMode) {
                    this.logPhotoDistribution();
                }
            }
            
            // Advanced distribution algorithm targeting 9% max variation
            calculateOptimalDistribution(photoOrder) {
                const targetVariation = CONFIG.TARGET_VARIATION;
                const maxIterations = CONFIG.MAX_ITERATIONS;
                
                const photoHeights = this.calculateAccuratePhotoHeights(photoOrder);
                
                if (this.debugMode) {
                    console.log('Pre-calculated photo heights:', photoHeights.map(h => `${h.toFixed(1)}px`));
                }
                
                let columnHeights = new Array(this.columnCount).fill(0);
                let columnAssignments = [];
                
                // First pass: distribute photos to shortest columns
                photoOrder.forEach((photoData, index) => {
                    let shortestColumnIndex = 0;
                    let minHeight = columnHeights[0];
                    
                    for (let i = 1; i < this.columnCount; i++) {
                        if (columnHeights[i] < minHeight) {
                            minHeight = columnHeights[i];
                            shortestColumnIndex = i;
                        }
                    }
                    
                    columnAssignments[index] = shortestColumnIndex;
                    columnHeights[shortestColumnIndex] += photoHeights[index];
                });
                
                let currentVariation = utils.calculateHeightVariation(columnHeights);
                
                if (this.debugMode) {
                    console.log(`Initial distribution - Variation: ${currentVariation.toFixed(1)}%`);
                    console.log('Initial column heights:', columnHeights.map(h => `${h.toFixed(1)}px`));
                }
                
                if (currentVariation <= targetVariation) {
                    if (this.debugMode) {
                        console.log('✅ Initial distribution already meets target variation!');
                    }
                    return {
                        columnAssignments,
                        finalHeights: columnHeights,
                        finalVariation: currentVariation,
                        iterations: 0
                    };
                }
                
                let iterations = 0;
                let bestVariation = currentVariation;
                let bestDistribution = [...columnAssignments];
                let bestHeights = [...columnHeights];
                
                while (currentVariation > targetVariation && iterations < maxIterations) {
                    iterations++;
                    let improved = false;
                    
                    // Try swapping photos between columns to improve balance
                    for (let i = 0; i < photoOrder.length && !improved; i++) {
                        for (let j = i + 1; j < photoOrder.length && !improved; j++) {
                            const currentCol1 = columnAssignments[i];
                            const currentCol2 = columnAssignments[j];
                            
                            if (currentCol1 === currentCol2) continue;
                            
                            const tempHeights = [...columnHeights];
                            tempHeights[currentCol1] = tempHeights[currentCol1] - photoHeights[i] + photoHeights[j];
                            tempHeights[currentCol2] = tempHeights[currentCol2] - photoHeights[j] + photoHeights[i];
                            
                            const newVariation = utils.calculateHeightVariation(tempHeights);
                            
                            if (newVariation < currentVariation) {
                                columnAssignments[i] = currentCol2;
                                columnAssignments[j] = currentCol1;
                                columnHeights = tempHeights;
                                currentVariation = newVariation;
                                improved = true;
                                
                                if (this.debugMode) {
                                    console.log(`Iteration ${iterations}: Swapped photos ${i} and ${j}, new variation: ${newVariation.toFixed(1)}%`);
                                }
                                
                                if (newVariation < bestVariation) {
                                    bestVariation = newVariation;
                                    bestDistribution = [...columnAssignments];
                                    bestHeights = [...columnHeights];
                                }
                                
                                if (newVariation <= targetVariation) {
                                    if (this.debugMode) {
                                        console.log(`✅ Target variation of ${targetVariation}% reached after ${iterations} iterations!`);
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    
                    // If no improvement found, try more aggressive optimization
                    if (!improved) {
                        const tallestColumn = columnHeights.indexOf(Math.max(...columnHeights));
                        const shortestColumn = columnHeights.indexOf(Math.min(...columnHeights));
                        
                        for (let i = 0; i < photoOrder.length; i++) {
                            if (columnAssignments[i] === tallestColumn) {
                                const tempHeights = [...columnHeights];
                                tempHeights[tallestColumn] -= photoHeights[i];
                                tempHeights[shortestColumn] += photoHeights[i];
                                
                                const newVariation = utils.calculateHeightVariation(tempHeights);
                                
                                if (newVariation < currentVariation) {
                                    columnAssignments[i] = shortestColumn;
                                    columnHeights = tempHeights;
                                    currentVariation = newVariation;
                                    improved = true;
                                    
                                    if (this.debugMode) {
                                        console.log(`Iteration ${iterations}: Moved photo ${i} from tallest to shortest column, new variation: ${newVariation.toFixed(1)}%`);
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (!improved) {
                        if (this.debugMode) {
                            console.log(`No more improvements possible after ${iterations} iterations`);
                        }
                        break;
                    }
                }
                
                if (bestVariation < currentVariation) {
                    if (this.debugMode) {
                        console.log(`Using best distribution found: variation ${bestVariation.toFixed(1)}% (vs current ${currentVariation.toFixed(1)}%)`);
                    }
                    columnAssignments = bestDistribution;
                    columnHeights = bestHeights;
                    currentVariation = bestVariation;
                }
                
                if (this.debugMode) {
                    console.log(`Optimization completed in ${iterations} iterations`);
                    console.log(`Final variation: ${currentVariation.toFixed(1)}% (target: ${targetVariation}%)`);
                }
                
                return {
                    columnAssignments,
                    finalHeights: columnHeights,
                    finalVariation: currentVariation,
                    iterations
                };
            }
            
            calculateAccuratePhotoHeights(photoOrder) {
                const containerWidth = this.grid ? this.grid.offsetWidth : window.innerWidth;
                const columnWidth = containerWidth / this.columnCount;
                const heights = [];
                
                photoOrder.forEach((photoData) => {
                    const img = photoData.element.querySelector('img');
                    let height = 200;
                    
                    if (img) {
                        if (img.naturalWidth && img.naturalHeight && img.naturalWidth > 0) {
                            const aspectRatio = img.naturalWidth / img.naturalHeight;
                            height = (columnWidth / aspectRatio) + 20;
                        } else if (img.dataset.width && img.dataset.height) {
                            const aspectRatio = parseInt(img.dataset.width) / parseInt(img.dataset.height);
                            height = (columnWidth / aspectRatio) + 20;
                        } else {
                            height = utils.estimatePhotoHeight(photoData.element, columnWidth);
                        }
                    }
                    
                    height = Math.max(150, Math.min(800, height));
                    heights.push(height);
                });
                
                return heights;
            }
            
            estimatePhotoHeight(photoElement) {
                const containerWidth = this.grid ? this.grid.offsetWidth : window.innerWidth;
                const columnWidth = containerWidth / this.columnCount;
                return utils.estimatePhotoHeight(photoElement, columnWidth);
            }
            
            updateColumnHeightsAfterImageLoad() {
                if (!this.columns || this.columns.length === 0) return;
                
                setTimeout(() => {
                    const columnHeights = new Array(this.columnCount).fill(0);
                    
                    this.columns.forEach((column, colIndex) => {
                        const photos = column.querySelectorAll('.photo-item');
                        photos.forEach(photo => {
                            const img = photo.querySelector('img');
                            if (img && img.classList.contains('loaded')) {
                                let height = 200;
                                
                                if (img.naturalHeight && img.naturalWidth) {
                                    const containerWidth = this.grid ? this.grid.offsetWidth : window.innerWidth;
                                    const columnWidth = containerWidth / this.columnCount;
                                    const aspectRatio = img.naturalWidth / img.naturalHeight;
                                    height = (columnWidth / aspectRatio) + 20;
                                } else {
                                    height = this.estimatePhotoHeight(photo);
                                }
                                
                                columnHeights[colIndex] += height;
                            }
                        });
                    });
                    
                    if (this.debugMode) {
                        console.log('Updated column heights after image load:');
                        columnHeights.forEach((height, index) => {
                            console.log(`  Column ${index + 1}: ${height.toFixed(1)}px`);
                        });
                        
                        const maxHeight = Math.max(...columnHeights);
                        const minHeight = Math.min(...columnHeights);
                        const heightDifference = maxHeight - minHeight;
                        console.log(`Height difference: ${heightDifference.toFixed(1)}px (${((heightDifference / maxHeight) * 100).toFixed(1)}% variation)`);
                    }
                }, 500);
            }
            
            logPhotoDistribution() {
                if (!this.columns || this.columns.length === 0) return;
                
                if (this.debugMode) {
                    console.log('📊 Current Photo Distribution:');
                    this.columns.forEach((column, colIndex) => {
                        const photos = column.querySelectorAll('.photo-item');
                        const photoIds = Array.from(photos).map(photo => photo.dataset.photoId || 'N/A');
                        console.log(`Column ${colIndex + 1}: ${photos.length} photos - IDs: [${photoIds.join(', ')}]`);
                    });
                    
                    const totalPhotos = this.columns.reduce((total, col) => total + col.querySelectorAll('.photo-item').length, 0);
                    const expectedRows = Math.ceil(totalPhotos / this.columnCount);
                    console.log(`Expected rows: ${expectedRows}, Total photos: ${totalPhotos}, Columns: ${this.columnCount}`);
                }
            }
            
            redistributePhotosAfterDelete() {
                if (!this.columns || this.columns.length === 0) {
                    console.warn('Columns not initialized during delete redistribution');
                    return;
                }
                
                const remainingPhotos = Array.from(document.querySelectorAll('.photo-item:not(.deleting)'));
                
                if (remainingPhotos.length === 0) {
                    if (this.debugMode) {
                        console.log('No remaining photos after delete');
                    }
                    return;
                }
                
                if (this.debugMode) {
                    console.log(`Redistributing ${remainingPhotos.length} remaining photos after delete using advanced balancing algorithm`);
                }
                
                this.updatePhotoOrderAfterDelete(remainingPhotos);
                this.optimizeColumns(CONFIG.TARGET_VARIATION);
            }
            
            updatePhotoOrderAfterDelete(remainingPhotos) {
                if (!this.photoOrder) return;
                
                const remainingPhotoIds = new Set(remainingPhotos.map(photo => photo.dataset.photoId));
                
                this.photoOrder = this.photoOrder.filter(item => 
                    remainingPhotoIds.has(item.photoId)
                );
                
                this.photoOrder.forEach((item, newIndex) => {
                    item.originalIndex = newIndex;
                });
                
                if (this.debugMode) {
                    console.log(`Updated photo order after delete: ${this.photoOrder.length} photos remaining`);
                }
            }
            
            verifyPhotoOrder() {
                if (!this.photoOrder || !this.columns) return false;
                
                if (!this.debugMode) return true;
                
                const currentPhotos = [];
                this.columns.forEach(column => {
                    const photos = column.querySelectorAll('.photo-item');
                    photos.forEach(photo => {
                        currentPhotos.push({
                            id: photo.dataset.photoId,
                            column: column.dataset.column,
                            originalIndex: photo.dataset.originalIndex,
                            currentPosition: photo.dataset.currentPosition,
                            element: photo
                        });
                    });
                });
                
                const storedIds = this.photoOrder.map(item => item.photoId);
                const currentIds = currentPhotos.map(item => item.id);
                
                const isOrderMaintained = storedIds.every((id, index) => id === currentIds[index]);
                
                if (!isOrderMaintained) {
                    console.warn('⚠️ Photo order mismatch detected!');
                    console.log('Stored order:', storedIds);
                    console.log('Current order:', currentIds);
                    
                    console.log('Detailed mismatch analysis:');
                    storedIds.forEach((storedId, index) => {
                        const currentId = currentIds[index];
                        if (storedId !== currentId) {
                            if (this.debugMode) {
                                console.warn(`  Position ${index + 1}: Expected ${storedId}, Got ${currentId}`);
                            }
                        }
                    });
                } else {
                    console.log('✅ Photo order verified and maintained correctly');
                    console.log('Order verification details:');
                    currentPhotos.forEach((photo, index) => {
                        console.log(`  ${index + 1}. Photo ID: ${photo.id}, Column: ${photo.column}, Original Index: ${photo.originalIndex}`);
                    });
                }
                
                return isOrderMaintained;
            }
            
            setupEventListeners() {
                // Photo item click events - use event delegation for better performance
                this.grid.addEventListener('click', (e) => {
                    const photoItem = e.target.closest('.photo-item');
                    if (!photoItem) return;
                    
                    // Don't trigger if clicking on buttons or links
                    if (e.target.closest('.photo-actions') || e.target.closest('a')) {
                        return;
                    }
                    
                    // Check if photo selection mode is active - if so, don't redirect
                    if (window.photoSelection && window.photoSelection.isInSelectionMode()) {
                        return;
                    }
                    
                    // Open photo detail only if not in selection mode
                    const photoId = photoItem.dataset.photoId;
                    if (photoId) {
                        window.location.href = `/photos/photo/${photoId}/`;
                    }
                });
            }
            
            handleKeyboardNavigation(e) {
                const focusedItem = document.querySelector('.photo-item:focus-within');
                if (!focusedItem) return;
                
                const currentIndex = Array.from(this.photoItems).indexOf(focusedItem);
                let nextIndex = currentIndex;
                
                switch (e.key) {
                    case 'ArrowRight':
                        nextIndex = Math.min(currentIndex + 1, this.photoItems.length - 1);
                        break;
                    case 'ArrowLeft':
                        nextIndex = Math.max(currentIndex - 1, 0);
                        break;
                    case 'ArrowDown':
                        const columnCount = parseInt(this.grid.style.getPropertyValue('--column-count')) || 4;
                        nextIndex = Math.min(currentIndex + columnCount, this.photoItems.length - 1);
                        break;
                    case 'ArrowUp':
                        const colCount = parseInt(this.grid.style.getPropertyValue('--column-count')) || 4;
                        nextIndex = Math.max(currentIndex - colCount, 0);
                        break;
                    case 'Enter':
                    case ' ':
                        if (window.photoSelection && window.photoSelection.isInSelectionMode()) {
                            return;
                        }
                        
                        const photoId = focusedItem.dataset.photoId;
                        if (photoId) {
                            window.location.href = `/photos/photo/${photoId}/`;
                        }
                        e.preventDefault();
                        return;
                    default:
                        return;
                }
                
                if (nextIndex !== currentIndex) {
                    this.photoItems[nextIndex].focus();
                    this.scrollToPhoto(this.photoItems[nextIndex]);
                }
            }
            
            scrollToPhoto(photoItem) {
                const rect = photoItem.getBoundingClientRect();
                const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;
                
                if (!isVisible) {
                    photoItem.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            }
            
            setupDeleteHandlers() {
                // Delete photo buttons - use event delegation
                this.grid.addEventListener('click', (e) => {
                    const deleteBtn = e.target.closest('.delete-photo');
                    if (!deleteBtn) return;
                    
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const photoId = deleteBtn.dataset.photoId;
                    if (photoId) {
                        this.showDeleteModal(photoId);
                    }
                });
                
                // Delete confirmation
                const confirmDeleteBtn = document.getElementById('confirmDelete');
                if (confirmDeleteBtn) {
                    confirmDeleteBtn.addEventListener('click', () => {
                        this.deletePhoto();
                    });
                }
            }
            
            showDeleteModal(photoId) {
                this.currentPhotoId = photoId;
                
                if (typeof bootstrap === 'undefined') {
                    if (this.debugMode) {
                        console.error('Bootstrap is not available for modal');
                        alert('Error: Bootstrap not loaded. Please refresh the page.');
                    }
                    return;
                }
                
                try {
                    const modalElement = document.getElementById('deletePhotoModal');
                    if (!modalElement) {
                        if (this.debugMode) {
                            console.error('Modal element not found');
                        }
                        return;
                    }
                    
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                    if (this.debugMode) {
                        console.log('Modal shown successfully');
                    }
                } catch (error) {
                    if (this.debugMode) {
                        console.error('Error showing modal:', error);
                    }
                    alert('Error showing delete confirmation. Please try again.');
                }
            }
            
            async deletePhoto() {
                if (!this.currentPhotoId) return;
                
                try {
                    const csrfToken = utils.getCSRFToken();
                    if (this.debugMode) {
                        console.log('CSRF token retrieved:', csrfToken ? 'Yes' : 'No');
                    }
                    
                    if (!csrfToken) {
                        if (this.debugMode) {
                            console.error('CSRF token not found. Available elements:');
                            console.log('CSRF input:', document.querySelector('[name=csrfmiddlewaretoken]'));
                            console.log('CSRF cookie:', utils.getCookie('csrftoken'));
                            console.log('CSRF meta:', document.querySelector('meta[name=csrf-token]'));
                        }
                        throw new Error('CSRF token not found. Please refresh the page and try again.');
                    }
                    
                    const deleteUrl = `/photos/photo/${this.currentPhotoId}/delete/`;
                    if (this.debugMode) {
                        console.log(`Attempting to delete photo ${this.currentPhotoId} with CSRF token: ${csrfToken.substring(0, 10)}...`);
                        console.log(`Delete URL: ${deleteUrl}`);
                    }
                    
                    const response = await fetch(deleteUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (this.debugMode) {
                        console.log(`Delete response status: ${response.status}`);
                        console.log(`Delete response headers:`, Object.fromEntries(response.headers.entries()));
                    }
                    
                    if (response.ok) {
                        // Remove photo from DOM
                        const photoItems = document.querySelectorAll(`[data-photo-id="${this.currentPhotoId}"]`);
                        photoItems.forEach(photoItem => {
                            photoItem.classList.add('deleting');
                            setTimeout(() => {
                                photoItem.remove();
                                this.redistributePhotosAfterDelete();
                            }, 300);
                        });
                        
                        // Close modal
                        try {
                            const modalElement = document.getElementById('deletePhotoModal');
                            if (modalElement) {
                                const modal = bootstrap.Modal.getInstance(modalElement);
                                if (modal) {
                                    modal.hide();
                                    if (this.debugMode) {
                                        console.log('Modal closed successfully');
                                    }
                                } else {
                                    console.warn('Modal instance not found, trying to hide manually');
                                    modalElement.classList.remove('show');
                                    modalElement.style.display = 'none';
                                    document.body.classList.remove('modal-open');
                                    const backdrop = document.querySelector('.modal-backdrop');
                                    if (backdrop) backdrop.remove();
                                }
                            }
                        } catch (error) {
                            if (this.debugMode) {
                                console.error('Error closing modal:', error);
                            }
                        }
                        
                        // Show success message
                        this.notificationManager.show('Photo deleted successfully', 'success');
                        
                    } else {
                        let errorMessage = 'Failed to delete photo';
                        try {
                            const errorData = await response.json();
                            errorMessage = errorData.message || errorMessage;
                        } catch (e) {
                            try {
                                const errorText = await response.text();
                                if (errorText) {
                                    errorMessage = `Server error: ${errorText}`;
                                }
                            } catch (e2) {
                                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                            }
                        }
                        throw new Error(errorMessage);
                    }
                    
                } catch (error) {
                    if (this.debugMode) {
                        console.error('Error deleting photo:', error);
                    }
                    this.notificationManager.show(`Error deleting photo: ${error.message}`, 'error');
                }
                
                this.currentPhotoId = null;
            }
            
            // Calculate optimal distribution with custom target variation
            calculateOptimalDistributionWithTarget(photoOrder, targetVariation) {
                const maxIterations = 150;
                
                const photoHeights = this.calculateAccuratePhotoHeights(photoOrder);
                
                if (this.debugMode) {
                    console.log(`Target variation: ${targetVariation}%`);
                    console.log('Pre-calculated photo heights:', photoHeights.map(h => `${h.toFixed(1)}px`));
                }
                
                let columnHeights = new Array(this.columnCount).fill(0);
                let columnAssignments = [];
                
                // First pass: distribute photos to shortest columns
                photoOrder.forEach((photoData, index) => {
                    let shortestColumnIndex = 0;
                    let minHeight = columnHeights[0];
                    
                    for (let i = 1; i < this.columnCount; i++) {
                        if (columnHeights[i] < minHeight) {
                            minHeight = columnHeights[i];
                            shortestColumnIndex = i;
                        }
                    }
                    
                    columnAssignments[index] = shortestColumnIndex;
                    columnHeights[shortestColumnIndex] += photoHeights[index];
                });
                
                let currentVariation = utils.calculateHeightVariation(columnHeights);
                
                if (this.debugMode) {
                    console.log(`Initial distribution - Variation: ${currentVariation.toFixed(1)}%`);
                    console.log('Initial column heights:', columnHeights.map(h => `${h.toFixed(1)}px`));
                }
                
                if (currentVariation <= targetVariation) {
                    if (this.debugMode) {
                        console.log(`✅ Initial distribution already meets target variation of ${targetVariation}%!`);
                    }
                    return {
                        columnAssignments,
                        finalHeights: columnHeights,
                        finalVariation: currentVariation,
                        iterations: 0,
                        targetAchieved: true
                    };
                }
                
                let iterations = 0;
                let bestVariation = currentVariation;
                let bestDistribution = [...columnAssignments];
                let bestHeights = [...columnHeights];
                
                while (currentVariation > targetVariation && iterations < maxIterations) {
                    iterations++;
                    let improved = false;
                    
                    // Try swapping photos between columns to improve balance
                    for (let i = 0; i < photoOrder.length && !improved; i++) {
                        for (let j = i + 1; j < photoOrder.length && !improved; j++) {
                            const currentCol1 = columnAssignments[i];
                            const currentCol2 = columnAssignments[j];
                            
                            if (currentCol1 === currentCol2) continue;
                            
                            const tempHeights = [...columnHeights];
                            tempHeights[currentCol1] = tempHeights[currentCol1] - photoHeights[i] + photoHeights[j];
                            tempHeights[currentCol2] = tempHeights[currentCol2] - photoHeights[j] + photoHeights[i];
                            
                            const newVariation = utils.calculateHeightVariation(tempHeights);
                            
                            if (newVariation < currentVariation) {
                                columnAssignments[i] = currentCol2;
                                columnAssignments[j] = currentCol1;
                                columnHeights = tempHeights;
                                currentVariation = newVariation;
                                improved = true;
                                
                                if (this.debugMode) {
                                    console.log(`Iteration ${iterations}: Swapped photos ${i} and ${j}, new variation: ${newVariation.toFixed(1)}%`);
                                }
                                
                                if (newVariation < bestVariation) {
                                    bestVariation = newVariation;
                                    bestDistribution = [...columnAssignments];
                                    bestHeights = [...columnHeights];
                                }
                                
                                if (newVariation <= targetVariation) {
                                    if (this.debugMode) {
                                        console.log(`✅ Target variation of ${targetVariation}% reached after ${iterations} iterations!`);
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    
                    // If no improvement found, try more aggressive optimization
                    if (!improved) {
                        const tallestColumn = columnHeights.indexOf(Math.max(...columnHeights));
                        const shortestColumn = columnHeights.indexOf(Math.min(...columnHeights));
                        
                        for (let i = 0; i < photoOrder.length; i++) {
                            if (columnAssignments[i] === tallestColumn) {
                                const tempHeights = [...columnHeights];
                                tempHeights[tallestColumn] -= photoHeights[i];
                                tempHeights[shortestColumn] += photoHeights[i];
                                
                                const newVariation = utils.calculateHeightVariation(tempHeights);
                                
                                if (newVariation < currentVariation) {
                                    columnAssignments[i] = shortestColumn;
                                    columnHeights = tempHeights;
                                    currentVariation = newVariation;
                                    improved = true;
                                    
                                    if (this.debugMode) {
                                        console.log(`Iteration ${iterations}: Moved photo ${i} from tallest to shortest column, new variation: ${newVariation.toFixed(1)}%`);
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    
                    // If still no improvement, try random swaps for a few iterations
                    if (!improved && iterations > maxIterations * 0.7) {
                        for (let attempt = 0; attempt < 5 && !improved; attempt++) {
                            const randomI = Math.floor(Math.random() * photoOrder.length);
                            const randomJ = Math.floor(Math.random() * photoOrder.length);
                            
                            if (randomI !== randomJ) {
                                const currentCol1 = columnAssignments[randomI];
                                const currentCol2 = columnAssignments[randomJ];
                                
                                if (currentCol1 !== currentCol2) {
                                    const tempHeights = [...columnHeights];
                                    tempHeights[currentCol1] = tempHeights[currentCol1] - photoHeights[randomI] + photoHeights[randomJ];
                                    tempHeights[currentCol2] = tempHeights[currentCol2] - photoHeights[randomJ] + photoHeights[randomI];
                                    
                                    const newVariation = utils.calculateHeightVariation(tempHeights);
                                    
                                    if (newVariation < currentVariation) {
                                        columnAssignments[randomI] = currentCol2;
                                        columnAssignments[randomJ] = currentCol1;
                                        columnHeights = tempHeights;
                                        currentVariation = newVariation;
                                        improved = true;
                                        
                                        if (this.debugMode) {
                                            console.log(`Iteration ${iterations}: Random swap improved variation to ${newVariation.toFixed(1)}%`);
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    if (!improved) {
                        if (this.debugMode) {
                            console.log(`No more improvements possible after ${iterations} iterations`);
                        }
                        break;
                    }
                }
                
                if (bestVariation < currentVariation) {
                    if (this.debugMode) {
                        console.log(`Using best distribution found: variation ${bestVariation.toFixed(1)}% (vs current ${currentVariation.toFixed(1)}%)`);
                    }
                    columnAssignments = bestDistribution;
                    columnHeights = bestHeights;
                    currentVariation = bestVariation;
                }
                
                const targetAchieved = currentVariation <= targetVariation;
                
                if (this.debugMode) {
                    console.log(`Optimization completed in ${iterations} iterations`);
                    console.log(`Final variation: ${currentVariation.toFixed(1)}% (target: ${targetVariation}%)`);
                    console.log(`Target achieved: ${targetAchieved ? '✅ YES' : '❌ NO'}`);
                }
                
                return {
                    columnAssignments,
                    finalHeights: columnHeights,
                    finalVariation: currentVariation,
                    iterations,
                    targetAchieved
                };
            }
            
            // Apply optimized distribution to the grid
            applyOptimizedDistribution(distributionResult) {
                const { columnAssignments, finalHeights, finalVariation } = distributionResult;
                
                const columnFragments = Array.from({ length: this.columnCount }, () => document.createDocumentFragment());
                
                distributionResult.columnAssignments.forEach((columnIndex, photoIndex) => {
                    const photoData = this.photoOrder[photoIndex];
                    const photoClone = photoData.element.cloneNode(true);
                    
                    photoClone.dataset.originalIndex = photoData.originalIndex;
                    photoClone.dataset.photoId = photoData.photoId;
                    photoClone.dataset.currentPosition = photoData.currentPosition;
                    photoClone.dataset.columnIndex = columnIndex;
                    photoClone.classList.add('loading');
                    
                    columnFragments[columnIndex].appendChild(photoClone);
                });
                
                columnFragments.forEach((colFragment, colIndex) => {
                    if (colFragment.children.length > 0) {
                        this.columns[colIndex].appendChild(colFragment);
                    }
                });
                
                setTimeout(() => {
                    const newPhotos = document.querySelectorAll('.photo-item.loading');
                    newPhotos.forEach((photo, index) => {
                        requestAnimationFrame(() => {
                            photo.classList.remove('loading');
                            photo.classList.add('loaded');
                        });
                    });
                }, 50);
                
                this.setupEventListeners();
                this.setupDeleteHandlers();
            }
        }

        // Initialize gallery when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Check if Bootstrap is loaded
            if (typeof bootstrap === 'undefined') {
                console.error('Bootstrap is not loaded! Please check that bootstrap.bundle.min.js is included.');
                return;
            }
            
            // Initialize photo gallery
            window.photoGallery = new PhotoGallery();
            
            // Initialize lazy loading
            window.lazyLoader = new LazyImageLoader();
            
            // Sync debug mode
            if (window.photoGallery) {
                window.lazyLoader.debugMode = window.photoGallery.debugMode;
            }
        });

        // Global debug methods for testing and optimization
        window.enablePhotoGalleryDebug = () => {
            if (window.photoGallery) {
                window.photoGallery.setDebugMode(true);
                console.log('PhotoGallery debug mode enabled. Use window.photoGallery.setDebugMode(false) to disable.');
            }
            if (window.lazyLoader) {
                window.lazyLoader.debugMode = true;
                console.log('LazyImageLoader debug mode also enabled.');
            }
            if (window.messageManager && window.messageManager.setDebugMode) {
                window.messageManager.setDebugMode(true);
                console.log('MessageManager debug mode also enabled.');
            }
        };

        window.disablePhotoGalleryDebug = () => {
            if (window.photoGallery) {
                window.photoGallery.setDebugMode(false);
                console.log('PhotoGallery debug mode disabled.');
            }
            if (window.lazyLoader) {
                window.lazyLoader.debugMode = false;
                console.log('LazyImageLoader debug mode also disabled.');
            }
            if (window.messageManager && window.messageManager.setDebugMode) {
                window.messageManager.setDebugMode(false);
                console.log('MessageManager debug mode also disabled.');
            }
        };

        window.showPhotoGalleryDebugStatus = () => {
            console.log('=== PhotoGallery Debug Status ===');
            if (window.photoGallery) {
                console.log(`PhotoGallery debug mode: ${window.photoGallery.debugMode ? 'ENABLED' : 'DISABLED'}`);
            } else {
                console.log('PhotoGallery: Not initialized');
            }
            if (window.lazyLoader) {
                console.log(`LazyImageLoader debug mode: ${window.lazyLoader.debugMode ? 'ENABLED' : 'DISABLED'}`);
            } else {
                console.log('LazyImageLoader: Not initialized');
            }
            if (window.messageManager) {
                console.log(`MessageManager debug mode: ${window.messageManager.getDebugMode() ? 'ENABLED' : 'DISABLED'}`);
            } else {
                console.log('MessageManager: Not initialized');
            }
            console.log('================================');
        };

        // Column optimization testing methods
        window.optimizePhotoGalleryColumns = () => {
            if (window.photoGallery) {
                console.log('🔄 Optimizing photo gallery columns...');
                window.photoGallery.optimizeColumns();
            } else {
                console.error('PhotoGallery not initialized');
            }
        };

        window.optimizePhotoGalleryColumnsWithTarget = (targetVariation = CONFIG.TARGET_VARIATION) => {
            if (window.photoGallery) {
                console.log(`🔄 Optimizing photo gallery columns with target variation: ${targetVariation}%`);
                window.photoGallery.optimizeColumns(targetVariation);
            } else {
                console.error('PhotoGallery not initialized');
            }
        };

        window.showPhotoGalleryLayoutInfo = () => {
            if (window.photoGallery) {
                const info = window.photoGallery.getLayoutInfo();
                console.log('📊 PhotoGallery Layout Information:');
                console.log(`  Columns: ${info.columnCount}`);
                console.log(`  Container width: ${info.containerWidth}px`);
                console.log(`  Viewport width: ${info.viewportWidth}px`);
                console.log(`  Device type: ${info.isMobile ? 'Mobile' : info.isTablet ? 'Tablet' : 'Desktop'}`);
                console.log(`  Photos per column:`, info.photosPerColumn);
                console.log(`  Estimated column heights:`, info.columnHeights);
                
                // Calculate height variation
                if (info.columnHeights.length > 0) {
                    const maxHeight = Math.max(...info.columnHeights);
                    const minHeight = Math.min(...info.columnHeights);
                    const variation = ((maxHeight - minHeight) / maxHeight * 100).toFixed(1);
                    console.log(`  Height variation: ${variation}%`);
                    console.log(`  Quality: ${variation <= CONFIG.TARGET_VARIATION ? '✅ EXCELLENT' : variation <= 15 ? '⚠️ GOOD' : '❌ NEEDS IMPROVEMENT'}`);
                }
            } else {
                console.error('PhotoGallery not initialized');
            }
        };

        window.forcePhotoGalleryRedistribution = () => {
            if (window.photoGallery) {
                console.log('🔄 Forcing photo redistribution...');
                window.photoGallery.optimizeColumns(CONFIG.TARGET_VARIATION);
            } else {
                console.error('PhotoGallery not initialized');
            }
        };

        window.testColumnOptimization = (targetVariation = CONFIG.TARGET_VARIATION) => {
            if (window.photoGallery) {
                console.log(`🧪 Testing column optimization with target: ${targetVariation}%`);
                console.log('Current layout info:');
                window.showPhotoGalleryLayoutInfo();
                
                console.log('\n🔄 Starting optimization...');
                const startTime = performance.now();
                
                window.photoGallery.optimizeColumns(targetVariation);
                
                setTimeout(() => {
                    const endTime = performance.now();
                    console.log(`\n✅ Optimization completed in ${(endTime - startTime).toFixed(2)}ms`);
                    console.log('Final layout info:');
                    window.showPhotoGalleryLayoutInfo();
                }, 500);
            } else {
                console.error('PhotoGallery not initialized');
            }
        };

        // Export for use in other modules
        if (typeof module !== 'undefined' && module.exports) {
            module.exports = PhotoGallery;
        }
