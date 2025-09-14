/* =============================================== */
/* ==============   USERS JAVASCRIPT   ========== */
/* =============================================== */

/**
 * Users Profile Management
 * Handles profile interactions, follow/unfollow, modals, and tabs
 */

class UsersProfileManager {
    constructor() {
        this.init();
    }

    init() {
        this.initBannerDropdown();
        this.initFollowButtons();
        this.initSocialStatsModal();
        this.initProfileTabs();
        this.initCollectionActions();
    }

    /* ======================= */
    /* =   BANNER DROPDOWN   =  */
    /* ======================= */

    initBannerDropdown() {
        const ellipsisBtn = document.getElementById('btn-ellipsis-banner');
        const dropdownMenu = document.getElementById('banner-dropdown-menu');
        
        if (ellipsisBtn && dropdownMenu) {
            // Toggle dropdown menu
            ellipsisBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdownMenu.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!ellipsisBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                    dropdownMenu.classList.remove('show');
                }
            });
            
            // Handle dropdown item clicks
            const dropdownItems = dropdownMenu.querySelectorAll('.dropdown-item');
            dropdownItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const action = item.getAttribute('data-action');
                    this.handleDropdownAction(action);
                    dropdownMenu.classList.remove('show');
                });
            });
        }
    }

    handleDropdownAction(action) {
        switch(action) {
            case 'block':
                console.log('Block user action');
                // Add block user functionality here
                break;
            case 'message':
                console.log('Send message action');
                // Add send message functionality here
                break;
            case 'report':
                console.log('Report user action');
                // Add report user functionality here
                break;
            case 'share':
                console.log('Share profile action');
                // Add share profile functionality here
                break;
            case 'settings':
                console.log('Banner settings action');
                // Add banner settings functionality here
                break;
        }
    }

    /* ======================= */
    /* =   FOLLOW BUTTONS   =  */
    /* ======================= */

    initFollowButtons() {
        const followBtn = document.getElementById('btn-follow');
        if (followBtn) {
            followBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const userId = followBtn.getAttribute('data-user-id');
                const username = followBtn.getAttribute('data-username');
                
                if (userId && username) {
                    this.toggleFollow(userId, username, followBtn);
                }
            });
        }
    }

    toggleFollow(userId, username, button) {
        const followText = button.querySelector('.follow-text');
        const isFollowing = button.getAttribute('data-is-following') === 'true';
        const isPrivate = button.getAttribute('data-is-private') === 'true';
        const followRequestSent = button.getAttribute('data-follow-request-sent') === 'true';
        
        // Allow canceling follow request if already sent
        if (followRequestSent && !isFollowing) {
            console.log('Canceling follow request');
            // Continue with the request to cancel it
        }
        
        // Show loading state
        button.disabled = true;
        if (isFollowing) {
            followText.textContent = 'Unfollowing...';
        } else if (followRequestSent) {
            followText.textContent = 'Canceling...';
        } else {
            followText.textContent = 'Following...';
        }
        
        // Make API call
        fetch(`/ajax/toggle-follow/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: `username=${encodeURIComponent(username)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update button state
                button.setAttribute('data-is-following', data.is_following ? 'true' : 'false');
                button.setAttribute('data-follow-request-sent', data.follow_request_sent ? 'true' : 'false');
                
                // Update button text based on state
                if (data.follow_request_sent) {
                    followText.textContent = 'Request Sent';
                } else if (data.is_following) {
                    followText.textContent = 'Following';
                } else {
                    followText.textContent = 'Follow';
                }
                
                // Update followers count if available
                if (data.relationship_data && data.relationship_data.followers_count !== undefined) {
                    const followersCount = document.getElementById(`followers-count-${username}`);
                    if (followersCount) {
                        followersCount.textContent = data.relationship_data.followers_count;
                    }
                }
                
                // Show success message if available
                if (data.message) {
                    console.log(data.message);
                }
            } else {
                console.error('Error:', data.message);
                // Revert button state
                followText.textContent = isFollowing ? 'Following' : 'Follow';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revert button state
            followText.textContent = isFollowing ? 'Following' : 'Follow';
        })
        .finally(() => {
            button.disabled = false;
        });
    }

    /* ======================= */
    /* =   SOCIAL STATS MODAL   =  */
    /* ======================= */

    initSocialStatsModal() {
        const clickableStats = document.querySelectorAll('.clickable-stat');
        const modal = document.getElementById('social-stats-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        const modalClose = document.getElementById('modal-close');

        // Handle clickable stats
        clickableStats.forEach(stat => {
            stat.addEventListener('click', () => {
                const type = stat.getAttribute('data-type');
                const username = stat.getAttribute('data-username');
                
                if (type === 'followers' || type === 'following') {
                    this.openSocialStatsModal(type, username, modal, modalTitle, modalBody);
                }
            });
        });

        // Event listeners for modal
        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeModal(modal));
        }
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        }

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.classList.contains('show')) {
                this.closeModal(modal);
            }
        });
    }

    openSocialStatsModal(type, username, modal, modalTitle, modalBody) {
        modal.classList.add('show');
        modalBody.innerHTML = this.getLoadingSpinner();
        
        // Set modal title
        modalTitle.textContent = type === 'followers' ? 'Followers' : 'Following';
        
        // Fetch data
        const url = type === 'followers' 
            ? `/ajax/get-followers/?username=${username}`
            : `/ajax/get-following/?username=${username}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    modalBody.innerHTML = data.html;
                    // Re-bind follow button events for the modal content
                    this.bindModalFollowButtons(modalBody);
                } else {
                    modalBody.innerHTML = this.getErrorState(data.message);
                }
            })
            .catch(error => {
                modalBody.innerHTML = this.getErrorState('Failed to load data');
            });
    }

    closeModal(modal) {
        modal.classList.remove('show');
    }

    bindModalFollowButtons(modalBody) {
        const followButtons = modalBody.querySelectorAll('.follow-btn');
        followButtons.forEach(button => {
            // Remove any existing event listeners
            button.onclick = null;
            
            // Add new event listener
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const userId = button.getAttribute('data-user-id');
                const username = button.getAttribute('data-username');
                
                if (userId && username) {
                    // Use the same follow function as the sidebar
                    if (window.recommendationsManager) {
                        window.recommendationsManager.followUser(userId, username);
                    } else {
                        console.error('RecommendationsManager not available');
                    }
                }
            });
        });
    }

    /* ======================= */
    /* =   PROFILE TABS   =  */
    /* ======================= */

    initProfileTabs() {
        const tabs = document.querySelectorAll('.profile-tab');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                
                // Remove active class from all tabs and panes
                tabs.forEach(t => t.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding pane
                tab.classList.add('active');
                const targetPane = document.getElementById(`${targetTab}-tab`);
                if (targetPane) {
                    targetPane.classList.add('active');
                }
                
                // Load content if not already loaded
                this.loadTabContent(targetTab);
            });
        });
        
        // Load content for the initially active tab
        const activeTab = document.querySelector('.profile-tab.active');
        if (activeTab) {
            const targetTab = activeTab.getAttribute('data-tab');
            this.loadTabContent(targetTab);
        }
    }

    loadTabContent(tabType) {
        const tabPane = document.getElementById(`${tabType}-tab`);
        const username = this.getCurrentUsername();
        
        console.log(`DEBUG: Loading ${tabType} tab, username: ${username}`);
        
        if (!tabPane || !username) {
            console.log(`DEBUG: Missing tabPane or username. tabPane: ${!!tabPane}, username: ${username}`);
            return;
        }
        
        // Check if content is already loaded
        if (tabPane.querySelector('.profile-posts-grid, .profile-collections-grid')) {
            return;
        }
        
        // Show loading state
        tabPane.innerHTML = this.getTabLoadingState(tabType);
        
        // Determine the correct URL
        const url = tabType === 'posts' 
            ? `/ajax/get-profile-posts/?username=${username}`
            : `/ajax/get-profile-collections/?username=${username}`;
        
        // Fetch content
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    tabPane.innerHTML = data.html;
                } else {
                    tabPane.innerHTML = this.getTabErrorState(tabType, data.message);
                }
            })
            .catch(error => {
                console.error(`Error loading ${tabType}:`, error);
                tabPane.innerHTML = this.getTabErrorState(tabType, 'Failed to load');
            });
    }

    /* ======================= */
    /* =   COLLECTION ACTIONS   =  */
    /* ======================= */

    initCollectionActions() {
        // Load more posts functionality
        const loadMorePostsBtn = document.querySelector('.load-more-posts');
        if (loadMorePostsBtn) {
            loadMorePostsBtn.addEventListener('click', () => {
                this.loadMoreContent('posts', loadMorePostsBtn);
            });
        }

        // Load more collections functionality
        const loadMoreCollectionsBtn = document.querySelector('.load-more-collections');
        if (loadMoreCollectionsBtn) {
            loadMoreCollectionsBtn.addEventListener('click', () => {
                this.loadMoreContent('collections', loadMoreCollectionsBtn);
            });
        }

        // Collection edit buttons
        const editBtns = document.querySelectorAll('.collection-edit-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const collectionId = btn.dataset.collectionId;
                window.location.href = `/collections/${collectionId}/edit/`;
            });
        });

        // Collection delete buttons
        const deleteBtns = document.querySelectorAll('.collection-delete-btn');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const collectionId = btn.dataset.collectionId;
                this.deleteCollection(collectionId, btn);
            });
        });
    }

    loadMoreContent(contentType, button) {
        const currentPage = parseInt(button.dataset.page);
        const username = this.getCurrentUsername();
        
        if (!username) return;
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        button.disabled = true;
        
        // Load more content
        const url = contentType === 'posts' 
            ? `/ajax/get-profile-posts/?username=${username}&page=${currentPage}`
            : `/ajax/get-profile-collections/?username=${username}&page=${currentPage}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Append new content to grid
                    const grid = document.querySelector(`.profile-${contentType}-grid`);
                    if (grid) {
                        grid.insertAdjacentHTML('beforeend', data.html);
                    }
                    
                    // Update page number
                    button.dataset.page = currentPage + 1;
                    
                    // Hide button if no more content
                    if (!data.has_next) {
                        button.style.display = 'none';
                    } else {
                        button.innerHTML = `<i class="fas fa-plus"></i> Load More ${contentType.charAt(0).toUpperCase() + contentType.slice(1)}`;
                        button.disabled = false;
                    }
                } else {
                    console.error(`Error loading more ${contentType}:`, data.message);
                    button.innerHTML = `<i class="fas fa-plus"></i> Load More ${contentType.charAt(0).toUpperCase() + contentType.slice(1)}`;
                    button.disabled = false;
                }
            })
            .catch(error => {
                console.error(`Error loading more ${contentType}:`, error);
                button.innerHTML = `<i class="fas fa-plus"></i> Load More ${contentType.charAt(0).toUpperCase() + contentType.slice(1)}`;
                button.disabled = false;
            });
    }

    deleteCollection(collectionId, button) {
        if (confirm('Are you sure you want to delete this collection? This action cannot be undone.')) {
            // Delete collection via AJAX
            fetch(`/ajax/delete-collection/${collectionId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove collection from grid
                    const collectionItem = document.querySelector(`[data-collection-id="${collectionId}"]`);
                    if (collectionItem) {
                        collectionItem.remove();
                    }
                    
                    // Show success message
                    if (window.showToast) {
                        window.showToast('Success', 'Collection deleted successfully', 'success');
                    }
                } else {
                    console.error('Error deleting collection:', data.message);
                    if (window.showToast) {
                        window.showToast('Error', data.message, 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Error deleting collection:', error);
                if (window.showToast) {
                    window.showToast('Error', 'Failed to delete collection', 'error');
                }
            });
        }
    }

    /* ======================= */
    /* =   UTILITY METHODS   =  */
    /* ======================= */

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    getCurrentUsername() {
        // Try to get username from various sources
        const usernameElement = document.querySelector('[data-username]');
        if (usernameElement) {
            return usernameElement.getAttribute('data-username');
        }
        
        // Fallback: try to extract from URL or other elements
        const url = window.location.pathname;
        // Try both /user/ and /profile/ patterns
        let match = url.match(/\/user\/([^\/]+)/);
        if (!match) {
            match = url.match(/\/profile\/([^\/]+)/);
        }
        return match ? match[1] : null;
    }

    getLoadingSpinner() {
        return `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading...</span>
            </div>
        `;
    }

    getErrorState(message) {
        return `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>Error</h4>
                <p>${message}</p>
            </div>
        `;
    }

    getTabLoadingState(tabType) {
        return `
            <div class="tab-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading ${tabType}...</span>
            </div>
        `;
    }

    getTabErrorState(tabType, message) {
        return `
            <div class="tab-error">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>Error</h4>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.usersProfileManager = new UsersProfileManager();
});
