from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import SanPham
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from types import SimpleNamespace
import re

ANH_SAN_PHAM_CHO_PHEP = {
    '04.jpeg', '08.png', '11.png', 'product-sofa.png',
    '05.png', '12.png', '07.png', '09.png', '14.jpeg',
    '19.jpeg', '03.jpeg', '20.png',
}

def anh_san_pham_tu_request(request):
    anh = request.GET.get('image', '04.jpeg')
    return anh if anh in ANH_SAN_PHAM_CHO_PHEP else '04.jpeg'

def trang_chu(request):
    danh_sach = SanPham.objects.all() # LÃ´i toÃ n bá»™ sáº£n pháº©m ra
    return render(request, 'index.html', {'san_pham_list': danh_sach})

@user_passes_test(lambda user: user.is_active and user.is_staff, login_url='dang_nhap')
def trang_admin(request):
    customer_count = get_user_model().objects.filter(is_staff=False, is_active=True).count()
    return render(request, 'admin_dashboard.html', {'customer_count': customer_count})

def goi_y_combo(request):
    return render(request, 'room_combo.html')

def goi_y_san_pham(request):
    return render(request, 'product_suggestions.html')

def thanh_toan(request):
    return render(request, 'checkout.html', {
        'vietqr_bank_id': settings.VIETQR_BANK_ID,
        'vietqr_account_no': settings.VIETQR_ACCOUNT_NO,
        'vietqr_account_name': settings.VIETQR_ACCOUNT_NAME,
    })

def ho_so(request):
    return render(request, 'profile.html')

def yeu_thich(request):
    return render(request, 'favorites.html')

def mo_phong_combo(request):
    return render(request, 'combo_studio.html')

def gio_hang(request):
    return render(request, 'cart.html')

def chi_tiet_san_pham(request, pk):
    san_pham = get_object_or_404(SanPham, pk=pk)
    goi_y = SanPham.objects.exclude(pk=pk)[:4]
    return render(request, 'product_detail.html', {
        'san_pham': san_pham,
        'goi_y': goi_y,
        'anh_san_pham': anh_san_pham_tu_request(request),
    })

def san_pham_mau(request):
    ten_san_pham = request.GET.get('name', 'Ghế xoay đệm bọc').strip()[:200] or 'Ghế xoay đệm bọc'
    try:
        gia_ban_vnd = int(re.sub(r'\D', '', request.GET.get('price', '99000')))
    except (TypeError, ValueError):
        gia_ban_vnd = 99000
    if not 0 < gia_ban_vnd <= 2_000_000_000:
        gia_ban_vnd = 99000
    san_pham = SimpleNamespace(
        ten_san_pham=ten_san_pham, gia_ban=gia_ban_vnd,
        gia_ban_vnd=gia_ban_vnd, gia_ban_hien_thi=f'{gia_ban_vnd:,}',
        danh_muc=SimpleNamespace(ten_danh_muc='Ghế'),
    )
    return render(request, 'product_detail.html', {
        'san_pham': san_pham,
        'goi_y': SanPham.objects.all()[:4],
        'anh_san_pham': anh_san_pham_tu_request(request),
    })

def dang_ky(request):
    return render(request, 'register.html')

@require_POST
def dang_xuat(request):
    auth_logout(request)
    return redirect('dang_nhap')

@never_cache
def dang_nhap(request):
    if request.user.is_authenticated:
        return redirect('trang_admin' if request.user.is_staff else 'trang_chu')

    login_error = ''
    if request.method == 'POST':
        login_identifier = request.POST.get('username', '').strip()
        username = login_identifier
        if '@' in login_identifier:
            matching_usernames = list(
                get_user_model().objects.filter(email__iexact=login_identifier)
                .values_list('username', flat=True)[:2]
            )
            if len(matching_usernames) == 1:
                username = matching_usernames[0]
            elif matching_usernames:
                username = ''
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next', '')
            next_is_admin = next_url.split('?', 1)[0] in {
                reverse('trang_admin'),
                '/admin/',
            }
            if next_url and (user.is_staff or not next_is_admin) and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('trang_admin' if user.is_staff else 'trang_chu')
        login_error = 'Tên đăng nhập hoặc mật khẩu không chính xác.'

    google_oauth_enabled = bool(
        settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET
    )
    return render(request, 'login.html', {
        'login_error': login_error,
        'google_oauth_enabled': google_oauth_enabled,
    })
# Create your views here.

