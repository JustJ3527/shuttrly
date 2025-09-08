// Theme management
const select = document.getElementById("theme-select");
const root = document.documentElement;
const navbarToggle = document.querySelector(".mobile-menu-toggle");
const mobileMenuOverlay = document.querySelector(".navbar-overlay");

// Load saved theme
let theme = localStorage.getItem("theme") || "device";
select.value = theme;

// Apply selected theme
function applyTheme(value) {
  if(value === "device") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = prefersDark ? "dark" : "light";
  } else {
    root.dataset.theme = value;
  }
  localStorage.setItem("theme", value);
  select.value = value;
}

// Apply on load
applyTheme(theme);

// Theme change via select
select.addEventListener("change", e => {
  theme = e.target.value;
  applyTheme(theme);
});

// System theme change if "device" option
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", e => {
  if(localStorage.getItem("theme") === "device") {
    applyTheme("device");
  }
});

// Mobile menu functionality
function initMobileMenu() {
  if (navbarToggle && mobileMenuOverlay) {
    // Toggle mobile menu
    navbarToggle.addEventListener("click", () => {
      document.body.classList.toggle("navbar-open");
    });
    
    // Close menu when clicking on overlay
    mobileMenuOverlay.addEventListener("click", (e) => {
      if (e.target === mobileMenuOverlay) {
        document.body.classList.remove("navbar-open");
      }
    });
    
    // Close menu when clicking on menu items
    const mobileMenuItems = mobileMenuOverlay.querySelectorAll("a");
    mobileMenuItems.forEach(item => {
      item.addEventListener("click", () => {
        document.body.classList.remove("navbar-open");
      });
    });
    
    // Close menu with Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && document.body.classList.contains("navbar-open")) {
        document.body.classList.remove("navbar-open");
      }
    });
  }
}

// Initialize mobile menu when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMobileMenu);
} else {
  initMobileMenu();
}

// Handle window resize to reset mobile menu state
window.addEventListener("resize", () => {
  if (window.innerWidth > 768) {
    // Reset mobile menu state on desktop
    document.body.classList.remove("navbar-open");
  }
});