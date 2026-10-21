import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0010_merge_20261016_1040"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SignupVoucherGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32)),
                ("display_name", models.CharField(max_length=32)),
                ("discount_value", models.PositiveIntegerField()),
                ("minimum_order", models.PositiveBigIntegerField()),
                ("issued_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("redeemed_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="signup_voucher_grants", to="store.order")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signup_voucher_grants", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-issued_at"]},
        ),
        migrations.AddConstraint(
            model_name="signupvouchergrant",
            constraint=models.UniqueConstraint(fields=("user", "code"), name="unique_signup_voucher_per_user"),
        ),
    ]
