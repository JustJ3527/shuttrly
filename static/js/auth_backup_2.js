// auth.js - Unified JavaScript functionality for authentication pages (login & register)
// Handles form validation, 2FA, countdown timers, and user interactions

// =============================================================================

    }
}
// GLOBAL VARIABLES AND UTILITIES
// =============================================================================

    }
}

let usernameTimeout;
let timeLeft;

// Messages are now handled by Django's message system via {% display_messages_with_auto_clear %}
// This ensures consistency across the application

// =============================================================================

    }
}
// FORM VALIDATION SYSTEM (UNIFIED)
// =============================================================================

    }
}

function initializeFormValidation() {
    const mainForm = document.getElementById("login-form") || document.getElementById("registration-form");
    
    if (mainForm) {
        // Disable native validation to take control
        mainForm.setAttribute("novalidate", true);
    
        mainForm.addEventListener("submit", (e) => {
            const submitButton = e.submitter;
            
            // Do not validate if it is the "Previous" button
            if (submitButton && submitButton.name === 'previous') {
                return;
            }
            
            let isValid = true;
            let firstInvalid = null;
    
            // Select only fields with "required"
            mainForm.querySelectorAll("[required]").forEach(input => {
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
            
            // Page-specific validations
            if (window.currentPage === 'register') {
                if (window.currentStep === "4" && !validateUsername()) {
                    e.preventDefault();
                    return;
                }
                
                if (window.currentStep === "5") {
                    const passwordValidation = validatePassword();
                    if (!passwordValidation.isValid) {
                        // Show password error message
                        showPasswordError(passwordValidation.message);
                        e.preventDefault();
                        return;
                    }
                }
            }
        });
    }
    
    });
}

// =============================================================================

    }
}
// COUNTDOWN TIMER SYSTEM (UNIFIED)
// =============================================================================

    }
}

function initializeCountdownTimer() {
    // For login page
    if (window.currentPage === 'login' && window.currentStep === 'email_2fa') {
        if (!window.canResendInitial && window.timeUntilResend > 0) {
            startCountdown(window.timeUntilResend, 'resend-timer-container', 'resend-button-container');
        }
    }
    
    // For register page
    if (window.currentPage === 'register' && window.currentStep === "2") {
        if (!window.canResend && window.timeUntilResend > 0) {
            // Use the delay from Django template if available, otherwise use the session time
            const delay = window.emailCodeResendDelay || window.timeUntilResend;
            startCountdown(delay, 'resend-timer-container', 'resend-button-container');
        }
    }
}

function startCountdown(initialTime, timerContainerId, buttonContainerId) {
    // Use the delay from Django template if available, otherwise use the initial time
    timeLeft = window.emailCodeResendDelay || initialTime;
    const countdown = document.getElementById('countdown');
    const timerContainer = document.getElementById(timerContainerId);
    const buttonContainer = document.getElementById(buttonContainerId);
    
    const timer = setInterval(() => {
        timeLeft--;
        if (countdown) {
            countdown.textContent = timeLeft;
        }
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            if (timerContainer) timerContainer.style.display = 'none';
            if (buttonContainer) buttonContainer.style.display = 'block';
        }
    }, 1000);
}

function updateResendButtonState() {
    const buttonContainer = document.getElementById('resend-button-container');
    const timerContainer = document.getElementById('resend-timer-container');
    const resendBtn = document.getElementById('resend-code-btn');
    
    if (buttonContainer && timerContainer) {
        // Restore button to original state
        if (resendBtn) {
            resendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Resend code';
            resendBtn.disabled = false;
        }
        
        buttonContainer.style.display = 'none';
        timerContainer.style.display = 'block';
        
        // Start countdown - Use the delay from Django template
        const delay = window.emailCodeResendDelay || 120; // Default to 2 minutes if not set
        let timeLeft = delay;
        const countdown = document.getElementById('countdown');
        
        // Use more precise timing for resend countdown
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
        }, 100); // Update more frequently for smoother countdown
    }
}

// =============================================================================

    }
}
// RESEND CODE FUNCTIONALITY (UNIFIED)
// =============================================================================

    }
}

function initializeResendCodeButton() {
    const resendBtn = document.getElementById('resend-code-btn');
    if (resendBtn) {
        resendBtn.addEventListener('click', handleResendCode);
    }
}

function handleResendCode() {
    if (window.currentPage === 'login') {
        handleLoginResendCode();
    } else if (window.currentPage === 'register') {
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

    }
}
// VERIFICATION CODE INPUT (UNIFIED)
// =============================================================================

    }
}

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

    }
}
// 2FA METHOD SELECTION (LOGIN ONLY)
// =============================================================================

    }
}

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

    }
}
// USERNAME VERIFICATION (REGISTER ONLY)
// =============================================================================

    }
}

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

