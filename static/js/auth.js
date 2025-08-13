// auth.js - Unified JavaScript functionality for authentication pages (login & register)
// Handles form validation, 2FA, countdown timers, and user interactions

// =============================================================================
// GLOBAL VARIABLES AND UTILITIES
// =============================================================================

let usernameTimeout;
let timeLeft;

// Messages are now handled by Django's message system via {% display_messages_with_auto_clear %}
// This ensures consistency across the application

// =============================================================================
// PAGE CONFIGURATION SYSTEM (UNIFIED)
// =============================================================================

// Configuration for different pages and their required functionality
const PAGE_CONFIGS = {
    'login': {
        'login': {
            formFields: {
                autoFocus: true,
                passwordToggles: true
            }
        },
        'email_2fa': {
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
        'choose_2fa': {
            twofaMethods: true,
            formFields: {
                autoFocus: true
            }
        },
        'totp_2fa': {
            verificationCode: true,
            formFields: {
                autoFocus: false,
                excludeSteps: ['email_2fa', 'totp_2fa']
            }
        }
    },
    'register': {
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
            formFields: {
                autoFocus: false,
                excludeSteps: ['2']
            }
        },
        '4': {
            usernameVerification: true,
            formFields: {
                autoFocus: true
            }
        },
        '5': {
            passwordValidation: true,
            passwordToggles: true,
            formFields: {
                autoFocus: true,
                passwordToggles: true
            }
        }
    },
    'password_reset_confirm': {
        'form': {
            passwordValidation: true,
            passwordToggles: true,
            formFields: {
                autoFocus: true,
                passwordToggles: true
            }
        }
    }
};

// =============================================================================
// FORM VALIDATION SYSTEM (UNIFIED)
// =============================================================================

