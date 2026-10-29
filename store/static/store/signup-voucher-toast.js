(() => {
  const toast = document.getElementById('signupVoucherToast');
  if (!toast) return;

  let dismissTimer;
  const dismiss = () => {
    toast.classList.remove('is-visible');
    window.setTimeout(() => { toast.hidden = true; }, 450);
  };

  toast.querySelector('.signup-voucher-toast__close')?.addEventListener('click', () => {
    window.clearTimeout(dismissTimer);
    dismiss();
  });

  window.requestAnimationFrame(() => toast.classList.add('is-visible'));
  dismissTimer = window.setTimeout(dismiss, 11000);
})();
