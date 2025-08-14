/**
 * Global Configuration File
 * Centralizes all configuration for JavaScript modules
 * 
 * @author Shuttrly
 * @version 1.0.0
 */

// =============================================================================
// GLOBAL CONFIGURATION
// =============================================================================

window.SHUTTRLY_CONFIG = {
    // Environment settings
    environment: {
        isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
        isProduction: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
        debugMode: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    },

    // API settings
    api: {
        baseUrl: window.location.origin,
        timeout: 30000,
        retryAttempts: 3,
        retryDelay: 1000
    },

    // UI Configuration
    ui: {
        // Animation settings
        animation: {
            duration: 300,
            easing: 'ease',
            fadeInDelay: 100,
            slideDistance: 20,
            staggerDelay: 50
        },
        
        // Transition settings
        transition: {
            duration: 200,
            easing: 'ease-in-out'
        },
        
        // Debounce settings
        debounce: {
            defaultDelay: 300,
            searchDelay: 500,
            resizeDelay: 250,
            scrollDelay: 100
        },
        
        // Scroll settings
        scroll: {
            smooth: true,
            offset: 0,
            duration: 800,
            threshold: 0.1
        },
        
        // Loading settings
        loading: {
            spinnerSize: 'sm',
            spinnerColor: 'primary',
            text: 'Loading...',
            timeout: 10000
        }
    },

    // Form Validation Configuration
    validation: {
        // Password validation rules
        password: {
            minLength: 8,
            maxLength: 128,
            requireUppercase: true,
            requireLowercase: true,
            requireNumbers: true,
            requireSpecialChars: false,
            strengthThreshold: 3
        },
        
        // Username validation rules
        username: {
            minLength: 3,
            maxLength: 30,
            allowedChars: /^[a-zA-Z0-9_-]+$/,
            reservedNames: ['admin', 'root', 'system', 'test', 'guest', 'user', 'anonymous']
        },
        
        // Email validation rules
        email: {
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            maxLength: 254,
            allowPlusSign: true
        },
        
        // Verification code validation rules
        verificationCode: {
            length: 6,
            pattern: /^\d{6}$/,
            autoSubmit: true,
            inputDelay: 100
        },
        
        // UI settings
        ui: {
            errorDisplayTime: 5000,
            animationDuration: 300,
            debounceDelay: 300,
            successDisplayTime: 3000
        }
    },

    // Countdown Configuration
    countdown: {
        // Default settings
        default: {
            updateInterval: 1000,
            animationDuration: 300,
            showResendDelay: 1000,
            warningThreshold: 10
        },
        
        // Email verification settings
        email: {
            resendDelay: 60,
            warningThreshold: 10,
            autoResend: false,
            maxResendAttempts: 3
        },
        
        // TOTP settings
        totp: {
            resendDelay: 30,
            warningThreshold: 5,
            autoResend: false,
            maxResendAttempts: 5
        },
        
        // UI settings
        ui: {
            fadeOutDuration: 200,
            slideDownDuration: 300,
            progressBarUpdate: 100,
            warningColor: '#ff6b35'
        }
    },

    // 2FA Configuration
    twofa: {
        // TOTP settings
        totp: {
            codeLength: 6,
            codePattern: /^\d{6}$/,
            autoSubmit: true,
            inputDelay: 100,
            maxAttempts: 3
        },
        
        // Email 2FA settings
        email: {
            codeLength: 6,
            codePattern: /^\d{6}$/,
            autoSubmit: true,
            resendDelay: 60,
            maxAttempts: 5
        },
        
        // Trusted devices settings
        trustedDevices: {
            maxDevices: 10,
            expirationDays: 30,
            autoCleanup: true
        },
        
        // UI settings
        ui: {
            animationDuration: 500,
            fadeInDelay: 100,
            errorDisplayTime: 3000,
            successDisplayTime: 2000
        }
    },

    // Authentication Configuration
    auth: {
        // Session settings
        session: {
            timeout: 3600, // 1 hour
            refreshThreshold: 300, // 5 minutes
            maxConcurrentSessions: 5
        },
        
        // Rate limiting
        rateLimit: {
            loginAttempts: 5,
            lockoutDuration: 900, // 15 minutes
            resetAttempts: 3
        },
        
        // Security settings
        security: {
            require2FA: false,
            passwordHistory: 5,
            minPasswordAge: 1, // days
            maxPasswordAge: 365 // days
        }
    },

    // Message Configuration
    messages: {
        // Auto-clear settings
        autoClear: {
            enabled: true,
            success: 5000,
            info: 8000,
            warning: 10000,
            error: 15000
        },
        
        // Animation settings
        animation: {
            slideIn: true,
            slideOut: true,
            duration: 300
        }
    },

    // Feature Flags
    features: {
        // Enable/disable features
        twoFactorAuth: true,
        passwordStrength: true,
        autoComplete: true,
        darkMode: false,
        accessibility: true,
        analytics: false,
        
        // Experimental features
        experimental: {
            progressiveWebApp: false,
            serviceWorker: false,
            webPushNotifications: false
        }
    }
};

