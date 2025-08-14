/**
 * UI Utilities System
 * Handles common UI operations, DOM manipulation, animations, and user interactions
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

// =============================================================================
// UI CONFIGURATION
// =============================================================================

const UI_CONFIG = {
    // Animation settings
    animation: {
        duration: 300,
        easing: 'ease',
        fadeInDelay: 100,
        slideDistance: 20
    },
    
    // Transition settings
    transition: {
        duration: 200,
        easing: 'ease-in-out'
    },
    
    // Debounce settings
    debounce: {
        defaultDelay: 300,
        searchDelay: 500,
        resizeDelay: 250
    },
    
    // Scroll settings
    scroll: {
        smooth: true,
        offset: 0,
        duration: 800
    }
};

// =============================================================================
// UI CORE SYSTEM
// =============================================================================

class UIUtils {
    constructor() {
        this.animations = new Map();
        this.eventListeners = new Map();
        this.isInitialized = false;
        this.debounceTimers = new Map();
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.initializeGlobalUI();
        this.isInitialized = true;
        console.log('🎨 UI Utils System initialized');
    }

    // =============================================================================
    // DOM MANIPULATION
    // =============================================================================

    /**
     * Create a DOM element with attributes and content
     * @param {string} tag - HTML tag name
     * @param {Object} attributes - Element attributes
     * @param {string|HTMLElement} content - Element content
     * @returns {HTMLElement} Created element
     */
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        // Set attributes
        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'innerHTML') {
                element.innerHTML = attributes[key];
            } else {
                element.setAttribute(key, attributes[key]);
            }
        });
        
        // Set content
        if (content) {
            if (typeof content === 'string') {
                element.textContent = content;
            } else if (content instanceof HTMLElement) {
                element.appendChild(content);
            }
        }
        
        return element;
    }

    /**
     * Remove an element with animation
     * @param {HTMLElement} element - Element to remove
     * @param {Object} options - Removal options
     */
    removeElement(element, options = {}) {
        const {
            animate = true,
            duration = UI_CONFIG.animation.duration,
            onComplete = null
        } = options;

        if (!animate) {
            element.remove();
            if (onComplete) onComplete();
            return;
        }

        // Fade out animation
        element.style.transition = `all ${duration}ms ${UI_CONFIG.animation.easing}`;
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';

        setTimeout(() => {
            element.remove();
            if (onComplete) onComplete();
        }, duration);
    }

    /**
     * Toggle element visibility with animation
     * @param {HTMLElement} element - Element to toggle
     * @param {boolean} show - Whether to show or hide
     * @param {Object} options - Animation options
     */
    toggleElement(element, show, options = {}) {
        const {
            animate = true,
            duration = UI_CONFIG.animation.duration,
            slide = true
        } = options;

        if (!animate) {
            element.style.display = show ? 'block' : 'none';
            return;
        }

        if (show) {
            element.style.display = 'block';
            element.style.opacity = '0';
            if (slide) {
                element.style.transform = `translateY(${UI_CONFIG.animation.slideDistance}px)`;
            }

            // Trigger reflow
            element.offsetHeight;

            element.style.transition = `all ${duration}ms ${UI_CONFIG.animation.easing}`;
            element.style.opacity = '1';
            if (slide) {
                element.style.transform = 'translateY(0)';
            }
        } else {
            element.style.transition = `all ${duration}ms ${UI_CONFIG.animation.easing}`;
            element.style.opacity = '0';
            if (slide) {
                element.style.transform = `translateY(${UI_CONFIG.animation.slideDistance}px)`;
            }

            setTimeout(() => {
                element.style.display = 'none';
            }, duration);
        }
    }

    /**
     * Show/hide multiple elements with staggered animation
     * @param {Array} elements - Array of elements to animate
     * @param {boolean} show - Whether to show or hide
     * @param {Object} options - Animation options
     */
    toggleElements(elements, show, options = {}) {
        const {
            stagger = UI_CONFIG.animation.fadeInDelay,
            duration = UI_CONFIG.animation.duration
        } = options;

        elements.forEach((element, index) => {
            setTimeout(() => {
                this.toggleElement(element, show, { duration });
            }, index * stagger);
        });
    }

    // =============================================================================
    // ANIMATIONS
    // =============================================================================

    /**
     * Fade in an element
     * @param {HTMLElement} element - Element to fade in
     * @param {Object} options - Animation options
     */
    fadeIn(element, options = {}) {
        const {
            duration = UI_CONFIG.animation.duration,
            delay = 0,
            onComplete = null
        } = options;

        element.style.opacity = '0';
        element.style.display = 'block';

        setTimeout(() => {
            element.style.transition = `opacity ${duration}ms ${UI_CONFIG.animation.easing}`;
            element.style.opacity = '1';

            setTimeout(() => {
                if (onComplete) onComplete();
            }, duration);
        }, delay);
    }

    /**
     * Fade out an element
     * @param {HTMLElement} element - Element to fade out
     * @param {Object} options - Animation options
     */
    fadeOut(element, options = {}) {
        const {
            duration = UI_CONFIG.animation.duration,
            hideAfter = true,
            onComplete = null
        } = options;

        element.style.transition = `opacity ${duration}ms ${UI_CONFIG.animation.easing}`;
        element.style.opacity = '0';

        setTimeout(() => {
            if (hideAfter) {
                element.style.display = 'none';
            }
            if (onComplete) onComplete();
        }, duration);
    }

    /**
     * Slide down an element
     * @param {HTMLElement} element - Element to slide down
     * @param {Object} options - Animation options
     */
    slideDown(element, options = {}) {
        const {
            duration = UI_CONFIG.animation.duration,
            onComplete = null
        } = options;

        element.style.display = 'block';
        element.style.height = '0';
        element.style.overflow = 'hidden';
        element.style.transition = `height ${duration}ms ${UI_CONFIG.animation.easing}`;

        // Trigger reflow
        element.offsetHeight;

        element.style.height = element.scrollHeight + 'px';

        setTimeout(() => {
            element.style.height = 'auto';
            element.style.overflow = '';
            if (onComplete) onComplete();
        }, duration);
    }

    /**
     * Slide up an element
     * @param {HTMLElement} element - Element to slide up
     * @param {Object} options - Animation options
     */
    slideUp(element, options = {}) {
        const {
            duration = UI_CONFIG.animation.duration,
            hideAfter = true,
            onComplete = null
        } = options;

        element.style.height = element.scrollHeight + 'px';
        element.style.overflow = 'hidden';
        element.style.transition = `height ${duration}ms ${UI_CONFIG.animation.easing}`;

        // Trigger reflow
        element.offsetHeight;

        element.style.height = '0';

        setTimeout(() => {
            if (hideAfter) {
                element.style.display = 'none';
            }
            element.style.overflow = '';
            if (onComplete) onComplete();
        }, duration);
    }

    /**
     * Add loading spinner to an element
     * @param {HTMLElement} element - Element to add spinner to
     * @param {Object} options - Spinner options
     */
    addLoadingSpinner(element, options = {}) {
        const {
            text = 'Loading...',
            size = 'sm',
            color = 'primary'
        } = options;

        const spinner = this.createElement('div', {
            className: `loading-spinner loading-spinner-${size} text-${color}`
        }, `
            <i class="fas fa-spinner fa-spin"></i>
            <span class="loading-text">${text}</span>
        `);

        element.appendChild(spinner);
        return spinner;
    }

    /**
     * Remove loading spinner from an element
     * @param {HTMLElement} element - Element to remove spinner from
     */
    removeLoadingSpinner(element) {
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }

    // =============================================================================
    // EVENT HANDLING
    // =============================================================================

    /**
     * Add event listener with automatic cleanup tracking
     * @param {HTMLElement} element - Element to add listener to
     * @param {string} event - Event type
     * @param {Function} handler - Event handler function
     * @param {Object} options - Event options
     */
    addEventListener(element, event, handler, options = {}) {
        const key = `${element.id || 'unknown'}_${event}`;
        
        element.addEventListener(event, handler, options);
        
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        this.eventListeners.get(key).push({ element, event, handler, options });
    }

    /**
     * Remove event listener
     * @param {HTMLElement} element - Element to remove listener from
     * @param {string} event - Event type
     * @param {Function} handler - Event handler function
     */
    removeEventListener(element, event, handler) {
        const key = `${element.id || 'unknown'}_${event}`;
        
        element.removeEventListener(event, handler);
        
        if (this.eventListeners.has(key)) {
            const listeners = this.eventListeners.get(key);
            const index = listeners.findIndex(l => l.handler === handler);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * Add click outside listener
     * @param {HTMLElement} element - Element to detect clicks outside of
     * @param {Function} callback - Callback function
     * @param {Array} excludeElements - Elements to exclude from detection
     */
    addClickOutsideListener(element, callback, excludeElements = []) {
        const handleClickOutside = (event) => {
            if (!element.contains(event.target) && 
                !excludeElements.some(exclude => exclude.contains(event.target))) {
                callback(event);
            }
        };

        document.addEventListener('click', handleClickOutside);
        
        // Store for cleanup
        const key = `${element.id || 'unknown'}_clickoutside`;
        this.eventListeners.set(key, [{ element: document, event: 'click', handler: handleClickOutside }]);
    }

    // =============================================================================
    // FORM UTILITIES
    // =============================================================================

    /**
     * Initialize password toggle functionality
     * @param {string} containerSelector - Container selector
     */
    initializePasswordToggles(containerSelector = 'body') {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        const toggleButtons = container.querySelectorAll('.password-toggle-icon');
        
        toggleButtons.forEach(toggleBtn => {
            const passwordField = toggleBtn.previousElementSibling;
            if (passwordField && passwordField.type === 'password') {
                this.addEventListener(toggleBtn, 'click', () => {
                    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordField.setAttribute('type', type);
                    
                    // Toggle icon
                    toggleBtn.classList.toggle('fa-eye');
                    toggleBtn.classList.toggle('fa-eye-slash');
                });
            }
        });
    }

    /**
     * Initialize form field focus management
     * @param {string} formSelector - Form selector
     */
    initializeFormFocus(formSelector) {
        const form = document.querySelector(formSelector);
        if (!form) return;

        const focusableFields = form.querySelectorAll('input, select, textarea, button:not([disabled])');
        
        focusableFields.forEach((field, index) => {
            this.addEventListener(field, 'keydown', (e) => {
                if (e.key === 'Enter' && e.target.type !== 'textarea') {
                    e.preventDefault();
                    const nextField = focusableFields[index + 1];
                    if (nextField) {
                        nextField.focus();
                    }
                }
            });
        });
    }

    /**
     * Auto-resize textarea based on content
     * @param {HTMLElement} textarea - Textarea element
     */
    initializeAutoResizeTextarea(textarea) {
        const resize = () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        };

        this.addEventListener(textarea, 'input', resize);
        this.addEventListener(textarea, 'focus', resize);
        
        // Initial resize
        resize();
    }

    // =============================================================================
    // SCROLL UTILITIES
    // =============================================================================

    /**
     * Smooth scroll to element
     * @param {HTMLElement|string} target - Target element or selector
     * @param {Object} options - Scroll options
     */
    smoothScrollTo(target, options = {}) {
        const {
            offset = UI_CONFIG.scroll.offset,
            duration = UI_CONFIG.scroll.duration,
            easing = 'ease-in-out'
        } = options;

        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const targetPosition = element.offsetTop - offset;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        const animation = (currentTime) => {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = this.easeInOutCubic(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        };

        requestAnimationFrame(animation);
    }

    /**
     * Easing function for smooth animations
     * @param {number} t - Current time
     * @param {number} b - Start value
     * @param {number} c - Change in value
     * @param {number} d - Duration
     * @returns {number} Eased value
     */
    easeInOutCubic(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t * t + b;
        t -= 2;
        return c / 2 * (t * t * t + 2) + b;
    }

    /**
     * Scroll to top with smooth animation
     * @param {Object} options - Scroll options
     */
    scrollToTop(options = {}) {
        const {
            duration = UI_CONFIG.scroll.duration,
            easing = 'ease-in-out'
        } = options;

        this.smoothScrollTo(document.body, { duration, easing });
    }

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    /**
     * Debounce function execution
     * @param {Function} func - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @param {string} key - Unique key for the debounce
     * @returns {Function} Debounced function
     */
    debounce(func, delay, key) {
        return (...args) => {
            if (this.debounceTimers.has(key)) {
                clearTimeout(this.debounceTimers.get(key));
            }
            
            const timer = setTimeout(() => {
                func.apply(this, args);
                this.debounceTimers.delete(key);
            }, delay);
            
            this.debounceTimers.set(key, timer);
        };
    }

    /**
     * Throttle function execution
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in milliseconds
     * @returns {Function} Throttled function
     */
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

    /**
     * Check if element is in viewport
     * @param {HTMLElement} element - Element to check
     * @param {Object} options - Check options
     * @returns {boolean} Whether element is in viewport
     */
    isInViewport(element, options = {}) {
        const {
            threshold = 0,
            rootMargin = '0px'
        } = options;

        const rect = element.getBoundingClientRect();
        const windowHeight = window.innerHeight || document.documentElement.clientHeight;
        const windowWidth = window.innerWidth || document.documentElement.clientWidth;

        return (
            rect.top >= -threshold &&
            rect.left >= -threshold &&
            rect.bottom <= windowHeight + threshold &&
            rect.right <= windowWidth + threshold
        );
    }

    /**
     * Add intersection observer for scroll animations
     * @param {HTMLElement} element - Element to observe
     * @param {Function} callback - Callback function
     * @param {Object} options - Observer options
     */
    addIntersectionObserver(element, callback, options = {}) {
        const {
            threshold = 0.1,
            rootMargin = '0px'
        } = options;

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        callback(entry.target, entry);
                    }
                });
            }, { threshold, rootMargin });

            observer.observe(element);
            return observer;
        } else {
            // Fallback for older browsers
            if (this.isInViewport(element)) {
                callback(element);
            }
        }
    }

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @param {Function} onSuccess - Success callback
     * @param {Function} onError - Error callback
     */
    copyToClipboard(text, onSuccess = null, onError = null) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                if (onSuccess) onSuccess();
            }).catch((err) => {
                if (onError) onError(err);
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                if (onSuccess) onSuccess();
            } catch (err) {
                if (onError) onError(err);
            }
            
            document.body.removeChild(textArea);
        }
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeGlobalUI() {
        // Initialize password toggles globally
        this.initializePasswordToggles();
        
        // Initialize form focus management
        document.querySelectorAll('form').forEach(form => {
            this.initializeFormFocus(`#${form.id}`);
        });
        
        // Initialize auto-resize textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            this.initializeAutoResizeTextarea(textarea);
        });
        
        // Add intersection observer for scroll animations
        document.querySelectorAll('[data-animate-on-scroll]').forEach(element => {
            this.addIntersectionObserver(element, (target) => {
                target.classList.add('animate-in');
            });
        });
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        // Clear all event listeners
        this.eventListeners.forEach((listeners, key) => {
            listeners.forEach(({ element, event, handler }) => {
                element.removeEventListener(event, handler);
            });
        });
        this.eventListeners.clear();
        
        // Clear all debounce timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        this.isInitialized = false;
        console.log('🎨 UI Utils System destroyed');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.uiUtils = new UIUtils();

