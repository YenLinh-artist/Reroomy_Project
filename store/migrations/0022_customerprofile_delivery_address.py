from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0021_merge_20261104_1630"),
    ]

    operations = [
        migrations.AddField(
            model_name="customerprofile",
            name="address",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="delivery_note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
