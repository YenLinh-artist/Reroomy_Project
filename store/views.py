from django.shortcuts import render
from django.shortcuts import render
from .models import SanPham

def trang_chu(request):
    danh_sach = SanPham.objects.all() # Lôi toàn bộ sản phẩm ra
    return render(request, 'index.html', {'san_pham_list': danh_sach})
# Create your views here.
