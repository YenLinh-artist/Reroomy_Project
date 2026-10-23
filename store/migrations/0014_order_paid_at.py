from django.db import migrations, models


def backfill_paid_at(apps, schema_editor):
    Order = apps.get_model("store", "Order")
    db_alias = schema_editor.connection.alias
    Order.objects.using(db_alias).filter(
        payment_status="paid",
        paid_at__isnull=True,
    ).update(paid_at=models.F("updated_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0013_monthly_voucher_rewards"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="paid_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_paid_at, migrations.RunPython.noop),
    ]
