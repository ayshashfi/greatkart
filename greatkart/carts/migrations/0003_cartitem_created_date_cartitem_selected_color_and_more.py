# Generated by Django 5.0 on 2024-01-01 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("carts", "0002_cart_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="selected_color",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="selected_size",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]