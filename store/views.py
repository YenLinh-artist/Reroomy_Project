from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
import uuid
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce

from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .forms import DanhMucForm, NhanVienCreationForm, NhanVienPasswordForm, SanPhamForm
from .models import (
    ChiTietDonHang,
    CustomerServiceConversation,
    CustomerServiceMessage,
    DanhMuc,
    DeXuatSanPham,
    DonHang,
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
for item in DEMO_PRODUCTS:
    item["display_price"] = f"{item['price'] // 1000}k"


def _local_demo_photo(filename):
    return settings.BASE_DIR / "store" / "static" / "store" / "images" / filename


def _demo_product(item):
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
        "variant": "Màu kem",
        "stock_status": "Còn hàng · mẫu minh họa",
        "is_demo": True,
        "sold_text": f"{item['sold']} lượt bán · mẫu minh họa",
    }


def _database_product(item):
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
        "variant": "Mẫu hiện có",
        "stock_status": f"Còn {item.so_luong} sản phẩm" if item.so_luong else "Tạm hết hàng",
        "is_demo": False,
        "sold_text": "Chưa có dữ liệu bán",
    }


def _products_for_homepage():
    saved_products = list(SanPham.objects.select_related("danh_muc").order_by("-pk"))
    if saved_products:
        return [_database_product(item) for item in saved_products]
    return [_demo_product(item) for item in DEMO_PRODUCTS]


def trang_chu(request):
    return render(request, "index.html", {
        "san_pham_list": _products_for_homepage(),
        "categories": ["Phổ biến", "Combo chăn ấm - gối êm", "Giấy dán tường", "Đèn ngủ - học tập", "Gương tường"],
    })


def gio_hang(request):
    return render(request, "store/cart.html")


def thanh_toan(request):
    return render(request, "store/checkout.html")


