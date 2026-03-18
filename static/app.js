document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submitter = form.querySelector('button[type="submit"]:not([disabled])');
      if (!submitter) return;
      submitter.classList.add('is-loading');
      if (!submitter.dataset.originalText) {
        submitter.dataset.originalText = submitter.textContent;
      }
      submitter.textContent = 'Please wait...';
    });
  });

  document.querySelectorAll('[data-flash-dismiss]').forEach((button) => {
    button.addEventListener('click', () => {
      const flash = button.closest('.flash');
      if (flash) flash.remove();
    });
  });
});
