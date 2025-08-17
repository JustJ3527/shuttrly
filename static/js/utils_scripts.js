document.addEventListener("DOMContentLoaded", () => {
    // Format datetime elements
    document.querySelectorAll('.user-datetime').forEach(el => {
      const datetimeStr = el.dataset.datetime;
      if (datetimeStr) {
        const date = new Date(datetimeStr);
        const options = { dateStyle: 'short', timeStyle: 'short' };
        el.textContent = new Intl.DateTimeFormat(navigator.language, options).format(date);
      }
    });

    // Function to remove only old/legacy Django messages (not the new system)
    function removeOldMessages() {
        // Only remove old message formats, not the new django-messages container
        const oldMessageSelectors = [
            '.messages:not(#django-messages)',
            '.alert:not(.messages-container .alert)',
            '.message',
            '.notification'
        ];
        
        oldMessageSelectors.forEach(selector => {
            const messages = document.querySelectorAll(selector);
            messages.forEach(message => {
                if (message && message.parentNode && !message.closest('#django-messages')) {
                    message.remove();
                }
            });
        });
    }

    // Remove only old messages on page load
    removeOldMessages();

    // Remove old messages when navigating with browser back/forward buttons
    window.addEventListener('popstate', removeOldMessages);

    // Remove old messages when using browser navigation
    window.addEventListener('beforeunload', removeOldMessages);

    // Remove old messages when the page becomes visible again (e.g., from another tab)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            removeOldMessages();
        }
    });

    // Intercept navigation events for single-page applications or AJAX requests
    let currentUrl = window.location.href;
    
    // Check for URL changes periodically
    setInterval(() => {
        if (currentUrl !== window.location.href) {
            currentUrl = window.location.href;
            removeOldMessages();
        }
    }, 100);

    // Override pushState and replaceState to catch programmatic navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
        originalPushState.apply(this, args);
        setTimeout(removeOldMessages, 50);
    };

    history.replaceState = function(...args) {
        originalReplaceState.apply(this, args);
        setTimeout(removeOldMessages, 50);
    };

    // =============================================================================
    // 2FA MANAGEMENT SYSTEM
    // =============================================================================

    // Initialize 2FA functionality if on personal settings page
    if (document.querySelector('.twofa-method-section')) {
        initialize2FASystem();
    }

    // Initialize password toggles for personal settings
    initializePasswordToggles('.settings-container');

    // Initialize form validation for personal settings
    initializePersonalSettingsValidation();
});

// =============================================================================
// 2FA MANAGEMENT FUNCTIONS
// =============================================================================

// Make functions globally accessible for HTML onclick attributes
window.showEnableEmail2FA = function() {
    document.getElementById('enable-email-2fa-form').style.display = 'block';
    document.getElementById('enable-email-2fa-button').style.display = 'none';
    
    // Add form validation on submit
    const form = document.getElementById('enable-email-2fa-form').querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validate2FAForm('enable-email-2fa-form')) {
                e.preventDefault();
                return false;
            }
        });
    }
};

window.showDisableEmail2FA = function() {
    document.getElementById('disable-email-2fa-form').style.display = 'block';
    document.getElementById('disable-email-2fa-button').style.display = 'none';
    
    // Add form validation on submit
    const form = document.getElementById('disable-email-2fa-form').querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validate2FAForm('disable-email-2fa-form')) {
                e.preventDefault();
                return false;
            }
        });
    }
};

window.hideEnableEmail2FA = function() {
    document.getElementById('enable-email-2fa-form').style.display = 'none';
    document.getElementById('enable-email-2fa-button').style.display = 'block';
    // Clear any validation errors
    clearAllFieldErrors();
};

window.hideDisableEmail2FA = function() {
    document.getElementById('disable-email-2fa-form').style.display = 'none';
    document.getElementById('disable-email-2fa-button').style.display = 'block';
    // Clear any validation errors
    clearAllFieldErrors();
};