function initializeFormValidation() {
    const form = document.getElementById("login-form") || document.getElementById("registration-form");
    
    if (form) {
        // Disable native validation to take control
        form.setAttribute("novalidate", true);
        
        // Handle form submission errors and restore button state
        form.addEventListener('error', (e) => {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                restoreSubmitButton(submitButton);
            }
        });
        
        // Handle form submission failures (network errors, timeouts, etc.)
        form.addEventListener('submit', (e) => {
            // Add a global error handler for the form
            window.addEventListener('error', () => {
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    restoreSubmitButton(submitButton);
                }
            });
        }, { once: true });
    
        form.addEventListener("submit", (e) => {
            const submitButton = e.submitter;
            
            // Do not validate if it is the "Previous" button
            if (submitButton && submitButton.name === 'previous') {
                return;
            }
            
            let isValid = true;
            let firstInvalid = null;
    
            // Select only fields with "required"
            form.querySelectorAll("[required]").forEach(input => {
                const errorContainer = input.closest(".mb-4, .mb-3")?.querySelector(".custom-error");
                if (errorContainer) errorContainer.remove(); // remove old messages
        
                if (!input.value.trim()) {
                    isValid = false;
                    if (!firstInvalid) firstInvalid = input;
        
                    // Add custom error message
                    const errorMsg = document.createElement("div");
                    errorMsg.className = "custom-error text-danger small mt-2";
                    errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> This field is required`;
                    input.closest(".mb-4, .mb-3")?.appendChild(errorMsg);
                }
            });
        
            if (!isValid) {
                e.preventDefault();
                if (firstInvalid) firstInvalid.focus();
                return;
            }
            
            // Prevent multiple form submissions
            let originalText = '';
            if (submitButton && !submitButton.disabled) {
                submitButton.disabled = true;
                originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                // Store button state for potential restoration
                submitButton.dataset.originalText = originalText;
                submitButton.dataset.isProcessing = 'true';
                
                // Re-enable button after 5 seconds as fallback
                setTimeout(() => {
                    if (submitButton.disabled && submitButton.dataset.isProcessing === 'true') {
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalText;
                        submitButton.dataset.isProcessing = 'false';
                    }
                }, 5000);
            }
            
            // Page-specific validations
            if (window.currentPage === 'register') {
                if (window.currentStep === "4" && !validateUsername()) {
                    e.preventDefault();
                    // Re-enable button if validation fails
                    restoreSubmitButton(submitButton);
                    return;
                }
                
                if (window.currentStep === "5") {
                    const passwordValidation = validatePassword();
                    if (!passwordValidation.isValid) {
                        // Show password error message
                        showFieldError('id_password1', passwordValidation.message, 'error');
                        e.preventDefault();
                        // Re-enable button if validation fails
                        restoreSubmitButton(submitButton);
                        return;
                    }
                }
            }
            
            // Password reset confirm page validation
            if (window.currentPage === 'password_reset_confirm') {
                const passwordValidation = validatePassword();
                if (!passwordValidation.isValid) {
                    // Show password error message
                    showFieldError('id_password1', passwordValidation.message, 'error');
                    e.preventDefault();
                    // Re-enable button if validation fails
                    restoreSubmitButton(submitButton);
                    return;
                }
            }
        });
    }
}

// =============================================================================
// COUNTDOWN TIMER SYSTEM (UNIFIED)
// =============================================================================

// Function to clean browser history and prevent form resubmission
function cleanBrowserHistory() {
    // Replace current history entry to prevent back button issues
    if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', window.location.href);
    }
    
    // Clear any form data from browser cache
    if (window.performance && window.performance.navigation) {
        // This helps prevent form resubmission warnings
        if (window.performance.navigation.type === window.performance.navigation.TYPE_BACK_FORWARD) {
            window.location.reload();
        }
    }
}

// =============================================================================
// GENERIC ERROR MANAGEMENT SYSTEM (UNIFIED)
// =============================================================================

// Function to restore submit button to its original state
function restoreSubmitButton(submitButton) {
    if (submitButton && submitButton.disabled) {
        submitButton.disabled = false;
        submitButton.innerHTML = submitButton.dataset.originalText || 'Submit';
        submitButton.dataset.isProcessing = 'false';
    }
}

// Generic function to show error messages for any field type
function showFieldError(fieldId, message, errorType = 'error') {
    const field = document.getElementById(fieldId);
    if (field) {
        // Remove any existing error messages
        clearFieldErrors(fieldId);
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = `text-${errorType === 'error' ? 'danger' : 'warning'} small mt-2 field-error-message`;
        errorDiv.innerHTML = `<i class="fas fa-${errorType === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i> ${message}`;
        
        // Insert after the field container
        const fieldContainer = field.closest('.mb-4, .mb-3');
        if (fieldContainer) {
            fieldContainer.appendChild(errorDiv);
        }
    }
}

// Generic function to clear error messages for any field
function clearFieldErrors(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        const fieldContainer = field.closest('.mb-4, .mb-3');
        if (fieldContainer) {
            const existingErrors = fieldContainer.querySelectorAll('.field-error-message');
            existingErrors.forEach(error => error.remove());
        }
    }
}

// Generic function to clear all error messages
function clearAllFieldErrors() {
    const existingErrors = document.querySelectorAll('.field-error-message');
    existingErrors.forEach(error => error.remove());
}

// =============================================================================
// GENERIC PASSWORD TOGGLE FUNCTIONALITY (REUSABLE)
// =============================================================================

function initializePasswordToggles(containerSelector = 'body') {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    // Find all password toggle buttons in the container
    const toggleButtons = container.querySelectorAll('.password-toggle-icon');
    
    toggleButtons.forEach(toggleBtn => {
        const passwordField = toggleBtn.previousElementSibling;
        if (passwordField && passwordField.type === 'password') {
            toggleBtn.addEventListener('click', function() {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle icon
                this.classList.toggle('fa-eye');
                this.classList.toggle('fa-eye-slash');
            });
        }
    });
}

// =============================================================================
// GENERIC TIMER MANAGEMENT SYSTEM (UNIFIED)
// =============================================================================

function initializeCountdownTimer(config) {
    const { 
        canResend, 
        timeUntilResend, 
        timerContainerId, 
        buttonContainerId, 
        countdownId = 'countdown',
        delay = null 
    } = config;
    
    if (!canResend && timeUntilResend > 0) {
        const actualDelay = delay || timeUntilResend;
        startCountdown(actualDelay, timerContainerId, buttonContainerId, countdownId);
    }
}

function startCountdown(initialTime, timerContainerId, buttonContainerId, countdownId = 'countdown') {
    let timeLeft = initialTime;
    const countdown = document.getElementById(countdownId);
    const timerContainer = document.getElementById(timerContainerId);
    const buttonContainer = document.getElementById(buttonContainerId);
    
    if (!timerContainer || !buttonContainer) return;
    
    const timer = setInterval(() => {
        timeLeft--;
        if (countdown) {
            countdown.textContent = timeLeft;
        }
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            timerContainer.style.display = 'none';
            buttonContainer.style.display = 'block';
        }
    }, 1000);
}

function updateResendButtonState(config) {
    const { 
        buttonContainerId, 
        timerContainerId, 
        resendBtnId = 'resend-code-btn',
        delay = 120 
    } = config;
    
    const buttonContainer = document.getElementById(buttonContainerId);
    const timerContainer = document.getElementById(timerContainerId);
    const resendBtn = document.getElementById(resendBtnId);
    
    if (buttonContainer && timerContainer) {
        // Restore button to original state
        if (resendBtn) {
            resendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Resend code';
            resendBtn.disabled = false;
        }
        
        buttonContainer.style.display = 'none';
        timerContainer.style.display = 'block';
        
        // Start countdown with precise timing
        let timeLeft = delay;
        const countdown = document.getElementById('countdown');
        const startTime = Date.now();
        const endTime = startTime + (timeLeft * 1000);
        
        const timer = setInterval(() => {
            const now = Date.now();
            timeLeft = Math.max(0, Math.ceil((endTime - now) / 1000));
            
            if (countdown) {
                countdown.textContent = timeLeft;
            }
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                timerContainer.style.display = 'none';
                buttonContainer.style.display = 'block';
            }
        }, 100);
    }
}

