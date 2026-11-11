from copy import deepcopy
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import DanhMuc, DeXuatSanPham, HoSoNhanVien, SanPham, Voucher
from .models import StaffProfile
from .validators import validate_gmail_address


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    max_files = 8
    max_file_size = 10 * 1024 * 1024

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", self.widget(attrs={"accept": "image/*", "multiple": True, "class": "js-product-images"}))
        kwargs.setdefault("help_text", "Có thể chọn tối đa 8 ảnh cùng lúc; mỗi ảnh tối đa 10 MB.")
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data in self.empty_values:
            return []
        files = list(data) if isinstance(data, (list, tuple)) else [data]
        if len(files) > self.max_files:
            raise ValidationError("Mỗi lần có thể tải lên tối đa 8 ảnh.")
        cleaned_files = [super(MultipleImageField, self).clean(upload, None) for upload in files]
        for upload in cleaned_files:
            extension = "." + upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
            content_type = getattr(upload, "content_type", "") or ""
            if extension not in self.allowed_extensions or (content_type and not content_type.startswith("image/")):
                raise ValidationError("Chỉ nhận ảnh JPG, PNG, WEBP hoặc GIF.")
            if upload.size > self.max_file_size:
                raise ValidationError("Mỗi ảnh tải lên không được vượt quá 10 MB.")
        return cleaned_files


def _validate_top_view_upload(upload):
    if not isinstance(upload, UploadedFile):
        return upload
    extension = "." + upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if extension not in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
        raise ValidationError("Ảnh Top View cần là PNG, SVG, WEBP hoặc JPG.")
    if upload.size > 10 * 1024 * 1024:
        raise ValidationError("Ảnh Top View không được vượt quá 10 MB.")
    content_type = getattr(upload, "content_type", "") or ""
    if content_type and not content_type.startswith("image/"):
        raise ValidationError("Vui lòng chọn tệp hình ảnh cho Top View.")
    return upload


class ProductTopViewForm(forms.Form):
    room_top_view = forms.FileField(
        required=False,
        label="Ảnh nhìn từ trên xuống (Top View)",
        help_text="Không bắt buộc. PNG nền trong suốt hoặc SVG sẽ rõ nhất.",
        widget=forms.FileInput(attrs={"accept": ".png,.svg,.webp,.jpg,.jpeg,image/*", "class": "js-product-top-view"}),
    )

    def clean_room_top_view(self):
        return _validate_top_view_upload(self.cleaned_data.get("room_top_view"))


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
    anh_bo_sung = MultipleImageField(label="Ảnh bổ sung", help_text="Chọn tối đa 8 ảnh cùng lúc. Ảnh đầu tiên sẽ làm ảnh đại diện nếu sản phẩm chưa có ảnh.")

    class Meta:
        model = SanPham
        fields = ("ten_san_pham", "danh_muc", "gia_ban", "so_luong", "phan_loai", "mo_ta", "hinh_anh", "room_top_view", "room_width_cm", "room_depth_cm", "is_active")
        labels = {
            "ten_san_pham": "Tên sản phẩm", "danh_muc": "Danh mục", "gia_ban": "Giá bán (₫)",
            "so_luong": "Tồn kho ban đầu", "phan_loai": "Phân loại",
            "mo_ta": "Mô tả", "hinh_anh": "Ảnh đại diện", "room_top_view": "Ảnh nhìn từ trên xuống (Top View)",
            "room_width_cm": "Ngang nhìn từ trên (cm)", "room_depth_cm": "Sâu nhìn từ trên (cm)",
            "is_active": "Đang kinh doanh",
        }
        help_texts = {
            "room_top_view": "Không bắt buộc. Ảnh này thay hình minh họa trong sơ đồ 2D; PNG nền trong suốt hoặc SVG sẽ rõ nhất.",
            "room_width_cm": "Dùng để vẽ tỷ lệ trên sơ đồ phòng; để trống cả hai kích thước nếu chưa biết.",
            "room_depth_cm": "Dùng để vẽ tỷ lệ trên sơ đồ phòng; để trống cả hai kích thước nếu chưa biết.",
        }
        widgets = {
            "ten_san_pham": forms.TextInput(attrs={"placeholder": "Ví dụ: Đèn ngủ mây nhỏ"}),
            "gia_ban": forms.NumberInput(attrs={"min": 0}),
            "so_luong": forms.NumberInput(attrs={"min": 0}),
            "phan_loai": forms.TextInput(attrs={"placeholder": "Màu kem, Màu trắng, Size S"}),
            "mo_ta": forms.Textarea(attrs={"rows": 5, "placeholder": "Chất liệu, kích thước, cách sử dụng..."}),
            "hinh_anh": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "room_top_view": forms.ClearableFileInput(attrs={"accept": ".png,.svg,.webp,.jpg,.jpeg,image/*", "class": "js-product-top-view"}),
            "room_width_cm": forms.NumberInput(attrs={"min": 1, "step": "0.1", "placeholder": "Ví dụ: 120"}),
            "room_depth_cm": forms.NumberInput(attrs={"min": 1, "step": "0.1", "placeholder": "Ví dụ: 60"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stock edits must go through the inventory ledger page.
        if self.instance and self.instance.pk:
            self.fields.pop("so_luong", None)
        self.fields["anh_bo_sung"] = deepcopy(self.declared_fields["anh_bo_sung"])
        self.order_fields([name for name in (
            "ten_san_pham", "danh_muc", "gia_ban", "so_luong", "phan_loai", "mo_ta",
            "hinh_anh", "anh_bo_sung", "room_top_view", "room_width_cm", "room_depth_cm", "is_active",
        ) if name in self.fields])

    def clean(self):
        cleaned = super().clean()
        width, depth = cleaned.get("room_width_cm"), cleaned.get("room_depth_cm")
        if bool(width) != bool(depth):
            message = "Nhập đủ cả chiều ngang và chiều sâu, hoặc để trống cả hai để dùng kích thước ước lượng."
            self.add_error("room_width_cm", message)
            self.add_error("room_depth_cm", message)
        return cleaned

    def clean_room_top_view(self):
        return _validate_top_view_upload(self.cleaned_data.get("room_top_view"))


class DeXuatSanPhamForm(forms.ModelForm):
    anh_bo_sung = MultipleImageField(label="Ảnh bổ sung", help_text="Chọn tối đa 8 ảnh cùng lúc; ảnh đầu tiên sẽ làm ảnh đại diện.")

    class Meta:
        model = DeXuatSanPham
        fields = ("ten_san_pham", "danh_muc", "gia_ban", "phan_loai", "mo_ta", "so_luong", "hinh_anh", "room_width_cm", "room_depth_cm")
        labels = {
            "ten_san_pham": "Tên sản phẩm",
            "danh_muc": "Danh mục",
            "gia_ban": "Giá bán (₫)",
            "phan_loai": "Phân loại",
            "mo_ta": "Mô tả",
            "so_luong": "Số lượng đề xuất nhập",
            "hinh_anh": "Ảnh đại diện",
            "room_width_cm": "Ngang nhìn từ trên (cm)",
            "room_depth_cm": "Sâu nhìn từ trên (cm)",
        }
        help_texts = {
            "room_width_cm": "Dùng để vẽ tỷ lệ trên sơ đồ phòng; để trống cả hai kích thước nếu chưa biết.",
            "room_depth_cm": "Dùng để vẽ tỷ lệ trên sơ đồ phòng; để trống cả hai kích thước nếu chưa biết.",
        }
        widgets = {
            "ten_san_pham": forms.TextInput(attrs={"placeholder": "Ví dụ: Đèn ngủ mây nhỏ"}),
            "gia_ban": forms.NumberInput(attrs={"min": 0}),
            "phan_loai": forms.TextInput(attrs={"placeholder": "Màu kem, màu trắng, size S"}),
            "mo_ta": forms.Textarea(attrs={"rows": 4, "placeholder": "Chất liệu, kích thước, công dụng..."}),
            "so_luong": forms.NumberInput(attrs={"min": 0}),
            "hinh_anh": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "room_width_cm": forms.NumberInput(attrs={"min": 1, "step": "0.1", "placeholder": "Ví dụ: 120"}),
            "room_depth_cm": forms.NumberInput(attrs={"min": 1, "step": "0.1", "placeholder": "Ví dụ: 60"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["anh_bo_sung"] = deepcopy(self.declared_fields["anh_bo_sung"])
        self.order_fields([
            "ten_san_pham", "danh_muc", "gia_ban", "phan_loai", "mo_ta", "so_luong",
            "hinh_anh", "anh_bo_sung", "room_width_cm", "room_depth_cm",
        ])

    def clean(self):
        cleaned = super().clean()
        width, depth = cleaned.get("room_width_cm"), cleaned.get("room_depth_cm")
        if bool(width) != bool(depth):
            message = "Nhập đủ cả chiều ngang và chiều sâu, hoặc để trống cả hai để dùng kích thước ước lượng."
            self.add_error("room_width_cm", message)
            self.add_error("room_depth_cm", message)
        return cleaned


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

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if code in {"ROOM25", "XINH"}:
            raise ValidationError("Mã này được dành riêng cho voucher tặng khi đăng ký tài khoản.")
        if code.startswith("THANKYOU-"):
            raise ValidationError("Mã này được dành riêng cho voucher thưởng cuối tháng.")
        return code
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import DanhMuc, HoSoNhanVien, SanPham


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
