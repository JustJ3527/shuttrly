/**
 * Countdown Timer System
 * Handles all countdown timers, resend delays, and time-based functionality
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

// =============================================================================
// COUNTDOWN CONFIGURATION
// =============================================================================

const COUNTDOWN_CONFIG = {
    // Default settings
    default: {
        updateInterval: 1000, // milliseconds
        animationDuration: 300,
        showResendDelay: 1000
    },
    
    // Email verification settings
    email: {
        resendDelay: 60, // seconds
        warningThreshold: 10, // seconds before showing warning
        autoResend: false
    },
    
    // TOTP settings
    totp: {
        resendDelay: 30, // seconds
        warningThreshold: 5,
        autoResend: false
    },
    
    // UI settings
    ui: {
        fadeOutDuration: 200,
        slideDownDuration: 300,
        progressBarUpdate: 100 // milliseconds
    }
};

// =============================================================================
// COUNTDOWN CORE SYSTEM
// =============================================================================

class CountdownManager {
    constructor() {
        this.timers = new Map();
        this.activeCountdowns = new Map();
        this.isInitialized = false;
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.initializeGlobalCountdowns();
        this.isInitialized = true;
        console.log('⏰ Countdown System initialized');
    }

    // =============================================================================
    // EMAIL VERIFICATION COUNTDOWN
    // =============================================================================

    /**
     * Initialize email verification countdown timer
     * @param {Object} options - Configuration options
     * @param {number} options.timeUntilResend - Initial time in seconds
     * @param {string} options.timerId - ID of timer element
     * @param {string} options.countdownId - ID of countdown container
     * @param {string} options.resendFormId - ID of resend form
     * @param {boolean} options.canResend - Whether resend is currently allowed
     */
    initializeEmailCountdown(options) {
        const {
            timeUntilResend,
            timerId = 'timer',
            countdownId = 'countdown',
            resendFormId = 'resend-form',
            canResend = false
        } = options;

        const timerElement = document.getElementById(timerId);
        const countdownElement = document.getElementById(countdownId);
        const resendForm = document.getElementById(resendFormId);

        if (!timerElement || !countdownElement) {
            console.warn('Email countdown elements not found');
            return;
        }

        if (canResend) {
            // Show resend form immediately
            countdownElement.style.display = 'none';
            if (resendForm) resendForm.style.display = 'block';
            return;
        }

        if (timeUntilResend > 0) {
            this.startEmailCountdown({
                timerElement,
                countdownElement,
                resendForm,
                initialTime: timeUntilResend
            });
        }
    }

    startEmailCountdown(options) {
        const {
            timerElement,
            countdownElement,
            resendForm,
            initialTime
        } = options;

        let timeLeft = initialTime;
        
        const updateTimer = () => {
            if (timeLeft <= 0) {
                // Show resend form when timer reaches zero
                this.showResendForm(countdownElement, resendForm);
                return;
            }

            // Update timer display
            this.updateTimerDisplay(timerElement, timeLeft);
            
            // Show warning if approaching threshold
            if (timeLeft <= COUNTDOWN_CONFIG.email.warningThreshold) {
                this.showWarningState(timerElement, countdownElement);
            }

            timeLeft--;
        };

        // Start the countdown
        updateTimer();
        const intervalId = setInterval(updateTimer, COUNTDOWN_CONFIG.default.updateInterval);
        
        // Store for cleanup
        this.activeCountdowns.set(countdownElement, {
            intervalId,
            type: 'email',
            options
        });
    }

    // =============================================================================
    // TOTP COUNTDOWN
    // =============================================================================

    /**
     * Initialize TOTP countdown timer
     * @param {Object} options - Configuration options
     */
    initializeTOTPCountdown(options) {
        const {
            timeUntilResend,
            timerId = 'timer',
            countdownId = 'countdown',
            resendFormId = 'resend-form',
            canResend = false
        } = options;

        const timerElement = document.getElementById(timerId);
        const countdownElement = document.getElementById(countdownId);
        const resendForm = document.getElementById(resendFormId);

        if (!timerElement || !countdownElement) {
            console.warn('TOTP countdown elements not found');
            return;
        }

        if (canResend) {
            countdownElement.style.display = 'none';
            if (resendForm) resendForm.style.display = 'block';
            return;
        }

        if (timeUntilResend > 0) {
            this.startTOTPCountdown({
                timerElement,
                countdownElement,
                resendForm,
                initialTime: timeUntilResend
            });
        }
    }

    startTOTPCountdown(options) {
        const {
            timerElement,
            countdownElement,
            resendForm,
            initialTime
        } = options;

        let timeLeft = initialTime;
        
        const updateTimer = () => {
            if (timeLeft <= 0) {
                this.showResendForm(countdownElement, resendForm);
                return;
            }

            this.updateTimerDisplay(timerElement, timeLeft);
            
            if (timeLeft <= COUNTDOWN_CONFIG.totp.warningThreshold) {
                this.showWarningState(timerElement, countdownElement);
            }

            timeLeft--;
        };

        updateTimer();
        const intervalId = setInterval(updateTimer, COUNTDOWN_CONFIG.default.updateInterval);
        
        this.activeCountdowns.set(countdownElement, {
            intervalId,
            type: 'totp',
            options
        });
    }

    // =============================================================================
    // GENERIC COUNTDOWN SYSTEM
    // =============================================================================

    /**
     * Create a generic countdown timer
     * @param {Object} options - Configuration options
     * @param {number} options.duration - Duration in seconds
     * @param {Function} options.onTick - Callback for each tick
     * @param {Function} options.onComplete - Callback when complete
     * @param {string} options.timerId - ID of timer element
     * @param {string} options.countdownId - ID of countdown container
     */
    createGenericCountdown(options) {
        const {
            duration,
            onTick,
            onComplete,
            timerId,
            countdownId
        } = options;

        const timerElement = timerId ? document.getElementById(timerId) : null;
        const countdownElement = countdownId ? document.getElementById(countdownId) : null;

        let timeLeft = duration;
        
        const updateTimer = () => {
            if (timeLeft <= 0) {
                if (onComplete) onComplete();
                return;
            }

            if (onTick) onTick(timeLeft);
            if (timerElement) this.updateTimerDisplay(timerElement, timeLeft);

            timeLeft--;
        };

        updateTimer();
        const intervalId = setInterval(updateTimer, COUNTDOWN_CONFIG.default.updateInterval);
        
        const countdownKey = countdownElement || `generic_${Date.now()}`;
        this.activeCountdowns.set(countdownKey, {
            intervalId,
            type: 'generic',
            options
        });

        return intervalId;
    }

    // =============================================================================
    // TIMER DISPLAY UTILITIES
    // =============================================================================

    updateTimerDisplay(timerElement, timeLeft) {
        if (!timerElement) return;

        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;

        if (minutes > 0) {
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        } else {
            timerElement.textContent = seconds.toString();
        }
    }

    showWarningState(timerElement, countdownElement) {
        if (timerElement) {
            timerElement.style.color = '#ff6b35';
            timerElement.style.fontWeight = 'bold';
        }
        
        if (countdownElement) {
            countdownElement.classList.add('warning');
        }
    }

    showResendForm(countdownElement, resendForm) {
        if (countdownElement) {
            countdownElement.style.display = 'none';
        }
        
        if (resendForm) {
            resendForm.style.display = 'block';
            // Add fade-in animation
            resendForm.style.opacity = '0';
            resendForm.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                resendForm.style.transition = `all ${COUNTDOWN_CONFIG.default.animationDuration}ms ease`;
                resendForm.style.opacity = '1';
                resendForm.style.transform = 'translateY(0)';
            }, COUNTDOWN_CONFIG.default.showResendDelay);
        }
    }

    // =============================================================================
    // PROGRESS BAR COUNTDOWN
    // =============================================================================

    /**
     * Create a progress bar countdown
     * @param {Object} options - Configuration options
     * @param {string} options.progressBarId - ID of progress bar element
     * @param {number} options.duration - Duration in seconds
     * @param {Function} options.onComplete - Callback when complete
     */
    createProgressBarCountdown(options) {
        const {
            progressBarId,
            duration,
            onComplete
        } = options;

        const progressBar = document.getElementById(progressBarId);
        if (!progressBar) {
            console.warn('Progress bar element not found');
            return;
        }

        let timeLeft = duration;
        const totalTime = duration;
        
        const updateProgress = () => {
            if (timeLeft <= 0) {
                if (onComplete) onComplete();
                return;
            }

            const progress = ((totalTime - timeLeft) / totalTime) * 100;
            progressBar.style.width = `${progress}%`;
            
            // Update progress bar color based on remaining time
            if (timeLeft <= totalTime * 0.2) {
                progressBar.style.backgroundColor = '#dc3545'; // Red
            } else if (timeLeft <= totalTime * 0.5) {
                progressBar.style.backgroundColor = '#ffc107'; // Yellow
            } else {
                progressBar.style.backgroundColor = '#28a745'; // Green
            }

            timeLeft--;
        };

        updateProgress();
        const intervalId = setInterval(updateProgress, COUNTDOWN_CONFIG.ui.progressBarUpdate);
        
        this.activeCountdowns.set(progressBar, {
            intervalId,
            type: 'progress',
            options
        });

        return intervalId;
    }

    // =============================================================================
    // COUNTDOWN MANAGEMENT
    // =============================================================================

    /**
     * Stop a specific countdown
     * @param {Element|string} countdownKey - Countdown element or ID
     */
    stopCountdown(countdownKey) {
        const countdown = this.activeCountdowns.get(countdownKey);
        if (countdown) {
            clearInterval(countdown.intervalId);
            this.activeCountdowns.delete(countdownKey);
        }
    }

    /**
     * Stop all countdowns
     */
    stopAllCountdowns() {
        this.activeCountdowns.forEach((countdown, key) => {
            clearInterval(countdown.intervalId);
        });
        this.activeCountdowns.clear();
    }

    /**
     * Pause a countdown
     * @param {Element|string} countdownKey - Countdown element or ID
     */
    pauseCountdown(countdownKey) {
        const countdown = this.activeCountdowns.get(countdownKey);
        if (countdown) {
            countdown.isPaused = true;
            clearInterval(countdown.intervalId);
        }
    }

    /**
     * Resume a paused countdown
     * @param {Element|string} countdownKey - Countdown element or ID
     */
    resumeCountdown(countdownKey) {
        const countdown = this.activeCountdowns.get(countdownKey);
        if (countdown && countdown.isPaused) {
            countdown.isPaused = false;
            // Restart the countdown logic here
            // This would need to be implemented based on the specific countdown type
        }
    }

    // =============================================================================
    // UTILITY FUNCTIONS
    // =============================================================================

    /**
     * Format time in human-readable format
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time string
     */
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else if (minutes > 0) {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        } else {
            return secs.toString();
        }
    }

    /**
     * Check if a countdown is active
     * @param {Element|string} countdownKey - Countdown element or ID
     * @returns {boolean} Whether countdown is active
     */
    isCountdownActive(countdownKey) {
        return this.activeCountdowns.has(countdownKey);
    }

    /**
     * Get countdown information
     * @param {Element|string} countdownKey - Countdown element or ID
     * @returns {Object|null} Countdown information
     */
    getCountdownInfo(countdownKey) {
        return this.activeCountdowns.get(countdownKey) || null;
    }

    // =============================================================================
    // INITIALIZATION
    // =============================================================================

    initializeGlobalCountdowns() {
        // Look for countdown elements on page load
        this.initializePageCountdowns();
        
        // Listen for dynamic content changes
        this.observeDOMChanges();
    }

    initializePageCountdowns() {
        // Initialize email countdowns
        const emailCountdowns = document.querySelectorAll('[data-countdown-type="email"]');
        emailCountdowns.forEach(countdown => {
            const timeUntilResend = parseInt(countdown.dataset.timeUntilResend || '0');
            const canResend = countdown.dataset.canResend === 'true';
            
            if (timeUntilResend > 0 || !canResend) {
                this.initializeEmailCountdown({
                    timeUntilResend,
                    timerId: countdown.querySelector('[id*="timer"]')?.id,
                    countdownId: countdown.id,
                    resendFormId: countdown.querySelector('[id*="resend"]')?.id,
                    canResend
                });
            }
        });

        // Initialize TOTP countdowns
        const totpCountdowns = document.querySelectorAll('[data-countdown-type="totp"]');
        totpCountdowns.forEach(countdown => {
            const timeUntilResend = parseInt(countdown.dataset.timeUntilResend || '0');
            const canResend = countdown.dataset.canResend === 'true';
            
            if (timeUntilResend > 0 || !canResend) {
                this.initializeTOTPCountdown({
                    timeUntilResend,
                    timerId: countdown.querySelector('[id*="timer"]')?.id,
                    countdownId: countdown.id,
                    resendFormId: countdown.querySelector('[id*="resend"]')?.id,
                    canResend
                });
            }
        });
    }

    observeDOMChanges() {
        // Use MutationObserver to detect dynamic content changes
        if (window.MutationObserver) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Check if new countdown elements were added
                                const newCountdowns = node.querySelectorAll('[data-countdown-type]');
                                if (newCountdowns.length > 0) {
                                    this.initializePageCountdowns();
                                }
                            }
                        });
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    // =============================================================================
    // CLEANUP
    // =============================================================================

    destroy() {
        this.stopAllCountdowns();
        this.isInitialized = false;
        console.log('⏰ Countdown System destroyed');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.countdownManager = new CountdownManager();

// Make functions globally accessible
window.initializeEmailCountdown = (options) => window.countdownManager.initializeEmailCountdown(options);
window.initializeTOTPCountdown = (options) => window.countdownManager.initializeTOTPCountdown(options);
window.createGenericCountdown = (options) => window.countdownManager.createGenericCountdown(options);
window.createProgressBarCountdown = (options) => window.countdownManager.createProgressBarCountdown(options);
window.stopCountdown = (key) => window.countdownManager.stopCountdown(key);
window.stopAllCountdowns = () => window.countdownManager.stopAllCountdowns();
window.pauseCountdown = (key) => window.countdownManager.pauseCountdown(key);
window.resumeCountdown = (key) => window.countdownManager.resumeCountdown(key);
window.formatTime = (seconds) => window.countdownManager.formatTime(seconds);

// =============================================================================
// LEGACY SUPPORT
// =============================================================================

// Support for existing countdown functionality
window.start2FACountdown = function(initialTime, timerElement, countdownElement) {
    return window.countdownManager.startEmailCountdown({
        timerElement,
        countdownElement,
        initialTime
    });
};

// =============================================================================
// DEBUG AND VERIFICATION
// =============================================================================

window.debugCountdownSystem = function() {
    console.log('🔍 Debugging Countdown System...');
    
    const functions = [
        'initializeEmailCountdown',
        'initializeTOTPCountdown',
        'createGenericCountdown',
        'createProgressBarCountdown',
        'stopCountdown',
        'stopAllCountdowns',
        'formatTime'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName}: Available`);
        } else {
            console.log(`❌ ${funcName}: Missing`);
        }
    });
    
    console.log(`⏰ Active countdowns: ${window.countdownManager.activeCountdowns.size}`);
    console.log('🔍 Countdown System Debug Complete');
};

// Auto-debug on page load if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof window.debugCountdownSystem === 'function') {
                window.debugCountdownSystem();
            }
        }, 1000);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CountdownManager;
}