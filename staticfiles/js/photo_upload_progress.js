/**
 * Photo Upload Progress Handler
 * Manages upload progress bar and batch processing feedback
 */

class PhotoUploadProgress {
    constructor() {
        this.progressInterval = null;
        this.isUploading = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkExistingProgress();
        this.updateJSStatus();
    }

    updateJSStatus() {
        const jsStatus = document.getElementById('js-status');
        if (jsStatus) {
            jsStatus.textContent = 'JS Ready';
            jsStatus.className = 'ms-3 badge bg-success';
        }
    }

    bindEvents() {
        const form = document.getElementById('upload-form');
        const fileInput = document.getElementById('id_photos');
        
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        }
    }

    handleFileSelection(event) {
        const files = event.target.files;
        const submitBtn = document.getElementById('upload-submit-btn');
        
        if (files.length > 0) {
            // Show warning for large file counts
            if (files.length > 30) {
                this.showWarning(`You've selected ${files.length} files. For optimal performance, consider uploading in smaller batches of 15-20 files.`);
            } else if (files.length > 15) {
                this.showInfo(`You've selected ${files.length} files. Processing will be done in batches of 15 for optimal performance.`);
            }
            
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        
        if (this.isUploading) {
            return; // Prevent multiple submissions
        }

        const form = event.target;
        const formData = new FormData(form);
        const files = document.getElementById('id_photos').files;

        if (files.length === 0) {
            this.showError('Please select at least one photo to upload.');
            return;
        }

        // Start upload process
        this.isUploading = true;
        this.showProgressSection();
        this.startProgressTracking();
        
        // Disable form during upload
        this.setFormState(false);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.redirected) {
                // Upload completed, redirect to gallery
                this.stopProgressTracking();
                this.hideProgressSection();
                window.location.href = response.url;
            } else if (response.ok) {
                const result = await response.json();
                this.handleUploadResult(result);
            } else {
                throw new Error(`Upload failed: ${response.status}`);
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.showError(`Upload failed: ${error.message}`);
            this.stopProgressTracking();
            this.hideProgressSection();
            this.setFormState(true);
        }

        this.isUploading = false;
    }

    showProgressSection() {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) {
            progressSection.style.display = 'block';
            progressSection.scrollIntoView({ behavior: 'smooth' });
            console.log('Progress section shown');
        } else {
            console.error('Progress section element not found');
        }
    }

    hideProgressSection() {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) {
            // Only hide if we have progress data and it's completed
            const hasProgressData = this.hasProgressData();
            if (hasProgressData) {
                progressSection.style.display = 'none';
                console.log('Progress section hidden');
            } else {
                console.log('Progress section kept visible - no data yet');
            }
        }
    }

    hasProgressData() {
        // Check if we have any meaningful progress data
        const totalFiles = document.getElementById('total-files');
        const processedFiles = document.getElementById('processed-files');
        
        if (totalFiles && processedFiles) {
            const total = parseInt(totalFiles.textContent) || 0;
            const processed = parseInt(processedFiles.textContent) || 0;
            return total > 0 && processed > 0;
        }
        return false;
    }

    startProgressTracking() {
        console.log('Starting progress tracking...');
        
        // Clear any existing progress
        this.clearProgress();
        
        // Ensure progress section stays visible
        this.showProgressSection();
        
        // Small delay to ensure the section is visible before starting updates
        setTimeout(() => {
            // Start polling for progress updates
            this.progressInterval = setInterval(() => {
                this.updateProgress();
            }, 1000); // Update every second
            
            console.log('Progress tracking interval started');
        }, 500);
    }

    stopProgressTracking() {
        console.log('Stopping progress tracking...');
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    async updateProgress() {
        try {
            const response = await fetch('/photos/upload-progress/');
            const progress = await response.json();
            
            console.log('Progress update received:', progress);
            
            // Only stop tracking if we have a definitive status
            if (progress.status === 'completed' || progress.status === 'failed') {
                console.log('Upload finished with status:', progress.status);
                this.stopProgressTracking();
                this.updateProgressDisplay(progress);
                
                if (progress.status === 'completed') {
                    // Keep progress visible for 5 seconds to show completion
                    setTimeout(() => {
                        this.hideProgressSection();
                    }, 5000);
                }
                // If failed, keep progress visible to show error
            } else if (progress.status === 'processing' || progress.total > 0) {
                // Still processing, update display
                this.updateProgressDisplay(progress);
            } else {
                // No progress data yet, this is normal at the start
                console.log('No progress data yet, continuing to poll...');
            }
        } catch (error) {
            console.error('Error fetching progress:', error);
            // Don't stop tracking on network errors, continue polling
        }
    }

    updateProgressDisplay(progress) {
        const progressBar = document.getElementById('upload-progress-bar');
        const totalFiles = document.getElementById('total-files');
        const processedFiles = document.getElementById('processed-files');
        const uploadedFiles = document.getElementById('uploaded-files');
        const currentBatch = document.getElementById('current-batch');

        console.log('Updating progress display:', progress);

        if (progress.total > 0) {
            const percentage = Math.round((progress.processed / progress.total) * 100);
            
            if (progressBar) {
                progressBar.style.width = `${percentage}%`;
                progressBar.textContent = `${percentage}%`;
            }

            if (totalFiles) totalFiles.textContent = progress.total;
            if (processedFiles) processedFiles.textContent = progress.processed;
            if (uploadedFiles) uploadedFiles.textContent = progress.uploaded;
            if (currentBatch) currentBatch.textContent = progress.current_batch;

            // Update progress bar color based on status
            if (progress.status === 'failed') {
                progressBar.classList.remove('bg-primary');
                progressBar.classList.add('bg-danger');
            } else if (progress.status === 'completed') {
                progressBar.classList.remove('bg-primary');
                progressBar.classList.add('bg-success');
            } else {
                // Processing or no status, keep primary color
                progressBar.classList.remove('bg-danger', 'bg-success');
                progressBar.classList.add('bg-primary');
            }
        } else {
            // No progress data yet, show initial state
            if (progressBar) {
                progressBar.style.width = '0%';
                progressBar.textContent = 'Starting...';
            }
            if (totalFiles) totalFiles.textContent = '0';
            if (processedFiles) processedFiles.textContent = '0';
            if (uploadedFiles) uploadedFiles.textContent = '0';
            if (currentBatch) currentBatch.textContent = '0';
        }
    }

    clearProgress() {
        const progressBar = document.getElementById('upload-progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressBar.classList.remove('bg-danger', 'bg-success');
            progressBar.classList.add('bg-primary');
        }

        document.getElementById('total-files').textContent = '0';
        document.getElementById('processed-files').textContent = '0';
        document.getElementById('uploaded-files').textContent = '0';
        document.getElementById('current-batch').textContent = '0';
    }

    setFormState(enabled) {
        const form = document.getElementById('upload-form');
        const submitBtn = document.getElementById('upload-submit-btn');
        
        if (form) {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.disabled = !enabled;
            });
        }
        
        if (submitBtn) {
            submitBtn.disabled = !enabled;
            if (enabled) {
                submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photos';
            } else {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            }
        }
    }

    handleUploadResult(result) {
        // Handle any specific upload results if needed
        console.log('Upload result:', result);
    }

    checkExistingProgress() {
        // Check if there's existing progress from a previous session
        fetch('/photos/upload-progress/')
            .then(response => response.json())
            .then(progress => {
                if (progress.status && progress.status !== 'completed') {
                    this.showProgressSection();
                    this.updateProgressDisplay(progress);
                }
            })
            .catch(error => {
                console.log('No existing progress found');
            });
    }

    showWarning(message) {
        this.showMessage(message, 'warning');
    }

    showInfo(message) {
        this.showMessage(message, 'info');
    }

    showError(message) {
        this.showMessage(message, 'danger');
    }

    showMessage(message, type = 'info') {
        // Create a Bootstrap alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert before the form
        const form = document.getElementById('upload-form');
        if (form && form.parentNode) {
            form.parentNode.insertBefore(alertDiv, form);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PhotoUploadProgress();
});

