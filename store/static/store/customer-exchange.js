(() => {
  const form = document.getElementById('exchangeRequestForm');
  if (!form) return;

  const itemSelect = form.querySelector('#exchangeOrderItem');
  const productSelect = form.querySelector('#exchangeProduct');
  const variantSelect = form.querySelector('#exchangeVariant');
  const submitButton = form.querySelector('.exchange-submit');
  const availability = form.querySelector('.exchange-availability');
  const currentCard = form.querySelector('#exchangeCurrentPreview');
  const targetCard = form.querySelector('#exchangeTargetPreview');
  const priceDifference = form.querySelector('#exchangePriceDifference');
  const placeholderIcon = form.dataset.placeholderIcon;

  if (!itemSelect || !productSelect || !variantSelect) return;

  const money = (value) => `${new Intl.NumberFormat('vi-VN').format(Number(value || 0))}₫`;

  function setPreview(card, { image, name, variant, quantity, total }) {
    const picture = card.querySelector('img');
    picture.src = image || placeholderIcon;
    picture.alt = name || 'Sản phẩm';
    const title = card.querySelector('[data-preview-name]');
    const description = card.querySelector('[data-preview-description]');
    const price = card.querySelector('[data-preview-price]');
    title.textContent = name || 'Chọn sản phẩm';
    description.textContent = `${variant || 'Chọn phân loại'} · SL ${quantity || 0}`;
    price.textContent = total == null ? '—' : money(total);
  }

  function currentItem() {
    const option = itemSelect.selectedOptions[0];
    if (!option) return null;
    const unitPrice = Number(option.dataset.price || 0);
    const quantity = Number(option.dataset.quantity || 0);
    return {
      option,
      productId: option.dataset.productId || '',
      name: option.dataset.name || option.textContent.trim(),
      variant: option.dataset.variant || 'Mẫu hiện có',
      image: option.dataset.image || '',
      unitPrice,
      quantity,
      lineTotal: unitPrice * quantity,
    };
  }

  function selectedTarget(item) {
    const option = productSelect.selectedOptions[0];
    if (!option || !option.value || option.disabled || !item) return null;
    const variants = (option.dataset.variants || '').split(',').map((value) => value.trim()).filter(Boolean);
    return {
      option,
      productId: option.value,
      name: option.dataset.name || option.textContent.trim(),
      image: option.dataset.image || '',
      unitPrice: Number(option.dataset.price || 0),
      quantity: item.quantity,
      lineTotal: Number(option.dataset.price || 0) * item.quantity,
      variants: variants.length ? variants : ['Mẫu hiện có'],
    };
  }

  function updateAvailability(message, state = '') {
    availability.textContent = message;
    availability.dataset.state = state;
  }

  function syncVariants(item, target) {
    if (!target) {
      variantSelect.replaceChildren(new Option('Chưa có sản phẩm phù hợp', ''));
      variantSelect.disabled = true;
      return;
    }
    const previous = variantSelect.value;
    const variants = target.variants.map((value) => new Option(value, value));
    variantSelect.replaceChildren(...variants);
    variantSelect.disabled = false;
    if (variants.some((option) => option.value === previous)) variantSelect.value = previous;
    else if (target.productId === item.productId && variants.some((option) => option.value === item.variant)) {
      const alternate = variants.find((option) => option.value !== item.variant);
      variantSelect.value = alternate ? alternate.value : item.variant;
    }
  }

  function refresh() {
    const item = currentItem();
    if (!item) return;
    const previousProduct = productSelect.value;
    let eligibleCount = 0;

    for (const option of productSelect.options) {
      if (!option.value) continue;
      const samePrice = Number(option.dataset.price) === item.unitPrice;
      const sameProduct = option.value === item.productId;
      const enoughStock = sameProduct || Number(option.dataset.stock || 0) >= item.quantity;
      option.disabled = !samePrice || !enoughStock;
      if (!option.disabled) eligibleCount += 1;
    }

    const wasStillEligible = [...productSelect.options].some((option) => option.value === previousProduct && !option.disabled);
    if (!wasStillEligible) {
      const first = [...productSelect.options].find((option) => option.value && !option.disabled);
      productSelect.value = first ? first.value : '';
    }

    let target = selectedTarget(item);
    syncVariants(item, target);
    target = selectedTarget(item);
    const selectedVariant = variantSelect.value;
    const sameSelection = target && target.productId === item.productId && selectedVariant === item.variant;
    const isReady = Boolean(target && selectedVariant && !sameSelection);

    setPreview(currentCard, {
      image: item.image,
      name: item.name,
      variant: item.variant,
      quantity: item.quantity,
      total: item.lineTotal,
    });
    setPreview(targetCard, {
      image: target?.image,
      name: target?.name,
      variant: selectedVariant,
      quantity: target?.quantity,
      total: target?.lineTotal,
    });

    if (target && priceDifference) {
      const difference = target.lineTotal - item.lineTotal;
      priceDifference.textContent = difference === 0
        ? `Chênh lệch ${money(0)} · giữ nguyên giá trị phần hàng đổi`
        : `Chênh lệch ${difference > 0 ? '+' : '−'}${money(Math.abs(difference))}`;
    }

    submitButton.disabled = !isReady;
    if (!eligibleCount) {
      updateAvailability('Hiện chưa có món còn hàng cùng đơn giá để đổi. Bạn có thể nhắn CSKH để được tư vấn.', 'error');
    } else if (sameSelection) {
      updateAvailability('Bạn đang chọn lại đúng món và phân loại hiện tại. Hãy chọn món khác hoặc một phân loại khác nhé.', 'error');
    } else {
      updateAvailability('Các lựa chọn bên dưới cùng đơn giá với món trong đơn; tổng tiền đơn không thay đổi.', 'ready');
    }
  }

  itemSelect.addEventListener('change', refresh);
  productSelect.addEventListener('change', refresh);
  variantSelect.addEventListener('change', refresh);
  form.addEventListener('submit', (event) => {
    if (submitButton.disabled) {
      event.preventDefault();
      updateAvailability('Chọn một sản phẩm hoặc phân loại khác trước khi gửi yêu cầu nha.', 'error');
    }
  });

  refresh();
})();
