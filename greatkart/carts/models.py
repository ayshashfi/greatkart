from django.db import models
from store.models import Product,Variation
from accounts.models import Account


# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE,null=True)
    cart_id=models.CharField(max_length=250,blank=True)
    date_added=models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.cart_id
    


from django.db import models

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    selected_color = models.CharField(max_length=255, null=True, blank=True)
    selected_size = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)

    # Add the discounted_price field
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product} - {self.quantity}"

    def calculate_discounted_price(self):
        # Calculate discounted price based on the product's offer
        if self.product.offer:
            return self.product.product_price - self.product.offer.discount_amount
        else:
            return self.product.product_price

    def sub_total(self):
        # Calculate subtotal based on the discounted price if available, otherwise use regular price
        if self.discounted_price is not None:
            return self.quantity * self.discounted_price
        else:
            return self.quantity * self.calculate_discounted_price()

    def save(self, *args, **kwargs):
        # Calculate and set the discounted_price before saving the CartItem
        self.discounted_price = self.calculate_discounted_price()
        super().save(*args, **kwargs)

    def __unicode__(self):
        return self.product


    