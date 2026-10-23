import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0013_monthly_voucher_rewards"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="dexuatsanpham",
            name="phan_loai",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.CreateModel(
            name="StaffChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_chat_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("created_at", "pk")},
        ),
    ]
