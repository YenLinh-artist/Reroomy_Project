from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0024_product_gallery_and_room_dimensions"),
    ]

    operations = [
        migrations.AddField(
            model_name="sanpham",
            name="room_top_view",
            field=models.FileField(blank=True, upload_to="products/top-view/"),
        ),
    ]
