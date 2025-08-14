/**
 * 2FA Management System
 * Handles all Two-Factor Authentication functionality
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

// =============================================================================
// 2FA CONFIGURATION
// =============================================================================

const TWOFA_CONFIG = {
    // TOTP settings
    totp: {
        codeLength: 6,
        codePattern: /^\d{6}$/,
        autoSubmit: true
    },
    
    // Email 2FA settings
    email: {
        codeLength: 6,
        codePattern: /^\d{6}$/,
        autoSubmit: true,
        resendDelay: 60 // seconds
    },
    
    // UI settings
    ui: {
        animationDuration: 500,
        fadeInDelay: 100,
        errorDisplayTime: 3000
    }
};

// =============================================================================
// 2FA CORE SYSTEM
// =============================================================================

class TwoFactorAuth {
    constructor() {
        this.isInitialized = false;
        this.currentMethod = null;
        this.countdownTimers = new Map();
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.initializeEventListeners();
        this.initialize2FASections();
        this.initializeTOTPCopy();
        this.initializeVerificationInputs();
        this.initializeCountdownTimers();
        this.initializeAnimations();
        
        this.isInitialized = true;
        console.log('🔐 2FA System initialized');
    }

    // =============================================================================
    // EMAIL 2FA MANAGEMENT
    // =============================================================================

    showEnableEmail2FA() {
        this.toggle2FAForm('enable-email-2fa-form', 'enable-email-2fa-button', true);
        this.initializeFormValidation('enable-email-2fa-form');
    }

    hideEnableEmail2FA() {
        this.toggle2FAForm('enable-email-2fa-form', 'enable-email-2fa-button', false);
        this.clearAllFieldErrors();
    }

    showDisableEmail2FA() {
        this.toggle2FAForm('disable-email-2fa-form', 'disable-email-2fa-button', true);
        this.initializeFormValidation('disable-email-2fa-form');
    }

    hideDisableEmail2FA() {
        this.toggle2FAForm('disable-email-2fa-form', 'disable-email-2fa-button', false);
        this.clearAllFieldErrors();
    }

    cancelEmail2FASetup() {
        if (this.confirmAction('Are you sure you want to cancel Email 2FA setup? This will clear any pending verification.')) {
            this.submitCancelAction();
        }
    }

    // =============================================================================
    // TOTP 2FA MANAGEMENT
    // =============================================================================

    showEnableTOTP2FA() {
        this.toggle2FAForm('enable-totp-2fa-form', 'enable-totp-2fa-button', true);
        this.initializeFormValidation('enable-totp-2fa-form');
    }

    hideEnableTOTP2FA() {
        this.toggle2FAForm('enable-totp-2fa-form', 'enable-totp-2fa-button', false);
        this.clearAllFieldErrors();
    }

    showDisableTOTP2FA() {
        this.toggle2FAForm('disable-totp-2fa-form', 'disable-totp-2fa-button', true);
        this.initializeFormValidation('disable-totp-2fa-form');
    }

    hideDisableTOTP2FA() {
        this.toggle2FAForm('disable-totp-2fa-form', 'disable-totp-2fa-button', false);
        this.clearAllFieldErrors();
    }

    cancelTOTP2FASetup() {
        if (this.confirmAction('Are you sure you want to cancel Authenticator App 2FA setup? This will clear any pending verification.')) {
            this.submitCancelAction();
        }
    }

    // =============================================================================
    // TRUSTED DEVICES MANAGEMENT
    // =============================================================================

    toggleDeviceDetails(header) {
        const details = header.nextElementSibling;
        const isExpanded = header.classList.contains('expanded');
        
        if (isExpanded) {
            // Collapse
            header.classList.remove('expanded');
            details.style.display = 'none';
            details.classList.remove('slide-down');
        } else {
            // Expand
            header.classList.add('expanded');
            details.style.display = 'block';
            details.classList.add('slide-down');
        }
    }

    // =============================================================================
    // TOTP URI COPY FUNCTIONALITY
    // =============================================================================

    initializeTOTPCopy() {
        const copyBtn = document.getElementById('copyTotpUriBtn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyTOTPURI());
        }
    }

    copyTOTPURI() {
        const input = document.getElementById('totpUriInput');
        if (!input) return;

        input.select();
        input.setSelectionRange(0, 99999); // For mobile devices
        
        navigator.clipboard.writeText(input.value).then(() => {
            this.showCopyMessage();
        }).catch(err => {
            this.showFieldError('totpUriInput', 'Error copying setup key: ' + err, 'error');
        });
    }

    showCopyMessage() {
        const msg = document.getElementById('copyMessage');
        if (msg) {
            msg.classList.add('show');
            setTimeout(() => { 
                msg.classList.remove('show'); 
            }, TWOFA_CONFIG.ui.errorDisplayTime);
        }
    }

    // =============================================================================
    // VERIFICATION CODE INPUTS
    // =============================================================================

    initializeVerificationInputs() {
        // Email verification codes
        document.querySelectorAll('.verification-code-input, input[name*="email_code"]').forEach(input => {
            this.setupVerificationInput(input, TWOFA_CONFIG.email);
        });

        // TOTP verification codes
        document.querySelectorAll('input[name*="totp_code"], input[name*="disable_totp_code"]').forEach(input => {
            this.setupVerificationInput(input, TWOFA_CONFIG.totp);
        });
    }

    setupVerificationInput(input, config) {
        input.addEventListener('input', (e) => {
            // Only allow numbers
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            
            // Auto-submit when code length is reached
            if (config.autoSubmit && e.target.value.length === config.codeLength) {
                e.target.closest('form').submit();
            }
        });

        // Add validation on blur
        input.addEventListener('blur', () => {
            this.validateVerificationCode(input, config);
        });
    }

    validateVerificationCode(input, config) {
        const code = input.value.trim();
        
        if (!code) {
            this.showFieldError(input.id, 'Verification code is required', 'error');
            input.classList.add('is-invalid');
            return false;
        }
        
        if (code.length !== config.codeLength || !config.codePattern.test(code)) {
            this.showFieldError(input.id, `Please enter a valid ${config.codeLength}-digit code`, 'error');
            input.classList.add('is-invalid');
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }

    // =============================================================================
    // COUNTDOWN TIMERS
    // =============================================================================

    initializeCountdownTimers() {
        const countdownInfo = document.querySelector('.countdown-info');
        if (countdownInfo && countdownInfo.querySelector('#timer')) {
            const timerElement = document.getElementById('timer');
            const timeUntilResend = parseInt(timerElement.textContent);
            
            if (timeUntilResend > 0) {
                this.startCountdown(timeUntilResend, timerElement, countdownInfo);
            }
        }
    }

    startCountdown(initialTime, timerElement, countdownElement) {
        let timeLeft = initialTime;
        
        const updateTimer = () => {
            if (timeLeft <= 0) {
                // Show resend form when timer reaches zero
                countdownElement.style.display = "none";
                const resendForm = document.querySelector('.resend-section form');
                if (resendForm) {
                    resendForm.style.display = "block";
                }
                return;
            }

            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;

            if (minutes > 0) {
                timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            } else {
                timerElement.textContent = seconds;
            }

            timeLeft--;
        };

        updateTimer();
        const intervalId = setInterval(updateTimer, 1000);
        
        // Store interval ID for cleanup
        this.countdownTimers.set(countdownElement, intervalId);
    }

    // =============================================================================
    // FORM VALIDATION
    // =============================================================================

    initializeFormValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', (e) => {
            if (!this.validate2FAForm(formId)) {
                e.preventDefault();
                return false;
            }
        });
    }

    validate2FAForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        let isValid = true;
        
        // Validate password fields
        const passwordInputs = form.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            if (!this.validate2FAPassword(input)) {
                isValid = false;
            }
        });
        
        // Validate TOTP code fields if present
        const totpInputs = form.querySelectorAll('input[name*="totp_code"]');
        totpInputs.forEach(input => {
            if (!this.validateVerificationCode(input, TWOFA_CONFIG.totp)) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    validate2FAPassword(input) {
        const password = input.value.trim();
        
        if (!password) {
            this.showFieldError(input.id, 'Password is required', 'error');
            input.classList.add('is-invalid');
            return false;
        }
        
        if (password.length < 8) {
            this.showFieldError(input.id, 'Password must be at least 8 characters long', 'error');
            input.classList.add('is-invalid');
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }

    // =============================================================================
    // UI UTILITIES
    // =============================================================================

    toggle2FAForm(formId, buttonId, showForm) {
        const form = document.getElementById(formId);
        const button = document.getElementById(buttonId);
        
        if (form && button) {
            form.style.display = showForm ? 'block' : 'none';
            button.style.display = showForm ? 'none' : 'block';
        }
    }

    initialize2FASections() {
        // Add fade-in animation to 2FA sections
        document.querySelectorAll('.twofa-method-section').forEach((section, index) => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                section.style.transition = `all ${TWOFA_CONFIG.ui.animationDuration}ms ease`;
                section.style.opacity = '1';
                section.style.transform = 'translateY(0)';
            }, index * TWOFA_CONFIG.ui.fadeInDelay);
        });
    }

    initializeAnimations() {
        // Initialize any additional animations
        this.initialize2FASections();
    }

    // =============================================================================
    // ERROR HANDLING
    // =============================================================================

    // showFieldError(fieldId, message, errorType = 'error') {
    //     const field = document.getElementById(fieldId);
    //     if (!field) return;

    //     // Remove any existing error messages
    //     this.clearFieldErrors(fieldId);
        
    //     // Create error message element
    //     const errorDiv = document.createElement('div');
    //     errorDiv.className = `field-error-message ${errorType === 'error' ? 'text-danger' : 'text-warning'}`;
    //     errorDiv.innerHTML = `<i class="fas fa-${errorType === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i> ${message}`;
        
    //     // Find the error container
    //     let errorContainer = field.closest('.form-group')?.querySelector('.error-message-container');
        
    //     // If no error container found, look for other common containers
    //     if (!errorContainer) {
    //         errorContainer = field.closest('.mb-4, .mb-3, .form-group');
    //     }
        
    //     if (errorContainer) {
    //         errorContainer.appendChild(errorDiv);
    //     }
    // }

    clearFieldErrors(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        const fieldContainer = field.closest('.mb-4, .mb-3, .form-group');
        if (fieldContainer) {
            const existingErrors = fieldContainer.querySelectorAll('.field-error-message');
            existingErrors.forEach(error => error.remove());
        }
    }

    clearAllFieldErrors() {
        const existingErrors = document.querySelectorAll('.field-error-message');
        existingErrors.forEach(error => error.remove());
    }

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    confirmAction(message) {
        return confirm(message);
    }

    submitCancelAction() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
            <input type="hidden" name="action" value="cancel">
        `;
        document.body.appendChild(form);
        form.submit();
    }

    // =============================================================================
    // EVENT LISTENERS
    // =============================================================================

    initializeEventListeners() {
        // Password toggle functionality for 2FA forms
        this.initializePasswordToggles();
        
        // Clear errors on input
        document.addEventListener('input', (e) => {
            if (e.target.closest('.inline-2fa-form')) {
                this.clearFieldErrors(e.target.id);
                e.target.classList.remove('is-invalid', 'is-valid');
            }
        });
    }

    initializePasswordToggles() {
        const container = document.querySelector('.settings-container') || document.body;
        const toggleButtons = container.querySelectorAll('.password-toggle-icon');
        
        toggleButtons.forEach(toggleBtn => {
            const passwordField = toggleBtn.previousElementSibling;
            if (passwordField && passwordField.type === 'password') {
                toggleBtn.addEventListener('click', () => {
                    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordField.setAttribute('type', type);
                    
                    // Toggle icon
                    toggleBtn.classList.toggle('fa-eye');
                    toggleBtn.classList.toggle('fa-eye-slash');
                });
            }
        });
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        // Clear all countdown timers
        this.countdownTimers.forEach(intervalId => {
            clearInterval(intervalId);
        });
        this.countdownTimers.clear();
        
        this.isInitialized = false;
        console.log('🔐 2FA System destroyed');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.twoFactorAuth = new TwoFactorAuth();

// Make functions globally accessible for HTML onclick attributes
window.showEnableEmail2FA = () => window.twoFactorAuth.showEnableEmail2FA();
window.hideEnableEmail2FA = () => window.twoFactorAuth.hideEnableEmail2FA();
window.showDisableEmail2FA = () => window.twoFactorAuth.showDisableEmail2FA();
window.hideDisableEmail2FA = () => window.twoFactorAuth.hideDisableEmail2FA();
window.cancelEmail2FASetup = () => window.twoFactorAuth.cancelEmail2FASetup();

window.showEnableTOTP2FA = () => window.twoFactorAuth.showEnableTOTP2FA();
window.hideEnableTOTP2FA = () => window.twoFactorAuth.hideEnableTOTP2FA();
window.showDisableTOTP2FA = () => window.twoFactorAuth.showDisableTOTP2FA();
window.hideDisableTOTP2FA = () => window.twoFactorAuth.hideDisableTOTP2FA();
window.cancelTOTP2FASetup = () => window.twoFactorAuth.cancelTOTP2FASetup();

window.toggleDeviceDetails = (header) => window.twoFactorAuth.toggleDeviceDetails(header);

// =============================================================================
// DEBUG AND VERIFICATION
// =============================================================================

window.debug2FAFunctions = function() {
    console.log('🔍 Debugging 2FA Functions...');
    
    const functions = [
        'showEnableEmail2FA',
        'hideEnableEmail2FA', 
        'showDisableEmail2FA',
        'hideDisableEmail2FA',
        'cancelEmail2FASetup',
        'showEnableTOTP2FA',
        'hideEnableTOTP2FA',
        'showDisableTOTP2FA',
        'hideDisableTOTP2FA',
        'cancelTOTP2FASetup',
        'toggleDeviceDetails'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName}: Available`);
        } else {
            console.log(`❌ ${funcName}: Missing`);
        }
    });
    
    console.log('🔍 2FA Functions Debug Complete');
};

// Auto-debug on page load if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof window.debug2FAFunctions === 'function') {
                window.debug2FAFunctions();
            }
        }, 1000);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TwoFactorAuth;
}