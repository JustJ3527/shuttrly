/**
 * Simple Photo Upload JavaScript
 * Handles basic photo upload functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('id_photos');
    const submitBtn = document.getElementById('upload-submit-btn');
    const progressDiv = document.getElementById('upload-progress');
    const resultsDiv = document.getElementById('upload-results');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultsList = document.getElementById('results-list');

    // Show selected files info
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            console.log(`Selected ${files.length} file(s)`);
            
            // Enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fas fa-upload"></i> Upload ${files.length} Photo(s)`;
            
            // Show file info
            let fileInfo = '<div class="alert alert-info"><strong>Selected files:</strong><ul class="mt-2 mb-0">';
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                fileInfo += `<li>${file.name} (${sizeMB} MB)</li>`;
            }
            fileInfo += '</ul></div>';
            
            // Insert file info after file input
            const fileInfoDiv = document.createElement('div');
            fileInfoDiv.id = 'file-info';
            fileInfoDiv.innerHTML = fileInfo;
            
            // Remove existing file info if any
            const existingInfo = document.getElementById('file-info');
            if (existingInfo) {
                existingInfo.remove();
            }
            
            // Insert new file info
            fileInput.parentNode.insertAdjacentElement('afterend', fileInfoDiv);
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photos';
            
            // Remove file info
            const existingInfo = document.getElementById('file-info');
            if (existingInfo) {
                existingInfo.remove();
            }
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const files = fileInput.files;
        if (files.length === 0) {
            alert('Please select at least one photo to upload.');
            return;
        }

        // Show progress
        progressDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

        // Create FormData
        const formData = new FormData(uploadForm);
        
        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress > 90) progress = 90;
            
            progressBar.style.width = progress + '%';
            progressText.textContent = Math.round(progress) + '%';
        }, 200);

        // Submit form
        fetch(uploadForm.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            
            if (response.ok) {
                return response.text();
            } else {
                throw new Error('Upload failed');
            }
        })
        .then(data => {
            // Hide progress
            progressDiv.style.display = 'none';
            
            // Show results
            resultsList.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle"></i> Upload Successful!</h6>
                    <p>${files.length} photo(s) uploaded successfully.</p>
                    <p>You will be redirected to your gallery in a few seconds...</p>
                </div>
            `;
            resultsDiv.style.display = 'block';
            
            // Reset form
            uploadForm.reset();
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photos';
            
            // Remove file info
            const existingInfo = document.getElementById('file-info');
            if (existingInfo) {
                existingInfo.remove();
            }
            
            // Redirect to gallery after 3 seconds
            setTimeout(() => {
                window.location.href = '/photos/gallery/';
            }, 3000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            console.error('Upload error:', error);
            
            // Hide progress
            progressDiv.style.display = 'none';
            
            // Show error
            resultsList.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle"></i> Upload Failed</h6>
                    <p>An error occurred during upload. Please try again.</p>
                    <p>Error: ${error.message}</p>
                </div>
            `;
            resultsDiv.style.display = 'block';
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photos';
        });
    });

    // File validation
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/tif',
            'image/raw', 'image/cr2', 'image/nef', 'image/arw', 'image/dng', 'image/cr3'
        ];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Check file size
            if (file.size > maxSize) {
                alert(`File "${file.name}" is too large. Maximum size is 100MB.`);
                fileInput.value = '';
                return;
            }
            
            // Check file type (basic check)
            const extension = file.name.split('.').pop().toLowerCase();
            const allowedExtensions = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'pef', 'srw', 'x3f', 'rw2', 'mrw', 'crw', 'kdc', 'dcr', 'mos', 'mef', 'nrw', 'cr3'];
            
            if (!allowedExtensions.includes(extension)) {
                alert(`File "${file.name}" has an unsupported format.`);
                fileInput.value = '';
                return;
            }
        }
    });

    // Drag and drop support
    const uploadContainer = document.querySelector('.upload-container');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadContainer.addEventListener(eventName, unhighlight, false);
    });

    uploadContainer.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        uploadContainer.classList.add('drag-over');
    }

    function unhighlight(e) {
        uploadContainer.classList.remove('drag-over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        fileInput.files = files;
        fileInput.dispatchEvent(new Event('change'));
    }
});
