"""
URL configuration for roomy_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.trang_chu, name='trang_chu'), # Trang chủ
    path('dang-nhap/', views.dang_nhap, name='dang_nhap'),
    path('dang-ky/', views.dang_ky, name='dang_ky'),
    path('dang-xuat/', views.dang_xuat, name='dang_xuat'),
    path('cskh/dang-nhap/', views.cskh_dang_nhap, name='cskh_dang_nhap'),
    path('cskh/dang-xuat/', views.dang_xuat, name='cskh_dang_xuat'),
    path('cskh/', views.cskh_hop_thu, name='cskh_hop_thu'),
    path('cskh/don-hang/', views.cskh_don_hang, name='cskh_don_hang'),
    path('cskh/don-hang/<int:order_id>/duyet/', views.cskh_duyet_don_hang, name='cskh_duyet_don_hang'),
    path('cskh/api/thong-bao/', views.cskh_thong_bao_api, name='cskh_thong_bao_api'),
    path('cskh/api/cuoc-tro-chuyen/<int:conversation_id>/', views.cskh_conversation_api, name='cskh_conversation_api'),
    path('ban-hang/', views.ban_hang_dashboard, name='ban_hang_dashboard'),
    path('ban-hang/don-hang/', views.ban_hang_don_hang, name='ban_hang_don_hang'),
    path('ban-hang/don-hang/<int:order_id>/cap-nhat/', views.ban_hang_cap_nhat_don, name='ban_hang_cap_nhat_don'),
    path('ho-tro/', views.ho_tro_khach_hang, name='ho_tro_khach_hang'),
    path('ho-tro/api/', views.customer_support_api, name='customer_support_api'),
    path('san-pham/<str:product_key>/', views.chi_tiet_san_pham, name='chi_tiet_san_pham'),
    path('gio-hang/', views.gio_hang, name='gio_hang'),
    path('thanh-toan/', views.thanh_toan, name='thanh_toan'),
    path('quan-tri/', views.quan_tri_dashboard, name='quan_tri_dashboard'),
    path('quan-tri/san-pham/', views.quan_tri_san_pham, name='quan_tri_san_pham'),
    path('quan-tri/san-pham/them/', views.quan_tri_tao_san_pham, name='quan_tri_tao_san_pham'),
    path('quan-tri/bai-dang-san-pham/', views.quan_tri_de_xuat_san_pham, name='quan_tri_de_xuat_san_pham'),
    path('quan-tri/bai-dang-san-pham/<int:submission_id>/duyet/', views.quan_tri_duyet_de_xuat_san_pham, name='quan_tri_duyet_de_xuat_san_pham'),
    path('quan-tri/bai-dang-san-pham/<int:submission_id>/tu-choi/', views.quan_tri_tu_choi_de_xuat_san_pham, name='quan_tri_tu_choi_de_xuat_san_pham'),
    path('cskh/bai-dang-san-pham/', views.cskh_de_xuat_san_pham, name='cskh_de_xuat_san_pham'),
    path('quan-tri/san-pham/<int:product_id>/sua/', views.quan_tri_sua_san_pham, name='quan_tri_sua_san_pham'),
    path('quan-tri/san-pham/<int:product_id>/xoa/', views.quan_tri_xoa_san_pham, name='quan_tri_xoa_san_pham'),
    path('quan-tri/danh-muc/', views.quan_tri_danh_muc, name='quan_tri_danh_muc'),
    path('quan-tri/nhan-vien/', views.quan_tri_nhan_vien, name='quan_tri_nhan_vien'),
    path('quan-tri/khach-hang/', views.quan_tri_khach_hang, name='quan_tri_khach_hang'),
    path('quan-tri/nhan-vien/<int:employee_id>/mat-khau/', views.quan_tri_dat_lai_mat_khau_nhan_vien, name='quan_tri_dat_lai_mat_khau_nhan_vien'),
    path('quan-tri/nhan-vien/<int:employee_id>/trang-thai/', views.quan_tri_trang_thai_nhan_vien, name='quan_tri_trang_thai_nhan_vien'),
    path('quan-tri/don-hang/', views.quan_tri_don_hang, name='quan_tri_don_hang'),
    path('quan-tri/don-hang/<int:order_id>/trang-thai/', views.quan_tri_cap_nhat_don_hang, name='quan_tri_cap_nhat_don_hang'),
    path('api/don-hang/', views.tao_don_hang, name='tao_don_hang'),
    path('api/thong-bao-don-hang/', views.thong_bao_don_hang, name='thong_bao_don_hang'),
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
