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

    // Function to remove Django messages
    function removeMessages() {
        // Remove Django messages from all possible locations
        const messageSelectors = [
            '.messages',
            '.alert',
            '[class*="alert-"]',
            '.message',
            '.notification'
        ];
        
        messageSelectors.forEach(selector => {
            const messages = document.querySelectorAll(selector);
            messages.forEach(message => {
                if (message && message.parentNode) {
                    message.remove();
                }
            });
        });
    }

    // Remove messages on page load
    removeMessages();

    // Remove messages when navigating with browser back/forward buttons
    window.addEventListener('popstate', removeMessages);

    // Remove messages when using browser navigation
    window.addEventListener('beforeunload', removeMessages);

    // Remove messages when the page becomes visible again (e.g., from another tab)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            removeMessages();
        }
    });

    // Intercept navigation events for single-page applications or AJAX requests
    let currentUrl = window.location.href;
    
    // Check for URL changes periodically
    setInterval(() => {
        if (currentUrl !== window.location.href) {
            currentUrl = window.location.href;
            removeMessages();
        }
    }, 100);

    // Override pushState and replaceState to catch programmatic navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
        originalPushState.apply(this, args);
        setTimeout(removeMessages, 50);
    };

    history.replaceState = function(...args) {
        originalReplaceState.apply(this, args);
        setTimeout(removeMessages, 50);
    };
});