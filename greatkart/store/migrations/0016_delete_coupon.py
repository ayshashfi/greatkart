# Generated by Django 5.0 on 2024-01-17 08:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0015_coupon"),
    ]

    operations = [
        migrations.DeleteModel(name="Coupon",),
    ]
