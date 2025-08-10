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
            this.setupEventListeners();
            this.startAutoRemoval();
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

        // Page navigation events
        window.addEventListener('beforeunload', () => this.removeAllAlerts(false));
        window.addEventListener('popstate', () => this.removeAllAlerts(false));
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.removeAllAlerts(false);
            }
        });

        // Form submission
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                this.removeAllAlerts(false);
            }
        });

        // URL change detection
        this.setupUrlChangeDetection();
    }

    setupUrlChangeDetection() {
        let currentUrl = window.location.href;
        const urlCheckInterval = setInterval(() => {
            if (currentUrl !== window.location.href) {
                currentUrl = window.location.href;
                this.removeAllAlerts(false);
                clearInterval(urlCheckInterval);
            }
        }, 100);
    }

    startAutoRemoval() {
        this.alerts.forEach((alert, index) => {
            const timer = setTimeout(() => {
                this.removeAlert(alert);
            }, 8000 + (index * 500)); // Stagger removal
            
            this.removalTimers.set(alert, timer);
        });
    }

    removeAlert(alert, animate = true) {
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
