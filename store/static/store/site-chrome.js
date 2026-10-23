(() => {
  const navLinks = [...document.querySelectorAll('#mainNav .navlink>a[data-nav-key]')];
  const refreshActiveLink = () => {
    const path = location.pathname.replace(/\/$/, '') || '/';
    const hash = location.hash;
    let active = null;
    if (hash === '#san-pham') active = 'shop';
    else if (hash === '#combo') active = 'room';
    else if (hash === '#about') active = 'about';
    else if (path === '/') active = 'home';
    else if (path.startsWith('/san-pham/')) active = 'shop';
    else if (path.startsWith('/phong-mau/') || path.startsWith('/goi-y-combo/')) active = 'room';
    navLinks.forEach(link => link.classList.toggle('active', link.dataset.navKey === active));
  };
  window.addEventListener('hashchange', refreshActiveLink);
  refreshActiveLink();

  const searchToggle = document.getElementById('searchToggle');
  const searchBar = document.getElementById('searchBar');
  const searchInput = document.getElementById('productSearch');
  const setSearchOpen = open => {
    if (!searchToggle || !searchBar) return;
    searchBar.classList.toggle('open', open);
    searchToggle.setAttribute('aria-expanded', String(open));
    if (open) searchInput?.focus();
  };
  searchToggle?.addEventListener('click', () => {
    const open = !searchBar?.classList.contains('open');
    setSearchOpen(open);
    if (!open && searchInput) {
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });

  const account = document.querySelector('.topbar .account');
  const accountToggle = document.getElementById('accountToggle');
  const setAccountOpen = open => {
    if (!account || !accountToggle) return;
    account.classList.toggle('is-open', open);
    accountToggle.setAttribute('aria-expanded', String(open));
  };
  accountToggle?.addEventListener('click', event => {
    event.stopPropagation();
    setAccountOpen(!account.classList.contains('is-open'));
  });

  document.addEventListener('click', event => {
    if (!event.target.closest('.topbar .account')) setAccountOpen(false);
    if (!event.target.closest('#searchToggle, #searchBar')) setSearchOpen(false);

    const notifyPop = document.getElementById('notifyPop');
    if (notifyPop && !event.target.closest('#notifyToggle, #notifyPop')) {
      notifyPop.classList.remove('open');
      document.getElementById('notifyToggle')?.setAttribute('aria-expanded', 'false');
    }

    const notifyToggle = event.target.closest('#notifyToggle');
    if (notifyToggle && !document.getElementById('notifyPop')) {
      location.href = notifyToggle.dataset.notificationsUrl || '/tai-khoan/#notifications';
      return;
    }

    const cartToggle = event.target.closest('#cartToggle');
    if (cartToggle && !window.storeCart) {
      location.href = cartToggle.dataset.cartUrl || '/gio-hang/';
    }
  });

  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    setSearchOpen(false);
    document.getElementById('notifyPop')?.classList.remove('open');
    document.getElementById('notifyToggle')?.setAttribute('aria-expanded', 'false');
    if (account?.classList.contains('is-open')) {
      setAccountOpen(false);
      accountToggle?.focus();
    }
  });
})();
