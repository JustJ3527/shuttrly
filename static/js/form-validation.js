/**
 * Form Validation System
 * Handles all form validation, error management, and form submission logic
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

// =============================================================================
// VALIDATION CONFIGURATION
// =============================================================================

const VALIDATION_CONFIG = {
    // Password validation rules
    password: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: false,
        maxLength: 128
    },
    
    // Username validation rules
    username: {
        minLength: 3,
        maxLength: 30,
        allowedChars: /^[a-zA-Z0-9_-]+$/,
        reservedNames: ['admin', 'root', 'system', 'test', 'guest']
    },
    
    // Email validation rules
    email: {
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        maxLength: 254
    },
    
    // Verification code validation rules
    verificationCode: {
        length: 6,
        pattern: /^\d{6}$/,
        autoSubmit: true
    },
    
    // UI settings
    ui: {
        errorDisplayTime: 5000,
        animationDuration: 300,
        debounceDelay: 300
    }
};

// =============================================================================
// VALIDATION CORE SYSTEM
// =============================================================================

class FormValidator {
    constructor() {
        this.validators = new Map();
        this.errorMessages = new Map();
        this.isInitialized = false;
        this.debounceTimers = new Map();
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.registerDefaultValidators();
        this.initializeGlobalValidation();
        this.isInitialized = true;
        console.log('✅ Form Validation System initialized');
    }

    // =============================================================================
    // VALIDATOR REGISTRATION
    // =============================================================================

    registerDefaultValidators() {
        // Password validation
        this.registerValidator('password', this.validatePassword.bind(this));
        
        // Username validation
        this.registerValidator('username', this.validateUsername.bind(this));
        
        // Email validation
        this.registerValidator('email', this.validateEmail.bind(this));
        
        // Verification code validation
        this.registerValidator('verificationCode', this.validateVerificationCode.bind(this));
        
        // Required field validation
        this.registerValidator('required', this.validateRequired.bind(this));
        
        // Length validation
        this.registerValidator('length', this.validateLength.bind(this));
        
        // Pattern validation
        this.registerValidator('pattern', this.validatePattern.bind(this));
    }

    /**
     * Register a custom validator function
     * @param {string} name - Validator name
     * @param {Function} validatorFn - Validation function
     */
    registerValidator(name, validatorFn) {
        this.validators.set(name, validatorFn);
    }

    /**
     * Register custom error messages
     * @param {string} fieldName - Field name
     * @param {Object} messages - Error messages object
     */
    registerErrorMessages(fieldName, messages) {
        this.errorMessages.set(fieldName, messages);
    }

    // =============================================================================
    // CORE VALIDATION FUNCTIONS
    // =============================================================================

    /**
     * Validate a field using registered validators
     * @param {HTMLElement} field - Field element to validate
     * @param {Array} rules - Array of validation rules
     * @returns {Object} Validation result
     */
    validateField(field, rules) {
        const value = field.value.trim();
        const fieldName = field.name || field.id;
        let isValid = true;
        let errors = [];
        let warnings = [];

        rules.forEach(rule => {
            const validator = this.validators.get(rule.type);
            if (validator) {
                const result = validator(field, value, rule);
                
                if (!result.isValid) {
                    isValid = false;
                    if (result.error) {
                        errors.push(result.error);
                    }
                }
                
                if (result.warning) {
                    warnings.push(result.warning);
                }
            }
        });

        return {
            isValid,
            errors,
            warnings,
            fieldName,
            value
        };
    }

    /**
     * Validate an entire form
     * @param {HTMLElement} form - Form element to validate
     * @param {Object} fieldRules - Field validation rules
     * @returns {Object} Form validation result
     */
    validateForm(form, fieldRules) {
        let isValid = true;
        let fieldResults = new Map();
        let formErrors = [];

        Object.keys(fieldRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"], #${fieldName}`);
            if (field) {
                const result = this.validateField(field, fieldRules[fieldName]);
                fieldResults.set(fieldName, result);
                
                if (!result.isValid) {
                    isValid = false;
                    formErrors.push(...result.errors);
                }
            }
        });

        return {
            isValid,
            fieldResults,
            formErrors
        };
    }

    // =============================================================================
    // SPECIFIC VALIDATORS
    // =============================================================================

    validatePassword(field, value, rule = {}) {
        const config = { ...VALIDATION_CONFIG.password, ...rule };
        const errors = [];
        const warnings = [];

        if (!value) {
            return { isValid: false, error: 'Password is required' };
        }

        if (value.length < config.minLength) {
            errors.push(`Password must be at least ${config.minLength} characters long`);
        }

        if (value.length > config.maxLength) {
            errors.push(`Password must be no more than ${config.maxLength} characters long`);
        }

        if (config.requireUppercase && !/[A-Z]/.test(value)) {
            errors.push('Password must contain at least one uppercase letter');
        }

        if (config.requireLowercase && !/[a-z]/.test(value)) {
            errors.push('Password must contain at least one lowercase letter');
        }

        if (config.requireNumbers && !/\d/.test(value)) {
            errors.push('Password must contain at least one number');
        }

        if (config.requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
            errors.push('Password must contain at least one special character');
        }

        // Password strength indicator
        let strength = 0;
        if (value.length >= config.minLength) strength++;
        if (/[A-Z]/.test(value)) strength++;
        if (/[a-z]/.test(value)) strength++;
        if (/\d/.test(value)) strength++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(value)) strength++;

        if (strength < 3) {
            warnings.push('Consider using a stronger password');
        }

        return {
            isValid: errors.length === 0,
            error: errors.length > 0 ? errors.join('; ') : null,
            warning: warnings.length > 0 ? warnings.join('; ') : null,
            strength
        };
    }

    validateUsername(field, value, rule = {}) {
        const config = { ...VALIDATION_CONFIG.username, ...rule };
        const errors = [];

        if (!value) {
            return { isValid: false, error: 'Username is required' };
        }

        if (value.length < config.minLength) {
            errors.push(`Username must be at least ${config.minLength} characters long`);
        }

        if (value.length > config.maxLength) {
            errors.push(`Username must be no more than ${config.maxLength} characters long`);
        }

        if (!config.allowedChars.test(value)) {
            errors.push('Username can only contain letters, numbers, underscores, and hyphens');
        }

        if (config.reservedNames.includes(value.toLowerCase())) {
            errors.push('This username is reserved and cannot be used');
        }

        return {
            isValid: errors.length === 0,
            error: errors.length > 0 ? errors.join('; ') : null
        };
    }

    validateEmail(field, value, rule = {}) {
        const config = { ...VALIDATION_CONFIG.email, ...rule };
        const errors = [];

        if (!value) {
            return { isValid: false, error: 'Email is required' };
        }

        if (value.length > config.maxLength) {
            errors.push(`Email must be no more than ${config.maxLength} characters long`);
        }

        if (!config.pattern.test(value)) {
            errors.push('Please enter a valid email address');
        }

        return {
            isValid: errors.length === 0,
            error: errors.length > 0 ? errors.join('; ') : null
        };
    }

    validateVerificationCode(field, value, rule = {}) {
        const config = { ...VALIDATION_CONFIG.verificationCode, ...rule };
        const errors = [];

        if (!value) {
            return { isValid: false, error: 'Verification code is required' };
        }

        if (value.length !== config.length) {
            errors.push(`Verification code must be exactly ${config.length} digits`);
        }

        if (!config.pattern.test(value)) {
            errors.push('Verification code must contain only numbers');
        }

        return {
            isValid: errors.length === 0,
            error: errors.length > 0 ? errors.join('; ') : null
        };
    }

    validateRequired(field, value, rule = {}) {
        if (!value || value.trim() === '') {
            return { 
                isValid: false, 
                error: rule.message || 'This field is required' 
            };
        }
        return { isValid: true };
    }

    validateLength(field, value, rule = {}) {
        const { min, max, message } = rule;
        const length = value.length;

        if (min && length < min) {
            return { 
                isValid: false, 
                error: message || `Minimum length is ${min} characters` 
            };
        }

        if (max && length > max) {
            return { 
                isValid: false, 
                error: message || `Maximum length is ${max} characters` 
            };
        }

        return { isValid: true };
    }

    validatePattern(field, value, rule = {}) {
        const { pattern, message } = rule;
        
        if (pattern && !pattern.test(value)) {
            return { 
                isValid: false, 
                error: message || 'Invalid format' 
            };
        }

        return { isValid: true };
    }

    // =============================================================================
    // ERROR MANAGEMENT
    // =============================================================================

    /**
     * Show error message for a field
     * @param {string} fieldId - Field ID
     * @param {string} message - Error message
     * @param {string} type - Error type (error, warning, info)
     */
    showFieldError(fieldId, message, type = 'error') {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Remove any existing error messages
        this.clearFieldErrors(fieldId);
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = `field-error-message ${this.getErrorClass(type)}`;
        errorDiv.innerHTML = `<i class="fas fa-${this.getErrorIcon(type)}"></i> ${message}`;
        
        // Find the error container
        let errorContainer = this.findErrorContainer(field);
        
        if (errorContainer) {
            errorContainer.appendChild(errorDiv);
            
            // Add animation
            errorDiv.style.opacity = '0';
            errorDiv.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                errorDiv.style.transition = `all ${VALIDATION_CONFIG.ui.animationDuration}ms ease`;
                errorDiv.style.opacity = '1';
                errorDiv.style.transform = 'translateY(0)';
            }, 10);
        }
    }

    /**
     * Clear error messages for a field
     * @param {string} fieldId - Field ID
     */
    clearFieldErrors(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        const fieldContainer = this.findErrorContainer(field);
        if (fieldContainer) {
            const existingErrors = fieldContainer.querySelectorAll('.field-error-message');
            existingErrors.forEach(error => {
                error.style.transition = `all ${VALIDATION_CONFIG.ui.animationDuration}ms ease`;
                error.style.opacity = '0';
                error.style.transform = 'translateY(-10px)';
                
                setTimeout(() => error.remove(), VALIDATION_CONFIG.ui.animationDuration);
            });
        }
    }

    /**
     * Clear all error messages
     */
    clearAllFieldErrors() {
        const existingErrors = document.querySelectorAll('.field-error-message');
        existingErrors.forEach(error => {
            error.style.transition = `all ${VALIDATION_CONFIG.ui.animationDuration}ms ease`;
            error.style.opacity = '0';
            error.style.transform = 'translateY(-10px)';
            
            setTimeout(() => error.remove(), VALIDATION_CONFIG.ui.animationDuration);
        });
    }

    /**
     * Find the appropriate error container for a field
     * @param {HTMLElement} field - Field element
     * @returns {HTMLElement|null} Error container element
     */
    findErrorContainer(field) {
        // Look for specific error container
        let errorContainer = field.closest('.form-group')?.querySelector('.error-message-container');
        
        // If no specific container, look for common containers
        if (!errorContainer) {
            errorContainer = field.closest('.mb-4, .mb-3, .form-group');
        }
        
        // If still no container, create one
        if (!errorContainer) {
            errorContainer = field.parentElement;
        }
        
        return errorContainer;
    }

    /**
     * Get CSS class for error type
     * @param {string} type - Error type
     * @returns {string} CSS class
     */
    getErrorClass(type) {
        switch (type) {
            case 'warning': return 'text-warning';
            case 'info': return 'text-info';
            case 'success': return 'text-success';
            default: return 'text-danger';
        }
    }

    /**
     * Get icon for error type
     * @param {string} type - Error type
     * @returns {string} Icon class
     */
    getErrorIcon(type) {
        switch (type) {
            case 'warning': return 'exclamation-triangle';
            case 'info': return 'info-circle';
            case 'success': return 'check-circle';
            default: return 'exclamation-circle';
        }
    }

    // =============================================================================
    // FORM SUBMISSION HANDLING
    // =============================================================================

    /**
     * Initialize form validation and submission handling
     * @param {string} formId - Form ID
     * @param {Object} fieldRules - Field validation rules
     * @param {Object} options - Additional options
     */
    initializeFormValidation(formId, fieldRules, options = {}) {
        const form = document.getElementById(formId);
        if (!form) return;

        const {
            preventSubmit = true,
            showErrors = true,
            autoValidate = true,
            onSubmit = null
        } = options;

        // Disable native validation
        form.setAttribute('novalidate', true);
        
        // Handle form submission
        form.addEventListener('submit', (e) => {
            if (preventSubmit) {
                e.preventDefault();
            }
            
            const validationResult = this.validateForm(form, fieldRules);
            
            if (showErrors) {
                this.displayFormValidationResults(validationResult);
            }
            
            if (validationResult.isValid && onSubmit) {
                onSubmit(form, validationResult);
            }
            
            return validationResult.isValid;
        });

        // Auto-validation on input
        if (autoValidate) {
            this.initializeAutoValidation(form, fieldRules);
        }

        // Handle form submission errors
        form.addEventListener('error', (e) => {
            this.restoreSubmitButton(form);
        });

        // Handle form submission failures
        form.addEventListener('submit', (e) => {
            window.addEventListener('error', () => {
                this.restoreSubmitButton(form);
            });
        }, { once: true });
    }

    /**
     * Initialize automatic validation on input
     * @param {HTMLElement} form - Form element
     * @param {Object} fieldRules - Field validation rules
     */
    initializeAutoValidation(form, fieldRules) {
        Object.keys(fieldRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"], #${fieldName}`);
            if (field) {
                // Clear errors on input
                field.addEventListener('input', () => {
                    this.clearFieldErrors(field.id || field.name);
                    field.classList.remove('is-invalid', 'is-valid');
                });

                // Validate on blur
                field.addEventListener('blur', () => {
                    const result = this.validateField(field, fieldRules[fieldName]);
                    if (!result.isValid) {
                        this.showFieldError(field.id || field.name, result.errors[0], 'error');
                        field.classList.add('is-invalid');
                    } else {
                        field.classList.remove('is-invalid');
                        field.classList.add('is-valid');
                    }
                });
            }
        });
    }

    /**
     * Display form validation results
     * @param {Object} validationResult - Validation result object
     */
    displayFormValidationResults(validationResult) {
        validationResult.fieldResults.forEach((result, fieldName) => {
            if (!result.isValid) {
                this.showFieldError(fieldName, result.errors[0], 'error');
            }
        });
    }

    // =============================================================================
    // SUBMIT BUTTON MANAGEMENT
    // =============================================================================

    /**
     * Disable submit button and show loading state
     * @param {HTMLElement} form - Form element
     * @param {string} loadingText - Loading text to display
     */
    disableSubmitButton(form, loadingText = 'Processing...') {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton && !submitButton.disabled) {
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.innerHTML;
            submitButton.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`;
            submitButton.dataset.isProcessing = 'true';
            
            // Re-enable button after 10 seconds as fallback
            setTimeout(() => {
                if (submitButton.disabled && submitButton.dataset.isProcessing === 'true') {
                    this.restoreSubmitButton(form);
                }
            }, 10000);
        }
    }

    /**
     * Restore submit button to original state
     * @param {HTMLElement} form - Form element
     */
    restoreSubmitButton(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton && submitButton.disabled) {
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.dataset.originalText || 'Submit';
            submitButton.dataset.isProcessing = 'false';
        }
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
     * Clean browser history to prevent form resubmission
     */
    cleanBrowserHistory() {
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', window.location.href);
        }
        
        if (window.performance && window.performance.navigation) {
            if (window.performance.navigation.type === window.performance.navigation.TYPE_BACK_FORWARD) {
                window.location.reload();
            }
        }
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeGlobalValidation() {
        // Look for forms with data-validation attribute
        document.querySelectorAll('form[data-validation]').forEach(form => {
            try {
                const validationRules = JSON.parse(form.dataset.validation);
                this.initializeFormValidation(form.id, validationRules);
            } catch (error) {
                console.warn('Invalid validation rules for form:', form.id);
            }
        });
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        // Clear all debounce timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();
        
        this.isInitialized = false;
        console.log('✅ Form Validation System destroyed');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.formValidator = new FormValidator();

// Make functions globally accessible
window.validateField = (field, rules) => window.formValidator.validateField(field, rules);
window.validateForm = (form, fieldRules) => window.formValidator.validateForm(form, fieldRules);
window.showFieldError = (fieldId, message, type) => window.formValidator.showFieldError(fieldId, message, type);
window.clearFieldErrors = (fieldId) => window.formValidator.clearFieldErrors(fieldId);
window.clearAllFieldErrors = () => window.formValidator.clearAllFieldErrors();
window.initializeFormValidation = (formId, fieldRules, options) => window.formValidator.initializeFormValidation(formId, fieldRules, options);
window.disableSubmitButton = (form, loadingText) => window.formValidator.disableSubmitButton(form, loadingText);
window.restoreSubmitButton = (form) => window.formValidator.restoreSubmitButton(form);

// =============================================================================
// LEGACY SUPPORT
// =============================================================================

// Support for existing validation functions
window.validatePassword = (input) => {
    const result = window.formValidator.validatePassword(input, input.value);
    if (!result.isValid) {
        window.formValidator.showFieldError(input.id, result.error, 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
};

window.validateUsername = (input) => {
    const result = window.formValidator.validateUsername(input, input.value);
    if (!result.isValid) {
        window.formValidator.showFieldError(input.id, result.error, 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    return true;
};

// =============================================================================
// DEBUG AND VERIFICATION
// =============================================================================

window.debugValidationSystem = function() {
    console.log('🔍 Debugging Form Validation System...');
    
    const functions = [
        'validateField',
        'validateForm',
        'showFieldError',
        'clearFieldErrors',
        'clearAllFieldErrors',
        'initializeFormValidation',
        'validatePassword',
        'validateUsername'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName}: Available`);
        } else {
            console.log(`❌ ${funcName}: Missing`);
        }
    });
    
    console.log(`✅ Registered validators: ${window.formValidator.validators.size}`);
    console.log('🔍 Form Validation System Debug Complete');
};

// Auto-debug on page load if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof window.debugValidationSystem === 'function') {
                window.debugValidationSystem();
            }
        }, 1000);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormValidator;
}