document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('.user-datetime').forEach(el => {
      const datetimeStr = el.dataset.datetime;
      if (datetimeStr) {
        const date = new Date(datetimeStr);
        const options = { dateStyle: 'short', timeStyle: 'short' };
        el.textContent = new Intl.DateTimeFormat(navigator.language, options).format(date);
      }
    });
  });