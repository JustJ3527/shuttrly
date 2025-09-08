/**
 * Settings Dashboard Navigation JavaScript
 * 
 * This file handles the dynamic navigation and interactions
 * for the settings dashboard using HTMX.
 */

// Global variables
let currentCategory = 'general';
let isLoading = false;

/**
 * Initialize settings navigation
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeSettingsNavigation();
    setupHTMXEventHandlers();
    setupAutoSaveHandlers();
});

/**
 * Initialize the settings navigation system
 */
function initializeSettingsNavigation() {
    // Set initial active category
    updateActiveNavigation();
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', handlePopState);
    
    // Set up category switching
    setupCategorySwitching();
    
    // Add message animations
    addMessageAnimations();
}

/**
 * Set up HTMX event handlers for better UX
 */
function setupHTMXEventHandlers() {
    // Show loading indicator
    htmx.on('htmx:beforeRequest', function(evt) {
        const target = evt.detail.target;
        if (target && target.id === 'settings-content-area') {
            showLoadingIndicator(target);
        }
        
        // Handle form submissions - disable submit buttons and show loading
        if (evt.detail.elt && evt.detail.elt.tagName === 'FORM') {
            handleFormSubmissionStart(evt.detail.elt);
        }
    });
    
    // Hide loading indicator and handle response
    htmx.on('htmx:afterRequest', function(evt) {
        const target = evt.detail.target;
        if (target && target.id === 'settings-content-area') {
            hideLoadingIndicator(target);
            
            if (evt.detail.xhr.status === 200) {
                handleSuccessfulResponse(evt);
            } else {
                handleErrorResponse(evt);
            }
        }
        
        // Re-enable submit buttons and hide loading states
        if (evt.detail.elt && evt.detail.elt.tagName === 'FORM') {
            handleFormSubmissionEnd(evt.detail.elt);
        }
    });
    
    // Handle HTMX errors
    htmx.on('htmx:responseError', function(evt) {
        console.error('HTMX Response Error:', evt.detail);
        showErrorMessage('An error occurred while loading the content. Please try again.');
        
        // Re-enable submit buttons on error
        if (evt.detail.elt && evt.detail.elt.tagName === 'FORM') {
            handleFormSubmissionEnd(evt.detail.elt);
        }
    });
}

/**
 * Set up auto-save handlers for checkboxes and radio buttons
 */
function setupAutoSaveHandlers() {
    // Auto-save for checkboxes with hx-post attribute
    document.addEventListener('change', function(evt) {
        if (evt.target.matches('input[type="checkbox"], input[type="radio"]')) {
            const form = evt.target.closest('form');
            if (form && form.hasAttribute('hx-post')) {
                // Trigger form submission for auto-save
                htmx.trigger(form, 'submit');
            }
        }
    });
}

/**
 * Show loading indicator
 */
