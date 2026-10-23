import calendar
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import (
    CustomerProfile,
    InventoryAdjustment,
    MonthlyVoucherRewardBatch,
    Order,
    SanPham,
    SignupVoucherGrant,
)


MONTHLY_VOUCHER_MINIMUM_SPEND = 10_000_000
MONTHLY_VOUCHER_DISCOUNT = 20
MONTHLY_VOUCHER_MINIMUM_ORDER = 1_000_000
MONTHLY_VOUCHER_NAME = "Thankyou"
BUSINESS_TIME_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def _add_one_calendar_month(value):
    month = value.month % 12 + 1
    year = value.year + (1 if value.month == 12 else 0)
    last_day = calendar.monthrange(year, month)[1]
    return value.replace(year=year, month=month, day=min(value.day, last_day))


@transaction.atomic
def issue_month_vouchers(reward_month, now=None):
    """Reward eligible registered customers for one completed calendar month."""
    now = now or timezone.now()
    local_now = timezone.localtime(now, BUSINESS_TIME_ZONE)
    reward_month = reward_month.replace(day=1)
    current_month_start = (reward_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    start = datetime.combine(reward_month, time.min).replace(tzinfo=BUSINESS_TIME_ZONE)
    end = datetime.combine(current_month_start, time.min).replace(tzinfo=BUSINESS_TIME_ZONE)

    batch, created = MonthlyVoucherRewardBatch.objects.get_or_create(month_start=reward_month)
    if not created:
        return batch.recipient_count

    qualified_users = list(
        CustomerProfile.objects.filter(
            user__isnull=False, user__is_active=True, user__is_staff=False, user__is_superuser=False,
        )
        .annotate(month_spend=Sum(
            "orders__total",
            filter=Q(
                orders__paid_at__gte=start,
                orders__paid_at__lt=end,
                orders__status=Order.Status.COMPLETED,
                orders__payment_status=Order.PaymentStatus.PAID,
            ),
        ))
        .filter(month_spend__gte=MONTHLY_VOUCHER_MINIMUM_SPEND)
        .order_by("user_id")
        .values_list("user_id", flat=True)
    )

    code = f"THANKYOU-{reward_month:%Y%m}"
    expires_at = _add_one_calendar_month(local_now)
    SignupVoucherGrant.objects.bulk_create([
        SignupVoucherGrant(
            user_id=user_id,
            code=code,
            display_name=MONTHLY_VOUCHER_NAME,
            discount_value=MONTHLY_VOUCHER_DISCOUNT,
            minimum_order=MONTHLY_VOUCHER_MINIMUM_ORDER,
            grant_type=SignupVoucherGrant.GrantType.MONTHLY,
            reward_month=reward_month,
            issued_at=now,
            expires_at=expires_at,
        )
        for user_id in qualified_users
    ], ignore_conflicts=True)

    batch.recipient_count = len(qualified_users)
    batch.processed_at = now
    batch.save(update_fields=["recipient_count", "processed_at"])
    return len(qualified_users)


@transaction.atomic
def confirm_order(order_id, actor):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status != Order.Status.PENDING:
        raise ValidationError("Chỉ xác nhận đơn đang chờ xử lý.")
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
        if not product or (not order.stock_reserved and product.so_luong < quantity):
            product_name = next(i.product_name for i in items if i.product_id == product_id)
            raise ValidationError(f"Không đủ tồn kho cho {product_name}.")
    for item in items:
        product = products.get(item.product_id)
        if not product:
            raise ValidationError(f"Sản phẩm {item.product_name} không còn trong danh mục.")
        if not order.stock_reserved:
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
    order.paid_at = timezone.now()
    order.save(update_fields=["payment_status", "paid_at", "updated_at"])
    return order


@transaction.atomic
def mark_online_payment_received(order_id, actor):
    """Manual payment confirmation for the simulated VietQR checkout flow."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.payment_method != Order.PaymentMethod.ONLINE:
        raise ValidationError("Chỉ xác nhận chuyển khoản cho đơn VietQR.")
    if order.status == Order.Status.CANCELLED:
        raise ValidationError("Không thể xác nhận thanh toán cho đơn đã hủy.")
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError("Đơn này đã được ghi nhận thanh toán.")
    order.payment_status = Order.PaymentStatus.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["payment_status", "paid_at", "updated_at"])
    return order


@transaction.atomic
def expire_unconfirmed_cod_orders(now=None):
    """Cancel COD orders left unconfirmed for three days after they enter the staff queue."""
    now = now or timezone.now()
    cutoff = now - timedelta(days=3)
    expired = Order.objects.select_for_update().filter(
        status=Order.Status.PENDING,
        payment_method=Order.PaymentMethod.COD,
        created_at__lte=cutoff,
    )
    count = 0
    for order in expired:
        cancel_order(order.pk, actor=None)
        from .models import OrderNotification
        OrderNotification.objects.create(
            order=order,
            message=f"Đơn hàng {order.code} đã tự hủy vì chưa được xác nhận sau 3 ngày.",
        )
        count += 1
    return count


def validate_voucher(voucher, order_total):
    if not voucher.is_usable(order_total):
        raise ValidationError("Voucher chưa được duyệt, chưa đến hạn, đã hết hạn/ lượt dùng hoặc chưa đủ giá trị đơn.")
    return True
