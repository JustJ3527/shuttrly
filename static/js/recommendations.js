/**
 * User Recommendations System
 * 
 * Handles user recommendation display, refresh, and follow actions
 * with AJAX integration and real-time updates.
 */

class RecommendationsManager {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.autoRefreshInterval = null;
        this.init();
    }

    /**
     * Initialize the recommendations system
     */
    init() {
        this.setupAutoRefresh();
        this.bindEvents();
    }

    /**
     * Get CSRF token from the page
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!token) {
            console.error('❌ CSRF token not found!');
            return null;
        }
        return token.value;
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Refresh button events are handled by onclick in HTML
        // Follow button events are handled by onclick in HTML
    }

    /**
     * Refresh recommendations
     */
    async refreshRecommendations() {
        const loadingEl = document.getElementById('recommendations-loading');
        const listEl = document.getElementById('recommendations-list');
        const emptyEl = document.getElementById('recommendations-empty');
        
        // Show loading state
        this.showLoadingState(loadingEl, listEl, emptyEl);
        
        try {
            const response = await fetch('/ajax/refresh-recommendations/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.updateRecommendationsHTML(data.recommendations_html);
                this.showToast('Success', data.message || 'Recommendations updated successfully!', 'success');
            } else {
                throw new Error(data.message || 'Failed to refresh recommendations');
            }
        } catch (error) {
            console.error('❌ Error refreshing recommendations:', error);
            this.showToast('Error', `Failed to refresh recommendations: ${error.message}`, 'error');
        } finally {
            this.hideLoadingState(loadingEl);
        }
    }

    /**
     * Update recommendations HTML with server-rendered content
     */
    updateRecommendationsHTML(html) {
        const containerEl = document.querySelector('.recommendations-section');
        
        if (!containerEl) return;
        
        // Find the recommendations content area (between header and footer)
        const headerEl = containerEl.querySelector('.recommendations-header');
        const footerEl = containerEl.querySelector('.recommendations-footer');
        
        // Remove existing content between header and footer
        const existingContent = containerEl.querySelectorAll('.recommendations-list, .recommendations-empty, .recommendations-loading');
        existingContent.forEach(el => el.remove());
        
        // Insert the new HTML after the header
        if (headerEl && footerEl) {
            headerEl.insertAdjacentHTML('afterend', html);
        } else {
            // Fallback: replace the entire content
            containerEl.innerHTML = `
                <div class="recommendations-header">
                    <h5 class="recommendations-title">Suggested Users</h5>
                    <button class="refresh-btn" onclick="refreshRecommendations()" title="Refresh recommendations">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
                ${html}
                <div class="recommendations-footer">
                    <small>
                        <i class="fas fa-info-circle"></i> 
                        Based on your interests and connections
                    </small>
                </div>
            `;
        }
    }


    /**
     * Follow a user
     */
    async followUser(userId, username) {
        const button = document.querySelector(`[data-user-id="${userId}"] .follow-btn`);
        if (!button) return;
        
        // Disable button and show loading
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Following...';
        
        try {
            const response = await fetch('/ajax/toggle-follow/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(username)}`
            });

            const data = await response.json();
            
            if (data.success) {
                // Update button to show following state
                button.innerHTML = '<i class="fas fa-check"></i> Following';
                button.disabled = true;
                
                // Refresh recommendations after follow
                await this.refreshRecommendationsAfterFollow();
                
                // Show success message after updating the UI
                setTimeout(() => {
                    this.showToast('Success', data.message || 'Successfully followed user!', 'success');
                }, 100);
            } else {
                throw new Error(data.message || 'Failed to follow user');
            }
        } catch (error) {
            console.error('Error following user:', error);
            button.disabled = false;
            button.innerHTML = originalText;
            this.showToast('Error', 'Failed to follow user', 'error');
        }
    }

    /**
     * Refresh recommendations after follow action
     */
    async refreshRecommendationsAfterFollow() {
        try {
            const response = await fetch('/ajax/get-recommendations/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                },
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateRecommendationsList(data.recommendations);
            }
        } catch (error) {
            console.error('Error refreshing recommendations after follow:', error);
        }
    }

    /**
     * Setup auto-refresh for recommendations
     */
    setupAutoRefresh() {
        // Only auto-refresh on home page
        if (window.location.pathname === '/' || window.location.pathname.includes('home')) {
            this.autoRefreshInterval = setInterval(() => {
                // Only refresh if user is still on the page and no loading is happening
                if (document.visibilityState === 'visible' && 
                    !document.getElementById('recommendations-loading')?.style.display === 'block') {
                    this.silentRefresh();
                }
            }, 300000); // 5 minutes
        }
    }

    /**
     * Silent refresh without showing loading state
     */
    async silentRefresh() {
        try {
            const response = await fetch('/ajax/get-recommendations/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                },
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateRecommendationsList(data.recommendations);
                console.log('Recommendations refreshed silently');
            }
        } catch (error) {
            console.error('Error in auto-refresh:', error);
        }
    }

    /**
     * Show loading state
     */
    showLoadingState(loadingEl, listEl, emptyEl) {
        if (loadingEl) loadingEl.style.display = 'block';
        if (listEl) listEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'none';
    }

    /**
     * Hide loading state
     */
    hideLoadingState(loadingEl) {
        if (loadingEl) loadingEl.style.display = 'none';
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        if (typeof window.showToast === 'function') {
            window.showToast(title, message, type);
        } else {
            console.log(`${title}: ${message}`);
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Cleanup resources
     */
    destroy() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// Initialize recommendations manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.recommendationsManager) {
        window.recommendationsManager = new RecommendationsManager();
    }
});

// Global functions for backward compatibility
function refreshRecommendations() {
    if (!window.recommendationsManager) {
        window.recommendationsManager = new RecommendationsManager();
    }
    window.recommendationsManager.refreshRecommendations();
}

function followUser(userId, username) {
    if (!window.recommendationsManager) {
        window.recommendationsManager = new RecommendationsManager();
    }
    window.recommendationsManager.followUser(userId, username);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.recommendationsManager) {
        window.recommendationsManager.destroy();
    }
});
