from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import DanhMucForm, SanPhamForm
from .models import DanhMuc, SanPham


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
    if request.user.is_authenticated:
        return redirect("trang_chu")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Bạn đã đăng nhập. Chào mừng trở lại!")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("trang_chu")
        messages.error(request, "Tên đăng nhập hoặc mật khẩu chưa chính xác.")
    return render(request, "login.html", {"next": next_url})


def dang_xuat(request):
    logout(request)
    return redirect("trang_chu")


@staff_member_required(login_url="dang_nhap")
def quan_tri_dashboard(request):
    month_values = [8, 11, 9, 14, 12, 17, 15, 21, 19, 25, 22, 29]
    products = list(SanPham.objects.select_related("danh_muc").order_by("so_luong", "ten_san_pham")[:5])
    return render(request, "store/admin_dashboard.html", {
        "product_count": SanPham.objects.count(),
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
    form = SanPhamForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        uploaded = request.FILES.get("hinh_anh")
        if uploaded and not (uploaded.content_type or "").startswith("image/"):
            form.add_error("hinh_anh", "Vui lòng chọn tệp ảnh.")
        else:
            saved.save()
            messages.success(request, "Đã thêm sản phẩm vào kho.")
            return redirect("quan_tri_san_pham")
    return render(request, "store/admin_product_form.html", {"form": form, "page_title": "Thêm sản phẩm", "editing": False})


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