// Debug functions for testing
function testProgressBar() {
    console.log('Testing progress bar...');
    const progressSection = document.getElementById('progress-section');
    const debugStatus = document.getElementById('debug-status');
    
    if (progressSection) {
        progressSection.style.display = 'block';
        debugStatus.textContent = 'Progress bar shown - simulating upload...';
        debugStatus.className = 'ms-3 text-success';
        
        // Simulate realistic progress
        simulateProgress();
        
        console.log('Progress bar test completed');
    } else {
        debugStatus.textContent = 'Progress section not found!';
        debugStatus.className = 'ms-3 text-danger';
        console.error('Progress section element not found');
    }
}

function simulateProgress() {
    // Simulate a realistic upload process
    let currentProgress = 0;
    const totalFiles = 15;
    let currentBatch = 1;
    
    const progressInterval = setInterval(() => {
        currentProgress += Math.random() * 3; // Random progress increment
        
        if (currentProgress >= totalFiles) {
            currentProgress = totalFiles;
            clearInterval(progressInterval);
            
            // Show completion
            document.getElementById('upload-progress-bar').style.width = '100%';
            document.getElementById('upload-progress-bar').textContent = '100%';
            document.getElementById('upload-progress-bar').classList.remove('bg-primary');
            document.getElementById('upload-progress-bar').classList.add('bg-success');
            
            document.getElementById('debug-status').textContent = 'Simulation completed!';
            document.getElementById('debug-status').className = 'ms-3 text-success';
        } else {
            const percentage = Math.round((currentProgress / totalFiles) * 100);
            
            // Update progress bar
            document.getElementById('upload-progress-bar').style.width = percentage + '%';
            document.getElementById('upload-progress-bar').textContent = percentage + '%';
            
            // Update counters
            document.getElementById('total-files').textContent = totalFiles;
            document.getElementById('processed-files').textContent = Math.round(currentProgress);
            document.getElementById('uploaded-files').textContent = Math.round(currentProgress * 0.9); // Some files might fail
            document.getElementById('current-batch').textContent = Math.ceil(currentProgress / 5); // New batch every 5 files
        }
    }, 200); // Update every 200ms for smooth animation
}

function clearProgress() {
    console.log('Clearing progress...');
    const progressSection = document.getElementById('progress-section');
    const debugStatus = document.getElementById('debug-status');
    
    if (progressSection) {
        progressSection.style.display = 'none';
        debugStatus.textContent = 'Progress cleared';
        debugStatus.className = 'ms-3 text-info';
        
        // Reset progress bar
        const progressBar = document.getElementById('upload-progress-bar');
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressBar.classList.remove('bg-danger', 'bg-success');
            progressBar.classList.add('bg-primary');
        }
        
        // Reset counters
        document.getElementById('total-files').textContent = '0';
        document.getElementById('processed-files').textContent = '0';
        document.getElementById('uploaded-files').textContent = '0';
        document.getElementById('current-batch').textContent = '0';
        
        console.log('Progress cleared');
    }
}

// Global error handler for debugging
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    const debugStatus = document.getElementById('debug-status');
    if (debugStatus) {
        debugStatus.textContent = 'JavaScript error: ' + e.error.message;
        debugStatus.className = 'ms-3 text-danger';
    }
});

// Log when the script loads
console.log('PhotoUploadProgress script loaded successfully');
