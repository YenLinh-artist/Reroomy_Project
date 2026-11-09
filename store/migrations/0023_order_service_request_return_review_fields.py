import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0022_customerprofile_delivery_address"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="orderservicerequest",
            name="unboxing_video",
            field=models.FileField(blank=True, upload_to="order_returns/videos/"),
        ),
        migrations.AddField(
            model_name="orderservicerequest",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_order_service_requests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="orderservicerequest",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderservicerequest",
            name="inventory_restored_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
