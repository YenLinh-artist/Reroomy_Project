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
        CANCELLED = "cancelled", "Đã hủy"
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


class SignupVoucherGrant(models.Model):
    """A one-use voucher assigned directly to a registered account."""
    class GrantType(models.TextChoices):
        SIGNUP = "signup", "Tặng khi đăng ký"
        MONTHLY = "monthly", "Thưởng tháng"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signup_voucher_grants")
    code = models.CharField(max_length=32)
    display_name = models.CharField(max_length=32)
    discount_value = models.PositiveIntegerField()
    minimum_order = models.PositiveBigIntegerField()
    grant_type = models.CharField(max_length=12, choices=GrantType.choices, default=GrantType.SIGNUP)
    reward_month = models.DateField(null=True, blank=True)
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    redeemed_order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="signup_voucher_grants")

    class Meta:
        ordering = ["-issued_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "code"], name="unique_signup_voucher_per_user"),
        ]

    def __str__(self):
        return f"{self.display_name} · {self.user}"


class MonthlyVoucherRewardBatch(models.Model):
    month_start = models.DateField(unique=True)
    recipient_count = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-month_start"]

    def __str__(self):
        return f"Voucher tháng {self.month_start:%m/%Y} · {self.recipient_count} khách"


class VoucherNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voucher_notifications")
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "voucher"], name="unique_voucher_notification_per_user"),
        ]

    def __str__(self):
        return f"{self.voucher.code}: {self.user}"


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


class DeXuatSanPham(models.Model):
    class TrangThai(models.TextChoices):
        CHO_DUYET = "pending", "Chờ duyệt"
        DA_DUYET = "approved", "Đã duyệt"
        TU_CHOI = "rejected", "Từ chối"

    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.PositiveIntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.PROTECT)
    phan_loai = models.CharField(max_length=300, blank=True)
    mo_ta = models.TextField(blank=True)
    so_luong = models.PositiveIntegerField(default=0)
    hinh_anh = models.FileField(upload_to="product_submissions/", blank=True)
    nguoi_tao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="de_xuat_san_pham",
        null=True,
        on_delete=models.SET_NULL,
    )
    nguoi_duyet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="de_xuat_san_pham_da_duyet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    trang_thai = models.CharField(max_length=10, choices=TrangThai.choices, default=TrangThai.CHO_DUYET)
    tao_luc = models.DateTimeField(auto_now_add=True)
    duyet_luc = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-tao_luc",)

    def __str__(self):
        return f"{self.ten_san_pham} ({self.get_trang_thai_display()})"


class StaffChatMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="staff_chat_messages",
        on_delete=models.CASCADE,
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("created_at", "pk")

    def __str__(self):
        return f"{self.sender}: {self.body[:50]}"


class HoSoNhanVien(models.Model):
    class BoPhan(models.TextChoices):
        CSKH = "cskh", "Chăm sóc khách hàng"
        BAN_HANG = "sales", "Nhân viên bán hàng"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="ho_so_nhan_vien",
        on_delete=models.CASCADE,
    )
    bo_phan = models.CharField(max_length=10, choices=BoPhan.choices, default=BoPhan.CSKH)

    def __str__(self):
        return f"{self.user.username} · {self.get_bo_phan_display()}"


class DonHang(models.Model):
    class TrangThai(models.TextChoices):
        MOI = "new", "Mới đặt"
        XAC_NHAN = "confirmed", "Đã duyệt"
        DANG_GIAO = "shipping", "Đang giao"
        HOAN_TAT = "completed", "Hoàn tất"
        DA_HUY = "cancelled", "Đã hủy"

    class ThanhToan(models.TextChoices):
        COD = "cod", "Thanh toán khi nhận hàng"
        BANK = "bank", "Chuyển khoản"

    khach_hang = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="don_hang",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    khach_hang_session_key = models.CharField(max_length=40, blank=True, default="")
    thong_bao_da_doc = models.BooleanField(default=False)
    ma_don = models.CharField(max_length=20, unique=True)
    ho_ten = models.CharField(max_length=150)
    so_dien_thoai = models.CharField(max_length=20)
    dia_chi = models.TextField()
    ghi_chu = models.TextField(blank=True)
    ghi_chu_noi_bo = models.TextField(blank=True)
    phuong_thuc = models.CharField(max_length=10, choices=ThanhToan.choices, default=ThanhToan.COD)
    trang_thai = models.CharField(max_length=20, choices=TrangThai.choices, default=TrangThai.MOI)
    tam_tinh = models.PositiveIntegerField()
    giam_gia = models.PositiveIntegerField(default=0)
    phi_giao_hang = models.PositiveIntegerField(default=0)
    tong_tien = models.PositiveIntegerField()
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-ngay_tao",)

    def __str__(self):
        return self.ma_don


class ChiTietDonHang(models.Model):
    don_hang = models.ForeignKey(DonHang, related_name="chi_tiet", on_delete=models.CASCADE)
    san_pham = models.ForeignKey(SanPham, null=True, blank=True, on_delete=models.SET_NULL)
    ten_san_pham = models.CharField(max_length=200)
    phan_loai = models.CharField(max_length=100, blank=True)
    don_gia = models.PositiveIntegerField()
    so_luong = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.ten_san_pham} × {self.so_luong}"


class CustomerServiceConversation(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="cskh_conversation",
        on_delete=models.CASCADE,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="cskh_assigned_conversations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Hỗ trợ: {self.customer.username}"


class CustomerServiceMessage(models.Model):
    class SenderRole(models.TextChoices):
        CUSTOMER = "customer", "Khách hàng"
        STAFF = "staff", "Nhân viên CSKH"

    conversation = models.ForeignKey(
        CustomerServiceConversation,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sender_role = models.CharField(max_length=10, choices=SenderRole.choices)
    body = models.TextField(max_length=3000)
    suggested_product = models.ForeignKey(
        SanPham,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cskh_suggestions",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        CustomerServiceConversation.objects.filter(pk=self.conversation_id).update(
            updated_at=self.created_at,
        )

    def __str__(self):
        return f"{self.get_sender_role_display()}: {self.body[:50]}"