function showLoadingIndicator(target) {
    if (target) {
        isLoading = true;
        target.style.opacity = '0.6';
        
        // Add loading spinner
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        spinner.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1000;
            font-size: 2rem;
            color: #28a745;
        `;
        
        target.style.position = 'relative';
        target.appendChild(spinner);
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator(target) {
    if (target) {
        isLoading = false;
        target.style.opacity = '1';
        
        // Remove loading spinner
        const spinner = target.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

/**
 * Handle form submission start - disable submit buttons and show loading states
 */
function handleFormSubmissionStart(form) {
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    
    submitButtons.forEach(button => {
        // Store original text and state
        if (!button.dataset.originalText) {
            button.dataset.originalText = button.innerHTML;
            button.dataset.originalDisabled = button.disabled;
        }
        
        // Disable button and show loading state
        button.disabled = true;
        button.classList.add('btn-loading');
        
        // Add loading spinner to button
        const originalContent = button.innerHTML;
        button.innerHTML = `
            <span class="btn-loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
            <span class="btn-loading-text">${originalContent}</span>
        `;
    });
}

/**
 * Handle form submission end - re-enable submit buttons and hide loading states
 */
function handleFormSubmissionEnd(form) {
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    
    submitButtons.forEach(button => {
        // Re-enable button and restore original state
        if (button.dataset.originalDisabled !== undefined) {
            button.disabled = button.dataset.originalDisabled === 'true';
        } else {
            button.disabled = false;
        }
        
        button.classList.remove('btn-loading');
        
        // Restore original content
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    });
}

/**
 * Handle successful HTMX response
 */
function handleSuccessfulResponse(evt) {
    const target = evt.detail.target;
    const response = evt.detail.xhr.responseText;
    
    // Don't override user selection - only update if no category is currently active
    // This prevents the URL from overriding user clicks
    if (!document.querySelector('.nav-item.active')) {
        updateActiveNavigation();
    }
    
    // Check for Django messages in the response
    const djangoMessages = extractDjangoMessages(response);
    
    if (djangoMessages.success && djangoMessages.success.length > 0) {
        djangoMessages.success.forEach(msg => showSuccessMessage(msg));
    }
    if (djangoMessages.error && djangoMessages.error.length > 0) {
        djangoMessages.error.forEach(msg => showErrorMessage(msg));
    }
    
    // Reinitialize any JavaScript functionality in the new content
    reinitializeContent(target);
}

/**
 * Handle error response
 */
function handleErrorResponse(evt) {
    const status = evt.detail.xhr.status;
    const response = evt.detail.xhr.responseText;
    
    // Try to extract Django messages from error response
    const djangoMessages = extractDjangoMessages(response);
    if (djangoMessages.error && djangoMessages.error.length > 0) {
        djangoMessages.error.forEach(msg => showErrorMessage(msg));
        return;
    }
    
    // Fallback to generic error messages
    let message = 'An error occurred while processing your request.';
    
    if (status === 400) {
        message = 'Please check your input and try again.';
    } else if (status === 403) {
        message = 'You do not have permission to perform this action.';
    } else if (status === 404) {
        message = 'The requested resource was not found.';
    } else if (status === 500) {
        message = 'A server error occurred. Please try again later.';
    }
    
    showErrorMessage(message);
}

/**
 * Extract Django messages from HTML response
 */
function extractDjangoMessages(htmlResponse) {
    const messages = { success: [], error: [], warning: [], info: [] };
    
    // Create a temporary DOM element to parse the HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlResponse;
    
    // Look for Django message containers - check multiple possible selectors
    const messageSelectors = [
        '.alert',
        '.message', 
        '[class*="alert-"]',
        '.settings-messages .alert',
        '.alert-success',
        '.alert-danger',
        '.alert-warning',
        '.alert-info'
    ];
    
    messageSelectors.forEach(selector => {
        const containers = tempDiv.querySelectorAll(selector);
        
        containers.forEach(container => {
            const text = container.textContent.trim();
            const className = container.className;
            
            // Skip if this is just a container, not an actual message
            if (text.length < 10) return;
            
            if (className.includes('alert-success') || className.includes('success')) {
                messages.success.push(text);
            } else if (className.includes('alert-danger') || className.includes('error')) {
                messages.error.push(text);
            } else if (className.includes('alert-warning') || className.includes('warning')) {
                messages.warning.push(text);
            } else if (className.includes('alert-info') || className.includes('info')) {
                messages.info.push(text);
            }
        });
    });
    
    // Also check for any text that looks like a success/error message
    const allText = tempDiv.textContent;
    if (allText.includes('successfully') || allText.includes('Success')) {
        const successMatch = allText.match(/([^.!?]*(?:successfully|Success)[^.!?]*[.!?])/i);
        if (successMatch && !messages.success.includes(successMatch[1])) {
            messages.success.push(successMatch[1].trim());
        }
    }
    
    if (allText.includes('Error') || allText.includes('error')) {
        const errorMatch = allText.match(/([^.!?]*(?:Error|error)[^.!?]*[.!?])/i);
        if (errorMatch && !messages.error.includes(errorMatch[1])) {
            messages.error.push(errorMatch[1].trim());
        }
    }
    
    return messages;
}

/**
 * Handle browser popstate (back/forward buttons)
 */
function handlePopState(event) {
    if (event.state && event.state.category) {
        currentCategory = event.state.category;
        updateActiveNavigation();
        loadCategory(event.state.category);
    } else {
        // Fallback: update navigation based on current URL
        updateActiveNavigation();
    }
}

/**
 * Set up category switching
 */
function setupCategorySwitching() {
    // Handle category navigation clicks
    document.addEventListener('click', function(evt) {
        if (evt.target.closest('.nav-item')) {
            const navItem = evt.target.closest('.nav-item');
            const href = navItem.getAttribute('href');
            
            if (href) {
                const category = href.split('/').pop();
                if (category && category !== 'settings') {
                    // Update active state immediately for better UX
                    updateActiveNavigationItem(navItem);
                    switchToCategory(category);
                }
            }
        }
    });
}

/**
 * Update active navigation item for immediate visual feedback
 */
function updateActiveNavigationItem(activeItem) {
    if (!activeItem) return;
    
    // Get the category from the clicked item
    const href = activeItem.getAttribute('href');
    let category = null;
    
    if (href) {
        // Extract category from href - handle multiple URL patterns
        let categoryMatch = href.match(/\/settings\/([^\/]+)/);
        if (categoryMatch) {
            category = categoryMatch[1];
        }
        
        // Alternative: check if href contains the category name
        if (!category) {
            const hrefParts = href.split('/');
            for (let i = 0; i < hrefParts.length; i++) {
                if (hrefParts[i] === 'settings' && hrefParts[i + 1]) {
                    category = hrefParts[i + 1];
                    break;
                }
            }
        }
    }
    
    if (category) {
        // Use the priority-based update function
        updateActiveNavigationWithPriority(category);
    } else {
        // Fallback: just update the visual state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        activeItem.classList.add('active');
    }
    
    // Debug: log what happened
    console.log('updateActiveNavigationItem:', {
        href: href,
        extractedCategory: category,
        element: activeItem
    });
}

/**
 * Switch to a specific category
 */
function switchToCategory(category) {
    if (isLoading || category === currentCategory) {
        return;
    }
    
    currentCategory = category;
    
    // Update URL without page reload
    const newUrl = `${window.settingsBaseUrl}${category}/`;
    window.history.pushState({ category: category }, '', newUrl);
    
    // Update active navigation indicator with user priority
    updateActiveNavigationWithPriority(category);
    
    // Load category content
    loadCategory(category);
}

/**
 * Load category content via HTMX
 */
function loadCategory(category) {
    const target = document.getElementById('settings-content-area');
    if (target) {
        // Update URL with category parameter
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('category', category);
        window.history.replaceState({ category: category }, '', newUrl);
        
        // Load content via HTMX - use the correct URL pattern
        // The URL should match Django's URL patterns for settings categories
        const url = `${window.settingsBaseUrl}${category}/`;
        htmx.ajax('GET', url, target);
        
        // Update current category
        currentCategory = category;
    }
}

/**
 * Update active navigation item
 */
function updateActiveNavigation() {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // First, try to get category from URL query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const urlCategory = urlParams.get('category');
    
    // Then check URL path
    const currentUrl = window.location.pathname;
    const pathCategory = currentUrl.split('/').pop();
    
    // Determine which category to use
    let categoryToActivate = null;
    
    if (urlCategory && urlCategory !== 'general') {
        categoryToActivate = urlCategory;
    } else if (pathCategory && pathCategory !== 'settings') {
        categoryToActivate = pathCategory;
    } else if (currentCategory) {
        categoryToActivate = currentCategory;
    }
    
    if (categoryToActivate) {
        // Try multiple strategies to find the navigation item
        let activeItem = null;
        
        // Strategy 1: Find by data-category attribute (most reliable)
        activeItem = document.querySelector(`.nav-item[data-category="${categoryToActivate}"]`);
        
        // Strategy 2: Find by href containing the category, but only within nav-item elements
        if (!activeItem) {
            activeItem = document.querySelector(`.nav-item[href*="${categoryToActivate}"]`);
        }
        
        // Strategy 3: Find by href ending with the category, but only within nav-item elements
        if (!activeItem) {
            activeItem = document.querySelector(`.nav-item[href$="/${categoryToActivate}/"]`);
        }
        
        if (activeItem) {
            activeItem.classList.add('active');
            currentCategory = categoryToActivate;
        }
        
        // Debug: log what happened
        console.log('updateActiveNavigation:', {
            categoryToActivate: categoryToActivate,
            activeItem: activeItem,
            strategies: {
                strategy1: document.querySelector(`.nav-item[data-category="${categoryToActivate}"]`),
                strategy2: document.querySelector(`.nav-item[href*="${categoryToActivate}"]`),
                strategy3: document.querySelector(`.nav-item[href$="/${categoryToActivate}/"]`)
            }
        });
    }
}

/**
 * Update active navigation item with user preference priority
 * This function respects user clicks and doesn't override them with URL state
 */
function updateActiveNavigationWithPriority(userSelectedCategory = null) {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    let categoryToActivate = null;
    
    // Priority 1: User explicitly selected category (highest priority)
    if (userSelectedCategory) {
        categoryToActivate = userSelectedCategory;
    }
    // Priority 2: Current global category
    else if (currentCategory) {
        categoryToActivate = currentCategory;
    }
    // Priority 3: URL parameters (lowest priority)
    else {
        const urlParams = new URLSearchParams(window.location.search);
        const urlCategory = urlParams.get('category');
        if (urlCategory && urlCategory !== 'general') {
            categoryToActivate = urlCategory;
        }
    }
    
    if (categoryToActivate) {
        // Try multiple strategies to find the navigation item
        let activeItem = null;
        
        // Strategy 1: Find by data-category attribute (most reliable)
        activeItem = document.querySelector(`.nav-item[data-category="${categoryToActivate}"]`);
        
        // Strategy 2: Find by href containing the category, but only within nav-item elements
        if (!activeItem) {
            activeItem = document.querySelector(`.nav-item[href*="${categoryToActivate}"]`);
        }
        
        // Strategy 3: Find by href ending with the category, but only within nav-item elements
        if (!activeItem) {
            activeItem = document.querySelector(`.nav-item[href$="/${categoryToActivate}/"]`);
        }
        
        if (activeItem) {
            activeItem.classList.add('active');
            currentCategory = categoryToActivate;
        }
        
        // Debug: log what happened
        console.log('updateActiveNavigationWithPriority:', {
            categoryToActivate: categoryToActivate,
            activeItem: activeItem,
            strategies: {
                strategy1: document.querySelector(`.nav-item[data-category="${categoryToActivate}"]`),
                strategy2: document.querySelector(`.nav-item[href*="${categoryToActivate}"]`),
                strategy3: document.querySelector(`.nav-item[href$="/${categoryToActivate}/"]`)
            }
        });
    }
}

/**
 * Reinitialize content after HTMX swap
 */
function reinitializeContent(target) {
    // Safety check: ensure target is a valid DOM element
    if (!target || typeof target.querySelectorAll !== 'function') {
        return;
    }
    
    try {
        // Reinitialize password toggles
        initializePasswordToggles(target);
        
        // Reinitialize form validation
        initializeFormValidation(target);
        
        // Reinitialize any other interactive elements
        initializeInteractiveElements(target);
    } catch (error) {
        // Silently handle reinitialization errors
    }
}

/**
 * Initialize password toggle functionality
 */
function initializePasswordToggles(container) {
    // Safety check: ensure container is a valid DOM element
    if (!container || typeof container.querySelectorAll !== 'function') {
        return;
    }
    
    const toggles = container.querySelectorAll('.password-toggle-icon');
    
    toggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (input && input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else if (input && input.type === 'text') {
                input.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation(container) {
    // Safety check: ensure container is a valid DOM element
    if (!container || typeof container.querySelectorAll !== 'function') {
        return;
    }
    
    const forms = container.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(evt) {
            if (!validateForm(this)) {
                evt.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements(container) {
    // Safety check: ensure container is a valid DOM element
    if (!container || typeof container.querySelectorAll !== 'function') {
        return;
    }
    
    // Initialize tooltips
    const tooltips = container.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        try {
            new bootstrap.Tooltip(tooltip);
        } catch (error) {
            // Silently handle tooltip initialization errors
        }
    });
    
    // Initialize modals
    const modals = container.querySelectorAll('[data-bs-toggle="modal"]');
    modals.forEach(modal => {
        modal.addEventListener('click', function(evt) {
            evt.preventDefault();
            const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetModal) {
                            try {
                const modalInstance = new bootstrap.Modal(targetModal);
                modalInstance.show();
            } catch (error) {
                // Silently handle modal initialization errors
            }
            }
        });
    });
}

/**
 * Validate form before submission
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required.');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    field.parentNode.appendChild(errorDiv);
    field.classList.add('is-invalid');
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.field-error-message');
    if (errorDiv) {
        errorDiv.remove();
    }
    field.classList.remove('is-invalid');
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    showMessage(message, 'success');
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    showMessage(message, 'error');
}

/**
 * Show message with type
 */
function showMessage(message, type) {
    // Remove existing messages of the same type to avoid duplicates
    const existingMessages = document.querySelectorAll(`.settings-message.alert-${type === 'success' ? 'success' : 'danger'}`);
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `settings-message alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add some styling for better visibility
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: none;
        border-radius: 8px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    // Insert message at the top of the body for better visibility
    document.body.appendChild(messageDiv);
    
    // Auto-hide after 6 seconds (longer for better UX)
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 300);
        }
    }, 6000);
    
    // Add click to dismiss functionality
    messageDiv.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-close') || e.target.classList.contains('btn-close')) {
            this.remove();
        }
    });
}

/**
 * Add CSS animations for message display
 */
function addMessageAnimations() {
    if (!document.getElementById('message-animations')) {
        const style = document.createElement('style');
        style.id = 'message-animations';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Utility function to get current category
 */
function getCurrentCategory() {
    return currentCategory;
}

/**
 * Utility function to check if loading
 */
function getLoadingState() {
    return isLoading;
}

// Export functions for global access
window.SettingsNavigation = {
    switchToCategory,
    loadCategory,
    getCurrentCategory,
    getLoadingState,
    showSuccessMessage,
    showErrorMessage,
    updateActiveNavigation,
    updateActiveNavigationWithPriority,
    updateActiveNavigationItem
};