// Function to show password error messages
function showPasswordError(message) {
    const password1 = document.getElementById('id_password1');
    if (password1) {
        // Remove any existing error messages
        clearPasswordErrors();
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-danger small mt-2 password-error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        
        // Insert after the password field
        const passwordContainer = password1.closest('.mb-3');
        if (passwordContainer) {
            passwordContainer.appendChild(errorDiv);
        }
    }
}

// Function to clear password error messages
function clearPasswordErrors() {
    const existingErrors = document.querySelectorAll('.password-error-message');
    existingErrors.forEach(error => error.remove());
}

// =============================================================================

    }
}
// PASSWORD VALIDATION (REGISTER ONLY)
// =============================================================================

    }
}

function initializePasswordValidation() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const strengthDiv = document.getElementById('password-strength');
    const matchDiv = document.getElementById('password-match');
    
    if (password1 && password2 && strengthDiv && matchDiv) {
        password1.addEventListener('input', function() {
            // Clear any existing password error messages when user starts typing
            clearPasswordErrors();
            
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
            clearPasswordErrors();
            checkPasswordMatch();
        });
    }
}

function checkPasswordStrength(password) {

// Function to get simple password display
function getSimplePasswordDisplay(result) {
    if (result.strength === 5) {
        return `<small class="text-success fw-bold"><i class="fas fa-check-circle"></i> Strong password</small>`;
    } else if (result.strength >= 3) {
        return `<small class="text-${result.color}"><i class="fas fa-info-circle"></i> ${result.label}</small>`;
    } else {
        return `<small class="text-${result.color}"><i class="fas fa-exclamation-triangle"></i> ${result.label}</small>`;
    }
}
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

    }
}
// PASSWORD VISIBILITY TOGGLE FUNCTIONALITY
// =============================================================================

    }
}

function initializePasswordVisibilityToggles() {
    // Toggle for registration password fields
    const togglePassword1 = document.getElementById('toggle-password1');
    const togglePassword2 = document.getElementById('toggle-password2');
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    
    // Toggle for login password field
    const togglePassword = document.getElementById('toggle-password');
    const password = document.getElementById('id_password');
    
    // Registration password 1 toggle
    if (togglePassword1 && password1) {
        togglePassword1.addEventListener('click', function() {
            togglePasswordVisibility(password1, togglePassword1);
        });
    }
    
    // Registration password 2 toggle
    if (togglePassword2 && password2) {
        togglePassword2.addEventListener('click', function() {
            togglePasswordVisibility(password2, togglePassword2);
        });
    }
    
    // Login password toggle
    if (togglePassword && password) {
        togglePassword.addEventListener('click', function() {
            togglePasswordVisibility(password, togglePassword);
        });
    }
}

function togglePasswordVisibility(passwordInput, toggleIcon) {
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
    
    // Update icon and tooltip
    if (type === 'text') {
        toggleIcon.className = 'fas fa-eye-slash password-toggle-icon';
        toggleIcon.title = 'Hide password';
    } else {
        toggleIcon.className = 'fas fa-eye password-toggle-icon';
        toggleIcon.title = 'Show password';
    }
}

// =============================================================================

    }
}
// AUTO-FOCUS FUNCTIONALITY (UNIFIED)
// =============================================================================

    }
}

function initializeAutoFocus() {
    const firstInput = document.querySelector('.form-control');
    if (firstInput) {
        // No auto-focus for verification code steps
        const noFocusSteps = ['email_2fa', 'totp_2fa', '2'];
        if (!noFocusSteps.includes(window.currentStep)) {
            firstInput.focus();
        }
    }
}



// =============================================================================

    }
}
// MAIN INITIALIZATION (UNIFIED)
// =============================================================================

    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation for all pages
    initializeFormValidation();
    
    // Initialize page-specific functionality
    if (window.currentPage === 'login') {
        initializeLoginFunctionality();
    } else if (window.currentPage === 'register') {
        initializeRegisterFunctionality();
    }
    
    // Initialize common functionality
    initializePasswordVisibilityToggles();
    initializeAutoFocus();
});

function initializeLoginFunctionality() {
    if (window.currentStep === 'email_2fa') {
        initializeCountdownTimer();
        initializeResendCodeButton();
        initializeVerificationCodeInput();
    }
    
    if (window.currentStep === 'choose_2fa') {
        initialize2FAMethodSelection();
    }
    
    if (window.currentStep === 'totp_2fa') {
        initializeVerificationCodeInput();
    }
}

function initializeRegisterFunctionality() {
    if (window.currentStep === "2") {
        initializeCountdownTimer();
        initializeResendCodeButton();
        initializeVerificationCodeInput();
    }
    
    if (window.currentStep === "4") {
        initializeUsernameVerification();
    }
    
    if (window.currentStep === "5") {
        initializePasswordValidation();
    }
}
