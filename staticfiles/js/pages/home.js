// Home Page JavaScript
function initializeHomePage() {
    console.log('Home page initialized');
    
    // Add any home page specific functionality here
    // For example, animations, interactive elements, etc.
    
    // Example: Add fade-in animation to content sections
    const contentSections = document.querySelectorAll('.content-section');
    contentSections.forEach((section, index) => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            section.style.opacity = '1';
            section.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

// Export for global access
window.HomePage = {
    initializeHomePage
};