// =============================================================================
// GENERIC FORM FIELD INITIALIZATION (UNIFIED)
// =============================================================================

function initializeFormFields(config) {
    const { 
        autoFocus = true, 
        passwordToggles = false, 
        containerSelector = 'body',
        excludeSteps = [] 
    } = config;
    
    // Auto-focus on first input (if enabled and not in excluded steps)
    if (autoFocus && !excludeSteps.includes(window.currentStep)) {
        const firstInput = document.querySelector('.form-control');
        if (firstInput) {
            firstInput.focus();
        }
    }
    
    // Initialize password toggles if requested
    if (passwordToggles) {
        initializePasswordToggles(containerSelector);
    }
}

// =============================================================================
// GENERIC RESEND CODE FUNCTIONALITY (UNIFIED)
// =============================================================================

function initializeResendCodeButton(config) {
    const { 
        resendBtnId = 'resend-code-btn',
        pageType, 
        step 
    } = config;
    
    const resendBtn = document.getElementById(resendBtnId);
    if (resendBtn) {
        resendBtn.addEventListener('click', () => handleResendCode(pageType, step));
    }
}

function handleResendCode(pageType, step) {
    if (pageType === 'login') {
        handleLoginResendCode();
    } else if (pageType === 'register') {
        handleRegisterResendCode();
    }
}

function handleLoginResendCode() {
    const form = document.getElementById('login-form');
    if (!form) return;

    const resendBtn = document.getElementById('resend-code-btn');
    if (!resendBtn) return;

    // Show loading state
    const originalText = resendBtn.innerHTML;
    resendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    resendBtn.disabled = true;

    const formData = new FormData();
    formData.append('step', 'email_2fa');
    formData.append('resend_code', '1');
    formData.append('csrfmiddlewaretoken', form.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
    .then(response => {
        if (response.ok) {
            // Redirect to refresh the page and show Django messages
            window.location.href = window.location.pathname + "?step=2";
        } else {
            // Restore button state on error
            resendBtn.innerHTML = originalText;
            resendBtn.disabled = false;
        }
    })
    .catch(() => {
        // Restore button state on error
        resendBtn.innerHTML = originalText;
        resendBtn.disabled = false;
    });
}

function handleRegisterResendCode() {
    const form = document.getElementById('registration-form');
    if (!form) return;

    const resendBtn = document.getElementById('resend-code-btn');
    if (!resendBtn) return;

    // Show loading state
    const originalText = resendBtn.innerHTML;
    resendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    resendBtn.disabled = true;

    const formData = new FormData();
    formData.append('step', '2');
    formData.append('resend_code', '1');
    formData.append('csrfmiddlewaretoken', form.querySelector('[name=csrfmiddlewaretoken]').value);

    fetch(window.resendCodeUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
    })
    .then(response => {
        if (response.ok) {
            // Redirect to refresh the page and show Django messages
            window.location.href = window.location.pathname + "?step=2";
        } else {
            // Restore button state on error
            resendBtn.innerHTML = originalText;
            resendBtn.disabled = false;
        }
    })
    .catch(() => {
        // Restore button state on error
        resendBtn.innerHTML = originalText;
        resendBtn.disabled = false;
    });
}

// =============================================================================
// VERIFICATION CODE INPUT (UNIFIED)
// =============================================================================

function initializeVerificationCodeInput() {
    const codeInput = document.querySelector('#id_twofa_code, #id_verification_code');
    if (codeInput) {
        codeInput.focus();
        
        codeInput.addEventListener('input', function() {
            // Allow only numbers
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Auto-submit if 6 numbers are entered (for register page)
            if (window.currentPage === 'register' && this.value.length === 6) {
                setTimeout(() => {
                    document.getElementById('registration-form').submit();
                }, 500);
            }
        });
    }
}

