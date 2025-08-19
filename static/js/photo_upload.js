/**
 * Photo Upload JavaScript
 * Handles drag & drop, file validation, and upload progress
 */

class PhotoUploader {
    constructor() {
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.uploadBtn = document.getElementById('upload-btn');
        this.uploadForm = document.getElementById('upload-form');
        this.uploadProgress = document.getElementById('upload-progress');
        this.uploadResults = document.getElementById('upload-results');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.uploadList = document.getElementById('upload-list');
        this.resultsList = document.getElementById('results-list');
        
        this.selectedFiles = [];
        this.uploadQueue = [];
        this.currentUpload = 0;
        this.totalUploads = 0;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupDragAndDrop();
    }
    
    bindEvents() {
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
        
        // Upload area click
        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // Browse files button click
        const browseBtn = document.getElementById('browse-files-btn');
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent triggering upload area click
                this.fileInput.click();
            });
        }
        
        // Form submission
        this.uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.startUpload();
        });
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
    }
    
    setupDragAndDrop() {
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.remove('dragover');
            }, false);
        });
        
        // Handle dropped files
        this.uploadArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFileSelection(files);
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        // Convert FileList to Array and validate
        const fileArray = Array.from(files);
        const validFiles = this.validateFiles(fileArray);
        
        if (validFiles.length === 0) {
            this.showError('No valid files selected. Please check file types and sizes.');
            return;
        }
        
        this.selectedFiles = validFiles;
        this.updateUploadButton();
        this.showFilePreview();
    }
    
    validateFiles(files) {
        const validFiles = [];
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedExtensions = [
            'jpg', 'jpeg', 'png', 'tiff', 'tif',
            'raw', 'cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'pef',
            'srw', 'x3f', 'rw2', 'mrw', 'crw', 'kdc', 'dcr', 'mos',
            'mef', 'nrw', 'cr3'
        ];
        
        files.forEach(file => {
            // Check file size
            if (file.size > maxSize) {
                this.showError(`File "${file.name}" is too large. Maximum size is 100MB.`);
                return;
            }
            
            // Check file extension
            const extension = file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(extension)) {
                this.showError(`File "${file.name}" has an unsupported format.`);
                return;
            }
            
            validFiles.push(file);
        });
        
        return validFiles;
    }
    
    updateUploadButton() {
        if (this.selectedFiles.length > 0) {
            this.uploadBtn.disabled = false;
            this.uploadBtn.innerHTML = `<i class="fas fa-upload"></i> Upload ${this.selectedFiles.length} Photo${this.selectedFiles.length > 1 ? 's' : ''}`;
        } else {
            this.uploadBtn.disabled = true;
            this.uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photos';
        }
    }
    
    showFilePreview() {
        // Clear previous preview
        this.uploadList.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            this.uploadList.appendChild(fileItem);
        });
    }
    
    createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'upload-item';
        item.innerHTML = `
            <div class="upload-item-icon processing">
                <i class="fas fa-spinner"></i>
            </div>
            <div class="upload-item-info">
                <div class="upload-item-name">${file.name}</div>
                <div class="upload-item-size">${this.formatFileSize(file.size)}</div>
            </div>
            <div class="upload-item-status processing">Processing...</div>
        `;
        return item;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    startUpload() {
        if (this.selectedFiles.length === 0) return;
        
        this.uploadQueue = [...this.selectedFiles];
        this.totalUploads = this.uploadQueue.length;
        this.currentUpload = 0;
        
        this.showUploadProgress();
        this.uploadNext();
    }
    
    showUploadProgress() {
        this.uploadProgress.style.display = 'block';
        this.updateProgress();
    }
    
    updateProgress() {
        const percentage = (this.currentUpload / this.totalUploads) * 100;
        this.progressFill.style.width = percentage + '%';
        this.progressText.textContent = `${this.currentUpload} of ${this.totalUploads} completed`;
    }
    
    uploadNext() {
        if (this.uploadQueue.length === 0) {
            this.uploadComplete();
            return;
        }
        
        const file = this.uploadQueue.shift();
        this.uploadFile(file);
    }
    
    uploadFile(file) {
        const formData = new FormData();
        formData.append('photos', file);
        
        // Add form fields
        const title = document.querySelector('input[name="title"]').value;
        const description = document.querySelector('textarea[name="description"]').value;
        const tags = document.querySelector('input[name="tags"]').value;
        const isPublic = document.querySelector('input[name="is_public"]').checked;
        
        if (title) formData.append('title', title);
        if (description) formData.append('description', description);
        if (tags) formData.append('tags', tags);
        formData.append('is_public', isPublic);
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        // Update file item status
        this.updateFileStatus(file.name, 'processing', 'Uploading...');
        
        // Send upload request
        fetch('/photos/upload/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.updateFileStatus(file.name, 'success', 'Uploaded');
                this.currentUpload++;
                this.updateProgress();
            } else {
                this.updateFileStatus(file.name, 'error', 'Failed');
                console.error('Upload failed:', data.error);
            }
        })
        .catch(error => {
            this.updateFileStatus(file.name, 'error', 'Error');
            console.error('Upload error:', error);
        })
        .finally(() => {
            this.uploadNext();
        });
    }
    
    updateFileStatus(fileName, status, text) {
        const fileItems = this.uploadList.querySelectorAll('.upload-item');
        fileItems.forEach(item => {
            const nameElement = item.querySelector('.upload-item-name');
            if (nameElement.textContent === fileName) {
                const icon = item.querySelector('.upload-item-icon');
                const statusElement = item.querySelector('.upload-item-status');
                
                // Update icon
                icon.className = `upload-item-icon ${status}`;
                if (status === 'success') {
                    icon.innerHTML = '<i class="fas fa-check"></i>';
                } else if (status === 'error') {
                    icon.innerHTML = '<i class="fas fa-times"></i>';
                }
                
                // Update status text
                statusElement.className = `upload-item-status ${status}`;
                statusElement.textContent = text;
            }
        });
    }
    
    uploadComplete() {
        this.showUploadResults();
        this.resetForm();
    }
    
    showUploadResults() {
        this.uploadProgress.style.display = 'none';
        this.uploadResults.style.display = 'block';
        
        // Show results summary
        const successCount = this.uploadList.querySelectorAll('.upload-item-icon.success').length;
        const errorCount = this.uploadList.querySelectorAll('.upload-item-icon.error').length;
        
        this.resultsList.innerHTML = `
            <div class="result-item">
                <div class="result-item-icon">
                    <i class="fas fa-check"></i>
                </div>
                <div class="result-item-info">
                    <div class="result-item-name">Upload Complete</div>
                    <div class="result-item-details">
                        ${successCount} photos uploaded successfully
                        ${errorCount > 0 ? `, ${errorCount} failed` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    resetForm() {
        this.selectedFiles = [];
        this.uploadQueue = [];
        this.currentUpload = 0;
        this.totalUploads = 0;
        
        this.updateUploadButton();
        this.uploadForm.reset();
        this.uploadList.innerHTML = '';
    }
    
    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-danger alert-dismissible fade show';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of form
        this.uploadForm.insertBefore(notification, this.uploadForm.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    showSuccess(message) {
        // Create success notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of form
        this.uploadForm.insertBefore(notification, this.uploadForm.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize uploader when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PhotoUploader();
});

// File type detection helpers
function isImageFile(file) {
    return file.type.startsWith('image/');
}

function isRawFile(file) {
    const rawExtensions = ['raw', 'cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'pef', 'srw', 'x3f', 'rw2', 'mrw', 'crw', 'kdc', 'dcr', 'mos', 'mef', 'nrw', 'cr3'];
    const extension = file.name.split('.').pop().toLowerCase();
    return rawExtensions.includes(extension);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
