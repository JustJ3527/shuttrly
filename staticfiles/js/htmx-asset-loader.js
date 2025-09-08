// HTMX Asset Loader
// Handles loading of page-specific CSS and JS files when content is loaded via HTMX

document.addEventListener('DOMContentLoaded', function() {
    // Listen for HTMX events
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        // Show loading indicator if needed
        const target = evt.detail.target;
        if (target.id === 'page-content') {
            showPageLoading();
        }
    });
    
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const target = evt.detail.target;
        if (target.id === 'page-content') {
            hidePageLoading();
            // Load page-specific assets
            loadPageAssets(evt.detail.xhr);
        }
    });
    
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        const target = evt.detail.target;
        if (target.id === 'page-content') {
            // Initialize page-specific functionality
            initializePageContent();
        }
    });
});

function showPageLoading() {
    // Create subtle loading indicator
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'page-loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="page-loading-content">
            <div class="loading-spinner"></div>
        </div>
    `;
    loadingOverlay.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        z-index: 9999;
        pointer-events: none;
    `;
    
    // Add CSS for the spinner
    const style = document.createElement('style');
    style.textContent = `
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(59, 130, 246, 0.2);
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .page-loading-content {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(loadingOverlay);
}

function hidePageLoading() {
    const loadingOverlay = document.getElementById('page-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

function loadPageAssets(xhr) {
    try {
        // Get the response text
        const responseText = xhr.responseText;
        
        // Create a temporary div to parse the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = responseText;
        
        // Extract CSS links
        const cssLinks = tempDiv.querySelectorAll('link[rel="stylesheet"]');
        cssLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && !document.querySelector(`link[href="${href}"]`)) {
                console.log('Loading CSS:', href);
                loadCSS(href);
            }
        });
        
        // Extract JS scripts - only load if not already loaded
        const jsScripts = tempDiv.querySelectorAll('script[src]');
        jsScripts.forEach(script => {
            const src = script.getAttribute('src');
            if (src && !isScriptAlreadyLoaded(src)) {
                console.log('Loading JS:', src);
                loadJS(src).catch(error => {
                    console.warn('Failed to load JS:', src, error);
                });
            } else if (src) {
                console.log('JS already loaded, skipping:', src);
            }
        });
        
        // Extract inline scripts - skip if they contain class declarations
        const inlineScripts = tempDiv.querySelectorAll('script:not([src])');
        inlineScripts.forEach(script => {
            if (script.textContent.trim()) {
                const code = script.textContent.trim();
                // Skip scripts that contain class declarations to avoid conflicts
                if (code.includes('class PhotoSearch') || code.includes('class PhotoSelector') || code.includes('class AdvancedGallery')) {
                    console.log('Skipping inline script with class declarations to avoid conflicts');
                    return;
                }
                console.log('Executing inline script');
                executeInlineScript(code);
            }
        });
        
    } catch (error) {
        console.error('Error loading page assets:', error);
    }
}

function isScriptAlreadyLoaded(src) {
    // Check if script is already in DOM
    if (document.querySelector(`script[src="${src}"]`)) {
        console.log('Script found in DOM:', src);
        return true;
    }
    
    // Check if the script is in our loaded scripts set
    if (window.loadedScripts && window.loadedScripts.has(src)) {
        console.log('Script found in loaded scripts set:', src);
        return true;
    }
    
    // Check if the class/function is already defined
    if (src.includes('photo-search.js') && typeof PhotoSearch !== 'undefined') {
        console.log('PhotoSearch class already defined');
        return true;
    }
    if (src.includes('photo-selector.js') && typeof PhotoSelector !== 'undefined') {
        console.log('PhotoSelector class already defined');
        return true;
    }
    if (src.includes('advanced-gallery.js') && typeof AdvancedGallery !== 'undefined') {
        console.log('AdvancedGallery class already defined');
        return true;
    }
    
    return false;
}

function loadCSS(href) {
    return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.onload = resolve;
        link.onerror = reject;
        document.head.appendChild(link);
    });
}

function loadJS(src) {
    return new Promise((resolve, reject) => {
        // Initialize loaded scripts set if it doesn't exist
        if (!window.loadedScripts) {
            window.loadedScripts = new Set();
        }
        
        // Check if already loaded
        if (window.loadedScripts.has(src)) {
            console.log('Script already loaded, skipping:', src);
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => {
            window.loadedScripts.add(src);
            console.log('Script loaded successfully:', src);
            resolve();
        };
        script.onerror = (error) => {
            console.error('Failed to load script:', src, error);
            reject(error);
        };
        document.head.appendChild(script);
    });
}

function executeInlineScript(code) {
    try {
        // Check if this is a class declaration that might already exist
        if (code.includes('class PhotoSearch') || code.includes('class PhotoSelector') || code.includes('class AdvancedGallery')) {
            console.log('Skipping inline script with class declarations to avoid conflicts');
            return;
        }
        
        // Create a new script element and execute the code
        const script = document.createElement('script');
        script.textContent = code;
        document.head.appendChild(script);
        document.head.removeChild(script);
    } catch (error) {
        console.error('Error executing inline script:', error);
    }
}

function initializePageContent() {
    // Call page-specific initialization functions
    const pageContent = document.getElementById('page-content');
    if (pageContent) {
        const pageName = pageContent.querySelector('[data-page]')?.getAttribute('data-page');
        
        switch (pageName) {
            case 'home':
                initializeHomePage();
                break;
            case 'advanced_gallery':
                initializeAdvancedGalleryPage();
                break;
            case 'public_profile':
                initializePublicProfilePage();
                break;
            default:
                console.log('No specific initialization for page:', pageName);
        }
    }
}

function initializeHomePage() {
    console.log('Initializing home page...');
    // Home page specific initialization
}

function initializeAdvancedGalleryPage() {
    console.log('Initializing advanced gallery page...');
    
    // Wait for the AdvancedGallery class to be available
    const initGallery = () => {
        if (typeof AdvancedGallery !== 'undefined') {
            console.log('AdvancedGallery class found, initializing...');
            
            // Hide loading indicators first
            const loadingBar = document.getElementById('gallery-loading-bar');
            const loadingText = document.querySelector('.loading-text');
            
            if (loadingBar) {
                loadingBar.style.display = 'none';
            }
            if (loadingText) {
                loadingText.style.display = 'none';
            }
            
            // Show gallery container
            const galleryContainer = document.querySelector('.advanced-gallery-container');
            if (galleryContainer) {
                galleryContainer.style.opacity = '1';
                galleryContainer.style.visibility = 'visible';
            }
            
            // Initialize the gallery only if not already initialized
            if (!window.advancedGalleryInstance) {
                try {
                    window.advancedGalleryInstance = new AdvancedGallery();
                    console.log('Advanced Gallery instance created successfully');
                } catch (error) {
                    console.error('Error creating Advanced Gallery instance:', error);
                }
            } else {
                console.log('Advanced Gallery instance already exists, reinitializing...');
                // Reinitialize the existing instance if needed
                if (window.advancedGalleryInstance.init) {
                    window.advancedGalleryInstance.init();
                }
            }
        } else {
            console.log('AdvancedGallery class not found, retrying...');
            setTimeout(initGallery, 200);
        }
    };
    
    // Start initialization with a small delay to ensure scripts are loaded
    setTimeout(initGallery, 100);
}

function initializePublicProfilePage() {
    console.log('Initializing public profile page...');
    // Public profile specific initialization
}

// Export for global access
window.HTMXAssetLoader = {
    loadCSS,
    loadJS,
    executeInlineScript,
    initializePageContent
};
