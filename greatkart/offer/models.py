from django.db import models
from django.db import models
from django.utils import timezone


class Offer(models.Model):
    offer_name=models.CharField(max_length=100,null=True)
    discount_amount=models.PositiveIntegerField(default=0)
    start_date=models.DateField(default= timezone.now)
    end_date= models.DateField(default=timezone.now)
    is_available=models.BooleanField(default =True)
    def __str__(self):
        return self.offer_name
    
    def is_offer_expired(self):
        return timezone.now().date() >=self.end_date


