import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0011_signupvouchergrant"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="voucher",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Bản nháp"),
                    ("pending", "Chờ duyệt"),
                    ("approved", "Đã duyệt"),
                    ("rejected", "Từ chối"),
                    ("cancelled", "Đã hủy"),
                    ("expired", "Hết hạn"),
                ],
                default="draft",
                max_length=12,
            ),
        ),
        migrations.CreateModel(
            name="VoucherNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=240)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("is_read", models.BooleanField(default=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="voucher_notifications", to=settings.AUTH_USER_MODEL)),
                ("voucher", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="store.voucher")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="vouchernotification",
            constraint=models.UniqueConstraint(fields=("user", "voucher"), name="unique_voucher_notification_per_user"),
        ),
    ]
