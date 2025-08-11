document.addEventListener("DOMContentLoaded", () => {
    // Format datetime elements
    document.querySelectorAll('.user-datetime').forEach(el => {
      const datetimeStr = el.dataset.datetime;
      if (datetimeStr) {
        const date = new Date(datetimeStr);
        const options = { dateStyle: 'short', timeStyle: 'short' };
        el.textContent = new Intl.DateTimeFormat(navigator.language, options).format(date);
      }
    });

    // Function to remove only old/legacy Django messages (not the new system)
    function removeOldMessages() {
        // Only remove old message formats, not the new django-messages container
        const oldMessageSelectors = [
            '.messages:not(#django-messages)',
            '.alert:not(.messages-container .alert)',
            '.message',
            '.notification'
        ];
        
        oldMessageSelectors.forEach(selector => {
            const messages = document.querySelectorAll(selector);
            messages.forEach(message => {
                if (message && message.parentNode && !message.closest('#django-messages')) {
                    message.remove();
                }
            });
        });
    }

    // Remove only old messages on page load
    removeOldMessages();

    // Remove old messages when navigating with browser back/forward buttons
    window.addEventListener('popstate', removeOldMessages);

    // Remove old messages when using browser navigation
    window.addEventListener('beforeunload', removeOldMessages);

    // Remove old messages when the page becomes visible again (e.g., from another tab)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            removeOldMessages();
        }
    });

    // Intercept navigation events for single-page applications or AJAX requests
    let currentUrl = window.location.href;
    
    // Check for URL changes periodically
    setInterval(() => {
        if (currentUrl !== window.location.href) {
            currentUrl = window.location.href;
            removeOldMessages();
        }
    }, 100);

    // Override pushState and replaceState to catch programmatic navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
        originalPushState.apply(this, args);
        setTimeout(removeOldMessages, 50);
    };

    history.replaceState = function(...args) {
        originalReplaceState.apply(this, args);
        setTimeout(removeOldMessages, 50);
    };
});