import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0023_order_service_request_return_review_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="sanpham",
            name="room_width_cm",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="sanpham",
            name="room_depth_cm",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="dexuatsanpham",
            name="room_width_cm",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="dexuatsanpham",
            name="room_depth_cm",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.CreateModel(
            name="SanPhamAnhBoSung",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anh", models.FileField(upload_to="products/gallery/")),
                ("tao_luc", models.DateTimeField(auto_now_add=True)),
                ("san_pham", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="anh_bo_sung", to="store.sanpham")),
            ],
            options={"ordering": ("pk",)},
        ),
        migrations.CreateModel(
            name="DeXuatSanPhamAnhBoSung",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anh", models.FileField(upload_to="product_submissions/gallery/")),
                ("tao_luc", models.DateTimeField(auto_now_add=True)),
                ("de_xuat", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="anh_bo_sung", to="store.dexuatsanpham")),
            ],
            options={"ordering": ("pk",)},
        ),
    ]