window.cancelEmail2FASetup = function() {
    if (confirm('Are you sure you want to cancel Email 2FA setup? This will clear any pending verification.')) {
        // Submit cancel action
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
            <input type="hidden" name="action" value="cancel">
        `;
        document.body.appendChild(form);
        form.submit();
    }
};

// TOTP 2FA Functions
window.showEnableTOTP2FA = function() {
    document.getElementById('enable-totp-2fa-form').style.display = 'block';
    document.getElementById('enable-totp-2fa-button').style.display = 'none';
    
    // Add form validation on submit
    const form = document.getElementById('enable-totp-2fa-form').querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validate2FAForm('enable-totp-2fa-form')) {
                e.preventDefault();
                return false;
            }
        });
    }
};

window.showDisableTOTP2FA = function() {
    document.getElementById('disable-totp-2fa-form').style.display = 'block';
    document.getElementById('disable-totp-2fa-button').style.display = 'none';
    
    // Add form validation on submit
    const form = document.getElementById('disable-totp-2fa-form').querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validate2FAForm('disable-totp-2fa-form')) {
                e.preventDefault();
                return false;
            }
        });
    }
};

window.hideEnableTOTP2FA = function() {
    document.getElementById('enable-totp-2fa-form').style.display = 'none';
    document.getElementById('enable-totp-2fa-button').style.display = 'block';
    // Clear any validation errors
    clearAllFieldErrors();
};

window.hideDisableTOTP2FA = function() {
    document.getElementById('disable-totp-2fa-form').style.display = 'none';
    document.getElementById('disable-totp-2fa-button').style.display = 'block';
    // Clear any validation errors
    clearAllFieldErrors();
};

window.cancelTOTP2FASetup = function() {
    if (confirm('Are you sure you want to cancel Authenticator App 2FA setup? This will clear any pending verification.')) {
        // Submit cancel action
        const form = document.createElement('form');
        form.method = 'POST';
        form.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
            <input type="hidden" name="action" value="cancel">
        `;
        document.body.appendChild(form);
        form.submit();
    }
};

// =============================================================================
// TRUSTED DEVICES MANAGEMENT
// =============================================================================

window.toggleDeviceDetails = function(header) {
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
};

// =============================================================================
// TOTP URI COPY FUNCTIONALITY
// =============================================================================

function initializeTOTPCopy() {
    const copyBtn = document.getElementById('copyTotpUriBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const input = document.getElementById('totpUriInput');
            input.select();
            input.setSelectionRange(0, 99999); // For mobile devices
            
            navigator.clipboard.writeText(input.value).then(() => {
                const msg = document.getElementById('copyMessage');
                msg.classList.add('show');
                setTimeout(() => { 
                    msg.classList.remove('show'); 
                }, 2000);
            }).catch(err => {
                showFieldError('totpUriInput', 'Error copying setup key: ' + err, 'error');
            });
        });
    }
}

// =============================================================================
// VERIFICATION CODE INPUTS
// =============================================================================

function initializeVerificationCodeInputs() {
    document.querySelectorAll('.verification-code-input').forEach(input => {
        input.addEventListener('input', function() {
            // Only allow numbers
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Auto-submit when 6 digits are entered
            if (this.value.length === 6) {
                this.closest('form').submit();
            }
        });
    });
}

// =============================================================================
// 2FA COUNTDOWN TIMERS
// =============================================================================

function initialize2FACountdownTimers() {
    const countdownInfo = document.querySelector('.countdown-info');
    if (countdownInfo && countdownInfo.querySelector('#timer')) {
        const timerElement = document.getElementById('timer');
        const timeUntilResend = parseInt(timerElement.textContent);
        
        if (timeUntilResend > 0) {
            start2FACountdown(timeUntilResend, timerElement, countdownInfo);
        }
    }
}

function start2FACountdown(initialTime, timerElement, countdownElement) {
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
    setInterval(updateTimer, 1000);
}

// =============================================================================
// 2FA ANIMATIONS
// =============================================================================

