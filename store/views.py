from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Sum, Count, Q, F, Avg
from django.http import Http404, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.core.exceptions import ValidationError
from functools import wraps
from types import SimpleNamespace
from datetime import date, timedelta
import json
import re
import uuid

from .forms import DanhMucForm, SanPhamForm, StaffAccountForm, VoucherForm
from .models import (CustomerProfile, DanhMuc, DecorConsultation, InventoryAdjustment,
                     Order, OrderItem, OrderNotification, ProductReview, SanPham, StaffProfile, Voucher)
from .services import cancel_order, confirm_order, mark_cod_collected

from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from .forms import DanhMucForm, NhanVienCreationForm, NhanVienPasswordForm, SanPhamForm
from .models import (
    CustomerServiceConversation,
    CustomerServiceMessage,
    DanhMuc,
    DeXuatSanPham,
    HoSoNhanVien,
    SanPham,
)


DEMO_PRODUCTS = [
    {"id": "lounger", "name": "Ghế lười", "category": "Đồ thư giãn", "price": 200000, "sold": "2.0K", "image": "product-lounger.jpg", "tag": "Bán chạy", "description": "Một góc ngồi mềm mại để đọc sách, xem phim hoặc nghỉ ngơi sau giờ học. Kích thước gọn, hợp với phòng trọ và căn hộ nhỏ."},
    {"id": "plush", "name": "Gối ôm Chii kawa", "category": "Chăn gối", "price": 200000, "sold": "2.0K", "image": "product-plush.jpg", "tag": "Mềm xinh", "description": "Gối ôm mềm mại với tạo hình đáng yêu, thêm một chút ấm áp cho chiếc giường và góc nghỉ ngơi của bạn."},
    {"id": "desk", "name": "Bàn gấp gọn", "category": "Bàn học", "price": 200000, "sold": "2.0K", "image": "product-desk.jpg", "tag": "Tiết kiệm chỗ", "description": "Mặt bàn rộng vừa đủ cho laptop, sách vở và một tách cà phê. Có thể gấp lại khi cần thêm diện tích sinh hoạt."},
    {"id": "chair", "name": "Sofa nhỏ", "category": "Đồ thư giãn", "price": 200000, "sold": "2.0K", "image": "product-chair.jpg", "tag": "Được yêu thích", "description": "Chiếc sofa nhỏ giúp căn phòng có thêm một góc tiếp khách ấm cúng mà không chiếm nhiều diện tích."},
    {"id": "lamp", "name": "Đèn có học", "category": "Đèn & ánh sáng", "price": 200000, "sold": "2.0K", "image": "product-lamp.jpg", "tag": "Góc học tập", "description": "Đèn bàn cho góc học tập buổi tối, ánh sáng dịu và kiểu dáng xinh xắn để bàn học thêm cảm hứng."},
    {"id": "stand", "name": "Đồ kê điện thoại", "category": "Góc học tập", "price": 200000, "sold": "2.0K", "image": "product-phone-stand.jpg", "tag": "Nhỏ mà tiện", "description": "Giá đỡ điện thoại nhỏ gọn cho bàn học, tiện xem bài giảng và gọi video mà vẫn rảnh tay."},
    {"id": "bin", "name": "Thùng rác vịt", "category": "Đồ tiện ích", "price": 200000, "sold": "2.0K", "image": "product-duck-bin.jpg", "tag": "Cưng xỉu", "description": "Một món đồ tiện ích nhỏ cho phòng ngủ hoặc bàn học, giúp giữ căn phòng gọn gàng hơn."},
    {"id": "bedside", "name": "Tủ đầu giường", "category": "Đồ tiện ích", "price": 200000, "sold": "2.0K", "image": "product-bedside.jpg", "tag": "Gọn gàng", "description": "Tủ nhỏ cạnh giường để cất sách, sạc điện thoại và những món đồ bạn thường dùng."},
]
DEMO_ADMIN_PRODUCTS = [
    {"ten_san_pham": "Đèn ngủ mây mini", "category": "Đèn & ánh sáng", "gia_ban": 189000, "so_luong": 3},
    {"ten_san_pham": "Kệ gỗ để bàn", "category": "Góc học tập", "gia_ban": 249000, "so_luong": 4},
    {"ten_san_pham": "Gối tựa hoa kem", "category": "Chăn gối", "gia_ban": 159000, "so_luong": 2},
]
DEMO_VOUCHERS = (
    {"code": "ROOM25", "discount_type": Voucher.DiscountType.PERCENT, "discount_value": 25, "minimum_order": 0, "usage_limit": 1000, "cap_amount": 50000},
    {"code": "XINH10", "discount_type": Voucher.DiscountType.PERCENT, "discount_value": 10, "minimum_order": 0, "usage_limit": 1000, "cap_amount": 30000},
)
for item in DEMO_PRODUCTS:
    item["display_price"] = f"{item['price'] // 1000}k"


def _demo_admin_products():
    return [SimpleNamespace(
        ten_san_pham=item["ten_san_pham"],
        danh_muc=SimpleNamespace(ten_danh_muc=item["category"]),
        gia_ban=item["gia_ban"], so_luong=item["so_luong"], is_active=True,
        is_demo=True, hinh_anh=None, pk=None,
    ) for item in DEMO_ADMIN_PRODUCTS]


def _demo_admin_orders():
    now = timezone.now()
    rows = [
        ("RR-DEMO-031", "Minh Anh", "0901 234 567", "shipping", "cod", "pending", 680000, "Gh\u1ebf l\u01b0\u1eddi", 1, 1),
        ("RR-DEMO-030", "Gia H\u00e2n", "0902 345 678", "pending", "cod", "pending", 420000, "B\u00e0n g\u1ea5p g\u1ecdn", 1, 4),
        ("RR-DEMO-029", "Qu\u1ed1c B\u1ea3o", "0903 456 789", "completed", "cod", "paid", 1250000, "\u0110\u00e8n ng\u1ee7 m\u00e2y mini", 2, 6),
        ("RR-DEMO-028", "Th\u1ea3o Vy", "0904 567 890", "cancelled", "cod", "pending", 199000, "G\u1ed1i t\u1ef1a hoa kem", 1, 8),
        ("RR-DEMO-027", "Kh\u00e1nh Linh", "0905 678 901", "confirmed", "cod", "pending", 349000, "K\u1ec7 g\u1ed7 \u0111\u1ec3 b\u00e0n", 1, 2),
    ]
    statuses = dict(Order.Status.choices)
    methods = dict(Order.PaymentMethod.choices)
    payments = dict(Order.PaymentStatus.choices)
    return [SimpleNamespace(
        code=code, customer=SimpleNamespace(full_name=name, phone=phone, email=""),
        status=status, payment_method=method, payment_status=payment,
        total=total, created_at=now - timedelta(days=days), is_demo=True,
        get_status_display=lambda value=status: statuses[value],
        get_payment_method_display=lambda value=method: methods[value],
        get_payment_status_display=lambda value=payment: payments[value],
        demo_items=[SimpleNamespace(product_name=product_name, quantity=quantity)],
    ) for code, name, phone, status, method, payment, total, product_name, quantity, days in rows]


def _local_demo_photo(filename):
    return settings.BASE_DIR / "store" / "static" / "store" / "images" / filename


def _demo_product(item):
    variants = ["Màu kem"]
    return {
        **item,
        "image_url": static(f"store/images/{item['image']}") if _local_demo_photo(item["image"]).is_file() else "",
        "has_photo": _local_demo_photo(item["image"]).is_file(),
        "detail_url": item["id"],
        "rating": "4.8",
        "reviews_count": "128",
        "old_price": int(item["price"] * 1.15),
        "price_text": f"{item['price']:,}".replace(",", ".") + "đ",
        "old_price_text": f"{int(item['price'] * 1.15):,}".replace(",", ".") + "đ",
        "variant": variants[0],
        "variants": variants,
        "stock_status": "Còn hàng · mẫu minh họa",
        "is_demo": True,
        "sold_text": f"{item['sold']} lượt bán · mẫu minh họa",
        "icon_url": _product_icon_url(item["category"], item["name"]),
    }


def _database_product(item):
    variants = [value.strip() for value in (item.phan_loai or "").split(",") if value.strip()] or ["Mẫu hiện có"]
    return {
        "id": str(item.pk),
        "name": item.ten_san_pham,
        "category": item.danh_muc.ten_danh_muc,
        "price": item.gia_ban,
        "display_price": f"{item.gia_ban // 1000}k" if item.gia_ban >= 1000 else f"{item.gia_ban}đ",
        "sold": "Mới",
        "image": item.hinh_anh.name if item.hinh_anh else "",
        "image_url": item.hinh_anh.url if item.hinh_anh else "",
        "has_photo": bool(item.hinh_anh),
        "tag": "Mới cập nhật",
        "description": item.mo_ta or "Thông tin sản phẩm sẽ sớm được cập nhật.",
        "detail_url": str(item.pk),
        "rating": "—",
        "reviews_count": "0",
        "old_price": None,
        "price_text": f"{item.gia_ban:,}".replace(",", ".") + "đ",
        "old_price_text": "",
        "variant": variants[0],
        "variants": variants,
        "stock_status": f"Còn {item.so_luong} sản phẩm" if item.so_luong else "Tạm hết hàng",
        "is_demo": False,
        "sold_text": "Chưa có dữ liệu bán",
        "icon_url": _product_icon_url(item.danh_muc.ten_danh_muc, item.ten_san_pham),
    }


def _product_icon_url(category, product_name=""):
    label = f"{category or ''} {product_name or ''}".casefold()
    if any(word in label for word in ("chăn", "gối", "ngủ", "giường")):
        icon = "bed-double"
    elif any(word in label for word in ("đèn", "ánh sáng")):
        icon = "lamp-floor"
    elif "t\u1ee7" in label:
        icon = "wardrobe"
    elif any(word in label for word in ("học", "bàn", "kệ", "sách")):
        icon = "table-2"
    elif any(word in label for word in ("ghế", "thư giãn", "sofa")):
        icon = "sofa"
    else:
        icon = "armchair"
    return static(f"store/icons/{icon}.svg")


def _products_for_homepage():
    all_saved_products = SanPham.objects.exists()
    saved_products = list(SanPham.objects.filter(is_active=True).select_related("danh_muc").order_by("-pk"))
    if all_saved_products:
        return [_database_product(item) for item in saved_products]
    return [_demo_product(item) for item in DEMO_PRODUCTS]


def _saved_consultation_proposal(raw_value):
    try:
        rows = json.loads(raw_value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and str(row.get("product_id", "")).isdigit()]


