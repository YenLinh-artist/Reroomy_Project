from django.db import models

class DanhMuc(models.Model):
    ten_danh_muc = models.CharField(max_length=100)

    def __str__(self):
        return self.ten_danh_muc

class SanPham(models.Model):
    ten_san_pham = models.CharField(max_length=200)
    gia_ban = models.IntegerField()
    danh_muc = models.ForeignKey(DanhMuc, on_delete=models.CASCADE)
    mo_ta = models.TextField(blank=True)
    so_luong = models.PositiveIntegerField(default=0)
    hinh_anh = models.FileField(upload_to="products/", blank=True)

    def __str__(self):
        return self.ten_san_pham
# Create your models here.