// =============================================================================
// 2FA METHOD SELECTION (LOGIN ONLY)
// =============================================================================

function initialize2FAMethodSelection() {
    document.querySelectorAll('.method-card').forEach(card => {
        card.addEventListener('click', function() {
            // Remove selected class from all cards
            document.querySelectorAll('.method-card').forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            
            // Check the corresponding radio button
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });

    // Auto-select if a method is already checked
    document.querySelectorAll('input[name="twofa_method"]:checked').forEach(radio => {
        radio.closest('.method-card').classList.add('selected');
    });
}

// =============================================================================
// USERNAME VERIFICATION (REGISTER ONLY)
// =============================================================================

function initializeUsernameVerification() {
    const usernameInput = document.getElementById('id_username');
    const feedback = document.getElementById('username-feedback');
    
    if (usernameInput && feedback) {
        usernameInput.addEventListener('input', function() {
            clearTimeout(usernameTimeout);
            const username = this.value.trim();
            
            // Hide Django form errors when user starts typing
            hideUsernameErrors();
            
            if (username.length === 0) {
                feedback.innerHTML = '';
                return;
            }
            
            // Enhanced validation using the same rules as the backend
            const validationResult = validateUsernameFormat(username);
            if (!validationResult.isValid) {
                feedback.innerHTML = `<span class="username-taken"><i class="fas fa-times-circle"></i> ${validationResult.message}</span>`;
                return;
            }
            
            feedback.innerHTML = '<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Verification...</span>';
            
            usernameTimeout = setTimeout(() => {
                checkUsernameAvailability(username, feedback);
            }, 500);
        });
    }
}

function validateUsernameFormat(username) {
    // Length validation
    if (username.length < 3) {
        return { isValid: false, message: 'Username must be at least 3 characters long' };
    }
    
    if (username.length > 30) {
        return { isValid: false, message: 'Username cannot exceed 30 characters' };
    }
    
    // Character validation
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        return { isValid: false, message: 'Username can only contain letters, numbers, and underscores' };
    }
    
    // Start validation
    if (/^[0-9_]/.test(username)) {
        return { isValid: false, message: 'Username cannot start with numbers or underscores' };
    }
    
    // End validation
    if (username.endsWith('_')) {
        return { isValid: false, message: 'Username cannot end with an underscore' };
    }
    
    // Consecutive underscores validation
    if (username.includes('__')) {
        return { isValid: false, message: 'Username cannot contain consecutive underscores' };
    }
    
    return { isValid: true, message: '' };
}

function checkUsernameAvailability(username, feedback) {
    fetch(window.usernameCheckUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: 'username=' + encodeURIComponent(username)
    })
    .then(response => response.json())
    .then(data => {
        if (data.available) {
            feedback.innerHTML = '<span class="username-available"><i class="fas fa-check-circle"></i> ' + data.message + '</span>';
        } else {
            feedback.innerHTML = '<span class="username-taken"><i class="fas fa-times-circle"></i> ' + data.message + '</span>';
        }
    })
    .catch(() => {
        feedback.innerHTML = '<span class="text-warning"><i class="fas fa-exclamation-triangle"></i> Verification error</span>';
    });
}

function validateUsername() {
    const username = document.getElementById('id_username').value.trim();
    const validationResult = validateUsernameFormat(username);
    
    if (!validationResult.isValid) {
        alert(validationResult.message);
        return false;
    }
    
    return true;
}

// Function to hide Django username errors
function hideUsernameErrors() {
    const usernameInput = document.getElementById('id_username');
    if (usernameInput) {
        // Find and hide Django form errors
        const errorContainer = usernameInput.closest('.mb-4').querySelector('.text-danger');
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
    }
}

// =============================================================================
// PASSWORD VALIDATION (REGISTER ONLY)
// =============================================================================

function initializePasswordValidation() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const strengthDiv = document.getElementById('password-strength');
    const matchDiv = document.getElementById('password-match');
    
    if (password1 && password2 && strengthDiv && matchDiv) {
        password1.addEventListener('input', function() {
            // Clear any existing password error messages when user starts typing
            clearFieldErrors('id_password1');
            
            const result = checkPasswordStrength(this.value);
            
            if (this.value.length > 0) {
                const requirementsHtml = `
                    <div class="progress mt-2" style="height: 6px;">
                        <div class="progress-bar bg-${result.color}" style="width: ${(result.strength/5)*100}%"></div>
                    </div>
                    <small class="text-${result.color} fw-bold">${result.label}</small>
                `;
                
                strengthDiv.innerHTML = requirementsHtml;
            } else {
                strengthDiv.innerHTML = '';
            }
            
            // Check for matching if the confirmation field is not empty
            if (password2.value) {
                checkPasswordMatch();
            }
        });
        
        password2.addEventListener('input', function() {
            // Clear any existing password error messages when user starts typing
            clearFieldErrors('id_password2');
            checkPasswordMatch();
        });
    }
}

