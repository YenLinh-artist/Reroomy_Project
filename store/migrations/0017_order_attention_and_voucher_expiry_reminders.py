import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0016_staffnotification"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Cần xác nhận"),
                    ("needs_attention", "Cần xử lý"),
                    ("confirmed", "Đã xác nhận"),
                    ("shipping", "Đang giao"),
                    ("completed", "Hoàn tất"),
                    ("cancelled", "Đã hủy"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="status_before_attention",
            field=models.CharField(blank=True, choices=[
                ("pending", "Cần xác nhận"),
                ("needs_attention", "Cần xử lý"),
                ("confirmed", "Đã xác nhận"),
                ("shipping", "Đang giao"),
                ("completed", "Hoàn tất"),
                ("cancelled", "Đã hủy"),
            ], default="", max_length=20),
        ),
        migrations.AddField(
            model_name="order",
            name="support_reason",
            field=models.CharField(blank=True, default="", max_length=400),
        ),
        migrations.CreateModel(
            name="VoucherExpiryReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_key", models.CharField(max_length=80)),
                ("message", models.CharField(max_length=240)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("is_read", models.BooleanField(default=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="voucher_expiry_reminders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="voucherexpiryreminder",
            constraint=models.UniqueConstraint(fields=("user", "source_key"), name="unique_voucher_expiry_reminder"),
        ),
    ]
