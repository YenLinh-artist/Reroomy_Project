from django.conf import settings
from django.db import models

class DanhMuc(models.Model):
    ten_danh_muc = models.CharField(max_length=100)

    def __str__(self):
        return self.ten_danh_muc

class SanPham(models.Model):
    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.IntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    mo_ta = models.TextField(blank=True)
    so_luong = models.PositiveIntegerField(default=0)
    hinh_anh = models.FileField(upload_to="products/", blank=True)

    def __str__(self):
        return self.ten_san_pham


class DeXuatSanPham(models.Model):
    class TrangThai(models.TextChoices):
        CHO_DUYET = "pending", "Chờ duyệt"
        DA_DUYET = "approved", "Đã duyệt"
        TU_CHOI = "rejected", "Từ chối"

    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.PositiveIntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.PROTECT)
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
# Create your models here.
