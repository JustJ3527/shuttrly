// Public Profile Page JavaScript
function initializePublicProfilePage() {
    console.log('Public profile page initialized');
    
    // Add any public profile page specific functionality here
    // This will be called when the profile page is loaded via HTMX
    
    // Example: Add smooth scroll behavior for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Example: Add hover effects to profile cards
    const profileCards = document.querySelectorAll('.info-card');
    profileCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Export for global access
window.PublicProfilePage = {
    initializePublicProfilePage
};
