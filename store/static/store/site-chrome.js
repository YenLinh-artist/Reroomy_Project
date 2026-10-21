(() => {
  const links = [...document.querySelectorAll('#mainNav .navlink>a[data-nav-key]')];
  if (links.length) {
    function refreshActiveLink() {
      const path = location.pathname.replace(/\/$/, '') || '/';
      const hash = location.hash;
      let active = null;
      if (hash === '#san-pham') active = 'shop';
      else if (hash === '#combo') active = 'room';
      else if (hash === '#about') active = 'about';
      else if (path === '/') active = 'home';
      else if (path.startsWith('/san-pham/')) active = 'shop';
      else if (path.startsWith('/phong-mau/') || path.startsWith('/goi-y-combo/')) active = 'room';
      links.forEach(link => link.classList.toggle('active', link.dataset.navKey === active));
    }
    window.addEventListener('hashchange', refreshActiveLink);
    refreshActiveLink();
  }

  const searchToggle = document.getElementById('searchToggle');
  const searchBar = document.getElementById('searchBar');
  const searchInput = document.getElementById('productSearch');
  if (searchToggle && searchBar && searchInput) {
    searchToggle.addEventListener('click', () => {
      const isOpen = searchBar.classList.toggle('open');
      searchToggle.setAttribute('aria-expanded', String(isOpen));
      if (isOpen) {
        searchInput.focus();
      } else if (location.pathname === '/' && searchInput.value) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  }

  const notificationToggle = document.getElementById('notifyToggle');
  const notificationPopup = document.getElementById('notifyPop');
  if (notificationToggle && !notificationPopup) {
    notificationToggle.addEventListener('click', () => {
      const destination = notificationToggle.dataset.notificationsUrl;
      if (destination) window.location.assign(destination);
    });
  }
})();
