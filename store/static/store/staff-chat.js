(() => {
  const card = document.querySelector('.staff-chat-card');
  const form = document.getElementById('staffChatForm');
  const input = document.getElementById('staffChatBody');
  const list = document.getElementById('staffChatMessages');
  const empty = document.getElementById('staffChatEmpty');
  const olderButton = document.getElementById('staffChatOlder');
  const error = document.getElementById('staffChatError');
  if (!card || !form || !input || !list) return;

  const api = card.dataset.api;
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  let lastId = 0;
  let initialized = false;
  let loading = false;

  function showError(message) {
    error.textContent = message;
    error.hidden = !message;
  }

  function createMessage(item) {
    const article = document.createElement('article');
    article.className = `staff-chat-message${item.mine ? ' mine' : ''}`;
    article.dataset.messageId = item.id;

    const meta = document.createElement('div');
    meta.className = 'staff-chat-meta';
    const sender = document.createElement('strong');
    sender.textContent = item.sender;
    const role = document.createElement('span');
    role.className = 'staff-chat-role';
    role.textContent = item.role;
    meta.append(sender, role);

    const bubble = document.createElement('div');
    bubble.className = 'staff-chat-bubble';
    bubble.textContent = item.body;

    const time = document.createElement('time');
    time.className = 'staff-chat-time';
    time.dateTime = item.created_at;
    time.textContent = new Intl.DateTimeFormat('vi-VN', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
    }).format(new Date(item.created_at));

    article.append(meta, bubble, time);
    return article;
  }

  function appendMessage(item) {
    if (empty) empty.hidden = true;
    const nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 100;
    const article = createMessage(item);
    list.append(article);
    if (nearBottom || !initialized) list.scrollTop = list.scrollHeight;
  }

  async function poll(initial = false) {
    if (loading) return;
    loading = true;
    try {
      const url = initial || !lastId ? api : `${api}?after=${lastId}`;
      const response = await fetch(url, { headers: { Accept: 'application/json' } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Chưa tải được tin nhắn.');
      if (initial || !lastId) {
        list.querySelectorAll('.staff-chat-message').forEach((node) => node.remove());
        for (const item of data.messages) {
          appendMessage(item);
          lastId = Math.max(lastId, item.id);
        }
        if (!data.messages.length && empty) empty.hidden = false;
        if (olderButton) olderButton.hidden = !data.has_older;
        initialized = true;
      } else {
        for (const item of data.messages) {
          appendMessage(item);
          lastId = Math.max(lastId, item.id);
        }
      }
      showError('');
    } catch (err) {
      showError(err.message || 'Mất kết nối tạm thời. Đang thử lại…');
    } finally {
      loading = false;
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = input.value.trim();
    if (!body) return;
    const button = form.querySelector('button[type=submit]');
    button.disabled = true;
    try {
      const response = await fetch(api, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf,
          Accept: 'application/json'
        },
        body: JSON.stringify({ body })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Chưa gửi được tin nhắn.');
      if (empty) empty.hidden = true;
      appendMessage(data.message);
      lastId = Math.max(lastId, data.message.id);
      initialized = true;
      input.value = '';
      showError('');
      input.focus();
    } catch (err) {
      showError(err.message || 'Chưa gửi được tin nhắn. Vui lòng thử lại.');
    } finally {
      button.disabled = false;
    }
  });

  if (olderButton) {
    olderButton.addEventListener('click', async () => {
      const firstMessage = list.querySelector('.staff-chat-message');
      if (!firstMessage) return;
      olderButton.disabled = true;
      try {
        const response = await fetch(`${api}?before=${firstMessage.dataset.messageId}`, {
          headers: { Accept: 'application/json' }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Chưa tải được tin nhắn cũ.');
        const previousHeight = list.scrollHeight;
        const fragment = document.createDocumentFragment();
        for (const item of data.messages) fragment.append(createMessage(item));
        list.prepend(fragment);
        list.scrollTop += list.scrollHeight - previousHeight;
        olderButton.hidden = !data.has_older;
        showError('');
      } catch (err) {
        showError(err.message || 'Chưa tải được tin nhắn cũ.');
      } finally {
        olderButton.disabled = false;
      }
    });
  }

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  poll(true);
  window.setInterval(() => poll(false), 4000);
})();
