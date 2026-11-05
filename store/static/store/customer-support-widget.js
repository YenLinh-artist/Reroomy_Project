(() => {
  const widget = document.querySelector('.customer-support-widget');
  if (!widget) return;

  const toggle = widget.querySelector('#customerSupportToggle');
  const panel = widget.querySelector('#customerSupportPanel');
  const list = widget.querySelector('#customerSupportMessages');
  const form = widget.querySelector('#customerSupportCompose');
  const error = widget.querySelector('#customerSupportError');
  const authenticated = widget.dataset.authenticated === 'true';
  const api = widget.dataset.api;
  let signature = '';
  let pendingRequestId = '';

  const formatMoney = (value) => `${new Intl.NumberFormat('vi-VN').format(Number(value || 0))}₫`;
  const formatTime = (value) => new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

  function appendProductCard(container, imageUrl, name, variant, quantity, price) {
    const card = document.createElement('div');
    card.className = 'support-request-product';
    if (imageUrl) {
      const image = document.createElement('img');
      image.src = imageUrl;
      image.alt = name || 'Sản phẩm';
      image.loading = 'lazy';
      card.append(image);
    } else {
      const placeholder = document.createElement('span');
      placeholder.className = 'support-request-image-placeholder';
      placeholder.textContent = 'Sản phẩm';
      card.append(placeholder);
    }
    const title = document.createElement('strong');
    title.textContent = name || 'Sản phẩm trong đơn';
    const description = document.createElement('small');
    description.textContent = `${variant || 'Mẫu hiện có'} · SL ${quantity || 1}`;
    const total = document.createElement('small');
    total.textContent = `${formatMoney(price)} / món`;
    card.append(title, description, total);
    container.append(card);
  }

  function appendRequestCard(container, request) {
    const card = document.createElement('section');
    card.className = 'support-request-card';
    card.dataset.requestId = request.id;

    const top = document.createElement('div');
    top.className = 'support-request-top';
    const heading = document.createElement('strong');
    heading.textContent = request.type_label || 'Yêu cầu hỗ trợ';
    const status = document.createElement('span');
    status.className = 'support-request-status';
    status.textContent = request.status_label || 'Đang tiếp nhận';
    top.append(heading, status);

    const orderLink = document.createElement('a');
    orderLink.className = 'support-order-link';
    orderLink.href = request.order_url || '#';
    orderLink.textContent = `Mã đơn ${request.order_code || ''} · Xem đơn hàng`;

    const products = document.createElement('div');
    products.className = 'support-request-products';
    appendProductCard(products, request.item_image, request.item_name, request.item_variant,
      request.quantity, request.item_unit_price);

    if (request.target_name) {
      const arrow = document.createElement('img');
      arrow.className = 'support-request-arrow';
      arrow.src = widget.dataset.arrowIcon;
      arrow.alt = 'đổi sang';
      products.append(arrow);
      appendProductCard(products, request.target_image, request.target_name, request.target_variant,
        request.quantity, request.target_price);
    } else {
      const empty = document.createElement('span');
      empty.setAttribute('aria-hidden', 'true');
      products.append(empty);
    }

    card.append(top, orderLink, products);
    if (request.target_name) {
      const price = document.createElement('div');
      price.className = 'support-request-price';
      const label = document.createElement('span');
      label.textContent = `Tổng giá trị: ${formatMoney(request.item_line_total)} → ${formatMoney(request.target_line_total)}`;
      const difference = document.createElement('strong');
      const delta = Number(request.price_difference || 0);
      difference.textContent = delta === 0 ? 'Chênh lệch 0₫' : `Chênh lệch ${delta > 0 ? '+' : '−'}${formatMoney(Math.abs(delta))}`;
      price.append(label, difference);
      card.append(price);
    }
    if (request.reason || request.details) {
      const note = document.createElement('p');
      note.className = 'support-request-note';
      note.textContent = [request.reason, request.details].filter(Boolean).join(' · ');
      card.append(note);
    }
    container.append(card);
  }

  function focusPendingRequest() {
    if (!pendingRequestId) return;
    const requestCard = list.querySelector(`[data-request-id="${pendingRequestId}"]`);
    if (!requestCard) return;
    requestCard.scrollIntoView({ block: 'center', behavior: 'smooth' });
    pendingRequestId = '';
  }

  function render(messages) {
    const nextSignature = JSON.stringify(messages);
    if (signature === nextSignature) {
      focusPendingRequest();
      return;
    }
    const nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 90;
    signature = nextSignature;
    list.replaceChildren();

    if (!messages.length) {
      const welcome = document.createElement('p');
      welcome.className = 'support-welcome';
      welcome.textContent = 'Chào bạn, Re:Room có thể hỗ trợ gì cho bạn nè?';
      list.append(welcome);
      return;
    }

    for (const item of messages) {
      const article = document.createElement('article');
      article.className = `support-message${item.sender_role === 'customer' ? ' mine' : ''}`;
      const meta = document.createElement('div');
      meta.className = 'support-message-meta';
      meta.textContent = item.sender_role === 'customer' ? 'Bạn' : (item.sender || 'CSKH Re:Room');
      const bubble = document.createElement('div');
      bubble.className = 'support-message-bubble';
      bubble.textContent = item.body;
      article.append(meta, bubble);
      if (item.order_request) appendRequestCard(article, item.order_request);
      if (item.product) {
        const suggestion = document.createElement('a');
        suggestion.className = 'support-suggested-product';
        suggestion.href = item.product.url;
        suggestion.textContent = `Gợi ý sản phẩm: ${item.product.name} · ${formatMoney(item.product.price)}`;
        article.append(suggestion);
      }
      const time = document.createElement('time');
      time.className = 'support-message-time';
      time.dateTime = item.created_at;
      time.textContent = formatTime(item.created_at);
      article.append(time);
      list.append(article);
    }

    if (nearBottom || pendingRequestId) list.scrollTop = list.scrollHeight;
    focusPendingRequest();
  }

  async function loadMessages() {
    if (!authenticated || panel.hidden) return;
    try {
      const response = await fetch(api, { headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!response.ok) throw new Error('Chưa tải được tin nhắn. Bạn thử mở lại sau nha.');
      if (!(response.headers.get('content-type') || '').includes('application/json')) {
        throw new Error('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục trò chuyện.');
      }
      const data = await response.json();
      render(data.messages || []);
      if (error) error.hidden = true;
    } catch (exception) {
      if (error) {
        error.textContent = exception.message || 'Kết nối chat đang gián đoạn.';
        error.hidden = false;
      }
    }
  }

  function openPanel(requestId = '') {
    document.dispatchEvent(new CustomEvent('reroom:overlay-open', { detail: { name: 'support' } }));
    pendingRequestId = requestId ? String(requestId) : '';
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Đóng chat tư vấn');
    if (authenticated) loadMessages();
  }

  function closePanel({ restoreFocus = true } = {}) {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Mở chat tư vấn');
    if (restoreFocus) toggle.focus({ preventScroll: true });
  }

  document.addEventListener('reroom:overlay-open', (event) => {
    if (event.detail?.name !== 'support' && !panel.hidden) closePanel({ restoreFocus: false });
  });

  toggle.addEventListener('click', () => panel.hidden ? openPanel() : closePanel());
  widget.querySelector('[data-support-close]').addEventListener('click', closePanel);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !panel.hidden) closePanel();
  });

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-support-open]');
    if (!trigger) return;
    event.preventDefault();
    openPanel(trigger.dataset.supportRequestId || '');
  });
  window.addEventListener('customer-support:open', (event) => openPanel(event.detail?.requestId || ''));

  if (form) {
    const input = form.elements.body;
    const sendButton = form.querySelector('button[type="submit"]');
    const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = input.value.trim();
      if (!body) return;
      sendButton.disabled = true;
      if (error) error.hidden = true;
      try {
        const response = await fetch(api, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf, Accept: 'application/json' },
          body: JSON.stringify({ body }),
        });
        if (!(response.headers.get('content-type') || '').includes('application/json')) {
          throw new Error('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để gửi tin nhắn.');
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Chưa gửi được tin nhắn. Bạn thử lại nha.');
        input.value = '';
        await loadMessages();
        input.focus();
      } catch (exception) {
        if (error) {
          error.textContent = exception.message || 'Kết nối chat đang gián đoạn.';
          error.hidden = false;
        }
      } finally {
        sendButton.disabled = false;
      }
    });

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 105)}px`;
    });
  }

  window.setInterval(loadMessages, 5000);
})();
