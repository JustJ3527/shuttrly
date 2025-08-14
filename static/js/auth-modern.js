/**
 * Modern Authentication System
 * Refactored authentication functionality using modular architecture
 * 
 * @author Shuttrly
 * @version 2.0.0
 */

// =============================================================================
// AUTHENTICATION CONFIGURATION
// =============================================================================

const AUTH_CONFIG = {
    // Page configurations
    pages: {
        login: {
            steps: {
                login: {
                    formFields: { autoFocus: true, passwordToggles: true }
                },
                email_2fa: {
                    countdownTimer: {
                        canResend: 'canResendInitial',
                        timeUntilResend: 'timeUntilResend',
                        timerContainerId: 'resend-timer-container',
                        buttonContainerId: 'resend-button-container'
                    },
                    resendCode: {
                        resendBtnId: 'resend-code-btn',
                        pageType: 'login',
                        step: 'email_2fa'
                    },
                    verificationCode: true,
                    formFields: {
                        autoFocus: false,
                        excludeSteps: ['email_2fa', 'totp_2fa']
                    }
                },
                choose_2fa: {
                    twofaMethods: true,
                    formFields: { autoFocus: true }
                },
                totp_2fa: {
                    verificationCode: true,
                    formFields: {
                        autoFocus: false,
                        excludeSteps: ['email_2fa', 'totp_2fa']
                    }
                }
            }
        },
        register: {
            steps: {
                '2': {
                    countdownTimer: {
                        canResend: 'canResend',
                        timeUntilResend: 'timeUntilResend',
                        timerContainerId: 'resend-timer-container',
                        buttonContainerId: 'resend-button-container',
                        delay: 'emailCodeResendDelay'
                    },
                    resendCode: {
                        resendBtnId: 'resend-code-btn',
                        pageType: 'register',
                        step: '2'
                    },
                    verificationCode: true,
                    formFields: { autoFocus: false, excludeSteps: ['2'] }
                },
                '4': {
                    usernameVerification: true,
                    formFields: { autoFocus: true }
                },
                '5': {
                    passwordValidation: true,
                    passwordToggles: true,
                    formFields: { autoFocus: true, passwordToggles: true }
                }
            }
        },
        password_reset_confirm: {
            steps: {
                form: {
                    passwordValidation: true,
                    passwordToggles: true,
                    formFields: { autoFocus: true, passwordToggles: true }
                }
            }
        }
    }
};

// =============================================================================
// AUTHENTICATION CORE SYSTEM
// =============================================================================

class ModernAuth {
    constructor() {
        this.currentPage = this.detectCurrentPage();
        this.currentStep = this.detectCurrentStep();
        this.isInitialized = false;
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.initializePage();
        this.initializeFormValidation();
        this.initializeCountdowns();
        this.initialize2FA();
        this.initializeUsernameVerification();
        this.initializePasswordValidation();
        this.initializePasswordToggles();
        this.initializeAutoFocus();
        
        this.isInitialized = true;
        console.log('🔐 Modern Auth System initialized for:', this.currentPage);
    }

    // =============================================================================
    // PAGE DETECTION
    // =============================================================================

    detectCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('/login')) return 'login';
        if (path.includes('/register')) return 'register';
        if (path.includes('/password-reset')) return 'password_reset_confirm';
        return 'unknown';
    }

    detectCurrentStep() {
        // Extract step from URL or form data
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        
        if (step) return step;
        
        // Check for step in form data
        const form = document.querySelector('form');
        if (form) {
            const stepInput = form.querySelector('input[name="step"]');
            if (stepInput) return stepInput.value;
        }
        
        return '1';
    }

    // =============================================================================
    // PAGE INITIALIZATION
    // =============================================================================

    initializePage() {
        const pageConfig = AUTH_CONFIG.pages[this.currentPage];
        if (!pageConfig) return;

        const stepConfig = pageConfig.steps[this.currentStep];
        if (!stepConfig) return;

        // Initialize step-specific functionality
        if (stepConfig.countdownTimer) {
            this.initializeCountdownForStep(stepConfig.countdownTimer);
        }

        if (stepConfig.resendCode) {
            this.initializeResendCode(stepConfig.resendCode);
        }

        if (stepConfig.verificationCode) {
            this.initializeVerificationCode();
        }

        if (stepConfig.twofaMethods) {
            this.initialize2FAMethodSelection();
        }

        if (stepConfig.usernameVerification) {
            this.initializeUsernameVerification();
        }

        if (stepConfig.passwordValidation) {
            this.initializePasswordValidation();
        }

        if (stepConfig.passwordToggles) {
            this.initializePasswordToggles();
        }

        if (stepConfig.formFields?.autoFocus) {
            this.initializeAutoFocus();
        }
    }

    // =============================================================================
    // FORM VALIDATION
    // =============================================================================

    initializeFormValidation() {
        const form = document.getElementById("login-form") || document.getElementById("registration-form");
        if (!form) return;

        // Use the form validation system
        const fieldRules = this.getFieldValidationRules();
        
        window.formValidator.initializeFormValidation(form.id, fieldRules, {
            preventSubmit: true,
            showErrors: true,
            autoValidate: true,
            onSubmit: (form, validationResult) => {
                this.handleFormSubmission(form, validationResult);
            }
        });
    }

    getFieldValidationRules() {
        const rules = {};
        
        // Add required field validation for all required inputs
        document.querySelectorAll('[required]').forEach(input => {
            rules[input.name || input.id] = [
                { type: 'required' }
            ];
        });

        // Add specific validation rules based on page and step
        if (this.currentPage === 'register' && this.currentStep === '5') {
            rules['id_password1'] = [
                { type: 'password' }
            ];
            rules['id_password2'] = [
                { type: 'required' },
                { type: 'pattern', pattern: /^$/, message: 'Passwords must match' }
            ];
        }

        if (this.currentPage === 'password_reset_confirm') {
            rules['id_new_password1'] = [
                { type: 'password' }
            ];
            rules['id_new_password2'] = [
                { type: 'required' },
                { type: 'pattern', pattern: /^$/, message: 'Passwords must match' }
            ];
        }

        return rules;
    }

    handleFormSubmission(form, validationResult) {
        if (!validationResult.isValid) {
            return false;
        }

        // Disable submit button
        window.formValidator.disableSubmitButton(form, 'Processing...');

        // Page-specific validations
        if (this.currentPage === 'register') {
            if (this.currentStep === "4" && !this.validateUsername()) {
                window.formValidator.restoreSubmitButton(form);
                return false;
            }
            
            if (this.currentStep === "5") {
                const passwordValidation = this.validatePassword();
                if (!passwordValidation.isValid) {
                    window.formValidator.showFieldError('id_password1', passwordValidation.message, 'error');
                    window.formValidator.restoreSubmitButton(form);
                    return false;
                }
            }
        }

        if (this.currentPage === 'password_reset_confirm') {
            const passwordValidation = this.validatePassword();
            if (!passwordValidation.isValid) {
                window.formValidator.showFieldError('id_new_password1', passwordValidation.message, 'error');
                window.formValidator.restoreSubmitButton(form);
                return false;
            }
        }

        // Form is valid, allow submission
        return true;
    }

    // =============================================================================
    // COUNTDOWN MANAGEMENT
    // =============================================================================

    initializeCountdownForStep(countdownConfig) {
        const {
            canResend,
            timeUntilResend,
            timerContainerId,
            buttonContainerId
        } = countdownConfig;

        // Use the countdown system
        window.countdownManager.initializeEmailCountdown({
            timeUntilResend: window[timeUntilResend] || 0,
            timerId: 'timer',
            countdownId: 'countdown',
            resendFormId: 'resend-form',
            canResend: window[canResend] || false
        });
    }

    initializeCountdowns() {
        // Look for countdown elements on the page
        document.querySelectorAll('[data-countdown-type]').forEach(countdown => {
            const type = countdown.dataset.countdownType;
            const timeUntilResend = parseInt(countdown.dataset.timeUntilResend || '0');
            const canResend = countdown.dataset.canResend === 'true';

            if (type === 'email') {
                window.countdownManager.initializeEmailCountdown({
                    timeUntilResend,
                    timerId: countdown.querySelector('[id*="timer"]')?.id,
                    countdownId: countdown.id,
                    resendFormId: countdown.querySelector('[id*="resend"]')?.id,
                    canResend
                });
            }
        });
    }

    // =============================================================================
    // RESEND CODE FUNCTIONALITY
    // =============================================================================

    initializeResendCode(resendConfig) {
        const resendBtn = document.getElementById(resendConfig.resendBtnId);
        if (!resendBtn) return;

        resendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleResendCode(resendConfig);
        });
    }

    handleResendCode(resendConfig) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
            <input type="hidden" name="action" value="resend_code">
            <input type="hidden" name="page_type" value="${resendConfig.pageType}">
            <input type="hidden" name="step" value="${resendConfig.step}">
        `;

        document.body.appendChild(form);
        form.submit();
    }

    // =============================================================================
    // VERIFICATION CODE
    // =============================================================================

    initializeVerificationCode() {
        const codeInput = document.querySelector('#id_twofa_code, #id_verification_code');
        if (!codeInput) return;

        // Use the 2FA system for verification code handling
        // The 2FA system will automatically handle verification code inputs
        console.log('Verification code input initialized');
    }

    // =============================================================================
    // 2FA METHOD SELECTION
    // =============================================================================

    initialize2FAMethodSelection() {
        const radioGroup = document.querySelectorAll('input[name="twofa_method"]');
        if (!radioGroup.length) return;

        radioGroup.forEach(radio => {
            radio.addEventListener('change', () => {
                this.handle2FAMethodChange(radio.value);
            });
        });
    }

    handle2FAMethodChange(method) {
        // Handle 2FA method selection
        console.log('2FA method selected:', method);
        
        // You can add specific logic here for different 2FA methods
        if (method === 'email') {
            // Handle email 2FA
        } else if (method === 'totp') {
            // Handle TOTP 2FA
        }
    }

    // =============================================================================
    // USERNAME VERIFICATION
    // =============================================================================

    initializeUsernameVerification() {
        const usernameInput = document.getElementById('id_username');
        if (!usernameInput) return;

        // Use debounced validation
        const debouncedValidation = window.uiUtils.debounce(
            () => this.validateUsernameField(usernameInput),
            UI_CONFIG.debounce.searchDelay,
            'username_validation'
        );

        usernameInput.addEventListener('input', debouncedValidation);
        usernameInput.addEventListener('blur', () => this.validateUsernameField(usernameInput));
    }

    validateUsernameField(input) {
        const username = input.value.trim();
        
        if (!username) {
            window.formValidator.showFieldError(input.id, 'Username is required', 'error');
            input.classList.add('is-invalid');
            return false;
        }

        // Use the form validation system
        const result = window.formValidator.validateUsername(input, username);
        
        if (!result.isValid) {
            window.formValidator.showFieldError(input.id, result.error, 'error');
            input.classList.add('is-invalid');
            return false;
        }

        // Check availability
        this.checkUsernameAvailability(username, input);
        return true;
    }

    checkUsernameAvailability(username, input) {
        const feedback = input.parentElement.querySelector('.username-feedback');
        if (!feedback) return;

        feedback.innerHTML = '<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Checking availability...</span>';

        // Simulate API call (replace with actual API call)
        setTimeout(() => {
            if (username.length >= 3) {
                feedback.innerHTML = '<span class="text-success"><i class="fas fa-check-circle"></i> Username available</span>';
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                feedback.innerHTML = '<span class="text-warning"><i class="fas fa-exclamation-triangle"></i> Username too short</span>';
            }
        }, 1000);
    }

    validateUsername() {
        const usernameInput = document.getElementById('id_username');
        if (!usernameInput) return true;

        return this.validateUsernameField(usernameInput);
    }

    // =============================================================================
    // PASSWORD VALIDATION
    // =============================================================================

    initializePasswordValidation() {
        const passwordInputs = document.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            input.addEventListener('blur', () => this.validatePasswordField(input));
            input.addEventListener('input', () => {
                window.formValidator.clearFieldErrors(input.id);
                input.classList.remove('is-invalid', 'is-valid');
            });
        });
    }

    validatePasswordField(input) {
        // Use the form validation system
        const result = window.formValidator.validatePassword(input, input.value);
        
        if (!result.isValid) {
            window.formValidator.showFieldError(input.id, result.error, 'error');
            input.classList.add('is-invalid');
            return false;
        }

        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }

    validatePassword() {
        const passwordInput = document.getElementById('id_password1') || document.getElementById('id_new_password1');
        if (!passwordInput) return { isValid: true };

        return window.formValidator.validatePassword(passwordInput, passwordInput.value);
    }

    // =============================================================================
    // PASSWORD TOGGLES
    // =============================================================================

    initializePasswordToggles() {
        // Use the UI utils system
        window.uiUtils.initializePasswordToggles();
    }

    // =============================================================================
    // AUTO FOCUS
    // =============================================================================

    initializeAutoFocus() {
        const form = document.querySelector('form');
        if (!form) return;

        // Focus on first input field
        const firstInput = form.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstInput) {
            firstInput.focus();
        }
    }

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    cleanBrowserHistory() {
        // Use the form validation system utility
        window.formValidator.cleanBrowserHistory();
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        this.isInitialized = false;
        console.log('🔐 Modern Auth System destroyed');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.modernAuth = new ModernAuth();

// Make functions globally accessible for backward compatibility
window.initializeFormValidation = () => window.modernAuth.initializeFormValidation();
window.validatePassword = (input) => window.modernAuth.validatePasswordField(input);
window.validateUsername = (input) => window.modernAuth.validateUsernameField(input);
window.cleanBrowserHistory = () => window.modernAuth.cleanBrowserHistory();

// =============================================================================
// DEBUG AND VERIFICATION
// =============================================================================

window.debugModernAuth = function() {
    console.log('🔍 Debugging Modern Auth System...');
    
    const functions = [
        'initializeFormValidation',
        'validatePassword',
        'validateUsername',
        'cleanBrowserHistory'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName}: Available`);
        } else {
            console.log(`❌ ${funcName}: Missing`);
        }
    });
    
    console.log(`🔐 Current page: ${window.modernAuth.currentPage}`);
    console.log(`🔐 Current step: ${window.modernAuth.currentStep}`);
    console.log('🔍 Modern Auth System Debug Complete');
};

// Auto-debug on page load if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof window.debugModernAuth === 'function') {
                window.debugModernAuth();
            }
        }, 1000);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernAuth;
}