/**
 * Advanced Lazy Loading System for Shuttrly
 * Uses Intersection Observer API for efficient image loading
 */

class LazyLoader {
    constructor(options = {}) {
        this.options = {
            rootMargin: '50px', // Start loading 50px before image enters viewport
            threshold: 0.1,     // Trigger when 10% of image is visible
            placeholderSrc: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="150"%3E%3Crect width="150" height="150" fill="%23f8f9fa"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23dee2e6"%3E%3C/svg%3E',
            ...options
        };
        
        this.observer = null;
        this.lazyImages = [];
        this.loadedImages = new Set();
        this.init();
    }
    
    init() {
        // Check if Intersection Observer is supported
        if (!('IntersectionObserver' in window)) {
            console.warn('Intersection Observer not supported, falling back to basic lazy loading');
            this.fallbackLazyLoading();
            return;
        }
        
        this.setupIntersectionObserver();
        this.scanForLazyImages();
    }
    
    setupIntersectionObserver() {
        this.observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            },
            {
                rootMargin: this.options.rootMargin,
                threshold: this.options.threshold
            }
        );
    }
    
    scanForLazyImages() {
        // Find all images that should be lazy loaded
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        images.forEach(img => {
            if (!this.loadedImages.has(img.src)) {
                this.setupLazyImage(img);
            }
        });
    }
    
    setupLazyImage(img) {
        // Store original source
        const originalSrc = img.src;
        
        // Set placeholder
        img.src = this.options.placeholderSrc;
        img.classList.add('lazy-loading');
        
        // Add data attribute for original source
        img.dataset.originalSrc = originalSrc;
        
        // Add loading animation
        this.addLoadingAnimation(img);
        
        // Observe the image
        this.observer.observe(img);
        this.lazyImages.push(img);
    }
    
    loadImage(img) {
        const originalSrc = img.dataset.originalSrc;
        
        if (!originalSrc) {
            console.warn('No original source found for image:', img);
            return;
        }
        
        // Create a new image to preload
        const tempImg = new Image();
        
        tempImg.onload = () => {
            // Image loaded successfully
            img.src = originalSrc;
            img.classList.remove('lazy-loading');
            img.classList.add('lazy-loaded');
            
            // Remove loading animation
            this.removeLoadingAnimation(img);
            
            // Mark as loaded
            this.loadedImages.add(originalSrc);
            
            // Trigger custom event
            this.triggerImageLoadedEvent(img, originalSrc);
        };
        
        tempImg.onerror = () => {
            // Image failed to load
            console.error('Failed to load image:', originalSrc);
            img.classList.remove('lazy-loading');
            img.classList.add('lazy-error');
            
            // Remove loading animation
            this.removeLoadingAnimation(img);
            
            // Show error placeholder
            img.src = this.getErrorPlaceholder();
        };
        
        // Start loading
        tempImg.src = originalSrc;
    }
    
    addLoadingAnimation(img) {
        // Create loading spinner
        const spinner = document.createElement('div');
        spinner.className = 'lazy-loading-spinner';
        spinner.innerHTML = `
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        
        // Position spinner over image
        spinner.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            padding: 8px;
        `;
        
        // Add to image container
        const container = img.closest('.photo-item, .collection-item');
        if (container) {
            container.style.position = 'relative';
            container.appendChild(spinner);
        }
    }
    
    removeLoadingAnimation(img) {
        const container = img.closest('.photo-item, .collection-item');
        if (container) {
            const spinner = container.querySelector('.lazy-loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }
    
    getErrorPlaceholder() {
        return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="150"%3E%3Crect width="150" height="150" fill="%23f8f9fa"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23dc3545"%3E❌%3C/text%3E%3C/svg%3E';
    }
    
    triggerImageLoadedEvent(img, src) {
        // Custom event for when image is loaded
        const event = new CustomEvent('imageLoaded', {
            detail: { img, src, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
    }
    
    fallbackLazyLoading() {
        // Fallback for browsers without Intersection Observer
        console.log('Using fallback lazy loading');
        
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        images.forEach(img => {
            const originalSrc = img.src;
            img.src = this.options.placeholderSrc;
            img.dataset.originalSrc = originalSrc;
            
            // Load on scroll
            const loadOnScroll = () => {
                if (this.isElementInViewport(img)) {
                    img.src = originalSrc;
                    img.classList.add('lazy-loaded');
                    window.removeEventListener('scroll', loadOnScroll);
                }
            };
            
            window.addEventListener('scroll', loadOnScroll);
            loadOnScroll(); // Check initial position
        });
    }
    
    isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Public method to manually refresh lazy loading
    refresh() {
        this.scanForLazyImages();
    }
    
    // Public method to destroy the lazy loader
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.lazyImages = [];
        this.loadedImages.clear();
    }
}

// Initialize lazy loading when DOM is ready
function initializeLazyLoading(options = {}) {
    return new LazyLoader(options);
}

// Auto-initialize if script is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.lazyLoader = initializeLazyLoading();
    });
} else {
    window.lazyLoader = initializeLazyLoading();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LazyLoader, initializeLazyLoading };
}
