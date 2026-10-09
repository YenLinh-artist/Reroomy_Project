from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import DanhMuc, HoSoNhanVien, SanPham

User = get_user_model()


class NhanVienCreationForm(UserCreationForm):
    bo_phan = forms.ChoiceField(
        label="Bộ phận",
        choices=HoSoNhanVien.BoPhan.choices,
        initial=HoSoNhanVien.BoPhan.CSKH,
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        error_messages={
            "required": "Vui lòng nhập email.",
            "invalid": "Vui lòng nhập địa chỉ email hợp lệ.",
        },
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "T\u00ean \u0111\u0103ng nh\u1eadp",
            "first_name": "T\u00ean",
            "last_name": "H\u1ecd",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Bắt buộc. Tối đa 150 ký tự; có thể dùng chữ, số và @/./+/-/_."
        self.fields["username"].error_messages.update({
            "required": "Vui lòng nhập tên đăng nhập.",
            "invalid": "Tên đăng nhập chỉ được chứa chữ, số và các ký tự @/./+/-/_.",
        })
        self.fields["first_name"].label = "T\u00ean"
        self.fields["last_name"].label = "H\u1ecd"
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["password1"].label = "M\u1eadt kh\u1ea9u"
        self.fields["password1"].help_text = "Mật khẩu cần đủ mạnh và không được quá phổ biến hoặc quá ngắn."
        self.fields["password1"].error_messages["required"] = "Vui lòng nhập mật khẩu."
        self.fields["password2"].label = "X\u00e1c nh\u1eadn m\u1eadt kh\u1ea9u"
        self.fields["password2"].help_text = "Nhập lại mật khẩu để xác nhận."
        self.fields["password2"].error_messages["required"] = "Vui lòng xác nhận mật khẩu."

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Hai mật khẩu chưa khớp nhau.", code="password_mismatch")
        return password2

    def validate_password_for_user(self, user, password_field_name="password2"):
        password = self.cleaned_data.get(password_field_name)
        if not password:
            return
        try:
            password_validation.validate_password(password, user)
        except ValidationError as error:
            translated_errors = {
                "password_too_short": "Mật khẩu quá ngắn. Hãy chọn mật khẩu dài hơn.",
                "password_too_common": "Mật khẩu này quá phổ biến. Hãy chọn mật khẩu khác.",
                "password_entirely_numeric": "Mật khẩu không được chỉ gồm chữ số.",
                "password_too_similar": "Mật khẩu quá giống thông tin cá nhân.",
            }
            self.add_error(password_field_name, forms.ValidationError([
                translated_errors.get(item.code, "Mật khẩu chưa đáp ứng yêu cầu bảo mật.")
                for item in error.error_list
            ]))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Tên đăng nhập này đã được sử dụng.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email n\u00e0y \u0111\u00e3 \u0111\u01b0\u1ee3c s\u1eed d\u1ee5ng.")
        return email


class NhanVienPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="M\u1eadt kh\u1ea9u m\u1edbi",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="X\u00e1c nh\u1eadn m\u1eadt kh\u1ea9u m\u1edbi",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("new_password1")
        password2 = cleaned.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                self.add_error("new_password2", "Hai m\u1eadt kh\u1ea9u ch\u01b0a kh\u1edbp nhau.")
            else:
                try:
                    password_validation.validate_password(password1, self.user)
                except ValidationError as error:
                    translated_errors = {
                        "password_too_short": "M\u1eadt kh\u1ea9u qu\u00e1 ng\u1eafn. H\u00e3y ch\u1ecdn m\u1eadt kh\u1ea9u d\u00e0i h\u01a1n.",
                        "password_too_common": "M\u1eadt kh\u1ea9u n\u00e0y qu\u00e1 ph\u1ed5 bi\u1ebfn. H\u00e3y ch\u1ecdn m\u1eadt kh\u1ea9u kh\u00e1c.",
                        "password_entirely_numeric": "M\u1eadt kh\u1ea9u kh\u00f4ng \u0111\u01b0\u1ee3c ch\u1ec9 g\u1ed3m ch\u1eef s\u1ed1.",
                        "password_too_similar": "M\u1eadt kh\u1ea9u qu\u00e1 gi\u1ed1ng th\u00f4ng tin c\u00e1 nh\u00e2n.",
                    }
                    for item in error.error_list:
                        self.add_error("new_password1", translated_errors.get(
                            item.code, "M\u1eadt kh\u1ea9u ch\u01b0a \u0111\u00e1p \u1ee9ng y\u00eau c\u1ea7u b\u1ea3o m\u1eadt."
                        ))
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user


class SanPhamForm(forms.ModelForm):
    class Meta:
        model = SanPham
        fields = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong", "mo_ta", "hinh_anh")
        labels = {
            "ten_san_pham": "T\u00ean s\u1ea3n ph\u1ea9m",
            "danh_muc": "Danh m\u1ee5c",
            "gia_ban": "Gi\u00e1 b\u00e1n",
            "so_luong": "S\u1ed1 l\u01b0\u1ee3ng trong kho",
            "mo_ta": "M\u00f4 t\u1ea3 s\u1ea3n ph\u1ea9m",
            "hinh_anh": "\u1ea2nh s\u1ea3n ph\u1ea9m",
        }
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
