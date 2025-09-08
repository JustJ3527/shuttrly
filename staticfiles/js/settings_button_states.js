/**
 * Settings Button States Management
 * 
 * This file handles the loading states and visual feedback
 * for submit buttons in the settings dashboard categories.
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeButtonStates();
});

/**
 * Initialize button loading states
 */
function initializeButtonStates() {
    // Set up form submission handlers for all forms
    const forms = document.querySelectorAll('form[hx-post]');
    forms.forEach(form => {
        setupFormButtonStates(form);
    });
}

/**
 * Set up button states for a specific form
 */
function setupFormButtonStates(form) {
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    
    submitButtons.forEach(button => {
        // Store original content
        if (!button.dataset.originalContent) {
            button.dataset.originalContent = button.innerHTML;
        }
        
        // Add click handler to show loading state immediately
        button.addEventListener('click', function() {
            if (!button.disabled) {
                showButtonLoading(button);
            }
        });
    });
}

/**
 * Show loading state for a button
 */
function showButtonLoading(button) {
    button.classList.add('btn-loading');
    button.disabled = true;
    
    // Show loading content if it exists
    const loadingContent = button.querySelector('.btn-loading-content');
    const normalContent = button.querySelector('.btn-content');
    
    if (loadingContent && normalContent) {
        normalContent.style.display = 'none';
        loadingContent.style.display = 'inline-block';
    }
}

/**
 * Hide loading state for a button
 */
function hideButtonLoading(button) {
    button.classList.remove('btn-loading');
    button.disabled = false;
    
    // Show normal content if it exists
    const loadingContent = button.querySelector('.btn-loading-content');
    const normalContent = button.querySelector('.btn-content');
    
    if (loadingContent && normalContent) {
        normalContent.style.display = 'inline-block';
        loadingContent.style.display = 'none';
    }
}

/**
 * Reset all button states in a form
 */
function resetFormButtonStates(form) {
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(button => {
        hideButtonLoading(button);
    });
}

/**
 * Global function to show button loading (can be called from templates)
 */
window.showButtonLoading = showButtonLoading;
window.hideButtonLoading = hideButtonLoading;
window.resetFormButtonStates = resetFormButtonStates;
