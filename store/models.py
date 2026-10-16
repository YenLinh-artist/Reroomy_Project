from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid

class DanhMuc(models.Model):
    ten_danh_muc = models.CharField(max_length=100)

    def __str__(self):
        return self.ten_danh_muc

class SanPham(models.Model):
    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.IntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    phan_loai = models.CharField(max_length=300, blank=True)
    mo_ta = models.TextField(blank=True)
    so_luong = models.PositiveIntegerField(default=0)
    hinh_anh = models.FileField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.ten_san_pham


class StaffProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Quản trị"
        SALES = "sales", "Bán hàng"
        CONSULTANT = "consultant", "Tư vấn decor"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SALES)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} · {self.get_role_display()}"


class CustomerProfile(models.Model):
    """Purchase identity. Guest customers are records too, without a login account."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="customer_profile")
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.full_name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ xác nhận"
        CONFIRMED = "confirmed", "Đã xác nhận"
        SHIPPING = "shipping", "Đang giao"
        COMPLETED = "completed", "Hoàn tất"
        CANCELLED = "cancelled", "Đã hủy"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "COD"
        ONLINE = "online", "Thanh toán online"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Chưa thanh toán"
        PAID = "paid", "Đã thanh toán"
        REFUNDED = "refunded", "Đã hoàn tiền"

    code = models.CharField(max_length=24, unique=True)
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(max_length=12, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    total = models.PositiveBigIntegerField(default=0)
    voucher_code = models.CharField(max_length=32, blank=True)
    shipping_address = models.TextField(blank=True)
    staff_assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_orders")
    stock_reserved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.payment_method == self.PaymentMethod.COD and self.payment_status == self.PaymentStatus.PAID and self.status != self.Status.COMPLETED:
            raise ValidationError({"payment_status": "COD chỉ được ghi nhận đã thu sau khi giao hàng hoàn tất."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(SanPham, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=200)
    unit_price = models.PositiveBigIntegerField()
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    variant = models.CharField(max_length=120, blank=True)

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class OrderNotification(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.code}: {self.message}"


class InventoryAdjustment(models.Model):
    product = models.ForeignKey(SanPham, on_delete=models.PROTECT, related_name="inventory_adjustments")
    quantity_delta = models.IntegerField()
    reason = models.CharField(max_length=200)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="inventory_events")
    created_at = models.DateTimeField(auto_now_add=True)


class Voucher(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Bản nháp"
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã duyệt"
        REJECTED = "rejected", "Từ chối"
        EXPIRED = "expired", "Hết hạn"

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Phần trăm"
        AMOUNT = "amount", "Số tiền"

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=12, choices=DiscountType.choices)
    discount_value = models.PositiveIntegerField()
    minimum_order = models.PositiveBigIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_vouchers")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_vouchers")

    def is_usable(self, order_total, now=None):
        now = now or timezone.now()
        return (self.status == self.Status.APPROVED and self.starts_at <= now < self.ends_at
                and self.used_count < self.usage_limit and order_total >= self.minimum_order)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "Thời điểm kết thúc phải sau thời điểm bắt đầu."})
        if self.discount_type == self.DiscountType.PERCENT and self.discount_value > 100:
            raise ValidationError({"discount_value": "Voucher phần trăm không thể vượt quá 100%."})
        if self.usage_limit < 1:
            raise ValidationError({"usage_limit": "Số lượt phát hành phải từ 1 trở lên."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class DecorConsultation(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Mới"
        ASSIGNED = "assigned", "Đã phân công"
        WORKING = "working", "Đang tư vấn"
        WAITING_CUSTOMER = "waiting_customer", "Chờ khách phản hồi"
        DONE = "done", "Hoàn tất"
        CANCELLED = "cancelled", "Đã hủy"

    code = models.CharField(max_length=24, unique=True)
    customer = models.ForeignKey(CustomerProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name="consultations")
    customer_name = models.CharField(max_length=160)
    contact = models.CharField(max_length=180)
    room_type = models.CharField(max_length=100, blank=True)
    area_m2 = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    style = models.CharField(max_length=120, blank=True)
    budget = models.PositiveBigIntegerField(null=True, blank=True)
    room_photo = models.FileField(upload_to="consultations/", blank=True)
    suggested_combo = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    conversation_log = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="decor_consultations")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)


class ProductReview(models.Model):
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="review")
    customer = models.ForeignKey(CustomerProfile, on_delete=models.PROTECT, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    content = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)
    reported = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.rating > 5:
            raise ValidationError({"rating": "Điểm đánh giá phải từ 1 đến 5."})
        if self.order_item.order.customer_id != self.customer_id or self.order_item.order.status != Order.Status.COMPLETED:
            raise ValidationError("Chỉ khách đã mua và hoàn tất đơn mới được đánh giá.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
# Create your models here.
