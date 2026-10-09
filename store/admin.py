from django.contrib import admin
from .models import ChiTietDonHang, DanhMuc, DeXuatSanPham, DonHang, SanPham


class ChiTietDonHangInline(admin.TabularInline):
    model = ChiTietDonHang
    extra = 0
    readonly_fields = ("ten_san_pham", "phan_loai", "don_gia", "so_luong")


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    search_fields = ("ten_danh_muc",)
    ordering = ("ten_danh_muc",)


@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong")
    list_filter = ("danh_muc",)
    search_fields = ("ten_san_pham", "danh_muc__ten_danh_muc")


@admin.register(DonHang)
class DonHangAdmin(admin.ModelAdmin):
    list_display = ("ma_don", "ho_ten", "so_dien_thoai", "tong_tien", "trang_thai", "ngay_tao")
    list_filter = ("trang_thai", "phuong_thuc", "ngay_tao")
    search_fields = ("ma_don", "ho_ten", "so_dien_thoai")
    readonly_fields = ("ma_don", "ngay_tao", "tam_tinh", "giam_gia", "phi_giao_hang", "tong_tien")
    inlines = (ChiTietDonHangInline,)


@admin.register(DeXuatSanPham)
class DeXuatSanPhamAdmin(admin.ModelAdmin):
    list_display = ("ten_san_pham", "nguoi_tao", "so_luong", "trang_thai", "tao_luc")
    list_filter = ("trang_thai", "tao_luc")
    search_fields = ("ten_san_pham", "nguoi_tao__username")
    readonly_fields = ("nguoi_tao", "nguoi_duyet", "tao_luc", "duyet_luc")
