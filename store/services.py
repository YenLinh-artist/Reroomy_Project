from django.core.exceptions import ValidationError
from django.db import transaction

from .models import InventoryAdjustment, Order, SanPham


@transaction.atomic
def confirm_order(order_id, actor):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status != Order.Status.PENDING:
        raise ValidationError("Chỉ xác nhận đơn đang chờ xử lý.")
    if order.stock_reserved:
        raise ValidationError("Kho cho đơn này đã được giữ trước đó, không thể trừ thêm lần nữa.")
    if order.payment_method == Order.PaymentMethod.ONLINE and order.payment_status != Order.PaymentStatus.PAID:
        raise ValidationError("Chưa nhận được xác nhận thanh toán online từ cổng thanh toán.")
    if not order.items.exists():
        raise ValidationError("Đơn hàng chưa có sản phẩm.")
    items = list(order.items.select_related("product"))
    products = {p.pk: p for p in SanPham.objects.select_for_update().filter(pk__in=[i.product_id for i in items if i.product_id])}
    requested = {}
    for item in items:
        if item.product_id:
            requested[item.product_id] = requested.get(item.product_id, 0) + item.quantity
    for product_id, quantity in requested.items():
        product = products.get(product_id)
        if not product or product.so_luong < quantity:
            product_name = next(i.product_name for i in items if i.product_id == product_id)
            raise ValidationError(f"Không đủ tồn kho cho {product_name}.")
    for item in items:
        product = products.get(item.product_id)
        if not product:
            raise ValidationError(f"Sản phẩm {item.product_name} không còn trong danh mục.")
        product = products[item.product_id]
        product.so_luong -= item.quantity
        product.save(update_fields=["so_luong"])
        InventoryAdjustment.objects.create(product=product, quantity_delta=-item.quantity, reason=f"Xác nhận đơn {order.code}", actor=actor, order=order)
    order.stock_reserved = True
    order.status = Order.Status.CONFIRMED
    # Online payment can only be marked paid by a verified payment callback/action.
    # COD deliberately remains pending until cash collection is recorded.
    order.save(update_fields=["stock_reserved", "status", "updated_at"])
    return order


@transaction.atomic
def cancel_order(order_id, actor):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status in (Order.Status.CANCELLED, Order.Status.COMPLETED):
        raise ValidationError("Không thể hủy đơn đã hủy hoặc đã hoàn tất.")
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError("Đơn đã thanh toán cần quy trình hoàn tiền trước khi hủy.")
    if order.stock_reserved:
        for item in order.items.select_related("product"):
            if item.product_id:
                product = SanPham.objects.select_for_update().get(pk=item.product_id)
                product.so_luong += item.quantity
                product.save(update_fields=["so_luong"])
                InventoryAdjustment.objects.create(product=product, quantity_delta=item.quantity, reason=f"Hoàn kho đơn {order.code}", actor=actor, order=order)
        order.stock_reserved = False
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["stock_reserved", "status", "updated_at"])
    return order


@transaction.atomic
def mark_cod_collected(order_id, actor):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.payment_method != Order.PaymentMethod.COD:
        raise ValidationError("Chỉ ghi nhận thu tiền mặt cho đơn COD.")
    if order.status != Order.Status.COMPLETED:
        raise ValidationError("Chỉ ghi nhận COD sau khi giao hàng thành công.")
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError("Đơn này đã được ghi nhận thanh toán.")
    order.payment_status = Order.PaymentStatus.PAID
    order.save(update_fields=["payment_status", "updated_at"])
    return order


def validate_voucher(voucher, order_total):
    if not voucher.is_usable(order_total):
        raise ValidationError("Voucher chưa được duyệt, chưa đến hạn, đã hết hạn/ lượt dùng hoặc chưa đủ giá trị đơn.")
    return True
