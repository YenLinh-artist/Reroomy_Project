(() => {
  const panel = document.getElementById('salesAssignmentNotifications');
  if (!panel) return;

  let list = panel.querySelector('.sales-assignment-list');
  const ensureList = () => {
    if (list) return list;
    const heading = document.createElement('div');
    heading.className = 'sales-assignment-heading';
    const title = document.createElement('strong');
    title.textContent = 'Đơn mới được giao cho bạn';
    const subtitle = document.createElement('span');
    subtitle.textContent = 'Admin đã phân công các đơn sau.';
    heading.append(title, subtitle);
    list = document.createElement('ul');
    list.className = 'sales-assignment-list';
    panel.append(heading, list);
    return list;
  };

  const appendNotification = notification => {
    if (panel.querySelector(`[data-notification-id="${notification.id}"]`)) return;
    const item = document.createElement('li');
    item.dataset.notificationId = notification.id;
    const copy = document.createElement('div');
    const message = document.createElement('strong');
    message.textContent = notification.message;
    const time = document.createElement('time');
    time.textContent = notification.created_at;
    copy.append(message, time);
    const link = document.createElement('a');
    link.href = notification.url;
    link.textContent = 'Mở đơn';
    item.append(copy, link);
    ensureList().prepend(item);
    panel.hidden = false;
  };

  let loading = false;
  const refresh = async () => {
    if (loading) return;
    loading = true;
    try {
      const response = await fetch(panel.dataset.notificationsUrl, {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
      });
      if (!response.ok) return;
      const data = await response.json();
      data.notifications.forEach(appendNotification);
    } catch {
      // The page still shows notifications rendered by the server.
    } finally {
      loading = false;
    }
  };

  refresh();
  window.setInterval(refresh, 12000);
})();