// Make functions globally accessible
window.createElement = (tag, attributes, content) => window.uiUtils.createElement(tag, attributes, content);
window.removeElement = (element, options) => window.uiUtils.removeElement(element, options);
window.toggleElement = (element, show, options) => window.uiUtils.toggleElement(element, show, options);
window.toggleElements = (elements, show, options) => window.uiUtils.toggleElements(elements, show, options);
window.fadeIn = (element, options) => window.uiUtils.fadeIn(element, options);
window.fadeOut = (element, options) => window.uiUtils.fadeOut(element, options);
window.slideDown = (element, options) => window.uiUtils.slideDown(element, options);
window.slideUp = (element, options) => window.uiUtils.slideUp(element, options);
window.addLoadingSpinner = (element, options) => window.uiUtils.addLoadingSpinner(element, options);
window.removeLoadingSpinner = (element) => window.uiUtils.removeLoadingSpinner(element);
window.smoothScrollTo = (target, options) => window.uiUtils.smoothScrollTo(target, options);
window.scrollToTop = (options) => window.uiUtils.scrollToTop(options);
window.isInViewport = (element, options) => window.uiUtils.isInViewport(element, options);
window.copyToClipboard = (text, onSuccess, onError) => window.uiUtils.copyToClipboard(text, onSuccess, onError);

// =============================================================================
// LEGACY SUPPORT
// =============================================================================

// Support for existing UI functions
window.initializePasswordToggles = (containerSelector) => window.uiUtils.initializePasswordToggles(containerSelector);

// =============================================================================
// DEBUG AND VERIFICATION
// =============================================================================

window.debugUISystem = function() {
    console.log('🔍 Debugging UI Utils System...');
    
    const functions = [
        'createElement',
        'removeElement',
        'toggleElement',
        'fadeIn',
        'fadeOut',
        'slideDown',
        'slideUp',
        'smoothScrollTo',
        'copyToClipboard',
        'isInViewport'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName}: Available`);
        } else {
            console.log(`❌ ${funcName}: Missing`);
        }
    });
    
    console.log(`🎨 Event listeners: ${window.uiUtils.eventListeners.size}`);
    console.log(`⏰ Debounce timers: ${window.uiUtils.debounceTimers.size}`);
    console.log('🔍 UI Utils System Debug Complete');
};

// Auto-debug on page load if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof window.debugUISystem === 'function') {
                window.debugUISystem();
            }
        }, 1000);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIUtils;
}