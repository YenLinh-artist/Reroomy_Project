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
# Create your models here.
