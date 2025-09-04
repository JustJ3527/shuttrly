/**
 * Debug script for Advanced Gallery
 * Use this to test and debug the gallery functionality
 */

// Debug functions
window.debugAdvancedGallery = {
    
    // Test layout switching
    testLayouts: function() {
        console.log('🧪 Testing layout switching...');
        
        if (window.advancedGallery) {
            // Test grid layout
            console.log('Testing Grid layout...');
            window.advancedGallery.switchLayout('grid');
            
            setTimeout(() => {
                console.log('Testing Masonry layout...');
                window.advancedGallery.switchLayout('masonry');
                
                setTimeout(() => {
                    console.log('Testing Masonry shuffle...');
                    window.advancedGallery.regenerateMasonryLayout();
                    
                    setTimeout(() => {
                        console.log('✅ Layout testing completed');
                    }, 1000);
                }, 1000);
            }, 1000);
        } else {
            console.error('❌ Advanced Gallery not initialized');
        }
    },
    
    // Test masonry functionality
    testMasonry: function() {
        console.log('🧪 Testing masonry functionality...');
        
        if (window.advancedGallery) {
            // Switch to masonry
            window.advancedGallery.switchLayout('masonry');
            
            setTimeout(() => {
                // Test shuffle multiple times
                for (let i = 0; i < 3; i++) {
                    setTimeout(() => {
                        window.advancedGallery.regenerateMasonryLayout();
                        console.log(`Masonry shuffle ${i + 1}/3`);
                    }, i * 1000);
                }
                
                setTimeout(() => {
                    console.log('✅ Masonry testing completed');
                }, 4000);
            }, 1000);
        } else {
            console.error('❌ Advanced Gallery not initialized');
        }
    },
    
    // Test selection mode
    testSelection: function() {
        console.log('🧪 Testing selection mode...');
        
        if (window.advancedGallery) {
            // Enable selection mode
            window.advancedGallery.toggleSelectionMode();
            console.log('Selection mode enabled');
            
            setTimeout(() => {
                // Select all photos
                window.advancedGallery.selectAllPhotos();
                console.log('All photos selected');
                
                setTimeout(() => {
                    // Disable selection mode
                    window.advancedGallery.toggleSelectionMode();
                    console.log('✅ Selection testing completed');
                }, 2000);
            }, 1000);
        } else {
            console.error('❌ Advanced Gallery not initialized');
        }
    },
    
    // Test lazy loading
    testLazyLoading: function() {
        console.log('🧪 Testing lazy loading...');
        
        if (window.advancedGallery) {
            console.log(`Total images: ${window.advancedGallery.totalImagesCount}`);
            console.log(`Loaded images: ${window.advancedGallery.loadedImagesCount}`);
            
            // Force load all images
            window.advancedGallery.loadAllImages();
            console.log('✅ Lazy loading test completed');
        } else {
            console.error('❌ Advanced Gallery not initialized');
        }
    },
    
    // Test search functionality
    testSearch: function() {
        console.log('🧪 Testing search functionality...');
        
        const searchInput = document.querySelector('.photo-search-input');
        if (searchInput) {
            // Test search
            searchInput.value = 'sunset';
            searchInput.dispatchEvent(new Event('input'));
            console.log('Search test performed');
            
            setTimeout(() => {
                // Clear search
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
                console.log('✅ Search testing completed');
            }, 2000);
        } else {
            console.error('❌ Search input not found');
        }
    },
    
    // Get gallery status
    getStatus: function() {
        console.log('📊 Advanced Gallery Status:');
        
        if (window.advancedGallery) {
            console.log(`- Current Layout: ${window.advancedGallery.currentLayout}`);
            console.log(`- Selection Mode: ${window.advancedGallery.selectionMode ? 'enabled' : 'disabled'}`);
            console.log(`- Selected Photos: ${window.advancedGallery.selectedPhotos.size}`);
            console.log(`- Total Images: ${window.advancedGallery.totalImagesCount}`);
            console.log(`- Loaded Images: ${window.advancedGallery.loadedImagesCount}`);
            console.log(`- PhotoSearch: ${window.advancedGallery.photoSearch ? 'initialized' : 'not initialized'}`);
            console.log(`- PhotoSelector: ${window.advancedGallery.photoSelector ? 'initialized' : 'not initialized'}`);
        } else {
            console.error('❌ Advanced Gallery not initialized');
        }
    },
    
    // Run all tests
    runAllTests: function() {
        console.log('🚀 Running all Advanced Gallery tests...');
        
        this.getStatus();
        
        setTimeout(() => this.testLayouts(), 1000);
        setTimeout(() => this.testMasonry(), 6000);
        setTimeout(() => this.testSelection(), 12000);
        setTimeout(() => this.testLazyLoading(), 17000);
        setTimeout(() => this.testSearch(), 19000);
        
        setTimeout(() => {
            console.log('✅ All tests completed!');
            this.getStatus();
        }, 22000);
    }
};

// Auto-run status check when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        console.log('🔍 Advanced Gallery Debug Tools Available');
        console.log('Use window.debugAdvancedGallery to access debug functions:');
        console.log('- debugAdvancedGallery.getStatus()');
        console.log('- debugAdvancedGallery.testLayouts()');
        console.log('- debugAdvancedGallery.testMasonry()');
        console.log('- debugAdvancedGallery.testSelection()');
        console.log('- debugAdvancedGallery.testLazyLoading()');
        console.log('- debugAdvancedGallery.testSearch()');
        console.log('- debugAdvancedGallery.runAllTests()');
        
        // Show initial status
        window.debugAdvancedGallery.getStatus();
    }, 2000);
});
