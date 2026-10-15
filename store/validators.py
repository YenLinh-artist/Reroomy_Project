from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ReRoomPasswordValidator:
    """Password rule shared by customer registration and staff account creation."""

    def validate(self, password, user=None):
        problems = []
        if len(password) < 8:
            problems.append(_("Mật khẩu cần có ít nhất 8 ký tự."))
        if not any(char.isupper() for char in password):
            problems.append(_("Mật khẩu cần có ít nhất một chữ cái in hoa."))
        if not any(char.islower() for char in password):
            problems.append(_("Mật khẩu cần có ít nhất một chữ cái thường."))
        if not any(char.isdigit() for char in password):
            problems.append(_("Mật khẩu cần có ít nhất một chữ số."))
        if problems:
            raise ValidationError(problems, code="reroom_password_policy")

    def get_help_text(self):
        return _("Tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và chữ số.")


def validate_gmail_address(value):
    """Require a syntactically valid address whose domain is exactly gmail.com."""
    from django.core.validators import validate_email

    email = str(value or "").strip()
    validate_email(email)
    if email.rsplit("@", 1)[-1].casefold() != "gmail.com":
        raise ValidationError("Vui l\u00f2ng d\u00f9ng email k\u1ebft th\u00fac b\u1eb1ng @gmail.com.", code="gmail_required")
    return email.lower()