def _consultation_proposal_total(rows):
    total = 0
    for row in rows:
        try:
            total += max(0, int(row.get("unit_price", 0))) * max(1, int(row.get("quantity", 1)))
        except (TypeError, ValueError):
            continue
    return total


def _active_checkout_vouchers():
    now = timezone.now()
    vouchers = list(Voucher.objects.filter(
        status=Voucher.Status.APPROVED, starts_at__lte=now, ends_at__gt=now,
        used_count__lt=F("usage_limit"),
    ).order_by("ends_at"))
    if settings.ADMIN_DEMO_MODE:
        demo_codes = [item["code"] for item in DEMO_VOUCHERS]
        saved_codes = set(Voucher.objects.filter(code__in=demo_codes).values_list("code", flat=True))
        vouchers.extend(
            SimpleNamespace(**item, used_count=0)
            for item in DEMO_VOUCHERS if item["code"] not in saved_codes
        )
    preview = [{
        "code": item.code,
        "discount_type": item.discount_type,
        "discount_value": item.discount_value,
        "minimum_order": item.minimum_order,
        "usage_left": item.usage_limit - item.used_count,
        "cap_amount": getattr(item, "cap_amount", None),
    } for item in vouchers]
    return vouchers, preview


def trang_chu(request):
    return render(request, "index.html", {
        "san_pham_list": _products_for_homepage(),
        "categories": ["Phổ biến", "Combo chăn ấm - gối êm", "Giấy dán tường", "Đèn ngủ - học tập", "Gương tường"],
    })


def gio_hang(request):
    _, voucher_preview = _active_checkout_vouchers()
    return render(request, "store/cart.html", {"voucher_preview": voucher_preview})


def thanh_toan(request):
    customer = CustomerProfile.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    last_order = Order.objects.filter(customer=customer).order_by("-created_at").first() if customer else None
    defaults = {
        "full_name": customer.full_name if customer else "",
        "email": customer.email if customer else (request.user.email if request.user.is_authenticated else ""),
        "phone": customer.phone if customer else "",
        "address": last_order.shipping_address.split("\nGhi chú:", 1)[0] if last_order else "",
    }
    if request.method == "POST":
        try:
            # Keep the optional voucher value defined even when no code was submitted.
            applied_voucher = None
            discount = 0
            submitted = json.loads(request.POST.get("cart_data", "[]"))
            if not isinstance(submitted, list) or not submitted:
                raise ValueError("Giỏ hàng chưa có sản phẩm được chọn.")
            if len(submitted) > 40:
                raise ValueError("Gi\u1ecf h\u00e0ng c\u00f3 qu\u00e1 nhi\u1ec1u d\u00f2ng s\u1ea3n ph\u1ea9m, vui l\u00f2ng t\u00e1ch th\u00e0nh nhi\u1ec1u \u0111\u01a1n.")
            clean_items, subtotal = [], 0
            for row in submitted[:40]:
                if not isinstance(row, dict):
                    raise ValueError("Th?ng tin s?n ph?m trong gi? kh?ng h?p l?.")
                key = str(row.get("id", ""))
                quantity = int(row.get("qty", 0))
                if quantity < 1 or quantity > 99:
                    raise ValueError("Số lượng sản phẩm chưa hợp lệ.")
                product = None
                demo = next((item for item in DEMO_PRODUCTS if item["id"] == key), None)
                if demo:
                    name, price = demo["name"], demo["price"]
                elif key.isdigit():
                    product = SanPham.objects.filter(pk=int(key), is_active=True).first()
                    if not product:
                        raise ValueError("Có sản phẩm không còn được bán. Vui lòng cập nhật giỏ hàng.")
                    if product.so_luong < quantity:
                        raise ValueError(f"{product.ten_san_pham} hiện không đủ số lượng trong kho.")
                    name, price = product.ten_san_pham, product.gia_ban
                else:
                    raise ValueError("Giỏ hàng có sản phẩm không hợp lệ.")
                clean_items.append((product, name, price, quantity, str(row.get("variant", ""))[:120]))
                subtotal += price * quantity
            full_name = request.POST.get("full_name", "").strip()[:160]
            email = request.POST.get("email", "").strip()[:254]
            phone = request.POST.get("phone", "").strip()[:30]
            address = request.POST.get("address", "").strip()[:1000]
            note = request.POST.get("note", "").strip()[:500]
            if not full_name or not phone or not address:
                raise ValueError("Vui lòng nhập họ tên, số điện thoại và địa chỉ giao hàng.")
            payment = request.POST.get("payment", Order.PaymentMethod.COD)
            if payment != Order.PaymentMethod.COD:
                raise ValueError("Hiện tại hệ thống chỉ hỗ trợ thanh toán khi nhận hàng (COD).")
            code = request.POST.get("voucher_code", "").strip().upper()
            shipping = 0 if subtotal >= 500000 else (20000 if subtotal else 0)
            with transaction.atomic():
                if code:
                    applied_voucher = Voucher.objects.select_for_update().filter(code=code).first()
                    if applied_voucher:
                        if not applied_voucher.is_usable(subtotal):
                            raise ValueError("Voucher không còn hiệu lực hoặc đơn hàng chưa đạt giá trị tối thiểu.")
                        if applied_voucher.discount_type == Voucher.DiscountType.PERCENT:
                            discount = (subtotal * applied_voucher.discount_value + 50) // 100
                        else:
                            discount = min(subtotal, applied_voucher.discount_value)
                    else:
                        demo_voucher = next((item for item in DEMO_VOUCHERS if item["code"] == code), None)
                        if not (settings.ADMIN_DEMO_MODE and demo_voucher):
                            raise ValueError("Mã voucher không hợp lệ hoặc chưa được duyệt.")
                        discount = min((subtotal * demo_voucher["discount_value"] + 50) // 100, demo_voucher["cap_amount"])
                if request.user.is_authenticated:
                    customer, _ = CustomerProfile.objects.get_or_create(
                        user=request.user,
                        defaults={"full_name": full_name, "email": email, "phone": phone},
                    )
                    customer.full_name, customer.email, customer.phone = full_name, email, phone
                    customer.save(update_fields=["full_name", "email", "phone"])
                else:
                    customer = CustomerProfile.objects.create(full_name=full_name, email=email, phone=phone)
                order = Order.objects.create(
                    code=f"RR-{uuid.uuid4().hex[:10].upper()}", customer=customer,
                    payment_method=Order.PaymentMethod.COD,
                    payment_status=Order.PaymentStatus.PENDING,
                    total=max(0, subtotal - discount) + shipping,
                    voucher_code=code if code else "",
                    shipping_address=address + (f"\nGhi chú: {note}" if note else ""),
                )
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=product, product_name=name, unit_price=price,
                              quantity=quantity, variant=variant)
                    for product, name, price, quantity, variant in clean_items
                ])
                OrderNotification.objects.create(
                    order=order,
                    message="Đơn hàng đã được tiếp nhận và đang chờ nhân viên bán hàng duyệt.",
                )
                if applied_voucher:
                    applied_voucher.used_count += 1
                    applied_voucher.save(update_fields=["used_count"])
            request.session["reroom_last_order_id"] = order.pk
            return redirect("dat_hang_thanh_cong")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            messages.error(request, str(exc))
    active_vouchers, voucher_preview = _active_checkout_vouchers()
    return render(request, "store/checkout.html", {
        "checkout_defaults": defaults, "active_vouchers": active_vouchers,
        "voucher_preview": voucher_preview,
    })


def dat_hang_thanh_cong(request):
    order_id = request.session.pop("reroom_last_order_id", None)
    if not order_id:
        return redirect("trang_chu")
    order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("items"), pk=order_id)
    purchased_ids = {str(product_id) for product_id in order.items.exclude(product_id=None).values_list("product_id", flat=True)}
    purchased_names = {item.product_name.casefold() for item in order.items.all()}
    suggestions = [
        product for product in _products_for_homepage()
        if product["id"] not in purchased_ids
        and product["name"].casefold() not in purchased_names
    ][:4]
    return render(request, "store/order_success.html", {"order": order, "suggestions": suggestions})


def theo_doi_don_hang(request, tracking_token):
    order = get_object_or_404(
        Order.objects.prefetch_related("notifications"), tracking_token=tracking_token
    )
    return render(request, "store/order_tracking.html", {"order": order})


@login_required
def bao_cao_danh_gia(request, review_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    review = get_object_or_404(
        ProductReview.objects.select_related("order_item__product"),
        pk=review_id,
        order_item__product__isnull=False,
        is_visible=True,
    )
    if review.customer.user_id == request.user.pk:
        messages.error(request, "Bạn không thể báo cáo đánh giá của chính mình.")
    else:
        review.reported = True
        review.is_visible = False
        review.save(update_fields=["reported", "is_visible"])
        messages.success(request, "Đã gửi báo cáo. Đánh giá được ẩn trong lúc nhân viên kiểm tra.")
    return redirect("chi_tiet_san_pham", product_key=str(review.order_item.product_id))


@login_required
def tai_khoan(request):
    if request.user.is_staff:
        return redirect("quan_tri_dashboard")
    customer, _ = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={"full_name": request.user.get_full_name() or request.user.username, "email": request.user.email},
    )
    if request.method == "POST":
        action = request.POST.get("action", "save_profile")
        if action == "change_password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Mật khẩu đã được cập nhật.")
            else:
                for errors in password_form.errors.values():
                    for error in errors:
                        messages.error(request, error)
            return redirect(f"{request.path}#settings")
        if action == "submit_review":
            order_item = get_object_or_404(
                OrderItem.objects.select_related("order", "product"),
                pk=request.POST.get("order_item_id"),
                order__customer=customer,
                order__status=Order.Status.COMPLETED,
                product__isnull=False,
            )
            try:
                rating = int(request.POST.get("rating", "0"))
            except (TypeError, ValueError):
                rating = 0
            content = request.POST.get("content", "").strip()[:1000]
            if rating not in range(1, 6) or not content:
                messages.error(request, "Chọn số sao từ 1 đến 5 và viết nội dung đánh giá nha.")
            elif ProductReview.objects.filter(order_item=order_item).exists():
                messages.error(request, "Sản phẩm trong đơn này đã được đánh giá rồi.")
            else:
                ProductReview.objects.create(
                    order_item=order_item,
                    customer=customer,
                    rating=rating,
                    content=content,
                    is_visible=False,
                )
                messages.success(request, "Đánh giá đã lưu và đang chờ nhân viên duyệt trước khi hiển thị.")
            return redirect("tai_khoan")
        if action != "save_profile":
            return redirect("tai_khoan")
        full_name = request.POST.get("full_name", "").strip()[:160]
        email = request.POST.get("email", "").strip()[:254]
        phone = request.POST.get("phone", "").strip()[:30]
        import re
        email_valid = True
        if email:
            try:
                validate_email(email)
            except ValidationError:
                email_valid = False
        if not full_name or not re.fullmatch(r"[0-9+() .-]{9,16}", phone):
            messages.error(request, "S\u1ed1 \u0111i\u1ec7n tho\u1ea1i ch\u01b0a \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng.")
        elif not email_valid:
            messages.error(request, "Email ch\u01b0a \u0111\u00fang \u0111\u1ecbnh d\u1ea1ng.")
        else:
            customer.full_name, customer.email, customer.phone = full_name, email, phone
            customer.save(update_fields=["full_name", "email", "phone"])
            request.user.first_name = full_name
            request.user.email = email
            request.user.save(update_fields=["first_name", "email"])
            messages.success(request, "Đã lưu thông tin tài khoản.")
            return redirect("tai_khoan")
    products = _products_for_homepage()
    order_queryset = Order.objects.filter(customer=customer).prefetch_related("items__review", "items__product").order_by("-created_at")
    orders = order_queryset[:10]
    reviews = ProductReview.objects.filter(customer=customer).select_related("order_item", "order_item__product").order_by("-created_at")[:20]
    notifications = OrderNotification.objects.filter(order__customer=customer).select_related("order")[:20]
    available_vouchers, _ = _active_checkout_vouchers()
    return render(request, "store/account.html", {
        "customer": customer,
        "products": products,
        "orders": orders,
        "orders_count": order_queryset.count(),
        "reviews": reviews,
        "reviews_count": ProductReview.objects.filter(customer=customer).count(),
        "order_notifications": notifications,
        "unread_notifications_count": OrderNotification.objects.filter(order__customer=customer, is_read=False).count(),
        "available_vouchers": available_vouchers,
        "password_form": PasswordChangeForm(user=request.user),
    })