function checkPasswordStrength(password) {
    let strength = 0;
    let requirements = {
        length: password.length >= 12,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        digits: /\d/.test(password),
        symbols: /[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]/.test(password)
    };
    
    // Calculate strength based on requirements met
    Object.values(requirements).forEach(met => {
        if (met) strength++;
    });
    
    const colors = ['danger', 'danger', 'warning', 'info', 'success'];
    const labels = ['Very weak', 'Weak', 'Medium', 'Good', 'Strong'];
    
    return {
        strength: strength,
        color: colors[Math.min(strength, 4)],
        label: labels[Math.min(strength, 4)],
        requirements: requirements
    };
}

function checkPasswordMatch() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const matchDiv = document.getElementById('password-match');
    
    if (password1 && password2 && matchDiv) {
        if (password2.value.length > 0) {
            if (password1.value === password2.value) {
                matchDiv.innerHTML = '<small class="text-success"><i class="fas fa-check"></i> Passwords match</small>';
            } else {
                matchDiv.innerHTML = '<small class="text-danger"><i class="fas fa-times"></i> Passwords do not match</small>';
            }
        } else {
            matchDiv.innerHTML = '';
        }
    }
}

function validatePassword() {
    const pwd1 = document.getElementById('id_password1').value;
    const pwd2 = document.getElementById('id_password2').value;
    
    // Check minimum length
    if (pwd1.length < 12) {
        return { isValid: false, message: 'Password must contain at least 12 characters.' };
    }
    
    // Check requirements using our strength checker
    const strength = checkPasswordStrength(pwd1);
    const missingRequirements = [];
    
    if (!strength.requirements.lowercase) missingRequirements.push('lowercase letter');
    if (!strength.requirements.uppercase) missingRequirements.push('uppercase letter');
    if (!strength.requirements.digits) missingRequirements.push('digit');
    if (!strength.requirements.symbols) missingRequirements.push('special character');
    
    if (missingRequirements.length > 0) {
        return { isValid: false, message: `Password must contain at least one: ${missingRequirements.join(', ')}.` };
    }
    
    // Check if passwords match
    if (pwd1 !== pwd2) {
        return { isValid: false, message: 'The passwords do not match.' };
    }
    
    return { isValid: true, message: '' };
}

// =============================================================================
// MAIN INITIALIZATION (UNIFIED)
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation for all pages
    initializeFormValidation();
    
    // Initialize page-specific functionality using configuration
    initializePageFunctionality();
    
    // Clean browser history to prevent form resubmission warnings
    cleanBrowserHistory();
});

function initializePageFunctionality() {
    const pageConfig = PAGE_CONFIGS[window.currentPage];
    if (!pageConfig) return;
    
    const stepConfig = pageConfig[window.currentStep];
    if (!stepConfig) return;
    
    // Initialize countdown timer if configured
    if (stepConfig.countdownTimer) {
        const config = stepConfig.countdownTimer;
        const canResend = window[config.canResend];
        const timeUntilResend = window[config.timeUntilResend];
        const delay = config.delay ? window[config.delay] : null;
        
        initializeCountdownTimer({
            canResend,
            timeUntilResend,
            timerContainerId: config.timerContainerId,
            buttonContainerId: config.buttonContainerId,
            delay
        });
    }
    
    // Initialize resend code button if configured
    if (stepConfig.resendCode) {
        initializeResendCodeButton(stepConfig.resendCode);
    }
    
    // Initialize verification code input if configured
    if (stepConfig.verificationCode) {
        initializeVerificationCodeInput();
    }
    
    // Initialize 2FA method selection if configured
    if (stepConfig.twofaMethods) {
        initialize2FAMethodSelection();
    }
    
    // Initialize username verification if configured
    if (stepConfig.usernameVerification) {
        initializeUsernameVerification();
    }
    
    // Initialize password validation if configured
    if (stepConfig.passwordValidation) {
        initializePasswordValidation();
    }
    
    // Initialize form fields (auto-focus, password toggles, etc.)
    if (stepConfig.formFields) {
        initializeFormFields(stepConfig.formFields);
    }
}
