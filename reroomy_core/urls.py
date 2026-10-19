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
    path('', views.trang_chu, name='trang_chu'),
    path('dang-nhap/', views.dang_nhap, name='dang_nhap'),
    path('dang-ky/', views.dang_ky, name='dang_ky'),
    path('dang-xuat/', views.dang_xuat, name='dang_xuat'),
    path('san-pham/<str:product_key>/', views.chi_tiet_san_pham, name='chi_tiet_san_pham'),
    path('danh-gia/<int:review_id>/bao-cao/', views.bao_cao_danh_gia, name='bao_cao_danh_gia'),
    path('gio-hang/', views.gio_hang, name='gio_hang'),
    path('thanh-toan/', views.thanh_toan, name='thanh_toan'),
    path('dat-hang-thanh-cong/', views.dat_hang_thanh_cong, name='dat_hang_thanh_cong'),
    path('theo-doi-don/<uuid:tracking_token>/', views.theo_doi_don_hang, name='theo_doi_don_hang'),
    path('tai-khoan/', views.tai_khoan, name='tai_khoan'),
    path('goi-y-combo/', views.goi_y_combo, name='goi_y_combo'),
    path('phong-mau/', views.phong_mau, name='phong_mau'),
    path('tu-van-decor/', views.tu_van_decor, name='tu_van_decor'),
    path('quan-tri/', views.quan_tri_dashboard, name='quan_tri_dashboard'),
    path('quan-tri/tai-khoan/', views.quan_tri_tai_khoan, name='quan_tri_tai_khoan'),
    path('quan-tri/san-pham/', views.quan_tri_san_pham, name='quan_tri_san_pham'),
    path('quan-tri/san-pham/them/', views.quan_tri_tao_san_pham, name='quan_tri_tao_san_pham'),
    path('quan-tri/san-pham/<int:product_id>/sua/', views.quan_tri_sua_san_pham, name='quan_tri_sua_san_pham'),
    path('quan-tri/san-pham/<int:product_id>/xoa/', views.quan_tri_xoa_san_pham, name='quan_tri_xoa_san_pham'),
    path('quan-tri/danh-muc/', views.quan_tri_danh_muc, name='quan_tri_danh_muc'),
    path('quan-tri/don-hang/', views.quan_tri_don_hang, name='quan_tri_don_hang'),
    path('quan-tri/don-hang/<int:order_id>/', views.quan_tri_chi_tiet_don, name='quan_tri_chi_tiet_don'),
    path('quan-tri/don-hang/<int:order_id>/cap-nhat/', views.quan_tri_cap_nhat_don, name='quan_tri_cap_nhat_don'),
    path('quan-tri/khach-hang/', views.quan_tri_khach_hang, name='quan_tri_khach_hang'),
    path('quan-tri/voucher/', views.quan_tri_vouchers, name='quan_tri_vouchers'),
    path('quan-tri/voucher/<int:voucher_id>/duyet/', views.quan_tri_duyet_voucher, name='quan_tri_duyet_voucher'),
    path('quan-tri/kho/', views.quan_tri_ton_kho, name='quan_tri_ton_kho'),
    path('quan-tri/nhan-vien/', views.quan_tri_nhan_vien, name='quan_tri_nhan_vien'),
    path('quan-tri/tu-van/', views.quan_tri_tu_van, name='quan_tri_tu_van'),
    path('quan-tri/tu-van/<int:case_id>/', views.quan_tri_chi_tiet_tu_van, name='quan_tri_chi_tiet_tu_van'),
    path('quan-tri/danh-gia/', views.quan_tri_danh_gia, name='quan_tri_danh_gia'),
    path('cskh/dang-nhap/', views.cskh_dang_nhap, name='cskh_dang_nhap'),
    path('cskh/dang-xuat/', views.dang_xuat, name='cskh_dang_xuat'),
    path('cskh/', views.cskh_hop_thu, name='cskh_hop_thu'),
    path('cskh/don-hang/', views.cskh_don_hang, name='cskh_don_hang'),
    path('cskh/don-hang/<int:order_id>/duyet/', views.cskh_duyet_don_hang, name='cskh_duyet_don_hang'),
    path('cskh/api/thong-bao/', views.cskh_thong_bao_api, name='cskh_thong_bao_api'),
    path('cskh/api/cuoc-tro-chuyen/<int:conversation_id>/', views.cskh_conversation_api, name='cskh_conversation_api'),
    path('ban-hang/', views.ban_hang_dashboard, name='ban_hang_dashboard'),
    path('ban-hang/san-pham/', views.ban_hang_san_pham, name='ban_hang_san_pham'),
    path('ban-hang/don-hang/', views.ban_hang_don_hang, name='ban_hang_don_hang'),
    path('ban-hang/don-hang/<int:order_id>/cap-nhat/', views.ban_hang_cap_nhat_don, name='ban_hang_cap_nhat_don'),
    path('ho-tro/', views.ho_tro_khach_hang, name='ho_tro_khach_hang'),
    path('ho-tro/api/', views.customer_support_api, name='customer_support_api'),
    path('quan-tri/bai-dang-san-pham/', views.quan_tri_de_xuat_san_pham, name='quan_tri_de_xuat_san_pham'),
    path('quan-tri/bai-dang-san-pham/<int:submission_id>/duyet/', views.quan_tri_duyet_de_xuat_san_pham, name='quan_tri_duyet_de_xuat_san_pham'),
    path('quan-tri/bai-dang-san-pham/<int:submission_id>/tu-choi/', views.quan_tri_tu_choi_de_xuat_san_pham, name='quan_tri_tu_choi_de_xuat_san_pham'),
    path('cskh/bai-dang-san-pham/', views.cskh_de_xuat_san_pham, name='cskh_de_xuat_san_pham'),
    path('quan-tri/nhan-vien/<int:employee_id>/mat-khau/', views.quan_tri_dat_lai_mat_khau_nhan_vien, name='quan_tri_dat_lai_mat_khau_nhan_vien'),
    path('quan-tri/nhan-vien/<int:employee_id>/trang-thai/', views.quan_tri_trang_thai_nhan_vien, name='quan_tri_trang_thai_nhan_vien'),
    path('api/thong-bao-don-hang/', views.thong_bao_don_hang, name='thong_bao_don_hang')
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