def goi_y_combo(request):
    width = request.GET.get("width", "3")
    depth = request.GET.get("depth", "4")
    style = request.GET.get("style", "ấm áp")
    try:
        width_value = min(10, max(1, float(width)))
        depth_value = min(15, max(1, float(depth)))
    except ValueError:
        width_value, depth_value, width, depth = 3.0, 4.0, "3", "4"
    suggestions = _products_for_homepage()
    return render(request, "store/combo_ideas.html", {
        "width": width, "depth": depth, "area": round(width_value * depth_value, 1),
        "style": style, "suggestions": suggestions,
        "room_icon": static("store/icons/layout-dashboard.svg"),
        "ruler_icon": static("store/icons/ruler.svg"),
    })



def tu_van_decor(request):
    if request.method == "POST":
        import re
        customer_name = request.POST.get("customer_name", "").strip()[:160]
        contact = request.POST.get("contact", "").strip()[:180]
        room_type = request.POST.get("room_type", "").strip()[:100]
        style = request.POST.get("style", "").strip()[:120]
        notes = request.POST.get("notes", "").strip()[:3000]
        area_raw = request.POST.get("area_m2", "").strip()
        budget_raw = request.POST.get("budget", "").strip()
        photo = request.FILES.get("room_photo")
        try:
            area = float(area_raw) if area_raw else None
            budget = int(budget_raw) if budget_raw else None
            if not customer_name or not contact or not room_type:
                raise ValueError("Vui l?ng nh?p t?n, c?ch li?n h? v? lo?i ph?ng.")
            if "@" in contact:
                from django.core.validators import validate_email
                try:
                    validate_email(contact)
                except ValidationError:
                    raise ValueError("Email li?n h? ch?a ??ng ??nh d?ng.")
            elif not re.fullmatch(r"[0-9+() .-]{9,16}", contact):
                raise ValueError("S? ?i?n tho?i li?n h? ch?a ??ng ??nh d?ng.")
            if area is not None and not 1 <= area <= 150:
                raise ValueError("Di?n t?ch ph?ng c?n trong kho?ng 1?150 m?.")
            if budget is not None and not 0 <= budget <= 1_000_000_000:
                raise ValueError("Ng?n s?ch ch?a h?p l?.")
            if photo and (photo.size > 5 * 1024 * 1024 or not (photo.content_type or "").startswith("image/")):
                raise ValueError("?nh ph?ng c?n l? t?p h?nh ?nh d??i 5 MB.")
        except (ValueError, TypeError) as exc:
            messages.error(request, str(exc))
        else:
            customer = None
            if request.user.is_authenticated:
                customer, _ = CustomerProfile.objects.get_or_create(
                    user=request.user,
                    defaults={"full_name": customer_name, "email": request.user.email},
                )
            DecorConsultation.objects.create(
                code=f"TV-{uuid.uuid4().hex[:10].upper()}", customer=customer,
                customer_name=customer_name, contact=contact, room_type=room_type,
                area_m2=area, style=style, budget=budget, room_photo=photo,
                notes=notes, status=DecorConsultation.Status.NEW,
            )
            messages.success(request, "\u0110\u00e3 g\u1eedi y\u00eau c\u1ea7u t\u01b0 v\u1ea5n. Nh\u00e2n vi\u00ean Re:Room s\u1ebd li\u00ean h\u1ec7 theo th\u00f4ng tin b\u1ea1n \u0111\u1ec3 l\u1ea1i.")
            return redirect("tu_van_decor")
    return render(request, "store/consultation_request.html")


def phong_mau(request):
    return render(request, "store/rooms.html", {"suggestions": _products_for_homepage()})


def chi_tiet_san_pham(request, product_key):
    product = next((item for item in DEMO_PRODUCTS if item["id"] == product_key), None)
    saved = None
    if product:
        item = _demo_product(product)
    elif product_key.isdigit():
        saved = get_object_or_404(SanPham.objects.select_related("danh_muc"), pk=int(product_key), is_active=True)
        item = _database_product(saved)
    else:
        raise Http404("Không tìm thấy sản phẩm")

    related = [
        _demo_product(other)
        for other in DEMO_PRODUCTS
        if other["id"] != product_key
    ][:4]
    if saved:
        review_rows = list(ProductReview.objects.filter(
            order_item__product=saved, is_visible=True,
        ).select_related("customer").order_by("-created_at"))
        review_average = ProductReview.objects.filter(
            order_item__product=saved, is_visible=True,
        ).aggregate(value=Avg("rating"))["value"]
        item["rating"] = f"{review_average:.1f}" if review_average else "—"
        item["reviews_count"] = str(len(review_rows))
        reviews = [SimpleNamespace(
            name=review.customer.full_name,
            text=review.content or "Khách hàng đã đánh giá sản phẩm này.",
            date=review.created_at.strftime("%d/%m/%Y"),
            pk=review.pk,
        ) for review in review_rows]
    else:
        reviews = [
            {"name": "Mây nhỏ", "text": "Món decor xinh, vừa vặn với góc phòng của mình.", "date": "Đánh giá minh họa"},
            {"name": "Linh Chi", "text": "Màu sắc dịu và nhìn ngoài đời cũng dễ phối.", "date": "Đánh giá minh họa"},
        ]
    return render(request, "store/product_detail.html", {
        "product": item,
        "related_products": related,
        "reviews": reviews,
        "review_count": item["reviews_count"],
        "is_database_product": bool(saved),
    })


def dang_ky(request):
    if request.user.is_authenticated:
        return redirect("trang_chu")
    if request.method == "POST":
        full_name = " ".join(request.POST.get("full_name", "").split())[:150]
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        errors = []

        if not full_name:
            errors.append("Vui lòng nhập họ và tên.")
        if not username:
            errors.append("Vui lòng nhập tên đăng nhập.")
        elif not re.fullmatch(r"[a-z0-9_]{1,150}", username):
            errors.append("Tên đăng nhập chỉ gồm chữ không dấu, số và dấu gạch dưới (_), không có khoảng trắng.")
        elif User.objects.filter(username__iexact=username).exists():
            errors.append("Tên đăng nhập đã tồn tại. Bạn thử tên khác nhé.")

        if email:
            try:
                validate_email(email)
            except ValidationError as exc:
                errors.extend(exc.messages)
            else:
                if len(email) > 254:
                    errors.append("Email không được dài quá 254 ký tự.")
                elif User.objects.filter(email__iexact=email).exists():
                    errors.append("Email này đã được dùng cho một tài khoản Re:Room rồi.")

        if not password:
            errors.append("Vui lòng nhập mật khẩu.")
        elif password != password_confirm:
            errors.append("Mật khẩu nhập lại không khớp.")
        else:
            try:
                validate_password(password, User(username=username, email=email, first_name=full_name))
            except ValidationError as exc:
                errors.extend(exc.messages)

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Only persist registration data after every field has passed validation.
                # Keep the account and its customer profile atomic so failures leave no partial records.
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=full_name,
                        password=password,
                    )
                    CustomerProfile.objects.create(user=user, full_name=full_name, email=email)
            except IntegrityError:
                messages.error(request, "Tên đăng nhập hoặc email vừa được sử dụng. Bạn thử lại nhé.")
            else:
                login(request, user)
                messages.success(request, "Tạo tài khoản thành công. Chào mừng bạn đến Re:Room!")
                return redirect("trang_chu")
    return render(request, "register.html")


def dang_nhap(request):
    if request.user.is_authenticated:
        return redirect(_staff_landing(request.user))
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "B\u1ea1n \u0111\u00e3 \u0111\u0103ng nh\u1eadp. Ch\u00e0o m\u1eebng tr\u1edf l\u1ea1i!")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(_staff_landing(user))
        messages.error(request, "T\u00ean \u0111\u0103ng nh\u1eadp ho\u1eb7c m\u1eadt kh\u1ea9u ch\u01b0a ch\u00ednh x\u00e1c.")
    return render(request, "login.html", {"next": next_url})


def dang_xuat(request):
    logout(request)
    return redirect("trang_chu")


