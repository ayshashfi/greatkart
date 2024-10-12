# Generated by Django 5.0 on 2024-01-09 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("carts", "0003_cartitem_created_date_cartitem_selected_color_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="discounted_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]