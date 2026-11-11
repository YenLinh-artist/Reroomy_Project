from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0025_sanpham_room_top_view"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderservicerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Chờ xử lý"),
                    ("admin_review", "Chờ admin duyệt"),
                    ("approved", "Đã xác nhận"),
                    ("rejected", "Không được duyệt"),
                    ("processing", "Đang tiếp nhận"),
                    ("received", "Đã nhận hàng hoàn"),
                    ("completed", "Đã xử lý xong"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="orderservicerequest",
            name="resolution_type",
            field=models.CharField(blank=True, choices=[("refund", "Hoàn tiền"), ("replacement", "Đổi sản phẩm")], default="", max_length=16),
        ),
        migrations.AddField(
            model_name="orderservicerequest",
            name="resolution_notes",
            field=models.TextField(blank=True, default="", max_length=1000),
        ),
    ]
