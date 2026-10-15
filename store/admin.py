from django.contrib import admin
from .models import (CustomerProfile, DanhMuc, DecorConsultation, InventoryAdjustment,
                     Order, OrderItem, ProductReview, SanPham, StaffProfile, Voucher)


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    search_fields = ("ten_danh_muc",)
    ordering = ("ten_danh_muc",)


@admin.register(SanPham)
class SanPhamAdmin(admin.ModelAdmin):
    list_display = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong")
    list_filter = ("danh_muc",)
    search_fields = ("ten_san_pham", "danh_muc__ten_danh_muc")


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_enabled")
    list_filter = ("role", "is_enabled")
    search_fields = ("user__username", "user__email")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "email", "phone")
    search_fields = ("full_name", "email", "phone")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "customer", "status", "payment_method", "payment_status", "total", "created_at")
    list_filter = ("status", "payment_method", "payment_status")
    search_fields = ("code", "customer__full_name", "customer__phone")
    inlines = (OrderItemInline,)
    readonly_fields = ("payment_status", "stock_reserved")


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("code", "status", "discount_type", "discount_value", "starts_at", "ends_at", "used_count", "usage_limit")
    list_filter = ("status", "discount_type")
    search_fields = ("code",)
    readonly_fields = ("status", "used_count", "created_by", "approved_by")


@admin.register(DecorConsultation)
class DecorConsultationAdmin(admin.ModelAdmin):
    list_display = ("code", "customer_name", "room_type", "assigned_to", "status", "created_at")
    list_filter = ("status", "room_type")
    search_fields = ("code", "customer_name", "contact")


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity_delta", "reason", "actor", "created_at")
    readonly_fields = ("product", "quantity_delta", "reason", "actor", "order", "created_at")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("customer", "order_item", "rating", "is_visible", "reported", "created_at")
    list_filter = ("is_visible", "reported", "rating")
