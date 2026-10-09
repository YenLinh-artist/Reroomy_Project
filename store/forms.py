from django import forms

from .models import DanhMuc, SanPham


class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong", "mo_ta", "hinh_anh")
        widgets = {
            "ten_san_pham": forms.TextInput(attrs={"placeholder": "Ví dụ: Đèn ngủ mây nhỏ"}),
            "gia_ban": forms.NumberInput(attrs={"min": 0}),
            "so_luong": forms.NumberInput(attrs={"min": 0}),
            "mo_ta": forms.Textarea(attrs={"rows": 5, "placeholder": "Chất liệu, kích thước, cách sử dụng..."}),
            "hinh_anh": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class DanhMucForm(forms.ModelForm):
    class Meta:
        model = DanhMuc
        fields = ("ten_danh_muc",)
        widgets = {"ten_danh_muc": forms.TextInput(attrs={"placeholder": "Ví dụ: Góc học tập"})}