def tao_don_hang(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        data = json.loads(request.body)
        name, phone, address = (str(data.get(key, "")).strip() for key in ("full_name", "phone", "address"))
        items = data.get("items", [])
        if not name or not phone or not address or not isinstance(items, list) or not items:
            return JsonResponse({"error": "Vui lòng điền đủ thông tin và chọn sản phẩm."}, status=400)
        code = str(data.get("voucher", "")).upper()
        if code not in ("", "ROOM25", "XINH10"):
            code = ""
        prepared, subtotal = [], 0
        demos = {item["id"]: item for item in DEMO_PRODUCTS}
        for entry in items:
            key, quantity = str(entry.get("id", "")), int(entry.get("qty", 0))
            if quantity < 1 or quantity > 99:
                return JsonResponse({"error": "Số lượng sản phẩm không hợp lệ."}, status=400)
            product = None
            if key.isdigit():
                product = SanPham.objects.filter(pk=int(key)).first()
            if product:
                title, price = product.ten_san_pham, product.gia_ban
            elif key in demos:
                title, price = demos[key]["name"], demos[key]["price"]
            else:
                return JsonResponse({"error": "Sản phẩm không còn tồn tại. Vui lòng tải lại giỏ hàng."}, status=400)
            subtotal += price * quantity
            prepared.append((product, title, str(entry.get("variant", ""))[:100], price, quantity))
        discount = min(round(subtotal * (0.25 if code == "ROOM25" else 0.1)), 50000 if code == "ROOM25" else 30000) if code else 0
        shipping = 0 if subtotal >= 500000 else 20000
        if not request.session.session_key:
            request.session.create()
        order = DonHang.objects.create(
            ma_don=f"RR{uuid.uuid4().hex[:8].upper()}", ho_ten=name, so_dien_thoai=phone[:20],
            dia_chi=address, ghi_chu=str(data.get("note", ""))[:2000],
            phuong_thuc="bank" if data.get("payment") == "bank" else "cod",
            tam_tinh=subtotal, giam_gia=discount, phi_giao_hang=shipping,
            tong_tien=subtotal - discount + shipping,
            khach_hang=request.user if request.user.is_authenticated and not request.user.is_staff else None,
            khach_hang_session_key=request.session.session_key or "",
        )
        ChiTietDonHang.objects.bulk_create([
            ChiTietDonHang(don_hang=order, san_pham=product, ten_san_pham=title,
                           phan_loai=variant, don_gia=price, so_luong=quantity)
            for product, title, variant, price, quantity in prepared
        ])
        return JsonResponse({"order_id": order.ma_don})
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Thông tin đơn hàng không hợp lệ."}, status=400)


def chi_tiet_san_pham(request, product_key):
    product = next((item for item in DEMO_PRODUCTS if item["id"] == product_key), None)
    if product:
        item = _demo_product(product)
    elif product_key.isdigit():
        saved = get_object_or_404(SanPham.objects.select_related("danh_muc"), pk=int(product_key))
        item = _database_product(saved)
    else:
        raise Http404("Không tìm thấy sản phẩm")

    related = [
        _demo_product(other)
        for other in DEMO_PRODUCTS
        if other["id"] != product_key
    ][:4]
    reviews = [
        {"name": "Mây nhỏ", "text": "Món decor xinh, vừa vặn với góc phòng của mình.", "date": "Đánh giá minh họa"},
        {"name": "Linh Chi", "text": "Màu sắc dịu và nhìn ngoài đời cũng dễ phối.", "date": "Đánh giá minh họa"},
    ]
    return render(request, "store/product_detail.html", {
        "product": item,
        "related_products": related,
        "reviews": reviews,
    })


def thong_bao_don_hang(request):
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if request.user.is_authenticated and request.user.is_staff:
        return JsonResponse({"notifications": [], "unread": 0})
    ownership = Q(pk__in=[])
    if request.session.session_key:
        ownership |= Q(khach_hang_session_key=request.session.session_key)
    if request.user.is_authenticated:
        ownership |= Q(khach_hang=request.user)
    orders = DonHang.objects.filter(
        ownership,
        thong_bao_da_doc=False,
    ).exclude(trang_thai=DonHang.TrangThai.MOI).order_by("-ngay_tao")
    if request.method == "POST":
        try:
            ids = json.loads(request.body).get("ids", [])
            ids = [int(value) for value in ids]
        except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Yêu cầu không hợp lệ."}, status=400)
        orders.filter(pk__in=ids).update(thong_bao_da_doc=True)
        return JsonResponse({"ok": True})
    notifications = [{
        "id": order.pk,
        "order_id": order.ma_don,
        "message": f"Đơn hàng {order.ma_don} của bạn đã được duyệt.",
        "created_at": order.ngay_tao.isoformat(),
    } for order in orders[:10]]
    return JsonResponse({"notifications": notifications, "unread": orders.count()})


def dang_ky(request):
    if request.user.is_authenticated:
        return redirect("trang_chu")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        if not username or not email or not password:
            messages.error(request, "Bạn điền đầy đủ thông tin giúp mình nhé.")
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Tên đăng nhập này đã được sử dụng rồi.")
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email này đã có tài khoản Re:Room rồi.")
        elif password != password_confirm:
            messages.error(request, "Hai mật khẩu chưa khớp nhau.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, "Tạo tài khoản thành công. Chào mừng bạn đến Re:Room!")
            return redirect("trang_chu")
    return render(request, "register.html")


def dang_nhap(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect(_staff_landing(request.user) if request.user.is_staff else "trang_chu")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Bạn đã đăng nhập. Chào mừng trở lại!")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(_staff_landing(user) if user.is_staff else "trang_chu")
        messages.error(request, "Tên đăng nhập hoặc mật khẩu chưa chính xác.")
    return render(request, "login.html", {"next": next_url})


def _staff_landing(user):
    if user.is_superuser:
        return "quan_tri_dashboard"
    if _has_sales_access(user):
        return "ban_hang_dashboard"
    return "cskh_hop_thu"


def _has_sales_access(user):
    if user.is_superuser:
        return True
    profile = getattr(user, "ho_so_nhan_vien", None)
    return bool(profile and profile.bo_phan == HoSoNhanVien.BoPhan.BAN_HANG)


def _has_cskh_access(user):
    if user.is_superuser:
        return True
    profile = getattr(user, "ho_so_nhan_vien", None)
    return not profile or profile.bo_phan == HoSoNhanVien.BoPhan.CSKH


def dang_xuat(request):
    logout(request)
    return redirect("trang_chu")


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
        "pending_order_count": DonHang.objects.filter(trang_thai=DonHang.TrangThai.MOI).count(),
    })


@staff_member_required(login_url="dang_nhap")
def cskh_don_hang(request):
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("Tài khoản này không thuộc bộ phận CSKH.")
    orders = DonHang.objects.filter(
        trang_thai__in=(DonHang.TrangThai.MOI, DonHang.TrangThai.XAC_NHAN),
    ).prefetch_related("chi_tiet").select_related("khach_hang")
    return render(request, "store/cskh_orders.html", {
        "orders": orders,
        "pending_order_count": DonHang.objects.filter(trang_thai=DonHang.TrangThai.MOI).count(),
    })


@staff_member_required(login_url="dang_nhap")
def cskh_duyet_don_hang(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _has_cskh_access(request.user):
        return HttpResponseForbidden("Tài khoản này không thuộc bộ phận CSKH.")
    order = get_object_or_404(DonHang, pk=order_id)
    if order.trang_thai == DonHang.TrangThai.MOI:
        order.trang_thai = DonHang.TrangThai.XAC_NHAN
        order.save(update_fields=["trang_thai"])
        messages.success(request, f"Đã duyệt đơn {order.ma_don}; trạng thái đã cập nhật trong quản lý đơn hàng.")
    else:
        messages.info(request, f"Đơn {order.ma_don} đã được xử lý trước đó.")
    return redirect("cskh_don_hang")


@staff_member_required(login_url="dang_nhap")
def ban_hang_dashboard(request):
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang này dành cho nhân viên bán hàng.")
    orders = DonHang.objects.exclude(trang_thai=DonHang.TrangThai.MOI)
    return render(request, "store/sales_dashboard.html", {
        "product_count": SanPham.objects.count(),
        "orders_to_process": orders.filter(trang_thai=DonHang.TrangThai.XAC_NHAN).count(),
        "orders_shipping": orders.filter(trang_thai=DonHang.TrangThai.DANG_GIAO).count(),
        "recent_orders": orders.select_related("khach_hang").order_by("-ngay_tao")[:5],
    })


@staff_member_required(login_url="dang_nhap")
def ban_hang_don_hang(request):
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang này dành cho nhân viên bán hàng.")
    orders = DonHang.objects.exclude(
        trang_thai=DonHang.TrangThai.MOI,
    ).prefetch_related("chi_tiet").select_related("khach_hang")
    return render(request, "store/sales_orders.html", {
        "orders": orders,
        "statuses": [choice for choice in DonHang.TrangThai.choices if choice[0] != DonHang.TrangThai.MOI],
    })


@staff_member_required(login_url="dang_nhap")
def ban_hang_cap_nhat_don(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _has_sales_access(request.user):
        return HttpResponseForbidden("Trang này dành cho nhân viên bán hàng.")
    order = get_object_or_404(DonHang, pk=order_id)
    if order.trang_thai == DonHang.TrangThai.MOI:
        return HttpResponseForbidden("Đơn cần được CSKH duyệt trước khi chuyển sang xử lý bán hàng.")
    allowed_statuses = {
        DonHang.TrangThai.XAC_NHAN,
        DonHang.TrangThai.DANG_GIAO,
        DonHang.TrangThai.HOAN_TAT,
        DonHang.TrangThai.DA_HUY,
    }
    new_status = request.POST.get("trang_thai")
    if new_status not in allowed_statuses:
        messages.error(request, "Trạng thái đơn hàng không hợp lệ.")
        return redirect("ban_hang_don_hang")
    order.trang_thai = new_status
    order.ghi_chu_noi_bo = request.POST.get("ghi_chu_noi_bo", "").strip()[:2000]
    order.save(update_fields=["trang_thai", "ghi_chu_noi_bo"])
    messages.success(request, f"Đã cập nhật đơn {order.ma_don}.")
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
def quan_tri_dashboard(request):
    month_values = [8, 11, 9, 14, 12, 17, 15, 21, 19, 25, 22, 29]
    products = list(SanPham.objects.select_related("danh_muc").order_by("so_luong", "ten_san_pham")[:5])
    return render(request, "store/admin_dashboard.html", {
        "product_count": SanPham.objects.count(),
        "pending_product_submissions": DeXuatSanPham.objects.filter(
            trang_thai=DeXuatSanPham.TrangThai.CHO_DUYET,
        ).count(),
        "category_count": DanhMuc.objects.count(),
        "customer_count": User.objects.filter(is_staff=False, is_superuser=False).count(),
        "low_stock_count": SanPham.objects.filter(so_luong__lte=5).count(),
        "stock_units": SanPham.objects.aggregate(total=Sum("so_luong"))["total"] or 0,
        "low_stock_products": products,
        "chart_data": month_values,
        "month_labels": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"],
    })


@staff_member_required(login_url="dang_nhap")
def quan_tri_san_pham(request):
    products = SanPham.objects.select_related("danh_muc").order_by("ten_san_pham")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(ten_san_pham__icontains=query)
    return render(request, "store/admin_products.html", {"products": products, "query": query})


@staff_member_required(login_url="dang_nhap")
def quan_tri_tao_san_pham(request):
    if not request.user.is_superuser and _has_cskh_access(request.user):
        return cskh_de_xuat_san_pham(request)
    form = SanPhamForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        uploaded = request.FILES.get("hinh_anh")
        if uploaded and not (uploaded.content_type or "").startswith("image/"):
            form.add_error("hinh_anh", "Vui lòng chọn tệp ảnh.")
        else:
            saved.save()
            messages.success(request, "Đã thêm sản phẩm vào kho.")
            return redirect("ban_hang_dashboard" if _has_sales_access(request.user) else "quan_tri_san_pham")
    template = "store/sales_product_form.html" if _has_sales_access(request.user) else "store/admin_product_form.html"
    return render(request, template, {"form": form, "page_title": "Thêm sản phẩm", "editing": False})


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


@staff_member_required(login_url="dang_nhap")
def quan_tri_xoa_san_pham(request, product_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    product = get_object_or_404(SanPham, pk=product_id)
    product.delete()
    messages.success(request, "Đã xóa sản phẩm khỏi kho.")
    return redirect("quan_tri_san_pham")


@staff_member_required(login_url="dang_nhap")
def quan_tri_danh_muc(request):
    form = DanhMucForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã thêm danh mục.")
        return redirect("quan_tri_danh_muc")
    categories = DanhMuc.objects.order_by("ten_danh_muc")
    return render(request, "store/admin_categories.html", {"form": form, "categories": categories})


@staff_member_required(login_url="dang_nhap")
def quan_tri_nhan_vien(request):
    if request.method == "POST" and not request.user.is_superuser:
        return HttpResponseForbidden("Chỉ quản trị viên cấp cao mới được tạo tài khoản nhân viên.")
    employee_form = NhanVienCreationForm(request.POST or None)
    if request.method == "POST" and employee_form.is_valid():
        employee = employee_form.save(commit=False)
        employee.is_staff = True
        employee.is_active = True
        employee.save()
        HoSoNhanVien.objects.update_or_create(
            user=employee,
            defaults={"bo_phan": employee_form.cleaned_data["bo_phan"]},
        )
        messages.success(request, f"Đã tạo tài khoản nhân viên {employee.username}.")
        return redirect("quan_tri_nhan_vien")
    employees = User.objects.filter(is_staff=True, is_superuser=False).order_by("username")
    query = request.GET.get("q", "").strip()
    if query:
        from django.db.models import Q
        employees = employees.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    return render(request, "store/admin_employees.html", {
        "employees": employees, "query": query, "employee_form": employee_form,
    })


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
def quan_tri_khach_hang(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    recent_completed_spend = Sum(
        "don_hang__tong_tien",
        filter=Q(
            don_hang__ngay_tao__gte=one_month_ago,
            don_hang__trang_thai=DonHang.TrangThai.HOAN_TAT,
        ),
    )
    customers = User.objects.filter(is_staff=False, is_superuser=False).annotate(
        chi_tieu_30_ngay=Coalesce(recent_completed_spend, Value(0)),
    ).order_by("-chi_tieu_30_ngay", "-date_joined")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        customers = customers.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    if status == "active":
        customers = customers.filter(is_active=True)
    elif status == "inactive":
        customers = customers.filter(is_active=False)
    customers = list(customers)
    for customer in customers:
        customer.chi_tieu_hien_thi = f"{customer.chi_tieu_30_ngay:,}".replace(",", ".")
        customer.uu_tien_voucher = customer.chi_tieu_30_ngay > 15_000_000
    return render(request, "store/admin_customers.html", {
        "customers": customers, "query": query, "selected_status": status,
        "moc_uu_tien": 15_000_000,
    })


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


@staff_member_required(login_url="dang_nhap")
def quan_tri_don_hang(request):
    orders = DonHang.objects.exclude(
        trang_thai=DonHang.TrangThai.MOI,
    ).prefetch_related("chi_tiet")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if query:
        from django.db.models import Q
        orders = orders.filter(Q(ma_don__icontains=query) | Q(ho_ten__icontains=query) | Q(so_dien_thoai__icontains=query))
    admin_statuses = [
        choice for choice in DonHang.TrangThai.choices
        if choice[0] != DonHang.TrangThai.MOI
    ]
    if status in {value for value, _label in admin_statuses}:
        orders = orders.filter(trang_thai=status)
    return render(request, "store/admin_orders.html", {
        "orders": orders, "query": query, "selected_status": status,
        "statuses": admin_statuses,
    })


@staff_member_required(login_url="dang_nhap")
def quan_tri_cap_nhat_don_hang(request, order_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    order = get_object_or_404(DonHang, pk=order_id)
    status = request.POST.get("trang_thai")
    if status in DonHang.TrangThai.values:
        order.trang_thai = status
        order.save(update_fields=["trang_thai"])
        messages.success(request, f"Đã cập nhật trạng thái đơn {order.ma_don}.")
    return redirect("quan_tri_don_hang")
