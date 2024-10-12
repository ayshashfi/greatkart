# Generated by Django 5.0 on 2023-12-23 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_address_is_saved_address"),
    ]

    operations = [
        migrations.RemoveField(model_name="address", name="address",),
        migrations.RemoveField(model_name="address", name="is_saved_address",),
        migrations.AddField(
            model_name="address",
            name="address_line_1",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="address",
            name="address_line_2",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