def _roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("dang_nhap")
            profile = getattr(request.user, "staff_profile", None)
            if not request.user.is_superuser and not (request.user.is_staff and profile and profile.is_enabled and profile.role in roles):
                return HttpResponseForbidden("Bạn không có quyền thực hiện thao tác này.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES, StaffProfile.Role.CONSULTANT)
def quan_tri_dashboard(request):
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        profile = None
    role = "admin" if request.user.is_superuser else profile.role
    month_values = [0] * 12
    today = timezone.localdate()
    revenue_by_month = (Order.objects.filter(status=Order.Status.COMPLETED, payment_status=Order.PaymentStatus.PAID,
                                               created_at__year=today.year)
                        .values_list("created_at__month").annotate(total=Sum("total"))) if role == "admin" else []
    for month, total in revenue_by_month:
        month_values[month - 1] = int(total or 0)
    products = list(SanPham.objects.select_related("danh_muc").order_by("so_luong", "ten_san_pham")[:5]) if role == "admin" else []
    order_count = Order.objects.count() if role in ("admin", "sales") else 0
    pending_orders = Order.objects.filter(status=Order.Status.PENDING).count() if role in ("admin", "sales") else 0
    new_order_count = Order.objects.filter(status=Order.Status.PENDING, created_at__date=today).count() if role == "sales" else 0
    needs_attention_count = Order.objects.filter(
        status=Order.Status.PENDING,
        created_at__lte=timezone.now() - timedelta(days=3),
    ).count() if role == "sales" else 0
    pending_review_count = ProductReview.objects.filter(is_visible=False, reported=False).count() if role in ("admin", "sales") else 0
    customer_count = CustomerProfile.objects.count() if role == "admin" else 0
    low_stock_products = list(SanPham.objects.filter(is_active=True, so_luong__lte=5).select_related("danh_muc").order_by("so_luong")[:5]) if role in ("admin", "sales") else []
    low_stock_count = SanPham.objects.filter(is_active=True, so_luong__lte=5).count() if role in ("admin", "sales") else 0
    stock_units = (SanPham.objects.filter(is_active=True).aggregate(total=Sum("so_luong"))["total"] or 0) if role in ("admin", "sales") else 0
    shipping_orders = Order.objects.filter(status=Order.Status.SHIPPING).count() if role == "sales" else 0
    preparing_orders = Order.objects.filter(status=Order.Status.CONFIRMED).count() if role == "sales" else 0
    consultant_cases = DecorConsultation.objects.filter(status__in=[
        DecorConsultation.Status.NEW, DecorConsultation.Status.ASSIGNED,
        DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER,
    ])
    if role == "consultant":
        consultant_cases = consultant_cases.filter(Q(assigned_to=request.user) | Q(assigned_to__isnull=True))
    new_consultations = consultant_cases.filter(status=DecorConsultation.Status.NEW).count()
    active_consultations = consultant_cases.filter(status__in=[DecorConsultation.Status.ASSIGNED, DecorConsultation.Status.WORKING]).count()
    waiting_consultations = consultant_cases.filter(status=DecorConsultation.Status.WAITING_CUSTOMER).count()
    priority_queryset = consultant_cases.filter(
        status__in=[DecorConsultation.Status.NEW, DecorConsultation.Status.ASSIGNED, DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER],
        created_at__lte=timezone.now() - timedelta(days=2),
    )
    priority_consultations = priority_queryset.count()
    proposal_revision_count = sum(
        1 for case in consultant_cases.filter(status__in=[DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER], budget__isnull=False).iterator()
        if _consultation_proposal_total(_saved_consultation_proposal(case.suggested_combo)) > case.budget
    )
    consultation_count = consultant_cases.count()
    needs_customer_info_count = Order.objects.filter(status=Order.Status.PENDING).filter(
        Q(customer__full_name="") | Q(customer__phone="") | Q(shipping_address="")
    ).distinct().count() if role == "sales" else 0
    recent_orders = list(Order.objects.select_related("customer").order_by("-created_at")[:5]) if role in ("admin", "sales") else []
    top_customers = list(CustomerProfile.objects.annotate(
        order_count=Count("orders", filter=~Q(orders__status=Order.Status.CANCELLED), distinct=True),
        spend=Sum("orders__total", filter=Q(orders__status=Order.Status.COMPLETED, orders__payment_status=Order.PaymentStatus.PAID)),
    ).order_by("-spend")[:5]) if role == "admin" else []
    # Sales dashboards must always represent actionable database rows, never the admin-only sample preview.
    demo_preview = bool(settings.ADMIN_DEMO_MODE and role == "admin" and order_count == 0)
    demo_products_preview = bool(settings.ADMIN_DEMO_MODE and role == "admin" and not SanPham.objects.exists())
    demo_consultation_count = DecorConsultation.objects.filter(status__in=[
        DecorConsultation.Status.NEW, DecorConsultation.Status.ASSIGNED,
        DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER,
    ]).count()
    if demo_preview:
        month_values = [8_000_000, 11_000_000, 9_000_000, 14_000_000, 12_000_000, 17_000_000, 15_000_000, 21_000_000, 19_000_000, 25_000_000, 22_000_000, 29_000_000]
        recent_orders = _demo_admin_orders()
        top_customers = [SimpleNamespace(full_name="Minh Anh", order_count=8, spend=4850000, user_id=1), SimpleNamespace(full_name="Gia Hân", order_count=6, spend=3260000, user_id=None), SimpleNamespace(full_name="Quốc Bảo", order_count=4, spend=2140000, user_id=2)]
        order_count, pending_orders, customer_count = 126, 8, 248
        new_order_count, needs_attention_count = 2, 1
        if demo_products_preview:
            low_stock_products = _demo_admin_products()
            low_stock_count, stock_units = len(DEMO_ADMIN_PRODUCTS), sum(item["so_luong"] for item in DEMO_ADMIN_PRODUCTS)
        demo_consultation_count = max(demo_consultation_count, 5)
    return render(request, "store/admin_dashboard.html", {
        "product_count": (len(DEMO_ADMIN_PRODUCTS) if demo_products_preview else SanPham.objects.count()) if role == "admin" else 0,
        "category_count": DanhMuc.objects.count() if role == "admin" else 0,
        "customer_count": customer_count,
        "low_stock_count": low_stock_count,
        "stock_units": stock_units,
        "low_stock_products": low_stock_products,
        "chart_data": month_values,
        "month_labels": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"],
        "revenue_total": sum(month_values), "order_count": order_count,
        "pending_orders": pending_orders,
        "new_order_count": new_order_count,
        "needs_attention_count": needs_attention_count,
        "pending_review_count": pending_review_count,
        "cancelled_order_count": sum(order.status == Order.Status.CANCELLED for order in _demo_admin_orders()) if demo_preview else Order.objects.filter(status=Order.Status.CANCELLED).count(),
        "shipping_orders": shipping_orders,
        "preparing_orders": preparing_orders,
        "new_consultations": new_consultations,
        "active_consultations": active_consultations,
        "waiting_consultations": waiting_consultations,
        "priority_consultations": priority_consultations,
        "proposal_revision_count": proposal_revision_count,
        "needs_customer_info_count": needs_customer_info_count,
        "recent_orders": recent_orders,
        "consultation_count": consultation_count if role == "consultant" else demo_consultation_count,
        "top_customers": top_customers,
        "role": role,
        "report_year": today.year,
        "demo_preview": demo_preview,
        "demo_products_preview": demo_products_preview,
    })


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES, StaffProfile.Role.CONSULTANT)
def quan_tri_tai_khoan(request):
    return render(request, "store/admin_account.html")


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_san_pham(request):
    products = SanPham.objects.select_related("danh_muc").order_by("ten_san_pham")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(ten_san_pham__icontains=query)
    demo_preview = bool(settings.ADMIN_DEMO_MODE and not SanPham.objects.exists())
    if demo_preview:
        products = _demo_admin_products()
        if query:
            products = [item for item in products if query.casefold() in item.ten_san_pham.casefold()]
    return render(request, "store/admin_products.html", {"products": products, "query": query, "demo_preview": demo_preview})


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_tao_san_pham(request):
    form = SanPhamForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        uploaded = request.FILES.get("hinh_anh")
        if uploaded and not (uploaded.content_type or "").startswith("image/"):
            form.add_error("hinh_anh", "Vui lòng chọn tệp ảnh.")
        else:
            saved.save()
            if saved.so_luong:
                InventoryAdjustment.objects.create(product=saved, quantity_delta=saved.so_luong, reason="Tồn kho khởi tạo khi tạo sản phẩm", actor=request.user)
            messages.success(request, "Đã thêm sản phẩm vào kho.")
            return redirect("quan_tri_san_pham")
    return render(request, "store/admin_product_form.html", {"form": form, "page_title": "Thêm sản phẩm", "editing": False})


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_sua_san_pham(request, product_id):
    product = get_object_or_404(SanPham, pk=product_id)
    form = SanPhamForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        uploaded = request.FILES.get("hinh_anh")
        if uploaded and not (uploaded.content_type or "").startswith("image/"):
            form.add_error("hinh_anh", "Vui lòng chọn tệp ảnh.")
        else:
            saved.save()
            messages.success(request, "Đã cập nhật sản phẩm.")
            return redirect("quan_tri_san_pham")
    return render(request, "store/admin_product_form.html", {"form": form, "page_title": "Chỉnh sửa sản phẩm", "editing": True, "product": product})


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_xoa_san_pham(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    product = get_object_or_404(SanPham, pk=product_id)
    product.is_active = False
    product.save(update_fields=["is_active"])
    messages.success(request, "Đã ngừng kinh doanh sản phẩm. Lịch sử đơn hàng và tồn kho được giữ lại.")
    return redirect("quan_tri_san_pham")


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_danh_muc(request):
    form = DanhMucForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã thêm danh mục.")
        return redirect("quan_tri_danh_muc")
    categories = DanhMuc.objects.order_by("ten_danh_muc")
    return render(request, "store/admin_categories.html", {"form": form, "categories": categories})


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES)
def quan_tri_don_hang(request):
    orders = Order.objects.select_related("customer", "staff_assignee").prefetch_related("items").order_by("-created_at")
    status = request.GET.get("status", "")
    search_term = request.GET.get("q", "").strip()
    payment_method = request.GET.get("payment", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    try:
        parsed_from = date.fromisoformat(date_from) if date_from else None
        parsed_to = date.fromisoformat(date_to) if date_to else None
    except ValueError:
        parsed_from = parsed_to = None
        messages.error(request, "Khoảng ngày lọc chưa hợp lệ.")
    all_orders = orders
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    if payment_method in Order.PaymentMethod.values:
        orders = orders.filter(payment_method=payment_method)
    if parsed_from:
        orders = orders.filter(created_at__date__gte=parsed_from)
    if parsed_to:
        orders = orders.filter(created_at__date__lte=parsed_to)
    if search_term:
        orders = orders.filter(Q(code__icontains=search_term) | Q(customer__full_name__icontains=search_term) | Q(customer__phone__icontains=search_term))
    needs_info = request.GET.get("needs_info") == "1"
    if needs_info:
        orders = orders.filter(Q(customer__full_name="") | Q(customer__phone="") | Q(shipping_address="")).distinct()
    profile = getattr(request.user, "staff_profile", None)
    role = "admin" if request.user.is_superuser else profile.role
    demo_preview = bool(settings.ADMIN_DEMO_MODE and role == "admin" and not Order.objects.exists())
    if demo_preview:
        all_orders = _demo_admin_orders()
        orders = all_orders
        if status in Order.Status.values:
            orders = [order for order in orders if order.status == status]
        if payment_method in Order.PaymentMethod.values:
            orders = [order for order in orders if order.payment_method == payment_method]
        if parsed_from:
            orders = [order for order in orders if order.created_at.date() >= parsed_from]
        if parsed_to:
            orders = [order for order in orders if order.created_at.date() <= parsed_to]
        if search_term:
            needle = search_term.casefold()
            orders = [order for order in orders if needle in f"{order.code} {order.customer.full_name} {order.customer.phone}".casefold()]
        if needs_info:
            orders = [order for order in orders if not order.customer.full_name or not order.customer.phone or not order.shipping_address]
    for order in all_orders:
        order.needs_attention = (
            order.status == Order.Status.PENDING
            and order.created_at <= timezone.now() - timedelta(days=3)
        )
    cancelled_order_count = sum(order.status == Order.Status.CANCELLED for order in all_orders) if demo_preview else Order.objects.filter(status=Order.Status.CANCELLED).count()
    sales_staff = StaffProfile.objects.filter(role=StaffProfile.Role.SALES, is_enabled=True).select_related("user") if role == "admin" else []
    return render(request, "store/admin_orders.html", {
        "orders": orders, "statuses": Order.Status.choices,
        "payment_methods": Order.PaymentMethod.choices,
        "selected_status": status, "selected_payment": payment_method,
        "date_from": date_from, "date_to": date_to,
        "sales_staff": sales_staff, "demo_preview": demo_preview,
        "query": search_term, "cancelled_order_count": cancelled_order_count, "role": role,
        "needs_info": needs_info,
    })


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES)
def quan_tri_chi_tiet_don(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("customer", "staff_assignee")
        .prefetch_related("items", "notifications", "inventory_events__product", "inventory_events__actor"),
        pk=order_id,
    )
    profile = getattr(request.user, "staff_profile", None)
    role = "admin" if request.user.is_superuser else profile.role
    return render(request, "store/admin_order_detail.html", {
        "order": order,
        "role": role,
        "can_assign": role == StaffProfile.Role.ADMIN,
        "inventory_events": order.inventory_events.all(),
    })


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES)
def quan_tri_cap_nhat_don(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    order = get_object_or_404(Order, pk=order_id)
    action = request.POST.get("action")
    notification_text = None
    try:
        if action == "assign":
            profile = getattr(request.user, "staff_profile", None)
            if not request.user.is_superuser and (not profile or profile.role != StaffProfile.Role.ADMIN):
                return HttpResponseForbidden("Chỉ quản trị viên được phân công đơn hàng.")
            staff_profile = get_object_or_404(StaffProfile, pk=request.POST.get("staff_profile"), role=StaffProfile.Role.SALES, is_enabled=True)
            order.staff_assignee = staff_profile.user
            order.save(update_fields=["staff_assignee", "updated_at"])
        elif action == "confirm":
            confirm_order(order.pk, request.user)
            notification_text = f"Đơn hàng {order.code} đã được duyệt thành công. Đơn COD sẽ thanh toán khi nhận hàng."
        elif action == "cancel":
            cancel_order(order.pk, request.user)
            notification_text = f"Đơn hàng {order.code} đã được hủy. Nếu cần hỗ trợ, bạn có thể liên hệ Re:Room."
        elif action == "shipping" and order.status == Order.Status.CONFIRMED:
            order.status = Order.Status.SHIPPING
            order.save(update_fields=["status", "updated_at"])
            notification_text = f"Đơn hàng {order.code} đang được giao đến bạn."
        elif action == "complete" and order.status == Order.Status.SHIPPING:
            order.status = Order.Status.COMPLETED
            order.save(update_fields=["status", "updated_at"])
            notification_text = f"Đơn hàng {order.code} đã giao thành công. Cảm ơn bạn đã mua sắm tại Re:Room!"
        elif action == "collect_cod":
            mark_cod_collected(order.pk, request.user)
            notification_text = f"Re:Room đã ghi nhận thanh toán COD cho đơn hàng {order.code}."
        else:
            raise ValidationError("Thao tác không hợp lệ với trạng thái đơn hiện tại.")
        messages.success(request, "Đã cập nhật đơn hàng.")
        if notification_text:
            OrderNotification.objects.create(order=order, message=notification_text)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("quan_tri_chi_tiet_don", order_id=order.pk)


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_khach_hang(request):
    customers = CustomerProfile.objects.annotate(
        order_count=Count("orders", filter=~Q(orders__status=Order.Status.CANCELLED), distinct=True),
        spend=Sum("orders__total", filter=Q(orders__status=Order.Status.COMPLETED, orders__payment_status=Order.PaymentStatus.PAID)),
    ).order_by("-spend")
    query = request.GET.get("q", "").strip()
    if query:
        customers = customers.filter(Q(full_name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query))
    demo_preview = bool(settings.ADMIN_DEMO_MODE and not customers.exists())
    if demo_preview:
        customers = [
            SimpleNamespace(full_name="Minh Anh", user_id=1, email="minhanh.demo@example.com", phone="0901 234 567", order_count=8, spend=4_850_000, last_order_at=timezone.now() - timedelta(days=1), is_demo=True),
            SimpleNamespace(full_name="Gia Hân", user_id=None, email="g.han.demo@example.com", phone="0902 345 678", order_count=6, spend=3_260_000, last_order_at=timezone.now() - timedelta(days=3), is_demo=True),
            SimpleNamespace(full_name="Quốc Bảo", user_id=2, email="quocbao.demo@example.com", phone="0903 456 789", order_count=4, spend=2_140_000, last_order_at=timezone.now() - timedelta(days=5), is_demo=True),
            SimpleNamespace(full_name="Thảo Vy", user_id=None, email="thaovy.demo@example.com", phone="0904 567 890", order_count=2, spend=860_000, last_order_at=timezone.now() - timedelta(days=8), is_demo=True),
        ]
        if query:
            needle = query.casefold()
            customers = [customer for customer in customers if needle in " ".join((customer.full_name, customer.email, customer.phone)).casefold()]
    return render(request, "store/admin_customers.html", {"customers": customers, "query": query, "demo_preview": demo_preview})


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_vouchers(request):
    form = VoucherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        voucher = form.save(commit=False)
        voucher.created_by = request.user
        voucher.status = Voucher.Status.PENDING
        voucher.save()
        messages.success(request, "Voucher đã tạo và đang chờ duyệt.")
        return redirect("quan_tri_vouchers")
    return render(request, "store/admin_vouchers.html", {"form": form, "vouchers": Voucher.objects.order_by("-starts_at")})


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_duyet_voucher(request, voucher_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if voucher.status != Voucher.Status.PENDING or voucher.ends_at <= timezone.now():
        messages.error(request, "Chỉ duyệt voucher đang chờ và còn hạn.")
    else:
        voucher.status = Voucher.Status.APPROVED
        voucher.approved_by = request.user
        voucher.save(update_fields=["status", "approved_by"])
        messages.success(request, "Voucher đã được duyệt.")
    return redirect("quan_tri_vouchers")


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES)
def quan_tri_ton_kho(request):
    products = SanPham.objects.select_related("danh_muc").order_by("so_luong", "ten_san_pham")
    profile = getattr(request.user, "staff_profile", None)
    role = StaffProfile.Role.ADMIN if request.user.is_superuser else profile.role
    can_adjust = role == StaffProfile.Role.ADMIN
    demo_preview = bool(settings.ADMIN_DEMO_MODE and role == StaffProfile.Role.ADMIN and not SanPham.objects.exists())
    if request.method == "POST":
        if not can_adjust:
            return HttpResponseForbidden("Nhân viên bán hàng chỉ được tra cứu tồn kho.")
        if demo_preview:
            messages.info(request, "Đây là dữ liệu mẫu, chưa thể điều chỉnh tồn kho.")
            return redirect("quan_tri_ton_kho")
        try:
            delta = int(request.POST.get("delta", "0"))
            reason = request.POST.get("reason", "").strip()
            if delta == 0 or not reason:
                raise ValueError
        except ValueError:
            messages.error(request, "Số lượng điều chỉnh hoặc lý do chưa hợp lệ.")
        else:
            with transaction.atomic():
                product = get_object_or_404(SanPham.objects.select_for_update(), pk=request.POST.get("product_id"))
                if product.so_luong + delta < 0:
                    messages.error(request, "Không thể giảm tồn kho thấp hơn 0.")
                else:
                    product.so_luong += delta
                    product.save(update_fields=["so_luong"])
                    InventoryAdjustment.objects.create(product=product, quantity_delta=delta, reason=reason, actor=request.user)
                    messages.success(request, "Đã ghi nhận điều chỉnh tồn kho.")
        return redirect("quan_tri_ton_kho")
    query = request.GET.get("q", "").strip()
    if query and not demo_preview:
        matches = (
            Q(ten_san_pham__icontains=query)
            | Q(danh_muc__ten_danh_muc__icontains=query)
            | Q(phan_loai__icontains=query)
        )
        product_number = query.strip().upper().removeprefix("SP-")
        if product_number.isdigit():
            matches |= Q(pk=int(product_number))
        products = products.filter(matches)
    if demo_preview:
        products = _demo_admin_products()
        if query:
            products = [item for item in products if query.casefold() in f"{item.ten_san_pham} {item.danh_muc.ten_danh_muc}".casefold()]
    products = list(products)
    product_ids = [product.pk for product in products if product.pk]
    variant_rows = OrderItem.objects.filter(product_id__in=product_ids).exclude(variant="").values_list("product_id", "variant").distinct()
    variant_map = {}
    for product_id, variant in variant_rows:
        variant_map.setdefault(product_id, []).append(variant)
    for product in products:
        product.display_code = f"SP-{product.pk:05d}" if product.pk else "Mẫu demo"
        configured_variants = [value.strip() for value in (getattr(product, "phan_loai", "") or "").split(",") if value.strip()]
        product.variant_summary = ", ".join(configured_variants or variant_map.get(product.pk, [])) or "Chưa cập nhật phân loại"
    events = InventoryAdjustment.objects.select_related("product", "actor").order_by("-created_at")[:20]
    return render(request, "store/admin_inventory.html", {
        "products": products, "events": events, "demo_preview": demo_preview,
        "query": query, "role": role, "can_adjust": can_adjust,
    })


@_roles_required(StaffProfile.Role.ADMIN)
def quan_tri_nhan_vien(request):
    account_form = StaffAccountForm(prefix="create")
    if request.method == "POST":
        if request.POST.get("action") == "create_staff":
            account_form = StaffAccountForm(request.POST, prefix="create")
            if account_form.is_valid():
                data = account_form.cleaned_data
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=data["username"], email=data["email"],
                        first_name=data["first_name"], password=data["password"], is_staff=True,
                    )
                    StaffProfile.objects.create(user=user, role=data["role"], is_enabled=True)
                messages.success(request, "Đã tạo tài khoản nhân viên. Hãy gửi thông tin đăng nhập riêng cho nhân viên.")
                return redirect("quan_tri_nhan_vien")
        else:
            profile = get_object_or_404(StaffProfile, pk=request.POST.get("profile_id"))
            role = request.POST.get("role")
            if role not in StaffProfile.Role.values:
                messages.error(request, "Vai trò không hợp lệ.")
            else:
                profile.role = role
                profile.is_enabled = request.POST.get("enabled") == "1"
                profile.save(update_fields=["role", "is_enabled"])
                profile.user.is_active = profile.is_enabled
                profile.user.save(update_fields=["is_active"])
                messages.success(request, "Đã cập nhật quyền nhân viên.")
            return redirect("quan_tri_nhan_vien")
    return render(request, "store/admin_staff.html", {"profiles": StaffProfile.objects.select_related("user").order_by("user__username"), "roles": StaffProfile.Role.choices, "account_form": account_form})


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.CONSULTANT)
def quan_tri_tu_van(request):
    profile = getattr(request.user, "staff_profile", None)
    role = StaffProfile.Role.ADMIN if request.user.is_superuser else profile.role
    all_cases = DecorConsultation.objects.select_related("customer", "assigned_to").order_by("-created_at")
    if role == StaffProfile.Role.CONSULTANT:
        all_cases = all_cases.filter(Q(assigned_to=request.user) | Q(assigned_to__isnull=True))
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    room_type = request.GET.get("room_type", "")
    priority_only = request.GET.get("priority") == "1"
    revision_only = request.GET.get("needs_revision") == "1"
    cases = all_cases
    if status in DecorConsultation.Status.values:
        cases = cases.filter(status=status)
    if query:
        cases = cases.filter(Q(code__icontains=query) | Q(customer_name__icontains=query) | Q(contact__icontains=query))
    if room_type:
        cases = cases.filter(room_type=room_type)
    if priority_only:
        cases = cases.filter(
            status__in=[DecorConsultation.Status.NEW, DecorConsultation.Status.ASSIGNED, DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER],
            created_at__lte=timezone.now() - timedelta(days=2),
        )
    cases = list(cases)
    for case in cases:
        proposal = _saved_consultation_proposal(case.suggested_combo)
        case.proposal_total = _consultation_proposal_total(proposal)
        case.proposal_summary = ", ".join(row.get("name", "Sản phẩm") for row in proposal) or case.suggested_combo
        case.needs_revision = bool(case.budget and case.proposal_total > case.budget)
    if revision_only:
        cases = [case for case in cases if case.needs_revision]
    dashboard_cases = list(all_cases)
    context = {
        "consultations": cases,
        "statuses": DecorConsultation.Status.choices,
        "room_types": DecorConsultation.objects.order_by("room_type").values_list("room_type", flat=True).distinct(),
        "selected_status": status,
        "selected_room_type": room_type,
        "query": query,
        "priority_only": priority_only,
        "revision_only": revision_only,
        "new_count": sum(case.status == DecorConsultation.Status.NEW for case in dashboard_cases),
        "working_count": sum(case.status in (DecorConsultation.Status.ASSIGNED, DecorConsultation.Status.WORKING) for case in dashboard_cases),
        "waiting_count": sum(case.status == DecorConsultation.Status.WAITING_CUSTOMER for case in dashboard_cases),
        "priority_count": sum(case.status in (DecorConsultation.Status.NEW, DecorConsultation.Status.ASSIGNED, DecorConsultation.Status.WORKING, DecorConsultation.Status.WAITING_CUSTOMER) and case.created_at <= timezone.now() - timedelta(days=2) for case in dashboard_cases),
        "role": role,
    }
    return render(request, "store/admin_consultations.html", context)


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.CONSULTANT)
def quan_tri_chi_tiet_tu_van(request, case_id):
    profile = getattr(request.user, "staff_profile", None)
    role = StaffProfile.Role.ADMIN if request.user.is_superuser else profile.role
    case = get_object_or_404(DecorConsultation.objects.select_related("customer", "assigned_to"), pk=case_id)
    if role == StaffProfile.Role.CONSULTANT and case.assigned_to_id not in (None, request.user.pk):
        return HttpResponseForbidden("Yêu cầu đang được nhân viên khác phụ trách.")

    if request.method == "POST":
        action = request.POST.get("action", "")
        with transaction.atomic():
            case = DecorConsultation.objects.select_for_update().select_related("assigned_to").get(pk=case_id)
            if role == StaffProfile.Role.CONSULTANT and case.assigned_to_id not in (None, request.user.pk):
                return HttpResponseForbidden("Yêu cầu vừa được nhân viên khác tiếp nhận.")

            def log_update(note):
                timestamp = timezone.localtime().strftime("%d/%m/%Y %H:%M")
                line = f"[{timestamp}] {request.user.username}: {note}"
                case.conversation_log = f"{case.conversation_log.rstrip()}\n{line}".strip()

            if action == "assign":
                if role != StaffProfile.Role.ADMIN:
                    if case.assigned_to_id is None:
                        case.assigned_to = request.user
                        case.status = DecorConsultation.Status.ASSIGNED
                        log_update("Đã nhận phụ trách yêu cầu.")
                    else:
                        messages.info(request, "Yêu cầu này đã được bạn tiếp nhận.")
                        return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                else:
                    assignee_id = request.POST.get("assignee_id", "").strip()
                    if assignee_id and not assignee_id.isdigit():
                        messages.error(request, "Nh\u00e2n vi\u00ean \u0111\u01b0\u1ee3c ch\u1ecdn kh\u00f4ng h\u1ee3p l\u1ec7.")
                        return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                    if assignee_id:
                        assignee = get_object_or_404(StaffProfile, pk=assignee_id, role=StaffProfile.Role.CONSULTANT, is_enabled=True)
                        case.assigned_to = assignee.user
                        if case.status == DecorConsultation.Status.NEW:
                            case.status = DecorConsultation.Status.ASSIGNED
                        log_update(f"Đã phân công cho {assignee.user.username}.")
                    else:
                        case.assigned_to = None
                        if case.status == DecorConsultation.Status.ASSIGNED:
                            case.status = DecorConsultation.Status.NEW
                        log_update("Đã bỏ phân công yêu cầu.")
                case.save(update_fields=["assigned_to", "status", "conversation_log"])
                messages.success(request, "Đã cập nhật người phụ trách.")
            elif action in ("save_proposal", "send_proposal"):
                selected_ids = list(dict.fromkeys(request.POST.getlist("product_id")))
                if any(not product_id.isdigit() for product_id in selected_ids):
                    messages.error(request, "Danh s\u00e1ch s\u1ea3n ph\u1ea9m kh\u00f4ng h\u1ee3p l\u1ec7. T\u1ea3i l\u1ea1i trang r\u1ed3i ch\u1ecdn l\u1ea1i nh\u00e9.")
                    return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                products = list(SanPham.objects.filter(pk__in=selected_ids, is_active=True).select_related("danh_muc")) if selected_ids else []
                if len(products) != len(selected_ids):
                    messages.error(request, "Một sản phẩm vừa bị ẩn hoặc không còn trong danh mục. Tải lại trang rồi chọn lại nha.")
                    return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                proposal = []
                for product in products:
                    try:
                        quantity = int(request.POST.get(f"quantity_{product.pk}", "1"))
                    except (TypeError, ValueError):
                        quantity = 0
                    if quantity < 1 or quantity > 99:
                        messages.error(request, f"Số lượng của {product.ten_san_pham} cần từ 1 đến 99.")
                        return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                    proposal.append({
                        "product_id": product.pk,
                        "name": product.ten_san_pham,
                        "unit_price": product.gia_ban,
                        "quantity": quantity,
                    })
                if action == "send_proposal" and not proposal:
                    messages.error(request, "Chọn ít nhất một sản phẩm trước khi gửi phương án.")
                    return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                case.suggested_combo = json.dumps(proposal, ensure_ascii=False)
                if role == StaffProfile.Role.CONSULTANT and case.assigned_to_id is None:
                    case.assigned_to = request.user
                case.status = DecorConsultation.Status.WAITING_CUSTOMER if action == "send_proposal" else DecorConsultation.Status.WORKING
                total = _consultation_proposal_total(proposal)
                log_update(
                    f"Đã đánh dấu gửi phương án gồm {len(proposal)} sản phẩm, tổng {total:,}đ; chuyển sang chờ khách phản hồi."
                    if action == "send_proposal" else f"Đã lưu bản nháp combo gồm {len(proposal)} sản phẩm, tổng {total:,}đ."
                )
                case.save(update_fields=["suggested_combo", "assigned_to", "status", "conversation_log"])
                messages.success(request, "Đã lưu và chuyển trạng thái chờ khách phản hồi." if action == "send_proposal" else "Đã lưu bản nháp phương án decor.")
            elif action == "update_status":
                new_status = request.POST.get("status", "")
                if new_status not in DecorConsultation.Status.values:
                    messages.error(request, "Trạng thái yêu cầu không hợp lệ.")
                    return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                old_status = case.get_status_display()
                case.status = new_status
                if role == StaffProfile.Role.CONSULTANT and case.assigned_to_id is None:
                    case.assigned_to = request.user
                log_update(f"Đổi trạng thái từ {old_status} sang {case.get_status_display()}.")
                case.save(update_fields=["assigned_to", "status", "conversation_log"])
                messages.success(request, "Đã cập nhật trạng thái tư vấn.")
            elif action == "add_note":
                note = request.POST.get("message", "").strip()[:1000]
                if not note:
                    messages.error(request, "Nhập nội dung trao đổi trước khi lưu.")
                    return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)
                log_update(note)
                case.save(update_fields=["conversation_log"])
                messages.success(request, "Đã thêm ghi chú vào lịch sử trao đổi.")
            else:
                messages.error(request, "Thao tác tư vấn không hợp lệ.")
        return redirect("quan_tri_chi_tiet_tu_van", case_id=case.pk)

    saved_proposal = _saved_consultation_proposal(case.suggested_combo)
    saved_by_id = {int(row["product_id"]): row for row in saved_proposal}
    products = list(SanPham.objects.filter(is_active=True).select_related("danh_muc").order_by("ten_san_pham"))
    for product in products:
        saved_row = saved_by_id.get(product.pk, {})
        product.proposal_selected = bool(saved_row)
        product.proposal_quantity = saved_row.get("quantity", 1)
    saved_total = _consultation_proposal_total(saved_proposal)
    legacy_proposal_note = case.suggested_combo if case.suggested_combo and not saved_proposal else ""
    return render(request, "store/admin_consultation_detail.html", {
        "case": case,
        "products": products,
        "saved_proposal": saved_proposal,
        "saved_total": saved_total,
        "legacy_proposal_note": legacy_proposal_note,
        "proposal_over_budget": bool(case.budget and saved_total > case.budget),
        "statuses": DecorConsultation.Status.choices,
        "consultant_staff": StaffProfile.objects.filter(role=StaffProfile.Role.CONSULTANT, is_enabled=True).select_related("user"),
        "role": role,
    })


