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
from django.urls import include, path
from store import views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('quan-tri/', views.trang_admin, name='trang_admin'),
    path('', views.trang_chu, name='trang_chu'),
    path('goi-y-combo/', views.goi_y_combo, name='goi_y_combo'),
    path('goi-y-san-pham/', views.goi_y_san_pham, name='goi_y_san_pham'),
    path('thanh-toan/', views.thanh_toan, name='thanh_toan'),
    path('ho-so/', views.ho_so, name='ho_so'),
    path('yeu-thich/', views.yeu_thich, name='yeu_thich'),
    path('mo-phong-combo/', views.mo_phong_combo, name='mo_phong_combo'),
    path('gio-hang/', views.gio_hang, name='gio_hang'),
    path('san-pham/<int:pk>/', views.chi_tiet_san_pham, name='chi_tiet_san_pham'),
    path('san-pham/mau/', views.san_pham_mau, name='san_pham_mau'),
    path('dang-ky/', views.dang_ky, name='dang_ky'),
    path('dang-nhap/', views.dang_nhap, name='dang_nhap'),
    path('dang-xuat/', views.dang_xuat, name='dang_xuat'),
]


