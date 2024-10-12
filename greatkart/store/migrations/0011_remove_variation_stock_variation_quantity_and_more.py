# Generated by Django 5.0 on 2023-12-30 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0010_rename_quantity_variation_stock"),
    ]

    operations = [
        migrations.RemoveField(model_name="variation", name="stock",),
        migrations.AddField(
            model_name="variation",
            name="quantity",
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name="color",
            name="color_code",
            field=models.CharField(max_length=15, null=True),
        ),
    ]