@_roles_required(StaffProfile.Role.ADMIN, StaffProfile.Role.SALES)
def quan_tri_danh_gia(request):
    if request.method == "POST":
        review = get_object_or_404(ProductReview, pk=request.POST.get("review_id"))
        action = request.POST.get("action")
        if action == "approve":
            review.is_visible, review.reported = True, False
            review.save(update_fields=["is_visible", "reported"])
            messages.success(request, "Đánh giá đã được duyệt và hiển thị trên sản phẩm.")
        elif action == "hide":
            review.is_visible = False
            review.save(update_fields=["is_visible"])
            messages.success(request, "Đánh giá đã được ẩn khỏi trang sản phẩm.")
        elif action == "report":
            review.reported = True
            review.is_visible = False
            review.save(update_fields=["reported", "is_visible"])
            messages.success(request, "Đánh giá đã được gắn cờ và ẩn để kiểm tra.")
        elif action == "clear_report":
            review.reported = False
            review.save(update_fields=["reported"])
            messages.success(request, "Đã gỡ cờ báo cáo.")
        else:
            messages.error(request, "Thao tác đánh giá không hợp lệ.")
        return redirect("quan_tri_danh_gia")
    reviews = ProductReview.objects.select_related("customer", "order_item", "order_item__product").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    visibility = request.GET.get("visibility", "")
    reported = request.GET.get("reported", "")
    if query:
        reviews = reviews.filter(
            Q(content__icontains=query)
            | Q(customer__full_name__icontains=query)
            | Q(order_item__product_name__icontains=query)
            | Q(order_item__order__code__icontains=query)
        )
    if visibility == "visible":
        reviews = reviews.filter(is_visible=True)
    elif visibility == "pending":
        reviews = reviews.filter(is_visible=False, reported=False)
    elif visibility == "hidden":
        reviews = reviews.filter(is_visible=False)
    if reported == "yes":
        reviews = reviews.filter(reported=True)
    elif reported == "no":
        reviews = reviews.filter(reported=False)
    return render(request, "store/admin_reviews.html", {
        "reviews": reviews, "query": query, "selected_visibility": visibility,
        "selected_reported": reported,
        "pending_review_count": ProductReview.objects.filter(is_visible=False, reported=False).count(),
        "reported_review_count": ProductReview.objects.filter(reported=True).count(),
    })




