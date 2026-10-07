from django.shortcuts import get_object_or_404, render
from .models import SanPham
from types import SimpleNamespace

def trang_chu(request):
    danh_sach = SanPham.objects.all() # LÃ´i toÃ n bá»™ sáº£n pháº©m ra
    return render(request, 'index.html', {'san_pham_list': danh_sach})

def goi_y_combo(request):
    return render(request, 'room_combo.html')

def goi_y_san_pham(request):
    return render(request, 'product_suggestions.html')

def thanh_toan(request):
    return render(request, 'checkout.html')

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
        'anh_san_pham': '04.jpeg',
    })

def san_pham_mau(request):
    san_pham = SimpleNamespace(
        ten_san_pham='Ghế xoay đệm bọc', gia_ban=99,
        danh_muc=SimpleNamespace(ten_danh_muc='Ghế'),
    )
    return render(request, 'product_detail.html', {
        'san_pham': san_pham,
        'goi_y': SanPham.objects.all()[:4],
        'anh_san_pham': '04.jpeg',
    })

def dang_ky(request):
    return render(request, 'register.html')

def dang_nhap(request):
    return render(request, 'login.html')
# Create your views here.