// =============================================================================
// CONFIGURATION HELPERS
// =============================================================================

window.SHUTTRLY_CONFIG.get = function(path, defaultValue = null) {
    const keys = path.split('.');
    let value = this;
    
    for (const key of keys) {
        if (value && typeof value === 'object' && key in value) {
            value = value[key];
        } else {
            return defaultValue;
        }
    }
    
    return value;
};

window.SHUTTRLY_CONFIG.set = function(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = this;
    
    for (const key of keys) {
        if (!(key in current) || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }
    
    current[lastKey] = value;
};

window.SHUTTRLY_CONFIG.merge = function(path, config) {
    const current = this.get(path, {});
    const merged = { ...current, ...config };
    this.set(path, merged);
};

// =============================================================================
// ENVIRONMENT-SPECIFIC OVERRIDES
// =============================================================================

// Development overrides
if (window.SHUTTRLY_CONFIG.environment.isDevelopment) {
    window.SHUTTRLY_CONFIG.debugMode = true;
    window.SHUTTRLY_CONFIG.features.experimental.progressiveWebApp = true;
    window.SHUTTRLY_CONFIG.features.experimental.serviceWorker = true;
}

// Production overrides
if (window.SHUTTRLY_CONFIG.environment.isProduction) {
    window.SHUTTRLY_CONFIG.debugMode = false;
    window.SHUTTRLY_CONFIG.features.analytics = true;
    window.SHUTTRLY_CONFIG.api.timeout = 15000;
}

// =============================================================================
// CONFIGURATION VALIDATION
// =============================================================================

window.SHUTTRLY_CONFIG.validate = function() {
    const errors = [];
    
    // Validate required configurations
    if (!this.ui.animation.duration) {
        errors.push('UI animation duration is required');
    }
    
    if (!this.validation.password.minLength) {
        errors.push('Password minimum length is required');
    }
    
    if (!this.countdown.email.resendDelay) {
        errors.push('Email countdown resend delay is required');
    }
    
    if (errors.length > 0) {
        console.error('Configuration validation errors:', errors);
        return false;
    }
    
    return true;
};

// =============================================================================
// CONFIGURATION INITIALIZATION
// =============================================================================

window.SHUTTRLY_CONFIG.init = function() {
    // Validate configuration
    if (!this.validate()) {
        console.error('Invalid configuration detected');
        return false;
    }
    
    // Apply configuration to modules
    this.applyToModules();
    
    console.log('✅ Configuration loaded successfully');
    return true;
};

window.SHUTTRLY_CONFIG.applyToModules = function() {
    // Apply UI configuration
    if (window.UI_CONFIG) {
        Object.assign(window.UI_CONFIG, this.ui);
    }
    
    // Apply validation configuration
    if (window.VALIDATION_CONFIG) {
        Object.assign(window.VALIDATION_CONFIG, this.validation);
    }
    
    // Apply countdown configuration
    if (window.COUNTDOWN_CONFIG) {
        Object.assign(window.COUNTDOWN_CONFIG, this.countdown);
    }
    
    // Apply 2FA configuration
    if (window.TWOFA_CONFIG) {
        Object.assign(window.TWOFA_CONFIG, this.twofa);
    }
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

window.SHUTTRLY_CONFIG.isFeatureEnabled = function(featurePath) {
    return this.get(`features.${featurePath}`, false);
};

window.SHUTTRLY_CONFIG.getApiUrl = function(endpoint) {
    return `${this.api.baseUrl}${endpoint}`;
};

window.SHUTTRLY_CONFIG.getTimeout = function(type = 'default') {
    const timeouts = {
        default: this.api.timeout,
        short: 5000,
        long: 60000
    };
    
    return timeouts[type] || timeouts.default;
};

// =============================================================================
// AUTO-INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize configuration
    window.SHUTTRLY_CONFIG.init();
    
    // Log configuration in development
    if (window.SHUTTRLY_CONFIG.environment.isDevelopment) {
        console.log('🔧 Configuration loaded:', window.SHUTTRLY_CONFIG);
    }
});

// =============================================================================
// EXPORTS
// =============================================================================

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.SHUTTRLY_CONFIG;
}