def thong_bao_don_hang(request):
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if not request.user.is_authenticated or request.user.is_staff:
        return JsonResponse({"notifications": [], "unread": 0})
    notifications = OrderNotification.objects.filter(
        order__customer__user=request.user,
        is_read=False,
    ).select_related("order").order_by("-created_at")
    if request.method == "POST":
        try:
            ids = json.loads(request.body).get("ids", [])
            ids = [int(value) for value in ids]
        except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Y\\u00eau c\\u1ea7u kh\\u00f4ng h\\u1ee3p l\\u1ec7."}, status=400)
        notifications.filter(pk__in=ids).update(is_read=True)
        return JsonResponse({"ok": True})
    unread = notifications.count()
    items = [{
        "id": item.pk,
        "order_id": item.order.code,
        "message": item.message,
        "created_at": item.created_at.isoformat(),
    } for item in notifications[:10]]
    return JsonResponse({"notifications": items, "unread": unread})


def _staff_landing(user):
    if user.is_superuser:
        return "quan_tri_dashboard"
    try:
        profile = user.staff_profile
        if profile.is_enabled and profile.role == StaffProfile.Role.ADMIN:
            return "quan_tri_dashboard"
    except StaffProfile.DoesNotExist:
        pass
    if _has_sales_access(user):
        return "ban_hang_dashboard"
    if _has_cskh_access(user):
        return "cskh_hop_thu"
    return "trang_chu"


