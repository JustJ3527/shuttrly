// auth.js - Unified JavaScript functionality for authentication pages (login & register)
// Handles form validation, 2FA, countdown timers, and user interactions

// =============================================================================
// GLOBAL VARIABLES AND UTILITIES
// =============================================================================

let usernameTimeout;
let timeLeft;

// Utility function to show messages (success/error)
function showMessage(message, type = 'success') {
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type} alert-dismissible fade show`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
    messageElement.innerHTML = `
        <i class="fas ${icon}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    insertMessage(messageElement);
}

function showSuccessMessage(message) {
    showMessage(message, 'success');
}

function showErrorMessage(message) {
    showMessage(message, 'danger');
}

// Utility function to insert messages
function insertMessage(messageElement) {
    const form = document.getElementById('login-form') || document.getElementById('registration-form');
    if (!form) return;
    
    const formContainer = form.closest('.step-content');
    if (formContainer) {
        const existingMessages = formContainer.querySelector('.alert');
        if (existingMessages) {
            existingMessages.remove();
        }
        formContainer.insertBefore(messageElement, formContainer.firstChild);
    }
}

// =============================================================================
// FORM VALIDATION SYSTEM (UNIFIED)
// =============================================================================

function initializeFormValidation() {
    const form = document.getElementById("login-form") || document.getElementById("registration-form");
    
    if (form) {
        // Disable native validation to take control
        form.setAttribute("novalidate", true);
    
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
            
            // Page-specific validations
            if (window.currentPage === 'register') {
                if (window.currentStep === "4" && !validateUsername()) {
                    e.preventDefault();
                    return;
                }
                
                if (window.currentStep === "5" && !validatePassword()) {
                    e.preventDefault();
                    return;
                }
            }
        });
    }
}

// =============================================================================
// COUNTDOWN TIMER SYSTEM (UNIFIED)
// =============================================================================

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
            startCountdown(window.timeUntilResend, 'resend-timer-container', 'resend-button-container');
        }
    }
}

function startCountdown(initialTime, timerContainerId, buttonContainerId) {
    timeLeft = initialTime;
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
    if (buttonContainer && timerContainer) {
        buttonContainer.style.display = 'none';
        timerContainer.style.display = 'block';
        
        // Start countdown - Use persistent timing
        const delay = window.emailCodeResendDelay || 20;
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
// RESEND CODE FUNCTIONALITY (UNIFIED)
// =============================================================================

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
            showSuccessMessage('A new verification code has been sent to your email address.');
            updateResendButtonState();
        } else {
            showErrorMessage('Error sending verification code. Please try again.');
        }
    })
    .catch(() => {
        showErrorMessage('Error requesting new code. Please try again.');
    });
}

function handleRegisterResendCode() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = window.resendCodeUrl;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    
    form.appendChild(csrfInput);
    document.body.appendChild(form);
    form.submit();
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
            
            if (username.length === 0) {
                feedback.innerHTML = '';
                return;
            }
            
            if (username.length < 3) {
                feedback.innerHTML = '<span class="username-taken"><i class="fas fa-times-circle"></i> Username must be at least 3 characters long </span>';
                return;
            }
            
            // Check allowed characters
            if (!/^[a-zA-Z0-9_]+$/.test(username)) {
                feedback.innerHTML = '<span class="username-taken"><i class="fas fa-times-circle"></i> Only letters, numbers and _ are allowed</span>';
                return;
            }
            
            feedback.innerHTML = '<span class="text-muted"><i class="fas fa-spinner fa-spin"></i> Verification...</span>';
            
            usernameTimeout = setTimeout(() => {
                checkUsernameAvailability(username, feedback);
            }, 500);
        });
    }
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
    if (username.length < 3) {
        alert('Username must contain at least 3 characters.');
        return false;
    }
    return true;
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
            const result = checkPasswordStrength(this.value);
            
            if (this.value.length > 0) {
                strengthDiv.innerHTML = `
                    <div class="progress mt-2" style="height: 6px;">
                        <div class="progress-bar bg-${result.color}" style="width: ${(result.strength/5)*100}%"></div>
                    </div>
                    <small class="text-${result.color} fw-bold">${result.label}</small>
                `;
            } else {
                strengthDiv.innerHTML = '';
            }
            
            // Check for matching if the confirmation field is not empty
            if (password2.value) {
                checkPasswordMatch();
            }
        });
        
        password2.addEventListener('input', checkPasswordMatch);
    }
}

function checkPasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    const colors = ['danger', 'danger', 'warning', 'info', 'success', 'success'];
    const labels = ['Very weak', 'Weak', 'Medium', 'Good', 'Strong', 'Very strong'];
    
    return {
        strength: strength,
        color: colors[strength],
        label: labels[strength]
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
    
    if (pwd1.length < 8) {
        alert('Password must contain at least 8 characters.');
        return false;
    }
    
    if (pwd1 !== pwd2) {
        alert('The passwords do not match.');
        return false;
    }
    
    return true;
}

// =============================================================================
// AUTO-FOCUS FUNCTIONALITY (UNIFIED)
// =============================================================================

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
// MAIN INITIALIZATION (UNIFIED)
// =============================================================================

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
        initializeVerificationCodeInput();
    }
    
    if (window.currentStep === "4") {
        initializeUsernameVerification();
    }
    
    if (window.currentStep === "5") {
        initializePasswordValidation();
    }
}