function initialize2FAAnimations() {
    // Add fade-in animation to 2FA sections
    document.querySelectorAll('.twofa-method-section').forEach((section, index) => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            section.style.transition = 'all 0.5s ease';
            section.style.opacity = '1';
            section.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// =============================================================================
// PASSWORD TOGGLE FUNCTIONALITY
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
// FORM VALIDATION AND ERROR HANDLING
// =============================================================================

function initializePersonalSettingsValidation() {
    const form = document.getElementById('personal-settings-form');
    if (!form) return;

    // Form submission with email verification if needed
    form.addEventListener('submit', function(e) {
        const newEmail = document.getElementById('id_email').value;
        const currentEmail = window.currentEmail;
        
        if (newEmail.toLowerCase() !== currentEmail.toLowerCase()) {
            e.preventDefault();
            showEmailVerificationModal(newEmail);
        }
    });

    // Email verification
    const verifyEmailBtn = document.getElementById('verifyEmailBtn');
    if (verifyEmailBtn) {
        verifyEmailBtn.addEventListener('click', function() {
            const code = document.getElementById('verificationCode').value;
            
            if (!code || code.length !== 6) {
                showFieldError('verificationCode', 'Please enter a valid 6-digit code', 'error');
                return;
            }
            
            // Here you would typically send the verification code to your backend
            // For now, we'll simulate success and submit the form
            document.getElementById('emailVerificationModal').querySelector('.btn-close').click();
            document.getElementById('personal-settings-form').submit();
        });
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
        const fieldContainer = field.closest('.mb-4, .mb-3, .form-group');
        if (fieldContainer) {
            fieldContainer.appendChild(errorDiv);
        }
    }
}

// Generic function to clear error messages for any field
function clearFieldErrors(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        const fieldContainer = field.closest('.mb-4, .mb-3, .form-group');
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
// EMAIL VERIFICATION MODAL
// =============================================================================

function showEmailVerificationModal(newEmail) {
    const modal = document.getElementById('emailVerificationModal');
    if (modal) {
        document.getElementById('newEmailDisplay').textContent = newEmail;
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
}

// =============================================================================
// 2FA FORM VALIDATION AND ERROR HANDLING
// =============================================================================

function initialize2FAFormValidation() {
    // Add validation for all 2FA password inputs
    document.querySelectorAll('.inline-2fa-form input[type="password"]').forEach(input => {
        input.addEventListener('blur', function() {
            validate2FAPassword(this);
        });
        
        input.addEventListener('input', function() {
            clearFieldErrors(this.id);
            this.classList.remove('is-invalid', 'is-valid');
        });
    });

    // Add validation for TOTP code inputs
    document.querySelectorAll('.inline-2fa-form input[name*="totp_code"], .inline-2fa-form input[name*="disable_totp_code"]').forEach(input => {
        input.addEventListener('blur', function() {
            validateTOTPCode(this);
        });
        
        input.addEventListener('input', function() {
            clearFieldErrors(this.id);
            this.classList.remove('is-invalid', 'is-valid');
            // Only allow numbers
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    });
}

function validate2FAPassword(input) {
    const password = input.value.trim();
    
    if (!password) {
        showFieldError(input.id, 'Password is required', 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    if (password.length < 8) {
        showFieldError(input.id, 'Password must be at least 8 characters long', 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    input.classList.add('is-valid');
    return true;
}

function validateTOTPCode(input) {
    const code = input.value.trim();
    
    if (!code) {
        showFieldError(input.id, 'Verification code is required', 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
        showFieldError(input.id, 'Please enter a valid 6-digit code', 'error');
        input.classList.add('is-invalid');
        return false;
    }
    
    input.classList.add('is-valid');
    return true;
}

function validate2FAForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    
    // Validate password fields
    const passwordInputs = form.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (!validate2FAPassword(input)) {
            isValid = false;
        }
    });
    
    // Validate TOTP code fields if present
    const totpInputs = form.querySelectorAll('input[name*="totp_code"]');
    totpInputs.forEach(input => {
        if (!validateTOTPCode(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Enhanced showFieldError function for 2FA forms
function showFieldError(fieldId, message, errorType = 'error') {
    const field = document.getElementById(fieldId);
    if (field) {
        // Remove any existing error messages
        clearFieldErrors(fieldId);
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = `field-error-message ${errorType === 'error' ? 'text-danger' : 'text-warning'}`;
        errorDiv.innerHTML = `<i class="fas fa-${errorType === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i> ${message}`;
        
        // Find the error container
        let errorContainer = field.closest('.form-group')?.querySelector('.error-message-container');
        
        // If no error container found, look for other common containers
        if (!errorContainer) {
            errorContainer = field.closest('.mb-4, .mb-3, .form-group');
        }
        
        if (errorContainer) {
            errorContainer.appendChild(errorDiv);
        }
    }
}