def _has_sales_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profile = user.staff_profile
        if profile.is_enabled and profile.user.is_active and profile.role in (StaffProfile.Role.SALES, StaffProfile.Role.ADMIN):
            return True
    except StaffProfile.DoesNotExist:
        pass
    try:
        return user.is_active and user.ho_so_nhan_vien.bo_phan == HoSoNhanVien.BoPhan.BAN_HANG
    except HoSoNhanVien.DoesNotExist:
        return False


def _has_cskh_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profile = user.staff_profile
        if profile.is_enabled and profile.user.is_active and profile.role in (StaffProfile.Role.CONSULTANT, StaffProfile.Role.ADMIN):
            return True
    except StaffProfile.DoesNotExist:
        pass
    try:
        return user.is_active and user.ho_so_nhan_vien.bo_phan == HoSoNhanVien.BoPhan.CSKH
    except HoSoNhanVien.DoesNotExist:
        return False


def cskh_dang_nhap(request):
    return redirect("dang_nhap")


@staff_member_required(login_url="dang_nhap")
def cskh_hop_thu(request):
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("Tài khoản này không thuộc bộ phận CSKH.")
    conversations = list(
        CustomerServiceConversation.objects.select_related("customer", "assigned_to")
        .order_by("-updated_at")
    )
    for conversation in conversations:
        conversation.unread_count = conversation.messages.filter(
            sender_role=CustomerServiceMessage.SenderRole.CUSTOMER,
            is_read=False,
        ).count()
    selected_id = request.GET.get("cuoc_tro_chuyen")
    selected = next((item for item in conversations if str(item.pk) == selected_id), None)
    if selected:
        selected.messages.filter(
            sender_role=CustomerServiceMessage.SenderRole.CUSTOMER,
            is_read=False,
        ).update(is_read=True)
        selected.assigned_to = selected.assigned_to or request.user
        selected.save(update_fields=["assigned_to"])
    return render(request, "store/cskh_inbox.html", {
        "conversations": conversations,
        "selected_conversation": selected,
        "products": SanPham.objects.order_by("ten_san_pham"),
        "pending_order_count": Order.objects.filter(status=Order.Status.PENDING).count(),
    })


def cskh_don_hang(request):
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("T\u00e0i kho\u1ea3n n\u00e0y kh\u00f4ng thu\u1ed9c b\u1ed9 ph\u1eadn CSKH.")
    orders = Order.objects.select_related("customer").prefetch_related("items").order_by("-created_at")
    return render(request, "store/cskh_orders.html", {
        "orders": orders,
        "pending_order_count": Order.objects.filter(status=Order.Status.PENDING).count(),
    })


