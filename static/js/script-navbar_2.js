// Theme management functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeSelect = document.getElementById('theme-select');
    const htmlElement = document.documentElement;

    function applyTheme(theme) {
        if (theme === 'device') {
            // Use device preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            htmlElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            // Apply specific theme
            htmlElement.setAttribute('data-theme', theme);
        }
    }

    if (themeSelect) {
        // The theme is already applied by an inline script in the <head>.
        // We just need to set the dropdown to the correct value.
        const savedTheme = localStorage.getItem('theme') || 'light';
        themeSelect.value = savedTheme;

        // Listen for theme changes from the user
        themeSelect.addEventListener('change', function() {
            const selectedTheme = this.value;
            applyTheme(selectedTheme);
            localStorage.setItem('theme', selectedTheme);
        });
    }
    
    // Listen for system theme changes and apply if 'device' is selected.
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        if (themeSelect && themeSelect.value === 'device') {
            applyTheme('device');
        }
    });

    // --- Mobile Navbar Functionality ---
    const toggleButton = document.querySelector('.mobile-menu-toggle');
    const overlay = document.querySelector('.navbar-overlay');
    const body = document.body;
    const navbar = document.querySelector('.navbar');

    function closeMenu() {
        body.classList.remove('navbar-open');
    }

    if (toggleButton && overlay && navbar) {
        toggleButton.addEventListener('click', (e) => {
            e.stopPropagation();
            body.classList.toggle('navbar-open');
        });

        overlay.addEventListener('click', closeMenu);

        // Close menu when a link inside is clicked
        navbar.addEventListener('click', (e) => {
            if (e.target.closest('a')) {
                closeMenu();
            }
        });

        // Close menu with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && body.classList.contains('navbar-open')) {
                closeMenu();
            }
        });
    }
});

// Utility function to get current theme
function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme');
}

// Utility function to toggle between light and dark themes
function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update select if it exists
    const themeSelect = document.getElementById('theme-select');
    if (themeSelect) {
        themeSelect.value = newTheme;
    }
}