# Generated by Django 5.0 on 2023-12-19 06:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_variation_stock"),
    ]

    operations = [
        migrations.RemoveField(model_name="variation", name="stock",),
    ]
