from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import DanhMuc, SanPham, Voucher
from .models import StaffProfile
from .validators import validate_gmail_address


class StaffAccountForm(forms.Form):
    username = forms.CharField(max_length=150, label="Tên đăng nhập")
    email = forms.EmailField(
        label="Email",
        help_text="D\u00f9ng \u0111\u1ecba ch\u1ec9 k\u1ebft th\u00fac b\u1eb1ng @gmail.com.",
        widget=forms.EmailInput(attrs={
            "pattern": r"[^@\s]+@gmail\.com",
            "title": "Vui l\u00f2ng d\u00f9ng email @gmail.com.",
            "placeholder": "ten@gmail.com",
        }),
    )
    first_name = forms.CharField(max_length=150, label="Tên nhân viên")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput, help_text="Tối thiểu 8 ký tự, có chữ hoa, chữ thường và số.")
    password_confirm = forms.CharField(label="Nhập lại mật khẩu", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="Vai trò", choices=(
        (StaffProfile.Role.SALES, "Nhân viên bán hàng"),
        (StaffProfile.Role.CONSULTANT, "Nhân viên tư vấn decor"),
    ))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Tên đăng nhập đã được sử dụng.")
        return username

    def clean_email(self):
        email = validate_gmail_address(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email này đã được dùng cho một tài khoản khác.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        if password:
            user = User(username=cleaned.get("username", ""), email=cleaned.get("email", ""), first_name=cleaned.get("first_name", ""))
            try:
                password_validation.validate_password(password, user)
            except ValidationError as exc:
                self.add_error("password", exc)
        if cleaned.get("password") and cleaned.get("password_confirm") and cleaned["password"] != cleaned["password_confirm"]:
            self.add_error("password_confirm", "Hai mật khẩu chưa khớp.")
        return cleaned


class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong", "phan_loai", "mo_ta", "hinh_anh", "is_active")
        labels = {
            "ten_san_pham": "Tên sản phẩm", "danh_muc": "Danh mục", "gia_ban": "Giá bán (₫)",
            "so_luong": "Tồn kho ban đầu", "phan_loai": "Phân loại",
            "mo_ta": "Mô tả", "hinh_anh": "Ảnh sản phẩm",
            "is_active": "Đang kinh doanh",
        }
        widgets = {
            "ten_san_pham": forms.TextInput(attrs={"placeholder": "Ví dụ: Đèn ngủ mây nhỏ"}),
            "gia_ban": forms.NumberInput(attrs={"min": 0}),
            "so_luong": forms.NumberInput(attrs={"min": 0}),
            "phan_loai": forms.TextInput(attrs={"placeholder": "Màu kem, Màu trắng, Size S"}),
            "mo_ta": forms.Textarea(attrs={"rows": 5, "placeholder": "Chất liệu, kích thước, cách sử dụng..."}),
            "hinh_anh": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stock edits must go through the inventory ledger page.
        if self.instance and self.instance.pk:
            self.fields.pop("so_luong", None)


class DanhMucForm(forms.ModelForm):
    class Meta:
        model = DanhMuc
        fields = ("ten_danh_muc",)
        labels = {"ten_danh_muc": "Tên danh mục"}
        widgets = {"ten_danh_muc": forms.TextInput(attrs={"placeholder": "Ví dụ: Góc học tập"})}


class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = ("code", "discount_type", "discount_value", "minimum_order", "usage_limit", "starts_at", "ends_at")
        labels = {
            "code": "Mã voucher", "discount_type": "Loại giảm giá", "discount_value": "Mức giảm",
            "minimum_order": "Giá trị đơn tối thiểu (₫)", "usage_limit": "Số lượt phát hành",
            "starts_at": "Bắt đầu", "ends_at": "Kết thúc",
        }
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("starts_at", "ends_at"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
