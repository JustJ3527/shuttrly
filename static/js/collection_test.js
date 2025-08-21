/**
 * Simple test script for photo selection functionality
 * Add this to the collection_add_photos.html template temporarily for debugging
 */

function testPhotoSelection() {
    console.log('=== Testing Photo Selection ===');
    
    // Check if elements exist
    const photoGrid = document.getElementById('photo-grid');
    const selectedCount = document.getElementById('selected-count');
    const photoIdsInput = document.getElementById('photo-ids-input');
    const addPhotosBtn = document.getElementById('add-photos-btn');
    
    console.log('Photo grid:', photoGrid);
    console.log('Selected count:', selectedCount);
    console.log('Photo IDs input:', photoIdsInput);
    console.log('Add photos button:', addPhotosBtn);
    
    // Check photo items
    const photoItems = document.querySelectorAll('.photo-selection-item');
    console.log('Photo items found:', photoItems.length);
    
    photoItems.forEach((item, index) => {
        const checkbox = item.querySelector('.photo-checkbox');
        const photoId = item.getAttribute('data-photo-id');
        const title = item.getAttribute('data-title');
        const tags = item.getAttribute('data-tags');
        
        console.log(`Photo ${index + 1}:`, {
            id: photoId,
            title: title,
            tags: tags,
            hasCheckbox: !!checkbox,
            checkboxValue: checkbox ? checkbox.value : 'N/A'
        });
    });
    
    // Test selection
    if (photoItems.length > 0) {
        const firstCheckbox = photoItems[0].querySelector('.photo-checkbox');
        if (firstCheckbox) {
            console.log('Testing selection of first photo...');
            firstCheckbox.checked = true;
            firstCheckbox.dispatchEvent(new Event('change'));
        }
    }
}

// Run test when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other scripts to initialize
    setTimeout(testPhotoSelection, 1000);
    
    // Also add a test button
    const testButton = document.createElement('button');
    testButton.textContent = 'Test Selection';
    testButton.className = 'btn btn-warning btn-sm';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.onclick = testPhotoSelection;
    document.body.appendChild(testButton);
});
