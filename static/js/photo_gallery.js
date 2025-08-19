/**
 * VSCO-Style Photo Gallery JavaScript
 * Handles responsive masonry grid and interactive features
 */

class PhotoGallery {
    constructor() {
        this.grid = document.getElementById('masonry-grid');
        this.photoItems = document.querySelectorAll('.photo-item');
        this.currentPhotoId = null;
        this.resizeTimeout = null;
        
        this.init();
    }
    
    init() {
        this.setupMasonryGrid();
        this.setupEventListeners();
        this.setupDeleteHandlers();
        this.animatePhotos();
    }
    
    setupMasonryGrid() {
        if (!this.grid) return;
        
        // Initial layout
        this.layoutMasonry();
        
        // Handle window resize
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.layoutMasonry();
            }, 250);
        });
    }
    
    layoutMasonry() {
        if (!this.grid) return;
        
        const containerWidth = this.grid.offsetWidth;
        let columnCount = 1;
        
        // Determine column count based on screen width
        if (containerWidth >= 1400) columnCount = 5;
        else if (containerWidth >= 1200) columnCount = 4;
        else if (containerWidth >= 992) columnCount = 3;
        else if (containerWidth >= 768) columnCount = 3;
        else if (containerWidth >= 576) columnCount = 2;
        else columnCount = 2;
        
        // Update CSS custom property for column count
        this.grid.style.setProperty('--column-count', columnCount);
        
        // Force reflow
        this.grid.style.columnCount = columnCount;
        
        // Add animation class to trigger reflow
        this.grid.classList.add('layout-updating');
        setTimeout(() => {
            this.grid.classList.remove('layout-updating');
        }, 100);
    }
    
    setupEventListeners() {
        // Photo item click events
        this.photoItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons or links
                if (e.target.closest('.photo-actions') || e.target.closest('a')) {
                    return;
                }
                
                // Open photo detail
                const photoId = item.dataset.photoId;
                if (photoId) {
                    window.location.href = `/photos/photo/${photoId}/`;
                }
            });
        });
    }
    
    handleKeyboardNavigation(e) {
        const focusedItem = document.querySelector('.photo-item:focus-within');
        if (!focusedItem) return;
        
        const currentIndex = Array.from(this.photoItems).indexOf(focusedItem);
        let nextIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowRight':
                nextIndex = Math.min(currentIndex + 1, this.photoItems.length - 1);
                break;
            case 'ArrowLeft':
                nextIndex = Math.max(currentIndex - 1, 0);
                break;
            case 'ArrowDown':
                // Move down by column count
                const columnCount = parseInt(this.grid.style.getPropertyValue('--column-count')) || 4;
                nextIndex = Math.min(currentIndex + columnCount, this.photoItems.length - 1);
                break;
            case 'ArrowUp':
                // Move up by column count
                const colCount = parseInt(this.grid.style.getPropertyValue('--column-count')) || 4;
                nextIndex = Math.max(currentIndex - colCount, 0);
                break;
            case 'Enter':
            case ' ':
                // Open photo detail
                const photoId = focusedItem.dataset.photoId;
                if (photoId) {
                    window.location.href = `/photos/photo/${photoId}/`;
                }
                e.preventDefault();
                return;
            default:
                return;
        }
        
        if (nextIndex !== currentIndex) {
            this.photoItems[nextIndex].focus();
            this.scrollToPhoto(this.photoItems[nextIndex]);
        }
    }
    
    scrollToPhoto(photoItem) {
        const rect = photoItem.getBoundingClientRect();
        const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;
        
        if (!isVisible) {
            photoItem.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }
    
    setupDeleteHandlers() {
        // Delete photo buttons
        document.querySelectorAll('.delete-photo').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const photoId = btn.dataset.photoId;
                if (photoId) {
                    this.showDeleteModal(photoId);
                }
            });
        });
        
        // Delete confirmation
        const confirmDeleteBtn = document.getElementById('confirmDelete');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                this.deletePhoto();
            });
        }
    }
    
    showDeleteModal(photoId) {
        this.currentPhotoId = photoId;
        const modal = new bootstrap.Modal(document.getElementById('deletePhotoModal'));
        modal.show();
    }
    
    async deletePhoto() {
        if (!this.currentPhotoId) return;
        
        try {
            const response = await fetch(`/photos/photo/${this.currentPhotoId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Remove photo from DOM
                const photoItem = document.querySelector(`[data-photo-id="${this.currentPhotoId}"]`);
                if (photoItem) {
                    photoItem.classList.add('deleting');
                    setTimeout(() => {
                        photoItem.remove();
                        this.layoutMasonry();
                    }, 300);
                }
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deletePhotoModal'));
                modal.hide();
                
                // Show success message
                this.showNotification('Photo deleted successfully', 'success');
                
            } else {
                throw new Error('Failed to delete photo');
            }
            
        } catch (error) {
            console.error('Error deleting photo:', error);
            this.showNotification('Error deleting photo', 'error');
        }
        
        this.currentPhotoId = null;
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Hide and remove
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
    
    animatePhotos() {
        // Intersection Observer for lazy loading and animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const photoItem = entry.target;
                    
                    // Add fade-in animation
                    photoItem.classList.add('fade-in');
                    
                    // Load image if not loaded
                    const img = photoItem.querySelector('.photo-image');
                    if (img && !img.complete) {
                        img.addEventListener('load', () => {
                            photoItem.classList.add('loaded');
                        });
                    } else {
                        photoItem.classList.add('loaded');
                    }
                    
                    // Stop observing
                    observer.unobserve(photoItem);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });
        
        // Observe all photo items
        this.photoItems.forEach(item => {
            observer.observe(item);
        });
    }
}

// Initialize gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.photoGallery = new PhotoGallery();
    
    // Add CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
            padding: 1rem 1.5rem;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 9999;
            max-width: 300px;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .notification-success {
            border-left: 4px solid #28a745;
        }
        
        .notification-success i {
            color: #28a745;
        }
        
        .notification-error {
            border-left: 4px solid #dc3545;
        }
        
        .notification-error i {
            color: #dc3545;
        }
        
        .photo-item.deleting {
            opacity: 0;
            transform: scale(0.8);
            transition: all 0.3s ease;
        }
        
        .masonry-grid.layout-updating {
            opacity: 0.8;
            transition: opacity 0.1s ease;
        }
    `;
    document.head.appendChild(style);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoGallery;
}