def cskh_duyet_don_hang(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("T\u00e0i kho\u1ea3n n\u00e0y kh\u00f4ng thu\u1ed9c b\u1ed9 ph\u1eadn CSKH.")
    messages.info(request, "Nh\u00e2n vi\u00ean CSKH tra c\u1ee9u h\u1ed3 s\u01a1; nh\u00e2n vi\u00ean b\u00e1n h\u00e0ng ph\u1ee5 tr\u00e1ch duy\u1ec7t \u0111\u01a1n.")
    return redirect("cskh_don_hang")


def ban_hang_dashboard(request):
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang n\u00e0y d\u00e0nh cho nh\u00e2n vi\u00ean b\u00e1n h\u00e0ng.")
    orders = Order.objects.select_related("customer").order_by("-created_at")
    return render(request, "store/sales_dashboard.html", {
        "product_count": SanPham.objects.filter(is_active=True).count(),
        "new_order_count": orders.filter(status=Order.Status.PENDING).count(),
        "orders_to_process": orders.filter(status=Order.Status.CONFIRMED).count(),
        "orders_shipping": orders.filter(status=Order.Status.SHIPPING).count(),
        "cancelled_orders": orders.filter(status=Order.Status.CANCELLED).count(),
        "recent_orders": orders[:5],
    })


def ban_hang_don_hang(request):
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang n\u00e0y d\u00e0nh cho nh\u00e2n vi\u00ean b\u00e1n h\u00e0ng.")
    orders = Order.objects.select_related("customer").prefetch_related("items").order_by("-created_at")
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    payment = request.GET.get("payment", "")
    if search:
        orders = orders.filter(Q(code__icontains=search) | Q(customer__full_name__icontains=search) | Q(customer__phone__icontains=search))
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    if payment in Order.PaymentMethod.values:
        orders = orders.filter(payment_method=payment)
    return render(request, "store/sales_orders.html", {
        "orders": orders,
        "statuses": Order.Status.choices,
        "payment_methods": Order.PaymentMethod.choices,
        "selected_status": status,
        "selected_payment": payment,
        "search": search,
    })


def ban_hang_cap_nhat_don(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang n\u00e0y d\u00e0nh cho nh\u00e2n vi\u00ean b\u00e1n h\u00e0ng.")
    order = get_object_or_404(Order, pk=order_id)
    action = request.POST.get("action", "")
    notification_text = None
    try:
        if action == "confirm":
            confirm_order(order.pk, request.user)
            notification_text = f"\u0110\u01a1n h\u00e0ng {order.code} \u0111\u00e3 \u0111\u01b0\u1ee3c duy\u1ec7t. \u0110\u01a1n COD thanh to\u00e1n khi nh\u1eadn h\u00e0ng."
        elif action == "cancel":
            cancel_order(order.pk, request.user)
            notification_text = f"\u0110\u01a1n h\u00e0ng {order.code} \u0111\u00e3 \u0111\u01b0\u1ee3c h\u1ee7y."
        elif action == "shipping" and order.status == Order.Status.CONFIRMED:
            order.status = Order.Status.SHIPPING
            order.save(update_fields=["status", "updated_at"])
            notification_text = f"\u0110\u01a1n h\u00e0ng {order.code} \u0111ang \u0111\u01b0\u1ee3c giao."
        elif action == "complete" and order.status == Order.Status.SHIPPING:
            order.status = Order.Status.COMPLETED
            order.save(update_fields=["status", "updated_at"])
            notification_text = f"\u0110\u01a1n h\u00e0ng {order.code} \u0111\u00e3 giao th\u00e0nh c\u00f4ng."
        elif action == "collect_cod":
            mark_cod_collected(order.pk, request.user)
            notification_text = f"Re:Room \u0111\u00e3 ghi nh\u1eadn thu COD cho \u0111\u01a1n {order.code}."
        else:
            raise ValidationError("Thao t\u00e1c kh\u00f4ng h\u1ee3p l\u1ec7 v\u1edbi tr\u1ea1ng th\u00e1i \u0111\u01a1n hi\u1ec7n t\u1ea1i.")
        messages.success(request, "\u0110\u00e3 c\u1eadp nh\u1eadt \u0111\u01a1n h\u00e0ng.")
        if notification_text:
            OrderNotification.objects.create(order=order, message=notification_text)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("ban_hang_don_hang")


@login_required(login_url="dang_nhap")
def ho_tro_khach_hang(request):
    if request.user.is_staff:
        return redirect(_staff_landing(request.user))
    conversation, _ = CustomerServiceConversation.objects.get_or_create(customer=request.user)
    conversation.messages.filter(
        sender_role=CustomerServiceMessage.SenderRole.STAFF,
        is_read=False,
    ).update(is_read=True)
    return render(request, "store/customer_support.html", {"conversation": conversation})


def _message_json(message):
    product = message.suggested_product
    return {
        "id": message.pk,
        "sender_role": message.sender_role,
        "sender": message.sender.get_full_name() or message.sender.username,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
        "product": ({
            "name": product.ten_san_pham,
            "url": f"/san-pham/{product.pk}/",
            "price": product.gia_ban,
        } if product else None),
    }


@login_required(login_url="dang_nhap")
def customer_support_api(request):
    if request.user.is_staff:
        return JsonResponse({"error": "Tài khoản nhân viên không dùng hộp thư khách hàng."}, status=403)
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    conversation, _ = CustomerServiceConversation.objects.get_or_create(customer=request.user)
    if request.method == "GET":
        conversation.messages.filter(
            sender_role=CustomerServiceMessage.SenderRole.STAFF,
            is_read=False,
        ).update(is_read=True)
        return JsonResponse({"messages": [
            _message_json(message)
            for message in conversation.messages.select_related("sender", "suggested_product")
        ]})
    try:
        body = str(json.loads(request.body).get("body", "")).strip()
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Nội dung tin nhắn không hợp lệ."}, status=400)
    if not body or len(body) > 3000:
        return JsonResponse({"error": "Tin nhắn cần có nội dung và không dài quá 3.000 ký tự."}, status=400)
    message = CustomerServiceMessage.objects.create(
        conversation=conversation,
        sender=request.user,
        sender_role=CustomerServiceMessage.SenderRole.CUSTOMER,
        body=body,
    )
    return JsonResponse({"message": _message_json(message)})


@staff_member_required(login_url="dang_nhap")
def cskh_conversation_api(request, conversation_id):
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("Tài khoản này không thuộc bộ phận CSKH.")
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    conversation = get_object_or_404(
        CustomerServiceConversation.objects.select_related("customer"), pk=conversation_id,
    )
    if request.method == "GET":
        conversation.messages.filter(
            sender_role=CustomerServiceMessage.SenderRole.CUSTOMER,
            is_read=False,
        ).update(is_read=True)
        return JsonResponse({"messages": [
            _message_json(message)
            for message in conversation.messages.select_related("sender", "suggested_product")
        ]})
    try:
        data = json.loads(request.body)
        body = str(data.get("body", "")).strip()
        product_id = data.get("product_id")
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Nội dung tư vấn không hợp lệ."}, status=400)
    if not body or len(body) > 3000:
        return JsonResponse({"error": "Tin nhắn cần có nội dung và không dài quá 3.000 ký tự."}, status=400)
    product = get_object_or_404(SanPham, pk=product_id) if product_id else None
    conversation.assigned_to = conversation.assigned_to or request.user
    conversation.save(update_fields=["assigned_to"])
    message = CustomerServiceMessage.objects.create(
        conversation=conversation,
        sender=request.user,
        sender_role=CustomerServiceMessage.SenderRole.STAFF,
        body=body,
        suggested_product=product,
    )
    return JsonResponse({"message": _message_json(message)})


@staff_member_required(login_url="dang_nhap")
def cskh_thong_bao_api(request):
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("Tài khoản này không thuộc bộ phận CSKH.")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    unread = CustomerServiceMessage.objects.filter(
        sender_role=CustomerServiceMessage.SenderRole.CUSTOMER,
        is_read=False,
    ).count()
    return JsonResponse({"unread": unread})


@staff_member_required(login_url="dang_nhap")
def cskh_de_xuat_san_pham(request):
    if request.user.is_superuser or not _has_cskh_access(request.user):
        return HttpResponseForbidden("Trang này dành cho nhân viên CSKH.")
    form = SanPhamForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded = request.FILES.get("hinh_anh")
        if uploaded and not (uploaded.content_type or "").startswith("image/"):
            form.add_error("hinh_anh", "Vui lòng chọn tệp ảnh.")
        else:
            proposed = form.save(commit=False)
            DeXuatSanPham.objects.create(
                ten_san_pham=proposed.ten_san_pham,
                gia_ban=proposed.gia_ban,
                danh_muc=proposed.danh_muc,
                mo_ta=proposed.mo_ta,
                so_luong=proposed.so_luong,
                hinh_anh=uploaded or None,
                nguoi_tao=request.user,
            )
            messages.success(request, "Bài đăng đã gửi admin duyệt. Sản phẩm sẽ vào kho và hiển thị sau khi được duyệt.")
            return redirect("cskh_de_xuat_san_pham")
    return render(request, "store/cskh_product_submissions.html", {
        "form": form,
        "submissions": DeXuatSanPham.objects.filter(nguoi_tao=request.user).select_related("danh_muc"),
    })


@staff_member_required(login_url="dang_nhap")
def quan_tri_de_xuat_san_pham(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ admin mới được duyệt bài đăng.")
    submissions = DeXuatSanPham.objects.select_related("danh_muc", "nguoi_tao")
    return render(request, "store/admin_product_submissions.html", {
        "submissions": submissions,
        "pending_count": submissions.filter(trang_thai=DeXuatSanPham.TrangThai.CHO_DUYET).count(),
    })


@staff_member_required(login_url="dang_nhap")
def quan_tri_duyet_de_xuat_san_pham(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ admin mới được duyệt bài đăng.")
    with transaction.atomic():
        submission = get_object_or_404(DeXuatSanPham.objects.select_for_update(), pk=submission_id)
        if submission.trang_thai != DeXuatSanPham.TrangThai.CHO_DUYET:
            messages.info(request, "Bài đăng này đã được xử lý trước đó.")
            return redirect("quan_tri_de_xuat_san_pham")
        product = SanPham.objects.select_for_update().filter(
            ten_san_pham__iexact=submission.ten_san_pham,
            danh_muc=submission.danh_muc,
        ).first()
        if product:
            product.so_luong = F("so_luong") + submission.so_luong
            product.gia_ban = submission.gia_ban
            product.mo_ta = submission.mo_ta
            if submission.hinh_anh:
                product.hinh_anh = submission.hinh_anh.name
            product.save(update_fields=["so_luong", "gia_ban", "mo_ta", "hinh_anh"])
        else:
            SanPham.objects.create(
                ten_san_pham=submission.ten_san_pham,
                gia_ban=submission.gia_ban,
                danh_muc=submission.danh_muc,
                mo_ta=submission.mo_ta,
                so_luong=submission.so_luong,
                hinh_anh=submission.hinh_anh.name if submission.hinh_anh else "",
            )
        submission.trang_thai = DeXuatSanPham.TrangThai.DA_DUYET
        submission.nguoi_duyet = request.user
        submission.duyet_luc = timezone.now()
        submission.save(update_fields=["trang_thai", "nguoi_duyet", "duyet_luc"])
    messages.success(request, "Đã duyệt bài đăng, cộng số lượng vào kho và hiển thị sản phẩm trên cửa hàng.")
    return redirect("quan_tri_de_xuat_san_pham")


@staff_member_required(login_url="dang_nhap")
def quan_tri_tu_choi_de_xuat_san_pham(request, submission_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ admin mới được duyệt bài đăng.")
    updated = DeXuatSanPham.objects.filter(
        pk=submission_id,
        trang_thai=DeXuatSanPham.TrangThai.CHO_DUYET,
    ).update(
        trang_thai=DeXuatSanPham.TrangThai.TU_CHOI,
        nguoi_duyet=request.user,
        duyet_luc=timezone.now(),
    )
    messages.success(request, "Đã từ chối bài đăng; kho không thay đổi." if updated else "Bài đăng này đã được xử lý trước đó.")
    return redirect("quan_tri_de_xuat_san_pham")


@staff_member_required(login_url="dang_nhap")
def quan_tri_trang_thai_nhan_vien(request, employee_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ quản trị viên cấp cao mới được đổi trạng thái nhân viên.")
    employee = get_object_or_404(User, pk=employee_id, is_staff=True, is_superuser=False)
    if employee.pk == request.user.pk:
        messages.error(request, "Bạn không thể tự khóa tài khoản đang sử dụng.")
    else:
        employee.is_active = not employee.is_active
        employee.save(update_fields=["is_active"])
        state = "đang hoạt động" if employee.is_active else "đã khóa"
        messages.success(request, f"Tài khoản {employee.username} hiện {state}.")
    return redirect("quan_tri_nhan_vien")


@staff_member_required(login_url="dang_nhap")
def quan_tri_dat_lai_mat_khau_nhan_vien(request, employee_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ quản trị viên cấp cao mới được đặt lại mật khẩu nhân viên.")
    employee = get_object_or_404(User, pk=employee_id, is_staff=True, is_superuser=False)
    form = NhanVienPasswordForm(employee, request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f"Đã cập nhật mật khẩu cho nhân viên {employee.username}.")
    else:
        errors = [str(error) for field_errors in form.errors.values() for error in field_errors]
        messages.error(request, " ".join(errors))
    return redirect("quan_tri_nhan_vien")




def ban_hang_san_pham(request):
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang n\u00e0y d\u00e0nh cho nh\u00e2n vi\u00ean b\u00e1n h\u00e0ng.")
    products = SanPham.objects.filter(is_active=True).select_related("danh_muc").order_by("so_luong", "ten_san_pham")
    search = request.GET.get("q", "").strip()
    if search:
        products = products.filter(
            Q(ten_san_pham__icontains=search)
            | Q(danh_muc__ten_danh_muc__icontains=search)
            | Q(phan_loai__icontains=search)
        )
    return render(request, "store/sales_products.html", {
        "products": products,
        "search": search,
        "low_stock_count": SanPham.objects.filter(is_active=True, so_luong__lte=5).count(),
    })
