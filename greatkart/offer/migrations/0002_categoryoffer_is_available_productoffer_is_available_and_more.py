# Generated by Django 5.0 on 2024-01-02 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("offer", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoryoffer",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="productoffer",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="referraloffer",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
    ]