/**
 * Notifications System JavaScript
 * Handles all notification-related interactions including modal, tabs, and actions
 */

class NotificationsManager {
    constructor() {
        this.currentTab = 'all';
        this.currentPage = 1;
        this.isLoading = false;
        this.notifications = [];
        this.counts = {};
        this.refreshInterval = null;
        
        this.init();
    }

    init() {
        // Only initialize if user is authenticated
        if (!document.getElementById('notifications-btn')) {
            return;
        }

        this.bindEvents();
        this.loadNotificationCount();
        this.setupPeriodicRefresh();
    }

    bindEvents() {
        // Notification button click
        const notificationBtn = document.getElementById('notifications-btn');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => this.toggleModal());
        }

        // Modal close events
        const closeBtn = document.getElementById('close-notifications-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }

        const modal = document.getElementById('notifications-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }

        // Tab switching
        const tabs = document.querySelectorAll('.notification-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabType = tab.getAttribute('data-tab');
                this.switchTab(tabType);
            });
        });

        // Action buttons
        this.bindActionButtons();
    }

    bindActionButtons() {
        // Mark all as read
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }

        // Clear all
        const clearAllBtn = document.getElementById('clear-all-btn');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllNotifications());
        }

        // Load more
        const loadMoreBtn = document.getElementById('load-more-notifications');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => this.loadMoreNotifications());
        }

        // Retry button
        const retryBtn = document.getElementById('retry-notifications');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.loadNotifications());
        }
    }

    toggleModal() {
        const modal = document.getElementById('notifications-modal');
        if (modal.classList.contains('show')) {
            this.closeModal();
        } else {
            this.openModal();
        }
    }

    openModal() {
        const modal = document.getElementById('notifications-modal');
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Load notifications when opening
        this.loadNotifications();
    }

    closeModal() {
        const modal = document.getElementById('notifications-modal');
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    switchTab(tabType) {
        if (this.currentTab === tabType) return;

        // Update active tab
        document.querySelectorAll('.notification-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabType}"]`).classList.add('active');

        this.currentTab = tabType;
        this.currentPage = 1;
        this.notifications = [];
        
        this.loadNotifications();
    }

    async loadNotificationCount() {
        try {
            const response = await fetch('/ajax/get-notification-count/');
            const data = await response.json();
            
            if (data.success) {
                this.updateNotificationBadge(data.count);
            }
        } catch (error) {
            console.error('Error loading notification count:', error);
        }
    }

    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    async loadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();

        try {
            const response = await fetch(`/ajax/get-notifications/?type=${this.currentTab}&page=${this.currentPage}`);
            const data = await response.json();
            
            if (data.success) {
                // Clear existing notifications completely
                this.notifications = [];
                
                // Load new notifications
                this.notifications = data.notifications;
                this.counts = data.counts;
                this.updateTabCounts();
                this.renderNotifications();
                this.updateLoadMoreButton(data.has_next);
            } else {
                this.showError(data.message || 'Error loading notifications');
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Error loading notifications');
        } finally {
            this.isLoading = false;
        }
    }

    async loadMoreNotifications() {
        if (this.isLoading) return;
        
        this.currentPage++;
        this.isLoading = true;

        try {
            const response = await fetch(`/ajax/get-notifications/?type=${this.currentTab}&page=${this.currentPage}`);
            const data = await response.json();
            
            if (data.success) {
                this.notifications = [...this.notifications, ...data.notifications];
                this.renderNotifications();
                this.updateLoadMoreButton(data.has_next);
            } else {
                this.currentPage--; // Revert page increment
                console.error('Error loading more notifications:', data.message);
            }
        } catch (error) {
            this.currentPage--; // Revert page increment
            console.error('Error loading more notifications:', error);
        } finally {
            this.isLoading = false;
        }
    }

    updateTabCounts() {
        Object.keys(this.counts).forEach(tabType => {
            const countElement = document.getElementById(`${tabType}-count`);
            if (countElement) {
                countElement.textContent = this.counts[tabType];
            }
        });
    }

    async refreshTabCounts() {
        try {
            const response = await fetch(`/ajax/get-notifications/?type=${this.currentTab}&page=1`);
            const data = await response.json();
            
            if (data.success) {
                this.counts = data.counts;
                this.updateTabCounts();
            }
        } catch (error) {
            console.error('Error refreshing tab counts:', error);
        }
    }

    renderNotifications() {
        const container = document.getElementById('notifications-list');
        const loading = document.getElementById('notifications-loading');
        const empty = document.getElementById('notifications-empty');
        const error = document.getElementById('notifications-error');

        // Hide all states
        [loading, empty, error].forEach(el => {
            if (el) el.style.display = 'none';
        });

        if (this.notifications.length === 0) {
            if (empty) empty.style.display = 'flex';
            return;
        }

        if (container) {
            container.style.display = 'block';
            container.innerHTML = this.generateNotificationsHTML();
            this.bindNotificationEvents();
        }
    }

    generateNotificationsHTML() {
        return this.notifications.map(notification => {
            const fullName = notification.from_user && notification.from_user.first_name && notification.from_user.last_name
                ? `${notification.from_user.first_name} ${notification.from_user.last_name}`
                : notification.from_user ? notification.from_user.username : 'System';

            const avatarHTML = notification.from_user && notification.from_user.profile_picture
                ? `<img src="${notification.from_user.profile_picture}" alt="${notification.from_user.username}" class="notification-avatar-img">`
                : `<div class="notification-avatar-placeholder"><i class="fas fa-user"></i></div>`;

            const actionButtonsHTML = this.generateActionButtonsHTML(notification);
            const relatedContentHTML = this.generateRelatedContentHTML(notification);

            return `
                <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                     data-notification-id="${notification.id}" 
                     data-type="${notification.type}">
                    <div class="notification-avatar">
                        ${avatarHTML}
                    </div>
                    <div class="notification-content">
                        <div class="notification-header">
                            <h6 class="notification-title">${notification.title}</h6>
                            <div class="notification-actions">
                                ${!notification.is_read ? `
                                    <button class="notification-action-btn mark-read-btn" data-notification-id="${notification.id}" title="Mark as read">
                                        <i class="fas fa-check"></i>
                                    </button>
                                ` : ''}
                                <button class="notification-action-btn delete-btn" data-notification-id="${notification.id}" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <p class="notification-message">${notification.message}</p>
                        <div class="notification-meta">
                            <span class="notification-time">${this.formatTimeAgo(notification.created_at)}</span>
                            <span class="notification-type-badge">${notification.type.replace('_', ' ')}</span>
                        </div>
                        ${actionButtonsHTML}
                        ${relatedContentHTML}
                    </div>
                    ${!notification.is_read ? '<div class="notification-unread-indicator"></div>' : ''}
                </div>
            `;
        }).join('');
    }

    generateActionButtonsHTML(notification) {
        if (notification.type === 'follow_request' && notification.from_user) {
            return `
                <div class="notification-action-buttons">
                    <button class="notification-action-button btn-accept" data-notification-id="${notification.id}" data-action="accept">
                        <i class="fas fa-check"></i> Accept
                    </button>
                    <button class="notification-action-button btn-reject" data-notification-id="${notification.id}" data-action="reject">
                        <i class="fas fa-times"></i> Reject
                    </button>
                </div>
            `;
        }
        return '';
    }

    generateRelatedContentHTML(notification) {
        // For like and comment notifications, show post cover on the right
        if ((notification.type === 'photo_liked' || notification.type === 'photo_commented') && notification.related_photo && notification.related_photo.thumbnail_url) {
            return `
                <div class="notification-post-cover" title="View post">
                    <img src="${notification.related_photo.thumbnail_url}" alt="Post cover">
                </div>
            `;
        }
        
        // For other notifications, show related content below
        if (notification.related_photo && notification.related_photo.thumbnail_url) {
            return `
                <div class="notification-related-content">
                    <img src="${notification.related_photo.thumbnail_url}" alt="Related photo" class="notification-related-image">
                </div>
            `;
        }
        
        if (notification.related_collection) {
            const coverHTML = notification.related_collection.cover_photo && notification.related_collection.cover_photo.thumbnail_url
                ? `<img src="${notification.related_collection.cover_photo.thumbnail_url}" alt="${notification.related_collection.name}" class="notification-related-image">`
                : `<div class="notification-collection-placeholder"><i class="fas fa-folder"></i></div>`;
            
            return `
                <div class="notification-related-content">
                    <div class="notification-related-collection">
                        ${coverHTML}
                        <span class="notification-collection-name">${notification.related_collection.name}</span>
                    </div>
                </div>
            `;
        }
        
        return '';
    }

    bindNotificationEvents() {
        // Mark as read buttons
        document.querySelectorAll('.mark-read-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = btn.getAttribute('data-notification-id');
                this.markAsRead(notificationId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = btn.getAttribute('data-notification-id');
                this.deleteNotification(notificationId);
            });
        });

        // Action buttons (accept/reject)
        document.querySelectorAll('.notification-action-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = btn.getAttribute('data-notification-id');
                const action = btn.getAttribute('data-action');
                this.handleNotificationAction(notificationId, action);
            });
        });

        // Post cover click (for like and comment notifications)
        document.querySelectorAll('.notification-post-cover').forEach(cover => {
            cover.addEventListener('click', (e) => {
                e.stopPropagation();
                // TODO: Navigate to the post when post detail view is implemented
                console.log('Navigate to post');
            });
        });
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch('/ajax/mark-notification-read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `notification_id=${notificationId}`
            });
            
            const data = await response.json();
            if (data.success) {
                this.updateNotificationReadState(notificationId);
                this.loadNotificationCount(); // Update badge
                this.refreshTabCounts(); // Update tab counts with real-time data
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async deleteNotification(notificationId) {
        try {
            const response = await fetch('/ajax/delete-notification/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `notification_id=${notificationId}`
            });
            
            const data = await response.json();
            if (data.success) {
                this.removeNotificationFromDOM(notificationId);
                this.loadNotificationCount(); // Update badge
                this.refreshTabCounts(); // Update tab counts with real-time data
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/ajax/mark-all-notifications-read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.loadNotifications(); // Reload to update UI
                this.loadNotificationCount(); // Update badge
                this.refreshTabCounts(); // Update tab counts with real-time data
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    async clearAllNotifications() {
        if (!confirm('Are you sure you want to delete all notifications?')) {
            return;
        }

        try {
            const response = await fetch('/ajax/clear-all-notifications/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.loadNotifications(); // Reload to update UI
                this.loadNotificationCount(); // Update badge
                this.refreshTabCounts(); // Update tab counts with real-time data
            }
        } catch (error) {
            console.error('Error clearing all notifications:', error);
        }
    }

    async handleNotificationAction(notificationId, action) {
        try {
            const response = await fetch('/ajax/handle-notification-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `notification_id=${notificationId}&action=${action}`
            });
            
            const data = await response.json();
            if (data.success) {
                this.removeNotificationFromDOM(notificationId);
                this.loadNotificationCount(); // Update badge
            } else {
                console.error('Error handling notification action:', data.message);
            }
        } catch (error) {
            console.error('Error handling notification action:', error);
        }
    }

    updateNotificationReadState(notificationId) {
        const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            notificationElement.classList.remove('unread');
            const unreadIndicator = notificationElement.querySelector('.notification-unread-indicator');
            if (unreadIndicator) {
                unreadIndicator.remove();
            }
            const markReadBtn = notificationElement.querySelector('.mark-read-btn');
            if (markReadBtn) {
                markReadBtn.remove();
            }
        }
    }

    removeNotificationFromDOM(notificationId) {
        const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (notificationElement) {
            notificationElement.remove();
        }
    }

    updateLoadMoreButton(hasNext) {
        const loadMoreContainer = document.getElementById('load-more-container');
        if (loadMoreContainer) {
            loadMoreContainer.style.display = hasNext ? 'block' : 'none';
        }
    }

    showLoading() {
        const loading = document.getElementById('notifications-loading');
        const empty = document.getElementById('notifications-empty');
        const error = document.getElementById('notifications-error');
        const list = document.getElementById('notifications-list');

        [empty, error, list].forEach(el => {
            if (el) el.style.display = 'none';
        });
        if (loading) loading.style.display = 'flex';
    }

    showError(message) {
        const loading = document.getElementById('notifications-loading');
        const empty = document.getElementById('notifications-empty');
        const error = document.getElementById('notifications-error');
        const list = document.getElementById('notifications-list');

        [loading, empty, list].forEach(el => {
            if (el) el.style.display = 'none';
        });
        if (error) {
            error.style.display = 'flex';
            const errorMessage = error.querySelector('p');
            if (errorMessage) {
                errorMessage.textContent = message;
            }
        }
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        }
    }

    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }
        
        // Fallback: try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        return '';
    }

    setupPeriodicRefresh() {
        // Refresh notification count and tab counts every 30 seconds
        setInterval(() => {
            this.loadNotificationCount();
            if (this.isOpen) {
                this.refreshTabCounts();
            }
        }, 30000);
    }
}

// Initialize notifications manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationsManager = new NotificationsManager();
});
