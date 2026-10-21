import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0012_vouchernotification_and_cancelled"),
    ]

    operations = [
        migrations.AddField(
            model_name="signupvouchergrant",
            name="grant_type",
            field=models.CharField(
                choices=[("signup", "Tặng khi đăng ký"), ("monthly", "Thưởng tháng")],
                default="signup",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="signupvouchergrant",
            name="reward_month",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="signupvouchergrant",
            name="is_read",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="MonthlyVoucherRewardBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month_start", models.DateField(unique=True)),
                ("recipient_count", models.PositiveIntegerField(default=0)),
                ("processed_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"ordering": ["-month_start"]},
        ),
    ]
