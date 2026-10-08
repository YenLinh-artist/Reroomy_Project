from django.db import models
from django.db import models

class DanhMuc(models.Model):
    ten_danh_muc = models.CharField(max_length=100)

    def __str__(self):
        return self.ten_danh_muc

class SanPham(models.Model):
    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.IntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)

    def __str__(self):
        return self.ten_san_pham

    @property
    def gia_ban_vnd(self):
        """Return price in đồng; older demo records store the value in thousands."""
        gia = self.gia_ban or 0
        return gia * 1000 if 0 < gia < 1000 else gia

    @property
    def gia_ban_hien_thi(self):
        return f'{self.gia_ban_vnd:,}'
# Create your models here.
