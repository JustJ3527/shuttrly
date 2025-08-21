// Theme management
const select = document.getElementById("theme-select");
const root = document.documentElement;
const navbarToggle = document.querySelector(".navbar-toggle");
const mobileMenuOverlay = document.querySelector(".mobile-menu-overlay");

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
      navbarToggle.classList.toggle("active");
      mobileMenuOverlay.classList.toggle("active");
      
      // Prevent body scroll when menu is open
      if (mobileMenuOverlay.classList.contains("active")) {
        document.body.style.overflow = "hidden";
      } else {
        document.body.style.overflow = "";
      }
    });
    
    // Close menu when clicking on overlay
    mobileMenuOverlay.addEventListener("click", (e) => {
      if (e.target === mobileMenuOverlay) {
        navbarToggle.classList.remove("active");
        mobileMenuOverlay.classList.remove("active");
        document.body.style.overflow = "";
      }
    });
    
    // Close menu when clicking on menu items
    const mobileMenuItems = mobileMenuOverlay.querySelectorAll("a");
    mobileMenuItems.forEach(item => {
      item.addEventListener("click", () => {
        navbarToggle.classList.remove("active");
        mobileMenuOverlay.classList.remove("active");
        document.body.style.overflow = "";
      });
    });
    
    // Close menu with Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && mobileMenuOverlay.classList.contains("active")) {
        navbarToggle.classList.remove("active");
        mobileMenuOverlay.classList.remove("active");
        document.body.style.overflow = "";
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
    if (navbarToggle) navbarToggle.classList.remove("active");
    if (mobileMenuOverlay) mobileMenuOverlay.classList.remove("active");
    document.body.style.overflow = "";
  }
});