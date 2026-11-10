(() => {
  const favoritesKey = 'reroom-demo-faves';
  const toast = document.createElement('div');
  toast.className = 'product-feedback-toast';
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  document.body.append(toast);

  let toastTimer;
  const showToast = (message) => {
    toast.textContent = message;
    toast.classList.add('is-visible');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 2200);
  };
  const readFavorites = () => {
    try {
      const value = JSON.parse(localStorage.getItem(favoritesKey) || '[]');
      return new Set(Array.isArray(value) ? value.map(String) : []);
    } catch {
      return new Set();
    }
  };
  const syncFavorites = () => {
    const favorites = readFavorites();
    document.querySelectorAll('.product-card .heart').forEach((button) => {
      const card = button.closest('.product-card');
      const saved = favorites.has(String(card?.dataset.id || ''));
      const name = card?.dataset.name || 'sản phẩm';
      button.classList.toggle('saved', saved);
      button.setAttribute('aria-pressed', String(saved));
      button.setAttribute('aria-label', saved ? `Bỏ ${name} khỏi yêu thích` : `Lưu ${name} vào yêu thích`);
    });
  };

  document.addEventListener('click', (event) => {
    const button = event.target.closest('.product-card .heart');
    if (!button) return;
    event.preventDefault();
    const card = button.closest('.product-card');
    if (!card?.dataset.id) return;
    const favorites = readFavorites();
    const id = String(card.dataset.id);
    const wasSaved = favorites.has(id);
    if (wasSaved) favorites.delete(id);
    else favorites.add(id);
    try {
      localStorage.setItem(favoritesKey, JSON.stringify([...favorites]));
    } catch {
      showToast('Không lưu được lúc này. Bạn thử lại sau nha.');
      return;
    }
    syncFavorites();
    showToast(wasSaved ? 'Đã bỏ khỏi yêu thích' : 'Đã lưu sản phẩm yêu thích');
  });

  document.addEventListener('reroom-cart-added', (event) => {
    if (event.detail?.source !== 'card') return;
    const id = String(event.detail?.id || '');
    document.querySelectorAll('.product-card').forEach((card) => {
      if (card.dataset.id !== id) return;
      const button = card.querySelector('.add-cart');
      if (!button) return;
      button.dataset.defaultLabel ||= button.textContent.trim();
      button.textContent = 'Đã thêm vào giỏ';
      button.classList.add('is-added');
      window.clearTimeout(button._reroomAddedTimer);
      button._reroomAddedTimer = window.setTimeout(() => {
        button.textContent = button.dataset.defaultLabel;
        button.classList.remove('is-added');
      }, 1400);
    });
    showToast(`Đã thêm ${event.detail?.name || 'sản phẩm'} vào giỏ hàng`);
  });

  document.addEventListener('reroom-stock-error', (event) => {
    if (event.detail?.source !== 'card') return;
    const stock = Number(event.detail?.stock);
    showToast(stock < 1 ? 'Sản phẩm đã hết hàng' : `Chỉ còn ${stock} sản phẩm`);
  });

  window.addEventListener('storage', (event) => {
    if (event.key === favoritesKey) syncFavorites();
  });
  syncFavorites();
})();
