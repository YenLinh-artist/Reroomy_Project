from django.shortcuts import render
from django.shortcuts import render
from .models import SanPham

def trang_chu(request):
    danh_sach = SanPham.objects.all() # Lôi toàn bộ sản phẩm ra
    return render(request, 'index.html', {'san_pham_list': danh_sach})

def dang_ky(request):
    return render(request, 'register.html')

def dang_nhap(request):
    return render(request, 'login.html')
# Create your views here.
