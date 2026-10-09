from django.contrib import admin
from .models import DanhMuc, SanPham


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    search_fields = ("ten_danh_muc",)
    ordering = ("ten_danh_muc",)


@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong")
    list_filter = ("danh_muc",)
    search_fields = ("ten_san_pham", "danh_muc__ten_danh_muc")
