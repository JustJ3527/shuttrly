/**
 * Django Messages Manager
 * Handles automatic removal and management of Django messages
 */

class MessageManager {
    constructor() {
        this.messagesContainer = null;
        this.alerts = [];
        this.removalTimers = new Map();
        this.init();
    }

    init() {
        this.messagesContainer = document.getElementById('django-messages');
        if (this.messagesContainer) {
            this.alerts = this.messagesContainer.querySelectorAll('.alert');
            console.log(`MessageManager: Found ${this.alerts.length} messages`);
            this.setupEventListeners();
            this.startAutoRemoval();
        } else {
            console.log('MessageManager: No messages container found');
        }
    }

    setupEventListeners() {
        // Close button events
        this.alerts.forEach(alert => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.addEventListener('click', () => this.removeAlert(alert));
            }
        });

        // Page navigation events - only remove on actual navigation
        window.addEventListener('beforeunload', () => {
            console.log('MessageManager: Page unloading, removing all alerts');
            this.removeAllAlerts(false);
        });
        
        // Page visibility change - be more conservative
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('MessageManager: Page hidden, pausing timers');
                this.pauseTimers();
            } else {
                console.log('MessageManager: Page visible, resuming timers');
                this.resumeTimers();
            }
        });

        // Form submission - only remove if actually navigating away
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM' && !form.hasAttribute('data-ajax')) {
                console.log('MessageManager: Form submission detected, removing alerts');
                this.removeAllAlerts(false);
            }
        });

        // URL change detection - be more conservative
        this.setupUrlChangeDetection();
    }

    setupUrlChangeDetection() {
        let currentUrl = window.location.href;
        let urlChangeCount = 0;
        
        const urlCheckInterval = setInterval(() => {
            if (currentUrl !== window.location.href) {
                urlChangeCount++;
                console.log(`MessageManager: URL change detected (${urlChangeCount})`);
                
                // Only remove messages after multiple URL changes to avoid false positives
                if (urlChangeCount >= 2) {
                    currentUrl = window.location.href;
                    console.log('MessageManager: Multiple URL changes, removing alerts');
                    this.removeAllAlerts(false);
                    clearInterval(urlCheckInterval);
                }
            }
        }, 500); // Check less frequently
    }

    startAutoRemoval() {
        this.alerts.forEach((alert, index) => {
            const delay = 15000 + (index * 1000); // 15 seconds + 1 second per message
            console.log(`MessageManager: Setting timer for message ${index + 1} to ${delay}ms`);
            
            const timer = setTimeout(() => {
                console.log(`MessageManager: Auto-removing message ${index + 1}`);
                this.removeAlert(alert);
            }, delay);
            
            this.removalTimers.set(alert, timer);
        });
    }

    pauseTimers() {
        // Store remaining time for each timer
        this.alerts.forEach(alert => {
            if (this.removalTimers.has(alert)) {
                const timer = this.removalTimers.get(alert);
                const remainingTime = this.getRemainingTime(timer);
                alert.dataset.remainingTime = remainingTime;
                clearTimeout(timer);
            }
        });
    }

    resumeTimers() {
        // Restart timers with remaining time
        this.alerts.forEach(alert => {
            if (alert.dataset.remainingTime) {
                const remainingTime = parseInt(alert.dataset.remainingTime);
                const timer = setTimeout(() => {
                    this.removeAlert(alert);
                }, remainingTime);
                this.removalTimers.set(alert, timer);
                delete alert.dataset.remainingTime;
            }
        });
    }

    getRemainingTime(timer) {
        // This is a simplified approach - in a real implementation you'd need to track start times
        return 5000; // Default 5 seconds if we can't calculate
    }

    removeAlert(alert, animate = true) {
        console.log('MessageManager: Removing alert', alert);
        
        // Clear the timer if it exists
        if (this.removalTimers.has(alert)) {
            clearTimeout(this.removalTimers.get(alert));
            this.removalTimers.delete(alert);
        }

        if (animate) {
            alert.classList.add('removing');
            setTimeout(() => {
                this.finalizeRemoval(alert);
            }, 300);
        } else {
            this.finalizeRemoval(alert);
        }
    }

    finalizeRemoval(alert) {
        if (alert && alert.parentNode) {
            alert.remove();
        }
        
        // Remove from alerts array
        const index = Array.from(this.alerts).indexOf(alert);
        if (index > -1) {
            this.alerts.splice(index, 1);
        }

        // Remove container if no more alerts
        if (this.messagesContainer && this.messagesContainer.children.length === 0) {
            this.messagesContainer.remove();
        }
    }

    removeAllAlerts(animate = true) {
        console.log(`MessageManager: Removing all ${this.alerts.length} alerts`);
        this.alerts.forEach(alert => this.removeAlert(alert, animate));
    }

    // Public method to manually remove all messages
    static clearAll() {
        const manager = new MessageManager();
        if (manager.messagesContainer) {
            manager.removeAllAlerts(false);
        }
    }

    // Public method to remove messages by type
    static clearByType(type) {
        const manager = new MessageManager();
        if (manager.messagesContainer) {
            const typeAlerts = manager.messagesContainer.querySelectorAll(`.alert-${type}`);
            typeAlerts.forEach(alert => manager.removeAlert(alert, false));
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new MessageManager();
});

// Global functions for external use
window.MessageManager = MessageManager;
window.clearAllMessages = () => MessageManager.clearAll();
window.clearMessagesByType = (type) => MessageManager.clearByType(type);
