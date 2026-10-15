import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def populate_tracking_tokens(apps, schema_editor):
    Order = apps.get_model("store", "Order")
    for order in Order.objects.filter(tracking_token__isnull=True).iterator():
        order.tracking_token = uuid.uuid4()
        order.save(update_fields=["tracking_token"])


class Migration(migrations.Migration):

    dependencies = [("store", "0006_order_voucher_code")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="tracking_token",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(populate_tracking_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="tracking_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.CreateModel(
            name="OrderNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=240)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("is_read", models.BooleanField(default=False)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="store.order")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
