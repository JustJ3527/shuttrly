document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.querySelector(".navbar-toggle");
    const menu = document.querySelector(".navbar-menu");

    toggleBtn?.addEventListener("click", () => {
        menu.classList.toggle("open");
    });
});